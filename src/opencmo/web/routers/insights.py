"""Insights API router."""

from __future__ import annotations

import json
import logging
import re

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import llm, storage
from opencmo.web.auth import get_request_account_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

_LANG_NAMES: dict[str, str] = {
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
}


def _match(pattern: str, value: str) -> re.Match[str] | None:
    return re.search(pattern, value)


def _translate_known_insight(row: dict, lang: str) -> dict | None:
    """Translate rule-generated insight copy without requiring an LLM call."""
    if lang != "zh":
        return None

    insight_type = str(row.get("insight_type") or "")
    title = str(row.get("title") or "")
    summary = str(row.get("summary") or "")

    translated_title: str | None = None
    translated_summary: str | None = None

    if insight_type == "serp_drop":
        title_match = _match(r"Keyword '(.+)' dropped (\d+) positions", title)
        summary_match = _match(r"'(.+)' moved from #(\d+) to #(\d+)\.", summary)
        if title_match:
            translated_title = f"关键词“{title_match.group(1)}”下跌 {title_match.group(2)} 位"
        if summary_match:
            translated_summary = (
                f"“{summary_match.group(1)}”从第 {summary_match.group(2)} 位变为第 "
                f"{summary_match.group(3)} 位。"
            )

    elif insight_type == "geo_decline":
        title_match = _match(r"GEO score dropped ([\d.]+) points", title)
        summary_match = _match(r"AI visibility score fell from ([\d.]+) to ([\d.]+)/100\.", summary)
        if title_match:
            translated_title = f"GEO 分数下降 {title_match.group(1)} 分"
        if summary_match:
            translated_summary = (
                f"AI 可见度分数从 {summary_match.group(1)} 降至 {summary_match.group(2)}/100。"
            )

    elif insight_type == "geo_sov_decline":
        title_match = _match(r"Brand share of voice dropped ([\d.]+) points", title)
        summary_match = _match(
            r"Share of voice in AI engine answers fell from ([\d.]+)% to ([\d.]+)%\.",
            summary,
        )
        if title_match:
            translated_title = f"品牌声量份额下降 {title_match.group(1)} 个百分点"
        if summary_match:
            translated_summary = (
                f"AI 引擎回答中的品牌声量份额从 {summary_match.group(1)}% 降至 "
                f"{summary_match.group(2)}%。竞品可能正在抢占用户对话。"
            )

    elif insight_type == "geo_platform_blackout":
        title_match = _match(r"No longer mentioned on (\d+) AI engine\(s\)", title)
        summary_match = _match(r"Brand mentions disappeared on: (.+?)\.", summary)
        if title_match:
            translated_title = f"在 {title_match.group(1)} 个 AI 引擎上不再被提及"
        if summary_match:
            translated_summary = (
                f"以下平台不再提及品牌：{summary_match.group(1)}。"
                "请检查这些平台上的内容新鲜度与重新索引情况。"
            )

    elif insight_type == "community_buzz":
        title_match = _match(r"High-engagement discussion on (.+)", title)
        summary_match = _match(r'"(.+)" — engagement ([\d.]+), (\d+) comments\.', summary)
        if title_match:
            translated_title = f"{title_match.group(1)} 上出现高互动讨论"
        if summary_match:
            translated_summary = (
                f"“{summary_match.group(1)}”的互动分为 {summary_match.group(2)}，"
                f"{summary_match.group(3)} 条评论。"
            )

    elif insight_type == "seo_regress":
        title_match = _match(r"SEO performance dropped ([\d.]+%)", title)
        summary_match = _match(r"Performance score fell from ([\d.]+%) to ([\d.]+%)\.", summary)
        if title_match:
            translated_title = f"SEO 表现下降 {title_match.group(1)}"
        if summary_match:
            translated_summary = f"表现分数从 {summary_match.group(1)} 降至 {summary_match.group(2)}。"

    elif insight_type == "competitor_gap":
        title_match = _match(r"(\d+) keyword gaps found", title)
        summary_match = _match(r"Competitors rank for keywords you don't track: (.+)\.", summary)
        if title_match:
            translated_title = f"发现 {title_match.group(1)} 个关键词缺口"
        if summary_match:
            translated_summary = f"竞品正在覆盖你尚未跟踪的关键词：{summary_match.group(1)}。"

    elif insight_type == "citability_regression":
        title_match = _match(r"Citability score dropped ([\d.]+) points", title)
        summary_match = _match(r"AI citation readiness fell from ([\d.]+) to ([\d.]+)\.", summary)
        if title_match:
            translated_title = f"AI 引用就绪分下降 {title_match.group(1)} 分"
        if summary_match:
            translated_summary = (
                f"AI 引用就绪度从 {summary_match.group(1)} 降至 {summary_match.group(2)}。"
                "内容被 AI 搜索引用的可能性可能降低。"
            )

    elif insight_type == "ai_crawlers_blocked":
        title_match = _match(r"(\d+)/(\d+) AI crawlers blocked", title)
        if title_match:
            translated_title = f"{title_match.group(1)}/{title_match.group(2)} 个 AI 爬虫被阻止"
            translated_summary = "超过一半的 AI 爬虫被 robots.txt 阻止，这会严重限制 AI 搜索可见度。"

    elif insight_type == "brand_presence_decline":
        title_match = _match(r"Brand presence score dropped ([\d.]+) points", title)
        summary_match = _match(r"Digital footprint score fell from ([\d.]+) to ([\d.]+)/100\.", summary)
        if title_match:
            translated_title = f"品牌存在感分数下降 {title_match.group(1)} 分"
        if summary_match:
            translated_summary = (
                f"数字足迹分数从 {summary_match.group(1)} 降至 {summary_match.group(2)}/100。"
                "请检查 G2、Capterra、LinkedIn 等平台上的可信度信号。"
            )

    elif insight_type == "no_content_hub":
        translated_title = "未检测到博客或内容栏目"
        translated_summary = (
            "持续更新的博客对 SEO 增长很重要。缺少内容中心会错过问题、工具和对比类关键词的排名机会。"
        )

    elif insight_type == "low_content_frequency":
        title_match = _match(r"Content publishing frequency is low \(([\d.]+) posts/month\)", title)
        if title_match:
            translated_title = f"内容发布频率偏低（每月 {title_match.group(1)} 篇）"
            translated_summary = "每月少于 2 篇内容会限制关键词覆盖增长。建议提高发布节奏。"

    if translated_title is None and translated_summary is None:
        return None

    return {
        **row,
        "title": translated_title or title,
        "summary": translated_summary or summary,
    }


async def _translate_insights(items: list[dict], lang: str) -> list[dict]:
    """Translate insight title and summary to the requested language via LLM.

    Falls back silently to the original English content on any error.
    """
    if not items:
        return items

    localized: list[dict] = []
    pending_indexes: list[int] = []
    pending_items: list[dict] = []

    for row in items:
        translated = _translate_known_insight(row, lang)
        if translated is None:
            pending_indexes.append(len(localized))
            pending_items.append(row)
            localized.append(row)
        else:
            localized.append(translated)

    if not pending_items or lang not in _LANG_NAMES:
        return localized

    lang_name = _LANG_NAMES[lang]
    payload = [{"id": r["id"], "title": r["title"], "summary": r["summary"]} for r in pending_items]
    system = "You are a precise translator. Output only valid JSON array, no markdown, no explanation."
    user = (
        f"Translate these marketing insight titles and summaries to {lang_name}.\n"
        f"Return the exact same JSON array structure with translated 'title' and 'summary' fields.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        raw = await llm.chat_completion(system, user, temperature=0.3)
        translated: list = json.loads(raw)
        mapping = {str(r["id"]): r for r in translated if isinstance(r, dict) and "id" in r}
        for index, row in zip(pending_indexes, pending_items):
            localized[index] = {
                **row,
                "title": mapping.get(str(row["id"]), {}).get("title", row["title"]),
                "summary": mapping.get(str(row["id"]), {}).get("summary", row["summary"]),
            }
        return localized
    except Exception:
        logger.debug("Insight translation failed for lang=%s, returning original", lang)
        return localized


@router.get("/insights")
async def api_v1_insights(request: Request):
    account_id = await get_request_account_id(request)
    project_id = request.query_params.get("project_id")
    unread = request.query_params.get("unread", "").lower() in ("true", "1")
    lang = request.query_params.get("lang", "en")
    pid = int(project_id) if project_id else None
    if pid is not None and not await storage.get_project(pid, account_id=account_id):
        return JSONResponse([], status_code=200)
    insights = await storage.list_insights(project_id=pid, unread_only=unread, account_id=account_id)
    insights = await _translate_insights(insights, lang)
    return JSONResponse(insights)


@router.get("/insights/summary")
async def api_v1_insights_summary(request: Request):
    account_id = await get_request_account_id(request)
    project_id = request.query_params.get("project_id")
    lang = request.query_params.get("lang", "en")
    pid = int(project_id) if project_id else None
    if pid is not None and not await storage.get_project(pid, account_id=account_id):
        return JSONResponse({"unread_count": 0, "recent": []})
    summary = await storage.get_insights_summary(project_id=pid, account_id=account_id)
    summary["recent"] = await _translate_insights(summary["recent"], lang)
    return JSONResponse(summary)


@router.post("/insights/{insight_id}/read")
async def api_v1_insight_read(insight_id: int):
    ok = await storage.mark_insight_read(insight_id)
    if not ok:
        return JSONResponse({"error": "Not found or already read"}, status_code=404)
    return JSONResponse({"ok": True})


@router.post("/insights/read-all")
async def api_v1_insights_read_all(request: Request):
    account_id = await get_request_account_id(request)
    project_id = request.query_params.get("project_id")
    pid = int(project_id) if project_id else None
    if pid is not None and not await storage.get_project(pid, account_id=account_id):
        return JSONResponse({"ok": True, "updated": 0})
    updated = await storage.mark_all_insights_read(project_id=pid, account_id=account_id)
    return JSONResponse({"ok": True, "updated": updated})
