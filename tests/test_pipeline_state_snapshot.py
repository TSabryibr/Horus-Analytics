from core.settings import settings
import pytest

from core import pipeline
from routes.shared import update_system_state


@pytest.fixture(autouse=True)
def reset_pipeline_state_cache(monkeypatch):
    monkeypatch.delenv("HORUS_DISABLE_READINESS_GATE", raising=False)
    with pipeline._PIPELINE_STATE_CACHE_LOCK:
        pipeline._PIPELINE_STATE_CACHE.clear()
        pipeline._PIPELINE_STATE_CACHE.update({"ts": 0.0, "snapshot": None})
    yield
    with pipeline._PIPELINE_STATE_CACHE_LOCK:
        pipeline._PIPELINE_STATE_CACHE.clear()
        pipeline._PIPELINE_STATE_CACHE.update({"ts": 0.0, "snapshot": None})


def test_refresh_pipeline_state_rewrites_fresh_message_when_worker_is_degraded(monkeypatch):
    update_system_state(
        {
            "status": "READY",
            "message": "Data pipeline is fresh.",
            "bootstrap_complete": True,
            "pipeline_state": "FRESH",
            "stale_mode": False,
            "data_version": 0,
            "freshness": {
                "history_fresh_ratio": 1.0,
                "intraday_live_ratio": 1.0,
                "history_ok": True,
                "intraday_ok": True,
                "market_open": True,
                "overall_ok": True,
                "checked_at": "2026-03-16T12:00:00",
                "session_mode": "LIVE",
            },
        }
    )
    monkeypatch.setattr(
        "core.pipeline.read_worker_state",
        lambda: {
            "enabled": True,
            "running": True,
            "syncing": False,
            "pipeline_state": "DEGRADED",
        },
    )
    monkeypatch.setattr(
        "core.pipeline._evaluate_freshness_with_timeout",
        lambda timeout_seconds: {
            "history": {"ok": False, "kpis": {"fresh_ratio": 0.0}},
            "intraday": {"ok": True, "kpis": {"live_ratio": 1.0}},
        },
    )

    snapshot = pipeline.refresh_pipeline_state(force=True)

    assert snapshot["pipeline_state"] == "DEGRADED"
    assert snapshot["stale_mode"] is True
    assert snapshot["message"] == "History freshness is below threshold. Read-only stale mode is active."


def test_refresh_pipeline_state_plays_local_sound_when_pipeline_becomes_stale(monkeypatch):
    sound_calls = []
    update_system_state(
        {
            "status": "READY",
            "message": "Data pipeline is fresh.",
            "bootstrap_complete": True,
            "pipeline_state": "FRESH",
            "stale_mode": False,
            "data_version": 0,
            "freshness": {
                "history_fresh_ratio": 1.0,
                "intraday_live_ratio": 1.0,
                "history_ok": True,
                "intraday_ok": True,
                "market_open": True,
                "overall_ok": True,
                "checked_at": "2026-06-07T13:55:00",
                "session_mode": "LIVE",
            },
        }
    )
    monkeypatch.setattr(
        "core.pipeline.read_worker_state",
        lambda: {
            "enabled": True,
            "running": True,
            "syncing": False,
            "pipeline_state": "STALE",
            "retry_reason": "freshness_below_threshold",
            "next_retry_seconds": 60,
            "freshness": {
                "history_fresh_ratio": 1.0,
                "intraday_live_ratio": 0.0,
                "history_ok": True,
                "intraday_ok": False,
                "market_open": True,
                "overall_ok": False,
                "checked_at": "2026-06-07T13:59:00",
                "session_mode": "LIVE",
            },
        },
    )
    monkeypatch.setattr(
        pipeline,
        "maybe_play_pipeline_stale_sound",
        lambda pipeline_state: sound_calls.append(pipeline_state),
        raising=False,
    )

    snapshot = pipeline.refresh_pipeline_state(force=True)

    assert snapshot["pipeline_state"] == "STALE"
    assert sound_calls == ["STALE"]


def test_daily_signal_scan_gate_can_run_history_readiness_when_pipeline_is_degraded(monkeypatch):
    monkeypatch.setattr("core.pipeline.settings.MAINTENANCE_MODE", False, raising=False)
    monkeypatch.setattr(
        "core.pipeline.refresh_pipeline_state",
        lambda force=False: {
            "pipeline_state": "DEGRADED",
            "freshness": {
                "history_ok": False,
                "history_fresh_ratio": 0.0,
                "intraday_ok": False,
                "intraday_live_ratio": 0.0,
                "market_open": False,
            },
        },
    )

    assert pipeline.pipeline_allows_active_ops("scheduled_daily_signal_scan") is True


def test_daily_signal_pipeline_gate_can_reach_its_own_freshness_guard_when_degraded(monkeypatch):
    monkeypatch.setattr("core.pipeline.settings.MAINTENANCE_MODE", False, raising=False)
    monkeypatch.setattr(
        "core.pipeline.refresh_pipeline_state",
        lambda force=False: {
            "pipeline_state": "DEGRADED",
            "freshness": {
                "history_ok": False,
                "history_fresh_ratio": 0.0,
                "intraday_ok": False,
                "intraday_live_ratio": 0.0,
                "market_open": False,
            },
        },
    )

    assert pipeline.pipeline_allows_active_ops("scheduled_daily_signal_pipeline") is True


def test_refresh_pipeline_state_promotes_non_recovering_degraded_worker_when_inline_freshness_is_fresh(monkeypatch):
    writes = []
    update_system_state(
        {
            "status": "READY",
            "message": "Read-only stale mode is active.",
            "bootstrap_complete": True,
            "pipeline_state": "DEGRADED",
            "stale_mode": True,
            "data_version": 0,
            "freshness": {
                "history_fresh_ratio": 0.0,
                "intraday_live_ratio": 0.0,
                "history_ok": False,
                "intraday_ok": True,
                "market_open": False,
                "overall_ok": False,
                "checked_at": "2026-06-01T14:34:35",
                "session_mode": "LIVE",
            },
        }
    )
    monkeypatch.setattr("core.pipeline.settings.is_market_open", lambda: True)
    monkeypatch.setattr(
        "core.pipeline.read_worker_state",
        lambda: {
            "enabled": True,
            "running": True,
            "syncing": False,
            "pipeline_state": "DEGRADED",
            "freshness": {
                "history_fresh_ratio": 0.0,
                "intraday_live_ratio": 0.0,
                "history_ok": False,
                "intraday_ok": True,
                "market_open": False,
                "overall_ok": False,
                "checked_at": "2026-06-01T14:34:35",
                "session_mode": "LIVE",
            },
            "retry_reason": None,
            "fail_count": 0,
            "next_retry_seconds": 0,
            "last_error": None,
        },
    )
    monkeypatch.setattr(
        "core.pipeline._write_worker_state",
        lambda payload, path=None: writes.append(dict(payload)),
        raising=False,
    )
    monkeypatch.setattr(
        "core.pipeline._evaluate_freshness_with_timeout",
        lambda timeout_seconds: {
            "history": {"ok": True, "kpis": {"fresh_ratio": 1.0}},
            "intraday": {"ok": True, "kpis": {"live_ratio": 0.9885}},
        },
    )

    snapshot = pipeline.refresh_pipeline_state(force=True)

    assert snapshot["pipeline_state"] == "FRESH"
    assert snapshot["stale_mode"] is False
    assert snapshot["message"] == "Data pipeline is fresh."
    assert snapshot["freshness"]["history_fresh_ratio"] == 1.0
    assert snapshot["freshness"]["intraday_live_ratio"] == 0.9885
    assert snapshot["sync_worker"]["pipeline_state"] == "FRESH"
    assert writes[-1]["pipeline_state"] == "FRESH"
    assert writes[-1]["last_success_at"] is not None
    assert writes[-1]["last_failure_at"] is None


def test_refresh_pipeline_state_preserves_known_fresh_state_when_worker_reconciliation_times_out(monkeypatch):
    update_system_state(
        {
            "status": "READY",
            "message": "Data pipeline is fresh.",
            "bootstrap_complete": True,
            "pipeline_state": "FRESH",
            "stale_mode": False,
            "data_version": 0,
            "freshness": {
                "history_fresh_ratio": 1.0,
                "intraday_live_ratio": 0.9885,
                "history_ok": True,
                "intraday_ok": True,
                "market_open": True,
                "overall_ok": True,
                "checked_at": "2026-06-01T14:50:00",
                "session_mode": "LIVE",
            },
        }
    )
    monkeypatch.setattr("core.pipeline.settings.is_market_open", lambda: True)
    monkeypatch.setattr(
        "core.pipeline.read_worker_state",
        lambda: {
            "enabled": True,
            "running": True,
            "syncing": False,
            "pipeline_state": "DEGRADED",
            "freshness": {
                "history_fresh_ratio": 0.0,
                "intraday_live_ratio": 0.0,
                "history_ok": False,
                "intraday_ok": True,
                "market_open": False,
                "overall_ok": False,
                "checked_at": "2026-06-01T14:34:35",
                "session_mode": "LIVE",
            },
            "retry_reason": None,
            "fail_count": 0,
            "next_retry_seconds": 0,
            "last_error": None,
        },
    )
    monkeypatch.setattr("core.pipeline._evaluate_freshness_with_timeout", lambda timeout_seconds: None)

    snapshot = pipeline.refresh_pipeline_state(force=True)

    assert snapshot["pipeline_state"] == "FRESH"
    assert snapshot["stale_mode"] is False
    assert snapshot["message"] == "Data pipeline is fresh."
    assert snapshot["freshness"]["overall_ok"] is True


def test_refresh_pipeline_state_rewrites_stale_message_when_worker_is_fresh(monkeypatch):
    update_system_state(
        {
            "status": "READY",
            "message": "Read-only stale mode is active.",
            "bootstrap_complete": True,
            "pipeline_state": "STALE",
            "stale_mode": True,
            "data_version": 0,
            "freshness": {
                "history_fresh_ratio": 0.8,
                "intraday_live_ratio": 0.4,
                "history_ok": True,
                "intraday_ok": False,
                "market_open": True,
                "overall_ok": False,
                "checked_at": "2026-03-16T12:00:00",
                "session_mode": "LIVE",
            },
        }
    )
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr(
        "core.pipeline.read_worker_state",
        lambda: {
            "enabled": True,
            "running": True,
            "syncing": False,
            "pipeline_state": "FRESH",
        },
    )

    snapshot = pipeline.refresh_pipeline_state(force=True)

    assert snapshot["pipeline_state"] == "FRESH"
    assert snapshot["stale_mode"] is False
    assert snapshot["message"] == "Data pipeline is fresh."


def test_refresh_pipeline_state_marks_retrying_worker_as_recovering(monkeypatch):
    update_system_state(
        {
            "status": "READY",
            "message": "Read-only stale mode is active.",
            "bootstrap_complete": True,
            "pipeline_state": "DEGRADED",
            "stale_mode": True,
            "data_version": 0,
            "freshness": {
                "history_fresh_ratio": 0.2,
                "intraday_live_ratio": 0.1,
                "history_ok": False,
                "intraday_ok": False,
                "market_open": True,
                "overall_ok": False,
                "checked_at": "2026-03-16T12:00:00",
                "session_mode": "LIVE",
            },
        }
    )
    monkeypatch.setattr(
        "core.pipeline.read_worker_state",
        lambda: {
            "enabled": True,
            "running": True,
            "syncing": False,
            "pipeline_state": "DEGRADED",
            "retry_reason": "sync_failed",
            "fail_count": 2,
            "next_retry_seconds": 30,
            "backoff_seconds": 60,
            "last_error": "sync_all completed but freshness remains below thresholds",
        },
    )

    snapshot = pipeline.refresh_pipeline_state(force=True)

    assert snapshot["pipeline_state"] == "DEGRADED"
    assert snapshot["sync_worker"]["recovering"] is True
    assert snapshot["sync_worker"]["retry_reason"] == "sync_failed"
    assert snapshot["sync_worker"]["syncing"] is False
    assert snapshot["sync_worker"]["next_retry_seconds"] == 30


def test_refresh_pipeline_state_does_not_mark_healthy_worker_as_recovering(monkeypatch):
    update_system_state(
        {
            "status": "READY",
            "message": "Data pipeline is fresh.",
            "bootstrap_complete": True,
            "pipeline_state": "FRESH",
            "stale_mode": False,
            "data_version": 0,
            "freshness": {
                "history_fresh_ratio": 1.0,
                "intraday_live_ratio": 1.0,
                "history_ok": True,
                "intraday_ok": True,
                "market_open": True,
                "overall_ok": True,
                "checked_at": "2026-03-16T12:00:00",
                "session_mode": "LIVE",
            },
        }
    )
    monkeypatch.setattr(
        "core.pipeline.read_worker_state",
        lambda: {
            "enabled": True,
            "running": True,
            "syncing": False,
            "pipeline_state": "FRESH",
            "fail_count": 0,
            "next_retry_seconds": 300,
            "backoff_seconds": 0,
            "last_error": None,
        },
    )

    snapshot = pipeline.refresh_pipeline_state(force=True)

    assert snapshot["pipeline_state"] == "FRESH"
    assert snapshot["sync_worker"]["recovering"] is False
    assert snapshot["sync_worker"]["next_retry_seconds"] == 300


def test_refresh_pipeline_state_does_not_regress_ready_system_back_to_starting(monkeypatch):
    update_system_state(
        {
            "status": "READY",
            "message": "Horus Terminal Online",
            "bootstrap_complete": True,
            "provisioning_status": "COMPLETED",
            "provisioning_target_trading_days": 3,
            "provisioning_completed_trading_days": 3,
            "pipeline_state": "STARTING",
            "stale_mode": False,
            "data_version": 0,
            "freshness": {},
        }
    )
    monkeypatch.setattr("core.pipeline.read_worker_state", lambda: {})

    snapshot = pipeline.refresh_pipeline_state(force=True)

    assert snapshot["status"] == "READY"
    assert snapshot["pipeline_state"] == "DEGRADED"
    assert snapshot["stale_mode"] is True
