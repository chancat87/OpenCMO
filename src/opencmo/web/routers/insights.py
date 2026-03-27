"""Insights API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


@router.get("/insights")
async def api_v1_insights(request: Request):
    project_id = request.query_params.get("project_id")
    unread = request.query_params.get("unread", "").lower() in ("true", "1")
    pid = int(project_id) if project_id else None
    return JSONResponse(await storage.list_insights(project_id=pid, unread_only=unread))


@router.get("/insights/summary")
async def api_v1_insights_summary(request: Request):
    project_id = request.query_params.get("project_id")
    pid = int(project_id) if project_id else None
    return JSONResponse(await storage.get_insights_summary(project_id=pid))


@router.post("/insights/{insight_id}/read")
async def api_v1_insight_read(insight_id: int):
    ok = await storage.mark_insight_read(insight_id)
    if not ok:
        return JSONResponse({"error": "Not found or already read"}, status_code=404)
    return JSONResponse({"ok": True})
