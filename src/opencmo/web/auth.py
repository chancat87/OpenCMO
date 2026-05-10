"""Authentication and request-safety helpers for the web app."""

from __future__ import annotations

import hmac
import ipaddress
import os
from urllib.parse import urlparse

from fastapi import Request

PUBLIC_API_PATHS = frozenset({
    "/api/v1/auth/login",
    "/api/v1/github-stats",
    "/api/v1/health",
    "/api/v1/site/stats",
    "/api/v1/waitlist",
})

PROTECTED_DOC_PATHS = frozenset({
    "/docs",
    "/redoc",
    "/openapi.json",
})


def get_web_token() -> str:
    """Return the configured admin token, or an empty string in open/dev mode."""
    return os.environ.get("OPENCMO_WEB_TOKEN", "").strip()


def is_auth_enabled() -> bool:
    return bool(get_web_token())


def requires_workspace_auth(path: str, method: str = "GET") -> bool:
    if not is_auth_enabled():
        return False
    if path in PUBLIC_API_PATHS:
        return False
    if path in PROTECTED_DOC_PATHS:
        return True
    if path.startswith("/api/v1/"):
        return True
    return False


def request_has_valid_bearer(request: Request) -> bool:
    token = get_web_token()
    if not token:
        return False
    auth_header = request.headers.get("Authorization", "")
    scheme, _, value = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not value:
        return False
    return hmac.compare_digest(value.strip(), token)


def validate_web_token(candidate: str) -> bool:
    token = get_web_token()
    return bool(token) and hmac.compare_digest((candidate or "").strip(), token)


def _host_is_blocked(host: str) -> bool:
    normalized = host.strip().lower().rstrip(".")
    if normalized in {"localhost", "0", "0.0.0.0"}:
        return True
    if normalized.endswith(".localhost") or normalized.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    return any((
        ip.is_loopback,
        ip.is_link_local,
        ip.is_private,
        ip.is_multicast,
        ip.is_reserved,
        ip.is_unspecified,
    ))


def normalize_external_https_url(value: str, *, field_name: str = "url") -> str:
    """Validate a user-supplied external HTTPS base URL.

    The value is used by server-side provider clients, so reject obvious SSRF
    targets and plaintext protocols. Hostname DNS resolution is intentionally
    not performed here to keep request handling deterministic.
    """
    cleaned = (value or "").strip().rstrip("/")
    if not cleaned:
        return ""
    parsed = urlparse(cleaned)
    if parsed.scheme != "https":
        raise ValueError(f"{field_name} must use https")
    if not parsed.hostname or _host_is_blocked(parsed.hostname):
        raise ValueError(f"{field_name} host is not allowed")
    return cleaned
