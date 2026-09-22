"""
Tests for HistoricalBackfill module and /api/system/backfill endpoints.
"""
from core.settings import settings
import datetime

from fastapi.testclient import TestClient
from peewee import fn
import pandas as pd

from core import TimeUtils
from core import DailyScanner
from api import app
from database import BackfillIntradayCheckpoint, Holiday, ProvisioningState, Signal

client = TestClient(app, raise_server_exceptions=False)


def _fake_signals_factory(tickers=None):
    """Return a mock get_market_signals that produces deterministic signals."""
    tickers = tickers or ["COMI", "EFIH"]
    def _mock_get_market_signals(index_choice="ALL", is_intraday=False, **kwargs):
        signals = []
        for t in tickers:
            signals.append({
                "Ticker": t,
                "Signal_Type": "BUY",
                "Entry_Price": 100.0,
                "Stop_Loss": 95.0,
                "Target_Price": 108.0,
                "Score": 8,
                "RSI": 62.0,
                "Volume_x": 1.5,
            })
        breadth = 55.0
        regime = {"regime": "BULLISH", "score": 7}
        return signals, [], breadth, regime
    return _mock_get_market_signals


def test_backfill_generates_signals(monkeypatch):
    """Backfill for 7 days should create Signal records with correct dates."""
    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI", "EFIH"])
    monkeypatch.setattr(DailyScanner, "get_market_signals", _fake_signals_factory())

    from core.market.HistoricalBackfill import  run_backfill
    result = run_backfill(days=7)

    assert result["status"] == "COMPLETED"
    assert result["signals_found"] > 0

    # Verify signals exist in the DB
    total = Signal.select().where(Signal.source == "Backfill").count()
    assert total > 0

    # Verify simulation is cleared
    assert TimeUtils.is_simulating() is False


def test_backfill_generates_intraday_and_swing_sources_by_default(monkeypatch):
    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI"])

    def _scanner(index_choice="ALL", is_intraday=False, **kwargs):
        signal_type = "INTRADAY_BREAKOUT" if is_intraday else "SWING_BREAKOUT"
        return (
            [{
                "Ticker": "COMI",
                "Signal_Type": signal_type,
                "Entry_Price": 100.0,
                "Score": 8,
            }],
            [],
            55.0,
            {"regime": "BULLISH"},
        )

    monkeypatch.setattr(DailyScanner, "get_market_signals", _scanner)

    from core.market.HistoricalBackfill import  run_backfill
    result = run_backfill(days=2)

    assert result["status"] == "COMPLETED"
    assert result["intraday_signals_found"] > 0
    assert result["swing_signals_found"] > 0
    assert Signal.select().where(Signal.source == "Backfill").count() > 0
    assert Signal.select().where(Signal.source == "BackfillIntraday").count() > 0


def test_backfill_skips_weekends(monkeypatch):
    """No signals should be generated for Friday/Saturday (EGX weekends)."""
    monkeypatch.setattr(DailyScanner, "get_market_signals", _fake_signals_factory())

    from core.market.HistoricalBackfill import  run_backfill
    run_backfill(days=14)

    # Check that no signals exist on a Friday or Saturday
    all_signals = list(Signal.select().where(Signal.source == "Backfill").dicts())
    for sig in all_signals:
        day = sig["date"]
        if isinstance(day, str):
            day = datetime.date.fromisoformat(day)
        # 4 = Friday, 5 = Saturday
        assert day.weekday() not in {4, 5}, f"Signal found on weekend day: {day} (weekday={day.weekday()})"


def test_backfill_clears_simulation_on_error(monkeypatch):
    """TimeUtils should be cleared even if DailyScanner throws."""
    def _exploding_scanner(**kwargs):
        raise RuntimeError("kaboom")

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI"])
    monkeypatch.setattr(DailyScanner, "get_market_signals", _exploding_scanner)

    from core.market.HistoricalBackfill import  run_backfill
    result = run_backfill(days=3)

    # Systemic replay failure should be explicit.
    assert result["status"] == "ERROR"
    assert TimeUtils.is_simulating() is False


def test_backfill_api_start(monkeypatch):
    """POST /api/system/backfill should return started status."""
    from core.market import HistoricalBackfill
    monkeypatch.setattr(HistoricalBackfill, "run_backfill", lambda **kwargs: {"status": "COMPLETED"})
    HistoricalBackfill.BACKFILL_STATE.update({"status": "IDLE"})

    res = client.post("/api/v1/system/backfill?days=3")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "started"


def test_backfill_api_start_defaults_to_saved_trading_days(monkeypatch):
    from core.market import HistoricalBackfill

    monkeypatch.setattr(
        HistoricalBackfill,
        "run_backfill",
        lambda days=252, mode="MANUAL", progress_callback=None, universe_choice="EGX30", signal_lanes="BOTH": {"status": "COMPLETED"},
    )
    HistoricalBackfill.BACKFILL_STATE.update({"status": "IDLE"})
    monkeypatch.setattr(settings, "HISTORICAL_BACKFILL_TRADING_DAYS", 126, raising=False)

    res = client.post("/api/v1/system/backfill")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] in {"started", "already_running"}
    assert body["days"] == 126


def test_backfill_api_start_defaults_to_252_when_setting_missing(monkeypatch):
    from core.market import HistoricalBackfill

    monkeypatch.setattr(
        HistoricalBackfill,
        "run_backfill",
        lambda days=252, mode="MANUAL", progress_callback=None, universe_choice="EGX30", signal_lanes="BOTH": {"status": "COMPLETED"},
    )
    HistoricalBackfill.BACKFILL_STATE.update({"status": "IDLE"})
    monkeypatch.delattr(settings, "HISTORICAL_BACKFILL_TRADING_DAYS", raising=False)

    res = client.post("/api/v1/system/backfill")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] in {"started", "already_running"}
    assert body["days"] == 252


def test_backfill_api_start_passes_selected_universe(monkeypatch):
    from core.market import HistoricalBackfill

    call = {}

    def _fake_run_backfill(days=252, mode="MANUAL", progress_callback=None, universe_choice="EGX30", signal_lanes="BOTH"):
        call["days"] = days
        call["mode"] = mode
        call["universe_choice"] = universe_choice
        call["signal_lanes"] = signal_lanes
        return {"status": "COMPLETED"}

    monkeypatch.setattr(HistoricalBackfill, "run_backfill", _fake_run_backfill)
    HistoricalBackfill.BACKFILL_STATE.update({"status": "IDLE"})

    res = client.post("/api/v1/system/backfill?days=21&universe=EGX100")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] in {"started", "already_running"}
    assert body["days"] == 21
    assert body["universe_choice"] == "EGX100"
    assert body["signal_lanes"] == "BOTH"
    assert call == {"days": 21, "mode": "MANUAL", "universe_choice": "EGX100", "signal_lanes": "BOTH"}


def test_backfill_api_start_passes_selected_signal_lanes(monkeypatch):
    from core.market import HistoricalBackfill

    call = {}

    def _fake_run_backfill(days=252, mode="MANUAL", progress_callback=None, universe_choice="EGX30", signal_lanes="BOTH"):
        call["days"] = days
        call["mode"] = mode
        call["universe_choice"] = universe_choice
        call["signal_lanes"] = signal_lanes
        return {"status": "COMPLETED"}

    monkeypatch.setattr(HistoricalBackfill, "run_backfill", _fake_run_backfill)
    HistoricalBackfill.BACKFILL_STATE.update({"status": "IDLE"})

    res = client.post("/api/v1/system/backfill?days=10&universe=EGX30&signal_lanes=SWING")

    assert res.status_code == 200
    body = res.json()
    assert body["status"] in {"started", "already_running"}
    assert body["signal_lanes"] == "SWING"
    assert call["signal_lanes"] == "SWING"


def test_backfill_api_start_rejects_invalid_universe(monkeypatch):
    from core.market import HistoricalBackfill

    monkeypatch.setattr(
        HistoricalBackfill,
        "run_backfill",
        lambda days=252, mode="MANUAL", progress_callback=None, universe_choice="EGX30", signal_lanes="BOTH": {"status": "COMPLETED"},
    )
    HistoricalBackfill.BACKFILL_STATE.update({"status": "IDLE"})

    res = client.post("/api/v1/system/backfill?days=21&universe=BAD")

    assert res.status_code == 400
    assert "universe" in str(res.json()).lower()


def test_backfill_api_status():
    """GET /api/system/backfill/status should return the state dict."""
    res = client.get("/api/v1/system/backfill/status")
    assert res.status_code == 200
    body = res.json()
    assert "status" in body
    assert "progress" in body
    assert "total_days" in body


def test_backfill_api_status_exposes_durable_provisioning_metadata():
    from core.market.HistoricalBackfill import  BACKFILL_STATE

    BACKFILL_STATE.update(
        {
            "status": "IDLE",
            "current_day": None,
            "progress": 0,
            "total_days": 0,
            "signals_found": 0,
            "mode": "MANUAL",
            "target_kind": "TRADING_DAYS",
            "universe_choice": "FULL",
            "error": None,
        }
    )

    ProvisioningState.create(
        target_trading_days=252,
        completed_trading_days=200,
        status="COMPLETED_WITH_WARNINGS",
        mode="AUTOMATIC",
        started_at=datetime.datetime(2026, 3, 20, 8, 0, 0),
        completed_at=datetime.datetime(2026, 3, 24, 9, 30, 0),
        last_error="Provisioning completed with limited historical coverage.",
    )

    res = client.get("/api/v1/system/backfill/status")

    assert res.status_code == 200
    body = res.json()
    assert body["durable_status"] == "COMPLETED_WITH_WARNINGS"
    assert body["target_trading_days"] == 252
    assert body["completed_trading_days"] == 200
    assert body["mode"] == "AUTOMATIC"
    assert body["universe_choice"] == "FULL"
    assert body["last_error"] == "Provisioning completed with limited historical coverage."
    assert body["started_at"] == "2026-03-20T08:00:00"
    assert body["completed_at"] == "2026-03-24T09:30:00"


def test_recent_market_days_targets_trading_days_not_calendar_days():
    from core.market import HistoricalBackfill

    days = HistoricalBackfill._recent_market_days(
        end_date=datetime.date(2026, 3, 24),
        trading_days=5,
    )

    assert days == [
        datetime.date(2026, 3, 17),
        datetime.date(2026, 3, 18),
        datetime.date(2026, 3, 19),
        datetime.date(2026, 3, 22),
        datetime.date(2026, 3, 23),
    ]


def test_recent_market_days_skip_db_holidays():
    from core.market import HistoricalBackfill

    Holiday.create(date=datetime.date(2026, 3, 23), description="Observed holiday")

    days = HistoricalBackfill._recent_market_days(
        end_date=datetime.date(2026, 3, 24),
        trading_days=5,
    )

    assert days == [
        datetime.date(2026, 3, 16),
        datetime.date(2026, 3, 17),
        datetime.date(2026, 3, 18),
        datetime.date(2026, 3, 19),
        datetime.date(2026, 3, 22),
    ]


def test_backfill_days_parameter_is_interpreted_as_trading_day_target(monkeypatch):
    from core.market import HistoricalBackfill

    TimeUtils.set_simulation(datetime.datetime(2026, 3, 24, 10, 0, 0))

    short_history = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0],
            "High": [101.0, 102.0, 103.0, 104.0],
            "Low": [99.0, 100.0, 101.0, 102.0],
            "Close": [100.5, 101.5, 102.5, 103.5],
            "Volume": [1000, 1100, 1200, 1300],
        },
        index=pd.to_datetime(["2026-03-18", "2026-03-19", "2026-03-22", "2026-03-23"]),
    )

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI"])
    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", lambda *args, **kwargs: short_history.copy())
    monkeypatch.setattr(DailyScanner, "get_market_signals", _fake_signals_factory(["COMI"]))

    result = HistoricalBackfill.run_backfill(days=3)

    assert result["status"] == "COMPLETED"
    assert result["total_days"] == 3
    assert result["target_kind"] == "TRADING_DAYS"
    assert HistoricalBackfill.BACKFILL_STATE["mode"] == "MANUAL"

    backfill_dates = [
        row.date
        for row in Signal.select().where(Signal.source == "Backfill").order_by(Signal.date.asc())
    ]
    assert backfill_dates == [
        datetime.date(2026, 3, 19),
        datetime.date(2026, 3, 22),
        datetime.date(2026, 3, 23),
    ]


def test_backfill_skips_scanner_when_no_tickers_are_available(monkeypatch):
    from core.market import HistoricalBackfill

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: [])

    def _should_not_run(**kwargs):
        raise AssertionError("scanner should not run when ticker universe is empty")

    monkeypatch.setattr(DailyScanner, "get_market_signals", _should_not_run)

    result = HistoricalBackfill.run_backfill(days=3)

    assert result["status"] == "COMPLETED_WITH_WARNINGS"
    assert result["total_days"] == 0
    assert "no tickers" in str(result["error"]).lower()


def test_backfill_tolerates_short_scanner_return_shape(monkeypatch, caplog):
    from core.market import HistoricalBackfill

    TimeUtils.set_simulation(datetime.datetime(2026, 3, 24, 10, 0, 0))

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI"])
    monkeypatch.setattr(DailyScanner, "get_market_signals", lambda **kwargs: ([], []))

    with caplog.at_level("WARNING", logger="HistoricalBackfill"):
        result = HistoricalBackfill.run_backfill(days=1)

    assert result["status"] == "COMPLETED"
    assert result["signals_found"] == 0
    assert not any("Backfill error on" in record.message for record in caplog.records)


def test_backfill_marks_short_history_as_completed_with_warnings(monkeypatch):
    from core.market import HistoricalBackfill

    TimeUtils.set_simulation(datetime.datetime(2026, 3, 24, 10, 0, 0))

    short_history = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0],
            "High": [101.0, 102.0, 103.0, 104.0],
            "Low": [99.0, 100.0, 101.0, 102.0],
            "Close": [100.5, 101.5, 102.5, 103.5],
            "Volume": [1000, 1100, 1200, 1300],
        },
        index=pd.to_datetime(["2026-03-18", "2026-03-19", "2026-03-22", "2026-03-23"]),
    )

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI"])
    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", lambda *args, **kwargs: short_history.copy())
    monkeypatch.setattr(DailyScanner, "get_market_signals", _fake_signals_factory(["COMI"]))
    # Ensure state is clean before run
    HistoricalBackfill.BACKFILL_STATE.update({"status": "IDLE"})
    if HistoricalBackfill._backfill_lock.locked():
        HistoricalBackfill._backfill_lock.release()

    result = HistoricalBackfill.run_backfill(days=5)

    assert result["status"] == "COMPLETED_WITH_WARNINGS"
    assert result["total_days"] == 4
    assert "shorter than target" in str(result["error"]).lower()


def test_backfill_marks_partial_day_failures_as_completed_with_warnings(monkeypatch):
    from core.market import HistoricalBackfill

    TimeUtils.set_simulation(datetime.datetime(2026, 3, 24, 10, 0, 0))

    call_count = {"count": 0}

    def _sometimes_fails(**kwargs):
        call_count["count"] += 1
        if call_count["count"] == 2:
            raise RuntimeError("day data gap")
        return _fake_signals_factory(["COMI"])(**kwargs)

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI"])
    monkeypatch.setattr(DailyScanner, "get_market_signals", _sometimes_fails)

    result = HistoricalBackfill.run_backfill(days=3)

    assert result["status"] == "COMPLETED_WITH_WARNINGS"
    assert result["total_days"] == 3
    assert result["signals_found"] > 0
    assert "1 lane run" in str(result["error"]).lower()


def test_backfill_handles_tz_aware_universe_slice(monkeypatch):
    from core.market import HistoricalBackfill

    TimeUtils.set_simulation(datetime.datetime(2026, 4, 6, 10, 0, 0))

    short_history = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0],
            "High": [101.0, 102.0, 103.0, 104.0],
            "Low": [99.0, 100.0, 101.0, 102.0],
            "Close": [100.5, 101.5, 102.5, 103.5],
            "Volume": [1000, 1100, 1200, 1300],
        },
        index=pd.to_datetime(["2026-03-31", "2026-04-01", "2026-04-02", "2026-04-05"]),
    )

    universe_df = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0],
            "High": [101.0, 102.0, 103.0, 104.0],
            "Low": [99.0, 100.0, 101.0, 102.0],
            "Close": [100.5, 101.5, 102.5, 103.5],
            "Volume": [1000, 1100, 1200, 1300],
        },
        index=pd.MultiIndex.from_arrays(
            [
                ["COMI", "COMI", "COMI", "COMI"],
                pd.to_datetime(
                    [
                        "2026-03-31T12:00:00Z",
                        "2026-04-01T12:00:00Z",
                        "2026-04-02T12:00:00Z",
                        "2026-04-05T12:00:00Z",
                    ],
                    utc=True,
                ),
            ],
            names=["Ticker", "Date"],
        ),
    )

    def _scanner(**kwargs):
        sliced = kwargs.get("universe_df")
        assert sliced is not None
        assert not sliced.empty
        return _fake_signals_factory(["COMI"])(**kwargs)

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI"])
    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", lambda *args, **kwargs: short_history.copy())
    monkeypatch.setattr("core.DataManager.DataManager.get_universe_data", lambda *args, **kwargs: universe_df.copy())
    monkeypatch.setattr(DailyScanner, "get_market_signals", _scanner)

    result = HistoricalBackfill.run_backfill(days=3)

    assert result["status"] == "COMPLETED"
    assert result["total_days"] == 3
    assert result["signals_found"] > 0


def test_backfill_full_universe_resolves_from_marketlists_all(monkeypatch):
    from core.market import HistoricalBackfill

    class _FrozenDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 6, 10, 0, 0)

    short_history = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0],
            "High": [101.0, 102.0, 103.0, 104.0],
            "Low": [99.0, 100.0, 101.0, 102.0],
            "Close": [100.5, 101.5, 102.5, 103.5],
            "Volume": [1000, 1100, 1200, 1300],
        },
        index=pd.to_datetime(["2026-03-31", "2026-04-01", "2026-04-02", "2026-04-05"]),
    )

    universe_df = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0],
            "High": [101.0, 102.0, 103.0, 104.0],
            "Low": [99.0, 100.0, 101.0, 102.0],
            "Close": [100.5, 101.5, 102.5, 103.5],
            "Volume": [1000, 1100, 1200, 1300],
        },
        index=pd.MultiIndex.from_arrays(
            [
                ["COMI", "COMI", "COMI", "COMI"],
                pd.to_datetime(["2026-03-31", "2026-04-01", "2026-04-02", "2026-04-05"]),
            ],
            names=["Ticker", "Date"],
        ),
    )

    requested_choice = {}
    requested_tickers = {}

    def _get_market_list(choice):
        requested_choice["value"] = choice
        return {"COMI"}

    def _get_universe_data(tickers, *args, **kwargs):
        requested_tickers["value"] = set(tickers)
        return universe_df.copy()

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI"])
    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", lambda *args, **kwargs: short_history.copy())
    monkeypatch.setattr("core.DataManager.DataManager.get_universe_data", _get_universe_data)
    monkeypatch.setattr("core.market.MarketLists.get_market_list", _get_market_list)
    monkeypatch.setattr(DailyScanner, "get_market_signals", _fake_signals_factory(["COMI"]))

    result = HistoricalBackfill.run_backfill(days=3, universe_choice="FULL")

    assert result["status"] == "COMPLETED"
    assert requested_choice["value"] == "ALL"
    assert requested_tickers["value"] == {"COMI"}


def test_backfill_state_records_selected_universe(monkeypatch):
    from core.market import HistoricalBackfill

    class _FrozenDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 6, 10, 0, 0)

    short_history = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0],
            "High": [101.0, 102.0, 103.0, 104.0],
            "Low": [99.0, 100.0, 101.0, 102.0],
            "Close": [100.5, 101.5, 102.5, 103.5],
            "Volume": [1000, 1100, 1200, 1300],
        },
        index=pd.to_datetime(["2026-03-31", "2026-04-01", "2026-04-02", "2026-04-05"]),
    )

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI"])
    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", lambda *args, **kwargs: short_history.copy())
    monkeypatch.setattr(DailyScanner, "get_market_signals", _fake_signals_factory(["COMI"]))

    result = HistoricalBackfill.run_backfill(days=3, universe_choice="EGX70")

    assert result["status"] == "COMPLETED"
    assert HistoricalBackfill.BACKFILL_STATE["universe_choice"] == "EGX70"


def test_manual_backfill_persists_provisioning_state(monkeypatch):
    from core.market import HistoricalBackfill

    TimeUtils.set_simulation(datetime.datetime(2026, 3, 24, 10, 0, 0))

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: ["COMI"])
    monkeypatch.setattr(DailyScanner, "get_market_signals", _fake_signals_factory(["COMI"]))

    result = HistoricalBackfill.run_backfill(days=3, mode="MANUAL")

    assert result["status"] == "COMPLETED"

    row = ProvisioningState.get(ProvisioningState.name == "HISTORICAL_SIGNAL_PROVISIONING")
    assert row.target_trading_days == 3
    assert row.completed_trading_days == 3
    assert row.status == "COMPLETED"
    assert row.mode == "MANUAL"
    assert row.started_at is not None
    assert row.completed_at is not None
    assert row.last_error is None


def test_manual_backfill_warning_persists_provisioning_state(monkeypatch):
    from core.market import HistoricalBackfill

    monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda *args, **kwargs: [])

    result = HistoricalBackfill.run_backfill(days=3, mode="MANUAL")

    assert result["status"] == "COMPLETED_WITH_WARNINGS"

    row = ProvisioningState.get(ProvisioningState.name == "HISTORICAL_SIGNAL_PROVISIONING")
    assert row.target_trading_days == 3
    assert row.completed_trading_days == 0
    assert row.status == "COMPLETED_WITH_WARNINGS"
    assert row.mode == "MANUAL"
    assert row.started_at is not None
    assert row.completed_at is not None
    assert "no tickers" in str(row.last_error).lower()


def test_apply_intraday_entry_prices_prefers_session_price_at_cutoff(monkeypatch):
    from core.market import HistoricalBackfill

    intra = pd.DataFrame(
        {
            "Open": [10.0, 10.2, 10.4],
            "High": [10.1, 10.3, 10.5],
            "Low": [9.9, 10.1, 10.3],
            "Close": [10.0, 10.2, 10.45],
            "Volume": [100, 120, 140],
        },
        index=pd.to_datetime(
            [
                "2026-05-14 10:00:00",
                "2026-05-14 11:30:00",
                "2026-05-14 13:00:00",
            ]
        ),
    )

    monkeypatch.setattr(
        "core.DataManager.DataManager.get_intraday_data",
        lambda ticker, limit=None, refresh_if_stale=True: intra.copy(),
    )

    signals = [{"Ticker": "COMI", "Entry_Price": 9.75, "Price": 9.75, "Score": 8, "Signal_Type": "BUY"}]
    patched = HistoricalBackfill._apply_intraday_entry_prices(
        signals,
        sim_date=datetime.date(2026, 5, 14),
        cutoff_dt=datetime.datetime(2026, 5, 14, 12, 0),
    )

    assert len(patched) == 1
    assert float(patched[0]["Entry_Price"]) == 10.2
    assert float(patched[0]["Price"]) == 10.2


def test_store_signals_for_day_updates_intraday_price_when_score_is_unchanged():
    from core.market import HistoricalBackfill

    Signal.create(
        ticker="COMI",
        date=datetime.date(2026, 5, 14),
        signal_type="BUY",
        price=10.0,
        score=8.0,
        source="BackfillIntraday",
    )

    summary = HistoricalBackfill._store_signals_for_day(
        [
            {
                "Ticker": "COMI",
                "Signal_Type": "BUY",
                "Entry_Price": 10.25,
                "Score": 8.0,
            }
        ],
        datetime.date(2026, 5, 14),
        source="BackfillIntraday",
        include_diagnostics=True,
    )

    updated = Signal.get(
        (Signal.ticker == "COMI")
        & (Signal.date == datetime.date(2026, 5, 14))
        & (Signal.signal_type == "BUY")
        & (Signal.source == "BackfillIntraday")
    )
    assert float(updated.price) == 10.25
    assert int(summary.get("updated", 0)) == 1


def test_apply_intraday_entry_prices_falls_back_to_session_open_from_universe(monkeypatch):
    from core.market import HistoricalBackfill

    monkeypatch.setattr(
        "core.DataManager.DataManager.get_intraday_data",
        lambda ticker, limit=None, refresh_if_stale=True: None,
    )

    universe_df = pd.DataFrame(
        {
            "Open": [10.4],
            "High": [10.9],
            "Low": [10.1],
            "Close": [10.7],
            "Volume": [1000],
        },
        index=pd.MultiIndex.from_arrays(
            [
                ["COMI"],
                pd.to_datetime(["2026-05-14T00:00:00"]),
            ],
            names=["Ticker", "Date"],
        ),
    )

    signals = [{"Ticker": "COMI", "Entry_Price": 10.0, "Price": 10.0, "Score": 8, "Signal_Type": "BUY"}]
    patched = HistoricalBackfill._apply_intraday_entry_prices(
        signals,
        sim_date=datetime.date(2026, 5, 14),
        cutoff_dt=datetime.datetime(2026, 5, 14, 12, 0),
        universe_df=universe_df,
    )

    assert len(patched) == 1
    assert float(patched[0]["Entry_Price"]) == 10.4
    assert float(patched[0]["Price"]) == 10.4


def test_intraday_checkpoints_for_day_uses_15_minute_grid(monkeypatch):
    from core.market import HistoricalBackfill

    monkeypatch.setattr(settings, "_active_market_start", lambda: "1000")
    monkeypatch.setattr(settings, "_active_market_end", lambda: "1030")
    monkeypatch.setattr(
        settings,
        "HISTORICAL_BACKFILL_INTRADAY_INTERVAL_MINS",
        15,
        raising=False,
    )

    points = HistoricalBackfill._intraday_checkpoints_for_day(datetime.date(2026, 5, 14))

    assert [p.strftime("%H:%M") for p in points] == ["10:00", "10:15", "10:30"]


def test_intraday_checkpoints_for_day_appends_market_close_when_off_grid(monkeypatch):
    from core.market import HistoricalBackfill

    monkeypatch.setattr(settings, "_active_market_start", lambda: "1000")
    monkeypatch.setattr(settings, "_active_market_end", lambda: "1032")
    monkeypatch.setattr(
        settings,
        "HISTORICAL_BACKFILL_INTRADAY_INTERVAL_MINS",
        15,
        raising=False,
    )

    points = HistoricalBackfill._intraday_checkpoints_for_day(datetime.date(2026, 5, 14))

    assert [p.strftime("%H:%M") for p in points] == ["10:00", "10:15", "10:30", "10:32"]


def test_store_intraday_checkpoint_snapshot_updates_existing_checkpoint_row():
    from core.market import HistoricalBackfill

    session_date = datetime.date(2026, 5, 14)
    checkpoint_at = datetime.datetime(2026, 5, 14, 10, 15)

    first = HistoricalBackfill._store_intraday_checkpoint_snapshot(
        [
            {
                "Ticker": "COMI",
                "Signal_Type": "BUY",
                "Entry_Price": 10.0,
                "Score": 7.0,
            }
        ],
        session_date=session_date,
        checkpoint_at=checkpoint_at,
        universe_choice="EGX30",
    )
    second = HistoricalBackfill._store_intraday_checkpoint_snapshot(
        [
            {
                "Ticker": "COMI",
                "Signal_Type": "BUY",
                "Entry_Price": 10.4,
                "Score": 8.5,
            }
        ],
        session_date=session_date,
        checkpoint_at=checkpoint_at,
        universe_choice="EGX30",
    )

    row = BackfillIntradayCheckpoint.get(
        (BackfillIntradayCheckpoint.session_date == session_date)
        & (BackfillIntradayCheckpoint.checkpoint_at == checkpoint_at)
        & (BackfillIntradayCheckpoint.ticker == "COMI")
        & (BackfillIntradayCheckpoint.signal_type == "BUY")
        & (BackfillIntradayCheckpoint.source == "BackfillIntraday")
    )

    assert int(first["inserted"]) == 1
    assert int(second["updated"]) == 1
    assert float(row.price) == 10.4
    assert float(row.score) == 8.5


def test_intraday_checkpoint_rows_capture_multiple_checkpoints_while_signal_table_stays_deduped():
    from core.market import HistoricalBackfill

    session_date = datetime.date(2026, 5, 14)
    payload_1015 = [{"Ticker": "COMI", "Signal_Type": "BUY", "Entry_Price": 10.1, "Score": 7.0}]
    payload_1030 = [{"Ticker": "COMI", "Signal_Type": "BUY", "Entry_Price": 10.3, "Score": 7.2}]

    HistoricalBackfill._store_signals_for_day(
        payload_1015,
        session_date,
        source="BackfillIntraday",
    )
    HistoricalBackfill._store_signals_for_day(
        payload_1030,
        session_date,
        source="BackfillIntraday",
    )

    HistoricalBackfill._store_intraday_checkpoint_snapshot(
        payload_1015,
        session_date=session_date,
        checkpoint_at=datetime.datetime(2026, 5, 14, 10, 15),
        universe_choice="EGX30",
    )
    HistoricalBackfill._store_intraday_checkpoint_snapshot(
        payload_1030,
        session_date=session_date,
        checkpoint_at=datetime.datetime(2026, 5, 14, 10, 30),
        universe_choice="EGX30",
    )

    signal_rows = Signal.select().where(
        (Signal.ticker == "COMI")
        & (Signal.date == session_date)
        & (Signal.signal_type == "BUY")
        & (Signal.source == "BackfillIntraday")
    )
    checkpoint_rows = BackfillIntradayCheckpoint.select().where(
        (BackfillIntradayCheckpoint.session_date == session_date)
        & (BackfillIntradayCheckpoint.ticker == "COMI")
        & (BackfillIntradayCheckpoint.signal_type == "BUY")
        & (BackfillIntradayCheckpoint.source == "BackfillIntraday")
    )

    assert signal_rows.count() == 1
    assert checkpoint_rows.count() == 2
