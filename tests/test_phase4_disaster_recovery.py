"""
TEST SUITE: PHASE 4 DISASTER RECOVERY & AUTOMATED SNAPSHOTTING
==============================================================
Validates:
1. Online zero-downtime SQLite streaming backup under active concurrent writes.
2. Integrity validation via PRAGMA integrity_check.
3. 14-day rolling backup retention pruning.
4. Deterministic database restoration with pre-restore safety snapshots.
5. AuditEngine SQLite storage integrity check.
6. APScheduler database_daily_backup cron registration (misfire_grace_time >= 300).
7. System API endpoints: GET/POST /api/v1/system/backups & full-status telemetry.
"""

import datetime
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api import app
from database.backup import (
    execute_database_backup,
    get_backup_status,
    list_backups,
    prune_backups,
    restore_database_backup,
)


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# 1. SQLite Online Streaming Backup Tests
# ---------------------------------------------------------------------------

def test_execute_database_backup_success():
    """Test online backup produces an integrity-checked snapshot with identical data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_db = Path(tmpdir) / "horus_test.db"
        backup_dir = Path(tmpdir) / "backups"

        # Initialize source DB
        conn = sqlite3.connect(str(src_db))
        conn.execute("CREATE TABLE signals (id INTEGER PRIMARY KEY, ticker TEXT, score REAL)")
        conn.execute("INSERT INTO signals VALUES (1, 'COMI', 8.5)")
        conn.execute("INSERT INTO signals VALUES (2, 'EAST', 7.2)")
        conn.commit()
        conn.close()

        # Run backup
        result = execute_database_backup(db_file=src_db, backup_dir=backup_dir, label="test_unit")

        assert result["status"] == "ok"
        assert result["integrity"] == "ok"
        assert "horus_backup_" in result["filename"]
        assert "test_unit" in result["filename"]
        assert Path(result["backup_file"]).exists()
        assert result["size_bytes"] > 0
        assert result["total_backups"] == 1

        # Verify data inside the backup
        bak_conn = sqlite3.connect(result["backup_file"])
        rows = bak_conn.execute("SELECT ticker, score FROM signals ORDER BY id").fetchall()
        bak_conn.close()

        assert rows == [("COMI", 8.5), ("EAST", 7.2)]


def test_execute_database_backup_under_active_concurrent_writes():
    """Test safe online backup while a background thread continuously writes to WAL source DB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_db = Path(tmpdir) / "horus_live.db"
        backup_dir = Path(tmpdir) / "backups"

        # Initialize WAL mode on live source
        conn = sqlite3.connect(str(src_db))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE ticks (id INTEGER PRIMARY KEY, price REAL, created_at TEXT)")
        conn.commit()
        conn.close()

        stop_writing = threading.Event()

        def writer():
            idx = 0
            while not stop_writing.is_set():
                try:
                    c = sqlite3.connect(str(src_db), timeout=5)
                    c.execute(
                        "INSERT INTO ticks (price, created_at) VALUES (?, ?)",
                        (100.0 + idx, datetime.datetime.now().isoformat())
                    )
                    c.commit()
                    c.close()
                    idx += 1
                except Exception:
                    pass
                time.sleep(0.005)

        writer_thread = threading.Thread(target=writer)
        writer_thread.start()

        try:
            time.sleep(0.05)
            # Execute backup concurrently while active writes occur
            result = execute_database_backup(db_file=src_db, backup_dir=backup_dir)

            assert result["status"] == "ok"
            assert result["integrity"] == "ok"
            assert Path(result["backup_file"]).exists()

            # Verify backup integrity and row presence
            bak_conn = sqlite3.connect(result["backup_file"])
            count = bak_conn.execute("SELECT COUNT(*) FROM ticks").fetchone()[0]
            integrity = bak_conn.execute("PRAGMA integrity_check;").fetchone()[0]
            bak_conn.close()

            assert count > 0
            assert integrity == "ok"
        finally:
            stop_writing.set()
            writer_thread.join()


# ---------------------------------------------------------------------------
# 2. Retention Pruning Tests
# ---------------------------------------------------------------------------

def test_backup_retention_pruning():
    """Test that backups older than max_retention_days are purged, while recent ones are kept."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = Path(tmpdir) / "backups"
        backup_dir.mkdir()

        now = time.time()
        day_seconds = 86400

        # Create 4 test files with simulated mtimes:
        # File 1: 25 days old (expired)
        # File 2: 18 days old (expired)
        # File 3: 5 days old (keep)
        # File 4: today (keep)
        expired_1 = backup_dir / "horus_backup_20260810_120000.db"
        expired_2 = backup_dir / "horus_backup_20260817_120000.db"
        recent_1 = backup_dir / "horus_backup_20260830_120000.db"
        recent_2 = backup_dir / "horus_backup_20260904_120000.db"

        for p in (expired_1, expired_2, recent_1, recent_2):
            p.write_text("sqlite placeholder")

        os.utime(str(expired_1), (now - 25 * day_seconds, now - 25 * day_seconds))
        os.utime(str(expired_2), (now - 18 * day_seconds, now - 18 * day_seconds))
        os.utime(str(recent_1), (now - 5 * day_seconds, now - 5 * day_seconds))
        os.utime(str(recent_2), (now - 1 * day_seconds, now - 1 * day_seconds))

        pruned = prune_backups(backup_dir, max_retention_days=14)

        assert pruned == 2
        assert not expired_1.exists()
        assert not expired_2.exists()
        assert recent_1.exists()
        assert recent_2.exists()


# ---------------------------------------------------------------------------
# 3. Restoration & Safety Snapshot Tests
# ---------------------------------------------------------------------------

def test_restore_database_backup():
    """Test restoring target DB from backup file creates safety snapshot and restores state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_db = Path(tmpdir) / "horus_active.db"
        backup_dir = Path(tmpdir) / "backups"

        # Create version 1 state
        conn = sqlite3.connect(str(src_db))
        conn.execute("CREATE TABLE config (key TEXT PRIMARY KEY, val TEXT)")
        conn.execute("INSERT INTO config VALUES ('version', '1.0.0')")
        conn.commit()
        conn.close()

        # Take backup of version 1
        bak_res = execute_database_backup(db_file=src_db, backup_dir=backup_dir, label="v1")
        assert bak_res["status"] == "ok"
        v1_backup_file = Path(bak_res["backup_file"])

        # Mutate target DB to version 2
        conn = sqlite3.connect(str(src_db))
        conn.execute("UPDATE config SET val = '2.0.0' WHERE key = 'version'")
        conn.commit()
        conn.close()

        # Verify mutation
        conn = sqlite3.connect(str(src_db))
        assert conn.execute("SELECT val FROM config WHERE key = 'version'").fetchone()[0] == "2.0.0"
        conn.close()

        # Execute restore from v1 backup
        restore_res = restore_database_backup(
            backup_file=v1_backup_file,
            target_db_file=src_db,
            create_safety_snapshot=True,
        )

        assert restore_res["status"] == "ok"
        assert restore_res["safety_snapshot"] is not None
        assert Path(restore_res["safety_snapshot"]).exists()

        # Verify DB is rolled back to version 1
        conn = sqlite3.connect(str(src_db))
        assert conn.execute("SELECT val FROM config WHERE key = 'version'").fetchone()[0] == "1.0.0"
        conn.close()


# ---------------------------------------------------------------------------
# 4. AuditEngine SQLite Storage Integrity Tests
# ---------------------------------------------------------------------------

def test_audit_engine_sqlite_storage_integrity(monkeypatch):
    """Test that AuditEngine.run_system_audit includes SQLite Storage Integrity check."""
    from core import AuditEngine

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "audit_test.db"
        conn = sqlite3.connect(str(test_db))
        conn.execute("CREATE TABLE audit_probe (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

        monkeypatch.setattr("database.backup._resolve_db_file", lambda db_file=None: test_db)

        report = AuditEngine.run_system_audit()

        checks = {c["name"]: c for c in report.get("checks", [])}
        assert "SQLite Storage Integrity" in checks
        storage_check = checks["SQLite Storage Integrity"]
        assert storage_check["status"] == "PASS"
        assert "integrity_check verified ok" in storage_check["detail"]


# ---------------------------------------------------------------------------
# 5. APScheduler Daily Backup Registration Tests
# ---------------------------------------------------------------------------

def test_scheduler_database_daily_backup_registration():
    """Test that database_daily_backup cron job is registered with misfire_grace_time >= 300."""
    from config.scheduler_setup import register_scheduled_jobs

    mock_scheduler = MagicMock()
    mock_scheduler.running = False

    added_jobs = {}
    def fake_add_job(func, trigger, **kwargs):
        job_id = kwargs.get("id")
        added_jobs[job_id] = kwargs

    mock_scheduler.add_job.side_effect = fake_add_job

    register_scheduled_jobs(mock_scheduler)

    assert "database_daily_backup" in added_jobs, "database_daily_backup not registered in scheduler"
    job_kwargs = added_jobs["database_daily_backup"]
    grace = job_kwargs.get("misfire_grace_time")
    assert grace is not None and grace >= 300, f"misfire_grace_time ({grace}) must be >= 300"
    assert job_kwargs.get("coalesce") is True, "database_daily_backup must have coalesce=True"


# ---------------------------------------------------------------------------
# 6. REST API Endpoints Tests
# ---------------------------------------------------------------------------

def test_system_backups_api(client, monkeypatch):
    """Test GET and POST /api/v1/system/backups endpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "horus.db"
        test_backup_dir = Path(tmpdir) / "backups"
        test_backup_dir.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(test_db))
        conn.execute("CREATE TABLE app_meta (name TEXT)")
        conn.commit()
        conn.close()

        monkeypatch.setattr("database.backup._resolve_db_file", lambda db_file=None: test_db)
        monkeypatch.setattr("database.backup._resolve_backup_dir", lambda backup_dir=None: test_backup_dir)

        # GET /api/v1/system/backups initially empty
        resp = client.get("/api/v1/system/backups")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["count"] == 0
        assert data["summary"]["configured"] is True

        # POST /api/v1/system/backups trigger manual snapshot
        create_resp = client.post("/api/v1/system/backups", json={"label": "api_test"})
        assert create_resp.status_code == 200
        create_data = create_resp.json()
        assert create_data["status"] == "success"
        assert "horus_backup_" in create_data["backup"]["filename"]
        assert "api_test" in create_data["backup"]["filename"]

        # GET /api/v1/system/backups reflects newly created backup
        list_resp = client.get("/api/v1/system/backups")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["count"] == 1
        assert list_data["summary"]["backup_count"] == 1
        assert list_data["summary"]["status"] == "HEALTHY"


def test_full_system_status_includes_backup(client):
    """Test GET /api/v1/system/full-status includes database_backup telemetry."""
    resp = client.get("/api/v1/system/full-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "database_backup" in data
    backup_info = data["database_backup"]
    assert backup_info.get("configured") is True
    assert "status" in backup_info
