import datetime
import pytest
from core.settings import settings
from core import TimeUtils
import core.scheduling as scheduling
from core.scheduling.state import (
    _mark_daily_signal_completed,
    _daily_signal_was_completed,
    _daily_signal_is_pending,
    _DAILY_SIGNAL_COMPLETED_DATES,
    _DAILY_SIGNAL_PENDING_DATES,
    _PRE_CLOSE_COMPLETED_DATES,
)
from core.scheduling.catchup import (
    catchup_missed_post_market_jobs,
    maybe_run_pending_daily_signal_after_data_update,
)
from core.market.LiveFeedManager import LiveFeedManager


@pytest.fixture(autouse=True)
def clean_scheduling_state():
    _DAILY_SIGNAL_COMPLETED_DATES.clear()
    _DAILY_SIGNAL_PENDING_DATES.clear()
    _PRE_CLOSE_COMPLETED_DATES.clear()
    TimeUtils.clear_simulation()
    yield
    _DAILY_SIGNAL_COMPLETED_DATES.clear()
    _DAILY_SIGNAL_PENDING_DATES.clear()
    _PRE_CLOSE_COMPLETED_DATES.clear()
    TimeUtils.clear_simulation()


def test_catchup_at_market_close_defers_future_daily_scan(monkeypatch):
    """At 14:30:00 market close, daily signal (15:00) and AI report (15:00) are not missed and must be deferred."""
    # Set time to 14:30:00 (exact market close)
    sim_dt = datetime.datetime(2026, 9, 6, 14, 30, 0)
    monkeypatch.setattr(TimeUtils, "now", lambda: sim_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: sim_dt.date())
    monkeypatch.setattr(TimeUtils, "is_simulating", lambda: False)
    monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")
    monkeypatch.setattr(settings, "is_market_open", lambda: False)

    scan_called = []
    monkeypatch.setattr(
        "core.scheduling.catchup.scheduled_scan_logic",
        lambda *args, **kwargs: scan_called.append(kwargs.get("scan_label")),
    )

    summary = catchup_missed_post_market_jobs()

    # Daily signal should NOT have executed at 14:30:00
    assert "daily_signal_scan" not in summary.get("executed_jobs", [])
    # Daily signal should be marked pending for today
    assert _daily_signal_is_pending("2026-09-06")
    assert not _daily_signal_was_completed("2026-09-06")


def test_catchup_at_1505_defers_if_data_not_ready(monkeypatch):
    """At 15:05:00, if EOD data is not ready, daily signal scan must defer and mark pending."""
    sim_dt = datetime.datetime(2026, 9, 6, 15, 5, 0)
    monkeypatch.setattr(TimeUtils, "now", lambda: sim_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: sim_dt.date())
    monkeypatch.setattr(TimeUtils, "is_simulating", lambda: False)
    monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")
    monkeypatch.setattr(settings, "is_market_open", lambda: False)

    # Data is not ready
    monkeypatch.setattr("core.scheduling.catchup._ensure_scheduler_data_ready", lambda label: False)

    scan_called = []
    monkeypatch.setattr(
        "core.scheduling.catchup.scheduled_scan_logic",
        lambda *args, **kwargs: scan_called.append(kwargs.get("scan_label")),
    )

    summary = catchup_missed_post_market_jobs()

    assert "daily_signal_scan" not in summary.get("executed_jobs", [])
    assert _daily_signal_is_pending("2026-09-06")
    assert not _daily_signal_was_completed("2026-09-06")
    assert len(scan_called) == 0 or "DAILY SIGNAL" not in scan_called


def test_catchup_at_1505_executes_when_data_is_ready(monkeypatch):
    """At 15:05:00, if EOD data is ready, daily signal scan runs and marks completed."""
    sim_dt = datetime.datetime(2026, 9, 6, 15, 5, 0)
    monkeypatch.setattr(TimeUtils, "now", lambda: sim_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: sim_dt.date())
    monkeypatch.setattr(TimeUtils, "is_simulating", lambda: False)
    monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")
    monkeypatch.setattr(settings, "is_market_open", lambda: False)

    monkeypatch.setattr("core.scheduling.catchup._ensure_scheduler_data_ready", lambda label: True)
    monkeypatch.setattr(
        "core.scheduling.catchup.scheduled_scan_logic",
        lambda *args, **kwargs: True,
    )

    summary = catchup_missed_post_market_jobs()

    assert "daily_signal_scan" in summary.get("executed_jobs", [])
    assert _daily_signal_was_completed("2026-09-06")


def test_data_update_hook_runs_pending_daily_signal(monkeypatch):
    """When new data updates post-market, maybe_run_pending_daily_signal_after_data_update triggers scan."""
    sim_dt = datetime.datetime(2026, 9, 6, 14, 33, 51)
    monkeypatch.setattr(TimeUtils, "now", lambda: sim_dt)
    monkeypatch.setattr(TimeUtils, "today", lambda: sim_dt.date())
    monkeypatch.setattr(TimeUtils, "is_simulating", lambda: False)
    monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")
    monkeypatch.setattr(settings, "is_market_open", lambda: False)

    monkeypatch.setattr("core.scheduling.catchup._ensure_scheduler_data_ready", lambda label: True)
    monkeypatch.setattr(
        "core.scheduling.catchup.scheduled_scan_logic",
        lambda *args, **kwargs: True,
    )
    ai_report_dispatched = []
    monkeypatch.setattr(
        "core.scheduling.reports.maybe_dispatch_pending_ai_daily_report_after_data_update",
        lambda: ai_report_dispatched.append(True),
    )

    result = maybe_run_pending_daily_signal_after_data_update()

    assert result["status"] == "completed"
    assert _daily_signal_was_completed("2026-09-06")
    assert len(ai_report_dispatched) == 1


def test_livefeed_fallback_resistance_signature():
    """LiveFeedManager._compute_fallback_resistance must execute without TypeError."""
    res = LiveFeedManager._compute_fallback_resistance()
    assert isinstance(res, dict)
