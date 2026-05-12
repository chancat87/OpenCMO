"""AI models (provider config + smart failover) CRUD API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


@router.get("/ai-models")
async def api_v1_list_ai_models(request: Request):
    role = request.query_params.get("role")
    enabled_only = request.query_params.get("enabled_only", "").lower() in ("true", "1")
    rows = await storage.list_ai_models(role=role, enabled_only=enabled_only)
    for r in rows:
        r["api_key_set"] = bool(r.get("api_key"))
        r.pop("api_key", None)
    return JSONResponse(rows)


@router.post("/ai-models")
async def api_v1_create_ai_model(request: Request):
    body = await request.json()
    if not body.get("name") or not body.get("model_id"):
        return JSONResponse({"error": "name and model_id are required"}, status_code=400)
    new_id = await storage.add_ai_model(
        role=body.get("role", "default"),
        name=body["name"],
        model_id=body["model_id"],
        api_key=body.get("api_key", ""),
        base_url=body.get("base_url", ""),
        failover_priority=int(body.get("failover_priority", 100)),
        daily_limit=int(body.get("daily_limit", 0)),
        enabled=bool(body.get("enabled", True)),
    )
    return JSONResponse({"id": new_id})


@router.patch("/ai-models/{model_id}")
async def api_v1_update_ai_model(model_id: int, request: Request):
    body = await request.json()
    allowed = {
        "role", "name", "api_key", "base_url", "model_id",
        "failover_priority", "daily_limit", "enabled",
    }
    fields = {k: v for k, v in body.items() if k in allowed}
    if not fields:
        return JSONResponse({"error": "No allowed fields to update"}, status_code=400)
    ok = await storage.update_ai_model(model_id, **fields)
    return JSONResponse({"ok": ok}, status_code=200 if ok else 404)


@router.delete("/ai-models/{model_id}")
async def api_v1_delete_ai_model(model_id: int):
    ok = await storage.delete_ai_model(model_id)
    return JSONResponse({"ok": ok}, status_code=200 if ok else 404)
