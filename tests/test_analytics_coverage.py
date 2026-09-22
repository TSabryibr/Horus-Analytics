"""
ANALYTICS ENDPOINTS TESTS
=========================
Tests for routes/analytics.py — realm endpoints, analytics scan/cache,
smart money, Monte Carlo, Ragnarok, RRG.
"""

from core.settings import settings
import pytest
import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd

from api import app
from database import Trade, Position, Portfolio

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# CACHE UTILITY TESTS
# =============================================================================

class TestCacheUtilities:
    """Tests for analytics cache helper functions."""

    def test_cache_ttl_from_env(self, monkeypatch):
        """_cache_ttl_seconds should read from env variable."""
        monkeypatch.setenv("NEWS_CACHE_TTL_SEC", "600")
        from routes.analytics import _cache_ttl_seconds
        assert _cache_ttl_seconds("NEWS_CACHE_TTL_SEC", 300) == 600

    def test_cache_ttl_invalid_env(self, monkeypatch):
        """_cache_ttl_seconds should fallback on invalid env."""
        monkeypatch.setenv("NEWS_CACHE_TTL_SEC", "not_a_number")
        from routes.analytics import _cache_ttl_seconds
        assert _cache_ttl_seconds("NEWS_CACHE_TTL_SEC", 300) == 300

    def test_cache_ttl_missing_env(self):
        """_cache_ttl_seconds should use default when env not set."""
        from routes.analytics import _cache_ttl_seconds
        assert _cache_ttl_seconds("NONEXISTENT_ENV_VAR_XYZ", 42) == 42

    def test_safe_int_valid(self):
        """_safe_int should parse valid strings."""
        from routes.analytics import _safe_int
        assert _safe_int("10", 5) == 10

    def test_safe_int_invalid(self):
        """_safe_int should return default on invalid string."""
        from routes.analytics import _safe_int
        assert _safe_int("abc", 5) == 5

    def test_safe_int_none(self):
        """_safe_int should return default on None."""
        from routes.analytics import _safe_int
        assert _safe_int(None, 7) == 7

    def test_analytics_cache_keeps_populated_closed_session_cache_when_boot_version_unresolved(self, monkeypatch):
        """A version 0 boot snapshot should not force off-hours analytics refresh."""
        from routes.analytics import _analytics_cache_needs_refresh

        monkeypatch.setattr(settings, "is_market_open", lambda: False)
        monkeypatch.setattr("routes.analytics._history_last_data_day", lambda: datetime.date(2026, 6, 1))

        state = {
            "rows": 264,
            "status": "IDLE",
            "last_updated": "2026-06-01 12:54:19",
            "version": 22,
        }

        assert _analytics_cache_needs_refresh(state, current_version=0) is False

    def test_resolve_workers_single_ticker(self):
        """_resolve_analytics_workers should return 1 for single ticker."""
        from routes.analytics import _resolve_analytics_workers
        assert _resolve_analytics_workers(1) == 1

    def test_resolve_workers_many_tickers(self):
        """_resolve_analytics_workers should return >1 for multiple tickers."""
        from routes.analytics import _resolve_analytics_workers
        workers = _resolve_analytics_workers(50)
        assert workers >= 4
        assert workers <= 32


# =============================================================================
# REALM ENDPOINTS (WITH MOCKING)
# =============================================================================

class TestRealmEndpoints:
    """Tests for Norse realm analytics endpoints using mocks."""

    def test_news_ratatoskr_success(self, monkeypatch, tmp_path):
        """GET /api/news should return news data."""
        async def _fake_gather_gossip():
            return {"stories": [{"title": "EGX up"}], "macro_correlation": 0.25}

        monkeypatch.setattr("routes.analytics.SentimentCrawler.async_gather_gossip", _fake_gather_gossip)
        monkeypatch.setattr("routes.analytics.SentimentCrawler.get_bifrost_sentiment", lambda news: {"score": 0.8})
        monkeypatch.setattr("routes.analytics.NEWS_CACHE_FILE", tmp_path / "news_cache.json", raising=False)
        # Clear cache to force fresh fetch
        from routes.shared import NEWS_CACHE
        NEWS_CACHE["data"] = None
        NEWS_CACHE["timestamp"] = None
        NEWS_CACHE["version"] = -1

        response = client.get("/api/v1/news")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 1

    def test_news_ratatoskr_error(self, monkeypatch, tmp_path):
        """GET /api/news should return error status on exception."""
        async def _fake_gather_gossip():
            raise Exception("API down")

        monkeypatch.setattr("routes.analytics.SentimentCrawler.async_gather_gossip", _fake_gather_gossip)
        monkeypatch.setattr("routes.analytics.NEWS_CACHE_FILE", tmp_path / "news_cache.json", raising=False)
        from routes.shared import NEWS_CACHE
        NEWS_CACHE["data"] = None
        NEWS_CACHE["timestamp"] = None
        NEWS_CACHE["version"] = -1

        response = client.get("/api/v1/news")
        assert response.status_code == 500
        assert "API down" in response.json()["detail"]

    def test_sectors_alfheim(self, monkeypatch):
        """GET /api/sectors should return sector data."""
        async def _fake_analyze_rotation():
            return [{"sector": "Banks"}]

        monkeypatch.setattr("routes.analytics.SectorRotation.async_analyze_rotation", _fake_analyze_rotation)
        from routes.shared import SECTOR_CACHE
        SECTOR_CACHE["data"] = None
        SECTOR_CACHE["timestamp"] = None

        response = client.get("/api/v1/sectors")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_traps_svartalfheim(self, monkeypatch):
        """GET /api/traps should return trap data."""
        monkeypatch.setattr("routes.analytics.Svartalfheim.hunt_traps", lambda: [{"ticker": "COMI", "type": "BULL"}])
        from routes.shared import TRAP_CACHE
        TRAP_CACHE["data"] = None
        TRAP_CACHE["timestamp"] = None

        response = client.get("/api/v1/traps")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_strategy_fenrir(self, monkeypatch):
        """GET /api/strategy should return strategy proposal."""
        monkeypatch.setattr("routes.analytics.ExecutionWatchdog.generate_strategy_proposal", lambda: {"action": "HOLD"})
        from routes.shared import STRATEGY_CACHE
        STRATEGY_CACHE["data"] = None
        STRATEGY_CACHE["timestamp"] = None

        response = client.get("/api/v1/strategy")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_prediction_macro(self, monkeypatch):
        """POST /api/prediction should return macro health check."""
        monkeypatch.setattr("routes.analytics.MarketPredictor.check_macro_health", lambda idx: {"health": "OK"})
        from routes.shared import ORACLE_CACHE
        ORACLE_CACHE["data"] = None
        ORACLE_CACHE["timestamp"] = None

        response = client.post("/api/v1/prediction", json={"mode": "MACRO", "index": "EGX30"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["mode"] == "MACRO"

    def test_prediction_squeeze(self, monkeypatch):
        """POST /api/prediction with mode=SQUEEZE should return squeeze data."""
        monkeypatch.setattr("routes.analytics.MarketPredictor.hunt_the_coil", lambda: [{"ticker": "COMI"}])
        response = client.post("/api/v1/prediction", json={"mode": "SQUEEZE"})
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "SQUEEZE"


# =============================================================================
# RRG ENDPOINT
# =============================================================================

class TestRRGEndpoint:
    """Tests for the Relative Rotation Graph endpoint."""

    def test_rrg_sectors_view(self, monkeypatch):
        """GET /api/rrg?view=sectors should return sector rotation data."""
        monkeypatch.setattr("routes.analytics.SectorRotation.analyze_rotation", lambda **kw: [{"name": "Banks"}])
        response = client.get("/api/v1/rrg", params={"view": "sectors", "trail": 5})
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_rrg_stocks_view(self, monkeypatch):
        """GET /api/rrg?view=stocks should return stock rotation data."""
        monkeypatch.setattr("routes.analytics.SectorRotation.analyze_stock_rotation", lambda **kw: [{"ticker": "COMI"}])
        response = client.get("/api/v1/rrg", params={"view": "stocks"})
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_rrg_error(self, monkeypatch):
        """GET /api/rrg should return error on exception."""
        monkeypatch.setattr("routes.analytics.SectorRotation.analyze_rotation", MagicMock(side_effect=Exception("Fail")))
        response = client.get("/api/v1/rrg", params={"view": "sectors"})
        assert response.status_code == 500
        assert "Fail" in response.json()["detail"]


# =============================================================================
# ANALYTICS SCAN
# =============================================================================

class TestAnalyticsScan:
    """Tests for analytics scan/refresh endpoints."""

    def test_analytics_status(self):
        """GET /api/analytics/status should return scan state."""
        response = client.get("/api/v1/analytics/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "rows" in data

    def test_analytics_endpoint_marks_auto_refresh_as_running(self, monkeypatch):
        """GET /api/analytics should expose RUNNING state when it auto-starts a scan."""
        monkeypatch.setattr("routes.analytics.run_analytics_task_logic", lambda scan_id: None)
        from routes.analytics import ANALYTICS_CACHE_STATE, ANALYTICS_LOCK


        original_session_mode = settings.SESSION_MODE
        settings.SESSION_MODE = "ANALYSIS"
        try:
            with ANALYTICS_LOCK:
                ANALYTICS_CACHE_STATE["data"] = []
                ANALYTICS_CACHE_STATE["rows"] = 0
                ANALYTICS_CACHE_STATE["status"] = "IDLE"
                ANALYTICS_CACHE_STATE["scan_id"] = None
                ANALYTICS_CACHE_STATE["started_at"] = None
                ANALYTICS_CACHE_STATE["completed_at"] = None
                ANALYTICS_CACHE_STATE["duration_sec"] = None
                ANALYTICS_CACHE_STATE["error"] = None
                ANALYTICS_CACHE_STATE["processed"] = 0
                ANALYTICS_CACHE_STATE["total"] = 0
                ANALYTICS_CACHE_STATE["progress_pct"] = 0
                ANALYTICS_CACHE_STATE["workers"] = 1

            response = client.get("/api/v1/analytics")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "RUNNING"
            assert data["scan_id"]
            assert data["workers"] == 1
            assert data["progress_pct"] == 0
        finally:
            settings.SESSION_MODE = original_session_mode
            with ANALYTICS_LOCK:
                ANALYTICS_CACHE_STATE["status"] = "IDLE"
                ANALYTICS_CACHE_STATE["scan_id"] = None

    def test_analytics_endpoint_refreshes_stale_live_session_cache_inline(self, monkeypatch):
        """During market hours, yesterday's analytics cache must not be served as live analytics."""
        from routes.analytics import ANALYTICS_CACHE_STATE, ANALYTICS_LOCK, SYSTEM_STATE

        original_session_mode = settings.SESSION_MODE
        original_version = SYSTEM_STATE.get("data_version", 0)

        def fake_run(scan_id):
            with ANALYTICS_LOCK:
                ANALYTICS_CACHE_STATE["data"] = [{"Ticker": "COMI", "Price": 11.0}]
                ANALYTICS_CACHE_STATE["rows"] = 1
                ANALYTICS_CACHE_STATE["status"] = "IDLE"
                ANALYTICS_CACHE_STATE["scan_id"] = scan_id
                ANALYTICS_CACHE_STATE["last_updated"] = "2026-06-02 10:05:00"
                ANALYTICS_CACHE_STATE["completed_at"] = "2026-06-02 10:05:00"
                ANALYTICS_CACHE_STATE["version"] = 22

        monkeypatch.setattr("routes.analytics.run_analytics_task_logic", fake_run)
        monkeypatch.setattr(settings, "is_market_open", lambda: True)
        monkeypatch.setattr("routes.analytics.TimeUtils.today", lambda: datetime.date(2026, 6, 2))
        monkeypatch.setattr(
            "routes.analytics.TimeUtils.now",
            lambda: datetime.datetime(2026, 6, 2, 10, 5, 0),
        )
        settings.SESSION_MODE = "LIVE"
        SYSTEM_STATE["data_version"] = 22

        try:
            with ANALYTICS_LOCK:
                ANALYTICS_CACHE_STATE["data"] = [{"Ticker": "COMI", "Price": 10.0}]
                ANALYTICS_CACHE_STATE["rows"] = 1
                ANALYTICS_CACHE_STATE["status"] = "IDLE"
                ANALYTICS_CACHE_STATE["scan_id"] = None
                ANALYTICS_CACHE_STATE["last_updated"] = "2026-06-01 12:54:19"
                ANALYTICS_CACHE_STATE["completed_at"] = "2026-06-01 12:54:19"
                ANALYTICS_CACHE_STATE["version"] = 22

            response = client.get("/api/v1/analytics")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "IDLE"
            assert data["last_updated"] == "2026-06-02 10:05:00"
            assert data["data"] == [{"Ticker": "COMI", "Price": 11.0}]
        finally:
            settings.SESSION_MODE = original_session_mode
            SYSTEM_STATE["data_version"] = original_version
            with ANALYTICS_LOCK:
                ANALYTICS_CACHE_STATE["status"] = "IDLE"
                ANALYTICS_CACHE_STATE["scan_id"] = None

    def test_analytics_refresh_starts_scan(self, monkeypatch):
        """POST /api/analytics/refresh should start a background scan."""
        # Mock the heavy scan task to prevent hanging
        monkeypatch.setattr("routes.analytics.run_analytics_task_logic", lambda scan_id: None)
        from routes.analytics import ANALYTICS_CACHE_STATE, ANALYTICS_LOCK
        with ANALYTICS_LOCK:
            ANALYTICS_CACHE_STATE["status"] = "IDLE"

        response = client.post("/api/v1/analytics/refresh")
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert data["status"] == "RUNNING"

        # Cleanup
        with ANALYTICS_LOCK:
            ANALYTICS_CACHE_STATE["status"] = "IDLE"

    def test_analytics_refresh_rejects_if_running(self):
        """POST /api/analytics/refresh should reject if already running."""
        from routes.analytics import ANALYTICS_CACHE_STATE, ANALYTICS_LOCK
        with ANALYTICS_LOCK:
            ANALYTICS_CACHE_STATE["status"] = "RUNNING"
            ANALYTICS_CACHE_STATE["scan_id"] = "test123"

        response = client.post("/api/v1/analytics/refresh")
        assert response.status_code == 200
        data = response.json()
        assert "already in progress" in data["message"].lower()

        # Cleanup
        with ANALYTICS_LOCK:
            ANALYTICS_CACHE_STATE["status"] = "IDLE"


class TestAnalyticsSnapshotReuse:
    """Tests for shared analytics snapshot reuse outside the route handler."""

    def test_ensure_analytics_rows_reuses_fresh_cache_without_recompute(self, monkeypatch):
        """Fresh analytics rows should be reused without rerunning the scan."""
        from routes.analytics import ensure_analytics_rows, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK

        rerun_calls = []
        monkeypatch.setattr("routes.analytics._current_data_version", lambda: 7)
        monkeypatch.setattr("routes.analytics.run_analytics_task_logic", lambda scan_id: rerun_calls.append(scan_id))

        with ANALYTICS_LOCK:
            ANALYTICS_CACHE_STATE["data"] = [{"Ticker": "COMI", "Resistance_20D": 80.0}]
            ANALYTICS_CACHE_STATE["rows"] = 1
            ANALYTICS_CACHE_STATE["version"] = 7
            ANALYTICS_CACHE_STATE["status"] = "IDLE"
            ANALYTICS_CACHE_STATE["cache_source"] = "memory"

        rows = ensure_analytics_rows(scan_id="shared_cache_001")

        assert rows == [{"Ticker": "COMI", "Resistance_20D": 80.0}]
        assert rerun_calls == []

    def test_ensure_analytics_rows_runs_scan_when_cache_missing(self, monkeypatch):
        """Missing analytics rows should be materialized once and returned."""
        from routes.analytics import ensure_analytics_rows, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK

        monkeypatch.setattr("routes.analytics._current_data_version", lambda: 9)

        def fake_run(scan_id):
            with ANALYTICS_LOCK:
                ANALYTICS_CACHE_STATE["data"] = [{"Ticker": "FWRY", "Resistance_20D": 12.5}]
                ANALYTICS_CACHE_STATE["rows"] = 1
                ANALYTICS_CACHE_STATE["version"] = 9
                ANALYTICS_CACHE_STATE["status"] = "IDLE"
                ANALYTICS_CACHE_STATE["cache_source"] = "memory"

        monkeypatch.setattr("routes.analytics.run_analytics_task_logic", fake_run)

        with ANALYTICS_LOCK:
            ANALYTICS_CACHE_STATE["data"] = []
            ANALYTICS_CACHE_STATE["rows"] = 0
            ANALYTICS_CACHE_STATE["version"] = -1
            ANALYTICS_CACHE_STATE["status"] = "IDLE"
            ANALYTICS_CACHE_STATE["cache_source"] = "memory"

        rows = ensure_analytics_rows(scan_id="shared_cache_002")

        assert rows == [{"Ticker": "FWRY", "Resistance_20D": 12.5}]

    def test_ensure_analytics_rows_prefers_stale_rows_over_recompute_when_allowed(self, monkeypatch):
        """Stale rows can be reused directly for warm startup callers like live feed."""
        from routes.analytics import ensure_analytics_rows, ANALYTICS_CACHE_STATE, ANALYTICS_LOCK

        rerun_calls = []
        monkeypatch.setattr("routes.analytics._current_data_version", lambda: 12)
        monkeypatch.setattr("routes.analytics._load_analytics_cache_from_disk", lambda: None)
        monkeypatch.setattr("routes.analytics.run_analytics_task_logic", lambda scan_id: rerun_calls.append(scan_id))

        with ANALYTICS_LOCK:
            ANALYTICS_CACHE_STATE["data"] = [{"Ticker": "HRHO", "Resistance_20D": 44.0}]
            ANALYTICS_CACHE_STATE["rows"] = 1
            ANALYTICS_CACHE_STATE["version"] = 11
            ANALYTICS_CACHE_STATE["status"] = "IDLE"
            ANALYTICS_CACHE_STATE["cache_source"] = "memory"

        rows = ensure_analytics_rows(scan_id="shared_cache_003", allow_stale=True)

        assert rows == [{"Ticker": "HRHO", "Resistance_20D": 44.0}]
        assert rerun_calls == []


# =============================================================================
# SMART MONEY & MONTE CARLO
# =============================================================================

class TestAdvancedAnalytics:
    """Tests for smart money, Monte Carlo, and Ragnarok endpoints."""

    def test_smart_money_success(self, monkeypatch):
        """GET /api/smart-money should return whale signals."""
        mock_df = pd.DataFrame([
            {"Ticker": "COMI", "Signal": "ACCUMULATION", "Strength": 10.5},
        ])
        monkeypatch.setattr("routes.analytics.SmartMoneyTracker.scan_for_whales", lambda: mock_df)
        response = client.get("/api/v1/smart-money")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 1

    def test_smart_money_empty(self, monkeypatch):
        """GET /api/smart-money should return empty list when no whales."""
        monkeypatch.setattr("routes.analytics.SmartMoneyTracker.scan_for_whales", lambda: pd.DataFrame())
        response = client.get("/api/v1/smart-money")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"] == []

    def test_ragnarok_no_tickers(self):
        """POST /api/ragnarok should return error when no tickers."""
        # Clear open positions and provide empty tickers
        response = client.post("/api/v1/ragnarok", json={
            "iterations": 100,
            "days": 10,
            "tickers": [],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "No portfolio tickers" in data["message"]

    def test_ragnarok_with_tickers(self, monkeypatch):
        """POST /api/ragnarok should return simulation results."""
        mock_result = {"ruin_probability": 0.05, "median_drawdown": 12.0}
        monkeypatch.setattr("routes.analytics.RagnarokSimulator.run_ragnarok_simulation", lambda **kw: mock_result)
        response = client.post("/api/v1/ragnarok", json={
            "iterations": 100,
            "days": 10,
            "tickers": ["COMI", "FWRY"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_seasonality_market(self, monkeypatch):
        """GET /api/seasonality/market should return market-wide seasonality."""
        monkeypatch.setattr("routes.analytics.Helheim.get_market_seasonality", lambda: {"jan": 5.0})
        response = client.get("/api/v1/seasonality/market")
        assert response.status_code == 200
