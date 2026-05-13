"""Tests for monitoring orchestration."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from opencmo import storage
from opencmo.monitoring import _collect_signals, run_monitoring_workflow
from opencmo.services.intelligence_service import analyze_and_enrich_project


@pytest.fixture(autouse=True)
def _db(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        yield


def run(coro):
    return asyncio.run(coro)


def test_run_monitoring_workflow_persists_artifacts():
    project_id = run(storage.ensure_project("Acme", "https://acme.test", "saas"))
    run(storage.add_tracked_keyword(project_id, "acme ai"))
    competitor_id = run(storage.add_competitor(project_id, "CompetitorX", url="https://comp.test"))
    run(storage.add_competitor_keyword(competitor_id, "acme ai"))

    run(storage.save_seo_scan(
        project_id,
        "https://acme.test",
        "{}",
        score_performance=0.42,
        score_lcp=4200,
        score_cls=0.18,
        score_tbt=700,
        has_robots_txt=False,
        has_sitemap=False,
        has_schema_org=False,
    ))
    run(storage.save_geo_scan(
        project_id,
        18,
        visibility_score=10,
        position_score=5,
        sentiment_score=3,
        platform_results_json='{"perplexity": {"mentioned": false}}',
    ))
    run(storage.save_community_scan(project_id, 0, '{"hits": []}'))

    with patch("opencmo.scheduler.run_scheduled_scan", new_callable=AsyncMock), \
         patch("opencmo.monitoring._collect_signals", new_callable=AsyncMock):
        result = run(run_monitoring_workflow(
            "task_monitor_1",
            project_id,
            monitor_id=1,
            job_type="full",
            job_id=1,
        ))

    assert result["status"] == "completed"
    assert result["findings"]
    assert result["recommendations"]

    findings = run(storage.get_task_findings("task_monitor_1"))
    recommendations = run(storage.get_task_recommendations("task_monitor_1"))
    latest = run(storage.get_latest_monitoring_summary(project_id))

    assert findings
    assert recommendations
    assert latest is not None
    assert latest["findings_count"] == len(findings)
    assert latest["recommendations_count"] == len(recommendations)
    assert findings[0]["metadata"]["status"] in {"confirmed", "likely", "hypothesis", "environment_limitation"}
    assert "dedupe_key" in findings[0]["metadata"]
    assert isinstance(recommendations[0]["metadata"], dict)


@pytest.mark.asyncio
async def test_collect_signals_surfaces_github_rate_limit_as_warning():
    project_id = await storage.ensure_project("Coze", "https://www.coze.com/", "ai")

    captured: list[dict] = []

    async def capture(_run_id: int, _callback, event: dict) -> None:
        captured.append(event)

    with patch("opencmo.monitoring._emit", side_effect=capture), \
         patch(
             "opencmo.services.github_service.auto_discover_from_product",
             new=AsyncMock(return_value={
                 "discovered": 0,
                 "contactable": 0,
                 "warnings": ["GitHub API rate limit exceeded during repository discovery. Results may be incomplete."],
             }),
         ):
        await _collect_signals(1, project_id, "github", 1, None)

    summaries = [event["summary"] for event in captured if event["stage"] == "signal_collect"]
    assert any("rate limit exceeded" in summary for summary in summaries)
    assert not any("0 found, 0 contactable" in summary for summary in summaries)
    warning = next(event for event in captured if "rate limit exceeded" in event["summary"])
    assert warning["code"] == "github_rate_limit"
    assert warning["kind"] == "source_limit"
    assert warning["blocking"] is False


@pytest.mark.asyncio
async def test_collect_signals_emits_github_success_when_discovery_has_no_warnings():
    project_id = await storage.ensure_project("Coze", "https://www.coze.com/", "ai")

    captured: list[dict] = []

    async def capture(_run_id: int, _callback, event: dict) -> None:
        captured.append(event)

    with patch("opencmo.monitoring._emit", side_effect=capture), \
         patch(
             "opencmo.services.github_service.auto_discover_from_product",
             new=AsyncMock(return_value={"discovered": 3, "contactable": 1, "warnings": []}),
         ):
        await _collect_signals(1, project_id, "github", 1, None)

    summaries = [event["summary"] for event in captured if event["stage"] == "signal_collect"]
    assert "GitHub discovery finished: 3 found, 1 contactable." in summaries
    assert not any("GitHub discovery failed" in summary for summary in summaries)


@pytest.mark.asyncio
async def test_collect_signals_seo_passes_url_to_health_score():
    project_id = await storage.ensure_project("SeoBrand", "https://seo.test", "saas")

    crawler = AsyncMock()
    crawler.__aenter__.return_value = crawler
    crawler.__aexit__.return_value = False
    crawler.arun.return_value = SimpleNamespace(
        html="<html><title>SEO Brand</title></html>",
        markdown="",
        media={},
        links={},
    )

    health_score = None

    def compute_score(*args, **kwargs):
        nonlocal health_score
        health_score = kwargs
        return 88.0

    with patch("crawl4ai.AsyncWebCrawler", return_value=crawler), \
         patch("opencmo.tools.seo_audit._fetch_core_web_vitals", new=AsyncMock(return_value=None)), \
         patch("opencmo.tools.seo_audit._check_robots_and_sitemap", new=AsyncMock(return_value={
             "has_robots": True,
             "robots_disallow_all": False,
             "has_sitemap": True,
             "sitemap_loc_count": 1,
             "sitemap_in_robots": "https://seo.test/sitemap.xml",
         })), \
         patch("opencmo.tools.seo_audit._check_security_headers", new=AsyncMock(return_value={"has_hsts": True, "has_security_headers": True})), \
         patch("opencmo.tools.seo_audit._compute_seo_health_score", side_effect=compute_score), \
         patch("opencmo.tools.serp_tracker.track_project_keywords", new=AsyncMock()), \
         patch("opencmo.monitoring._emit", new=AsyncMock()):
        await _collect_signals(1, project_id, "seo", 1, None)

    assert health_score is not None
    assert health_score["url"] == "https://seo.test"
    history = await storage.get_seo_history(project_id, limit=1)
    assert history[0]["seo_health_score"] == 88.0


@pytest.mark.asyncio
async def test_collect_signals_geo_persists_provider_status_and_success_rate():
    project_id = await storage.ensure_project("GeoBrand", "https://geo.test", "saas")

    ok_provider = SimpleNamespace(
        name="Perplexity",
        is_enabled=True,
        check_visibility_multi=AsyncMock(return_value=SimpleNamespace(
            mentioned=True,
            total_mention_count=2,
            best_position_pct=25,
            source_status="ok",
            error=None,
            per_query_results=[
                SimpleNamespace(
                    content_snippet="GeoBrand is frequently recommended.",
                    source_status="ok",
                ),
            ],
        )),
    )
    failing_provider = SimpleNamespace(
        name="Claude",
        is_enabled=True,
        check_visibility_multi=AsyncMock(side_effect=RuntimeError("provider unavailable")),
    )

    with patch("opencmo.tools.geo_providers.GEO_PROVIDER_REGISTRY", [ok_provider, failing_provider]), \
         patch("opencmo.tools.text_signals.analyze_geo_sentiment", new=AsyncMock(return_value=SimpleNamespace(score=21, label="positive", reasoning="ok"))), \
         patch("opencmo.monitoring._emit", new=AsyncMock()):
        await _collect_signals(1, project_id, "geo", 1, None)

    history = await storage.get_geo_history(project_id, limit=1)
    assert history[0]["crawl_success_rate"] == 0.5
    assert history[0]["geo_score"] == 83
    payload = json.loads(history[0]["platform_results_json"])
    assert payload["Perplexity"]["source_status"] == "ok"
    assert payload["Claude"]["source_status"] == "error"
    assert payload["Claude"]["error"] == "provider unavailable"


@pytest.mark.asyncio
async def test_analysis_enrichment_skips_brand_update_when_identity_exists():
    existing_id = await storage.ensure_project("ActualBrand", "https://same.test", "saas")
    duplicate_id = await storage.ensure_project("Same", "https://same.test", "auto")

    with patch(
        "opencmo.services.intelligence_service.analyze_url_with_ai",
        new=AsyncMock(return_value={
            "brand_name": "ActualBrand",
            "category": "ai",
            "keywords": ["actualbrand monitoring"],
            "competitors": [],
        }),
    ):
        await analyze_and_enrich_project(duplicate_id, "https://same.test")

    existing = await storage.get_project(existing_id)
    duplicate = await storage.get_project(duplicate_id)
    keywords = await storage.list_tracked_keywords(duplicate_id)

    assert existing["brand_name"] == "ActualBrand"
    assert duplicate["brand_name"] == "Same"
    assert duplicate["category"] == "ai"
    assert [item["keyword"] for item in keywords] == ["actualbrand monitoring"]
