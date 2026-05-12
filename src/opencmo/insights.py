"""Proactive Insight Engine — rule-based detectors that surface actionable changes.

Zero LLM cost. All detectors are pure Python comparing current vs previous scan data.
Insights are persisted to SQLite and surfaced via API to the frontend NotificationBell
and InsightBanner components.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from opencmo import storage

logger = logging.getLogger(__name__)


# Threshold below which Share-of-Voice mention counts are too noisy to compare.
_GEO_SOV_MIN_PREV_MENTIONS = 5
# Drop in brand share points (0..1 scale) to surface as warning / critical.
_GEO_SOV_WARNING_DROP = 0.05
_GEO_SOV_CRITICAL_DROP = 0.15
# Minimum platforms in the previous scan before a "blackout" delta is trustworthy.
_GEO_BLACKOUT_MIN_PREV_PLATFORMS = 2


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Insight:
    project_id: int
    insight_type: str      # serp_drop, geo_decline, community_buzz, seo_regress, competitor_gap
    severity: str          # critical, warning, info
    title: str
    summary: str
    action_type: str       # navigate, chat, api_call
    action_params: str     # JSON string with route/prompt/endpoint


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------


async def _detect_serp_drops(project_id: int) -> list[Insight]:
    """Detect keywords where SERP position dropped >= 5 positions."""
    insights: list[Insight] = []
    db = await storage.get_db()
    try:
        # Get latest 2 snapshots per keyword
        cursor = await db.execute(
            """SELECT keyword, position, checked_at,
                      ROW_NUMBER() OVER (PARTITION BY keyword ORDER BY checked_at DESC) AS rn
               FROM serp_snapshots
               WHERE project_id = ? AND error IS NULL AND position IS NOT NULL
               ORDER BY keyword, checked_at DESC""",
            (project_id,),
        )
        rows = await cursor.fetchall()

        # Group by keyword: {keyword: [(position, checked_at), ...]}
        kw_data: dict[str, list[tuple[int, str]]] = {}
        for r in rows:
            keyword, position, checked_at, rn = r[0], r[1], r[2], r[3]
            if rn <= 2:
                kw_data.setdefault(keyword, []).append((position, checked_at))

        for kw, snapshots in kw_data.items():
            if len(snapshots) < 2:
                continue
            current_pos, prev_pos = snapshots[0][0], snapshots[1][0]
            drop = current_pos - prev_pos  # positive = rank got worse
            if drop >= 5:
                severity = "critical" if drop >= 10 else "warning"
                insights.append(Insight(
                    project_id=project_id,
                    insight_type="serp_drop",
                    severity=severity,
                    title=f"Keyword '{kw}' dropped {drop} positions",
                    summary=f"'{kw}' moved from #{prev_pos} to #{current_pos}.",
                    action_type="navigate",
                    action_params=f'{{"route": "/projects/{project_id}/serp"}}',
                ))
    finally:
        await db.close()
    return insights


async def _detect_geo_decline(project_id: int) -> list[Insight]:
    """Detect GEO score decline >= 10 points."""
    latest = await storage.get_latest_scans(project_id)
    prev = await storage.get_previous_scans(project_id)

    if not latest.get("geo") or not prev or not prev.get("geo"):
        return []

    current_score = latest["geo"]["score"]
    prev_score = prev["geo"]["score"]
    if current_score is None or prev_score is None:
        return []

    drop = prev_score - current_score
    if drop >= 10:
        severity = "critical" if drop >= 20 else "warning"
        return [Insight(
            project_id=project_id,
            insight_type="geo_decline",
            severity=severity,
            title=f"GEO score dropped {drop} points",
            summary=f"AI visibility score fell from {prev_score} to {current_score}/100.",
            action_type="navigate",
            action_params=f'{{"route": "/projects/{project_id}/geo"}}',
        )]
    return []


def _safe_json_loads(raw: object) -> object | None:
    if not raw:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


async def _detect_geo_sov_decline(project_id: int) -> list[Insight]:
    """Detect a meaningful drop in brand Share-of-Voice across AI engine answers.

    Compares the latest two ``geo_scans`` and surfaces when the brand's share of
    mentions vs. tracked competitors falls noticeably. Requires the previous scan
    to have at least ``_GEO_SOV_MIN_PREV_MENTIONS`` mentions so the share isn't
    statistical noise.
    """
    history = await storage.get_geo_history(project_id, limit=2)
    if len(history) < 2:
        return []

    latest = _safe_json_loads(history[0].get("share_of_voice_json"))
    previous = _safe_json_loads(history[1].get("share_of_voice_json"))
    if not isinstance(latest, dict) or not isinstance(previous, dict):
        return []

    prev_total = previous.get("total_mentions")
    if not isinstance(prev_total, (int, float)) or prev_total < _GEO_SOV_MIN_PREV_MENTIONS:
        return []

    prev_brand = (previous.get("brand") or {}).get("share")
    latest_brand = (latest.get("brand") or {}).get("share")
    if not isinstance(prev_brand, (int, float)) or not isinstance(latest_brand, (int, float)):
        return []

    drop = float(prev_brand) - float(latest_brand)
    if drop < _GEO_SOV_WARNING_DROP:
        return []

    severity = "critical" if drop >= _GEO_SOV_CRITICAL_DROP else "warning"
    drop_pct = round(drop * 100, 1)
    prev_pct = round(float(prev_brand) * 100, 1)
    latest_pct = round(float(latest_brand) * 100, 1)
    return [Insight(
        project_id=project_id,
        insight_type="geo_sov_decline",
        severity=severity,
        title=f"Brand share of voice dropped {drop_pct} points",
        summary=(
            f"Share of voice in AI engine answers fell from {prev_pct}% to {latest_pct}%. "
            "Competitors may be taking over the conversation."
        ),
        action_type="navigate",
        action_params=f'{{"route": "/projects/{project_id}/geo"}}',
    )]


async def _detect_geo_platform_blackout(project_id: int) -> list[Insight]:
    """Detect platforms where the brand was mentioned previously but no longer is.

    Surfaces a single insight that lists the affected platforms. Skips when the
    previous scan only covered a single platform (one data point is too noisy).
    """
    history = await storage.get_geo_history(project_id, limit=2)
    if len(history) < 2:
        return []

    latest = _safe_json_loads(history[0].get("platform_results_json"))
    previous = _safe_json_loads(history[1].get("platform_results_json"))
    if not isinstance(latest, dict) or not isinstance(previous, dict):
        return []

    def _platform_items(payload: dict) -> dict[str, dict]:
        return {
            name: data
            for name, data in payload.items()
            if not name.startswith("_") and isinstance(data, dict)
        }

    prev_platforms = _platform_items(previous)
    latest_platforms = _platform_items(latest)
    if len(prev_platforms) < _GEO_BLACKOUT_MIN_PREV_PLATFORMS:
        return []

    lost: list[str] = []
    for name, prev_data in prev_platforms.items():
        if not prev_data.get("mentioned"):
            continue
        latest_data = latest_platforms.get(name) or {}
        if latest_data.get("mentioned"):
            continue
        lost.append(name)

    if not lost:
        return []

    lost_sorted = sorted(lost)
    platforms_label = ", ".join(lost_sorted[:3])
    if len(lost_sorted) > 3:
        platforms_label += f" +{len(lost_sorted) - 3} more"

    severity = "critical" if len(lost_sorted) >= 3 else "warning"
    return [Insight(
        project_id=project_id,
        insight_type="geo_platform_blackout",
        severity=severity,
        title=f"No longer mentioned on {len(lost_sorted)} AI engine(s)",
        summary=(
            f"Brand mentions disappeared on: {platforms_label}. "
            "Check content freshness and re-indexing on these platforms."
        ),
        action_type="navigate",
        action_params=f'{{"route": "/projects/{project_id}/geo"}}',
    )]


async def _detect_community_buzz(project_id: int) -> list[Insight]:
    """Detect high-engagement community discussions (engagement > 50)."""
    insights: list[Insight] = []
    discussions = await storage.get_tracked_discussions(project_id)
    for d in discussions:
        score = d.get("engagement_score") or 0
        if score > 50:
            title_short = d["title"][:60]
            insights.append(Insight(
                project_id=project_id,
                insight_type="community_buzz",
                severity="warning" if score > 80 else "info",
                title=f"High-engagement discussion on {d['platform']}",
                summary=f'"{title_short}" — engagement {score}, {d.get("comments_count", 0)} comments.',
                action_type="navigate",
                action_params=f'{{"route": "/projects/{project_id}/community", "url": "{d["url"]}"}}',
            ))
    return insights[:3]  # Top 3 only


async def _detect_seo_regress(project_id: int) -> list[Insight]:
    """Detect SEO performance score regression > 0.1."""
    latest = await storage.get_latest_scans(project_id)
    prev = await storage.get_previous_scans(project_id)

    if not latest.get("seo") or not prev or not prev.get("seo"):
        return []

    current_score = latest["seo"]["score"]
    prev_score = prev["seo"]["score"]
    if current_score is None or prev_score is None:
        return []

    drop = prev_score - current_score
    if drop > 0.1:
        severity = "critical" if drop > 0.3 else "warning"
        return [Insight(
            project_id=project_id,
            insight_type="seo_regress",
            severity=severity,
            title=f"SEO performance dropped {drop:.0%}",
            summary=f"Performance score fell from {prev_score:.0%} to {current_score:.0%}.",
            action_type="navigate",
            action_params=f'{{"route": "/projects/{project_id}/seo"}}',
        )]
    return []


async def _detect_competitor_gaps(project_id: int) -> list[Insight]:
    """Detect competitor keywords that the brand doesn't track."""
    insights: list[Insight] = []
    db = await storage.get_db()
    try:
        cursor = await db.execute(
            """SELECT ck.keyword, COUNT(DISTINCT c.id) AS comp_count
               FROM competitor_keywords ck
               JOIN competitors c ON c.id = ck.competitor_id
               WHERE c.project_id = ?
                 AND LOWER(ck.keyword) NOT IN (
                     SELECT LOWER(keyword) FROM tracked_keywords WHERE project_id = ?
                 )
               GROUP BY LOWER(ck.keyword)
               ORDER BY comp_count DESC
               LIMIT 5""",
            (project_id, project_id),
        )
        rows = await cursor.fetchall()
        if rows and len(rows) >= 3:
            keywords = [r[0] for r in rows]
            insights.append(Insight(
                project_id=project_id,
                insight_type="competitor_gap",
                severity="warning",
                title=f"{len(rows)} keyword gaps found",
                summary=f"Competitors rank for keywords you don't track: {', '.join(keywords[:3])}.",
                action_type="navigate",
                action_params=f'{{"route": "/projects/{project_id}/graph"}}',
            ))
    finally:
        await db.close()
    return insights


async def _detect_citability_regression(project_id: int) -> list[Insight]:
    """Detect citability score regression (>10 point drop)."""
    insights: list[Insight] = []
    history = await storage.get_citability_history(project_id, limit=2)
    if len(history) >= 2:
        current = history[0]["avg_score"]
        previous = history[1]["avg_score"]
        drop = previous - current
        if drop > 10:
            insights.append(Insight(
                project_id=project_id,
                insight_type="citability_regression",
                severity="warning",
                title=f"Citability score dropped {drop:.0f} points",
                summary=f"AI citation readiness fell from {previous:.0f} to {current:.0f}. Content may be less likely to be cited by AI search engines.",
                action_type="chat",
                action_params=f'{{"message": "My citability score dropped from {previous:.0f} to {current:.0f}. How can I improve my content for AI citations?"}}',
            ))
    return insights


async def _detect_brand_presence_decline(project_id: int) -> list[Insight]:
    """Detect brand presence score decline (>15 point drop)."""
    insights: list[Insight] = []
    history = await storage.get_brand_presence_history(project_id, limit=2)
    if len(history) >= 2:
        current = history[0].get("footprint_score", 0)
        previous = history[1].get("footprint_score", 0)
        drop = previous - current
        if drop > 15:
            insights.append(Insight(
                project_id=project_id,
                insight_type="brand_presence_decline",
                severity="warning",
                title=f"Brand presence score dropped {drop} points",
                summary=f"Digital footprint score fell from {previous} to {current}/100. Check platform presence across G2, Capterra, LinkedIn, and other credibility signals.",
                action_type="chat",
                action_params=f'{{"message": "My brand presence score dropped from {previous} to {current}. What platforms should I focus on to improve?"}}',
            ))
    return insights


async def _detect_low_content_frequency(project_id: int) -> list[Insight]:
    """Detect sites with no blog or very low content publishing frequency.

    Only fires after at least one successful SEO scan (proof that the URL is
    reachable), to avoid false positives on newly added or test projects.
    """
    project = await storage.get_project(project_id)
    if not project:
        return []

    # Only check content frequency if the site has been successfully scanned before
    seo_history = await storage.get_seo_history(project_id, limit=1)
    if not seo_history:
        return []

    try:
        from opencmo.tools.content_frequency import _analyze_content_frequency
        data = await _analyze_content_frequency(project["url"])
    except Exception:
        return []

    if not data.get("has_blog"):
        return [Insight(
            project_id=project_id,
            insight_type="no_content_hub",
            severity="warning",
            title="No blog or content section detected",
            summary="A regularly updated blog is essential for SEO growth. Without one, you miss opportunities to rank for problem, tool, and comparison keywords.",
            action_type="chat",
            action_params='{"message": "I don\'t have a blog yet. Help me plan a content strategy for my product."}',
        )]

    ppm = data.get("posts_per_month", 0)
    if ppm is not None and ppm < 1:
        return [Insight(
            project_id=project_id,
            insight_type="low_content_frequency",
            severity="info",
            title=f"Content publishing frequency is low ({ppm} posts/month)",
            summary="Publishing fewer than 2 posts per month limits your keyword coverage growth. Consider increasing publishing cadence.",
            action_type="chat",
            action_params=f'{{"message": "I only publish {ppm} posts per month. Help me plan a content calendar."}}',
        )]

    return []


async def _detect_ai_crawler_blocks(project_id: int) -> list[Insight]:
    """Detect if >50% of AI crawlers are blocked."""
    insights: list[Insight] = []
    history = await storage.get_ai_crawler_history(project_id, limit=1)
    if history:
        latest = history[0]
        blocked = latest["blocked_count"]
        total = latest["total_crawlers"]
        if blocked > total * 0.5:
            insights.append(Insight(
                project_id=project_id,
                insight_type="ai_crawlers_blocked",
                severity="critical",
                title=f"{blocked}/{total} AI crawlers blocked",
                summary="More than half of AI crawlers are blocked by robots.txt. This severely limits your AI search visibility.",
                action_type="chat",
                action_params=f'{{"message": "My robots.txt is blocking {blocked} out of {total} AI crawlers. Help me fix this."}}',
            ))
    return insights


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DETECTORS = [
    _detect_serp_drops,
    _detect_geo_decline,
    _detect_geo_sov_decline,
    _detect_geo_platform_blackout,
    _detect_community_buzz,
    _detect_seo_regress,
    _detect_competitor_gaps,
    _detect_citability_regression,
    _detect_ai_crawler_blocks,
    _detect_brand_presence_decline,
    _detect_low_content_frequency,
]


async def detect_insights(project_id: int) -> list[Insight]:
    """Run all detectors for a project. Deduplicates against recent insights (24h).

    Returns list of newly created insights.
    """
    all_insights: list[Insight] = []

    for detector in _DETECTORS:
        try:
            results = await detector(project_id)
            all_insights.extend(results)
        except Exception:
            logger.exception("Insight detector %s failed for project %d", detector.__name__, project_id)

    # Deduplicate: check existing insights from last 24h
    saved: list[Insight] = []
    for insight in all_insights:
        is_dup = await storage.is_insight_duplicate(
            project_id, insight.insight_type, insight.title,
        )
        if not is_dup:
            await storage.save_insight(
                project_id=insight.project_id,
                insight_type=insight.insight_type,
                severity=insight.severity,
                title=insight.title,
                summary=insight.summary,
                action_type=insight.action_type,
                action_params=insight.action_params,
            )
            saved.append(insight)

    if saved:
        logger.info("Generated %d new insights for project %d", len(saved), project_id)

    return saved
