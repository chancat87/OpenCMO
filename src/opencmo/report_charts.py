"""Deterministic SVG chart generation for persisted AI CMO reports."""

from __future__ import annotations

import html
import os
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

_SUPPORTED_LOCALES = {"en", "zh", "ja", "ko", "es"}
_CHART_COPY = {
    "en": {
        "empty": "Insufficient data; no chart was generated.",
        "chart_note": "Chart note",
        "data_source": "Data source",
        "data_points": "data points",
        "data_limit": "Data limitation: charts use only real collected system data; missing values are not fabricated.",
        "kpi_snapshot": "Key Metrics Snapshot",
        "kpi_snapshot_desc": "Current snapshot of SEO, GEO, AI citation trust, brand footprint, and community hits.",
        "serp_rank": "Current SERP Rankings (Lower Is Better)",
        "serp_rank_desc": "Current organic search positions for tracked keywords.",
        "coverage": "Data Coverage",
        "coverage_available": "Available",
        "coverage_total": "Total sources",
        "coverage_desc": "Coverage of available sources in this report fact package.",
        "risk_distribution": "Risk and Recommendation Distribution",
        "risk_distribution_desc": "Action pressure aggregated by normalized priority.",
        "weekly_risk_distribution": "Weekly Risk and Recommendation Distribution",
        "weekly_risk_distribution_desc": "Distribution of actionable issues in this reporting period.",
        "trend": "{metric} Trend",
        "trend_desc": "{metric} trend from real samples inside this report window.",
        "citability_trend": "AI Citation Trust Trend",
        "citability_trend_desc": "AI citation trust trend across recent samples.",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "unknown": "Unknown",
    },
    "zh": {
        "empty": "当前数据不足，未生成图表。",
        "chart_note": "图表说明",
        "data_source": "数据来源",
        "data_points": "数据点",
        "data_limit": "数据限制：图表只使用系统已采集到的真实数据，缺失值不会被补造。",
        "kpi_snapshot": "关键指标快照",
        "kpi_snapshot_desc": "SEO、GEO、AI 引文可信度、品牌足迹与社区命中的当前快照。",
        "serp_rank": "SERP 当前排名（数字越小越靠前）",
        "serp_rank_desc": "已跟踪关键词的当前自然搜索排名。",
        "coverage": "数据覆盖度",
        "coverage_available": "有数据",
        "coverage_total": "总数据源",
        "coverage_desc": "本报告事实包的数据源覆盖情况。",
        "risk_distribution": "风险与建议分布",
        "risk_distribution_desc": "近期发现与建议按优先级聚合后的执行压力。",
        "weekly_risk_distribution": "本周风险与建议分布",
        "weekly_risk_distribution_desc": "本周期可行动问题按优先级聚合后的分布。",
        "trend": "{metric} 趋势",
        "trend_desc": "{metric} 在本报告窗口内的真实历史走势。",
        "citability_trend": "AI 引文可信度趋势",
        "citability_trend_desc": "AI 引文可信度在最近样本中的走势。",
        "high": "高优先级",
        "medium": "中优先级",
        "low": "低优先级",
        "unknown": "未知",
    },
    "ja": {
        "empty": "データが不足しているため、チャートは生成されませんでした。",
        "chart_note": "チャート注記",
        "data_source": "データソース",
        "data_points": "データ点",
        "data_limit": "データ制約: チャートは収集済みの実データのみを使用し、欠損値は補完しません。",
        "kpi_snapshot": "主要指標スナップショット",
        "kpi_snapshot_desc": "SEO、GEO、AI引用信頼度、ブランド露出、コミュニティ反応の現状です。",
        "serp_rank": "現在のSERP順位（小さいほど良い）",
        "serp_rank_desc": "追跡キーワードの現在の自然検索順位です。",
        "coverage": "データカバレッジ",
        "coverage_available": "利用可能",
        "coverage_total": "総データソース",
        "coverage_desc": "このレポート事実パッケージのデータソース網羅状況です。",
        "risk_distribution": "リスクと推奨事項の分布",
        "risk_distribution_desc": "優先度別に集計した実行圧力です。",
        "weekly_risk_distribution": "週間リスクと推奨事項の分布",
        "weekly_risk_distribution_desc": "この期間の実行可能な課題分布です。",
        "trend": "{metric}トレンド",
        "trend_desc": "このレポート期間内の実サンプルに基づく{metric}の推移です。",
        "citability_trend": "AI引用信頼度トレンド",
        "citability_trend_desc": "最近のサンプルにおけるAI引用信頼度の推移です。",
        "high": "高",
        "medium": "中",
        "low": "低",
        "unknown": "不明",
    },
    "ko": {
        "empty": "현재 데이터가 부족하여 차트를 생성하지 못했습니다.",
        "chart_note": "차트 설명",
        "data_source": "데이터 출처",
        "data_points": "데이터 포인트",
        "data_limit": "데이터 제한: 차트는 시스템이 수집한 실제 데이터만 사용하며 누락값은 만들지 않습니다.",
        "kpi_snapshot": "핵심 지표 스냅샷",
        "kpi_snapshot_desc": "SEO, GEO, AI 인용 신뢰도, 브랜드 발자취, 커뮤니티 반응의 현재 스냅샷입니다.",
        "serp_rank": "현재 SERP 순위(낮을수록 좋음)",
        "serp_rank_desc": "추적 키워드의 현재 자연 검색 순위입니다.",
        "coverage": "데이터 커버리지",
        "coverage_available": "사용 가능",
        "coverage_total": "전체 데이터 소스",
        "coverage_desc": "이 보고서 사실 패키지의 데이터 소스 커버리지입니다.",
        "risk_distribution": "리스크 및 권고 분포",
        "risk_distribution_desc": "정규화된 우선순위별 실행 압력입니다.",
        "weekly_risk_distribution": "주간 리스크 및 권고 분포",
        "weekly_risk_distribution_desc": "이번 보고 기간의 실행 가능한 이슈 분포입니다.",
        "trend": "{metric} 추세",
        "trend_desc": "이번 보고 기간 내 실제 샘플 기반 {metric} 추세입니다.",
        "citability_trend": "AI 인용 신뢰도 추세",
        "citability_trend_desc": "최근 샘플의 AI 인용 신뢰도 추세입니다.",
        "high": "높음",
        "medium": "중간",
        "low": "낮음",
        "unknown": "알 수 없음",
    },
    "es": {
        "empty": "No se generó ningún gráfico porque los datos son insuficientes.",
        "chart_note": "Nota del gráfico",
        "data_source": "Fuente de datos",
        "data_points": "puntos de datos",
        "data_limit": "Limitación de datos: los gráficos usan solo datos reales recopilados; no se inventan valores faltantes.",
        "kpi_snapshot": "Instantánea de Métricas Clave",
        "kpi_snapshot_desc": "Instantánea actual de SEO, GEO, confianza de citas de IA, huella de marca y señales de comunidad.",
        "serp_rank": "Ranking SERP Actual (Menor Es Mejor)",
        "serp_rank_desc": "Posiciones orgánicas actuales de las palabras clave monitorizadas.",
        "coverage": "Cobertura de Datos",
        "coverage_available": "Disponible",
        "coverage_total": "Fuentes totales",
        "coverage_desc": "Cobertura de fuentes disponibles en este paquete de hechos del informe.",
        "risk_distribution": "Distribución de Riesgos y Recomendaciones",
        "risk_distribution_desc": "Presión de ejecución agregada por prioridad normalizada.",
        "weekly_risk_distribution": "Distribución Semanal de Riesgos y Recomendaciones",
        "weekly_risk_distribution_desc": "Distribución de problemas accionables en este periodo.",
        "trend": "Tendencia de {metric}",
        "trend_desc": "Tendencia de {metric} con muestras reales dentro de la ventana del informe.",
        "citability_trend": "Tendencia de Confianza de Citas de IA",
        "citability_trend_desc": "Tendencia de confianza de citas de IA en muestras recientes.",
        "high": "Alta",
        "medium": "Media",
        "low": "Baja",
        "unknown": "Desconocida",
    },
}
_PRIORITY_ALIASES = {
    "critical": "high",
    "high": "high",
    "warning": "medium",
    "medium": "medium",
    "info": "low",
    "low": "low",
}


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


def _normalize_locale(locale: str | None) -> str:
    normalized = (locale or "zh").split("-", 1)[0].lower()
    return normalized if normalized in _SUPPORTED_LOCALES else "zh"


def _copy(locale: str | None) -> dict[str, str]:
    return _CHART_COPY[_normalize_locale(locale)]


def charts_to_markdown(charts: list[ReportChart], *, locale: str = "zh") -> str:
    copy = _copy(locale)
    if not charts:
        return copy["empty"]
    blocks = []
    for chart in charts:
        blocks.append(
            "\n".join(
                [
                    f"### {chart.title}",
                    chart.markdown,
                    f"{copy['chart_note']}: {chart.description}",
                    f"{copy['data_source']}: `{chart.data_source}`; {copy['data_points']}: {chart.points_count}.",
                    copy["data_limit"],
                ]
            )
        )
    return "\n\n".join(blocks)


def build_report_charts(kind: str, facts: dict, meta: dict, *, locale: str = "zh") -> list[ReportChart]:
    charts: list[ReportChart] = []
    charts.extend(_strategic_charts(facts, meta, locale) if kind == "strategic" else _periodic_charts(facts, meta, locale))
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


def _strategic_charts(facts: dict, meta: dict, locale: str) -> list[ReportChart]:
    copy = _copy(locale)
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
        charts.append(_bar_chart(copy["kpi_snapshot"], kpis, "latest_scans/citability/brand_presence", copy["kpi_snapshot_desc"]))

    serp = [
        (str(item.get("keyword") or "keyword")[:24], _number(item.get("position")))
        for item in (facts.get("serp_latest") or [])
        if item.get("position") is not None
    ][:8]
    if serp:
        charts.append(_bar_chart(copy["serp_rank"], serp, "serp_latest.position", copy["serp_rank_desc"]))

    coverage = [
        (copy["coverage_available"], _number(meta.get("sample_count"))),
        (copy["coverage_total"], _number(meta.get("total_data_sources"))),
    ]
    if all(value is not None for _, value in coverage):
        charts.append(_bar_chart(copy["coverage"], coverage, "meta.sample_count/meta.total_data_sources", copy["coverage_desc"]))

    distribution = _finding_distribution(facts, locale=locale)
    if distribution:
        charts.append(_bar_chart(copy["risk_distribution"], distribution, "findings/recommendations", copy["risk_distribution_desc"]))
    return charts


def _periodic_charts(facts: dict, meta: dict, locale: str) -> list[ReportChart]:
    copy = _copy(locale)
    charts: list[ReportChart] = []
    trend_series = [
        ("SEO", [(item.get("scanned_at"), _to_percent(item.get("score_performance"))) for item in _latest_first(facts.get("seo_history") or [], "scanned_at")]),
        ("GEO", [(item.get("scanned_at"), _number(item.get("geo_score"))) for item in _latest_first(facts.get("geo_history") or [], "scanned_at")]),
        ("Community", [(item.get("scanned_at"), _number(item.get("total_hits"))) for item in _latest_first(facts.get("community_history") or [], "scanned_at")]),
    ]
    for title, series in trend_series:
        points = [(label, value) for label, value in reversed(series) if value is not None]
        if len(points) >= 2:
            charts.append(_line_chart(copy["trend"].format(metric=title), points[-10:], f"{title.lower()}_history", copy["trend_desc"].format(metric=title)))

    citability = [(item.get("created_at") or item.get("scanned_at"), _to_percent(item.get("avg_score"))) for item in _latest_first(facts.get("citability") or [], "created_at")]
    citability_points = [(label, value) for label, value in reversed(citability) if value is not None]
    if len(citability_points) >= 2:
        charts.append(_line_chart(copy["citability_trend"], citability_points[-10:], "citability.avg_score", copy["citability_trend_desc"]))

    distribution = _finding_distribution(facts, locale=locale)
    if distribution:
        charts.append(_bar_chart(copy["weekly_risk_distribution"], distribution, "findings/recommendations", copy["weekly_risk_distribution_desc"]))
    return charts


def _finding_distribution(facts: dict, *, locale: str = "zh") -> list[tuple[str, float]]:
    copy = _copy(locale)
    counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    for item in facts.get("findings") or []:
        priority = _PRIORITY_ALIASES.get(str((item.get("severity") or item.get("priority") or "unknown")).lower(), "unknown")
        counts[priority if priority in counts else "unknown"] += 1
    for item in facts.get("recommendations") or []:
        priority = _PRIORITY_ALIASES.get(str(item.get("priority") or "unknown").lower(), "unknown")
        counts[priority if priority in counts else "unknown"] += 1
    return [(copy[label], count) for label, count in counts.items() if count]


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
