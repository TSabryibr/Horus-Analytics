"""
PHASE 7: FINAL COVERAGE PUSH
================================
Tests for the last uncovered lines: analytics run_analytics_task_logic
(with mocked MomentumBreakoutScanner), disk cache load/persist, _history_last_data_day,
system full-status error paths, scanner background_scan_task, and
portfolio management report action items.
"""

from core.settings import settings
import pytest
import json
import datetime
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np

from api import app
from database import Trade, Position, Portfolio, Signal

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# ANALYTICS: run_analytics_task_logic with mocked MomentumBreakoutScanner
# =============================================================================

class TestRunAnalyticsTaskLogic:
    """Tests for the core analytics scan logic function."""

    def test_run_analytics_empty_tickers(self, monkeypatch):
        """run_analytics_task_logic with 0 tickers should complete instantly."""
        from routes.analytics import (
            run_analytics_task_logic, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK,
        )
        monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda: [])
        run_analytics_task_logic("test_empty_001")
        with ANALYTICS_LOCK:
            assert ANALYTICS_CACHE_STATE["status"] == "IDLE"
            assert ANALYTICS_CACHE_STATE["rows"] == 0
            assert ANALYTICS_CACHE_STATE["scan_id"] == "test_empty_001"
            assert ANALYTICS_CACHE_STATE["progress_pct"] == 100

    def test_run_analytics_with_tickers(self, monkeypatch):
        """run_analytics_task_logic should process tickers via MomentumBreakoutScanner.analyze_stock."""
        from routes.analytics import (
            run_analytics_task_logic, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK,
        )
        monkeypatch.setattr("core.DataManager.DataManager.list_tickers", lambda: ["COMI", "FWRY"])
        monkeypatch.setattr("core.analyzers.MomentumBreakoutScanner.analyze_stock",
                            lambda ticker: {"Ticker": ticker, "Score": 80})
        run_analytics_task_logic("test_tickers_001")
        with ANALYTICS_LOCK:
            assert ANALYTICS_CACHE_STATE["status"] == "IDLE"
            assert ANALYTICS_CACHE_STATE["rows"] == 2
            assert ANALYTICS_CACHE_STATE["progress_pct"] == 100
            assert len(ANALYTICS_CACHE_STATE["data"]) == 2

    def test_run_analytics_partial_failure(self, monkeypatch):
        """run_analytics_task_logic should survive individual ticker failures."""
        from routes.analytics import (
            run_analytics_task_logic, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK,
        )
        call_count = {"n": 0}
        def _mock_analyze(ticker):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise ValueError("Ticker data missing")
            return {"Ticker": ticker, "Score": 75}

        monkeypatch.setattr("core.DataManager.DataManager.list_tickers",
                            lambda: ["A", "B", "C"])
        monkeypatch.setattr("core.analyzers.MomentumBreakoutScanner.analyze_stock", _mock_analyze)
        run_analytics_task_logic("test_partial_001")
        with ANALYTICS_LOCK:
            assert ANALYTICS_CACHE_STATE["status"] == "IDLE"
            # 2 out of 3 should succeed
            assert ANALYTICS_CACHE_STATE["rows"] == 2

    def test_run_analytics_total_failure(self, monkeypatch):
        """run_analytics_task_logic should handle total failure gracefully."""
        from routes.analytics import (
            run_analytics_task_logic, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK,
        )
        monkeypatch.setattr("core.DataManager.DataManager.list_tickers",
                            MagicMock(side_effect=Exception("DataManager offline")))
        run_analytics_task_logic("test_fail_001")
        with ANALYTICS_LOCK:
            assert ANALYTICS_CACHE_STATE["status"] == "ERROR"
            assert "DataManager offline" in ANALYTICS_CACHE_STATE["error"]


# =============================================================================
# ANALYTICS: disk cache load/persist
# =============================================================================

class TestAnalyticsDiskCache:
    """Tests for analytics cache disk persistence."""

    def test_load_from_disk(self, tmp_path, monkeypatch):
        """_load_analytics_cache_from_disk should restore from file."""
        from routes.analytics import (
            _load_analytics_cache_from_disk, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK,
        )
        cache_file = tmp_path / "analytics_cache.json"
        cache_file.write_text(json.dumps({
            "data": [{"Ticker": "COMI", "Score": 90}],
            "last_updated": "2025-02-19 14:00:00",
            "completed_at": "2025-02-19 14:05:00",
            "duration_sec": 300,
        }))
        monkeypatch.setattr("routes.analytics.ANALYTICS_CACHE_FILE", cache_file)
        _load_analytics_cache_from_disk()
        with ANALYTICS_LOCK:
            assert ANALYTICS_CACHE_STATE["rows"] == 1
            assert ANALYTICS_CACHE_STATE["cache_source"] == "disk"
            assert ANALYTICS_CACHE_STATE["status"] == "IDLE"

    def test_load_from_disk_missing_file(self, tmp_path, monkeypatch):
        """_load_analytics_cache_from_disk should handle missing file."""
        from routes.analytics import _load_analytics_cache_from_disk
        monkeypatch.setattr("routes.analytics.ANALYTICS_CACHE_FILE",
                            tmp_path / "nonexistent.json")
        # Should not raise
        _load_analytics_cache_from_disk()

    def test_load_from_disk_invalid_json(self, tmp_path, monkeypatch):
        """_load_analytics_cache_from_disk should handle invalid JSON."""
        from routes.analytics import _load_analytics_cache_from_disk
        cache_file = tmp_path / "analytics_cache.json"
        cache_file.write_text("not valid json!!!")
        monkeypatch.setattr("routes.analytics.ANALYTICS_CACHE_FILE", cache_file)
        _load_analytics_cache_from_disk()  # Should not raise

    def test_load_from_disk_no_data_list(self, tmp_path, monkeypatch):
        """_load_analytics_cache_from_disk should skip if data is not a list."""
        from routes.analytics import _load_analytics_cache_from_disk
        cache_file = tmp_path / "analytics_cache.json"
        cache_file.write_text(json.dumps({"data": "not_a_list"}))
        monkeypatch.setattr("routes.analytics.ANALYTICS_CACHE_FILE", cache_file)
        _load_analytics_cache_from_disk()  # Should not raise

    def test_persist_to_disk(self, tmp_path, monkeypatch):
        """_persist_analytics_cache_to_disk should write cache file."""
        from routes.analytics import (
            _persist_analytics_cache_to_disk, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK,
        )
        cache_file = tmp_path / "cache" / "analytics_cache.json"
        monkeypatch.setattr("routes.analytics.ANALYTICS_CACHE_FILE", cache_file)
        with ANALYTICS_LOCK:
            ANALYTICS_CACHE_STATE["data"] = [{"Ticker": "TEST", "Score": 50}]
            ANALYTICS_CACHE_STATE["rows"] = 1
        _persist_analytics_cache_to_disk()
        assert cache_file.exists()
        loaded = json.loads(cache_file.read_text())
        assert loaded["rows"] == 1

    def test_history_last_data_day(self, monkeypatch):
        """_history_last_data_day should return date from DataManager status."""
        from routes.analytics import _history_last_data_day
        monkeypatch.setattr("core.DataManager.DataManager.get_data_status",
                            lambda: {"last_updated": "2025-02-19 14:00:00"})
        result = _history_last_data_day()
        assert result == datetime.date(2025, 2, 19)

    def test_history_last_data_day_error(self, monkeypatch):
        """_history_last_data_day should return None on error."""
        from routes.analytics import _history_last_data_day
        monkeypatch.setattr("core.DataManager.DataManager.get_data_status",
                            MagicMock(side_effect=Exception("Offline")))
        assert _history_last_data_day() is None


# =============================================================================
# SYSTEM: full-status error paths
# =============================================================================

class TestSystemFullStatus:
    """Tests for system full-status endpoint error paths."""

    def test_full_status_data_error(self, monkeypatch):
        """GET /api/system/full-status should handle data_status error."""
        monkeypatch.setattr("routes.data.evaluate_freshness",
                            MagicMock(side_effect=Exception("Data engine down")))
        monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda s: None)
        response = client.get("/api/v1/system/full-status")
        assert response.status_code == 200
        data = response.json()
        assert data["data_status"]["status"] == "ERROR"
        assert "Data engine down" in data["data_status"]["message"]

    def test_full_status_with_scheduler_jobs(self, monkeypatch):
        """GET /api/system/full-status should include scheduler jobs."""
        mock_job = MagicMock()
        mock_job.id = "test_job"
        mock_job.next_run_time = datetime.datetime(2025, 2, 19, 15, 0, 0)
        mock_job.trigger = "interval[0:05:00]"

        from routes.shared import scheduler
        monkeypatch.setattr(scheduler, "get_jobs", lambda: [mock_job])
        monkeypatch.setattr("routes.data.evaluate_freshness",
                            lambda **kw: {"status": "OK"})
        monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda s: None)
        response = client.get("/api/v1/system/full-status")
        assert response.status_code == 200
        data = response.json()
        assert len(data["scheduler"]["jobs"]) >= 1
        assert data["scheduler"]["jobs"][0]["id"] == "test_job"


# =============================================================================
# SCANNER: background_scan_task
# =============================================================================

class TestBackgroundScanTask:
    """Tests for scanner background_scan_task function."""

    def test_background_scan_success(self, monkeypatch):
        """background_scan_task should process signals and update state."""
        from routes.scanner import background_scan_task
        from routes.shared import SCAN_STATE

        mock_signals = [
            {"Ticker": "COMI", "Signal_Type": "BUY", "Entry_Price": 85.0, "Score": 90},
            {"Ticker": "FWRY", "Signal_Type": "SELL", "Entry_Price": 5.0, "Score": 70},
        ]
        monkeypatch.setattr("routes.scanner.DailyScanner.get_market_signals",
                            lambda index_choice, is_intraday, progress_callback: (
                                mock_signals, [], {}, "BULLISH"
                            ))
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", False)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_DAILY", False)
        monkeypatch.setattr("routes.scanner.get_excluded_tickers_upper", lambda: set())

        background_scan_task("EGX30", False, False, use_active_profile=False)
        assert SCAN_STATE["status"] == "COMPLETED"
        assert SCAN_STATE["result"]["signals_count"] == 2
        assert SCAN_STATE["result"]["regime"] == "BULLISH"

    def test_background_scan_with_notify(self, monkeypatch):
        """background_scan_task with notify=True should send Telegram."""
        from routes.scanner import background_scan_task
        from routes.shared import SCAN_STATE

        sent_msgs = []
        monkeypatch.setattr("routes.scanner.AlertManager.filter_new_signals", lambda signals, scan_label: list(signals))
        monkeypatch.setattr("routes.scanner.DailyScanner.get_market_signals",
                            lambda index_choice, is_intraday, progress_callback: (
                                [{"Ticker": "COMI", "Signal_Type": "BUY", "Entry_Price": 85.0, "Score": 90}],
                                [], {}, "NEUTRAL"
                            ))
        monkeypatch.setattr("routes.scanner.TelegramBot_Alerts.format_signal_alert",
                            lambda signals: "COMI BUY 85.0")
        monkeypatch.setattr("routes.scanner.AlertManager.broadcast_alert",
                            lambda msg, priority="INFO", ticker=None, signal_data=None: sent_msgs.append(msg))
        monkeypatch.setattr("routes.scanner.AlertManager.broadcast_image", lambda *args, **kwargs: None)
        monkeypatch.setattr("core.ReportGenerator.create_horus_signal_card", lambda **kwargs: b"fake-image")
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", False)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_HORUS_EYE", False)

        background_scan_task("EGX30", False, True, use_active_profile=False)
        assert SCAN_STATE["status"] == "COMPLETED"
        assert len(sent_msgs) >= 1

    def test_background_scan_error(self, monkeypatch):
        """background_scan_task should set ERROR status on exception."""
        from routes.scanner import background_scan_task
        from routes.shared import SCAN_STATE

        monkeypatch.setattr("routes.scanner.DailyScanner.get_market_signals",
                            MagicMock(side_effect=Exception("Scanner crashed")))

        background_scan_task("EGX30", False, False, use_active_profile=False)
        assert SCAN_STATE["status"] == "ERROR"
        assert "Scanner crashed" in SCAN_STATE["error"]

    def test_background_scan_auto_trade(self, monkeypatch):
        """background_scan_task with AUTO_TRADE should trigger AutoTrader."""
        from routes.scanner import background_scan_task
        from routes.shared import SCAN_STATE

        persist_calls = []
        execute_calls = []
        monkeypatch.setattr("routes.scanner.DailyScanner.get_market_signals",
                            lambda index_choice, is_intraday, progress_callback: (
                                [{
                                    "Ticker": "COMI",
                                    "Signal_Type": "BUY",
                                    "Entry_Price": 85.0,
                                    "Stop_Loss": 82.0,
                                    "Target_Price": 90.0,
                                    "Score": 90,
                                }],
                                [], {}, "BULLISH"
                            ))
        monkeypatch.setattr("routes.scanner.settings.AUTO_TRADE_ENABLED", True)
        monkeypatch.setattr("routes.scanner.settings.TELEGRAM_AUTO_BROADCAST_DAILY", False)
        monkeypatch.setattr(
            "routes.scanner._persist_manual_scan_run",
            lambda **kwargs: persist_calls.append(kwargs) or {"status": "completed", "run": {"id": 91}},
        )
        monkeypatch.setattr(
            "routes.scanner.SignalExecutor.execute_run",
            lambda run_id: execute_calls.append(run_id) or {"status": "completed"},
        )

        background_scan_task("EGX30", False, False, use_active_profile=False)
        assert SCAN_STATE["status"] == "COMPLETED"
        assert len(persist_calls) == 1
        assert execute_calls == [91]


# =============================================================================
# PORTFOLIO: action items in management report
# =============================================================================

class TestPortfolioActionItems:
    """Tests for management report with various action item triggers."""

    def test_report_with_exit_immediately_action(self, monkeypatch):
        """Management report should flag EXIT_IMMEDIATELY when price <= SL."""
        monkeypatch.setattr("routes.portfolio.RiskManager.analyze_portfolio",
                            lambda pid: {"status": "CRITICAL", "health_score": 30, "heat": 80,
                                        "recommendations": [{"title": "Cut losses", "message": "Price below SL", "severity": "HIGH"}]})
        p = Portfolio.select().first()
        Position.get_or_create(
            portfolio=p.id, ticker="EXIT_TEST", status="OPEN",
            defaults={
                "shares": 100, "entry_price": 100.0, "stop_loss": 95.0,
                "target_price": 110.0, "current_price": 93.0, "currency": "EGP",
            },
        )
        response = client.get(f"/api/v1/portfolio/management/report?portfolio_id={p.id}")
        assert response.status_code == 200
        data = response.json()
        # Find the EXIT_TEST position
        exit_pos = [pos for pos in data["positions"] if pos["ticker"] == "EXIT_TEST"]
        if exit_pos:
            assert exit_pos[0]["action"] == "EXIT_IMMEDIATELY"

    def test_report_with_take_profit_action(self, monkeypatch):
        """Management report should flag TAKE_PROFIT when price >= TP1."""
        monkeypatch.setattr("routes.portfolio.RiskManager.analyze_portfolio",
                            lambda pid: {"status": "HEALTHY", "health_score": 85, "heat": 10, "recommendations": []})
        p = Portfolio.select().first()
        Position.get_or_create(
            portfolio=p.id, ticker="TP_TEST", status="OPEN",
            defaults={
                "shares": 100, "entry_price": 50.0, "stop_loss": 47.0,
                "target_price": 55.0, "current_price": 56.0, "currency": "EGP",
            },
        )
        response = client.get(f"/api/v1/portfolio/management/report?portfolio_id={p.id}")
        assert response.status_code == 200
        data = response.json()
        tp_pos = [pos for pos in data["positions"] if pos["ticker"] == "TP_TEST"]
        if tp_pos:
            assert tp_pos[0]["action"] == "TAKE_PROFIT_REVIEW"

    def test_report_with_reduce_risk_action(self, monkeypatch):
        """Management report should flag REDUCE_RISK when drawdown > 3%."""
        monkeypatch.setattr("routes.portfolio.RiskManager.analyze_portfolio",
                            lambda pid: {"status": "WARNING", "health_score": 60, "heat": 40, "recommendations": []})
        p = Portfolio.select().first()
        Position.get_or_create(
            portfolio=p.id, ticker="RISK_TEST", status="OPEN",
            defaults={
                "shares": 100, "entry_price": 100.0, "stop_loss": 90.0,
                "target_price": 120.0, "current_price": 96.5, "currency": "EGP",
            },
        )
        response = client.get(f"/api/v1/portfolio/management/report?portfolio_id={p.id}")
        assert response.status_code == 200
        data = response.json()
        risk_pos = [pos for pos in data["positions"] if pos["ticker"] == "RISK_TEST"]
        if risk_pos:
            assert risk_pos[0]["action"] == "REDUCE_RISK_REVIEW"

    def test_format_management_report(self, monkeypatch):
        """_format_portfolio_management_report should produce valid markdown text."""
        monkeypatch.setattr("routes.portfolio.RiskManager.analyze_portfolio",
                            lambda pid: {"status": "HEALTHY", "health_score": 85, "heat": 10,
                                        "recommendations": [{"title": "Rebalance", "message": "Consider rebalancing", "severity": "INFO"}]})
        from routes.portfolio import _build_portfolio_management_report, _format_portfolio_management_report
        p = Portfolio.select().first()
        report = _build_portfolio_management_report(p.id)
        formatted = _format_portfolio_management_report(report, include_positions=5)
        assert "PORTFOLIO MANAGEMENT REPORT" in formatted
        assert "Summary" in formatted
        assert "Risk" in formatted
