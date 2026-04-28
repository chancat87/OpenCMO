"""Waitlist signups for the hosted OpenCMO version.

Phase 1 schema is intentionally minimal: email + source + created_at.
Source is whitelisted at the storage layer as defense-in-depth (the
API layer also restricts via Pydantic Literal). Storage normalizes
unknown sources to '' silently.
"""

from __future__ import annotations

import re
from typing import Optional

from opencmo.storage._db import get_db

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ALLOWED_SOURCES = {"home_inline", "hosted_page", ""}


def is_valid_email(email: str) -> bool:
    """Reject obviously bad input. Real validation = double opt-in (Phase 2)."""
    if not isinstance(email, str):
        return False
    e = email.strip().lower()
    if len(e) > 254 or len(e) < 5:
        return False
    return bool(_EMAIL_RE.match(e))


def _normalize_source(source: Optional[str]) -> str:
    """Whitelist-only — defends against arbitrary string injection in source col."""
    if not source:
        return ""
    s = source.strip()
    return s if s in _ALLOWED_SOURCES else ""


async def add_to_waitlist(email: str, source: str = "") -> bool:
    """Idempotent insert. Returns True if accepted (new or duplicate)."""
    if not is_valid_email(email):
        return False
    normalized_source = _normalize_source(source)
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO waitlist (email, source, created_at) "
            "VALUES (?, ?, datetime('now'))",
            (email.strip().lower(), normalized_source),
        )
        await db.commit()
        return True
    finally:
        await db.close()


async def count_waitlist() -> int:
    """For monitoring / debug only — no public endpoint exposes this."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) FROM waitlist")
        row = await cursor.fetchone()
        return int(row[0]) if row else 0
    finally:
        await db.close()
