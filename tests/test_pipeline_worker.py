from core.settings import settings
from datetime import datetime, timedelta
import threading
import time
from unittest.mock import MagicMock


from data_engine import pipeline_worker


class _OneShotStopEvent:
    def __init__(self):
        self._is_set = False

    def is_set(self):
        return self._is_set

    def set(self):
        self._is_set = True

    def clear(self):
        self._is_set = False

    def wait(self, timeout=None):
        self._is_set = True
        return False


def _freshness(*, history_ok: bool, intraday_ok: bool, history_ratio: float, intraday_ratio: float) -> dict:
    return {
        "history": {"ok": history_ok, "kpis": {"fresh_ratio": history_ratio}},
        "intraday": {"ok": intraday_ok, "kpis": {"live_ratio": intraday_ratio}},
    }


def test_sync_worker_persists_retry_reason_when_sync_completes_but_data_stays_stale(monkeypatch):
    writes = []
    now = datetime(2026, 3, 16, 12, 0, 0)

    def _now():
        nonlocal now
        now = now + timedelta(seconds=1)
        return now

    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.now", _now)
    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr("data_engine.pipeline_worker.settings.is_market_open", lambda: True)
    monkeypatch.setattr(settings, "SESSION_MODE", "LIVE", raising=False)
    monkeypatch.setattr("data_engine.pipeline_worker.random.uniform", lambda a, b: 1.0)
    monkeypatch.setattr("data_engine.pipeline_worker._write_worker_state", lambda payload, path=None: writes.append(dict(payload)))
    monkeypatch.setattr(
        "data_engine.pipeline_worker.evaluate_freshness",
        MagicMock(
            side_effect=[
                _freshness(history_ok=True, intraday_ok=False, history_ratio=1.0, intraday_ratio=0.2),
                _freshness(history_ok=True, intraday_ok=False, history_ratio=1.0, intraday_ratio=0.2),
            ]
        ),
    )
    monkeypatch.setattr("data_engine.pipeline_worker._sync_all_with_timeout", lambda timeout_seconds: None)

    worker = pipeline_worker.AdaptiveSyncWorker(logger=MagicMock())
    worker._stop_event = _OneShotStopEvent()

    worker._run_loop()

    assert len(writes) == 2
    assert writes[0]["pipeline_state"] == "SYNCING"
    assert writes[-1]["pipeline_state"] == "STALE"
    assert writes[-1]["retry_reason"] == "freshness_below_threshold"
    assert writes[-1]["recovering"] is True
    assert writes[-1]["next_retry_seconds"] == 30
    assert "freshness remains below thresholds" in writes[-1]["last_error"]


def test_sync_worker_persists_retry_reason_when_sync_fails(monkeypatch):
    writes = []
    now = datetime(2026, 3, 16, 12, 0, 0)

    def _now():
        nonlocal now
        now = now + timedelta(seconds=1)
        return now

    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.now", _now)
    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr("data_engine.pipeline_worker.settings.is_market_open", lambda: True)
    monkeypatch.setattr(settings, "SESSION_MODE", "LIVE", raising=False)
    monkeypatch.setattr("data_engine.pipeline_worker.random.uniform", lambda a, b: 1.0)
    monkeypatch.setattr("data_engine.pipeline_worker._write_worker_state", lambda payload, path=None: writes.append(dict(payload)))
    monkeypatch.setattr(
        "data_engine.pipeline_worker.evaluate_freshness",
        MagicMock(
            return_value=_freshness(history_ok=True, intraday_ok=False, history_ratio=1.0, intraday_ratio=0.2)
        ),
    )
    monkeypatch.setattr(
        "data_engine.pipeline_worker._sync_all_with_timeout",
        MagicMock(side_effect=TimeoutError("sync_all exceeded timeout (900s)")),
    )

    worker = pipeline_worker.AdaptiveSyncWorker(logger=MagicMock())
    worker._stop_event = _OneShotStopEvent()

    worker._run_loop()

    assert len(writes) == 2
    assert writes[0]["pipeline_state"] == "SYNCING"
    assert writes[-1]["pipeline_state"] == "DEGRADED"
    assert writes[-1]["retry_reason"] == "sync_failed"
    assert writes[-1]["recovering"] is True
    assert writes[-1]["next_retry_seconds"] == 30
    assert writes[-1]["last_error"] == "sync_all exceeded timeout (900s)"


def test_sync_worker_runs_one_closed_session_verification_pass_then_idles_as_fresh(monkeypatch):
    writes = []
    now = datetime(2026, 3, 28, 12, 0, 0)

    def _now():
        nonlocal now
        now = now + timedelta(seconds=1)
        return now

    sync_calls = []

    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.now", _now)
    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr("data_engine.pipeline_worker.settings.is_market_open", lambda: False)
    monkeypatch.setattr(settings, "SESSION_MODE", "ANALYSIS", raising=False)
    monkeypatch.setattr("data_engine.pipeline_worker._write_worker_state", lambda payload, path=None: writes.append(dict(payload)))
    monkeypatch.setattr(
        "data_engine.pipeline_worker.evaluate_freshness",
        MagicMock(return_value=_freshness(history_ok=True, intraday_ok=False, history_ratio=1.0, intraday_ratio=0.0)),
    )
    monkeypatch.setattr("data_engine.pipeline_worker._sync_all_with_timeout", lambda timeout_seconds: sync_calls.append(timeout_seconds))

    worker = pipeline_worker.AdaptiveSyncWorker(logger=MagicMock())
    worker._stop_event = _OneShotStopEvent()

    worker._run_loop()

    assert len(writes) == 2
    assert writes[0]["pipeline_state"] == "SYNCING"
    assert writes[-1]["pipeline_state"] == "FRESH"
    assert writes[-1]["retry_reason"] is None
    assert writes[-1]["recovering"] is False
    assert len(sync_calls) == 1


def test_sync_worker_pauses_while_time_travel_is_active(monkeypatch):
    evaluate_mock = MagicMock(side_effect=AssertionError("freshness should not run during time travel"))
    sync_mock = MagicMock(side_effect=AssertionError("sync_all should not run during time travel"))

    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.is_simulating", lambda: True)
    monkeypatch.setattr("data_engine.pipeline_worker.evaluate_freshness", evaluate_mock)
    monkeypatch.setattr("data_engine.pipeline_worker._sync_all_with_timeout", sync_mock)

    worker = pipeline_worker.AdaptiveSyncWorker(logger=MagicMock())
    worker._stop_event = _OneShotStopEvent()

    worker._run_loop()

    evaluate_mock.assert_not_called()
    sync_mock.assert_not_called()


def test_sync_worker_uses_dedicated_timeout_instead_of_short_startup_timeout(monkeypatch):
    monkeypatch.setenv("STARTUP_SYNC_TIMEOUT_SEC", "120")
    monkeypatch.delenv("PIPELINE_WORKER_SYNC_TIMEOUT_SEC", raising=False)

    worker = pipeline_worker.AdaptiveSyncWorker(logger=MagicMock())

    assert worker.sync_timeout_sec == 900


def test_sync_all_with_timeout_reuses_inflight_run_instead_of_starting_duplicate(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    calls = []

    def _fake_sync_all():
        calls.append("run")
        started.set()
        release.wait(2)

    monkeypatch.setattr("data_engine.pipeline_worker.sync_all", _fake_sync_all)
    monkeypatch.setattr("data_engine.pipeline_worker._SYNC_ALL_ACTIVE", None, raising=False)

    try:
        pipeline_worker._sync_all_with_timeout(1)
    except TimeoutError:
        pass

    assert started.wait(1) is True
    assert calls == ["run"]

    try:
        pipeline_worker._sync_all_with_timeout(1)
    except TimeoutError:
        pass

    assert calls == ["run"]
    release.set()
    time.sleep(0.05)


def test_sync_worker_closed_session_verification_idles_after_single_completed_pass_even_if_slightly_below_threshold(monkeypatch):
    writes = []
    now = datetime(2026, 4, 2, 21, 25, 0)

    def _now():
        nonlocal now
        now = now + timedelta(seconds=1)
        return now

    sync_calls = []

    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.now", _now)
    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr("data_engine.pipeline_worker.settings.is_market_open", lambda: False)
    monkeypatch.setattr(settings, "SESSION_MODE", "LIVE", raising=False)
    monkeypatch.setattr("data_engine.pipeline_worker._write_worker_state", lambda payload, path=None: writes.append(dict(payload)))
    monkeypatch.setattr(
        "data_engine.pipeline_worker.evaluate_freshness",
        MagicMock(
            side_effect=[
                _freshness(history_ok=True, intraday_ok=False, history_ratio=1.0, intraday_ratio=0.0),
                _freshness(history_ok=False, intraday_ok=False, history_ratio=0.8963, intraday_ratio=0.0),
            ]
        ),
    )
    monkeypatch.setattr("data_engine.pipeline_worker._sync_all_with_timeout", lambda timeout_seconds: sync_calls.append(timeout_seconds))

    worker = pipeline_worker.AdaptiveSyncWorker(logger=MagicMock())
    worker._stop_event = _OneShotStopEvent()

    worker._run_loop()

    assert len(sync_calls) == 1
    assert len(writes) == 2
    assert writes[0]["pipeline_state"] == "SYNCING"
    assert writes[-1]["pipeline_state"] == "DEGRADED"
    assert writes[-1]["retry_reason"] is None
    assert writes[-1]["recovering"] is False


def test_sync_worker_closed_session_degraded_state_runs_single_sync_then_idles(monkeypatch):
    writes = []
    now = datetime(2026, 4, 7, 21, 3, 0)

    def _now():
        nonlocal now
        now = now + timedelta(seconds=1)
        return now

    sync_calls = []

    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.now", _now)
    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr("data_engine.pipeline_worker.settings.is_market_open", lambda: False)
    monkeypatch.setattr(settings, "SESSION_MODE", "LIVE", raising=False)
    monkeypatch.setattr("data_engine.pipeline_worker.random.uniform", lambda a, b: 1.0)
    monkeypatch.setattr("data_engine.pipeline_worker._write_worker_state", lambda payload, path=None: writes.append(dict(payload)))
    monkeypatch.setattr(
        "data_engine.pipeline_worker.evaluate_freshness",
        MagicMock(
            side_effect=[
                _freshness(history_ok=False, intraday_ok=True, history_ratio=0.0, intraday_ratio=0.8919),
                _freshness(history_ok=False, intraday_ok=True, history_ratio=0.8963, intraday_ratio=0.8919),
            ]
        ),
    )
    monkeypatch.setattr("data_engine.pipeline_worker._sync_all_with_timeout", lambda timeout_seconds: sync_calls.append(timeout_seconds))

    worker = pipeline_worker.AdaptiveSyncWorker(logger=MagicMock())
    worker._stop_event = _OneShotStopEvent()

    worker._run_loop()

    assert len(sync_calls) == 1
    assert len(writes) == 2
    assert writes[0]["pipeline_state"] == "SYNCING"
    assert writes[-1]["pipeline_state"] == "DEGRADED"
    assert writes[-1]["retry_reason"] is None
    assert writes[-1]["recovering"] is False


def test_sync_worker_closed_session_degraded_state_is_not_recorded_as_success(monkeypatch):
    writes = []
    now = datetime(2026, 4, 7, 21, 3, 0)

    def _now():
        nonlocal now
        now = now + timedelta(seconds=1)
        return now

    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.now", _now)
    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr("data_engine.pipeline_worker.settings.is_market_open", lambda: False)
    monkeypatch.setattr(settings, "SESSION_MODE", "LIVE", raising=False)
    monkeypatch.setattr("data_engine.pipeline_worker.random.uniform", lambda a, b: 1.0)
    monkeypatch.setattr("data_engine.pipeline_worker._write_worker_state", lambda payload, path=None: writes.append(dict(payload)))
    monkeypatch.setattr(
        "data_engine.pipeline_worker.evaluate_freshness",
        MagicMock(
            side_effect=[
                _freshness(history_ok=False, intraday_ok=True, history_ratio=0.0, intraday_ratio=0.8919),
                _freshness(history_ok=False, intraday_ok=True, history_ratio=0.8963, intraday_ratio=0.8919),
            ]
        ),
    )
    monkeypatch.setattr("data_engine.pipeline_worker._sync_all_with_timeout", lambda timeout_seconds: None)

    worker = pipeline_worker.AdaptiveSyncWorker(logger=MagicMock())
    worker._stop_event = _OneShotStopEvent()

    worker._run_loop()

    assert writes[-1]["pipeline_state"] == "DEGRADED"
    assert writes[-1]["last_success_at"] is None
    assert writes[-1]["last_failure_at"] is not None
    assert writes[-1]["retry_reason"] is None


def test_sync_worker_promotes_back_to_live_if_market_opens_during_startup_sync(monkeypatch):
    writes = []
    now = datetime(2026, 4, 8, 14, 29, 50)
    market_state = {"open": False}
    transitions = []

    def _now():
        nonlocal now
        now = now + timedelta(seconds=1)
        return now

    def _sync(timeout_seconds):
        market_state["open"] = True

    def _transition(mode: str):
        transitions.append(mode)
        settings.SESSION_MODE = mode
        return {"status": "transitioned", "to": mode}

    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.now", _now)
    monkeypatch.setattr("data_engine.pipeline_worker.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr("data_engine.pipeline_worker.settings.is_market_open", lambda: market_state["open"])
    monkeypatch.setattr(settings, "SESSION_MODE", "ANALYSIS", raising=False)
    monkeypatch.setattr("data_engine.pipeline_worker._write_worker_state", lambda payload, path=None: writes.append(dict(payload)))
    monkeypatch.setattr(
        "data_engine.pipeline_worker.evaluate_freshness",
        MagicMock(
            side_effect=[
                _freshness(history_ok=False, intraday_ok=False, history_ratio=0.0, intraday_ratio=0.0),
                _freshness(history_ok=True, intraday_ok=True, history_ratio=1.0, intraday_ratio=1.0),
                _freshness(history_ok=True, intraday_ok=True, history_ratio=1.0, intraday_ratio=1.0),
            ]
        ),
    )
    monkeypatch.setattr("data_engine.pipeline_worker._sync_all_with_timeout", _sync)
    monkeypatch.setattr("core.session_mode.apply_mode_transition", _transition)

    worker = pipeline_worker.AdaptiveSyncWorker(logger=MagicMock())
    worker._stop_event = _OneShotStopEvent()

    worker._run_loop()

    assert transitions == ["LIVE"]
    assert settings.SESSION_MODE == "LIVE"
    assert writes[-1]["pipeline_state"] == "FRESH"
