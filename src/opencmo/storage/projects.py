"""Project CRUD operations."""

from __future__ import annotations

import json

from opencmo.storage._db import get_db
from opencmo.storage.accounts import get_admin_account_id


def _parse_aliases(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return []


async def _resolve_account_id(account_id: int | None) -> int:
    return int(account_id) if account_id is not None else await get_admin_account_id()


async def ensure_project(brand_name: str, url: str, category: str, account_id: int | None = None) -> int:
    """Upsert a project row and return its id."""
    resolved_account_id = await _resolve_account_id(account_id)
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO projects (account_id, brand_name, url, category) VALUES (?, ?, ?, ?)",
            (resolved_account_id, brand_name, url, category),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id FROM projects WHERE account_id = ? AND brand_name = ? AND url = ?",
            (resolved_account_id, brand_name, url),
        )
        row = await cursor.fetchone()
        if row is None:
            # Legacy databases may still have the historical global UNIQUE(brand_name, url).
            cursor = await db.execute(
                "SELECT id FROM projects WHERE brand_name = ? AND url = ? AND account_id = ?",
                (brand_name, url, resolved_account_id),
            )
            row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("project insert failed")
        return row[0]
    finally:
        await db.close()


async def update_project(
    project_id: int,
    brand_name: str | None = None,
    category: str | None = None,
    aliases: list[str] | None = None,
) -> None:
    """Update project metadata (brand_name, category, and/or aliases)."""
    fields: list[str] = []
    values: list = []
    if brand_name is not None:
        fields.append("brand_name = ?")
        values.append(brand_name)
    if category is not None:
        fields.append("category = ?")
        values.append(category)
    if aliases is not None:
        fields.append("aliases = ?")
        values.append(json.dumps([a for a in aliases if a]))
    if not fields:
        return
    values.append(project_id)
    db = await get_db()
    try:
        await db.execute(
            f"UPDATE projects SET {', '.join(fields)} WHERE id = ?",
            tuple(values),
        )
        await db.commit()
    finally:
        await db.close()


async def get_project(project_id: int, account_id: int | None = None) -> dict | None:
    """Return project dict by id, or None."""
    db = await get_db()
    try:
        where = "id = ?"
        params: tuple = (project_id,)
        if account_id is not None:
            where = "id = ? AND account_id = ?"
            params = (project_id, account_id)
        cursor = await db.execute(
            f"SELECT id, account_id, brand_name, url, category, aliases FROM projects WHERE {where}",
            params,
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "account_id": row[1],
            "brand_name": row[2],
            "url": row[3],
            "category": row[4],
            "aliases": _parse_aliases(row[5]),
        }
    finally:
        await db.close()


async def list_projects(account_id: int | None = None) -> list[dict]:
    """Return all projects, newest first (highest id first)."""
    db = await get_db()
    try:
        if account_id is None:
            query = "SELECT id, account_id, brand_name, url, category, aliases FROM projects ORDER BY id DESC"
            params: tuple = ()
        else:
            query = "SELECT id, account_id, brand_name, url, category, aliases FROM projects WHERE account_id = ? ORDER BY id DESC"
            params = (account_id,)
        cursor = await db.execute(
            query,
            params,
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "account_id": r[1],
                "brand_name": r[2],
                "url": r[3],
                "category": r[4],
                "aliases": _parse_aliases(r[5]),
            }
            for r in rows
        ]
    finally:
        await db.close()


async def find_projects_by_brand(brand_name: str, account_id: int | None = None) -> list[dict]:
    """Find projects whose brand_name matches (case-insensitive)."""
    db = await get_db()
    try:
        where = "brand_name = ? COLLATE NOCASE"
        params: tuple = (brand_name,)
        if account_id is not None:
            where += " AND account_id = ?"
            params = (brand_name, account_id)
        cursor = await db.execute(
            f"SELECT id, account_id, brand_name, url, category, aliases FROM projects WHERE {where}",
            params,
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "account_id": r[1],
                "brand_name": r[2],
                "url": r[3],
                "category": r[4],
                "aliases": _parse_aliases(r[5]),
            }
            for r in rows
        ]
    finally:
        await db.close()


async def find_project_by_identity(brand_name: str, url: str, account_id: int | None = None) -> dict | None:
    """Find a project by the database identity key used for uniqueness."""
    db = await get_db()
    try:
        where = "brand_name = ? AND url = ?"
        params: tuple = (brand_name, url)
        if account_id is not None:
            where += " AND account_id = ?"
            params = (brand_name, url, account_id)
        cursor = await db.execute(
            f"SELECT id, account_id, brand_name, url, category, aliases FROM projects WHERE {where}",
            params,
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "account_id": row[1],
            "brand_name": row[2],
            "url": row[3],
            "category": row[4],
            "aliases": _parse_aliases(row[5]),
        }
    finally:
        await db.close()


async def delete_project(project_id: int, account_id: int | None = None) -> bool:
    """Delete a project and all its related data. Returns True if deleted."""
    if account_id is not None and await get_project(project_id, account_id) is None:
        return False
    db = await get_db()
    try:
        await db.execute("UPDATE chat_sessions SET project_id = NULL WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM approvals WHERE project_id = ?", (project_id,))
        # Delete graph expansion data
        await db.execute("DELETE FROM graph_expansion_edges WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM graph_expansion_nodes WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM graph_expansions WHERE project_id = ?", (project_id,))
        # Delete discussion snapshots (via tracked_discussions)
        await db.execute(
            """DELETE FROM discussion_snapshots WHERE discussion_id IN
               (SELECT id FROM tracked_discussions WHERE project_id = ?)""",
            (project_id,),
        )
        # Delete tracked discussions
        await db.execute("DELETE FROM tracked_discussions WHERE project_id = ?", (project_id,))
        # Delete scans
        await db.execute("DELETE FROM seo_scans WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM geo_scans WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM community_scans WHERE project_id = ?", (project_id,))
        # Delete SERP data
        await db.execute("DELETE FROM serp_snapshots WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM tracked_keywords WHERE project_id = ?", (project_id,))
        # Delete competitors and their keywords
        await db.execute(
            """DELETE FROM competitor_keywords WHERE competitor_id IN
               (SELECT id FROM competitors WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute("DELETE FROM competitors WHERE project_id = ?", (project_id,))
        # Delete campaign artifacts and runs
        await db.execute(
            """DELETE FROM campaign_artifacts WHERE run_id IN
               (SELECT id FROM campaign_runs WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute("DELETE FROM campaign_runs WHERE project_id = ?", (project_id,))
        # Delete trend briefings and insights
        await db.execute("DELETE FROM trend_briefings WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM insights WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM reports WHERE project_id = ?", (project_id,))
        # Delete monitoring artifacts
        await db.execute(
            """DELETE FROM scan_findings WHERE run_id IN
               (SELECT id FROM scan_runs WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute(
            """DELETE FROM scan_recommendations WHERE run_id IN
               (SELECT id FROM scan_runs WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute(
            """DELETE FROM scan_run_steps WHERE run_id IN
               (SELECT id FROM scan_runs WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute("DELETE FROM scan_runs WHERE project_id = ?", (project_id,))
        # Delete scheduled jobs
        await db.execute("DELETE FROM scheduled_jobs WHERE project_id = ?", (project_id,))
        # Delete background tasks and their events
        await db.execute(
            """DELETE FROM background_task_events WHERE task_id IN
               (SELECT task_id FROM background_tasks WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute("DELETE FROM background_tasks WHERE project_id = ?", (project_id,))
        # Delete remaining tables with project_id
        await db.execute("UPDATE chat_sessions SET project_id = NULL WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM approvals WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM graph_expansion_edges WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM citability_scans WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM ai_crawler_scans WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM brand_presence_scans WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM brand_kits WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM blog_drafts WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM manual_tracking WHERE project_id = ?", (project_id,))
        try:
            await db.execute("DELETE FROM report_tasks WHERE project_id = ?", (project_id,))
        except Exception:
            pass  # legacy table — may not exist on fresh installs
        # Delete the project itself
        cursor = await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
