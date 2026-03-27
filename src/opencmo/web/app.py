"""FastAPI web dashboard for OpenCMO — Jinja2 SSR + REST API + SPA mount.

This module creates the ``app`` instance, registers auth middleware,
includes all domain routers, and provides the SPA catch-all route and
server entry point.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse

from opencmo import storage

_HERE = Path(__file__).parent
_SPA_DIR = _HERE.parent.parent.parent / "frontend" / "dist"  # <repo>/frontend/dist

app = FastAPI(title="OpenCMO Dashboard")
app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")
logger = logging.getLogger(__name__)


# In-memory expansion tracking (lightweight, no third task model)
_expansion_progress: dict[int, list[dict]] = {}   # project_id -> progress events
_expansion_tasks: dict[int, asyncio.Task] = {}     # project_id -> running asyncio.Task


# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def _startup_fix_stale_expansions():
    """Mark any stale 'running' expansions as interrupted (from previous process)."""
    await storage.ensure_db()
    try:
        fixed = await storage.fix_stale_expansions(timeout_seconds=60)
        if fixed:
            logger.info("Fixed %d stale expansion(s) on startup", fixed)
    except Exception:
        pass  # table may not exist yet on first run


@app.on_event("startup")
async def _startup_runtime_services():
    """Start optional runtime services after DB bootstrap."""
    from opencmo import scheduler

    if not scheduler.is_scheduler_available():
        logger.info("APScheduler not installed; scheduled monitors will remain inactive.")
        return

    loaded_jobs = await scheduler.load_jobs_from_db()
    scheduler.start_scheduler()
    logger.info("Scheduler started with %d enabled monitor job(s)", loaded_jobs)


@app.on_event("shutdown")
async def _shutdown_runtime_services():
    """Stop optional runtime services cleanly."""
    from opencmo import scheduler

    scheduler.stop_scheduler()
    logger.info("Scheduler stopped")


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

_PUBLIC_PREFIXES = ("/static/", "/favicon", "/api/v1/auth/", "/api/v1/health")

_LOGIN_HTML = """<!DOCTYPE html>
<html><head><title>OpenCMO Login</title>
<style>
body{font-family:system-ui;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f8fafc}
.card{background:#fff;padding:2rem;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);max-width:360px;width:100%}
h2{margin:0 0 1rem}input{width:100%;padding:.5rem;border:1px solid #d1d5db;border-radius:4px;margin:.5rem 0}
button{width:100%;padding:.5rem;background:#2563eb;color:#fff;border:none;border-radius:4px;cursor:pointer;margin-top:.5rem}
button:hover{background:#1d4ed8}.error{color:#dc2626;font-size:.875rem;margin-top:.5rem;display:none}
</style></head><body>
<div class="card"><h2>OpenCMO</h2><p>Enter your access token to continue.</p>
<form id="f"><input name="token" type="password" placeholder="Token" required>
<button type="submit">Login</button><div class="error" id="e">Invalid token</div></form></div>
<script>
document.getElementById('f').onsubmit=async e=>{
  e.preventDefault();const t=e.target.token.value;
  const r=await fetch('/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:t})});
  if(r.ok)location.reload();else document.getElementById('e').style.display='block';
};
</script></body></html>"""


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    token = os.environ.get("OPENCMO_WEB_TOKEN")
    if token:
        path = request.url.path
        if path == "/" or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
            return await call_next(request)
        # Check Authorization header or cookie
        auth = request.headers.get("Authorization", "")
        cookie_token = request.cookies.get("opencmo_token", "")
        if auth != f"Bearer {token}" and cookie_token != token:
            if path.startswith("/api/"):
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            return HTMLResponse(_LOGIN_HTML, status_code=401)
    return await call_next(request)


# ---------------------------------------------------------------------------
# Auth endpoint
# ---------------------------------------------------------------------------


@app.post("/api/v1/auth/login")
async def auth_login(request: Request):
    body = await request.json()
    expected = os.environ.get("OPENCMO_WEB_TOKEN", "")
    if not expected or body.get("token") != expected:
        return JSONResponse({"error": "Invalid token"}, status_code=401)
    resp = JSONResponse({"ok": True})
    resp.set_cookie("opencmo_token", expected, httponly=True, samesite="lax")
    return resp


@app.get("/api/v1/health")
async def api_v1_health():
    from opencmo import scheduler

    return JSONResponse({
        "ok": True,
        "scheduler": scheduler.scheduler_status(),
    })


# ---------------------------------------------------------------------------
# Include domain routers
# ---------------------------------------------------------------------------

from opencmo.web.routers.legacy import router as legacy_router
from opencmo.web.routers.projects import router as projects_router
from opencmo.web.routers.graph import router as graph_router
from opencmo.web.routers.insights import router as insights_router
from opencmo.web.routers.keywords import router as keywords_router
from opencmo.web.routers.monitors import router as monitors_router
from opencmo.web.routers.campaigns import router as campaigns_router
from opencmo.web.routers.approvals import router as approvals_router
from opencmo.web.routers.tasks import router as tasks_router
from opencmo.web.routers.chat import router as chat_router
from opencmo.web.routers.settings import router as settings_router
from opencmo.web.routers.report import router as report_router

app.include_router(legacy_router)
app.include_router(projects_router)
app.include_router(graph_router)
app.include_router(insights_router)
app.include_router(keywords_router)
app.include_router(monitors_router)
app.include_router(campaigns_router)
app.include_router(approvals_router)
app.include_router(tasks_router)
app.include_router(chat_router)
app.include_router(settings_router)
app.include_router(report_router)


# ---------------------------------------------------------------------------
# SPA mount — /app/ serves React frontend
# ---------------------------------------------------------------------------


@app.get("/app")
@app.get("/app/{full_path:path}")
async def spa_catchall(request: Request, full_path: str = ""):
    index = _SPA_DIR / "index.html"
    if not index.exists():
        return HTMLResponse(
            "<h1>Frontend not built</h1><p>Run <code>cd frontend && npm run build</code> to build the SPA.</p>",
            status_code=404,
        )
    # Serve static assets from dist
    if full_path and not full_path.startswith("index.html"):
        asset = _SPA_DIR / full_path
        if asset.exists() and asset.is_file():
            import mimetypes
            ct = mimetypes.guess_type(str(asset))[0] or "application/octet-stream"
            return StreamingResponse(open(asset, "rb"), media_type=ct)
    # SPA fallback — always return index.html
    return HTMLResponse(index.read_text())


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------


def run_server(port: int = 8080):
    import uvicorn

    load_dotenv()
    host = os.environ.get("OPENCMO_WEB_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=port)
