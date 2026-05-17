"""Keywords API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage
from opencmo.web.auth import get_request_account_id

router = APIRouter(prefix="/api/v1")


@router.get("/projects/{project_id}/keywords")
async def api_v1_keywords(project_id: int):
    return JSONResponse(await storage.list_tracked_keywords(project_id))


@router.post("/projects/{project_id}/keywords")
async def api_v1_add_keyword(project_id: int, request: Request):
    body = await request.json()
    keyword = body.get("keyword", "").strip()
    if not keyword:
        return JSONResponse({"error": "keyword is required"}, status_code=400)
    kw_id = await storage.add_tracked_keyword(project_id, keyword)
    if kw_id:
        await storage.seed_node_if_expansion_exists(project_id, "keyword", kw_id, priority=80)
    return JSONResponse({"id": kw_id, "keyword": keyword}, status_code=201)


@router.delete("/keywords/{keyword_id}")
async def api_v1_delete_keyword(keyword_id: int, request: Request):
    account_id = await get_request_account_id(request)
    keyword = await storage.get_tracked_keyword(keyword_id)
    if not keyword or not await storage.get_project(keyword["project_id"], account_id=account_id):
        return JSONResponse({"error": "Not found"}, status_code=404)
    ok = await storage.remove_tracked_keyword(keyword_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})
