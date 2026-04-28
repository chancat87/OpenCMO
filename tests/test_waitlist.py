"""Tests for the hosted-version waitlist storage helpers."""
from __future__ import annotations

import pytest

from opencmo.storage import waitlist


def _setup_db(tmp_path, monkeypatch):
    """Standard isolated SQLite setup."""
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    monkeypatch.setattr(storage, "_SCHEMA_READY_FOR", None, raising=False)
    return db_path


def test_is_valid_email_accepts_normal():
    assert waitlist.is_valid_email("user@example.com") is True
    assert waitlist.is_valid_email("name+tag@sub.co.uk") is True


def test_is_valid_email_rejects_garbage():
    assert waitlist.is_valid_email("") is False
    assert waitlist.is_valid_email("abc") is False
    assert waitlist.is_valid_email("@x.com") is False
    assert waitlist.is_valid_email("foo@") is False
    assert waitlist.is_valid_email("foo@bar") is False  # no TLD
    assert waitlist.is_valid_email("a" * 250 + "@x.co") is False  # over 254
    assert waitlist.is_valid_email(None) is False  # type: ignore[arg-type]
    assert waitlist.is_valid_email(123) is False  # type: ignore[arg-type]


def test_normalize_source_whitelist():
    assert waitlist._normalize_source(None) == ""
    assert waitlist._normalize_source("") == ""
    assert waitlist._normalize_source("home_inline") == "home_inline"
    assert waitlist._normalize_source("hosted_page") == "hosted_page"
    assert waitlist._normalize_source("bogus") == ""  # silently coerced
    assert waitlist._normalize_source("'; DROP TABLE waitlist; --") == ""
    assert waitlist._normalize_source("  home_inline  ") == "home_inline"  # stripped


@pytest.mark.asyncio
async def test_valid_email_accepted(tmp_path, monkeypatch):
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    assert await storage.add_to_waitlist("alice@example.com") is True
    assert await storage.count_waitlist() == 1


@pytest.mark.asyncio
async def test_duplicate_email_idempotent(tmp_path, monkeypatch):
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    assert await storage.add_to_waitlist("alice@example.com") is True
    assert await storage.add_to_waitlist("alice@example.com") is True  # duplicate ok
    assert await storage.count_waitlist() == 1


@pytest.mark.asyncio
async def test_email_normalized_lowercase_and_strip(tmp_path, monkeypatch):
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    assert await storage.add_to_waitlist("  ALICE@Example.COM  ") is True
    assert await storage.add_to_waitlist("alice@example.com") is True  # same row
    assert await storage.count_waitlist() == 1


@pytest.mark.asyncio
async def test_invalid_email_rejected(tmp_path, monkeypatch):
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    assert await storage.add_to_waitlist("") is False
    assert await storage.add_to_waitlist("bad") is False
    assert await storage.add_to_waitlist("foo@") is False
    assert await storage.count_waitlist() == 0


@pytest.mark.asyncio
async def test_source_recorded(tmp_path, monkeypatch):
    from opencmo import storage

    _setup_db(tmp_path, monkeypatch)
    await storage.ensure_db()

    await storage.add_to_waitlist("a@x.co", source="home_inline")
    await storage.add_to_waitlist("b@x.co", source="hosted_page")
    await storage.add_to_waitlist("c@x.co", source="bogus")  # coerced to ""
    await storage.add_to_waitlist("d@x.co")  # default ""

    db = await storage.get_db()
    try:
        cursor = await db.execute("SELECT email, source FROM waitlist ORDER BY email")
        rows = await cursor.fetchall()
    finally:
        await db.close()

    assert [(r[0], r[1]) for r in rows] == [
        ("a@x.co", "home_inline"),
        ("b@x.co", "hosted_page"),
        ("c@x.co", ""),
        ("d@x.co", ""),
    ]
