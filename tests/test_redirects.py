"""Server-side 301 redirects for legacy paths.

Both GET and HEAD must return 301 (production smoke uses ``curl -I`` =
HEAD, and the catch-all has both methods, so missing HEAD = 405).

Locale prefix MUST be preserved on the target. Otherwise users on
the EN site clicking a stale link land on the root, not /en/.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    monkeypatch.setattr(storage, "_SCHEMA_READY_FOR", None, raising=False)

    from opencmo.web.app import app
    return TestClient(app, follow_redirects=False)


# (request_path, expected_location) — covers all 12 (4 paths × 3 locales)
_REDIRECT_CASES = [
    ("/b2b-leads",       "/services"),
    ("/en/b2b-leads",    "/en/services"),
    ("/zh/b2b-leads",    "/zh/services"),
    ("/sample-data",     "/services"),
    ("/en/sample-data",  "/en/services"),
    ("/zh/sample-data",  "/zh/services"),
    ("/data-policy",     "/"),
    ("/en/data-policy",  "/en"),
    ("/zh/data-policy",  "/zh"),
    ("/seo-geo",         "/services"),
    ("/en/seo-geo",      "/en/services"),
    ("/zh/seo-geo",      "/zh/services"),
]


@pytest.mark.parametrize("path, expected", _REDIRECT_CASES)
def test_get_redirects_301_with_correct_location(client, path, expected):
    r = client.get(path)
    assert r.status_code == 301, (
        f"GET {path}: got {r.status_code}, expected 301. "
        f"If 422, the redirect handler treats `request` as a query param "
        f"(forgot typed Request annotation)."
    )
    assert r.headers.get("location") == expected, (
        f"GET {path}: location {r.headers.get('location')!r} != {expected!r}. "
        f"If all targets are the same, _make_redirect closure has late-binding bug."
    )


@pytest.mark.parametrize("path, expected", _REDIRECT_CASES)
def test_head_redirects_301_with_correct_location(client, path, expected):
    """curl -I (HEAD) is the standard production smoke."""
    r = client.head(path)
    assert r.status_code == 301, (
        f"HEAD {path}: got {r.status_code}. If 405, redirect routes are missing "
        f"methods=['GET', 'HEAD']."
    )
    assert r.headers.get("location") == expected


def test_locales_distinct(client):
    """Confirm we don't have closure late-binding bug — different new
    targets for different old paths must come through correctly."""
    seo_target = client.get("/seo-geo").headers.get("location")
    data_target = client.get("/data-policy").headers.get("location")
    assert seo_target == "/services"
    assert data_target == "/"
    assert seo_target != data_target
