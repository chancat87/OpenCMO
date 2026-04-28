"""Tests for the cached /api/v1/github-stats logic.

L1 = in-process memory dict
L2 = SQLite github_stats_cache
Single-flight lock prevents thundering herd on cold start.

We mock at the ``github_get_with_headers`` boundary, not httpx — the
upstream wrapper itself is exercised by github_api integration tests
that already exist.
"""
from __future__ import annotations

import asyncio

import pytest

from opencmo.web import github_stats as gs_module


def _setup_db(tmp_path, monkeypatch):
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    monkeypatch.setattr(storage, "_SCHEMA_READY_FOR", None, raising=False)


def _reset_caches():
    gs_module._mem_cache.clear()


def _stub_repo_response():
    return {
        "stargazers_count": 73,
        "pushed_at": "2026-04-25T00:00:00Z",
        "forks_count": 5,
    }


@pytest.fixture(autouse=True)
def _clear_state():
    _reset_caches()
    yield
    _reset_caches()


@pytest.mark.asyncio
async def test_cold_path_fetches_and_writes_both_layers(tmp_path, monkeypatch):
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    calls = {"repo": 0, "contrib": 0}

    async def fake_get(path, params=None):
        if "contributors" in path:
            calls["contrib"] += 1
            return ([], {"Link": '</repos/x/contributors?per_page=1&page=4>; rel="last"'})
        calls["repo"] += 1
        return (_stub_repo_response(), {})

    monkeypatch.setattr(gs_module, "github_get_with_headers", fake_get)

    stats = await gs_module.get_github_stats()
    assert stats["stars"] == 73
    assert stats["contributors"] == 4
    assert stats["last_commit_iso"] == "2026-04-25T00:00:00Z"
    assert stats["fetched_at"] is not None
    assert calls == {"repo": 1, "contrib": 1}

    # L1 hit — second call should not invoke fake_get
    stats2 = await gs_module.get_github_stats()
    assert stats2 == stats
    assert calls == {"repo": 1, "contrib": 1}

    # L2 also written (clear L1 + verify SQLite has it)
    _reset_caches()
    sqlite_cached = await storage.get_cached_github_stats(gs_module._CACHE_KEY, gs_module._CACHE_TTL_SEC)
    assert sqlite_cached is not None
    assert sqlite_cached["stars"] == 73


@pytest.mark.asyncio
async def test_l2_sqlite_cache_hit_after_restart(tmp_path, monkeypatch):
    """Simulate process restart by clearing L1 only, verify L2 fills it."""
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    calls = {"count": 0}

    async def fake_get(path, params=None):
        calls["count"] += 1
        if "contributors" in path:
            return ([], {})
        return (_stub_repo_response(), {})

    monkeypatch.setattr(gs_module, "github_get_with_headers", fake_get)

    # First call: cold path, hits fake_get twice (repo + contrib)
    await gs_module.get_github_stats()
    assert calls["count"] == 2

    # "Restart" — clear L1 only
    _reset_caches()

    # Second call: L1 miss → L2 hit → no further fake_get calls
    stats = await gs_module.get_github_stats()
    assert stats["stars"] == 73
    assert calls["count"] == 2  # unchanged


@pytest.mark.asyncio
async def test_partial_failure_returns_nulls_and_does_not_cache(tmp_path, monkeypatch):
    """If contributors fails but repo succeeds, plan says return all-null
    AND not cache. (Don't poison the 24h window.)"""
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    async def fake_get(path, params=None):
        if "contributors" in path:
            return (None, {})  # contributor fetch fails
        return (_stub_repo_response(), {})

    monkeypatch.setattr(gs_module, "github_get_with_headers", fake_get)

    stats = await gs_module.get_github_stats()
    assert stats == {"stars": None, "contributors": None, "last_commit_iso": None, "fetched_at": None}

    # Neither L1 nor L2 should have been written
    assert gs_module._mem_cache.get(gs_module._CACHE_KEY) is None
    sqlite_cached = await storage.get_cached_github_stats(gs_module._CACHE_KEY, gs_module._CACHE_TTL_SEC)
    assert sqlite_cached is None


@pytest.mark.asyncio
async def test_full_failure_returns_nulls(tmp_path, monkeypatch):
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    async def fake_get(path, params=None):
        return (None, {})

    monkeypatch.setattr(gs_module, "github_get_with_headers", fake_get)
    stats = await gs_module.get_github_stats()
    assert all(v is None for v in stats.values())


@pytest.mark.asyncio
async def test_contributor_count_no_link_header(tmp_path, monkeypatch):
    """Single page response (≤ per_page contributors) — len fallback."""
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    async def fake_get(path, params=None):
        if "contributors" in path:
            return ([{"login": "alice"}, {"login": "bob"}], {})  # no Link header
        return (_stub_repo_response(), {})

    monkeypatch.setattr(gs_module, "github_get_with_headers", fake_get)
    stats = await gs_module.get_github_stats()
    assert stats["contributors"] == 2


@pytest.mark.asyncio
async def test_contributor_count_with_link_header(tmp_path, monkeypatch):
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    async def fake_get(path, params=None):
        if "contributors" in path:
            link = (
                '<https://api.github.com/repositories/1/contributors?page=2&per_page=1>; rel="next", '
                '<https://api.github.com/repositories/1/contributors?page=42&per_page=1>; rel="last"'
            )
            return ([{"login": "alice"}], {"Link": link})
        return (_stub_repo_response(), {})

    monkeypatch.setattr(gs_module, "github_get_with_headers", fake_get)
    stats = await gs_module.get_github_stats()
    assert stats["contributors"] == 42


@pytest.mark.asyncio
async def test_contributor_count_zero(tmp_path, monkeypatch):
    """Empty contributors list → 0."""
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    async def fake_get(path, params=None):
        if "contributors" in path:
            return ([], {})  # no Link
        return (_stub_repo_response(), {})

    monkeypatch.setattr(gs_module, "github_get_with_headers", fake_get)
    stats = await gs_module.get_github_stats()
    # 0 contributors but repo succeeded — but our spec says any null returns _empty_stats
    # Wait: contrib=0 is not None, so this is success path with stars=73, contrib=0
    assert stats["stars"] == 73
    assert stats["contributors"] == 0


@pytest.mark.asyncio
async def test_single_flight_lock(tmp_path, monkeypatch):
    """5 concurrent cold-start requests → only one fetch."""
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    calls = {"count": 0}
    started = asyncio.Event()
    proceed = asyncio.Event()

    async def slow_get(path, params=None):
        calls["count"] += 1
        started.set()
        await proceed.wait()  # block first call until others have queued
        if "contributors" in path:
            return ([], {})
        return (_stub_repo_response(), {})

    monkeypatch.setattr(gs_module, "github_get_with_headers", slow_get)

    # Kick off 5 concurrent calls
    tasks = [asyncio.create_task(gs_module.get_github_stats()) for _ in range(5)]

    # Wait for one to start, give others time to queue on the lock
    await started.wait()
    await asyncio.sleep(0.05)
    proceed.set()

    results = await asyncio.gather(*tasks)
    # First call did the work (2 inner calls = repo + contributors).
    # All other callers should see the L1 cache and skip fetching.
    assert calls["count"] == 2
    assert all(r["stars"] == 73 for r in results)


@pytest.mark.asyncio
async def test_endpoint_returns_200(tmp_path, monkeypatch):
    """Smoke: /api/v1/github-stats endpoint reachable + 200."""
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    async def fake_get(path, params=None):
        if "contributors" in path:
            link = '<https://api.github.com/repositories/1/contributors?per_page=1&page=4>; rel="last"'
            return ([{"login": "alice"}], {"Link": link})
        return (_stub_repo_response(), {})

    monkeypatch.setattr(gs_module, "github_get_with_headers", fake_get)

    from fastapi.testclient import TestClient
    from opencmo.web.app import app

    with TestClient(app) as client:
        r = client.get("/api/v1/github-stats")
        assert r.status_code == 200
        body = r.json()
        assert body["stars"] == 73
        assert body["contributors"] == 4
