"""Tests for web dashboard routes."""

from unittest.mock import patch

import pytest

from opencmo import storage

# FastAPI is an optional dependency
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from opencmo.web.app import app


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        yield TestClient(app)


def test_dashboard_empty(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "OpenCMO" in resp.text


def test_dashboard_with_project(tmp_path):
    import asyncio
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        asyncio.run(storage.ensure_project("Test", "https://test.com", "testing"))
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Test" in resp.text


def test_project_not_found(client):
    resp = client.get("/project/99999")
    assert resp.status_code == 404


def test_project_pages(tmp_path):
    import asyncio
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        pid = asyncio.run(storage.ensure_project("Test", "https://test.com", "testing"))
        client = TestClient(app)
        for path in [f"/project/{pid}", f"/project/{pid}/seo", f"/project/{pid}/geo", f"/project/{pid}/community"]:
            resp = client.get(path)
            assert resp.status_code == 200, f"Failed for {path}"


def test_api_endpoints(tmp_path):
    import asyncio
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        pid = asyncio.run(storage.ensure_project("Test", "https://test.com", "testing"))
        client = TestClient(app)
        for path in [f"/api/project/{pid}/seo-data", f"/api/project/{pid}/geo-data", f"/api/project/{pid}/community-data"]:
            resp = client.get(path)
            assert resp.status_code == 200
            data = resp.json()
            assert "labels" in data or "scan_labels" in data
