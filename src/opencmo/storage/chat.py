"""Chat session storage."""

from __future__ import annotations

from opencmo.storage._db import get_db
from opencmo.storage.accounts import get_admin_account_id


async def create_chat_session(
    session_id: str,
    title: str = "",
    project_id: int | None = None,
    account_id: int | None = None,
) -> None:
    resolved_account_id = int(account_id) if account_id is not None else await get_admin_account_id()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO chat_sessions (id, account_id, title, project_id) VALUES (?, ?, ?, ?)",
            (session_id, resolved_account_id, title, project_id),
        )
        await db.commit()
    finally:
        await db.close()


async def list_chat_sessions(account_id: int | None = None) -> list[dict]:
    db = await get_db()
    try:
        where = ""
        params: tuple = ()
        if account_id is not None:
            where = "WHERE s.account_id = ?"
            params = (account_id,)
        cursor = await db.execute(
            f"""SELECT s.id, s.account_id, s.title, s.created_at, s.updated_at, s.project_id, p.brand_name
               FROM chat_sessions s
               LEFT JOIN projects p ON p.id = s.project_id
               {where}
               ORDER BY s.updated_at DESC, s.id DESC""",
            params,
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "account_id": r[1],
                "title": r[2],
                "created_at": r[3],
                "updated_at": r[4],
                "project_id": r[5],
                "project_name": r[6],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_chat_session(session_id: str, account_id: int | None = None) -> dict | None:
    db = await get_db()
    try:
        where = "s.id = ?"
        params: tuple = (session_id,)
        if account_id is not None:
            where += " AND s.account_id = ?"
            params = (session_id, account_id)
        cursor = await db.execute(
            f"""SELECT s.id, s.account_id, s.title, s.input_items, s.created_at, s.updated_at, s.project_id, p.brand_name
               FROM chat_sessions s
               LEFT JOIN projects p ON p.id = s.project_id
               WHERE {where}""",
            params,
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "account_id": row[1],
            "title": row[2],
            "input_items": row[3],
            "created_at": row[4],
            "updated_at": row[5],
            "project_id": row[6],
            "project_name": row[7],
        }
    finally:
        await db.close()


async def update_chat_session(
    session_id: str,
    input_items_json: str,
    title: str | None = None,
    account_id: int | None = None,
) -> bool:
    db = await get_db()
    try:
        where = "id = ?"
        suffix: tuple = (session_id,)
        if account_id is not None:
            where += " AND account_id = ?"
            suffix = (session_id, account_id)
        if title is not None:
            cursor = await db.execute(
                f"UPDATE chat_sessions SET input_items = ?, title = ?, updated_at = datetime('now') WHERE {where}",
                (input_items_json, title, *suffix),
            )
        else:
            cursor = await db.execute(
                f"UPDATE chat_sessions SET input_items = ?, updated_at = datetime('now') WHERE {where}",
                (input_items_json, *suffix),
            )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def delete_chat_session(session_id: str, account_id: int | None = None) -> bool:
    db = await get_db()
    try:
        where = "id = ?"
        params: tuple = (session_id,)
        if account_id is not None:
            where += " AND account_id = ?"
            params = (session_id, account_id)
        cursor = await db.execute(f"DELETE FROM chat_sessions WHERE {where}", params)
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def clear_chat_sessions() -> None:
    db = await get_db()
    try:
        await db.execute("DELETE FROM chat_sessions")
        await db.commit()
    finally:
        await db.close()
