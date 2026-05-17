"""Key-value settings storage.

Two storage layers coexist:

1. ``account_settings`` (per-account, multi-tenant) — the primary location for
   user-owned credentials (Reddit, Twitter, SMTP, DataForSEO, GEO providers,
   etc.). Each account owns and reads its own keys; account A can never see
   account B's values.

2. ``settings`` (legacy global) — kept as a last-resort fallback for system
   operations that need to work before any account context exists (e.g. signup
   verification emails). New writes should always go to ``account_settings``;
   the legacy table is preserved so old code paths keep working and so
   ``get_system_setting`` has somewhere to fall back to when no admin account
   has configured a value yet.

Resolution order for ``get_system_setting``:
    admin-account row in account_settings → legacy ``settings`` row → ``None``
"""

from __future__ import annotations

import logging
import os

from opencmo.storage._db import get_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-account API (multi-tenant)
# ---------------------------------------------------------------------------


async def get_account_setting(account_id: int, key: str) -> str | None:
    """Return a single per-account setting value, or ``None`` when missing."""
    if not account_id or not key:
        return None
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT value FROM account_settings WHERE account_id = ? AND key = ?",
            (int(account_id), str(key)),
        )
        row = await cursor.fetchone()
        return row[0] if row else None
    finally:
        await db.close()


async def set_account_setting(account_id: int, key: str, value: str) -> None:
    """Upsert a per-account setting. Empty/blank values are rejected."""
    if not account_id or not key:
        raise ValueError("account_id and key are required")
    if value is None:
        raise ValueError("value must not be None — use delete_account_setting instead")
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO account_settings (account_id, key, value, updated_at)
               VALUES (?, ?, ?, datetime('now'))
               ON CONFLICT(account_id, key) DO UPDATE SET
                   value = excluded.value,
                   updated_at = datetime('now')""",
            (int(account_id), str(key), str(value)),
        )
        await db.commit()
    finally:
        await db.close()


async def delete_account_setting(account_id: int, key: str) -> bool:
    """Remove a per-account setting. Returns True when a row was deleted."""
    if not account_id or not key:
        return False
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM account_settings WHERE account_id = ? AND key = ?",
            (int(account_id), str(key)),
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def list_account_settings(account_id: int) -> dict[str, str]:
    """Return every per-account setting for an account as a flat dict."""
    if not account_id:
        return {}
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT key, value FROM account_settings WHERE account_id = ?",
            (int(account_id),),
        )
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows if row[0]}
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# System-level read (admin account → legacy global table)
# ---------------------------------------------------------------------------


async def _resolve_admin_account_id() -> int | None:
    """Find the admin account id without raising. Returns ``None`` for fresh installs."""
    admin_email = os.environ.get("OPENCMO_ADMIN_EMAIL", "hello@aidcmo.com").strip().lower()
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT a.id
               FROM accounts a
               JOIN account_members m ON m.account_id = a.id
               JOIN users u ON u.id = m.user_id
               WHERE u.email = ?
               ORDER BY a.id
               LIMIT 1""",
            (admin_email,),
        )
        row = await cursor.fetchone()
        if row:
            return int(row[0])
        cursor = await db.execute(
            "SELECT a.id FROM accounts a JOIN account_members m ON m.account_id = a.id "
            "JOIN users u ON u.id = m.user_id WHERE u.role = 'admin' ORDER BY a.id LIMIT 1"
        )
        row = await cursor.fetchone()
        if row:
            return int(row[0])
        return None
    except Exception as exc:
        logger.debug("admin account lookup failed: %s", exc)
        return None
    finally:
        await db.close()


async def get_system_setting(key: str) -> str | None:
    """Read a system-level setting.

    Resolution order:
        1. Admin account's row in ``account_settings``
        2. Legacy global ``settings`` row
        3. ``None``
    """
    if not key:
        return None
    admin_id = await _resolve_admin_account_id()
    if admin_id is not None:
        value = await get_account_setting(admin_id, key)
        if value:
            return value

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?", (str(key),)
        )
        row = await cursor.fetchone()
        return row[0] if row else None
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Legacy helpers — preserved so unmodified callers keep working.
# All future code should call the per-account API directly via
# ``llm.get_key`` (account ContextVar) or ``get_system_setting`` (admin fallback).
# ---------------------------------------------------------------------------


async def get_setting(key: str) -> str | None:
    """Compatibility shim: resolves a key via the system-level cascade.

    Callers that need per-account isolation should switch to
    ``get_account_setting`` or ``llm.get_key`` (which reads the account
    ContextVar set by the web middleware).
    """
    return await get_system_setting(key)


async def set_setting(key: str, value: str) -> None:
    """Compatibility shim: writes to the legacy global ``settings`` table.

    Prefer ``set_account_setting`` for new code so values stay isolated per
    account. Kept here so older call sites (CLI tools, scripts) keep working.
    """
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (str(key), str(value)),
        )
        await db.commit()
    finally:
        await db.close()


async def delete_setting(key: str) -> bool:
    """Compatibility shim: removes a key from the legacy global table."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM settings WHERE key = ?", (str(key),)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
