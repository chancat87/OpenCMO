"""Tests for the AI CMO report system."""

import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opencmo import service, storage
from opencmo.reports import _classify_findings


@pytest.fixture(autouse=True)
def _db(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        yield


def run(coro):
    return asyncio.run(coro)


async def _seed_project():
    project_id = await storage.ensure_project("Acme", "https://acme.test", "saas")
    await storage.add_tracked_keyword(project_id, "acme ai")
    competitor_id = await storage.add_competitor(project_id, "CompetitorX", url="https://comp.test")
    await storage.add_competitor_keyword(competitor_id, "competitor keyword")
    await storage.save_seo_scan(
        project_id,
        "https://acme.test",
        "{}",
        score_performance=0.82,
        score_lcp=2100,
        score_cls=0.03,
        score_tbt=180,
        has_robots_txt=True,
        has_sitemap=True,
        has_schema_org=True,
    )
    await storage.save_geo_scan(
        project_id,
        74,
        visibility_score=28,
        position_score=31,
        sentiment_score=15,
        platform_results_json='{"chatgpt": {"mentioned": true}}',
    )
    await storage.save_community_scan(project_id, 4, '{"hits": []}')
    await storage.save_serp_snapshot(project_id, "acme ai", 5, "https://acme.test", "mock", None)
    return project_id


@pytest.mark.asyncio
async def test_report_version_history_tracks_latest_per_kind_and_audience():
    project_id = await _seed_project()

    first = await storage.create_report_bundle(
        project_id=project_id,
        kind="strategic",
        source_run_id=None,
        window_start=None,
        window_end=None,
        records={
            "human": {
                "generation_status": "completed",
                "content": "human v1",
                "content_html": "<p>human v1</p>",
                "meta": {"sample_count": 1},
            },
            "agent": {
                "generation_status": "completed",
                "content": "agent v1",
                "content_html": "<p>agent v1</p>",
                "meta": {"sample_count": 1},
            },
        },
    )
    second = await storage.create_report_bundle(
        project_id=project_id,
        kind="strategic",
        source_run_id=None,
        window_start=None,
        window_end=None,
        records={
            "human": {
                "generation_status": "completed",
                "content": "human v2",
                "content_html": "<p>human v2</p>",
                "meta": {"sample_count": 2},
            },
            "agent": {
                "generation_status": "completed",
                "content": "agent v2",
                "content_html": "<p>agent v2</p>",
                "meta": {"sample_count": 2},
            },
        },
    )

    assert all(item["version"] == 1 for item in first)
    assert all(item["version"] == 2 for item in second)

    latest = await storage.get_latest_reports(project_id)
    assert latest["strategic"]["human"]["content"] == "human v2"
    assert latest["strategic"]["agent"]["content"] == "agent v2"

    history = await storage.list_reports(project_id, kind="strategic", audience="human")
    assert [item["version"] for item in history] == [2, 1]
    assert history[0]["is_latest"] is True
    assert history[1]["is_latest"] is False


@pytest.mark.asyncio
async def test_report_latest_is_scoped_by_locale():
    project_id = await _seed_project()

    zh = await storage.create_report_bundle(
        project_id=project_id,
        kind="strategic",
        locale="zh",
        source_run_id=None,
        window_start=None,
        window_end=None,
        records={
            "human": {
                "generation_status": "completed",
                "content": "中文报告",
                "content_html": "<p>中文报告</p>",
                "meta": {},
            },
        },
    )
    en = await storage.create_report_bundle(
        project_id=project_id,
        kind="strategic",
        locale="en",
        source_run_id=None,
        window_start=None,
        window_end=None,
        records={
            "human": {
                "generation_status": "completed",
                "content": "English report",
                "content_html": "<p>English report</p>",
                "meta": {},
            },
        },
    )

    assert zh[0]["version"] == 1
    assert en[0]["version"] == 1
    assert (await storage.get_latest_reports(project_id, locale="zh"))["strategic"]["human"]["content"] == "中文报告"
    assert (await storage.get_latest_reports(project_id, locale="en"))["strategic"]["human"]["content"] == "English report"


@pytest.mark.asyncio
async def test_failed_bundle_does_not_replace_latest_completed_report():
    project_id = await _seed_project()

    await storage.create_report_bundle(
        project_id=project_id,
        kind="strategic",
        source_run_id=None,
        window_start=None,
        window_end=None,
        records={
            "human": {
                "generation_status": "completed",
                "content": "human ok",
                "content_html": "<p>human ok</p>",
                "meta": {},
            },
            "agent": {
                "generation_status": "completed",
                "content": "agent ok",
                "content_html": "<p>agent ok</p>",
                "meta": {},
            },
        },
    )

    failed = await storage.create_report_bundle(
        project_id=project_id,
        kind="strategic",
        source_run_id=None,
        window_start=None,
        window_end=None,
        records={
            "human": {
                "generation_status": "failed",
                "content": "",
                "content_html": "",
                "meta": {"llm_error": "LLM unavailable"},
            },
            "agent": {
                "generation_status": "failed",
                "content": "",
                "content_html": "",
                "meta": {"llm_error": "LLM unavailable"},
            },
        },
    )

    latest = await storage.get_latest_reports(project_id)
    assert latest["strategic"]["human"]["content"] == "human ok"
    assert latest["strategic"]["agent"]["content"] == "agent ok"
    assert all(item["is_latest"] is False for item in failed)

    history = await storage.list_reports(project_id, kind="strategic", audience="human")
    assert [item["version"] for item in history] == [2, 1]
    assert history[0]["generation_status"] == "failed"
    assert history[0]["is_latest"] is False
    assert history[1]["is_latest"] is True


@pytest.mark.asyncio
async def test_generate_strategic_report_bundle_creates_human_and_agent_versions():
    project_id = await _seed_project()

    # Human now goes through the pipeline; agent uses single-call
    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        mock_pipeline.side_effect = [
            "# Strategic Human\n\n## 当前优势\n- 好",
            "# Strategic Human v2\n\n## 最近变化摘要\n- GEO up",
        ]
        mock_llm.side_effect = [
            "# Strategic Agent\n\n- objective: expand visibility",
            "# Strategic Agent v2\n\n- objective: defend gains",
        ]

        first = await service.regenerate_project_report(project_id, "strategic")
        second = await service.regenerate_project_report(project_id, "strategic")

    assert first["kind"] == "strategic"
    assert first["human"]["version"] == 1
    assert first["agent"]["version"] == 1
    assert "当前优势" in first["human"]["content"]
    assert first["human"]["meta"]["used_pipeline"] is True

    assert second["human"]["version"] == 2
    assert second["agent"]["version"] == 2
    assert "最近变化摘要" in second["human"]["content"]


@pytest.mark.asyncio
async def test_generate_periodic_report_bundle_marks_sparse_samples():
    project_id = await storage.ensure_project("Sparse", "https://sparse.test", "saas")
    await storage.save_geo_scan(
        project_id,
        33,
        visibility_score=10,
        position_score=12,
        sentiment_score=11,
        platform_results_json='{}',
    )

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        mock_pipeline.return_value = "# Weekly Human\n\n样本稀疏"
        mock_llm.return_value = "# Weekly Agent\n\nsample_count: 1"
        report = await service.regenerate_project_report(project_id, "periodic")

    assert report["kind"] == "periodic"
    assert report["human"]["version"] == 1
    assert report["human"]["meta"]["sample_count"] == 1
    assert report["human"]["meta"]["low_sample"] is True
    assert "样本稀疏" in report["human"]["content"]
    assert mock_pipeline.await_count == 1  # human via pipeline
    assert mock_llm.await_count == 1       # agent via single-call


@pytest.mark.asyncio
async def test_periodic_facts_filters_windowed_sources_and_exposes_pipeline_aliases():
    from opencmo.reports import _build_periodic_facts

    now = datetime(2026, 5, 10, 12, 0, 0)
    fresh = "2026-05-09T12:00:00"
    stale = "2026-04-20T12:00:00"
    future = "2026-05-11T12:00:00"
    project = {"id": 99, "brand_name": "Windowed", "category": "saas", "url": "https://windowed.test"}

    with patch("opencmo.reports.storage.get_project", AsyncMock(return_value=project)), \
         patch("opencmo.reports.storage.list_tracked_keywords", AsyncMock(return_value=[{"keyword": "windowed"}])), \
         patch("opencmo.reports.storage.get_seo_history", AsyncMock(return_value=[
             {"scanned_at": future, "score_performance": 0.9},
             {"scanned_at": fresh, "score_performance": 0.8},
             {"scanned_at": stale, "score_performance": 0.5},
         ])), \
         patch("opencmo.reports.storage.get_geo_history", AsyncMock(return_value=[
             {"scanned_at": fresh, "geo_score": 60},
             {"scanned_at": stale, "geo_score": 40},
         ])), \
         patch("opencmo.reports.storage.get_community_history", AsyncMock(return_value=[
             {"scanned_at": fresh, "total_hits": 7},
             {"scanned_at": stale, "total_hits": 2},
         ])), \
         patch("opencmo.reports.storage.get_tracked_discussions", AsyncMock(return_value=[
             {"last_checked_at": fresh, "title": "fresh discussion"},
             {"last_checked_at": stale, "title": "stale discussion"},
         ])), \
         patch("opencmo.reports._get_recent_approvals", AsyncMock(return_value=[])), \
         patch("opencmo.reports._get_recent_recommendations", AsyncMock(return_value=[])), \
         patch("opencmo.reports._get_recent_findings", AsyncMock(return_value=[])), \
         patch("opencmo.reports.storage.get_all_serp_latest", AsyncMock(return_value=[
             {"checked_at": fresh, "keyword": "fresh serp"},
             {"checked_at": stale, "keyword": "stale serp"},
         ])), \
         patch("opencmo.reports.storage.list_insights", AsyncMock(return_value=[
             {"created_at": fresh, "title": "fresh insight"},
             {"created_at": stale, "title": "stale insight"},
         ])), \
         patch("opencmo.reports.storage.get_citability_history", AsyncMock(return_value=[
             {"scanned_at": fresh, "avg_score": 0.7},
             {"scanned_at": stale, "avg_score": 0.3},
         ])), \
         patch("opencmo.reports.storage.get_ai_crawler_history", AsyncMock(return_value=[
             {"scanned_at": fresh, "blocked_count": 1},
             {"scanned_at": stale, "blocked_count": 8},
         ])), \
         patch("opencmo.reports.storage.get_brand_presence_history", AsyncMock(return_value=[
             {"scanned_at": fresh, "footprint_score": 50},
             {"scanned_at": stale, "footprint_score": 10},
         ])), \
         patch("opencmo.reports.build_project_opportunity_snapshot", AsyncMock(return_value={
             "opportunities": [],
             "cluster_summary": {},
         })):
        facts, meta = await _build_periodic_facts(99, now=now, window_days=7)

    assert [item["scanned_at"] for item in facts["seo_history"]] == [fresh]
    assert facts["geo_history"] == [{"scanned_at": fresh, "geo_score": 60}]
    assert facts["community_history"] == [{"scanned_at": fresh, "total_hits": 7}]
    assert [item["title"] for item in facts["discussions"]] == ["fresh discussion"]
    assert [item["keyword"] for item in facts["serp_latest"]] == ["fresh serp"]
    assert [item["title"] for item in facts["insights"]] == ["fresh insight"]
    assert facts["citability"] == [{"scanned_at": fresh, "avg_score": 0.7}]
    assert facts["ai_crawler"] == [{"scanned_at": fresh, "blocked_count": 1}]
    assert facts["brand_presence"] == [{"scanned_at": fresh, "footprint_score": 50}]
    assert facts["seo_latest"] == facts["seo_history"][0]
    assert facts["geo_latest"] == facts["geo_history"][0]
    assert facts["community_latest"] == facts["community_history"][0]
    assert facts["serp_snapshots"] == facts["serp_latest"]
    assert facts["insights_history"] == facts["insights"]
    assert meta["sample_count"] == 8


@pytest.mark.asyncio
async def test_recent_findings_and_recommendations_respect_window():
    from opencmo.reports import _get_recent_findings, _get_recent_recommendations

    project_id = await storage.ensure_project("Window DB", "https://window-db.test", "saas")
    run_id = await storage.create_scan_run("window-db-run", None, project_id, "full")
    await storage.replace_scan_artifacts(
        run_id,
        findings=[
            {"domain": "seo", "severity": "critical", "title": "fresh finding", "summary": "fresh"},
            {"domain": "seo", "severity": "warning", "title": "stale finding", "summary": "stale"},
        ],
        recommendations=[
            {
                "domain": "seo",
                "priority": "high",
                "owner_type": "engineering",
                "action_type": "fix",
                "title": "fresh rec",
                "summary": "fresh",
                "rationale": "fresh",
            },
            {
                "domain": "seo",
                "priority": "medium",
                "owner_type": "engineering",
                "action_type": "fix",
                "title": "stale rec",
                "summary": "stale",
                "rationale": "stale",
            },
        ],
    )
    db = await storage.get_db()
    try:
        await db.execute(
            "UPDATE scan_findings SET created_at = CASE title WHEN 'fresh finding' THEN ? ELSE ? END WHERE run_id = ?",
            ("2026-05-09T12:00:00", "2026-04-20T12:00:00", run_id),
        )
        await db.execute(
            "UPDATE scan_recommendations SET created_at = CASE title WHEN 'fresh rec' THEN ? ELSE ? END WHERE run_id = ?",
            ("2026-05-09T12:00:00", "2026-04-20T12:00:00", run_id),
        )
        await db.commit()
    finally:
        await db.close()

    start = datetime(2026, 5, 1, 0, 0, 0)
    end = datetime(2026, 5, 10, 0, 0, 0)
    findings = await _get_recent_findings(project_id, limit=10, start=start, end=end)
    recommendations = await _get_recent_recommendations(project_id, limit=10, start=start, end=end)

    assert [item["title"] for item in findings] == ["fresh finding"]
    assert [item["title"] for item in recommendations] == ["fresh rec"]


@pytest.mark.asyncio
async def test_send_project_report_reuses_latest_periodic_human_report(monkeypatch):
    project_id = await _seed_project()
    monkeypatch.setenv("OPENCMO_SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("OPENCMO_SMTP_PORT", "587")
    monkeypatch.setenv("OPENCMO_SMTP_USER", "user@test.com")
    monkeypatch.setenv("OPENCMO_SMTP_PASS", "pass")
    monkeypatch.setenv("OPENCMO_REPORT_EMAIL", "report@test.com")

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        mock_pipeline.return_value = "# Weekly Human\n\n重要变化"
        mock_llm.return_value = "# Weekly Agent\n\nbrief"
        await service.regenerate_project_report(project_id, "periodic")

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = await service.send_project_report(project_id)

    assert result["ok"] is True
    sent_message = mock_server.send_message.call_args[0][0]
    assert "Weekly Human" in sent_message.as_string()


@pytest.mark.asyncio
async def test_generate_report_uses_persisted_llm_settings(monkeypatch):
    project_id = await _seed_project()
    await storage.set_setting("OPENAI_API_KEY", "persisted-key")
    await storage.set_setting("OPENAI_BASE_URL", "https://example.test/v1")
    await storage.set_setting("OPENCMO_MODEL_DEFAULT", "provider-model")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENCMO_MODEL_DEFAULT", raising=False)

    def fake_response(text: str):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
        )

    fake_create = AsyncMock(
        side_effect=[
            # Pipeline internally calls _generate_llm_markdown multiple times,
            # but we mock the pipeline itself for the human report.
            fake_response("# Agent brief"),
        ]
    )
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=fake_create),
        )
    )

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("openai.AsyncOpenAI", return_value=fake_client) as mock_client:
        mock_pipeline.return_value = "# Human report via pipeline"
        report = await service.regenerate_project_report(project_id, "strategic")

    assert report["human"]["meta"]["used_fallback"] is False
    assert report["human"]["meta"]["used_pipeline"] is True
    assert report["human"]["meta"]["model"] == "provider-model"
    # Agent brief uses _generate_llm_markdown → openai client
    assert mock_client.call_count == 1
    for call in mock_client.call_args_list:
        assert call.kwargs == {
            "api_key": "persisted-key",
            "base_url": "https://example.test/v1",
        }
    assert fake_create.await_count == 1
    assert all(call.kwargs["model"] == "provider-model" for call in fake_create.await_args_list)


@pytest.mark.asyncio
async def test_generate_report_marks_failed_when_all_generation_paths_fail():
    project_id = await _seed_project()

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        mock_pipeline.side_effect = RuntimeError("Pipeline exploded")
        mock_llm.side_effect = RuntimeError("LLM unavailable")

        report = await service.regenerate_project_report(project_id, "strategic")

    assert report["human"]["generation_status"] == "failed"
    assert report["human"]["content"] == ""
    assert report["human"]["content_html"] == ""
    assert report["human"]["meta"]["used_pipeline"] is False
    assert report["human"]["meta"]["used_fallback"] is False
    assert "LLM unavailable" in str(report["human"]["meta"].get("llm_error"))
    assert report["agent"]["generation_status"] == "failed"
    assert report["agent"]["content"] == ""
    latest = await storage.get_latest_reports(project_id)
    assert latest["strategic"]["human"] is None
    assert latest["strategic"]["agent"] is None


@pytest.mark.asyncio
async def test_generate_report_retries_empty_content_on_same_model():
    project_id = await _seed_project()

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._get_report_model", new_callable=AsyncMock, return_value="gpt-5.4"), \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        mock_pipeline.side_effect = RuntimeError("Pipeline exploded")
        mock_llm.side_effect = ["", "# Same-model retry report", "# Agent brief"]

        report = await service.regenerate_project_report(project_id, "strategic")

    assert report["human"]["generation_status"] == "completed"
    assert "Same-model retry report" in report["human"]["content"]
    assert report["human"]["meta"]["used_fallback"] is True
    assert report["human"]["meta"]["model"] == "gpt-5.4"
    assert mock_llm.await_count == 3


def test_classify_findings_separates_verified_hypothesis_and_environment():
    validated, environment, hypotheses = _classify_findings([
        {"title": "Verified", "metadata": {"status": "confirmed"}},
        {"title": "Maybe", "metadata": {"status": "hypothesis"}},
        {"title": "Timeout", "metadata": {"status": "environment_limitation"}},
    ])

    assert [item["title"] for item in validated] == ["Verified"]
    assert [item["title"] for item in environment] == ["Timeout"]
    assert [item["title"] for item in hypotheses] == ["Maybe"]

def test_strategic_agent_prompt_avoids_nonexistent_cli_contracts():
    from opencmo.reports import _prompts

    facts = {
        "project": {
            "brand_name": "Acme",
            "category": "saas",
            "url": "https://acme.test",
        }
    }
    meta = {"sample_count": 3, "total_data_sources": 8}

    system, user = _prompts("strategic", "agent", facts, meta, previous_exists=False)

    assert "Task X.Y" not in system
    assert "opencmo seo setup --project=X" not in system
    assert "opencmo health check --module=seo" not in system
    assert "Google Search Console、Ahrefs" not in system
    assert user.startswith("项目战略事实包：")


def test_report_prompt_fragments_preserve_truth_rules_across_audiences():
    from opencmo.reports import _prompts

    facts = {
        "project": {
            "brand_name": "Acme",
            "category": "saas",
            "url": "https://acme.test",
        }
    }
    meta = {"sample_count": 1, "total_data_sources": 8}

    human_system, _ = _prompts("strategic", "human", facts, meta, previous_exists=False)
    agent_system, _ = _prompts("strategic", "agent", facts, meta, previous_exists=False)

    assert "第一个一级章节必须是 `## 先说结论`" in human_system
    assert "第二个一级章节必须是 `## 目录`" in human_system
    assert "必须放在 `## 目录` 后" in human_system

    for prompt in (human_system, agent_system):
        assert "事实 / 推断 / 建议" in prompt
        assert "缺失时必须明确标注" in prompt
        assert "不得补造数字" in prompt


def test_human_report_prompt_uses_locale_specific_structure_labels():
    from opencmo.reports import _prompts

    facts = {
        "project": {
            "brand_name": "Acme",
            "category": "saas",
            "url": "https://acme.test",
        }
    }
    meta = {"sample_count": 1, "total_data_sources": 8}

    system, _ = _prompts("strategic", "human", facts, meta, previous_exists=False, locale="en")

    assert "第一个一级章节必须是 `## Bottom Line`" in system
    assert "第二个一级章节必须是 `## Table of Contents`" in system
    assert "必须包含 `## Charts at a Glance`" in system
    assert "## 先说结论" not in system


def test_report_prompt_distinguishes_facts_from_recommendations_when_data_is_sparse():
    from opencmo.reports import _prompts

    facts = {
        "project": {
            "brand_name": "Acme",
            "category": "saas",
            "url": "https://acme.test",
        }
    }
    meta = {"sample_count": 1, "total_data_sources": 8}

    system, _ = _prompts("periodic", "human", facts, meta, previous_exists=False)

    assert "先写已确认事实，再写推断，最后写建议" in system
    assert "样本稀疏时" in system
    assert "第一个一级章节必须是 `## 先说结论`" in system
    assert "第二个一级章节必须是 `## 目录`" in system
