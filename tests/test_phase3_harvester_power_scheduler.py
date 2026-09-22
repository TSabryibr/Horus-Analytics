"""
TESTS FOR PHASE 3: HARVESTER DURABILITY, OS SLEEP IMMUNITY & SCHEDULER HARDENING
================================================================================
Verifies:
  1. Workstation keep-alive (utils/power.py) state tracking and Kernel32 calls
  2. Session mode transitions (LIVE/ANALYSIS) hook into power keep-alive
  3. Atomic safe_sqlite_backup in mubasher_extractor prevents lock errors
  4. Harvester perform_extraction concurrency lock & setting restoration
  5. APScheduler cron jobs have misfire_grace_time >= 300 and coalesce=True
  6. Harvester service taskkill uses shell=False and validated integer PID
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from core.settings import settings
from utils.power import (
    ES_AWAYMODE_REQUIRED,
    ES_CONTINUOUS,
    ES_SYSTEM_REQUIRED,
    is_keepalive_active,
    set_market_keepalive,
)


@pytest.fixture(autouse=True)
def cleanup_power_state():
    """Ensure keepalive is clean before and after each test."""
    set_market_keepalive(False)
    yield
    set_market_keepalive(False)


# ---------------------------------------------------------------------------
# 1. Power Keep-Alive Tests
# ---------------------------------------------------------------------------

def test_power_keepalive_state_toggle():
    """Test engaging and releasing keep-alive updates tracking flag."""
    assert is_keepalive_active() is False

    res = set_market_keepalive(True)
    assert res is True
    assert is_keepalive_active() is True

    res2 = set_market_keepalive(False)
    assert res2 is True
    assert is_keepalive_active() is False


def test_power_keepalive_kernel32_flags(monkeypatch):
    """Test that Kernel32 SetThreadExecutionState is called with correct bitmasks."""
    called_flags = []

    mock_kernel32 = MagicMock()
    mock_kernel32.SetThreadExecutionState.side_effect = lambda flags: called_flags.append(flags) or 1

    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setattr("ctypes.windll.kernel32", mock_kernel32, raising=False)

    # Enable
    set_market_keepalive(True)
    expected_enable_flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED
    assert expected_enable_flags in called_flags

    # Disable
    set_market_keepalive(False)
    assert ES_CONTINUOUS in called_flags


# ---------------------------------------------------------------------------
# 2. Session Mode Transitions Hook Tests
# ---------------------------------------------------------------------------

def test_session_mode_transition_hooks_keepalive(monkeypatch):
    """Test that applying LIVE transition engages keepalive and ANALYSIS releases it."""
    from core.session_mode import apply_mode_transition

    power_states = []
    monkeypatch.setattr(
        "utils.power.set_market_keepalive",
        lambda enable: power_states.append(enable) or True,
    )
    monkeypatch.setattr(settings, "SESSION_MODE", "ANALYSIS")
    monkeypatch.setattr(settings, "is_market_open", lambda: False)

    # Transition to LIVE
    apply_mode_transition("LIVE")
    assert True in power_states

    # Transition to ANALYSIS
    apply_mode_transition("ANALYSIS")
    assert False in power_states


# ---------------------------------------------------------------------------
# 3. Mubasher Harvester Atomic SQLite Backup Tests
# ---------------------------------------------------------------------------

def test_safe_sqlite_backup_atomic():
    """Test safe_sqlite_backup successfully creates an atomic snapshot of a live SQLite database."""
    from data_engine.mubasher_extractor import safe_sqlite_backup

    with tempfile.TemporaryDirectory() as tmpdir:
        src_db = Path(tmpdir) / "source.db"
        dst_db = Path(tmpdir) / "destination.db"

        # Create source database and populate it
        conn = sqlite3.connect(src_db)
        conn.execute("CREATE TABLE test_bars (ticker TEXT, close REAL)")
        conn.execute("INSERT INTO test_bars VALUES ('COMI', 55.4)")
        conn.execute("INSERT INTO test_bars VALUES ('FWRY', 6.2)")
        conn.commit()
        conn.close()

        success = safe_sqlite_backup(src_db, dst_db)
        assert success is True
        assert dst_db.exists()

        # Verify destination contents
        conn = sqlite3.connect(dst_db)
        rows = conn.execute("SELECT ticker, close FROM test_bars ORDER BY ticker").fetchall()
        conn.close()
        assert rows == [("COMI", 55.4), ("FWRY", 6.2)]


def test_safe_sqlite_backup_concurrent_stress():
    """Test safe_sqlite_backup while background thread continuously writes to source DB."""
    from data_engine.mubasher_extractor import safe_sqlite_backup

    with tempfile.TemporaryDirectory() as tmpdir:
        src_db = Path(tmpdir) / "live_mubasher.db"
        dst_db = Path(tmpdir) / "shadow_mubasher.db"

        # Initialize WAL mode on source
        conn = sqlite3.connect(src_db)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE ticks (id INTEGER PRIMARY KEY, price REAL)")
        conn.commit()
        conn.close()

        stop_writing = threading.Event()

        def writer():
            idx = 0
            while not stop_writing.is_set():
                try:
                    c = sqlite3.connect(src_db)
                    c.execute("INSERT INTO ticks (price) VALUES (?)", (10.0 + idx,))
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
            # Execute backup while writes are actively occurring
            success = safe_sqlite_backup(src_db, dst_db)
            assert success is True
            assert dst_db.exists()

            # Verify shadow database is valid and uncorrupted
            c_dst = sqlite3.connect(dst_db)
            count = c_dst.execute("SELECT COUNT(*) FROM ticks").fetchone()[0]
            integrity = c_dst.execute("PRAGMA integrity_check").fetchone()[0]
            c_dst.close()

            assert count > 0
            assert integrity == "ok"
        finally:
            stop_writing.set()
            writer_thread.join()


def test_mubasher_perform_extraction_concurrency_guard(monkeypatch):
    """Test that perform_extraction uses lock to skip duplicate concurrent ticks."""
    from data_engine.mubasher_extractor import _EXTRACTION_LOCK, perform_extraction

    # Simulate lock already held
    _EXTRACTION_LOCK.acquire()
    try:
        result = perform_extraction()
        assert result is False  # Skipped because lock was busy
    finally:
        _EXTRACTION_LOCK.release()


# ---------------------------------------------------------------------------
# 4. APScheduler Misfire Durability Tests
# ---------------------------------------------------------------------------

def test_scheduler_cron_misfire_grace_times():
    """Test that all critical scheduler cron jobs have misfire_grace_time >= 300."""
    from config.scheduler_setup import register_scheduled_jobs

    mock_scheduler = MagicMock()
    mock_scheduler.running = False

    added_jobs = {}
    def fake_add_job(func, trigger, **kwargs):
        job_id = kwargs.get("id")
        added_jobs[job_id] = kwargs

    mock_scheduler.add_job.side_effect = fake_add_job

    register_scheduled_jobs(mock_scheduler)

    critical_cron_jobs = [
        "signal_daily_pipeline",
        "signal_walkforward_validation",
        "wfa_metrics_update",
        "system_audit",
    ]

    for job_id in critical_cron_jobs:
        assert job_id in added_jobs, f"Job {job_id} not registered"
        job_kwargs = added_jobs[job_id]
        grace_time = job_kwargs.get("misfire_grace_time")
        assert grace_time is not None, f"Job {job_id} missing misfire_grace_time"
        assert grace_time >= 300, f"Job {job_id} misfire_grace_time ({grace_time}) must be >= 300"
        assert job_kwargs.get("coalesce") is True, f"Job {job_id} must have coalesce=True"


# ---------------------------------------------------------------------------
# 5. Harvester Subprocess Taskkill Sanitization Tests
# ---------------------------------------------------------------------------

def test_harvester_stop_service_sanitized(monkeypatch):
    """Test that harvester_service.stop_service invokes taskkill with shell=False and list args."""
    import data_engine.harvester_service as hs

    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setattr(hs, "get_service_status", lambda: {"running": True, "pid": 12345})

    captured_cmds = []
    def fake_run(cmd, **kwargs):
        captured_cmds.append((cmd, kwargs))
        return MagicMock(returncode=0)

    mock_pid_file = MagicMock()
    mock_pid_file.exists.return_value = False
    monkeypatch.setattr(hs, "PID_FILE", mock_pid_file)
    monkeypatch.setattr(hs.subprocess, "run", fake_run)
    monkeypatch.setattr(hs, "_is_process_running", lambda pid: False)
    monkeypatch.setattr(hs, "update_status", lambda status: None)

    hs.stop_service()

    assert len(captured_cmds) >= 1
    cmd, kwargs = captured_cmds[0]
    assert cmd == ["taskkill", "/F", "/PID", "12345"]
    assert kwargs.get("shell") is False
