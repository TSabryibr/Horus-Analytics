import pytest
import datetime
from unittest.mock import MagicMock
from core import TimeUtils
from core.settings import settings
import core.scheduling


def test_market_schedule_continuous_close_and_preclose_time(monkeypatch):
    monkeypatch.setattr(settings, "MARKET_END_HHMM_NORMAL", "1415")
    close_h, close_m = settings.get_market_close_hour_minute()
    assert (close_h, close_m) == (14, 15)

    schedule = core.scheduling.get_market_signal_schedule()
    assert schedule["close_hour"] == 14
    assert schedule["close_minute"] == 15
    # Preclose time should be before 14:15
    preclose_dt = schedule["pre_close_dt"]
    assert preclose_dt.hour == 14 or preclose_dt.hour == 13
    assert preclose_dt.time() < datetime.time(14, 15)


def test_history_and_intraday_ready_logic():
    # When both are OK
    freshness_ok = {
        "overall_ok": True,
        "history": {
            "ok": True,
            "last_updated": "2026-07-23",
            "calendar_expected_last_working_day": "2026-07-23",
            "kpis": {"fresh_ratio": 0.95},
        },
        "intraday": {
            "ok": True,
            "last_bar": TimeUtils.now().strftime("%Y-%m-%d %H:%M:%S"),
            "kpis": {"live_ratio": 0.90},
        },
    }
    assert core.scheduling._daily_signal_history_ready(freshness_ok) is True
    assert core.scheduling._history_and_intraday_ready(freshness_ok) is True

    # When history is stale
    freshness_stale_history = {
        "overall_ok": False,
        "history": {
            "ok": False,
            "last_updated": "2026-07-22",
            "calendar_expected_last_working_day": "2026-07-23",
            "kpis": {"fresh_ratio": 0.50},
        },
        "intraday": {
            "ok": True,
            "last_bar": TimeUtils.now().strftime("%Y-%m-%d %H:%M:%S"),
            "kpis": {"live_ratio": 0.90},
        },
    }
    assert core.scheduling._history_and_intraday_ready(freshness_stale_history) is False

    # When intraday is stale
    freshness_stale_intraday = {
        "overall_ok": False,
        "history": {
            "ok": True,
            "last_updated": "2026-07-23",
            "calendar_expected_last_working_day": "2026-07-23",
            "kpis": {"fresh_ratio": 0.95},
        },
        "intraday": {
            "ok": False,
            "last_bar": "2026-07-22 10:00:00",
            "kpis": {"live_ratio": 0.10},
        },
    }
    assert core.scheduling._history_and_intraday_ready(freshness_stale_intraday) is False


def test_subscriber_data_waiting_notice_broadcast(monkeypatch):
    run_date = "2026-07-23-test-notice"
    alerts = []
    
    with core.scheduling._DATA_WAITING_NOTICE_LOCK:
        core.scheduling._DATA_WAITING_NOTICE_SENT_DATES.discard(run_date)

    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda msg: alerts.append(msg))

    # First call should send notice
    sent = core.scheduling._maybe_broadcast_data_waiting_subscriber_notice(run_date)
    assert sent is True
    assert len(alerts) == 1
    assert "daily signal will be sent once" in alerts[0].lower() or "تحديث بيانات السوق" in alerts[0]

    # Second call on same date should not duplicate
    sent_again = core.scheduling._maybe_broadcast_data_waiting_subscriber_notice(run_date)
    assert sent_again is False
    assert len(alerts) == 1


def test_ensure_scheduler_data_ready_dispatches_notice_when_stale(monkeypatch):
    run_date = TimeUtils.today().isoformat()
    with core.scheduling._DATA_WAITING_NOTICE_LOCK:
        core.scheduling._DATA_WAITING_NOTICE_SENT_DATES.discard(run_date)

    stale_freshness = {
        "overall_ok": False,
        "history": {"ok": False, "kpis": {"fresh_ratio": 0.1}},
        "intraday": {"ok": False, "kpis": {"live_ratio": 0.1}},
    }
    monkeypatch.setattr("core.scheduling._scheduler_freshness", lambda scan_type: stale_freshness)
    monkeypatch.setattr("core.scheduling._sync_scheduler_data", lambda label: False)

    alerts = []
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda msg: alerts.append(msg))

    ready = core.scheduling._ensure_scheduler_data_ready("PRE-CLOSE")
    assert ready is False
    assert len(alerts) == 1
    assert "daily signal will be sent once" in alerts[0].lower() or "تحديث بيانات السوق" in alerts[0]


def test_daily_scanner_pre_close_ghost_candidate_gating(monkeypatch):
    from core import DailyScanner
    from core import SignalEngine
    from core.settings import settings
    import pandas as pd

    today = TimeUtils.today()
    yesterday = today - datetime.timedelta(days=1)
    monkeypatch.setattr(settings, "is_recent_trading_day", lambda d, max_trading_days=1: True)
    monkeypatch.setattr(settings, "is_market_open", lambda now=None: True)

    dates_today = pd.date_range(end=pd.Timestamp(today), periods=25, freq="D")
    dates_yesterday = pd.date_range(end=pd.Timestamp(yesterday), periods=25, freq="D")

    rows_today = [
        {"Open": 10.0, "High": 12.0, "Low": 9.5, "Close": 11.5, "Volume": 500000, "Turnover": 5750000, "Avg_Turnover": 5000000, "Move": 3.0, "Rel_Vol": 2.0}
        for _ in dates_today
    ]
    df_today = pd.DataFrame(rows_today, index=pd.MultiIndex.from_product([["TODAY_STOCK"], dates_today], names=["Ticker", "Date"]))

    rows_yesterday = [
        {"Open": 10.0, "High": 12.0, "Low": 9.5, "Close": 11.5, "Volume": 500000, "Turnover": 5750000, "Avg_Turnover": 5000000, "Move": 3.0, "Rel_Vol": 2.0}
        for _ in dates_yesterday
    ]
    df_yesterday = pd.DataFrame(rows_yesterday, index=pd.MultiIndex.from_product([["YESTERDAY_STOCK"], dates_yesterday], names=["Ticker", "Date"]))

    universe_df = pd.concat([df_today, df_yesterday])
    universe_df = SignalEngine.add_indicators_universe(universe_df, settings.LOOKBACK)

    # Run pre-close scan (is_pre_close=True, is_intraday=False)
    signals, monitored, breadth, regime = DailyScanner.get_market_signals(
        is_pre_close=True,
        is_intraday=False,
        universe_df=universe_df,
    )

    monitored_tickers = [m["Ticker"] for m in monitored]

    # TODAY_STOCK should be monitored / fresh
    assert "TODAY_STOCK" in monitored_tickers
    # YESTERDAY_STOCK must NOT be fresh / monitored under daily_preview
    assert "YESTERDAY_STOCK" not in monitored_tickers

