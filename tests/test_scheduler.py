"""Tests for scheduler module."""

from unittest.mock import patch

import pytest

from opencmo import storage
from opencmo.scheduler import run_scheduled_scan


@pytest.mark.asyncio
async def test_scheduled_scan_missing_project(tmp_path):
    """Scan for non-existent project should not raise."""
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        # Ensure tables exist
        db = await storage.get_db()
        await db.close()
        await run_scheduled_scan(99999, "full")  # should just log and return


@pytest.mark.asyncio
async def test_job_crud(tmp_path):
    """Test add/list/remove scheduled jobs."""
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        pid = await storage.ensure_project("TestBrand", "https://test.com", "testing")

        job_id = await storage.add_scheduled_job(pid, "seo", "0 9 * * *")
        assert job_id > 0

        jobs = await storage.list_scheduled_jobs()
        assert len(jobs) == 1
        assert jobs[0]["brand_name"] == "TestBrand"
        assert jobs[0]["job_type"] == "seo"

        ok = await storage.remove_scheduled_job(job_id)
        assert ok is True

        jobs = await storage.list_scheduled_jobs()
        assert len(jobs) == 0
