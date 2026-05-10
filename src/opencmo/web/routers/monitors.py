"""Monitors API router."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse, urlunparse

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1")

_DNS_LABEL_RE = re.compile(r"^[A-Za-z0-9-]+$")


def _normalize_locale(value: str | None) -> str:
    locale = (value or "en").strip().lower()
    if locale.startswith("zh"):
        return "zh"
    if locale.startswith("ja"):
        return "ja"
    if locale.startswith("ko"):
        return "ko"
    if locale.startswith("es"):
        return "es"
    return "en"


def _is_valid_hostname(hostname: str) -> bool:
    if hostname == "localhost":
        return True
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass
    if "." not in hostname:
        return False
    labels = hostname.split(".")
    return all(
        label
        and len(label) <= 63
        and _DNS_LABEL_RE.fullmatch(label)
        and not label.startswith("-")
        and not label.endswith("-")
        for label in labels
    )


def _normalize_monitor_url(raw_url: str) -> tuple[str, str]:
    value = raw_url.strip()
    if not value:
        return "", "url_required"
    if any(char.isspace() for char in value):
        return "", "invalid_url"
    if "://" not in value:
        value = f"https://{value}"

    parsed = urlparse(value)
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname or ""
    try:
        port = parsed.port
    except ValueError:
        return "", "invalid_url"
    if port is not None and not 1 <= port <= 65535:
        return "", "invalid_url"
    if scheme not in {"http", "https"} or not hostname or not _is_valid_hostname(hostname.lower()):
        return "", "invalid_url"

    netloc = parsed.netloc
    if parsed.hostname:
        host_start = netloc.rfind(parsed.hostname)
        if host_start >= 0:
            netloc = f"{netloc[:host_start]}{parsed.hostname.lower()}{netloc[host_start + len(parsed.hostname):]}"
    return urlunparse(parsed._replace(scheme=scheme, netloc=netloc)), ""


async def _enqueue_scan_task(
    *,
    monitor_id: int,
    project_id: int,
    job_type: str,
    job_id: int,
    analyze_url: str | None = None,
    locale: str = "en",
) -> dict:
    from opencmo.background import service as bg_service

    payload = {
        "monitor_id": monitor_id,
        "project_id": project_id,
        "job_type": job_type,
        "job_id": job_id,
        "locale": locale,
    }
    if analyze_url:
        payload["analyze_url"] = analyze_url

    return await bg_service.enqueue_task(
        kind="scan",
        project_id=project_id,
        payload=payload,
        dedupe_key=f"scan:monitor:{monitor_id}",
    )


def _pending_scan_response(task: dict) -> dict:
    payload = task["payload"]
    return {
        "task_id": task["task_id"],
        "monitor_id": payload["monitor_id"],
        "project_id": task["project_id"],
        "job_type": payload["job_type"],
        "status": "pending",
        "created_at": task["created_at"],
        "completed_at": task["completed_at"],
        "error": None,
        "progress": [],
        "run_id": None,
        "summary": "",
        "findings_count": 0,
        "recommendations_count": 0,
    }


@router.get("/monitors")
async def api_v1_monitors():
    from opencmo import service
    return JSONResponse(await service.list_monitors())


@router.post("/monitors")
async def api_v1_create_monitor(request: Request):
    from opencmo import service

    body = await request.json()
    url, url_error = _normalize_monitor_url(body.get("url", ""))
    if url_error == "url_required":
        return JSONResponse({"error": "url is required", "error_code": "url_required"}, status_code=400)
    if url_error:
        return JSONResponse(
            {
                "error": "Enter a valid website URL, for example https://example.com.",
                "error_code": "invalid_url",
            },
            status_code=400,
        )
    # Auto-derive brand from URL domain if not provided
    brand = body.get("brand", "").strip()
    if not brand:
        domain = urlparse(url).hostname or ""
        brand = domain.removeprefix("www.").split(".")[0].capitalize() or domain
    category = body.get("category", "").strip() or "auto"
    job_type = body.get("job_type", "full")
    locale = _normalize_locale(body.get("locale", "en"))
    result = await service.create_monitor(
        brand, url, category,
        job_type=job_type,
        locale=locale,
        cron_expr=body.get("cron_expr", "0 9 * * *"),
        keywords=body.get("keywords"),
    )
    # Auto-trigger: AI analysis (extract brand/category/keywords) + first scan
    task = await _enqueue_scan_task(
        monitor_id=result["monitor_id"],
        project_id=result["project_id"],
        job_type=job_type,
        job_id=result["monitor_id"],
        analyze_url=url,
        locale=locale,
    )
    if task:
        result["task_id"] = task["task_id"]
    return JSONResponse(result, status_code=201)


@router.delete("/monitors/{monitor_id}")
async def api_v1_delete_monitor(monitor_id: int):
    from opencmo import service
    ok = await service.remove_monitor(monitor_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@router.patch("/monitors/{monitor_id}")
async def api_v1_update_monitor(monitor_id: int, request: Request):
    from opencmo import service

    body = await request.json()
    cron_expr = body.get("cron_expr")
    enabled = body.get("enabled")
    if cron_expr is None and enabled is None:
        return JSONResponse({"error": "Nothing to update"}, status_code=400)
    ok = await service.update_monitor(monitor_id, cron_expr=cron_expr, enabled=enabled)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@router.post("/monitors/{monitor_id}/run")
async def api_v1_run_monitor(monitor_id: int, request: Request):
    from opencmo import service
    from opencmo.background import service as bg_service

    job = await service.get_monitor(monitor_id)
    if not job:
        return JSONResponse({"error": "Monitor not found"}, status_code=404)

    # Support optional force parameter in request body
    force = False
    locale_override: str | None = None
    try:
        body = await request.json()
        force = bool(body.get("force", False))
        locale_override = _normalize_locale(body.get("locale")) if body.get("locale") else None
    except Exception:
        pass

    existing = await bg_service.find_active_task_by_dedupe_key(f"scan:monitor:{monitor_id}")
    if existing is not None:
        if not force:
            return JSONResponse({"error": "Monitor is already running"}, status_code=409)
        # Force: mark the existing task as failed, then enqueue a new one
        await bg_service.fail_task(
            existing["task_id"],
            error={"message": "Superseded by forced re-run"},
        )

    if locale_override and locale_override != job.get("locale", "en"):
        await service.update_monitor(monitor_id, locale=locale_override)
        job["locale"] = locale_override

    record = await _enqueue_scan_task(
        monitor_id=monitor_id,
        project_id=job["project_id"],
        job_type=job["job_type"],
        job_id=monitor_id,
        locale=locale_override or job.get("locale", "en"),
    )
    return JSONResponse(_pending_scan_response(record), status_code=202)
