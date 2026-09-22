import pytest
import datetime
from pathlib import Path
from unittest.mock import MagicMock

from core.settings import settings
from core.scheduling.reports import (
    _daily_ai_report_history_is_ready,
    _ai_report_payload_has_stale_inputs,
)
from core.DailyScanner import (
    _candidate_diagnostics_enabled,
    _maybe_sync_intraday,
)
import core.DailyScanner as DailyScannerModule


def test_daily_ai_report_history_is_ready_blocks_when_pending_eod():
    """Verify AI daily report does not dispatch when EOD daily bars are pending."""
    freshness = {
        "ok": True,
        "history": {
            "ok": True,
            "expected_last_working_day": "2026-09-06",
            "calendar_expected_last_working_day": "2026-09-07",
            "last_updated": "2026-09-06",
            "pending_eod_history": True,
        },
    }
    assert _daily_ai_report_history_is_ready(freshness) is False


def test_daily_ai_report_history_is_ready_allows_when_eod_complete():
    """Verify AI daily report dispatches when today's EOD daily bars are present."""
    freshness = {
        "ok": True,
        "history": {
            "ok": True,
            "expected_last_working_day": "2026-09-07",
            "calendar_expected_last_working_day": "2026-09-07",
            "last_updated": "2026-09-07",
            "pending_eod_history": False,
        },
    }
    assert _daily_ai_report_history_is_ready(freshness) is True


def test_ai_report_payload_has_stale_inputs_detects_pending_eod():
    """Verify payload is treated as stale whenever pending_eod_history is True."""
    freshness = {
        "history": {
            "pending_eod_history": True,
            "ok": True,
            "expected_last_working_day": "2026-09-06",
            "last_updated": "2026-09-06",
        }
    }
    payload = {
        "snapshot_degraded": False,
    }
    assert _ai_report_payload_has_stale_inputs(payload, freshness=freshness) is True


def test_ai_report_payload_has_stale_inputs_detects_freshness_stale():
    """Verify payload with freshness_stale issue stays pending if history is not ready."""
    freshness = {
        "history": {
            "pending_eod_history": False,
            "ok": False,
            "expected_last_working_day": "2026-09-07",
            "last_updated": "2026-09-06",
        }
    }
    payload = {
        "snapshot_degraded": True,
        "snapshot_degradation": {
            "issues": [{"reason": "freshness_stale"}],
        },
    }
    assert _ai_report_payload_has_stale_inputs(payload, freshness=freshness) is True


def test_candidate_diagnostics_enabled_for_intraday_and_pre_close():
    """Verify candidate diagnostics logging is enabled for both intraday and pre-close."""
    assert _candidate_diagnostics_enabled(is_pre_close=True, is_intraday=False) is True
    assert _candidate_diagnostics_enabled(is_pre_close=False, is_intraday=True) is True
    assert _candidate_diagnostics_enabled(is_pre_close=True, is_intraday=True) is True


def test_maybe_sync_intraday_force_bypasses_throttle(monkeypatch):
    """Verify pre-close force=True bypasses the 5-minute sync throttle."""
    DailyScannerModule._last_intraday_sync_ts = datetime.datetime.now()
    ingest_mock = MagicMock(return_value=5)
    monkeypatch.setattr("data_engine.ingest_intraday.ingest_intraday", ingest_mock)
    monkeypatch.setattr(settings, "is_market_open", lambda: True)

    # force=False should be throttled because last sync was just now
    _maybe_sync_intraday(force=False)
    assert ingest_mock.call_count == 0

    # force=True must bypass throttle and invoke ingest_intraday
    _maybe_sync_intraday(force=True)
    assert ingest_mock.call_count == 1


def test_ingestion_lock_uses_canonical_data_root(tmp_path, monkeypatch):
    """Verify ingestion lock is created inside settings.DATA_ROOT."""
    from data_engine.ingest_intraday import _ingestion_lock
    test_data_root = tmp_path / "data"
    monkeypatch.setattr(settings, "DATA_ROOT", str(test_data_root))

    with _ingestion_lock() as acquired:
        assert acquired is True
        lock_file = test_data_root / "ingest_intraday.lock"
        assert lock_file.exists()

    # Lock file should be removed upon exit
    assert not lock_file.exists()


def test_freshness_resolves_mubasher_root_dir():
    """Verify freshness evaluator correctly points to MUBASHER_ROOT_DIR."""
    from data_engine.mubasher_sqlite_source import build_paths
    root = getattr(settings, "MUBASHER_ROOT_DIR", None) or getattr(settings, "MUBASHER_PATH", None)
    assert root is not None
    paths = build_paths(Path(root), user_id=getattr(settings, "MUBASHER_USER_ID", None) or None)
    assert paths.history_db.exists()
    assert paths.intraday_db.exists()
