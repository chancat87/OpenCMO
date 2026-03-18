"""FastAPI web dashboard for OpenCMO."""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from opencmo import storage

_HERE = Path(__file__).parent
_TEMPLATES = Jinja2Templates(directory=str(_HERE / "templates"))

app = FastAPI(title="OpenCMO Dashboard")
app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")


# ---------------------------------------------------------------------------
# HTML routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    projects = await storage.list_projects()
    project_data = []
    for p in projects:
        latest = await storage.get_latest_scans(p["id"])
        project_data.append({**p, "latest": latest})
    return _TEMPLATES.TemplateResponse("dashboard.html", {"request": request, "projects": project_data})


@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_overview(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    latest = await storage.get_latest_scans(project_id)
    seo_history = await storage.get_seo_history(project_id, limit=10)
    geo_history = await storage.get_geo_history(project_id, limit=10)
    discussions = await storage.get_tracked_discussions(project_id)
    return _TEMPLATES.TemplateResponse("project.html", {
        "request": request,
        "project": project,
        "latest": latest,
        "seo_history": seo_history,
        "geo_history": geo_history,
        "discussions": discussions,
    })


@app.get("/project/{project_id}/seo", response_class=HTMLResponse)
async def project_seo(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    history = await storage.get_seo_history(project_id, limit=20)
    return _TEMPLATES.TemplateResponse("seo.html", {
        "request": request, "project": project, "history": history,
    })


@app.get("/project/{project_id}/geo", response_class=HTMLResponse)
async def project_geo(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    history = await storage.get_geo_history(project_id, limit=20)
    return _TEMPLATES.TemplateResponse("geo.html", {
        "request": request, "project": project, "history": history,
    })


@app.get("/project/{project_id}/community", response_class=HTMLResponse)
async def project_community(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    discussions = await storage.get_tracked_discussions(project_id)
    community_history = await storage.get_community_history(project_id, limit=10)
    return _TEMPLATES.TemplateResponse("community.html", {
        "request": request, "project": project,
        "discussions": discussions, "community_history": community_history,
    })


# ---------------------------------------------------------------------------
# JSON API routes (Chart.js data sources)
# ---------------------------------------------------------------------------


@app.get("/api/project/{project_id}/seo-data")
async def api_seo_data(project_id: int):
    history = await storage.get_seo_history(project_id, limit=30)
    history.reverse()  # oldest first for charts
    return JSONResponse({
        "labels": [s["scanned_at"][:10] for s in history],
        "performance": [s["score_performance"] for s in history],
        "lcp": [s["score_lcp"] for s in history],
        "cls": [s["score_cls"] for s in history],
        "tbt": [s["score_tbt"] for s in history],
    })


@app.get("/api/project/{project_id}/geo-data")
async def api_geo_data(project_id: int):
    history = await storage.get_geo_history(project_id, limit=30)
    history.reverse()
    return JSONResponse({
        "labels": [s["scanned_at"][:10] for s in history],
        "geo_score": [s["geo_score"] for s in history],
        "visibility": [s["visibility_score"] for s in history],
        "position": [s["position_score"] for s in history],
        "sentiment": [s["sentiment_score"] for s in history],
    })


@app.get("/api/project/{project_id}/community-data")
async def api_community_data(project_id: int):
    history = await storage.get_community_history(project_id, limit=30)
    history.reverse()
    discussions = await storage.get_tracked_discussions(project_id)
    # Platform distribution
    platforms: dict[str, int] = {}
    for d in discussions:
        platforms[d["platform"]] = platforms.get(d["platform"], 0) + 1
    return JSONResponse({
        "scan_labels": [s["scanned_at"][:10] for s in history],
        "scan_hits": [s["total_hits"] for s in history],
        "platform_labels": list(platforms.keys()),
        "platform_counts": list(platforms.values()),
    })


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------


def run_server(port: int = 8080):
    import uvicorn

    load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=port)
