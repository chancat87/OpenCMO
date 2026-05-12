"""Tests for the ai_models storage submodule (provider config + quota claim)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from opencmo import storage


@pytest.fixture
def db(tmp_path):
    """Patch storage to use an isolated SQLite database for each test."""
    db_path = tmp_path / "ai_models.db"
    with patch.object(storage, "_DB_PATH", db_path), \
         patch.object(storage, "_SCHEMA_READY_FOR", None):
        yield db_path


# ---------------------------------------------------------------------------
# list_ai_models
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_ai_models_empty(db):
    rows = await storage.list_ai_models()
    assert rows == []


@pytest.mark.asyncio
async def test_list_ai_models_ordered_by_priority_then_id(db):
    id_a = await storage.add_ai_model(
        role="default", name="A", model_id="m-a", failover_priority=200,
    )
    id_b = await storage.add_ai_model(
        role="default", name="B", model_id="m-b", failover_priority=100,
    )
    id_c = await storage.add_ai_model(
        role="default", name="C", model_id="m-c", failover_priority=100,
    )

    rows = await storage.list_ai_models()
    ids = [r["id"] for r in rows]
    # Priority asc: B(100) < C(100) < A(200); tie -> by id ascending
    assert ids == [id_b, id_c, id_a]


@pytest.mark.asyncio
async def test_list_ai_models_filters_by_role_and_enabled(db):
    await storage.add_ai_model(
        role="default", name="A", model_id="m-a", enabled=True,
    )
    await storage.add_ai_model(
        role="default", name="B", model_id="m-b", enabled=False,
    )
    await storage.add_ai_model(
        role="embedding", name="C", model_id="m-c", enabled=True,
    )

    default_rows = await storage.list_ai_models(role="default")
    assert {r["name"] for r in default_rows} == {"A", "B"}

    default_enabled = await storage.list_ai_models(role="default", enabled_only=True)
    assert {r["name"] for r in default_enabled} == {"A"}

    embed_rows = await storage.list_ai_models(role="embedding")
    assert {r["name"] for r in embed_rows} == {"C"}


# ---------------------------------------------------------------------------
# get_ai_model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_ai_model_hit_and_miss(db):
    new_id = await storage.add_ai_model(
        role="default",
        name="Primary",
        model_id="deepseek-chat",
        api_key="sk-test",
        base_url="https://api.deepseek.com",
        failover_priority=10,
        daily_limit=50,
        enabled=True,
    )
    row = await storage.get_ai_model(new_id)
    assert row is not None
    assert row["id"] == new_id
    assert row["name"] == "Primary"
    assert row["model_id"] == "deepseek-chat"
    assert row["api_key"] == "sk-test"
    assert row["base_url"] == "https://api.deepseek.com"
    assert row["failover_priority"] == 10
    assert row["daily_limit"] == 50
    assert row["enabled"] is True
    assert row["used_today"] == 0
    assert row["used_total"] == 0

    missing = await storage.get_ai_model(999_999)
    assert missing is None


# ---------------------------------------------------------------------------
# update_ai_model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_ai_model_individual_fields(db):
    new_id = await storage.add_ai_model(
        role="default", name="orig", model_id="m-1",
    )

    assert await storage.update_ai_model(new_id, name="renamed") is True
    row = await storage.get_ai_model(new_id)
    assert row["name"] == "renamed"

    assert await storage.update_ai_model(new_id, model_id="m-2") is True
    row = await storage.get_ai_model(new_id)
    assert row["model_id"] == "m-2"

    assert await storage.update_ai_model(new_id, api_key="sk-x") is True
    row = await storage.get_ai_model(new_id)
    assert row["api_key"] == "sk-x"

    assert await storage.update_ai_model(new_id, base_url="https://x") is True
    row = await storage.get_ai_model(new_id)
    assert row["base_url"] == "https://x"

    assert await storage.update_ai_model(new_id, role="embedding") is True
    row = await storage.get_ai_model(new_id)
    assert row["role"] == "embedding"

    assert await storage.update_ai_model(new_id, failover_priority=5) is True
    row = await storage.get_ai_model(new_id)
    assert row["failover_priority"] == 5

    assert await storage.update_ai_model(new_id, daily_limit=42) is True
    row = await storage.get_ai_model(new_id)
    assert row["daily_limit"] == 42

    assert await storage.update_ai_model(new_id, enabled=False) is True
    row = await storage.get_ai_model(new_id)
    assert row["enabled"] is False


@pytest.mark.asyncio
async def test_update_ai_model_missing_id_returns_false(db):
    assert await storage.update_ai_model(123456, name="ghost") is False


@pytest.mark.asyncio
async def test_update_ai_model_ignores_unknown_fields(db):
    new_id = await storage.add_ai_model(
        role="default", name="orig", model_id="m-1",
    )
    # No allowed fields -> returns False (nothing to update).
    assert await storage.update_ai_model(new_id, used_total=999) is False
    row = await storage.get_ai_model(new_id)
    assert row["used_total"] == 0


# ---------------------------------------------------------------------------
# delete_ai_model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_ai_model_hit_and_miss(db):
    new_id = await storage.add_ai_model(
        role="default", name="A", model_id="m-a",
    )
    assert await storage.delete_ai_model(new_id) is True
    assert await storage.get_ai_model(new_id) is None
    # Second delete of same id is a miss.
    assert await storage.delete_ai_model(new_id) is False
    assert await storage.delete_ai_model(987654) is False


# ---------------------------------------------------------------------------
# claim_quota
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_claim_quota_unlimited(db):
    new_id = await storage.add_ai_model(
        role="default", name="A", model_id="m-a", daily_limit=0,
    )
    for expected in (1, 2, 3, 4, 5):
        assert await storage.claim_quota(new_id) is True
        row = await storage.get_ai_model(new_id)
        assert row["used_today"] == expected
        assert row["used_total"] == expected


@pytest.mark.asyncio
async def test_claim_quota_respects_daily_limit(db):
    new_id = await storage.add_ai_model(
        role="default", name="A", model_id="m-a", daily_limit=3,
    )
    assert await storage.claim_quota(new_id) is True
    assert await storage.claim_quota(new_id) is True
    assert await storage.claim_quota(new_id) is True
    # 4th attempt blocked
    assert await storage.claim_quota(new_id) is False
    row = await storage.get_ai_model(new_id)
    assert row["used_today"] == 3
    assert row["used_total"] == 3


@pytest.mark.asyncio
async def test_claim_quota_resets_after_rolling_24h(db):
    new_id = await storage.add_ai_model(
        role="default", name="A", model_id="m-a", daily_limit=2,
    )
    # Fill the daily quota.
    assert await storage.claim_quota(new_id) is True
    assert await storage.claim_quota(new_id) is True
    assert await storage.claim_quota(new_id) is False

    # Backdate last_reset_at so the rolling window has elapsed.
    raw = await storage.get_db()
    try:
        await raw.execute(
            "UPDATE ai_models SET last_reset_at = '2020-01-01 00:00:00' WHERE id = ?",
            (new_id,),
        )
        await raw.commit()
    finally:
        await raw.close()

    # Next claim must reset used_today to 1 and succeed.
    assert await storage.claim_quota(new_id) is True
    row = await storage.get_ai_model(new_id)
    assert row["used_today"] == 1


@pytest.mark.asyncio
async def test_claim_quota_disabled_returns_false(db):
    new_id = await storage.add_ai_model(
        role="default", name="A", model_id="m-a", enabled=False,
    )
    assert await storage.claim_quota(new_id) is False
    row = await storage.get_ai_model(new_id)
    assert row["used_today"] == 0
    assert row["used_total"] == 0


@pytest.mark.asyncio
async def test_claim_quota_unknown_id_returns_false(db):
    assert await storage.claim_quota(424242) is False
