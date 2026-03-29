"""Service layer — shared business logic for CLI and Web.

This module is a backward-compatible re-export layer.  The actual
implementations now live in focused domain modules under ``opencmo.services``:

- ``monitoring_service`` — monitors, keywords, reports, status
- ``approval_service``  — content approval queue and publishing
- ``intelligence_service`` — AI-powered URL analysis and competitor discovery
"""

from __future__ import annotations

# ── Monitoring & project management ──────────────────────────────────
from opencmo.services.monitoring_service import (  # noqa: F401
    create_monitor,
    remove_monitor,
    update_monitor,
    get_monitor,
    list_monitors,
    get_monitor_history,
    run_monitor,
    resolve_project,
    manage_keywords,
    send_project_report,
    regenerate_project_report,
    get_status_summary,
)

# ── Approval & publishing ────────────────────────────────────────────
from opencmo.services.approval_service import (  # noqa: F401
    create_approval,
    list_approvals,
    get_approval,
    approve_approval,
    reject_approval,
)

# ── AI intelligence (URL analysis, competitor discovery) ─────────────
from opencmo.services.intelligence_service import (  # noqa: F401
    analyze_url_with_ai,
    analyze_and_enrich_project,
    discover_competitors,
)
