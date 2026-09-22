import datetime
import pytest
from core import TimeUtils
from core.settings import settings
import core.scheduling as scheduling
from database import SignalRun


@pytest.fixture(autouse=True)
def _reset_scheduler_completion_sets():
    with scheduling._MORNING_DAILY_SIGNAL_LOCK:
        scheduling._MORNING_DAILY_SIGNAL_COMPLETED_DATES.clear()
    with scheduling._PRE_CLOSE_LOCK:
        scheduling._PRE_CLOSE_COMPLETED_DATES.clear()
    with scheduling._DAILY_SIGNAL_LOCK:
        scheduling._DAILY_SIGNAL_COMPLETED_DATES.clear()
    yield
    with scheduling._MORNING_DAILY_SIGNAL_LOCK:
        scheduling._MORNING_DAILY_SIGNAL_COMPLETED_DATES.clear()
    with scheduling._PRE_CLOSE_LOCK:
        scheduling._PRE_CLOSE_COMPLETED_DATES.clear()
    with scheduling._DAILY_SIGNAL_LOCK:
        scheduling._DAILY_SIGNAL_COMPLETED_DATES.clear()


def test_morning_daily_signal_scan_skips_after_market_open(monkeypatch):
    # Set time to 10:30 AM (after market open)
    now_dt = TimeUtils.now().replace(hour=10, minute=30, second=0)
    monkeypatch.setattr(TimeUtils, "now", lambda: now_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: now_dt.date())

    res = scheduling.scheduled_morning_daily_signal_scan()
    assert res is False


def test_morning_daily_signal_scan_skips_on_weekend(monkeypatch):
    # Find a Friday date (EGX weekend)
    today_dt = datetime.datetime(2026, 7, 24, 9, 30, 0)  # 2026-07-24 is Friday
    assert today_dt.weekday() == 4  # Friday
    monkeypatch.setattr(TimeUtils, "now", lambda: today_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: today_dt.date())

    res = scheduling.scheduled_morning_daily_signal_scan()
    assert res is False


def test_monday_morning_catching_up_sunday(monkeypatch):
    # Monday 09:30 AM (trading morning)
    monday_dt = datetime.datetime(2026, 7, 27, 9, 30, 0)  # Monday
    sunday_date = datetime.date(2026, 7, 26)  # Previous trading session

    monkeypatch.setattr(TimeUtils, "now", lambda: monday_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: monday_dt.date())

    monkeypatch.setattr("core.scheduling._background_ops_paused_for_time_travel", lambda: False)
    monkeypatch.setattr(scheduling._pipeline, "pipeline_allows_active_ops", lambda action: True)
    monkeypatch.setattr(SignalRun, "get_or_none", lambda *args, **kwargs: None)

    calls = []
    def _mock_scan(*args, **kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr(scheduling, "scheduled_scan_logic", _mock_scan)

    res = scheduling.scheduled_morning_daily_signal_scan()
    assert res is True
    assert len(calls) == 1
    assert calls[0].get("market_date") == sunday_date
    assert calls[0].get("preview_only") is False


def test_sunday_morning_catching_up_thursday(monkeypatch):
    # Sunday 09:30 AM (trading morning after Friday-Saturday EGX weekend)
    sunday_dt = datetime.datetime(2026, 7, 26, 9, 30, 0)  # Sunday
    thursday_date = datetime.date(2026, 7, 23)  # Previous completed trading session

    monkeypatch.setattr(TimeUtils, "now", lambda: sunday_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: sunday_dt.date())

    monkeypatch.setattr("core.scheduling._background_ops_paused_for_time_travel", lambda: False)
    monkeypatch.setattr(scheduling._pipeline, "pipeline_allows_active_ops", lambda action: True)
    monkeypatch.setattr(SignalRun, "get_or_none", lambda *args, **kwargs: None)

    calls = []
    def _mock_scan(*args, **kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr(scheduling, "scheduled_scan_logic", _mock_scan)

    res = scheduling.scheduled_morning_daily_signal_scan()
    assert res is True
    assert len(calls) == 1
    assert calls[0].get("market_date") == thursday_date


def test_db_holiday_gaps(monkeypatch):
    # Monday 09:30 AM. Sunday July 26 is a DB holiday.
    monday_dt = datetime.datetime(2026, 7, 27, 9, 30, 0)
    sunday_date = datetime.date(2026, 7, 26)
    thursday_date = datetime.date(2026, 7, 23)

    monkeypatch.setattr(TimeUtils, "now", lambda: monday_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: monday_dt.date())

    def _mock_is_holiday(d):
        return d == sunday_date

    monkeypatch.setattr(settings, "_is_db_holiday", _mock_is_holiday)
    monkeypatch.setattr("core.scheduling._background_ops_paused_for_time_travel", lambda: False)
    monkeypatch.setattr(scheduling._pipeline, "pipeline_allows_active_ops", lambda action: True)
    monkeypatch.setattr(SignalRun, "get_or_none", lambda *args, **kwargs: None)

    calls = []
    def _mock_scan(*args, **kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr(scheduling, "scheduled_scan_logic", _mock_scan)

    res = scheduling.scheduled_morning_daily_signal_scan()
    assert res is True
    assert len(calls) == 1
    assert calls[0].get("market_date") == thursday_date


def test_restart_before_market_open_durable_idempotency(monkeypatch):
    monday_dt = datetime.datetime(2026, 7, 27, 9, 30, 0)
    sunday_date = datetime.date(2026, 7, 26)

    monkeypatch.setattr(TimeUtils, "now", lambda: monday_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: monday_dt.date())

    # Simulate existing DB SignalRun with status COMPLETED
    class DummyRun:
        status = "COMPLETED"

    def _mock_get_or_none(clause):
        return DummyRun()

    monkeypatch.setattr(SignalRun, "get_or_none", _mock_get_or_none)
    monkeypatch.setattr("core.scheduling._background_ops_paused_for_time_travel", lambda: False)
    monkeypatch.setattr(scheduling._pipeline, "pipeline_allows_active_ops", lambda action: True)

    calls = []
    monkeypatch.setattr(scheduling, "scheduled_scan_logic", lambda *a, **kw: calls.append(kw) or True)

    res = scheduling.scheduled_morning_daily_signal_scan()
    assert res is False
    assert len(calls) == 0


def test_repeated_watchdog_invocation(monkeypatch):
    monday_dt = datetime.datetime(2026, 7, 27, 9, 30, 0)
    sunday_date = datetime.date(2026, 7, 26)

    monkeypatch.setattr(TimeUtils, "now", lambda: monday_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: monday_dt.date())

    monkeypatch.setattr("core.scheduling._background_ops_paused_for_time_travel", lambda: False)
    monkeypatch.setattr(scheduling._pipeline, "pipeline_allows_active_ops", lambda action: True)
    monkeypatch.setattr(SignalRun, "get_or_none", lambda *args, **kwargs: None)

    calls = []
    monkeypatch.setattr(scheduling, "scheduled_scan_logic", lambda *a, **kw: calls.append(kw) or True)

    res1 = scheduling.scheduled_morning_daily_signal_scan()
    assert res1 is True
    assert len(calls) == 1

    res2 = scheduling.scheduled_morning_daily_signal_scan()
    assert res2 is False
    assert len(calls) == 1


def test_catchup_before_market_close_returns_skipped(monkeypatch):
    # 09:33 AM on Monday (before market close)
    today_dt = datetime.datetime(2026, 7, 27, 9, 33, 0)
    monkeypatch.setattr(TimeUtils, "now", lambda: today_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: today_dt.date())

    result = scheduling.catchup_missed_post_market_jobs()
    assert result.get("status") == "skipped"
    assert result.get("reason") == "before_market_close"
    assert result.get("executed_jobs") == []


def test_catchup_after_market_close(monkeypatch):
    # 15:30 PM on Monday (after market close)
    monday_dt = datetime.datetime(2026, 7, 27, 15, 30, 0)
    run_date_str = monday_dt.date().isoformat()

    monkeypatch.setattr(TimeUtils, "now", lambda: monday_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: monday_dt.date())

    monkeypatch.setattr(SignalRun, "get_or_none", lambda *args, **kwargs: None)

    scans_run = []
    def _mock_scan(is_intraday=False, scan_label="", market_date=None, preview_only=False):
        scans_run.append((scan_label, market_date, preview_only))
        return True

    monkeypatch.setattr(scheduling, "scheduled_scan_logic", _mock_scan)
    monkeypatch.setattr(scheduling, "_ensure_scheduler_data_ready", lambda *args, **kwargs: True, raising=False)

    result = scheduling.catchup_missed_post_market_jobs()
    assert result.get("status") == "completed"
    assert result.get("run_date") == run_date_str
    assert "pre_close_scan" in result.get("executed_jobs", [])
    assert "daily_signal_scan" in result.get("executed_jobs", [])


def test_replay_simulation_date_behavior(monkeypatch):
    # Market open time is 10:00 AM. Suppose current simulation time is 10:30 AM.
    now_dt = datetime.datetime(2026, 7, 27, 10, 30, 0)
    monkeypatch.setattr(TimeUtils, "now", lambda: now_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: now_dt.date())
    monkeypatch.setattr(TimeUtils, "is_simulating", lambda: True)

    monkeypatch.setattr("core.scheduling._background_ops_paused_for_time_travel", lambda: False)
    monkeypatch.setattr(scheduling._pipeline, "pipeline_allows_active_ops", lambda action: True)
    monkeypatch.setattr(SignalRun, "get_or_none", lambda *args, **kwargs: None)

    calls = []
    monkeypatch.setattr(scheduling, "scheduled_scan_logic", lambda *a, **kw: calls.append(kw) or True)

    # In simulation mode, the market open check is bypassed
    res = scheduling.scheduled_morning_daily_signal_scan()
    assert res is True
    assert len(calls) == 1
