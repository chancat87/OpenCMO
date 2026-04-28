"""SQLite-backed cache for GitHub repo stats.

L2 cache layer (the L1 in-process memory cache lives in
``opencmo.web.github_stats``). This module survives process restart
and shares the cache across multiple worker processes if any are
ever added.

TTL is enforced at read time, not via background eviction — we never
have more than ~10 rows total (one per cached repo key).
"""

from __future__ import annotations

import json
import time
from typing import Optional

from opencmo.storage._db import get_db


async def get_cached_github_stats(key: str, ttl_sec: int) -> Optional[dict]:
    """Return parsed payload if fresh; None if missing or stale."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT payload, fetched_at FROM github_stats_cache WHERE key = ?",
            (key,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        payload, fetched_at = row[0], float(row[1])
        if time.time() - fetched_at > ttl_sec:
            return None
        return json.loads(payload)
    finally:
        await db.close()


async def set_cached_github_stats(key: str, payload: dict) -> None:
    """Upsert the cache row. Caller is responsible for not caching failures."""
    db = await get_db()
    try:
        await db.execute(
            """
            INSERT INTO github_stats_cache (key, payload, fetched_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                payload = excluded.payload,
                fetched_at = excluded.fetched_at
            """,
            (key, json.dumps(payload), time.time()),
        )
        await db.commit()
    finally:
        await db.close()
