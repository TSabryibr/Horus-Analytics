"""
DEEP COVERAGE: ANALYTICS, DATA, SCANNER INTERNALS
===================================================
Targeted tests for the remaining uncovered lines across analytics
(Monte Carlo, watcher, health, cache persistence), data (sync lifecycle,
ticker data transform, portfolio freshness), and scanner (background
scan task, sanitize_floats).
"""

from core.settings import settings
import pytest
import json
import datetime
import warnings
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from api import app
from database import Trade, Position, Portfolio

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# ANALYTICS: Monte Carlo with trades
# =============================================================================

class TestMonteCarlo:
    """Tests for the Monte Carlo simulation endpoint."""

    def test_montecarlo_no_trades(self):
        """POST /api/montecarlo with no closed trades should return warning."""
        response = client.post("/api/v1/montecarlo", json={
            "initial_capital": 100000,
            "simulations": 100,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "warning"
        assert "No closed trades" in data["message"]

    def test_montecarlo_with_trades(self, monkeypatch):
        """POST /api/montecarlo should run simulation when trades exist."""
        # Seed trades
        p = Portfolio.select().first()
        Trade.create(
            ticker="COMI", shares=100, entry_price=10.0, exit_price=12.0,
            entry_date="2025-01-01", exit_date="2025-01-10",
            pnl=200.0, pnl_pct=20.0, portfolio=p,
        )
        Trade.create(
            ticker="FWRY", shares=50, entry_price=5.0, exit_price=4.0,
            entry_date="2025-01-05", exit_date="2025-01-12",
            pnl=-50.0, pnl_pct=-10.0, portfolio=p,
        )
        mock_result = {
            "median_final": 105000,
            "best_final": 130000,
            "worst_final": 85000,
            "ruin_probability": 0.02,
        }
        monkeypatch.setattr("routes.analytics.MonteCarlo.run_monte_carlo", lambda trades, cap, sims: mock_result)
        response = client.post("/api/v1/montecarlo", json={
            "initial_capital": 100000,
            "simulations": 100,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data

    def test_montecarlo_with_trades_no_pnl_pct(self, monkeypatch):
        """POST /api/montecarlo should calculate pnl_pct when 0 in DB."""
        p = Portfolio.select().first()
        Trade.create(
            ticker="SWDY", shares=200, entry_price=20.0, exit_price=22.0,
            entry_date="2025-02-01", exit_date="2025-02-10",
            pnl=400.0, pnl_pct=0, portfolio=p,
        )
        monkeypatch.setattr("routes.analytics.MonteCarlo.run_monte_carlo",
                            lambda trades, cap, sims: {"median_final": 110000})
        response = client.post("/api/v1/montecarlo", json={
            "initial_capital": 100000,
            "simulations": 50,
        })
        assert response.status_code == 200
        assert response.json()["status"] == "success"


# =============================================================================
# ANALYTICS: Watcher, Health, Seasonality
# =============================================================================

class TestWatcherAndHealth:
    """Tests for watcher status and portfolio health endpoints."""

    def test_watcher_status(self, monkeypatch):
        """GET /api/watcher/status should return monitoring state."""
        monkeypatch.setattr("core.settings.settings.ENABLE_INTRADAY_ALERTS", True)
        monkeypatch.setattr("core.settings.settings.AUTO_TRADE_ENABLED", False)
        monkeypatch.setattr("core.settings.settings.is_market_open", lambda: False)
        response = client.get("/api/v1/watcher/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "watcher" in data
        watcher = data["watcher"]
        assert "running" in watcher
        assert "intraday_enabled" in watcher
        assert "auto_trade_enabled" in watcher
        assert "market_open" in watcher

    def test_health_heimdall(self, monkeypatch):
        """GET /api/v1/analytics/health should return portfolio health."""
        monkeypatch.setattr("routes.analytics.Heimdall.get_portfolio_health",
                            lambda: {"health": "GOOD", "score": 85})
        response = client.get("/api/v1/analytics/health")
        assert response.status_code == 200
        data = response.json()
        assert data["health"] == "GOOD"

    def test_seasonality_ticker(self, monkeypatch):
        """GET /api/seasonality should return ticker-specific seasonality."""
        monkeypatch.setattr("routes.analytics.Helheim.analyze_seasonality",
                            lambda ticker: {"jan": 3.2, "feb": -1.5})
        response = client.get("/api/v1/seasonality", params={"ticker": "COMI"})
        assert response.status_code == 200

    def test_audit_strategies(self, monkeypatch):
        """GET /api/audit should return strategy audit results."""
        monkeypatch.setattr("routes.analytics.Midgard.audit_strategies",
                            lambda days_limit=None: {"win_rate": 65, "avg_pnl": 2.5})
        response = client.get("/api/v1/audit")
        assert response.status_code == 200

    def test_whales_vanaheim(self, monkeypatch):
        """GET /api/whales should return whale tracking data."""
        monkeypatch.setattr("routes.analytics.Vanaheim.hunt_whales",
                            lambda: [{"ticker": "COMI", "flow": "ACCUMULATION"}])
        from routes.shared import WHALE_CACHE
        WHALE_CACHE["data"] = None
        WHALE_CACHE["timestamp"] = None
        response = client.get("/api/v1/whales")
        assert response.status_code == 200


# =============================================================================
# ANALYTICS: Cache internals
# =============================================================================

class TestAnalyticsCacheInternals:
    """Tests for analytics cache persistence and date parsing."""

    def test_parse_date_prefix_valid(self):
        """_parse_date_prefix should parse YYYY-MM-DD."""
        from routes.analytics import _parse_date_prefix
        result = _parse_date_prefix("2025-06-15 12:30:00")
        assert result == datetime.date(2025, 6, 15)

    def test_parse_date_prefix_none(self):
        """_parse_date_prefix should return None for None."""
        from routes.analytics import _parse_date_prefix
        assert _parse_date_prefix(None) is None

    def test_parse_date_prefix_invalid(self):
        """_parse_date_prefix should return None for invalid."""
        from routes.analytics import _parse_date_prefix
        assert _parse_date_prefix("not-a-date") is None

    def test_cache_is_fresh(self):
        """_cache_is_fresh should return True for recent cache."""
        from routes.analytics import _cache_is_fresh, _current_data_version
        from core import TimeUtils
        cache = {"timestamp": TimeUtils.now(), "version": _current_data_version(), "data": [{"ticker": "COMI"}]}
        assert _cache_is_fresh(cache, 300) is True

    def test_cache_is_stale(self):
        """_cache_is_fresh should return False for stale cache."""
        from routes.analytics import _cache_is_fresh, _current_data_version
        from core import TimeUtils
        cache = {"timestamp": TimeUtils.now() - datetime.timedelta(seconds=600), "version": _current_data_version(), "data": [{"ticker": "COMI"}]}
        assert _cache_is_fresh(cache, 300) is False

    def test_cache_is_fresh_no_timestamp(self):
        """_cache_is_fresh should return False for no timestamp."""
        from routes.analytics import _cache_is_fresh
        assert _cache_is_fresh({}, 300) is False

    def test_analytics_scan_state_lifecycle(self):
        """_begin_analytics_scan should set scan state correctly."""
        from routes.analytics import _begin_analytics_scan, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK
        _begin_analytics_scan("test_scan_123", total=50, workers=4)
        with ANALYTICS_LOCK:
            assert ANALYTICS_CACHE_STATE["status"] == "RUNNING"
            assert ANALYTICS_CACHE_STATE["scan_id"] == "test_scan_123"
            assert ANALYTICS_CACHE_STATE["total"] == 50
            assert ANALYTICS_CACHE_STATE["workers"] == 4
            # Cleanup
            ANALYTICS_CACHE_STATE["status"] = "IDLE"

    def test_update_scan_progress(self):
        """_update_scan_progress should update progress correctly."""
        from routes.analytics import _update_scan_progress, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK
        _update_scan_progress(25, 50)
        with ANALYTICS_LOCK:
            assert ANALYTICS_CACHE_STATE["processed"] == 25
            assert ANALYTICS_CACHE_STATE["progress_pct"] == 50

    def test_analytics_state_snapshot(self):
        """_analytics_state_snapshot should return copy of state."""
        from routes.analytics import _analytics_state_snapshot
        snapshot = _analytics_state_snapshot(include_data=False)
        assert "status" in snapshot
        assert "data" not in snapshot

        snapshot_with_data = _analytics_state_snapshot(include_data=True)
        assert "data" in snapshot_with_data


# =============================================================================
# DATA: Sync lifecycle, ticker data with DataFrame
# =============================================================================

class TestDataDeepCoverage:
    """Tests for data sync lifecycle and ticker data transformation."""

    def test_data_sync_start(self, monkeypatch):
        """POST /api/data/sync/start should start background sync."""
        # Must mock the actual function that BackgroundTasks will call synchronously
        monkeypatch.setattr("routes.data.sync_all", lambda force_history_recent_days=0: None)
        from routes.data import DATA_SYNC_STATE, DATA_SYNC_LOCK
        with DATA_SYNC_LOCK:
            DATA_SYNC_STATE["status"] = "IDLE"

        response = client.post("/api/v1/data/sync/start")
        assert response.status_code == 200
        data = response.json()
        assert data["started"] is True

        # Cleanup
        with DATA_SYNC_LOCK:
            DATA_SYNC_STATE["status"] = "IDLE"

    def test_data_sync_start_already_running(self):
        """POST /api/data/sync/start should reject if already running."""
        from routes.data import DATA_SYNC_STATE, DATA_SYNC_LOCK
        with DATA_SYNC_LOCK:
            DATA_SYNC_STATE["status"] = "RUNNING"

        response = client.post("/api/v1/data/sync/start")
        assert response.status_code == 200
        data = response.json()
        assert data["started"] is False

        # Cleanup
        with DATA_SYNC_LOCK:
            DATA_SYNC_STATE["status"] = "IDLE"

    def test_ticker_data_success(self, monkeypatch):
        """GET /api/data/ticker/{ticker} should return OHLCV records."""
        mock_df = pd.DataFrame({
            "Date": pd.date_range("2025-01-01", periods=5),
            "Open": [10, 11, 12, 13, 14],
            "High": [11, 12, 13, 14, 15],
            "Low": [9, 10, 11, 12, 13],
            "Close": [10.5, 11.5, 12.5, 13.5, 14.5],
            "Volume": [1000, 2000, 3000, 4000, 5000],
        })
        monkeypatch.setattr("routes.data.DataManager.get_stock_data", lambda ticker, **kw: mock_df)
        response = client.get("/api/v1/data/ticker/COMI")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5
        assert "Close" in data[0]

    def test_intraday_data_success(self, monkeypatch):
        """GET /api/data/intraday/{ticker} should return intraday OHLCV."""
        mock_df = pd.DataFrame({
            "Date": pd.date_range("2025-01-01 10:00", periods=3, freq="5min"),
            "Open": [10, 10.1, 10.2],
            "High": [10.2, 10.3, 10.4],
            "Low": [9.9, 10.0, 10.1],
            "Close": [10.1, 10.2, 10.3],
            "Volume": [100, 200, 300],
        })
        monkeypatch.setattr("routes.data.DataManager.get_intraday_data", lambda ticker, limit=300: mock_df)
        response = client.get("/api/v1/data/intraday/COMI")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_portfolio_freshness(self, monkeypatch):
        """GET /api/data/status/portfolio should return portfolio KPIs."""
        monkeypatch.setattr("routes.data.evaluate_freshness", lambda **kw: {
            "run_date": "2025-02-19",
            "history": {"kpis": {"staleness": 0}},
            "intraday": {"kpis": {"staleness": 5}},
            "overall_ok": True,
        })
        monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)
        response = client.get("/api/v1/data/status/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert "run_date" in data
        assert "overall_ok" in data

    def test_sync_runs(self, monkeypatch):
        """GET /api/data/sync/runs should return run metadata."""
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_history",
                "status": "COMPLETED",
                "provider_context": {"reason": "most_recent_history", "fallback_from": None},
            },
            {
                "run_id": "002",
                "stage": "ingest_intraday",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "status": "ERROR",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
        ])
        response = client.get("/api/v1/data/sync/runs")
        assert response.status_code == 200
        data = response.json()
        assert "runs" in data
        assert data["summary"]["total_runs"] == 3
        assert data["summary"]["fallback_runs"] == 1
        assert data["summary"]["error_runs"] == 1
        assert data["summary"]["problem_runs"] == 2

    def test_sync_runs_problems_only_filters_fallback_and_error_runs(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_history",
                "status": "COMPLETED",
                "provider_context": {"reason": "most_recent_history", "fallback_from": None},
            },
            {
                "run_id": "002",
                "stage": "ingest_intraday",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "status": "WARNING",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs", params={"problems_only": "true"})

        assert response.status_code == 200
        data = response.json()
        assert {run["run_id"] for run in data["runs"]} == {"002", "003"}
        assert data["summary"]["problem_runs"] == 2

    def test_sync_runs_treat_runtime_ingest_fallback_as_problem(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_history",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "most_recent_history",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "002",
                "stage": "ingest_intraday",
                "status": "COMPLETED",
                "provider_context": {"reason": "most_recent_intraday", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs", params={"problems_only": "true"})

        assert response.status_code == 200
        data = response.json()
        assert {run["run_id"] for run in data["runs"]} == {"001"}
        assert data["summary"]["fallback_runs"] == 1
        assert data["summary"]["problem_runs"] == 1

    def test_sync_runs_surface_runtime_fallback_fields_on_rows(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "failure_mode": "source_unavailable",
                        "status": "completed_with_fallback",
                    },
                },
            }
        ])

        response = client.get("/api/v1/data/sync/runs")

        assert response.status_code == 200
        data = response.json()
        run = data["runs"][0]
        assert run["has_provider_fallback"] is True
        assert run["runtime_used_provider"] == "CSV"
        assert run["runtime_fallback_from"] == "MUBASHER_DB"
        assert run["runtime_failure_mode"] == "source_unavailable"
        assert run["runtime_status"] == "completed_with_fallback"

    def test_sync_runs_surface_problem_type_on_rows(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_history",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "status": "WARNING",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
            {
                "run_id": "004",
                "stage": "ingest_ticks",
                "status": "ERROR",
                "provider_context": {
                    "reason": "configured_ticks_provider",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "005",
                "stage": "ingest_history",
                "status": "COMPLETED",
                "provider_context": {"reason": "most_recent_history", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs")

        assert response.status_code == 200
        data = response.json()
        problem_types = {run["run_id"]: run["problem_type"] for run in data["runs"]}
        assert problem_types["001"] == "selection_fallback"
        assert problem_types["002"] == "runtime_fallback"
        assert problem_types["003"] == "warning"
        assert problem_types["004"] == "error"
        assert problem_types["005"] is None

    def test_sync_runs_split_selection_and_runtime_fallback_counts(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_history",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "failure_mode": "source_unavailable",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "status": "ERROR",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs")

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["fallback_runs"] == 2
        assert data["summary"]["selection_fallback_runs"] == 1
        assert data["summary"]["runtime_fallback_runs"] == 1
        assert data["summary"]["problem_runs"] == 3

    def test_sync_runs_summary_counts_problem_types(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_history",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "status": "WARNING",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
            {
                "run_id": "004",
                "stage": "ingest_ticks",
                "status": "ERROR",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
            {
                "run_id": "005",
                "stage": "ingest_history",
                "status": "COMPLETED",
                "provider_context": {"reason": "most_recent_history", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs")

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["problem_type_counts"] == {
            "error": 1,
            "warning": 1,
            "selection_fallback": 1,
            "runtime_fallback": 1,
        }

    def test_sync_runs_summary_counts_stages_and_providers(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_history",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "provider": "DIRECTFN",
                "status": "WARNING",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
            {
                "run_id": "004",
                "stage": "ingest_ticks",
                "provider": "DIRECTFN",
                "status": "ERROR",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
            {
                "run_id": "005",
                "stage": "ingest_history",
                "provider": "CSV",
                "status": "COMPLETED",
                "provider_context": {"reason": "most_recent_history", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs")

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["stage_counts"] == {
            "ingest_intraday": 1,
            "ingest_history": 2,
            "ingest_ticks": 2,
        }
        assert data["summary"]["provider_counts"] == {
            "MUBASHER_DB": 2,
            "DIRECTFN": 2,
            "CSV": 1,
        }

    def test_sync_runs_facets_scope_problem_type_counts_to_filtered_rows(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_history",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "provider": "MUBASHER_DB",
                "status": "WARNING",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs", params={"problem_type": "runtime_fallback"})

        assert response.status_code == 200
        data = response.json()
        assert {run["run_id"] for run in data["runs"]} == {"002"}
        assert data["summary"]["problem_type_counts"] == {
            "error": 0,
            "warning": 1,
            "selection_fallback": 1,
            "runtime_fallback": 1,
        }
        assert data["facets"]["problem_type_counts"] == {
            "error": 0,
            "warning": 0,
            "selection_fallback": 0,
            "runtime_fallback": 1,
        }

    def test_sync_runs_filter_selection_fallback_type(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_history",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
        ])

        response = client.get("/api/v1/data/sync/runs", params={"fallback_type": "selection"})

        assert response.status_code == 200
        data = response.json()
        assert {run["run_id"] for run in data["runs"]} == {"001"}
        assert data["filters"]["fallback_type"] == "selection"

    def test_sync_runs_filter_runtime_fallback_type(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_history",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "status": "ERROR",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs", params={"fallback_type": "runtime"})

        assert response.status_code == 200
        data = response.json()
        assert {run["run_id"] for run in data["runs"]} == {"002"}
        assert data["filters"]["fallback_type"] == "runtime"

    def test_sync_runs_reject_invalid_fallback_type(self):
        response = client.get("/api/v1/data/sync/runs", params={"fallback_type": "bad"})

        assert response.status_code == 400
        assert response.json()["detail"] == "fallback_type must be 'selection' or 'runtime'"

    def test_sync_runs_filter_problem_type_error(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_ticks",
                "status": "ERROR",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "status": "WARNING",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs", params={"problem_type": "error"})

        assert response.status_code == 200
        data = response.json()
        assert {run["run_id"] for run in data["runs"]} == {"002"}
        assert data["filters"]["problem_type"] == "error"

    def test_sync_runs_filter_problem_type_runtime_fallback(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_history",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "status": "ERROR",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs", params={"problem_type": "runtime_fallback"})

        assert response.status_code == 200
        data = response.json()
        assert {run["run_id"] for run in data["runs"]} == {"002"}
        assert data["filters"]["problem_type"] == "runtime_fallback"

    def test_sync_runs_reject_invalid_problem_type(self):
        response = client.get("/api/v1/data/sync/runs", params={"problem_type": "bad"})

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "problem_type must be 'error', 'warning', 'selection_fallback', or 'runtime_fallback'"
        )

    def test_sync_runs_filter_stage(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_history",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "provider": "MUBASHER_DB",
                "status": "WARNING",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs", params={"stage": "INGEST_HISTORY"})

        assert response.status_code == 200
        data = response.json()
        assert {run["run_id"] for run in data["runs"]} == {"002"}
        assert data["filters"]["stage"] == "ingest_history"

    def test_sync_runs_filter_provider(self, monkeypatch):
        monkeypatch.setattr("routes.data.list_runs", lambda realm, limit: [
            {
                "run_id": "001",
                "stage": "ingest_intraday",
                "provider": "MUBASHER_DB",
                "status": "COMPLETED",
                "provider_context": {"reason": "stale_db_fallback", "fallback_from": "MUBASHER_DB"},
            },
            {
                "run_id": "002",
                "stage": "ingest_history",
                "provider": "CSV",
                "status": "COMPLETED",
                "provider_context": {
                    "reason": "explicit_provider_override",
                    "fallback_from": None,
                    "ingest_summary": {
                        "used_provider": "CSV",
                        "fallback_from": "MUBASHER_DB",
                        "status": "completed_with_fallback",
                    },
                },
            },
            {
                "run_id": "003",
                "stage": "ingest_ticks",
                "provider": "MUBASHER_DB",
                "status": "WARNING",
                "provider_context": {"reason": "configured_ticks_provider", "fallback_from": None},
            },
        ])

        response = client.get("/api/v1/data/sync/runs", params={"provider": "mubasher_db"})

        assert response.status_code == 200
        data = response.json()
        assert {run["run_id"] for run in data["runs"]} == {"001", "003"}
        assert data["filters"]["provider"] == "MUBASHER_DB"

    def test_sync_runs_reject_invalid_stage(self):
        response = client.get("/api/v1/data/sync/runs", params={"stage": "bad_stage"})

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "stage must be 'ingest_intraday', 'ingest_history', or 'ingest_ticks'"
        )

    def test_sync_runs_reject_invalid_provider(self):
        response = client.get("/api/v1/data/sync/runs", params={"provider": "bad_provider"})

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "provider must be 'AUTO', 'CSV', 'MUBASHER_DB', 'DIRECTFN', or 'METASTOCK_DAT'"
        )

    def test_sync_runs_openapi_documents_filters(self):
        response = client.get("/openapi.json")

        assert response.status_code == 200
        operation = response.json()["paths"]["/api/v1/data/sync/runs"]["get"]
        assert operation["summary"] == "List recent ingestion runs"
        assert "provider fallback" in operation["description"].lower()
        assert operation["responses"]["200"]["description"] == "Recent sync runs with derived diagnostics"

        parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}

        assert "recent runs" in parameters["limit"]["description"].lower()
        assert "problem_type" in parameters["problems_only"]["description"]

    def test_openapi_has_no_duplicate_operation_id_warnings(self):
        app.openapi_schema = None

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            schema = app.openapi()

        assert "paths" in schema
        duplicate_operation_warnings = [
            str(item.message) for item in captured if "Duplicate Operation ID" in str(item.message)
        ]
        assert duplicate_operation_warnings == []

    def test_portfolio_routes_do_not_register_duplicate_post_handlers(self):
        route_entries = [
            (route.path, tuple(sorted(getattr(route, "methods", []) or [])))
            for route in app.routes
            if getattr(route, "path", None) in {"/api/v1/portfolios", "/api/v1/risk/check"}
        ]

        assert route_entries.count(("/api/v1/portfolios", ("POST",))) == 1
        assert route_entries.count(("/api/v1/risk/check", ("POST",))) == 1

    def test_data_status(self, monkeypatch):
        """GET /api/data/status should return data freshness."""
        monkeypatch.setattr("routes.data.evaluate_freshness", lambda **kw: {
            "history": {"fresh": True},
            "intraday": {"fresh": False},
            "overall_ok": True,
        })
        report = {
            "recommended_provider": "MUBASHER_DB",
            "recommended_history_provider": "MUBASHER_DB",
            "recommended_intraday_provider": "CSV",
            "recommended_history_details": {
                "provider": "MUBASHER_DB",
                "reason": "most_recent_history",
                "fallback_from": None,
                "evidence": {"history_latest": "20260211"},
            },
            "recommended_intraday_details": {
                "provider": "CSV",
                "reason": "stale_db_fallback",
                "fallback_from": "MUBASHER_DB",
                "evidence": {"stale_minutes": 20},
            },
        }
        monkeypatch.setattr(
            "routes.data.resolve_timeframe_provider",
            lambda timeframe: ("MUBASHER_DB", report) if timeframe == "history" else ("CSV", report),
        )
        monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)
        response = client.get("/api/v1/data/status")
        assert response.status_code == 200
        data = response.json()
        assert data["source"]["history_decision"]["reason"] == "most_recent_history"
        assert data["source"]["intraday_decision"]["reason"] == "stale_db_fallback"


# =============================================================================
# SCANNER: sanitize_floats, background_scan_task
# =============================================================================

class TestScannerInternals:
    """Tests for scanner helper functions and background task."""

    def test_sanitize_nan(self):
        """sanitize_floats should replace NaN with 0."""
        from routes.scanner import sanitize_floats
        assert sanitize_floats(float('nan')) == 0.0

    def test_sanitize_inf(self):
        """sanitize_floats should replace inf with 0."""
        from routes.scanner import sanitize_floats
        assert sanitize_floats(float('inf')) == 0.0

    def test_sanitize_nested(self):
        """sanitize_floats should handle nested dicts and lists."""
        from routes.scanner import sanitize_floats
        result = sanitize_floats({
            "a": [1.0, float('nan'), {"b": float('inf')}],
            "c": 3.14,
        })
        assert result["a"][1] == 0.0
        assert result["a"][2]["b"] == 0.0
        assert result["c"] == 3.14

    def test_sanitize_numpy_generic(self):
        """sanitize_floats should handle numpy scalar types."""
        from routes.scanner import sanitize_floats
        result = sanitize_floats(np.float64(3.14))
        assert result == pytest.approx(3.14)

    def test_stress_test_api(self, monkeypatch):
        """POST /api/stress-test should return stress test results."""
        monkeypatch.setattr("routes.analytics.StressTest.run_stress_test",
                            lambda idx: {"scenarios": [{"name": "2020 crash", "impact": -15}]})
        response = client.post("/api/v1/stress-test", json={"index": "EGX30"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_prediction_error_handling(self, monkeypatch):
        """POST /api/prediction should return error on exception."""
        monkeypatch.setattr("routes.analytics.MarketPredictor.check_macro_health",
                            MagicMock(side_effect=Exception("Data timeout")))
        from routes.shared import ORACLE_CACHE
        ORACLE_CACHE["data"] = None
        ORACLE_CACHE["timestamp"] = None
        response = client.post("/api/v1/prediction", json={"mode": "MACRO", "index": "EGX30"})
        assert response.status_code == 500
        assert "Data timeout" in response.json()["detail"]
