from core.settings import settings
import datetime

import pandas as pd

from database import ScannerStrategyProfile


def _make_profile(**overrides):
    defaults = {
        "profile_name": "Replay Test Profile",
        "source_type": "PRICE_ACTION",
        "script_source": '{"strategy_id":"ascending_triangle_breakout"}',
        "script_hash": f"hash-{datetime.datetime.now().timestamp()}",
        "market": "EGX30",
        "timeframe": "1D",
        "profile_state": "ACTIVE",
    }
    defaults.update(overrides)
    return ScannerStrategyProfile.create(**defaults)


def test_start_replay_records_selected_profile(monkeypatch):
    import core.replay_engine as replay_engine

    profile = _make_profile()

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None, name=None):
            self.target = target
            self.args = args

        def start(self):
            return None

    monkeypatch.setattr(replay_engine, "_resolve_replay_scanner_profile", lambda profile_id=None, use_active_profile=False: profile)
    monkeypatch.setattr(
        replay_engine,
        "_get_replay_intraday_availability",
        lambda replay_date, replay_market="EGX30": {
            "available": True,
            "date": replay_date.isoformat(),
            "intraday_records": 120,
            "available_start_date": "2026-04-30",
            "available_end_date": "2026-04-30",
        },
    )
    monkeypatch.setattr(replay_engine.threading, "Thread", DummyThread)

    result = replay_engine.start_replay(
        replay_date="2026-04-30",
        speed=10,
        notify=False,
        report=False,
        profile_id=profile.id,
        use_active_profile=False,
    )

    assert result["status"] == "started"
    assert result["profile_id"] == profile.id
    assert result["profile_name"] == profile.profile_name
    assert replay_engine._REPLAY_STATE["profile_id"] == profile.id
    assert replay_engine._REPLAY_STATE["profile_name"] == profile.profile_name
    assert replay_engine._REPLAY_STATE["intraday_availability"]["intraday_records"] == 120


def test_start_replay_rejects_date_without_intraday_records(monkeypatch):
    import core.replay_engine as replay_engine

    profile = _make_profile()

    class FailingThread:
        def __init__(self, *args, **kwargs):
            raise AssertionError("replay thread should not start without intraday records")

    monkeypatch.setattr(replay_engine, "_resolve_replay_scanner_profile", lambda profile_id=None, use_active_profile=False: profile)
    monkeypatch.setattr(
        replay_engine,
        "_get_replay_intraday_availability",
        lambda replay_date, replay_market="EGX30": {
            "available": False,
            "date": replay_date.isoformat(),
            "intraday_records": 0,
            "available_start_date": "2026-05-02",
            "available_end_date": "2026-05-05",
            "nearest_next_date": "2026-05-02",
            "available_dates_sample": ["2026-05-02", "2026-05-03", "2026-05-05"],
        },
    )
    monkeypatch.setattr(replay_engine.threading, "Thread", FailingThread)

    result = replay_engine.start_replay(
        replay_date="2026-04-30",
        speed=10,
        notify=False,
        report=False,
        profile_id=profile.id,
    )

    assert result["status"] == "error"
    assert result["code"] == "intraday_data_unavailable"
    assert result["date"] == "2026-04-30"
    assert result["available_start_date"] == "2026-05-02"
    assert "2026-04-30" in result["message"]
    assert "2026-05-02" in result["message"]


def test_start_replay_campaign_rejects_missing_intraday_records(monkeypatch):
    import core.replay_engine as replay_engine

    profile = _make_profile()

    class FailingThread:
        def __init__(self, *args, **kwargs):
            raise AssertionError("campaign replay thread should not start without intraday records")

    monkeypatch.setattr(replay_engine, "_resolve_replay_scanner_profile", lambda profile_id=None, use_active_profile=False: profile)
    monkeypatch.setattr(
        replay_engine,
        "_get_replay_campaign_intraday_availability",
        lambda start_date, end_date, replay_market="EGX30", include_weekends=False, max_days=31, allow_missing_intraday_as_holidays=False: {
            "available": False,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "missing_dates": ["2026-05-13"],
            "replay_dates": ["2026-05-12", "2026-05-14"],
            "days_total": 2,
            "available_start_date": "2026-05-12",
            "available_end_date": "2026-05-14",
        },
    )
    monkeypatch.setattr(replay_engine.threading, "Thread", FailingThread)

    result = replay_engine.start_replay_campaign(
        start_date="2026-05-12",
        end_date="2026-05-14",
        speed=20,
        notify=False,
        report=False,
        profile_id=profile.id,
    )

    assert result["status"] == "error"
    assert result["code"] == "intraday_campaign_data_unavailable"
    assert result["missing_dates"] == ["2026-05-13"]
    assert "2026-05-13" in result["message"]
    assert replay_engine._REPLAY_STATE["status"] == "ERROR"
    assert replay_engine._REPLAY_STATE["mode"] == "CAMPAIGN"


def test_start_replay_campaign_records_campaign_status(monkeypatch):
    import core.replay_engine as replay_engine

    profile = _make_profile()
    started = []

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None, name=None):
            self.target = target
            self.args = args
            self.name = name

        def start(self):
            started.append((self.target.__name__, self.args, self.name))

    monkeypatch.setattr(replay_engine, "_resolve_replay_scanner_profile", lambda profile_id=None, use_active_profile=False: profile)
    monkeypatch.setattr(
        replay_engine,
        "_get_replay_campaign_intraday_availability",
        lambda start_date, end_date, replay_market="EGX30", include_weekends=False, max_days=31, allow_missing_intraday_as_holidays=False: {
            "available": True,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "missing_dates": [],
            "replay_dates": ["2026-05-12", "2026-05-13"],
            "days_total": 2,
            "available_start_date": "2026-05-12",
            "available_end_date": "2026-05-13",
        },
    )
    monkeypatch.setattr(replay_engine.threading, "Thread", DummyThread)

    result = replay_engine.start_replay_campaign(
        start_date="2026-05-12",
        end_date="2026-05-13",
        speed=20,
        notify=False,
        report=False,
        reset_portfolio=False,
        profile_id=profile.id,
    )

    assert result["status"] == "started"
    assert result["mode"] == "CAMPAIGN"
    assert result["days_total"] == 2
    assert result["reset_portfolio"] is False
    assert replay_engine._REPLAY_STATE["mode"] == "CAMPAIGN"
    assert replay_engine._REPLAY_STATE["start_date"] == "2026-05-12"
    assert replay_engine._REPLAY_STATE["end_date"] == "2026-05-13"
    assert replay_engine._REPLAY_STATE["days_total"] == 2
    assert replay_engine._REPLAY_STATE["replay_dates"] == ["2026-05-12", "2026-05-13"]
    assert started == [("_replay_campaign_worker", ([datetime.date(2026, 5, 12), datetime.date(2026, 5, 13)], 20, False, False, False, False, False, False), "ReplayCampaignEngine")]


def test_start_replay_campaign_can_treat_missing_intraday_days_as_holidays(monkeypatch):
    import core.replay_engine as replay_engine

    replay_engine._reset_state()
    profile = _make_profile()
    started = []

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None, name=None):
            self.target = target
            self.args = args
            self.name = name

        def start(self):
            started.append((self.target.__name__, self.args, self.name))

    monkeypatch.setattr(replay_engine, "_resolve_replay_scanner_profile", lambda profile_id=None, use_active_profile=False: profile)
    monkeypatch.setattr(
        replay_engine,
        "_get_replay_campaign_intraday_availability",
        lambda start_date, end_date, replay_market="EGX30", include_weekends=False, max_days=31, allow_missing_intraday_as_holidays=False: {
            "available": allow_missing_intraday_as_holidays,
            "code": "ok" if allow_missing_intraday_as_holidays else "intraday_campaign_data_unavailable",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "missing_dates": ["2026-05-07"],
            "skipped_holiday_dates": ["2026-05-07"] if allow_missing_intraday_as_holidays else [],
            "replay_dates": ["2026-05-06", "2026-05-10"],
            "days_total": 2,
            "available_start_date": "2026-04-23",
            "available_end_date": "2026-05-13",
            "allow_missing_intraday_as_holidays": allow_missing_intraday_as_holidays,
        },
    )
    monkeypatch.setattr(replay_engine.threading, "Thread", DummyThread)

    result = replay_engine.start_replay_campaign(
        start_date="2026-05-06",
        end_date="2026-05-10",
        speed=20,
        notify=False,
        report=False,
        profile_id=profile.id,
        allow_missing_intraday_as_holidays=True,
    )

    assert result["status"] == "started"
    assert result["replay_dates"] == ["2026-05-06", "2026-05-10"]
    assert result["intraday_availability"]["skipped_holiday_dates"] == ["2026-05-07"]
    assert result["allow_missing_intraday_as_holidays"] is True
    assert replay_engine._REPLAY_STATE["allow_missing_intraday_as_holidays"] is True
    assert replay_engine._REPLAY_STATE["skipped_holiday_dates"] == ["2026-05-07"]
    assert started == [("_replay_campaign_worker", ([datetime.date(2026, 5, 6), datetime.date(2026, 5, 10)], 20, False, False, True, False, True, False), "ReplayCampaignEngine")]


def test_load_open_replay_positions_restores_intraday_simulation_book():
    import core.replay_engine as replay_engine
    from database import Portfolio, Position

    portfolio = Portfolio.create(name="Intraday Simulation", type="SYSTEM", auto_manage=True)
    Position.create(
        portfolio=portfolio,
        ticker="ORAS",
        shares=1000,
        entry_price=675.03,
        stop_loss=675.03,
        target_price=718.56,
        target_price_2=747.31,
        tp1_hit=True,
        entry_date=datetime.datetime(2026, 5, 12, 10, 5),
        status="OPEN",
    )
    Position.create(
        portfolio=portfolio,
        ticker="CLOSED",
        shares=1000,
        entry_price=10,
        stop_loss=9,
        target_price=11,
        target_price_2=12,
        status="CLOSED",
    )

    trades = replay_engine._load_open_replay_positions()

    assert trades == [
        {
            "ticker": "ORAS",
            "side": "BUY",
            "state": "TP1_HIT",
            "shares": 1000,
            "entry_price": 675.03,
            "stop_loss": 675.03,
            "tp1": 718.56,
            "tp2": 747.31,
            "tp1_hit": True,
            "exit_reason": None,
            "entry_at": "2026-05-12T10:05:00",
            "exit_at": None,
            "exit_price": None,
        }
    ]


def test_replay_position_entry_debits_cash_and_blocks_overspend(monkeypatch):
    import core.replay_engine as replay_engine
    from database import Portfolio, Position

    portfolio = Portfolio.create(name="Intraday Simulation", type="SYSTEM", auto_manage=True, cash_egp=1000)
    monkeypatch.setattr(replay_engine.TimeUtils, "now", lambda: datetime.datetime(2026, 5, 12, 10, 5))

    first = replay_engine._create_mock_replay_position({
        "ticker": "CASH",
        "shares": 10,
        "entry_price": 50,
        "stop_loss": 45,
        "tp1": 55,
        "tp2": 60,
        "entry_at": "2026-05-12T10:05:00",
    })
    second = replay_engine._create_mock_replay_position({
        "ticker": "RICH",
        "shares": 20,
        "entry_price": 50,
        "stop_loss": 45,
        "tp1": 55,
        "tp2": 60,
        "entry_at": "2026-05-12T10:10:00",
    })

    portfolio = Portfolio.get_by_id(portfolio.id)
    assert first is True
    assert second is False
    assert portfolio.cash_egp == 500
    assert Position.select().where(Position.portfolio == portfolio).count() == 1


def test_replay_position_close_realizes_trade_and_returns_cash(monkeypatch):
    import core.replay_engine as replay_engine
    from database import Portfolio, Position, Trade

    portfolio = Portfolio.create(name="Intraday Simulation", type="SYSTEM", auto_manage=True, cash_egp=500)
    Position.create(
        portfolio=portfolio,
        ticker="CASH",
        shares=10,
        entry_price=50,
        stop_loss=45,
        target_price=55,
        target_price_2=60,
        entry_date=datetime.datetime(2026, 5, 12, 10, 5),
        status="OPEN",
    )
    monkeypatch.setattr(replay_engine.TimeUtils, "now", lambda: datetime.datetime(2026, 5, 12, 11, 15))

    replay_engine._update_mock_position_state("CASH", "CLOSED", exit_price=60, exit_reason="REPLAY_TARGET_2")

    portfolio = Portfolio.get_by_id(portfolio.id)
    trade = Trade.get(Trade.ticker == "CASH")
    assert portfolio.cash_egp == 1100
    assert Position.select().where(Position.portfolio == portfolio).count() == 0
    assert trade.pnl == 100
    assert trade.entry_date == datetime.datetime(2026, 5, 12, 10, 5)
    assert trade.exit_date == datetime.datetime(2026, 5, 12, 11, 15)


def test_campaign_availability_skips_weekends_and_flags_missing_weekdays(monkeypatch):
    import core.replay_engine as replay_engine

    monkeypatch.setattr(
        "data_engine.intraday_store.get_intraday_date_counts",
        lambda realm="EGX": [
            {"date": "2026-05-10", "records": 120, "tickers": 3},
            {"date": "2026-05-12", "records": 140, "tickers": 4},
        ],
    )

    availability = replay_engine._get_replay_campaign_intraday_availability(
        datetime.date(2026, 5, 8),
        datetime.date(2026, 5, 12),
        replay_market="EGX30",
    )

    assert availability["available"] is False
    assert availability["replay_dates"] == ["2026-05-10", "2026-05-12"]
    assert availability["missing_dates"] == ["2026-05-11"]
    assert availability["days_total"] == 2


def test_campaign_availability_can_skip_missing_weekdays_as_holidays(monkeypatch):
    import core.replay_engine as replay_engine

    monkeypatch.setattr(
        "data_engine.intraday_store.get_intraday_date_counts",
        lambda realm="EGX": [
            {"date": "2026-05-06", "records": 120, "tickers": 3},
            {"date": "2026-05-10", "records": 140, "tickers": 4},
        ],
    )

    availability = replay_engine._get_replay_campaign_intraday_availability(
        datetime.date(2026, 5, 6),
        datetime.date(2026, 5, 10),
        replay_market="EGX30",
        allow_missing_intraday_as_holidays=True,
    )

    assert availability["available"] is True
    assert availability["replay_dates"] == ["2026-05-06", "2026-05-10"]
    assert availability["missing_dates"] == ["2026-05-07"]
    assert availability["skipped_holiday_dates"] == ["2026-05-07"]
    assert availability["allow_missing_intraday_as_holidays"] is True


def test_campaign_availability_error_explains_weekend_only_range():
    import core.replay_engine as replay_engine

    message = replay_engine._format_campaign_availability_error({
        "start_date": "2026-05-08",
        "end_date": "2026-05-09",
        "missing_dates": [],
        "available_start_date": "2026-05-10",
        "available_end_date": "2026-05-14",
    })

    assert "does not contain any EGX trading weekdays" in message


def test_replay_campaign_worker_carries_active_trades_between_days(monkeypatch):
    import core.replay_engine as replay_engine

    replay_engine._reset_state()
    replay_engine._REPLAY_STATE.update({
        "mode": "CAMPAIGN",
        "status": "STARTING",
        "started_at": "2026-05-13T02:00:00",
        "profile_id": None,
        "market": "EGX30",
    })
    calls = []

    def fake_run_day(
        replay_date,
        speed,
        notify,
        replay_profile=None,
        replay_market="EGX30",
        day_index=1,
        days_total=1,
        live_channel_routing=False,
    ):
        calls.append((replay_date.isoformat(), list(replay_engine._REPLAY_STATE["active_trades"])))
        if day_index == 1:
            replay_engine._REPLAY_STATE["active_trades"].append({
                "ticker": "ORAS",
                "side": "BUY",
                "state": "OPEN",
                "entry_price": 10.0,
                "stop_loss": 9.0,
                "tp1": 11.0,
                "tp2": 12.0,
            })
        else:
            replay_engine._REPLAY_STATE["active_trades"][0]["state"] = "CLOSED"
        replay_engine._REPLAY_STATE["signals_found"] = day_index
        return {
            "date": replay_date.isoformat(),
            "ticks_completed": 1,
            "total_ticks": 1,
            "signals_found": day_index,
            "open_positions": 1 if day_index == 1 else 0,
            "closed_positions": 0 if day_index == 1 else 1,
            "stopped": False,
        }

    monkeypatch.setattr(replay_engine, "_clear_simulation_portfolio", lambda: None)
    monkeypatch.setattr(replay_engine, "_resolve_replay_scanner_profile", lambda profile_id=None, use_active_profile=False: None)
    monkeypatch.setattr(replay_engine, "_run_replay_campaign_day", fake_run_day)
    monkeypatch.setattr(replay_engine.TimeUtils, "clear_replay", lambda: None)
    monkeypatch.setattr("core.AlertManager.clear_deduplication_state", lambda date_text: None)

    replay_engine._replay_campaign_worker(
        [datetime.date(2026, 5, 12), datetime.date(2026, 5, 13)],
        speed=20,
        notify=False,
        report=False,
        reset_portfolio=True,
    )

    assert calls[0] == ("2026-05-12", [])
    assert calls[1][0] == "2026-05-13"
    assert calls[1][1][0]["ticker"] == "ORAS"
    assert replay_engine._REPLAY_STATE["status"] == "COMPLETED"
    assert replay_engine._REPLAY_STATE["days_completed"] == 2
    assert replay_engine._REPLAY_STATE["campaign_summary"]["closed_positions"] == 1


def test_replay_campaign_summary_counts_lifecycle_outcomes(monkeypatch):
    import core.replay_engine as replay_engine

    replay_engine._reset_state()
    replay_engine._REPLAY_STATE.update({
        "mode": "CAMPAIGN",
        "status": "STARTING",
        "started_at": "2026-05-13T02:00:00",
        "profile_id": None,
        "market": "EGX30",
        "signals_found": 5,
    })

    monkeypatch.setattr(replay_engine, "_clear_simulation_portfolio", lambda: None)
    monkeypatch.setattr(replay_engine, "_resolve_replay_scanner_profile", lambda profile_id=None, use_active_profile=False: None)
    monkeypatch.setattr(replay_engine.TimeUtils, "clear_replay", lambda: None)
    monkeypatch.setattr("core.AlertManager.clear_deduplication_state", lambda date_text: None)
    info_messages = []
    monkeypatch.setattr(replay_engine.logger, "info", lambda message: info_messages.append(message))
    def fake_run_day(*args, **kwargs):
        replay_engine._REPLAY_STATE["active_trades"] = [
            {"ticker": "OPEN", "side": "BUY", "state": "OPEN", "entry_price": 10.0, "stop_loss": 9.0, "tp1": 11.0, "tp2": 12.0},
            {"ticker": "TP1", "side": "BUY", "state": "TP1_HIT", "entry_price": 10.0, "stop_loss": 10.0, "tp1": 11.0, "tp2": 12.0},
            {"ticker": "TP2", "side": "BUY", "state": "CLOSED", "entry_price": 10.0, "stop_loss": 10.0, "tp1": 11.0, "tp2": 12.0, "tp1_hit": True, "exit_reason": "target_2"},
            {"ticker": "SL", "side": "BUY", "state": "CLOSED", "entry_price": 10.0, "stop_loss": 9.0, "tp1": 11.0, "tp2": 12.0, "exit_reason": "stop_loss"},
            {"ticker": "BE", "side": "BUY", "state": "CLOSED", "entry_price": 10.0, "stop_loss": 10.0, "tp1": 11.0, "tp2": 12.0, "tp1_hit": True, "exit_reason": "breakeven_stop"},
        ]
        return {
            "date": "2026-05-12",
            "ticks_completed": 1,
            "total_ticks": 1,
            "signals_found": 5,
            "open_positions": 2,
            "closed_positions": 3,
            "stopped": False,
        }

    monkeypatch.setattr(replay_engine, "_run_replay_campaign_day", fake_run_day)

    replay_engine._replay_campaign_worker(
        [datetime.date(2026, 5, 12)],
        speed=20,
        notify=False,
        report=False,
        reset_portfolio=False,
    )

    summary = replay_engine._REPLAY_STATE["campaign_summary"]
    assert summary["open_positions"] == 2
    assert summary["closed_positions"] == 3
    assert summary["tp1_hits"] == 3
    assert summary["tp2_exits"] == 1
    assert summary["stop_loss_exits"] == 1
    assert summary["breakeven_stop_exits"] == 1
    completion_log = "\n".join(info_messages)
    assert "open=2" in completion_log
    assert "closed=3" in completion_log
    assert "tp1=3" in completion_log
    assert "tp2=1" in completion_log
    assert "sl=1" in completion_log


def test_run_one_tick_uses_selected_profile_for_non_intraday_only(monkeypatch):
    import core.replay_engine as replay_engine

    profile = _make_profile(profile_name="Daily Replay Profile", profile_state="READY")
    core_calls = []
    profile_calls = []

    monkeypatch.setattr(replay_engine.TimeUtils, "now", lambda: datetime.datetime(2026, 4, 30, 14, 10))
    monkeypatch.setattr(
        replay_engine.DailyScanner,
        "get_market_signals",
        lambda index_choice, is_intraday, **kwargs: (core_calls.append((index_choice, is_intraday)) or ([], [], 0.0, "UNKNOWN")),
    )
    monkeypatch.setattr(
        replay_engine,
        "_run_selected_replay_profile_scan",
        lambda selected_profile: (profile_calls.append(selected_profile.id) or ([], [], 0.0, "BULLISH", {"profile_name": selected_profile.profile_name})),
    )
    monkeypatch.setattr(replay_engine, "_persist_replay_signals", lambda signals: None)

    intraday_result = replay_engine._run_one_tick(
        tick_index=1,
        is_intraday=True,
        scan_label="INTRADAY",
        notify=False,
        replay_profile=profile,
        replay_market="EGX30",
    )
    daily_result = replay_engine._run_one_tick(
        tick_index=2,
        is_intraday=False,
        scan_label="DAILY SIGNAL",
        notify=False,
        replay_profile=profile,
        replay_market="EGX30",
    )

    assert intraday_result["error"] is None
    assert daily_result["error"] is None
    assert core_calls == [("EGX30", True)]
    assert profile_calls == [profile.id]


def test_replay_daily_signal_queues_pending_next_open_entry(monkeypatch):
    import core.replay_engine as replay_engine

    signal = {
        "Ticker": "ORAS",
        "Signal_Type": "BUY",
        "Entry_Price": 100.0,
        "Stop_Loss": 95.0,
        "Target_Price": 110.0,
        "Target_Price_2": 118.0,
        "Score": 9,
    }

    replay_engine._reset_state()
    monkeypatch.setattr(replay_engine.TimeUtils, "now", lambda: datetime.datetime(2026, 5, 12, 15, 0))
    monkeypatch.setattr(
        replay_engine.DailyScanner,
        "get_market_signals",
        lambda index_choice, is_intraday, **kwargs: ([signal], [], 78.0, "BULLISH"),
    )
    monkeypatch.setattr("core.AlertManager.filter_new_signals", lambda signals, scan_label: list(signals))
    monkeypatch.setattr(replay_engine, "_persist_replay_signals", lambda signals: None)

    result = replay_engine._run_one_tick(
        tick_index=1,
        is_intraday=False,
        scan_label="DAILY SIGNAL",
        notify=False,
        replay_market="EGX30",
    )

    assert result["error"] is None
    assert result["pending_entries"]["queued"] == 1
    assert result["pending_entries"]["opened"] == 0
    assert replay_engine._REPLAY_STATE["active_trades"] == []
    assert replay_engine._REPLAY_STATE["pending_entries"] == [
        {
            "ticker": "ORAS",
            "state": "PENDING_OPEN",
            "trigger_source": "DAILY_NEXT_OPEN",
            "scan_label": "DAILY SIGNAL",
            "regime": "BULLISH",
            "planned_entry_price": 100.0,
            "queued_at": "2026-05-12T15:00:00",
            "signal": signal,
        }
    ]


def test_replay_reconciles_unconfirmed_pre_close_preview_and_cancels_pending(monkeypatch):
    import core.replay_engine as replay_engine

    replay_engine._reset_state()
    preview = {
        "Ticker": "ORAS",
        "Signal_Type": "BUY",
        "Entry_Price": 100.0,
        "Stop_Loss": 95.0,
        "Target_Price": 110.0,
        "Target_Price_2": 118.0,
        "Score": 9,
    }
    replay_engine._REPLAY_STATE["pending_entries"] = [
        {
            "ticker": "ORAS",
            "state": "PENDING_OPEN",
            "trigger_source": "PRE_CLOSE",
            "scan_label": "PRE-CLOSE",
            "planned_entry_price": 100.0,
            "signal": preview,
        }
    ]
    sent = []
    monkeypatch.setattr(
        replay_engine,
        "_broadcast_replay_followup",
        lambda trade, **kwargs: sent.append((trade, kwargs)) or {"ok": True},
    )

    recorded = replay_engine._record_replay_pre_close_previews([preview])
    result = replay_engine._reconcile_replay_pre_close_previews(
        [{"Ticker": "FWRY", "Signal_Type": "BUY"}],
        notify=True,
    )

    assert recorded["tickers"] == ["ORAS"]
    assert result["cancelled"] == 1
    assert result["cancelled_tickers"] == ["ORAS"]
    assert result["cancelled_pending_entries"] == 1
    assert replay_engine._REPLAY_STATE["pending_entries"] == []
    assert sent == [
        (
            {"ticker": "ORAS", "side": "BUY", "stop_loss": 95.0, "tp2": 118.0},
            {"trigger_state": "CANCELLED", "close_reason": "PRE_CLOSE_NOT_CONFIRMED"},
        )
    ]


def test_replay_intraday_executes_pending_daily_entry_at_visible_open(monkeypatch):
    import core.replay_engine as replay_engine
    from database import Portfolio, Position

    Portfolio.create(name="Intraday Simulation", type="SYSTEM", auto_manage=True, cash_egp=1_000_000)
    replay_engine._reset_state()
    replay_engine._REPLAY_STATE["pending_entries"] = [
        {
            "ticker": "ORAS",
            "state": "PENDING_OPEN",
            "trigger_source": "DAILY_NEXT_OPEN",
            "scan_label": "DAILY SIGNAL",
            "regime": "BULLISH",
            "planned_entry_price": 100.0,
            "queued_at": "2026-05-12T15:00:00",
            "signal": {
                "Ticker": "ORAS",
                "Signal_Type": "BUY",
                "Entry_Price": 100.0,
                "Stop_Loss": 95.0,
                "Target_Price": 110.0,
                "Target_Price_2": 118.0,
                "Score": 9,
            },
        }
    ]
    bar = pd.DataFrame(
        [{"Open": 101.0, "High": 101.2, "Low": 100.8, "Close": 101.1, "Volume": 1000}],
        index=[pd.Timestamp("2026-05-13 10:00")],
    )

    monkeypatch.setattr(settings, "PENDING_ENTRY_MAX_GAP_PCT", 1.5, raising=False)
    monkeypatch.setattr(settings, "COMMISSION_PCT", 0.0, raising=False)
    monkeypatch.setattr(settings, "SLIPPAGE_PCT", 0.0, raising=False)
    monkeypatch.setattr(replay_engine.TimeUtils, "now", lambda: datetime.datetime(2026, 5, 13, 10, 0))
    monkeypatch.setattr(
        "core.DataManager.DataManager.get_intraday_data",
        lambda ticker, limit=1, refresh_if_stale=False: bar,
    )
    monkeypatch.setattr(
        replay_engine.DailyScanner,
        "get_market_signals",
        lambda index_choice, is_intraday, **kwargs: ([], [], 80.0, "BULLISH"),
    )
    monkeypatch.setattr("core.AlertManager.filter_new_signals", lambda signals, scan_label: list(signals))
    monkeypatch.setattr(replay_engine, "_persist_replay_signals", lambda signals: None)

    result = replay_engine._run_one_tick(
        tick_index=1,
        is_intraday=True,
        scan_label="INTRADAY",
        notify=False,
        replay_market="EGX30",
    )

    assert result["error"] is None
    assert result["pending_entries"]["opened"] == 1
    assert result["pending_entries"]["skipped"] == 0
    assert replay_engine._REPLAY_STATE["pending_entries"] == []
    assert len(replay_engine._REPLAY_STATE["active_trades"]) == 1
    trade = replay_engine._REPLAY_STATE["active_trades"][0]
    assert trade["ticker"] == "ORAS"
    assert trade["planned_entry_price"] == 100.0
    assert trade["actual_entry_price"] == 101.0
    assert trade["gap_pct"] == 1.0
    assert trade["trigger_source"] == "DAILY_NEXT_OPEN"
    position = Position.get(Position.ticker == "ORAS")
    assert position.entry_price == 101.0


def test_replay_intraday_skips_pending_daily_entry_when_gap_exceeds_limit(monkeypatch):
    import core.replay_engine as replay_engine

    replay_engine._reset_state()
    replay_engine._REPLAY_STATE["pending_entries"] = [
        {
            "ticker": "ORAS",
            "state": "PENDING_OPEN",
            "trigger_source": "DAILY_NEXT_OPEN",
            "scan_label": "DAILY SIGNAL",
            "regime": "BULLISH",
            "planned_entry_price": 100.0,
            "queued_at": "2026-05-12T15:00:00",
            "signal": {
                "Ticker": "ORAS",
                "Signal_Type": "BUY",
                "Entry_Price": 100.0,
                "Stop_Loss": 95.0,
                "Target_Price": 110.0,
                "Target_Price_2": 118.0,
                "Score": 9,
            },
        }
    ]
    bar = pd.DataFrame(
        [{"Open": 103.0, "High": 103.2, "Low": 102.8, "Close": 103.1, "Volume": 1000}],
        index=[pd.Timestamp("2026-05-13 10:00")],
    )

    monkeypatch.setattr(settings, "PENDING_ENTRY_MAX_GAP_PCT", 1.5, raising=False)
    monkeypatch.setattr(replay_engine.TimeUtils, "now", lambda: datetime.datetime(2026, 5, 13, 10, 0))
    monkeypatch.setattr(
        "core.DataManager.DataManager.get_intraday_data",
        lambda ticker, limit=1, refresh_if_stale=False: bar,
    )
    monkeypatch.setattr(
        replay_engine.DailyScanner,
        "get_market_signals",
        lambda index_choice, is_intraday, **kwargs: ([], [], 80.0, "BULLISH"),
    )
    monkeypatch.setattr("core.AlertManager.filter_new_signals", lambda signals, scan_label: list(signals))
    monkeypatch.setattr(replay_engine, "_persist_replay_signals", lambda signals: None)

    result = replay_engine._run_one_tick(
        tick_index=1,
        is_intraday=True,
        scan_label="INTRADAY",
        notify=False,
        replay_market="EGX30",
    )

    assert result["error"] is None
    assert result["pending_entries"]["opened"] == 0
    assert result["pending_entries"]["skipped"] == 1
    assert result["pending_entries"]["items"][0]["reason"] == "gap_threshold_exceeded"
    assert replay_engine._REPLAY_STATE["pending_entries"] == []
    assert replay_engine._REPLAY_STATE["active_trades"] == []


def test_replay_intraday_notifies_entry_once_without_signal_summary(monkeypatch):
    import core.replay_engine as replay_engine

    signal = {
        "Ticker": "ORAS",
        "Signal_Type": "BUY",
        "Entry_Price": 675.03,
        "Stop_Loss": 642.38,
        "Target_Price": 718.56,
        "Target_Price_2": 747.31,
        "Score": 9,
    }
    signal_broadcasts = []
    entries = []

    monkeypatch.setattr(replay_engine.TimeUtils, "now", lambda: datetime.datetime(2026, 5, 12, 11, 5))
    monkeypatch.setattr(
        replay_engine.DailyScanner,
        "get_market_signals",
        lambda index_choice, is_intraday, **kwargs: ([signal], [], 80.0, "BULLISH"),
    )
    monkeypatch.setattr("core.AlertManager.filter_new_signals", lambda signals, scan_label: list(signals))
    monkeypatch.setattr(replay_engine, "_persist_replay_signals", lambda signals: None)
    monkeypatch.setattr(replay_engine, "_broadcast_replay_signals", lambda *args, **kwargs: signal_broadcasts.append(args))
    monkeypatch.setattr(replay_engine, "_create_mock_replay_position", lambda trade: True)
    monkeypatch.setattr(replay_engine, "_notify_replay_entry", lambda sig: entries.append(sig["Ticker"]))
    monkeypatch.setattr(replay_engine, "_mock_trade_monitor", lambda notify=True: None)
    replay_engine._reset_state()

    result = replay_engine._run_one_tick(
        tick_index=1,
        is_intraday=True,
        scan_label="INTRADAY",
        notify=True,
        replay_market="EGX30",
    )

    assert result["error"] is None
    assert entries == ["ORAS"]
    assert signal_broadcasts == []


def test_replay_entry_notification_sends_single_card_when_available(monkeypatch):
    import core.replay_engine as replay_engine

    alerts = []
    images = []
    signal = {
        "Ticker": "ORAS",
        "Entry_Price": 675.03,
        "Stop_Loss": 642.38,
        "Target_Price": 718.56,
        "Target_Price_2": 747.31,
        "Score": 9,
    }

    monkeypatch.setattr("core.TelegramBot_Alerts._test_telegram_config", lambda: ("token", "chat"))
    monkeypatch.setattr("core.ReportGenerator.create_horus_signal_card", lambda **kwargs: "card-bytes")
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda message, **kwargs: alerts.append((message, kwargs)))
    monkeypatch.setattr("core.AlertManager.broadcast_image", lambda image, caption, **kwargs: images.append((image, caption, kwargs)))

    replay_engine._notify_replay_entry(signal)

    assert alerts == []
    assert len(images) == 1
    assert images[0][0] == "card-bytes"
    assert "ORAS" in images[0][1]


def test_replay_monitor_advances_trade_without_notifications(monkeypatch):
    import core.replay_engine as replay_engine

    replay_engine._reset_state()
    replay_engine._REPLAY_STATE["active_trades"] = [
        {
            "ticker": "COMI",
            "side": "BUY",
            "state": "OPEN",
            "entry_price": 10.0,
            "stop_loss": 9.5,
            "tp1": 11.0,
            "tp2": 12.0,
        }
    ]
    updates = []
    broadcasts = []
    bar = pd.DataFrame(
        [{"Open": 10.0, "High": 11.2, "Low": 10.0, "Close": 11.1, "Volume": 1000}],
        index=[pd.Timestamp("2026-04-30 10:05")],
    )

    monkeypatch.setattr(
        "core.DataManager.DataManager.get_intraday_data",
        lambda ticker, limit=1, refresh_if_stale=False: bar,
    )
    monkeypatch.setattr(replay_engine, "_update_mock_position_state", lambda *args, **kwargs: updates.append((args, kwargs)))
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda *args, **kwargs: broadcasts.append((args, kwargs)))
    monkeypatch.setattr("core.TelegramBot_Alerts._test_telegram_config", lambda: ("token", "chat"))

    replay_engine._mock_trade_monitor(notify=False)

    trade = replay_engine._REPLAY_STATE["active_trades"][0]
    assert trade["state"] == "TP1_HIT"
    assert trade["stop_loss"] == 10.0
    assert trade["tp1_hit"] is True
    assert updates == [(("COMI", "OPEN"), {"tp1_hit": True, "new_sl": 10.0})]
    assert broadcasts == []


def test_replay_monitor_labels_breakeven_stop_after_tp1(monkeypatch):
    import core.replay_engine as replay_engine

    replay_engine._reset_state()
    replay_engine._REPLAY_STATE["active_trades"] = [
        {
            "ticker": "COMI",
            "side": "BUY",
            "state": "TP1_HIT",
            "entry_price": 10.0,
            "stop_loss": 10.0,
            "tp1": 11.0,
            "tp2": 12.0,
        }
    ]
    messages = []
    bar = pd.DataFrame(
        [{"Open": 10.6, "High": 10.8, "Low": 9.9, "Close": 10.0, "Volume": 1000}],
        index=[pd.Timestamp("2026-04-30 10:10")],
    )

    monkeypatch.setattr(
        "core.DataManager.DataManager.get_intraday_data",
        lambda ticker, limit=1, refresh_if_stale=False: bar,
    )
    monkeypatch.setattr(replay_engine, "_update_mock_position_state", lambda *args, **kwargs: None)
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda message, **kwargs: messages.append(message))
    monkeypatch.setattr("core.TelegramBot_Alerts._test_telegram_config", lambda: ("token", "chat"))

    replay_engine._mock_trade_monitor(notify=True)

    assert replay_engine._REPLAY_STATE["active_trades"][0]["state"] == "CLOSED"
    assert replay_engine._REPLAY_STATE["active_trades"][0]["exit_reason"] == "breakeven_stop"
    assert any("Breakeven Stop hit" in message for message in messages)


def test_replay_monitor_uses_daily_followup_copy_for_tp1_tp2_and_stop_loss(monkeypatch):
    import core.replay_engine as replay_engine

    replay_engine._reset_state()
    replay_engine._REPLAY_STATE["active_trades"] = [
        {
            "ticker": "TP1",
            "side": "BUY",
            "state": "OPEN",
            "entry_price": 10.0,
            "stop_loss": 9.5,
            "tp1": 11.0,
            "tp2": 12.0,
        },
        {
            "ticker": "TP2",
            "side": "BUY",
            "state": "TP1_HIT",
            "entry_price": 10.0,
            "stop_loss": 10.0,
            "tp1": 11.0,
            "tp2": 12.0,
        },
        {
            "ticker": "SL",
            "side": "BUY",
            "state": "OPEN",
            "entry_price": 10.0,
            "stop_loss": 9.5,
            "tp1": 11.0,
            "tp2": 12.0,
        },
    ]
    bars = {
        "TP1": pd.DataFrame([{"Open": 10.5, "High": 11.1, "Low": 10.2, "Close": 11.0}], index=[pd.Timestamp("2026-05-12 10:10")]),
        "TP2": pd.DataFrame([{"Open": 11.5, "High": 12.1, "Low": 11.4, "Close": 12.0}], index=[pd.Timestamp("2026-05-12 10:15")]),
        "SL": pd.DataFrame([{"Open": 10.0, "High": 10.2, "Low": 9.4, "Close": 9.5}], index=[pd.Timestamp("2026-05-12 10:20")]),
    }
    messages = []

    monkeypatch.setattr("core.TelegramBot_Alerts._test_telegram_config", lambda: ("token", "chat"))
    monkeypatch.setattr(
        "core.DataManager.DataManager.get_intraday_data",
        lambda ticker, limit=1, refresh_if_stale=False: bars[ticker],
    )
    monkeypatch.setattr(replay_engine, "_update_mock_position_state", lambda *args, **kwargs: None)
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda message, **kwargs: messages.append(message))

    replay_engine._mock_trade_monitor(notify=True)

    assert messages == [
        (
            "🎯 *HORUS TRADE UPDATE | TARGET 1 HIT*\n"
            "HORUS UPDATE\n"
            "Ticker: *TP1* | Direction: *BUY*\n"
            "• Target 1 reached successfully.\n"
            "• Move stop loss to breakeven at *10.00 LE*.\n"
            "• Keep Target 2 active at *12.00 LE*.\n"
            "🛡️ Capital protected. Let the runner trade."
        ),
        (
            "🏁 *HORUS TRADE CLOSE | TARGET 2 REACHED*\n"
            "HORUS CLOSE\n"
            "Ticker: *TP2* | Direction: *BUY*\n"
            "• Final target reached at *12.00 LE*.\n"
            "• Signal fully closed. No further action.\n"
            "✨ Trade complete."
        ),
        (
            "🛑 *HORUS TRADE CLOSE | STOP LOSS HIT*\n"
            "HORUS CLOSE\n"
            "Ticker: *SL* | Direction: *BUY*\n"
            "• Stop Loss hit at *9.50 LE*.\n"
            "• Signal fully closed. No further action.\n"
            "🛡️ Capital preservation is rule #1."
        ),
    ]


def test_replay_live_channel_routing_uses_main_telegram_config(monkeypatch):
    from core import TelegramBot_Alerts, TimeUtils

    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "main-token", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "main-chat", raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_TEST_BOT_TOKEN", "test-token", raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_TEST_CHAT_ID", "test-chat", raising=False)

    TimeUtils.set_replay(datetime.datetime(2026, 5, 12, 10, 0), market_override=True, live_channel_routing=True)
    try:
        assert TelegramBot_Alerts._current_telegram_config() == {
            "token": "main-token",
            "chat_id": "main-chat",
        }
    finally:
        TimeUtils.clear_replay()


def test_start_replay_records_live_channel_routing(monkeypatch):
    import core.replay_engine as replay_engine

    profile = _make_profile()
    started = []

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None, name=None):
            self.target = target
            self.args = args
            self.name = name

        def start(self):
            started.append((self.target.__name__, self.args, self.name))

    monkeypatch.setattr(replay_engine, "_resolve_replay_scanner_profile", lambda profile_id=None, use_active_profile=False: profile)
    monkeypatch.setattr(
        replay_engine,
        "_get_replay_intraday_availability",
        lambda replay_date, replay_market="EGX30": {
            "available": True,
            "date": replay_date.isoformat(),
            "intraday_records": 120,
            "available_start_date": "2026-05-12",
            "available_end_date": "2026-05-12",
        },
    )
    monkeypatch.setattr(replay_engine.threading, "Thread", DummyThread)

    result = replay_engine.start_replay(
        replay_date="2026-05-12",
        speed=10,
        notify=True,
        report=False,
        profile_id=profile.id,
        live_channel_routing=True,
    )

    assert result["status"] == "started"
    assert result["live_channel_routing"] is True
    assert replay_engine._REPLAY_STATE["live_channel_routing"] is True
    assert started == [
        (
            "_replay_worker",
            (datetime.date(2026, 5, 12), 10, True, False, False, True),
            "ReplayEngine",
        )
    ]


def test_broadcast_replay_followup_suppresses_exit_card_for_cancelled_and_zero_entry(monkeypatch):
    import core.replay_engine as replay_engine
    from core import ReportGenerator, AlertManager

    cards_generated = []
    images_broadcast = []
    alerts_broadcast = []

    monkeypatch.setattr(
        "core.ReportGenerator.create_exit_card",
        lambda *args, **kwargs: cards_generated.append((args, kwargs)) or object(),
    )
    monkeypatch.setattr(
        "core.AlertManager.broadcast_image",
        lambda *args, **kwargs: images_broadcast.append((args, kwargs)),
    )
    monkeypatch.setattr(
        "core.AlertManager.broadcast_alert",
        lambda msg, **kwargs: alerts_broadcast.append(msg) or {"ok": True},
    )

    # 1. Unconfirmed / Cancelled Pre-Close Signal (No entry exists)
    cancelled_trade = {
        "ticker": "MASR",
        "side": "BUY",
        "stop_loss": 8.327,
        "tp2": 9.50,
    }
    replay_engine._broadcast_replay_followup(
        cancelled_trade,
        trigger_state="CANCELLED",
        close_reason="PRE_CLOSE_NOT_CONFIRMED",
    )

    assert len(cards_generated) == 0, "Exit card must NEVER be generated for cancelled pre-close signal!"
    assert len(images_broadcast) == 0, "Image must NEVER be broadcast for cancelled pre-close signal!"
    assert len(alerts_broadcast) == 1
    assert "MASR" in alerts_broadcast[0]
    assert "Pre-close signal not confirmed" in alerts_broadcast[0]

    # 2. Stop loss hit with invalid/missing entry price (entry_price <= 0)
    zero_entry_trade = {
        "ticker": "MOIN",
        "side": "BUY",
        "entry_price": 0.0,
        "stop_loss": 38.54,
    }
    replay_engine._broadcast_replay_followup(
        zero_entry_trade,
        trigger_state="STOP_LOSS_HIT",
        close_price=38.54,
    )
    assert len(cards_generated) == 0, "Exit card must NEVER be generated when entry_price <= 0!"
    assert len(images_broadcast) == 0, "Image must NEVER be broadcast when entry_price <= 0!"
    assert len(alerts_broadcast) == 2


def test_create_exit_card_raises_on_non_positive_entry():
    import pytest
    from core import ReportGenerator

    with pytest.raises(ValueError, match="entry price must be positive"):
        ReportGenerator.create_exit_card(
            ticker="MASR",
            exit_price=8.327,
            entry_price=0.0,
            pnl_pct=0.0,
            reason="STOP_LOSS",
        )

