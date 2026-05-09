"""Deterministic SVG chart generation for persisted AI CMO reports."""

from __future__ import annotations

import html
import os
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ReportChart:
    title: str
    description: str
    data_source: str
    points_count: int
    asset_id: str
    markdown: str
    degraded: bool = False

    def to_meta(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("markdown", None)
        return payload


def get_report_asset_dir() -> Path:
    configured = os.environ.get("OPENCMO_REPORT_ASSET_DIR")
    if configured:
        return Path(configured)
    db_path = os.environ.get("OPENCMO_DB_PATH")
    if db_path:
        return Path(db_path).expanduser().parent / "report_assets"
    return Path.home() / ".opencmo" / "report_assets"


def get_report_asset_path(asset_id: str) -> Path | None:
    if not re.fullmatch(r"[a-f0-9]{32}", asset_id):
        return None
    return get_report_asset_dir() / f"{asset_id}.svg"


def delete_chart_assets(asset_ids: Iterable[str]) -> None:
    for asset_id in asset_ids:
        asset_path = get_report_asset_path(asset_id)
        if not asset_path:
            continue
        try:
            asset_path.unlink(missing_ok=True)
        except OSError:
            continue


def charts_to_markdown(charts: list[ReportChart]) -> str:
    if not charts:
        return "当前数据不足，未生成图表。"
    blocks = []
    for chart in charts:
        blocks.append(
            "\n".join(
                [
                    f"### {chart.title}",
                    chart.markdown,
                    f"图表说明：{chart.description}",
                    f"数据来源：`{chart.data_source}`；数据点：{chart.points_count}。",
                    "数据限制：图表只使用系统已采集到的真实数据，缺失值不会被补造。",
                ]
            )
        )
    return "\n\n".join(blocks)


def build_report_charts(kind: str, facts: dict, meta: dict) -> list[ReportChart]:
    charts: list[ReportChart] = []
    charts.extend(_strategic_charts(facts, meta) if kind == "strategic" else _periodic_charts(facts, meta))
    return charts[:4]


def _asset_id() -> str:
    return uuid.uuid4().hex


def _write_svg(asset_id: str, svg: str) -> None:
    directory = get_report_asset_dir()
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{asset_id}.svg").write_text(svg, encoding="utf-8")


def _markdown(asset_id: str, title: str) -> str:
    return f"![{title}](/api/v1/report-assets/{asset_id}.svg)"


def _to_percent(value: Any) -> float | None:
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if 0 <= num <= 1:
        return round(num * 100, 1)
    return round(num, 1)


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _latest_first(items: list[dict], date_key: str) -> list[dict]:
    return sorted(items or [], key=lambda item: str(item.get(date_key) or ""), reverse=True)


def _strategic_charts(facts: dict, meta: dict) -> list[ReportChart]:
    charts: list[ReportChart] = []
    latest = facts.get("latest_scans") or {}
    kpis = [
        ("SEO", _to_percent((latest.get("seo") or {}).get("score"))),
        ("GEO", _number((latest.get("geo") or {}).get("score"))),
        ("Citability", _to_percent((facts.get("citability") or [{}])[0].get("avg_score") if facts.get("citability") else None)),
        ("Brand", _number((facts.get("brand_presence") or [{}])[0].get("footprint_score") if facts.get("brand_presence") else None)),
        ("Community", _number((latest.get("community") or {}).get("total_hits"))),
    ]
    kpis = [(label, value) for label, value in kpis if value is not None]
    if kpis:
        charts.append(_bar_chart("关键指标快照", kpis, "latest_scans/citability/brand_presence", "SEO、GEO、AI 引文可信度、品牌足迹与社区命中的当前快照。"))

    serp = [
        (str(item.get("keyword") or "keyword")[:24], _number(item.get("position")))
        for item in (facts.get("serp_latest") or [])
        if item.get("position") is not None
    ][:8]
    if serp:
        charts.append(_bar_chart("SERP 当前排名（数字越小越靠前）", serp, "serp_latest.position", "已跟踪关键词的当前自然搜索排名。"))

    coverage = [
        ("有数据", _number(meta.get("sample_count"))),
        ("总数据源", _number(meta.get("total_data_sources"))),
    ]
    if all(value is not None for _, value in coverage):
        charts.append(_bar_chart("数据覆盖度", coverage, "meta.sample_count/meta.total_data_sources", "本报告事实包的数据源覆盖情况。"))

    distribution = _finding_distribution(facts)
    if distribution:
        charts.append(_bar_chart("风险与建议分布", distribution, "findings/recommendations", "近期发现与建议按优先级聚合后的执行压力。"))
    return charts


def _periodic_charts(facts: dict, meta: dict) -> list[ReportChart]:
    charts: list[ReportChart] = []
    trend_series = [
        ("SEO", [(item.get("scanned_at"), _to_percent(item.get("score_performance"))) for item in _latest_first(facts.get("seo_history") or [], "scanned_at")]),
        ("GEO", [(item.get("scanned_at"), _number(item.get("geo_score"))) for item in _latest_first(facts.get("geo_history") or [], "scanned_at")]),
        ("Community", [(item.get("scanned_at"), _number(item.get("total_hits"))) for item in _latest_first(facts.get("community_history") or [], "scanned_at")]),
    ]
    for title, series in trend_series:
        points = [(label, value) for label, value in reversed(series) if value is not None]
        if len(points) >= 2:
            charts.append(_line_chart(f"{title} 趋势", points[-10:], f"{title.lower()}_history", f"{title} 在本报告窗口内的真实历史走势。"))

    citability = [(item.get("created_at") or item.get("scanned_at"), _to_percent(item.get("avg_score"))) for item in _latest_first(facts.get("citability") or [], "created_at")]
    citability_points = [(label, value) for label, value in reversed(citability) if value is not None]
    if len(citability_points) >= 2:
        charts.append(_line_chart("AI 引文可信度趋势", citability_points[-10:], "citability.avg_score", "AI 引文可信度在最近样本中的走势。"))

    distribution = _finding_distribution(facts)
    if distribution:
        charts.append(_bar_chart("本周风险与建议分布", distribution, "findings/recommendations", "本周期可行动问题按优先级聚合后的分布。"))
    return charts


def _finding_distribution(facts: dict) -> list[tuple[str, float]]:
    counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    for item in facts.get("findings") or []:
        priority = str((item.get("severity") or item.get("priority") or "unknown")).lower()
        counts[priority if priority in counts else "unknown"] += 1
    for item in facts.get("recommendations") or []:
        priority = str(item.get("priority") or "unknown").lower()
        counts[priority if priority in counts else "unknown"] += 1
    return [(label, count) for label, count in counts.items() if count]


def _bar_chart(title: str, values: list[tuple[str, float | None]], source: str, description: str) -> ReportChart:
    values = [(label, float(value)) for label, value in values if value is not None]
    asset_id = _asset_id()
    max_value = max((value for _, value in values), default=1) or 1
    width = 760
    row_h = 42
    height = 110 + row_h * len(values)
    rows = []
    for index, (label, value) in enumerate(values):
        y = 76 + index * row_h
        bar_w = max(4, int((value / max_value) * 460))
        rows.append(f'<text x="28" y="{y + 18}" font-size="14" fill="#334155">{html.escape(label)}</text>')
        rows.append(f'<rect x="190" y="{y}" width="{bar_w}" height="24" rx="5" fill="#4f46e5"/>')
        rows.append(f'<text x="{205 + bar_w}" y="{y + 18}" font-size="13" fill="#0f172a">{value:g}</text>')
    svg = _svg_frame(width, height, title, "\n".join(rows))
    _write_svg(asset_id, svg)
    return ReportChart(title, description, source, len(values), asset_id, _markdown(asset_id, title))


def _line_chart(title: str, points: list[tuple[Any, float]], source: str, description: str) -> ReportChart:
    points = [(str(label or index + 1), float(value)) for index, (label, value) in enumerate(points)]
    asset_id = _asset_id()
    width = 760
    height = 320
    min_v = min(value for _, value in points)
    max_v = max(value for _, value in points)
    span = max(max_v - min_v, 1)
    left, right, top, bottom = 70, 700, 70, 250
    coords = []
    for index, (_, value) in enumerate(points):
        x = left + (right - left) * (index / max(len(points) - 1, 1))
        y = bottom - ((value - min_v) / span) * (bottom - top)
        coords.append((x, y, value))
    path = " ".join(("M" if index == 0 else "L") + f" {x:.1f} {y:.1f}" for index, (x, y, _) in enumerate(coords))
    circles = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#4f46e5"><title>{value:g}</title></circle>'
        for x, y, value in coords
    )
    labels = "\n".join(
        f'<text x="{x:.1f}" y="278" font-size="11" fill="#64748b" text-anchor="middle">{html.escape(label[:10])}</text>'
        for (label, _), (x, _, _) in zip(points, coords)
    )
    body = (
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#cbd5e1"/>'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#cbd5e1"/>'
        f'<text x="22" y="{top + 6}" font-size="12" fill="#64748b">{max_v:g}</text>'
        f'<text x="22" y="{bottom + 4}" font-size="12" fill="#64748b">{min_v:g}</text>'
        f'<path d="{path}" fill="none" stroke="#4f46e5" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
        f"{circles}{labels}"
    )
    svg = _svg_frame(width, height, title, body)
    _write_svg(asset_id, svg)
    return ReportChart(title, description, source, len(points), asset_id, _markdown(asset_id, title))


def _svg_frame(width: int, height: int, title: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">'
        '<rect width="100%" height="100%" rx="16" fill="#ffffff"/>'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="16" fill="none" stroke="#e2e8f0"/>'
        f'<text x="28" y="38" font-size="20" font-weight="700" fill="#0f172a">{html.escape(title)}</text>'
        f"{body}</svg>"
    )
