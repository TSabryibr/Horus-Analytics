"""
SCANNER & DATA ENDPOINT TESTS
==============================
Tests for routes/scanner.py and routes/data.py - scanner control,
signal history, data access, sync status.
"""

from core.settings import settings
from core.exclusions import get_all_exclusions
import pytest
import datetime
import pandas as pd
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api import app
from database import Signal, Trade, ScannerStrategyProfile

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# SCANNER ENDPOINTS
# =============================================================================

def test_svartalfheim_process_ticker_uses_history_only(monkeypatch):
    from core.analyzers import Svartalfheim

    calls = []
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    df = pd.DataFrame(
        {
            "Open": [10.0] * 30,
            "High": [11.0] * 30,
            "Low": [9.0] * 30,
            "Close": [10.0] * 30,
            "Volume": [100000] * 30,
        },
        index=dates,
    )

    def fake_get_stock_data(ticker, include_live=True, **kwargs):
        calls.append({"ticker": ticker, "include_live": include_live})
        return df.copy()

    monkeypatch.setattr(Svartalfheim.DataManager.DataManager, "get_stock_data", fake_get_stock_data)

    Svartalfheim._process_ticker("COMI")

    assert calls == [{"ticker": "COMI", "include_live": False}]


def test_vanaheim_async_hunt_whales_uses_history_only(monkeypatch):
    from core.analyzers import Vanaheim

    calls = []
    dates = pd.date_range("2026-01-01", periods=40, freq="D")
    df = pd.DataFrame(
        {
            "Open": [10.0] * 40,
            "High": [11.0] * 40,
            "Low": [9.0] * 40,
            "Close": [10.0] * 40,
            "Volume": [200000] * 40,
        },
        index=dates,
    )

    def fake_get_stock_data(ticker, include_live=True, **kwargs):
        calls.append({"ticker": ticker, "include_live": include_live})
        return df.copy()

    monkeypatch.setattr(Vanaheim.MarketLists, "get_market_list", lambda _: ["COMI"])
    monkeypatch.setattr(Vanaheim.DataManager.DataManager, "get_stock_data", fake_get_stock_data)
    monkeypatch.setattr(Vanaheim.MarketLists, "get_sector", lambda ticker: "Banks")

    result = asyncio.run(Vanaheim.async_hunt_whales())

    assert result["status"] == "success"
    assert calls == [{"ticker": "COMI", "include_live": False}]


def test_maybe_sync_intraday_skips_ingest_when_intraday_fresh(monkeypatch):
    from core import DailyScanner

    monkeypatch.setattr("core.DailyScanner.settings.is_market_open", lambda: True)
    monkeypatch.setattr("core.DailyScanner.TimeUtils.now", lambda: datetime.datetime(2026, 4, 16, 11, 30))
    monkeypatch.setattr("core.DailyScanner._last_intraday_sync_ts", None)
    monkeypatch.setattr(
        "core.DailyScanner.evaluate_freshness",
        lambda realm, run_date, scan_type="DAILY": {
            "overall_ok": True,
            "intraday": {"ok": True, "age_mins": 1.0, "kpis": {"live_ratio": 0.9}},
        },
    )

    ingest_mock = MagicMock()
    monkeypatch.setattr("data_engine.ingest_intraday.ingest_intraday", ingest_mock)

    DailyScanner._maybe_sync_intraday()

    ingest_mock.assert_not_called()


def test_maybe_sync_intraday_refreshes_when_live_bar_older_than_sync_interval(monkeypatch):
    from core import DailyScanner

    monkeypatch.setattr("core.DailyScanner.settings.is_market_open", lambda: True)
    monkeypatch.setattr("core.DailyScanner.TimeUtils.now", lambda: datetime.datetime(2026, 4, 16, 11, 30))
    monkeypatch.setattr("core.DailyScanner._last_intraday_sync_ts", None)
    monkeypatch.setenv("INTRADAY_SYNC_MINUTES", "5")
    monkeypatch.setattr(
        "core.DailyScanner.evaluate_freshness",
        lambda realm, run_date, scan_type="DAILY": {
            "overall_ok": True,
            "intraday": {"ok": True, "age_mins": 6.0, "kpis": {"live_ratio": 0.9}},
        },
    )

    ingest_mock = MagicMock()
    monkeypatch.setattr("data_engine.ingest_intraday.ingest_intraday", ingest_mock)

    DailyScanner._maybe_sync_intraday()

    ingest_mock.assert_called_once()


def test_daily_scanner_pre_close_uses_live_merged_universe(monkeypatch):
    from core import DailyScanner

    calls = []

    monkeypatch.setattr("core.DailyScanner.DataManager.list_tickers", lambda: ["COMI"])
    monkeypatch.setattr("core.DailyScanner.get_excluded_tickers_upper", lambda: set())

    def fake_get_universe_data(tickers, include_live=False):
        calls.append({"tickers": list(tickers), "include_live": include_live})
        return pd.DataFrame()

    monkeypatch.setattr("core.DailyScanner.DataManager.get_universe_data", fake_get_universe_data)

    signals, monitored, breadth, regime = DailyScanner.get_market_signals(
        index_choice="EGX30",
        is_intraday=False,
        is_pre_close=True,
    )

    assert signals == []
    assert monitored == []
    assert breadth == 0.0
    assert regime == "UNKNOWN"
    assert calls == [{"tickers": ["COMI"], "include_live": True}]


def test_daily_scanner_pre_close_excludes_tickers_without_today_live_bar(monkeypatch):
    from core import DailyScanner

    index = pd.MultiIndex.from_tuples(
        [
            ("COMI", pd.Timestamp("2026-06-01")),
            ("FWRY", pd.Timestamp("2026-05-25")),
        ],
        names=["Ticker", "Row"],
    )
    universe_df = pd.DataFrame(
        {
            "Date": [pd.Timestamp("2026-06-01"), pd.Timestamp("2026-05-25")],
            "Open": [10.0, 20.0],
            "High": [11.0, 21.0],
            "Low": [9.8, 19.8],
            "Close": [10.8, 20.8],
            "Volume": [100000.0, 100000.0],
            "EMA9": [10.0, 20.0],
            "RSI": [58.0, 58.0],
            "ATR": [0.4, 0.4],
            "Rel_Vol": [2.0, 2.0],
            "Move": [3.0, 3.0],
            "Turnover": [2_000_000.0, 2_000_000.0],
            "Avg_Turnover": [2_000_000.0, 2_000_000.0],
            "Res_20": [10.5, 20.5],
        },
        index=index,
    )

    monkeypatch.setattr("core.DailyScanner.TimeUtils.now", lambda: datetime.datetime(2026, 6, 1, 14, 10))
    monkeypatch.setattr("core.DailyScanner.TimeUtils.today", lambda: datetime.date(2026, 6, 1))
    monkeypatch.setattr("core.DailyScanner.settings.LOOKBACK", 20, raising=False)
    monkeypatch.setattr("core.DailyScanner.get_trade_permission", lambda ticker: {"allowed": True})
    monkeypatch.setattr("core.DailyScanner.SignalEngine.add_indicators_universe", lambda frame, lookback: frame)
    monkeypatch.setattr(
        "core.DailyScanner.SignalEngine.vectorize_signals",
        lambda latest_rows, settings, resistance_col: pd.Series(True, index=latest_rows.index),
    )
    monkeypatch.setattr(
        "core.DailyScanner.SignalEngine.check_buy_signal",
        lambda last, settings, resistance_col, profile=None: {
            "Signal_Type": "BUY",
            "Signal_Setup": "BREAKOUT",
            "Entry_Price": float(last["Close"]),
            "Stop_Loss": float(last["Close"]) * 0.97,
            "Target_Price": float(last["Close"]) * 1.05,
            "Score": 8,
            "RSI": float(last["RSI"]),
            "Volume_Spike": float(last["Rel_Vol"]),
        },
    )
    monkeypatch.setattr("core.DailyScanner.SignalEngine.check_trickster_signal", lambda *args, **kwargs: None)
    monkeypatch.setattr("core.DailyScanner.MarketLists.is_egx70_ticker", lambda ticker: False)
    monkeypatch.setattr("core.market.SectorAnalysis.get_sector", lambda ticker: "Banks")
    monkeypatch.setattr("core.DailyScanner.Vanaheim.hunt_whales", lambda universe=None: {"candidates": []})
    monkeypatch.setattr("core.DailyScanner.Svartalfheim.hunt_traps", lambda universe=None: {"bull_traps": [], "bear_traps": []})
    monkeypatch.setattr("core.DailyScanner.calculate_sector_relative_strength", lambda *args, **kwargs: {"Banks": 0.1})
    monkeypatch.setattr(
        "core.DailyScanner.route_candidate",
        lambda **kwargs: {
            "allowed": True,
            "route_profile": "EGX30_TREND_PROFILE",
            "liquidity_tier": "LIQUID",
            "sector_rs_14": 0.1,
            "routing_reason": "egx30_trend",
        },
    )
    monkeypatch.setattr("core.DailyScanner.audit.log_event", MagicMock())

    signals, monitored, breadth, regime = DailyScanner.get_market_signals(
        index_choice="EGX30",
        is_pre_close=True,
        universe_df=universe_df,
    )

    assert [signal["Ticker"] for signal in signals] == ["COMI"]
    assert {row["Ticker"] for row in monitored} == {"COMI"}
    assert signals[0]["Confirmation"] == "PRE-CLOSE"
    assert signals[0]["Preview_Mode"] == "DAILY_RULES_LIVE_CLOSE"
    assert signals[0]["Preview_Source"] == "PRE_CLOSE_DAILY_PREVIEW"
    assert signals[0]["Preview_Close"] == 10.8
    assert signals[0]["Preview_Volume"] == 100000.0


def test_daily_scanner_retries_ticker_listing_after_cold_empty_cache(monkeypatch):
    from core import DailyScanner

    calls = []
    clear_calls = []
    ticker_responses = iter([[], ["COMI"]])

    monkeypatch.setattr("core.DailyScanner.DataManager.list_tickers", lambda: next(ticker_responses))
    monkeypatch.setattr("data_engine.api.clear_data_cache", lambda: clear_calls.append(True))
    monkeypatch.setattr("core.DailyScanner.get_excluded_tickers_upper", lambda: set())

    def fake_get_universe_data(tickers, include_live=False):
        calls.append({"tickers": list(tickers), "include_live": include_live})
        return pd.DataFrame()

    monkeypatch.setattr("core.DailyScanner.DataManager.get_universe_data", fake_get_universe_data)

    signals, monitored, breadth, regime = DailyScanner.get_market_signals(
        index_choice="EGX30",
        is_intraday=True,
    )

    assert signals == []
    assert monitored == []
    assert breadth == 0.0
    assert regime == "UNKNOWN"
    assert clear_calls == [True]
    assert calls == [{"tickers": ["COMI"], "include_live": True}]

class TestScannerEndpoints:
    """Tests for scanner control and history endpoints."""

    def test_start_scanner(self):
        """POST /api/scanner/start should start a background scan."""
        response = client.post("/api/v1/scanner/start", params={
            "index": "EGX30",
            "intraday": False,
            "notify": False,
        })
        assert response.status_code == 200
        data = response.json()
        # Either started or already running
        assert "message" in data
        assert "started" in data

    def test_start_scanner_rejects_if_running(self, monkeypatch):
        """POST /api/scanner/start should reject if scan already running."""
        monkeypatch.setattr(
            "routes.scanner.SCAN_STATE",
            {"status": "RUNNING", "progress": 50, "total": 100,
             "current_ticker": "COMI", "result": None, "error": None},
        )
        response = client.post("/api/v1/scanner/start")
        assert response.status_code == 200
        data = response.json()
        assert data["started"] is False

    def test_control_scan_daily(self):
        """POST /api/control/scan should trigger a daily scan."""
        response = client.post("/api/v1/control/scan", json={
            "type": "DAILY",
            "notify": False,
            "index": "EGX30",
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_signal_history(self, monkeypatch):
        """GET /api/scanner/history should return recent signals."""
        monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: set())
        # Seed a signal
        Signal.create(ticker="COMI", signal_type="BREAKOUT", price=50.0, score=8, source="Test")

        response = client.get("/api/v1/scanner/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["ticker"] == "COMI"

    def test_signal_history_excludes_blacklisted(self, monkeypatch):
        Signal.create(ticker="COMI", signal_type="BREAKOUT", price=50.0, score=8, source="Test")
        Signal.create(ticker="FWRY", signal_type="BREAKOUT", price=20.0, score=7, source="Test")
        monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: {"comi"})

        response = client.get("/api/v1/scanner/history")
        assert response.status_code == 200
        data = response.json()
        tickers = {row["ticker"] for row in data}
        assert "COMI" not in tickers
        assert "FWRY" in tickers

    def test_weekly_report_empty(self):
        """GET /api/reports/weekly should return empty trades list when no trades."""
        response = client.get("/api/v1/reports/weekly")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["trades"], list)

    def test_weekly_report_with_trades(self, monkeypatch):
        """GET /api/reports/weekly should return trades when they exist."""
        monkeypatch.setattr("routes.analysis_reports.get_all_exclusions", lambda: set(), raising=False)
        from database import Portfolio
        p = Portfolio.select().first()
        Trade.create(
            ticker="COMI", shares=100, entry_price=10.0, exit_price=11.5,
            entry_date="2025-01-01", exit_date="2025-01-05",
            pnl=150.0, pnl_pct=15.0, portfolio=p,
        )
        response = client.get("/api/v1/reports/weekly")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) >= 1

    def test_background_scan_task_broadcast_path_uses_mode_label(self, monkeypatch):
        from io import BytesIO
        from routes.scanner import background_scan_task, SCAN_STATE

        signal = {
            "Ticker": "COMI",
            "Signal_Type": "BUY",
            "Entry_Price": 102.4,
            "Stop_Loss": 99.0,
            "Target_Price": 108.0,
            "Target_Price_2": 112.0,
            "Score": 8,
            "RSI": 63.2,
            "Volume_x": 2.1,
        }

        monkeypatch.setattr(
            "routes.scanner.DailyScanner.get_market_signals",
            lambda index_choice, is_intraday, progress_callback=None: ([signal], [], {"value": 0}, "BULLISH"),
        )
        monkeypatch.setattr("routes.scanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr("routes.scanner.AlertManager.filter_new_signals", lambda signals, scan_label: list(signals))

        broadcast_alert = MagicMock()
        broadcast_image = MagicMock()
        monkeypatch.setattr("routes.scanner.AlertManager.broadcast_alert", broadcast_alert)
        monkeypatch.setattr("routes.scanner.AlertManager.broadcast_image", broadcast_image)
        monkeypatch.setattr("routes.scanner.TelegramBot_Alerts.format_signal_alert", lambda signals: "summary")

        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_INTRADAY", True)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_DAILY", True)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_HORUS_EYE", False)
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", False)

        monkeypatch.setattr("routes.scanner.Signal.get_or_none", lambda *args, **kwargs: None)
        monkeypatch.setattr("routes.scanner.Signal.create", lambda **kwargs: None)
        monkeypatch.setattr("routes.scanner.TimeUtils.today", lambda: datetime.date(2026, 3, 9))
        monkeypatch.setattr(
            "core.ReportGenerator.create_horus_signal_card",
            lambda **kwargs: BytesIO(b"fake-image"),
        )

        background_scan_task(index="EGX30", intraday=True, notify=False)

        assert SCAN_STATE["status"] == "COMPLETED"
        assert broadcast_alert.call_count >= 2
        assert broadcast_image.call_count >= 1

    def test_background_scan_task_respects_main_channel_none_policy_even_when_notify_requested(self, monkeypatch):
        from io import BytesIO
        from routes.scanner import background_scan_task, SCAN_STATE

        signal = {
            "Ticker": "COMI",
            "Signal_Type": "BUY",
            "Entry_Price": 102.4,
            "Stop_Loss": 99.0,
            "Target_Price": 108.0,
            "Target_Price_2": 112.0,
            "Score": 8,
            "RSI": 63.2,
            "Volume_x": 2.1,
        }

        monkeypatch.setattr(
            "routes.scanner.DailyScanner.get_market_signals",
            lambda index_choice, is_intraday, progress_callback=None: ([signal], [], {"value": 0}, "BULLISH"),
        )
        monkeypatch.setattr("routes.scanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr("routes.scanner.AlertManager.filter_new_signals", lambda signals, scan_label: list(signals))

        broadcast_alert = MagicMock()
        broadcast_image = MagicMock()
        monkeypatch.setattr("routes.scanner.AlertManager.broadcast_alert", broadcast_alert)
        monkeypatch.setattr("routes.scanner.AlertManager.broadcast_image", broadcast_image)
        monkeypatch.setattr("routes.scanner.TelegramBot_Alerts.format_signal_alert", lambda signals: "summary")

        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_INTRADAY", True)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "none", raising=False)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_HORUS_EYE", False)
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", False)

        monkeypatch.setattr("routes.scanner.Signal.get_or_none", lambda *args, **kwargs: None)
        monkeypatch.setattr("routes.scanner.Signal.create", lambda **kwargs: None)
        monkeypatch.setattr("routes.scanner.TimeUtils.today", lambda: datetime.date(2026, 3, 9))
        monkeypatch.setattr(
            "core.ReportGenerator.create_horus_signal_card",
            lambda **kwargs: BytesIO(b"fake-image"),
        )

        background_scan_task(index="EGX30", intraday=True, notify=True)

        assert SCAN_STATE["status"] == "COMPLETED"
        broadcast_alert.assert_not_called()
        broadcast_image.assert_not_called()

    def test_background_scan_task_routes_intraday_auto_trade_via_signal_executor(self, monkeypatch):
        from routes.scanner import background_scan_task

        signal = {
            "Ticker": "COMI",
            "Signal_Type": "BUY",
            "Entry_Price": 102.4,
            "Stop_Loss": 99.0,
            "Target_Price": 108.0,
            "Score": 8,
        }

        monkeypatch.setattr(
            "routes.scanner.DailyScanner.get_market_signals",
            lambda index_choice, is_intraday, progress_callback=None: ([signal], [], {"value": 0}, "BULLISH"),
        )
        monkeypatch.setattr("routes.scanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_INTRADAY", False)
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", True)
        monkeypatch.setattr("routes.scanner.Signal.get_or_none", lambda *args, **kwargs: None)
        monkeypatch.setattr("routes.scanner.Signal.create", lambda **kwargs: None)

        persist_mock = MagicMock(return_value={"status": "completed", "run": {"id": 17}})
        execute_mock = MagicMock(return_value={"status": "completed", "summary": {}})
        monkeypatch.setattr("routes.scanner._persist_manual_scan_run", persist_mock)
        monkeypatch.setattr("routes.scanner.SignalExecutor.execute_run", execute_mock)

        background_scan_task(index="EGX30", intraday=True, notify=False)

        persist_mock.assert_called_once()
        execute_mock.assert_called_once_with(17)

    def test_background_scan_task_daily_auto_trade_uses_deduped_signal_executor_path(self, monkeypatch):
        from routes.scanner import background_scan_task

        duplicate_signal = {
            "Ticker": "ARVA",
            "Signal_Type": "BUY",
            "Entry_Price": 10.08,
            "Stop_Loss": 9.2384,
            "Target_Price": 11.2021,
            "Score": 8,
        }
        new_signal = {
            "Ticker": "COMI",
            "Signal_Type": "BUY",
            "Entry_Price": 102.4,
            "Stop_Loss": 99.0,
            "Target_Price": 108.0,
            "Score": 8,
        }

        monkeypatch.setattr(
            "routes.scanner.DailyScanner.get_market_signals",
            lambda index_choice, is_intraday, progress_callback=None: ([duplicate_signal, new_signal], [], {"value": 0}, "BULLISH"),
        )
        monkeypatch.setattr("routes.scanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_DAILY", True)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_HORUS_EYE", False)
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", True)
        monkeypatch.setattr("routes.scanner.AlertManager.filter_new_signals", lambda signals, scan_label: [new_signal])
        monkeypatch.setattr("routes.scanner.AlertManager.broadcast_alert", lambda *args, **kwargs: {"ok": True})
        monkeypatch.setattr("routes.scanner.AlertManager.broadcast_image", lambda *args, **kwargs: {"ok": True})
        monkeypatch.setattr("routes.scanner.TelegramBot_Alerts.format_signal_alert", lambda signals: "summary")
        monkeypatch.setattr("routes.scanner.Signal.get_or_none", lambda *args, **kwargs: None)
        monkeypatch.setattr("routes.scanner.Signal.create", lambda **kwargs: None)

        persist_mock = MagicMock(return_value={"status": "completed", "run": {"id": 33}})
        execute_mock = MagicMock(return_value={"status": "completed", "summary": {"pending": 1}})
        monkeypatch.setattr("routes.scanner._persist_manual_scan_run", persist_mock)
        monkeypatch.setattr("routes.scanner.SignalExecutor.execute_run", execute_mock)

        background_scan_task(index="EGX30", intraday=False, notify=False)

        persist_mock.assert_called_once()
        passed_signals = persist_mock.call_args.kwargs["signals"]
        assert [signal["Ticker"] for signal in passed_signals] == ["COMI"]
        execute_mock.assert_called_once_with(33)

    def test_background_scan_task_preserves_microstructure_metadata(self, monkeypatch):
        from routes.scanner import background_scan_task, SCAN_STATE

        signal = {
            "Ticker": "COMI",
            "Signal_Type": "BUY",
            "Signal_Setup": "BREAKOUT",
            "Entry_Price": 102.4,
            "Stop_Loss": 99.0,
            "Target_Price": 108.0,
            "Target_Price_2": 112.0,
            "Score": 8,
            "RSI": 63.2,
            "Volume_x": 2.6,
            "VSA_Valid": True,
            "Volume_Mult_20": 2.6,
            "Route_Profile": "EGX30_TREND_PROFILE",
            "Liquidity_Tier": "LIQUID",
            "Sector_RS_14": 0.12,
            "Routing_Reason": "egx30_trend",
            "Trap_Risk": None,
            "Expected_Slippage_Pct": None,
            "Execution_Cap_Shares": None,
        }

        monkeypatch.setattr(
            "routes.scanner.DailyScanner.get_market_signals",
            lambda index_choice, is_intraday, progress_callback=None: ([signal], [], {"value": 0}, "BULLISH"),
        )
        monkeypatch.setattr("routes.scanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_DAILY", False)
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", False)

        background_scan_task(index="EGX30", intraday=False, notify=False)

        assert SCAN_STATE["status"] == "COMPLETED"
        result_signal = SCAN_STATE["result"]["signals"][0]
        assert result_signal["Route_Profile"] == "EGX30_TREND_PROFILE"
        assert result_signal["Liquidity_Tier"] == "LIQUID"
        assert result_signal["Sector_RS_14"] == 0.12
        assert result_signal["Routing_Reason"] == "egx30_trend"
        assert result_signal["VSA_Valid"] is True

    def test_background_scan_task_exposes_whale_trap_diagnostics(self, monkeypatch):
        from routes.scanner import background_scan_task, SCAN_STATE

        signals = [
            {
                "Ticker": "COMI",
                "Signal_Type": "BUY",
                "Entry_Price": 102.4,
                "Stop_Loss": 99.0,
                "Target_Price": 108.0,
                "Score": 8,
                "Whale_Alignment": "SUPPORTIVE",
                "Trap_Risk_Band": "LOW",
                "Trap_Risk_Reason": "low_risk_alignment",
                "Enforcement_State": "ALLOW",
                "Enforcement_Reason": "not_enforced",
                "Enforcement_Profile": "EGX30_BALANCED",
                "Route_Profile": "EGX30_TREND_PROFILE",
            },
            {
                "Ticker": "FWRY",
                "Signal_Type": "BUY",
                "Entry_Price": 20.0,
                "Stop_Loss": 18.5,
                "Target_Price": 23.0,
                "Score": 7,
                "Whale_Alignment": "CONFLICT",
                "Trap_Risk_Band": "SEVERE",
                "Trap_Risk_Reason": "distribution_against_breakout",
                "Enforcement_State": "BLOCK_EXECUTION",
                "Enforcement_Reason": "severe_trap_risk",
                "Enforcement_Profile": "EGX70_STRICT",
                "Route_Profile": "EGX70_TACTICAL_PROFILE",
            },
        ]

        monkeypatch.setattr(
            "routes.scanner.DailyScanner.get_market_signals",
            lambda index_choice, is_intraday, progress_callback=None: (signals, [], 62.5, "BULLISH"),
        )
        monkeypatch.setattr("routes.scanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_DAILY", False)
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", False)
        monkeypatch.setattr("routes.scanner.Signal.get_or_none", lambda *args, **kwargs: None)
        monkeypatch.setattr("routes.scanner.Signal.create", lambda **kwargs: None)

        background_scan_task(index="EGX30", intraday=False, notify=False)

        assert SCAN_STATE["status"] == "COMPLETED"
        diagnostics = SCAN_STATE["result"]["whale_trap_diagnostics"]
        assert diagnostics["rollout_mode"] == "shadow"
        assert diagnostics["supportive_whale_alignments"] == 1
        assert diagnostics["whale_conflicts"] == 1
        assert diagnostics["high_trap_risk_count"] == 0
        assert diagnostics["severe_trap_risk_count"] == 1
        assert diagnostics["top_trap_risk_reasons"] == {"distribution_against_breakout": 1}
        enforcement = SCAN_STATE["result"]["enforcement_diagnostics"]
        assert enforcement["rollout_mode"] == "visible_but_blocked"
        assert enforcement["allow_count"] == 1
        assert enforcement["watch_only_count"] == 0
        assert enforcement["block_count"] == 1
        assert enforcement["counts_by_reason"] == {"severe_trap_risk": 1}
        calibration = SCAN_STATE["result"]["calibration_diagnostics"]
        assert calibration["rollout_mode"] == "compare_only"
        assert calibration["market_segments"]["EGX30"]["active_enforcement_profile"] == "EGX30_GUARDED"
        assert calibration["market_segments"]["EGX30"]["rollback_profile"] == "EGX30_BALANCED"
        assert calibration["market_segments"]["EGX70"]["active_enforcement_profile"] == "EGX70_HARDENED"
        assert calibration["market_segments"]["EGX70"]["rollback_profile"] == "EGX70_STRICT"
        assert calibration["market_segments"]["EGX70"]["calibration_summary"]["candidates"]["EGX70_STRICT"]["deltas"]["block_delta"] == 0

    def test_background_scan_task_runs_selected_pine_scanner_profile(self, monkeypatch):
        from routes.scanner import background_scan_task, SCAN_STATE

        profile = ScannerStrategyProfile.create(
            profile_name="EGX Pine Scanner",
            source_type="PINE",
            script_source="""
//@version=5
strategy("Fast Slow", overlay=true)
fast = ta.sma(close, 2)
slow = ta.sma(close, 3)
if ta.crossover(fast, slow)
    strategy.entry("Long", strategy.long)
if ta.crossunder(fast, slow)
    strategy.close("Long")
""",
            script_hash="pine-scanner-profile-hash",
            market="EGX30",
            timeframe="1D",
            profile_state="DRAFT",
            backtest_summary_json='{"max_drawdown": 6.4, "total_return": 18.5, "trade_count": 37, "win_rate": 57.1, "walk_forward_pass": true, "oos_trade_count": 12, "commission_pct": 0.05, "slippage_pct": 0.1, "promotion_artifacts": {"artifact_hash": "pine-scanner-artifact"}}',
            compatibility_summary_json='{"compatibility_score": 92.0, "readiness": "READY", "messages": ["Uses supported ta.sma crossover logic", "No unsupported Pine constructs detected"]}',
            ranking_summary_json='{"alignment_score": 61.0, "combined_score": 74.5, "performance_score": 80.0, "recommended": true}',
            ready_at=datetime.datetime(2026, 3, 29, 9, 20),
            activated_at=datetime.datetime(2026, 3, 30, 9, 45),
            activation_count=2,
            activation_history_json='[{"event_type":"ACTIVATED","activated_at":"2026-03-30T09:45:00","previous_active_profile_name":"Legacy Pine"}]',
        )

        dates = pd.date_range("2025-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "Open": [10.0, 10.0, 9.0, 10.0, 12.0],
                "High": [10.2, 10.2, 9.2, 10.2, 12.2],
                "Low": [9.8, 9.8, 8.8, 9.8, 11.8],
                "Close": [10.0, 10.0, 9.0, 10.0, 12.0],
                "Volume": [1000, 1000, 1000, 1000, 1400],
            },
            index=dates,
        )
        df.index.name = "Date"

        def _unexpected_native_scanner(*args, **kwargs):
            raise AssertionError("Native DailyScanner path should not run for Pine profile scans")

        monkeypatch.setattr("routes.scanner.DailyScanner.get_market_signals", _unexpected_native_scanner)
        monkeypatch.setattr("routes.scanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_DAILY", False)
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", False)
        monkeypatch.setattr("core.market.MarketLists.get_market_list", lambda choice: {"COMI"})
        monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", lambda ticker, include_live=False: df.copy())
        monkeypatch.setattr("routes.scanner.Signal.get_or_none", lambda *args, **kwargs: None)
        monkeypatch.setattr("routes.scanner.Signal.create", lambda **kwargs: None)

        background_scan_task(index="ALL", intraday=False, notify=False, profile_id=profile.id)

        assert SCAN_STATE["status"] == "COMPLETED"
        assert SCAN_STATE["result"]["strategy_profile"]["source_type"] == "PINE"
        assert SCAN_STATE["result"]["strategy_profile"]["profile_name"] == "EGX Pine Scanner"
        assert SCAN_STATE["result"]["strategy_profile"]["ready_at"] == "2026-03-29T09:20:00"
        assert SCAN_STATE["result"]["strategy_profile"]["activated_at"] == "2026-03-30T09:45:00"
        assert SCAN_STATE["result"]["strategy_profile"]["activation_count"] == 2
        assert SCAN_STATE["result"]["strategy_profile"]["activation_history"][0]["previous_active_profile_name"] == "Legacy Pine"
        assert SCAN_STATE["result"]["strategy_profile"]["backtest_summary"]["total_return"] == 18.5
        assert SCAN_STATE["result"]["strategy_profile"]["backtest_summary"]["trade_count"] == 37
        assert SCAN_STATE["result"]["strategy_profile"]["compatibility_summary"]["readiness"] == "READY"
        assert SCAN_STATE["result"]["strategy_profile"]["compatibility_summary"]["compatibility_score"] == 92.0
        assert SCAN_STATE["result"]["strategy_profile"]["compatibility_summary"]["messages"][0] == "Uses supported ta.sma crossover logic"
        assert SCAN_STATE["result"]["strategy_profile"]["ranking_summary"]["combined_score"] == 74.5
        assert SCAN_STATE["result"]["strategy_profile"]["ranking_summary"]["recommended"] is True
        assert SCAN_STATE["result"]["strategy_profile"]["promotion_summary"]["profile_state"] == "READY"
        assert SCAN_STATE["result"]["strategy_profile"]["promotion_summary"]["thresholds"]["compatibility_score"] == 70.0
        assert SCAN_STATE["result"]["strategy_profile"]["promotion_summary"]["actuals"]["combined_score"] == 74.5
        assert SCAN_STATE["result"]["signals_count"] == 1
        assert SCAN_STATE["result"]["signals"][0]["Ticker"] == "COMI"
        assert SCAN_STATE["result"]["signals"][0]["Routing_Reason"] == "pine_profile_signal"

    def test_background_scan_task_runs_selected_price_action_profile(self, monkeypatch):
        from routes.scanner import background_scan_task, SCAN_STATE

        profile = ScannerStrategyProfile.create(
            profile_name="EGX Price Action Scanner",
            source_type="PRICE_ACTION",
            script_source='{"strategy_id":"ascending_triangle_breakout","strategy_name":"Ascending Triangle Breakout","family":"SWING"}',
            script_hash="price-action-profile-hash",
            market="EGX30",
            timeframe="1D",
            profile_state="ACTIVE",
            backtest_summary_json='{"max_drawdown": 4.0, "total_return": 12.5, "trade_count": 6, "win_rate": 66.7}',
            compatibility_summary_json='{"compatibility_score": 88.0, "readiness": "READY", "messages": ["Daily EGX OHLCV backtest completed without intraday dependency."]}',
            ranking_summary_json='{"alignment_score": 80.0, "combined_score": 81.5, "performance_score": 82.0, "recommended": true}',
            ready_at=datetime.datetime(2026, 4, 28, 9, 20),
            activated_at=datetime.datetime(2026, 4, 28, 9, 45),
            activation_count=1,
            activation_history_json='[{"event_type":"ACTIVATED","activated_at":"2026-04-28T09:45:00","previous_active_profile_name":"Legacy Core"}]',
            import_rule_spec_json='{"strategy_id":"ascending_triangle_breakout"}',
        )

        dates = pd.date_range("2025-01-01", periods=9, freq="D")
        df = pd.DataFrame(
            {
                "Open": [10.0, 10.1, 10.3, 10.4, 10.5, 10.6, 10.7, 11.25, 11.3],
                "High": [10.8, 10.9, 11.0, 10.95, 10.98, 11.0, 11.1, 11.4, 13.5],
                "Low": [9.2, 9.4, 9.6, 9.8, 10.0, 10.2, 10.5, 11.1, 11.2],
                "Close": [10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 11.2, 11.3, 13.0],
                "Volume": [1000, 1000, 1000, 1000, 1000, 1000, 2500, 1800, 3000],
            },
            index=dates,
        )
        df.index.name = "Date"

        def _unexpected_native_scanner(*args, **kwargs):
            raise AssertionError("Native DailyScanner path should not run for price-action profile scans")

        monkeypatch.setattr("routes.scanner.DailyScanner.get_market_signals", _unexpected_native_scanner)
        monkeypatch.setattr("routes.scanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_DAILY", False)
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", False)
        monkeypatch.setattr("core.market.MarketLists.get_market_list", lambda choice: {"COMI"})
        monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", lambda ticker, include_live=False: df.copy())
        monkeypatch.setattr("routes.scanner.Signal.get_or_none", lambda *args, **kwargs: None)
        monkeypatch.setattr("routes.scanner.Signal.create", lambda **kwargs: None)

        background_scan_task(index="ALL", intraday=False, notify=False, profile_id=profile.id)

        assert SCAN_STATE["status"] == "COMPLETED"
        assert SCAN_STATE["result"]["strategy_profile"]["source_type"] == "PRICE_ACTION"
        assert SCAN_STATE["result"]["strategy_profile"]["profile_name"] == "EGX Price Action Scanner"
        assert SCAN_STATE["result"]["strategy_profile"]["backtest_summary"]["total_return"] == 12.5
        assert SCAN_STATE["result"]["strategy_profile"]["ranking_summary"]["combined_score"] == 81.5
        assert SCAN_STATE["result"]["signals_count"] == 1
        assert SCAN_STATE["result"]["signals"][0]["Ticker"] == "COMI"
        assert SCAN_STATE["result"]["signals"][0]["Routing_Reason"] == "price_action_profile_signal"

    def test_daily_scanner_returns_full_empty_payload_when_universe_load_fails(self, monkeypatch):
        from core import DailyScanner

        monkeypatch.setattr("core.DailyScanner.DataManager.list_tickers", lambda: ["COMI"])
        monkeypatch.setattr("core.DailyScanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr(
            "core.DailyScanner.DataManager.get_universe_data",
            lambda tickers, include_live=False: pd.DataFrame(),
        )

        signals, monitored, breadth, regime = DailyScanner.get_market_signals(index_choice="EGX30")

        assert signals == []
        assert monitored == []
        assert breadth == 0.0
        assert regime == "UNKNOWN"

    def test_daily_scanner_attaches_whale_and_trap_metadata(self, monkeypatch):
        from core import DailyScanner
        audit_log = MagicMock()
        monkeypatch.setattr("core.DailyScanner.TimeUtils.now", lambda: datetime.datetime(2026, 3, 27))

        index = pd.MultiIndex.from_tuples(
            [("COMI", datetime.datetime(2026, 3, 26))],
            names=["Ticker", "Row"],
        )
        universe_df = pd.DataFrame(
            {
                "Date": [datetime.datetime(2026, 3, 26)],
                "Close": [102.4],
                "EMA9": [100.0],
                "RSI": [63.2],
            },
            index=index,
        )

        monkeypatch.setattr("core.DailyScanner.DataManager.list_tickers", lambda: ["COMI"])
        monkeypatch.setattr("core.DailyScanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr("core.DailyScanner.DataManager.get_universe_data", lambda tickers, include_live=False: universe_df)
        monkeypatch.setattr("core.DailyScanner.SignalEngine.add_indicators_universe", lambda frame, lookback: frame)
        monkeypatch.setattr(
            "core.DailyScanner.SignalEngine.vectorize_signals",
            lambda latest_rows, settings, resistance_col: pd.Series([True], index=latest_rows.index),
        )
        monkeypatch.setattr("core.DailyScanner.MarketLists.is_egx70_ticker", lambda ticker: False)
        monkeypatch.setattr(
            "core.DailyScanner.SignalEngine.check_buy_signal",
            lambda last, settings, resistance_col, profile=None: {
                "Signal_Type": "BUY",
                "Signal_Setup": "BREAKOUT",
                "Entry_Price": 102.4,
                "Stop_Loss": 99.0,
                "Target_Price": 108.0,
                "Target_Price_2": 112.0,
                "Score": 8,
                "RSI": 63.2,
                "Volume_Spike": 2.6,
                "VSA_Valid": True,
            },
        )
        monkeypatch.setattr("core.DailyScanner.SignalEngine.check_trickster_signal", lambda *args, **kwargs: None)
        monkeypatch.setattr("core.DailyScanner.calculate_sector_relative_strength", lambda *args, **kwargs: {"Banks": 0.12})
        monkeypatch.setattr(
            "core.DailyScanner.route_candidate",
            lambda **kwargs: {
                "allowed": True,
                "route_profile": "EGX30_TREND_PROFILE",
                "liquidity_tier": "LIQUID",
                "sector_rs_14": 0.12,
                "routing_reason": "egx30_trend",
            },
        )
        monkeypatch.setattr(
            "core.regime_router.route_candidate",
            lambda **kwargs: {
                "allowed": True,
                "route_profile": "EGX30_TREND_PROFILE",
                "liquidity_tier": "LIQUID",
                "sector_rs_14": 0.12,
                "routing_reason": "egx30_trend",
            },
        )
        monkeypatch.setattr("core.market.SectorAnalysis.get_sector", lambda ticker: "Banks")
        monkeypatch.setattr(
            "core.DailyScanner.Vanaheim.hunt_whales",
            lambda universe=None: {
                "status": "success",
                "count": 1,
                "candidates": [
                    {"Ticker": "COMI", "Signal": "ACCUMULATION", "Strength": 9.0, "Sector": "Banks"}
                ],
            },
        )
        monkeypatch.setattr(
            "core.DailyScanner.Svartalfheim.hunt_traps",
            lambda universe=None: {"status": "none", "bull_traps": [], "bear_traps": []},
        )
        monkeypatch.setattr("core.DailyScanner.audit.log_event", audit_log)

        signals, monitored, breadth, regime = DailyScanner.get_market_signals(index_choice="EGX30")

        assert len(signals) == 1
        assert monitored
        assert breadth == 100.0
        assert regime == "BULLISH"

        signal = signals[0]
        assert signal["Whale_Signal"] == "ACCUMULATION"
        assert signal["Whale_Alignment"] == "SUPPORTIVE"
        assert signal["Whale_Reason"] == "accumulation_support"
        assert signal["Whale_Strength"] == 1.0
        assert signal["Trap_Risk_Score"] == 0
        assert signal["Trap_Risk_Band"] == "LOW"
        assert signal["Trap_Risk_Reason"] == "low_risk_alignment"
        assert signal["Trap_Risk"] == "LOW"
        audit_meta = audit_log.call_args.kwargs["meta"]
        assert audit_meta["whale_trap_diagnostics"]["supportive_whale_alignments"] == 1
        assert audit_meta["whale_trap_diagnostics"]["whale_conflicts"] == 0
        assert audit_meta["whale_trap_diagnostics"]["threshold_analysis"]["would_review_count"] == 0
        assert audit_meta["whale_trap_diagnostics"]["threshold_analysis"]["would_block_count"] == 0
        assert signal["Enforcement_State"] == "ALLOW"
        assert signal["Enforcement_Visibility"] == "VISIBLE"
        assert signal["Enforcement_Reason"] == "not_enforced"
        assert signal["Enforcement_Profile"] == "EGX30_GUARDED"
        assert audit_meta["enforcement_diagnostics"]["allow_count"] == 1
        assert audit_meta["enforcement_diagnostics"]["watch_only_count"] == 0
        assert audit_meta["enforcement_diagnostics"]["block_count"] == 0
        assert audit_meta["calibration_diagnostics"]["rollout_mode"] == "compare_only"
        assert audit_meta["calibration_diagnostics"]["market_segments"]["EGX30"]["active_enforcement_profile"] == "EGX30_GUARDED"
        assert audit_meta["calibration_diagnostics"]["market_segments"]["EGX30"]["rollback_profile"] == "EGX30_BALANCED"

    def test_daily_scanner_keeps_blocked_signal_visible_with_enforcement_reason(self, monkeypatch):
        from core import DailyScanner
        audit_log = MagicMock()
        monkeypatch.setattr("core.DailyScanner.TimeUtils.now", lambda: datetime.datetime(2026, 3, 27))

        index = pd.MultiIndex.from_tuples(
            [("FWRY", datetime.datetime(2026, 3, 26))],
            names=["Ticker", "Row"],
        )
        universe_df = pd.DataFrame(
            {
                "Date": [datetime.datetime(2026, 3, 26)],
                "Close": [20.0],
                "EMA9": [19.5],
                "RSI": [58.0],
            },
            index=index,
        )

        monkeypatch.setattr("core.DailyScanner.DataManager.list_tickers", lambda: ["FWRY"])
        monkeypatch.setattr("core.DailyScanner.get_excluded_tickers_upper", lambda: set())
        monkeypatch.setattr("core.DailyScanner.DataManager.get_universe_data", lambda tickers, include_live=False: universe_df)
        monkeypatch.setattr("core.DailyScanner.SignalEngine.add_indicators_universe", lambda frame, lookback: frame)
        monkeypatch.setattr(
            "core.DailyScanner.SignalEngine.vectorize_signals",
            lambda latest_rows, settings, resistance_col: pd.Series([True], index=latest_rows.index),
        )
        monkeypatch.setattr("core.DailyScanner.MarketLists.is_egx70_ticker", lambda ticker: True)
        monkeypatch.setattr(
            "core.DailyScanner.SignalEngine.check_buy_signal",
            lambda last, settings, resistance_col, profile=None: {
                "Signal_Type": "BUY",
                "Signal_Setup": "BREAKOUT",
                "Entry_Price": 20.0,
                "Stop_Loss": 18.4,
                "Target_Price": 22.5,
                "Target_Price_2": 23.2,
                "Score": 7,
                "RSI": 58.0,
                "Volume_Spike": 2.1,
                "VSA_Valid": False,
            },
        )
        monkeypatch.setattr("core.DailyScanner.SignalEngine.check_trickster_signal", lambda *args, **kwargs: None)
        monkeypatch.setattr("core.DailyScanner.calculate_sector_relative_strength", lambda *args, **kwargs: {"Tech": -0.03})
        monkeypatch.setattr(
            "core.DailyScanner.route_candidate",
            lambda **kwargs: {
                "allowed": True,
                "route_profile": "EGX70_TACTICAL_PROFILE",
                "liquidity_tier": "ILLIQUID",
                "sector_rs_14": -0.03,
                "routing_reason": "egx70_tactical",
            },
        )
        monkeypatch.setattr(
            "core.regime_router.route_candidate",
            lambda **kwargs: {
                "allowed": True,
                "route_profile": "EGX70_TACTICAL_PROFILE",
                "liquidity_tier": "ILLIQUID",
                "sector_rs_14": -0.03,
                "routing_reason": "egx70_tactical",
            },
        )
        monkeypatch.setattr("core.market.SectorAnalysis.get_sector", lambda ticker: "Tech")
        monkeypatch.setattr(
            "core.DailyScanner.Vanaheim.hunt_whales",
            lambda universe=None: {
                "status": "success",
                "count": 1,
                "candidates": [
                    {"Ticker": "FWRY", "Signal": "DISTRIBUTION", "Strength": 9.0, "Sector": "Tech"}
                ],
            },
        )
        monkeypatch.setattr(
            "core.DailyScanner.Svartalfheim.hunt_traps",
            lambda universe=None: {
                "status": "success",
                "bull_traps": [{"Ticker": "FWRY"}],
                "bear_traps": [],
            },
        )
        monkeypatch.setattr("core.DailyScanner.audit.log_event", audit_log)

        signals, monitored, breadth, regime = DailyScanner.get_market_signals(index_choice="EGX70")

        assert len(signals) == 1
        assert monitored
        assert breadth == 100.0
        assert regime == "BULLISH"

        signal = signals[0]
        assert signal["Ticker"] == "FWRY"
        assert signal["Trap_Risk_Band"] == "SEVERE"
        assert signal["Whale_Alignment"] == "CONFLICT"
        assert signal["Enforcement_State"] == "BLOCK_EXECUTION"
        assert signal["Enforcement_Visibility"] == "VISIBLE"
        assert signal["Enforcement_Reason"] == "severe_trap_risk"
        assert signal["Enforcement_Profile"] == "EGX70_HARDENED"
        assert "severe trap risk" in signal["Enforcement_Notes"].lower()

        audit_meta = audit_log.call_args.kwargs["meta"]
        assert audit_meta["enforcement_diagnostics"]["allow_count"] == 0
        assert audit_meta["enforcement_diagnostics"]["watch_only_count"] == 0
        assert audit_meta["enforcement_diagnostics"]["block_count"] == 1
        assert audit_meta["enforcement_diagnostics"]["counts_by_reason"] == {"severe_trap_risk": 1}
        assert audit_meta["calibration_diagnostics"]["market_segments"]["EGX70"]["active_enforcement_profile"] == "EGX70_HARDENED"
        assert audit_meta["calibration_diagnostics"]["market_segments"]["EGX70"]["rollback_profile"] == "EGX70_STRICT"


# =============================================================================
# DATA ENDPOINTS
# =============================================================================

class TestDataEndpoints:
    """Tests for data API endpoints."""

    def test_data_tickers(self, monkeypatch):
        """GET /api/data/tickers should return list of tickers."""
        monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: set())
        monkeypatch.setattr(
            "routes.data.DataManager.list_tickers",
            lambda: ["COMI", "FWRY", "SWDY"],
        )
        response = client.get("/api/v1/data/tickers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "COMI" in data

    def test_data_tickers_exclude_blacklisted(self, monkeypatch):
        monkeypatch.setattr("routes.data.DataManager.list_tickers", lambda: ["COMI", "FWRY"])
        monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: {"comi"})
        response = client.get("/api/v1/data/tickers")
        assert response.status_code == 200
        data = response.json()
        assert "COMI" not in data
        assert "FWRY" in data

    def test_ticker_data_blacklisted_blocked(self, monkeypatch):
        monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: {"COMI"})
        response = client.get("/api/v1/data/ticker/COMI")
        assert response.status_code == 403
        assert "blacklisted" in response.json()["detail"].lower()

    def test_ticker_data_not_found(self, monkeypatch):
        """GET /api/data/ticker/{ticker} should return 404 for unknown ticker."""
        monkeypatch.setattr(
            "routes.data.DataManager.get_stock_data",
            lambda ticker, limit=100, enrich_obv=False: None,
        )
        response = client.get("/api/v1/data/ticker/UNKNOWN_TICKER")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_intraday_data_not_found(self, monkeypatch):
        """GET /api/data/intraday/{ticker} should return 404 when no data."""
        monkeypatch.setattr(
            "routes.data.DataManager.get_intraday_data",
            lambda ticker, limit=300: None,
        )
        response = client.get("/api/v1/data/intraday/UNKNOWN_TICKER")
        assert response.status_code == 404

    def test_data_sync_status(self):
        """GET /api/data/sync/status should return current sync state."""
        response = client.get("/api/v1/data/sync/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["IDLE", "RUNNING", "COMPLETED", "ERROR"]

    def test_pipeline_observability(self):
        """GET /api/data/observability should return metrics."""
        response = client.get("/api/v1/data/observability")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
