"""AI model provider config storage for smart failover."""

from __future__ import annotations

from typing import Any

from opencmo.storage._db import get_db

_ALLOWED_UPDATE_FIELDS: frozenset[str] = frozenset({
    "role",
    "name",
    "api_key",
    "base_url",
    "model_id",
    "failover_priority",
    "daily_limit",
    "enabled",
})

_SELECT_COLUMNS = (
    "id, role, name, api_key, base_url, model_id, failover_priority, "
    "daily_limit, used_today, used_total, last_reset_at, enabled, "
    "created_at, updated_at"
)


def _row_to_dict(row: Any) -> dict:
    return {
        "id": row[0],
        "role": row[1],
        "name": row[2],
        "api_key": row[3],
        "base_url": row[4],
        "model_id": row[5],
        "failover_priority": row[6],
        "daily_limit": row[7],
        "used_today": row[8],
        "used_total": row[9],
        "last_reset_at": row[10],
        "enabled": bool(row[11]),
        "created_at": row[12],
        "updated_at": row[13],
    }


async def list_ai_models(
    role: str | None = None,
    enabled_only: bool = False,
) -> list[dict]:
    """Return ai_models rows ordered by failover_priority ASC, id ASC."""
    clauses: list[str] = []
    params: list[Any] = []
    if role is not None:
        clauses.append("role = ?")
        params.append(role)
    if enabled_only:
        clauses.append("enabled = 1")
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = (
        f"SELECT {_SELECT_COLUMNS} FROM ai_models{where} "
        "ORDER BY failover_priority ASC, id ASC"
    )
    db = await get_db()
    try:
        cursor = await db.execute(sql, params)
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        await db.close()


async def get_ai_model(model_pk_id: int) -> dict | None:
    """Return a single ai_models row by primary key id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            f"SELECT {_SELECT_COLUMNS} FROM ai_models WHERE id = ?",
            (model_pk_id,),
        )
        row = await cursor.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        await db.close()


async def add_ai_model(
    *,
    role: str,
    name: str,
    model_id: str,
    api_key: str = "",
    base_url: str = "",
    failover_priority: int = 100,
    daily_limit: int = 0,
    enabled: bool = True,
) -> int:
    """Insert a new ai_models row. Returns the new primary key id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO ai_models (
                role, name, api_key, base_url, model_id,
                failover_priority, daily_limit, enabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                role,
                name,
                api_key,
                base_url,
                model_id,
                int(failover_priority),
                int(daily_limit),
                1 if enabled else 0,
            ),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def update_ai_model(model_pk_id: int, **fields: Any) -> bool:
    """Update one or more ai_models columns. Returns True if a row changed."""
    cleaned: dict[str, Any] = {}
    for key, value in fields.items():
        if key not in _ALLOWED_UPDATE_FIELDS:
            continue
        if key == "enabled":
            cleaned[key] = 1 if value else 0
        elif key in {"failover_priority", "daily_limit"}:
            cleaned[key] = int(value)
        else:
            cleaned[key] = value
    if not cleaned:
        return False

    set_clause = ", ".join(f"{col} = ?" for col in cleaned)
    set_clause += ", updated_at = datetime('now')"
    params = list(cleaned.values()) + [model_pk_id]

    db = await get_db()
    try:
        cursor = await db.execute(
            f"UPDATE ai_models SET {set_clause} WHERE id = ?",
            params,
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def delete_ai_model(model_pk_id: int) -> bool:
    """Delete an ai_models row. Returns True if a row was deleted."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM ai_models WHERE id = ?",
            (model_pk_id,),
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def claim_quota(model_pk_id: int) -> bool:
    """Atomically reserve one usage slot on a model.

    Returns True if the caller may proceed. Side effects when True:
        - ``used_today`` is incremented by 1.
        - ``used_total`` is incremented by 1.
        - ``last_reset_at`` is set to now when the rolling 24h window had
          elapsed (zeroing ``used_today`` before the increment).

    The implementation avoids any SELECT-then-UPDATE race by using a
    single SQL UPDATE whose WHERE clause encodes both the enabled flag
    and the daily quota check (with an inline rolling-reset condition).
    """
    db = await get_db()
    try:
        # Single atomic UPDATE:
        #   - resets used_today to 0 when last_reset_at is older than 1 day
        #     (or NULL — first use), bumping last_reset_at to now.
        #   - increments used_today (effectively the post-reset value plus one).
        #   - rejects when disabled or when the *post-reset* used_today would
        #     equal or exceed daily_limit (zero means unlimited).
        cursor = await db.execute(
            """UPDATE ai_models
                  SET used_today = CASE
                          WHEN last_reset_at IS NULL
                            OR last_reset_at < datetime('now', '-1 day')
                          THEN 1
                          ELSE used_today + 1
                      END,
                      used_total = used_total + 1,
                      last_reset_at = CASE
                          WHEN last_reset_at IS NULL
                            OR last_reset_at < datetime('now', '-1 day')
                          THEN datetime('now')
                          ELSE last_reset_at
                      END,
                      updated_at = datetime('now')
                WHERE id = ?
                  AND enabled = 1
                  AND (
                      daily_limit = 0
                      OR (
                          CASE
                              WHEN last_reset_at IS NULL
                                OR last_reset_at < datetime('now', '-1 day')
                              THEN 0
                              ELSE used_today
                          END
                      ) < daily_limit
                  )""",
            (model_pk_id,),
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
