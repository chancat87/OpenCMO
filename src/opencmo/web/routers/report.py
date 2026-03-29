"""Report API router — with async task support for report generation."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from opencmo import storage
from opencmo.storage._db import get_db

router = APIRouter(prefix="/api/v1")


@router.get("/projects/{project_id}/reports")
async def api_v1_reports(project_id: int, kind: str | None = None, audience: str | None = None):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(await storage.list_reports(project_id, kind=kind, audience=audience))


@router.get("/projects/{project_id}/reports/latest")
async def api_v1_latest_reports(project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(await storage.get_latest_reports(project_id))


@router.get("/reports/{report_id}")
async def api_v1_report_detail(report_id: int):
    report = await storage.get_report(report_id)
    if not report:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(report)


# ----- Report Task management (async regeneration) -----

async def _create_report_task(project_id: int, kind: str) -> str:
    """Create a report task record and return the task_id."""
    task_id = str(uuid.uuid4())
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO report_tasks (task_id, project_id, kind, status) VALUES (?, ?, ?, 'pending')",
            (task_id, project_id, kind),
        )
        await db.commit()
    finally:
        await db.close()
    return task_id


async def _update_report_task(task_id: str, status: str, progress: list | None = None, error: str | None = None) -> None:
    """Update a report task's status and progress."""
    db = await get_db()
    try:
        parts = ["status = ?"]
        params: list = [status]
        if progress is not None:
            parts.append("progress_json = ?")
            params.append(json.dumps(progress, ensure_ascii=False))
        if error is not None:
            parts.append("error = ?")
            params.append(error)
        if status in ("completed", "failed"):
            parts.append("completed_at = datetime('now')")
        params.append(task_id)
        await db.execute(
            f"UPDATE report_tasks SET {', '.join(parts)} WHERE task_id = ?",
            params,
        )
        await db.commit()
    finally:
        await db.close()


async def _get_report_task(task_id: str) -> dict | None:
    """Get a report task by its task_id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT task_id, project_id, kind, status, progress_json, error,
                      created_at, completed_at
               FROM report_tasks WHERE task_id = ?""",
            (task_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "task_id": row[0],
            "project_id": row[1],
            "kind": row[2],
            "status": row[3],
            "progress": json.loads(row[4] or "[]"),
            "error": row[5],
            "created_at": row[6],
            "completed_at": row[7],
        }
    finally:
        await db.close()


async def _run_report_in_background(task_id: str, project_id: int, kind: str) -> None:
    """Background coroutine that runs the report regeneration and updates the task record."""
    from opencmo import service

    progress_events: list[dict] = []

    def on_progress(event: dict):
        progress_events.append(event)
        # Fire-and-forget task update (don't block pipeline)
        asyncio.get_event_loop().create_task(
            _update_report_task(task_id, "running", progress=progress_events)
        )

    try:
        await _update_report_task(task_id, "running")
        result = await service.regenerate_project_report(project_id, kind, on_progress=on_progress)
        await _update_report_task(task_id, "completed", progress=progress_events)
    except Exception as exc:
        await _update_report_task(task_id, "failed", progress=progress_events, error=str(exc))


@router.post("/projects/{project_id}/reports/{kind}/regenerate")
async def api_v1_regenerate_report(project_id: int, kind: str):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)

    task_id = await _create_report_task(project_id, kind)
    asyncio.get_event_loop().create_task(_run_report_in_background(task_id, project_id, kind))

    return JSONResponse({"task_id": task_id, "status": "pending"})


@router.get("/reports/tasks/{task_id}")
async def api_v1_report_task(task_id: str):
    """Get the status and progress of a report generation task."""
    task = await _get_report_task(task_id)
    if not task:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    return JSONResponse(task)


@router.post("/projects/{project_id}/report")
async def api_v1_report(project_id: int):
    from opencmo import service
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    result = await service.send_project_report(project_id)
    if result["ok"]:
        return JSONResponse(result)
    return JSONResponse(result, status_code=500)
