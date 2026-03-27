"""Tasks and scan runs API router."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


@router.get("/tasks")
async def api_v1_tasks():
    from opencmo.web import task_registry
    return JSONResponse([t.to_dict() for t in task_registry.list_tasks()])


@router.get("/tasks/{task_id}")
async def api_v1_task(task_id: str):
    from opencmo.web import task_registry
    record = task_registry.get_task(task_id)
    if not record:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(record.to_dict())


@router.get("/tasks/{task_id}/findings")
async def api_v1_task_findings(task_id: str):
    return JSONResponse(await storage.get_task_findings(task_id))


@router.get("/tasks/{task_id}/recommendations")
async def api_v1_task_recommendations(task_id: str):
    return JSONResponse(await storage.get_task_recommendations(task_id))


@router.get("/monitors/{monitor_id}/runs")
async def api_v1_monitor_runs(monitor_id: int):
    return JSONResponse(await storage.list_scan_runs_by_monitor(monitor_id))
