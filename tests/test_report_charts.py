from __future__ import annotations

from fastapi.testclient import TestClient

from opencmo.report_charts import build_report_charts, delete_chart_assets, get_report_asset_path
from opencmo.reports import (
    _normalize_report_headings,
    _postprocess_human_report_content,
    _simple_markdown_to_html,
)
from opencmo.web.app import app


def test_strategic_chart_builder_uses_real_fact_values(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCMO_REPORT_ASSET_DIR", str(tmp_path))
    facts = {
        "latest_scans": {
            "seo": {"score": 0.82},
            "geo": {"score": 57},
            "community": {"total_hits": 12},
        },
        "citability": [{"avg_score": 0.41}],
        "brand_presence": [{"footprint_score": 33}],
        "serp_latest": [{"keyword": "ai cmo", "position": 4}],
        "findings": [{"severity": "high"}],
        "recommendations": [{"priority": "medium"}],
    }
    charts = build_report_charts("strategic", facts, {"sample_count": 3, "total_data_sources": 5})

    assert charts
    assert charts[0].markdown.startswith("![")
    svg = get_report_asset_path(charts[0].asset_id).read_text(encoding="utf-8")
    assert "SEO" in svg
    assert "82" in svg
    assert "57" in svg


def test_periodic_chart_builder_requires_two_points_for_trends(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCMO_REPORT_ASSET_DIR", str(tmp_path))
    facts = {
        "seo_history": [{"scanned_at": "2026-05-01T00:00:00", "score_performance": 0.7}],
        "geo_history": [
            {"scanned_at": "2026-05-01T00:00:00", "geo_score": 40},
            {"scanned_at": "2026-05-02T00:00:00", "geo_score": 50},
        ],
        "community_history": [],
        "citability": [],
        "findings": [],
        "recommendations": [],
    }
    charts = build_report_charts("periodic", facts, {"sample_count": 2, "total_data_sources": 8})

    assert [chart.title for chart in charts] == ["GEO 趋势"]
    svg = get_report_asset_path(charts[0].asset_id).read_text(encoding="utf-8")
    assert "40" in svg
    assert "50" in svg


def test_report_heading_normalization_and_chart_section_insertion():
    content = "# 总标题\n\n## 1. 执行摘要\n\n正文\n\n#### 深层标题\n\n内容"

    normalized = _normalize_report_headings(content)
    assert "####" not in normalized
    assert "### 深层标题" in normalized

    processed = _postprocess_human_report_content(normalized, "### 图表\n![图](/api/v1/report-assets/abc.svg)")
    assert "## 2. 数据图表速览" in processed
    assert processed.count("# 总标题") == 1


def test_simple_markdown_to_html_supports_images():
    asset_id = "a" * 32
    html = _simple_markdown_to_html(f"![关键指标](/api/v1/report-assets/{asset_id}.svg)")

    assert f'<img src="/api/v1/report-assets/{asset_id}.svg" alt="关键指标" />' in html
    assert "<figcaption>关键指标</figcaption>" in html


def test_simple_markdown_to_html_rejects_external_images():
    html = _simple_markdown_to_html("![x](https://attacker.com/pixel.gif)")

    assert "<img" not in html
    assert "<p>![x](https://attacker.com/pixel.gif)</p>" in html


def test_simple_markdown_to_html_rejects_javascript_url():
    html = _simple_markdown_to_html("![x](javascript:alert(1))")

    assert "<img" not in html
    assert "<p>![x](javascript:alert(1))</p>" in html


def test_postprocess_skips_chart_section_when_already_referenced():
    asset_id = "b" * 32
    content = f"# 总标题\n\n## 二、数据图表速览\n\n正文 /api/v1/report-assets/{asset_id}.svg"

    processed = _postprocess_human_report_content(content, "### 图表\n![图](/api/v1/report-assets/c.svg)")

    assert processed == content
    assert "## 2. 数据图表速览" not in processed


def test_delete_chart_assets_removes_files_and_ignores_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCMO_REPORT_ASSET_DIR", str(tmp_path))
    asset_ids = ["c" * 32, "d" * 32]
    for asset_id in asset_ids:
        (tmp_path / f"{asset_id}.svg").write_text("<svg></svg>", encoding="utf-8")

    delete_chart_assets([*asset_ids, "e" * 32, "not-valid"])

    assert not (tmp_path / f"{asset_ids[0]}.svg").exists()
    assert not (tmp_path / f"{asset_ids[1]}.svg").exists()


def test_report_asset_route_serves_svg(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCMO_REPORT_ASSET_DIR", str(tmp_path))
    asset_id = "a" * 32
    (tmp_path / f"{asset_id}.svg").write_text("<svg></svg>", encoding="utf-8")

    response = TestClient(app).get(f"/api/v1/report-assets/{asset_id}.svg")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")


def test_report_asset_route_rejects_missing_or_invalid_assets(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENCMO_REPORT_ASSET_DIR", str(tmp_path))
    client = TestClient(app)

    invalid_response = client.get("/api/v1/report-assets/not-valid.svg")
    missing_response = client.get(f"/api/v1/report-assets/{'f' * 32}.svg")

    assert invalid_response.status_code == 404
    assert missing_response.status_code == 404
