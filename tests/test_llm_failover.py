"""Tests for chat_completion_with_failover — multi-model fallback orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from opencmo import llm, storage


@pytest.fixture
def db(tmp_path):
    """Patch storage to use an isolated SQLite database for each test."""
    db_path = tmp_path / "failover.db"
    with patch.object(storage, "_DB_PATH", db_path), \
         patch.object(storage, "_SCHEMA_READY_FOR", None):
        yield db_path


# ---------------------------------------------------------------------------
# No registered models -> falls back to single-model chat_completion_messages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_models_falls_back_to_chat_completion_messages(db):
    mock_completion = AsyncMock(return_value="legacy-output")
    with patch.object(llm, "chat_completion_messages", mock_completion):
        result = await llm.chat_completion_with_failover(
            "default", system="hi", user="hello",
        )
    assert result == "legacy-output"
    mock_completion.assert_awaited_once()
    call = mock_completion.await_args
    passed_messages = call.kwargs.get("messages") or (call.args[0] if call.args else None)
    assert passed_messages is not None
    assert passed_messages[0]["content"] == "hi"
    assert passed_messages[1]["content"] == "hello"
    assert call.kwargs.get("model_override") is None
    assert call.kwargs.get("api_key_override") is None


# ---------------------------------------------------------------------------
# Single model success
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_model_success(db):
    model_pk = await storage.add_ai_model(
        role="default", name="Primary", model_id="primary-model",
        api_key="sk-primary", base_url="https://primary.example.com",
        failover_priority=10,
    )

    mock_completion = AsyncMock(return_value="primary-output")
    with patch.object(llm, "chat_completion_messages", mock_completion):
        result = await llm.chat_completion_with_failover(
            "default", messages=[{"role": "user", "content": "x"}],
        )

    assert result == "primary-output"
    mock_completion.assert_awaited_once()
    call = mock_completion.await_args
    assert call.kwargs["model_override"] == "primary-model"
    assert call.kwargs["api_key_override"] == "sk-primary"
    assert call.kwargs["base_url_override"] == "https://primary.example.com"

    # quota was consumed
    row = await storage.get_ai_model(model_pk)
    assert row["used_today"] == 1


# ---------------------------------------------------------------------------
# Two models — first fails, second succeeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_failover_to_second_model_on_exception(db):
    primary_pk = await storage.add_ai_model(
        role="default", name="Primary", model_id="primary-model",
        api_key="sk-primary", failover_priority=10,
    )
    backup_pk = await storage.add_ai_model(
        role="default", name="Backup", model_id="backup-model",
        api_key="sk-backup", failover_priority=20,
    )

    call_count = {"n": 0}

    async def fake_completion(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("provider 1 failed")
        return "backup-output"

    with patch.object(llm, "chat_completion_messages", side_effect=fake_completion):
        result = await llm.chat_completion_with_failover(
            "default", system="s", user="u",
        )

    assert result == "backup-output"
    assert call_count["n"] == 2

    primary_row = await storage.get_ai_model(primary_pk)
    backup_row = await storage.get_ai_model(backup_pk)
    assert primary_row["used_today"] == 1
    assert backup_row["used_today"] == 1


# ---------------------------------------------------------------------------
# Both models raise -> the last exception propagates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_models_fail_raises_last_exception(db):
    await storage.add_ai_model(
        role="default", name="A", model_id="m-a", failover_priority=10,
    )
    await storage.add_ai_model(
        role="default", name="B", model_id="m-b", failover_priority=20,
    )

    call_count = {"n": 0}

    async def fake_completion(*args, **kwargs):
        call_count["n"] += 1
        raise RuntimeError(f"failure-{call_count['n']}")

    with patch.object(llm, "chat_completion_messages", side_effect=fake_completion):
        with pytest.raises(RuntimeError, match="failure-2"):
            await llm.chat_completion_with_failover(
                "default", system="s", user="u",
            )
    assert call_count["n"] == 2


# ---------------------------------------------------------------------------
# Quota exhausted on first model -> skip to second
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_skip_model_at_quota_limit(db):
    primary_pk = await storage.add_ai_model(
        role="default", name="Primary", model_id="m-primary",
        failover_priority=10, daily_limit=1,
    )
    backup_pk = await storage.add_ai_model(
        role="default", name="Backup", model_id="m-backup",
        failover_priority=20, daily_limit=0,
    )
    # Burn primary's only quota.
    assert await storage.claim_quota(primary_pk) is True

    mock_completion = AsyncMock(return_value="backup-output")
    with patch.object(llm, "chat_completion_messages", mock_completion):
        result = await llm.chat_completion_with_failover(
            "default", system="s", user="u",
        )

    assert result == "backup-output"
    mock_completion.assert_awaited_once()
    call = mock_completion.await_args
    assert call.kwargs["model_override"] == "m-backup"

    primary_row = await storage.get_ai_model(primary_pk)
    backup_row = await storage.get_ai_model(backup_pk)
    assert primary_row["used_today"] == 1  # unchanged, claim rejected
    assert backup_row["used_today"] == 1


# ---------------------------------------------------------------------------
# All models skipped on quota -> RuntimeError, no LLM call made
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_models_skipped_raises_runtime_error(db):
    only_pk = await storage.add_ai_model(
        role="default", name="Only", model_id="m-only",
        failover_priority=10, daily_limit=1,
    )
    assert await storage.claim_quota(only_pk) is True

    mock_completion = AsyncMock(return_value="should-not-run")
    with patch.object(llm, "chat_completion_messages", mock_completion):
        with pytest.raises(RuntimeError, match="daily quota exhausted"):
            await llm.chat_completion_with_failover(
                "default", system="s", user="u",
            )
    mock_completion.assert_not_awaited()


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_requires_messages_or_system_user(db):
    with pytest.raises(ValueError):
        await llm.chat_completion_with_failover("default")
    with pytest.raises(ValueError):
        await llm.chat_completion_with_failover("default", system="only-system")


@pytest.mark.asyncio
async def test_accepts_messages_arg(db):
    await storage.add_ai_model(
        role="default", name="A", model_id="m-a", failover_priority=10,
    )
    mock_completion = AsyncMock(return_value="ok")
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "usr"},
        {"role": "assistant", "content": "hi"},
        {"role": "user", "content": "more"},
    ]
    with patch.object(llm, "chat_completion_messages", mock_completion):
        result = await llm.chat_completion_with_failover("default", messages=msgs)
    assert result == "ok"
    call = mock_completion.await_args
    passed_messages = call.kwargs.get("messages") or call.args[0]
    assert passed_messages == msgs
