"""Email report — sends persisted AI CMO reports via SMTP."""

from __future__ import annotations

import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from agents import function_tool

logger = logging.getLogger(__name__)
_REPORT_ASSET_RELATIVE_SRC_RE = re.compile(r'(<img\b[^>]*\bsrc=)(["\'])(/api/v1/report-assets/[a-f0-9]{32}\.svg)(\2)', re.IGNORECASE)


def _get_smtp_config() -> dict | None:
    """Read SMTP config from env/ContextVar. Returns None if any required var is missing."""
    from opencmo import llm

    host = llm.get_key("OPENCMO_SMTP_HOST")
    port = llm.get_key("OPENCMO_SMTP_PORT")
    user = llm.get_key("OPENCMO_SMTP_USER")
    password = llm.get_key("OPENCMO_SMTP_PASS")
    recipient = llm.get_key("OPENCMO_REPORT_EMAIL")

    if not all([host, port, user, password, recipient]):
        return None

    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "recipient": recipient,
    }


def _get_report_public_base_url() -> str:
    from opencmo import llm

    base_url = (
        llm.get_key("OPENCMO_PUBLIC_BASE_URL")
        or llm.get_key("OPENCMO_APP_BASE_URL")
        or llm.get_key("OPENCMO_REPORT_BASE_URL")
        or "https://www.aidcmo.com"
    )
    return str(base_url).rstrip("/")


def _make_report_asset_urls_absolute(html: str) -> str:
    base_url = _get_report_public_base_url()

    def replace(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}{base_url}{match.group(3)}{match.group(4)}"

    return _REPORT_ASSET_RELATIVE_SRC_RE.sub(replace, html)


async def send_report_impl(project_id: int, *, locale: str = "zh") -> dict:
    """Build and send the latest periodic human report for a project."""
    from opencmo import storage

    locale = storage.normalize_report_locale(locale)
    config = _get_smtp_config()
    if not config:
        return {"ok": False, "error": "SMTP not configured"}

    project = await storage.get_project(project_id)
    if not project:
        return {"ok": False, "error": f"Project {project_id} not found"}

    report = await storage.get_latest_report(project_id, "periodic", "human", locale=locale)
    if not report:
        from opencmo.reports import generate_periodic_report_bundle

        generated = await generate_periodic_report_bundle(project_id, source_run_id=None, locale=locale)
        report = generated["human"]
    if report.get("generation_status") != "completed" or not (report.get("content_html") or report.get("content")):
        return {"ok": False, "error": "Latest weekly report is unavailable"}

    html = _make_report_asset_urls_absolute(report.get("content_html") or f"<pre>{report.get('content', '')}</pre>")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"OpenCMO Weekly Brief: {project['brand_name']}"
    msg["From"] = config["user"]
    msg["To"] = config["recipient"]
    msg["X-OpenCMO-Report-Title"] = report.get("content", "").splitlines()[0].lstrip("# ").strip() or "Weekly Brief"
    msg.attach(MIMEText(html, "html"))

    try:
        port = config["port"]
        if port == 465:
            with smtplib.SMTP_SSL(config["host"], port, timeout=30) as server:
                server.login(config["user"], config["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(config["host"], port, timeout=30) as server:
                server.starttls()
                server.login(config["user"], config["password"])
                server.send_message(msg)
        return {
            "ok": True,
            "recipient": config["recipient"],
            "report_id": report["id"],
            "kind": report["kind"],
            "audience": report["audience"],
            "locale": report.get("locale", locale),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@function_tool
async def send_email_report(project_id: int) -> str:
    """Send an email report with latest scan data for a project.

    Args:
        project_id: The project ID to generate a report for.
    """
    result = await send_report_impl(project_id)
    if result["ok"]:
        return f"Report sent to {result['recipient']}"
    else:
        return f"Failed to send report: {result['error']}"
