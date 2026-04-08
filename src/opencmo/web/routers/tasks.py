"""Tasks and scan runs API router."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from opencmo import storage
from opencmo.background import service as bg_service
from opencmo.opportunities import build_project_opportunity_snapshot

router = APIRouter(prefix="/api/v1")

_SCAN_STAGE_ORDER = [
    "context_build",
    "signal_collect",
    "signal_normalize",
    "domain_review",
    "strategy_synthesis",
    "persist_publish",
]


def _compat_status(status: str) -> str:
    if status in {"queued", "claimed"}:
        return "pending"
    if status == "cancel_requested":
        return "running"
    if status == "cancelled":
        return "failed"
    return status


def _progress_from_events(events: list[dict]) -> list[dict]:
    progress: list[dict] = []
    for event in events:
        if event["event_type"] != "progress":
            continue
        payload = event["payload"] or {}
        if payload:
            progress.append(payload)
            continue
        progress.append(
            {
                "stage": event["phase"],
                "status": event["status"],
                "summary": event["summary"],
            }
        )
    return progress


def _latest_stage_cards(events: list[dict]) -> list[dict]:
    cards: dict[str, dict] = {}
    for event in events:
        if event["event_type"] != "progress":
            continue
        payload = event["payload"] or {}
        stage = payload.get("stage") or event["phase"] or ""
        if not stage:
            continue
        summary = payload.get("summary") or payload.get("detail") or event["summary"] or ""
        cards[stage] = {
            "stage": stage,
            "status": payload.get("status") or event["status"] or "running",
            "summary": summary,
            "agent": payload.get("agent") or "",
            "event_count": cards.get(stage, {}).get("event_count", 0) + 1,
        }

    return sorted(
        cards.values(),
        key=lambda item: (
            _SCAN_STAGE_ORDER.index(item["stage"])
            if item["stage"] in _SCAN_STAGE_ORDER
            else len(_SCAN_STAGE_ORDER),
            item["stage"],
        ),
    )


def _resolution_hint(summary: str) -> str:
    text = (summary or "").lower()
    if "api key" in text or "no llm" in text:
        return "Configure the missing provider keys, then rerun the scan for full analysis coverage."
    if "fallback" in text:
        return "Fallback coverage is usable, but review the source evidence before acting on it."
    if "rate limit" in text or "429" in text:
        return "Retry after the provider limit resets, or add a dedicated API key to reduce throttling."
    if "failed" in text or "error" in text:
        return "Retry the scan. If the issue persists, inspect provider configuration and network access."
    return "Review this stage before acting on the final recommendations."


def _scan_issues(events: list[dict], task_error: str | None = None) -> list[dict]:
    issues: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for event in events:
        if event["event_type"] != "progress":
            continue
        payload = event["payload"] or {}
        status = payload.get("status") or event["status"] or ""
        if status not in {"warning", "failed"}:
            continue
        stage = payload.get("stage") or event["phase"] or "unknown"
        summary = payload.get("summary") or payload.get("detail") or event["summary"] or ""
        key = (stage, summary)
        if key in seen:
            continue
        seen.add(key)
        issues.append(
            {
                "stage": stage,
                "status": status,
                "summary": summary,
                "resolution": _resolution_hint(summary),
            }
        )

    if task_error:
        issues.append(
            {
                "stage": "task",
                "status": "failed",
                "summary": task_error,
                "resolution": _resolution_hint(task_error),
            }
        )

    return issues


def _unique_domains(findings: list[dict], recommendations: list[dict], opportunities: list[dict] | None = None) -> list[str]:
    ordered: list[str] = []
    for item in findings + recommendations + (opportunities or []):
        domain = item.get("domain")
        if domain and domain not in ordered:
            ordered.append(domain)
    return ordered


def _overview_headline(task: dict, findings: list[dict], recommendations: list[dict]) -> str:
    if task["status"] == "failed":
        return (task["error"] or {}).get("message") or "Scan failed before a complete monitoring brief was created."
    if findings or recommendations:
        return (
            f"{len(findings)} findings and {len(recommendations)} "
            f"{'recommended action' if len(recommendations) == 1 else 'recommended actions'} ready."
        )
    return (task["result"] or {}).get("summary") or "Initial scan completed."


async def _serialize_scan_artifacts(task: dict) -> dict:
    events = await bg_service.list_task_events(task["task_id"])
    findings = await storage.get_task_findings(task["task_id"])
    recommendations = await storage.get_task_recommendations(task["task_id"])
    snapshot = await build_project_opportunity_snapshot(task["project_id"])
    opportunities = snapshot["opportunities"]
    error_message = (task["error"] or {}).get("message")

    return {
        "overview": {
            "headline": _overview_headline(task, findings, recommendations),
            "findings_count": len(findings),
            "recommendations_count": len(recommendations),
            "focus_domains": _unique_domains(findings, recommendations, opportunities["top"]),
        },
        "stage_cards": _latest_stage_cards(events),
        "issues": _scan_issues(events, error_message if task["status"] == "failed" else None),
        "brief": {
            "top_findings": findings[:3],
            "top_recommendations": recommendations[:3],
        },
        "opportunities": opportunities,
        "cluster_summary": snapshot["cluster_summary"],
    }


async def _serialize_scan_task(task: dict) -> dict:
    events = await bg_service.list_task_events(task["task_id"])
    payload = task["payload"]
    result = task["result"] or {}
    error = task["error"] or {}
    return {
        "task_id": task["task_id"],
        "task_kind": "scan",
        "monitor_id": payload["monitor_id"],
        "project_id": task["project_id"],
        "job_type": payload["job_type"],
        "status": _compat_status(task["status"]),
        "created_at": task["created_at"],
        "completed_at": task["completed_at"],
        "error": error.get("message"),
        "progress": _progress_from_events(events),
        "run_id": result.get("run_id"),
        "summary": result.get("summary") or error.get("message") or "",
        "findings_count": result.get("findings_count", 0),
        "recommendations_count": result.get("recommendations_count", 0),
    }


async def _serialize_report_task(task: dict) -> dict:
    events = await bg_service.list_task_events(task["task_id"])
    payload = task["payload"]
    result = task["result"] or {}
    error = task["error"] or {}
    return {
        "task_id": task["task_id"],
        "task_kind": "report",
        "report_kind": payload["kind"],
        "project_id": task["project_id"],
        "status": _compat_status(task["status"]),
        "created_at": task["created_at"],
        "completed_at": task["completed_at"],
        "error": error.get("message"),
        "progress": _progress_from_events(events),
        "summary": result.get("summary") or error.get("message") or "",
    }


async def _serialize_graph_task(task: dict) -> dict:
    events = await bg_service.list_task_events(task["task_id"])
    payload = task["payload"]
    result = task["result"] or {}
    error = task["error"] or {}
    return {
        "task_id": task["task_id"],
        "task_kind": "graph_expansion",
        "project_id": task["project_id"],
        "status": _compat_status(task["status"]),
        "created_at": task["created_at"],
        "completed_at": task["completed_at"],
        "error": error.get("message"),
        "progress": _progress_from_events(events),
        "summary": result.get("summary") or error.get("message") or "",
        "runtime_state": result.get("runtime_state"),
        "current_wave": result.get("current_wave"),
        "nodes_discovered": result.get("nodes_discovered"),
        "nodes_explored": result.get("nodes_explored"),
        "graph_project_id": payload["project_id"],
    }


async def serialize_background_task(task: dict) -> dict:
    kind = task["kind"]
    if kind == "scan":
        return await _serialize_scan_task(task)
    if kind == "report":
        return await _serialize_report_task(task)
    if kind == "graph_expansion":
        return await _serialize_graph_task(task)
    raise ValueError(f"Unsupported background task kind: {kind}")


@router.get("/tasks")
async def api_v1_tasks():
    tasks = await bg_service.list_tasks(limit=200)
    return JSONResponse([await serialize_background_task(task) for task in tasks])


@router.get("/tasks/{task_id}")
async def api_v1_task(task_id: str):
    record = await bg_service.get_task(task_id)
    if record is None:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(await serialize_background_task(record))


@router.get("/tasks/{task_id}/artifacts")
async def api_v1_task_artifacts(task_id: str):
    record = await bg_service.get_task(task_id)
    if record is None:
        return JSONResponse({"error": "Not found"}, status_code=404)
    if record["kind"] != "scan":
        return JSONResponse({"error": "Artifacts are only available for scan tasks"}, status_code=400)
    return JSONResponse(await _serialize_scan_artifacts(record))


@router.get("/tasks/{task_id}/findings")
async def api_v1_task_findings(task_id: str):
    return JSONResponse(await storage.get_task_findings(task_id))


@router.get("/tasks/{task_id}/recommendations")
async def api_v1_task_recommendations(task_id: str):
    return JSONResponse(await storage.get_task_recommendations(task_id))


@router.patch("/tasks/{task_id}/notes")
async def api_v1_task_update_notes(task_id: str, body: dict):
    """Update the editable notes/summary for a completed scan run."""
    notes = body.get("notes", "")
    await storage.update_scan_run_notes(task_id, notes)
    return JSONResponse({"ok": True})


@router.get("/monitors/{monitor_id}/runs")
async def api_v1_monitor_runs(monitor_id: int):
    return JSONResponse(await storage.list_scan_runs_by_monitor(monitor_id))
