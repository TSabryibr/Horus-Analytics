"""
LIVE FEED & SIMULATION ENDPOINT TESTS
=======================================
Tests for routes/live.py and routes/simulation.py — live feed
start/stop/status, time-travel simulation lifecycle.
"""

from core.settings import settings
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api import app

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# LIVE FEED ENDPOINTS
# =============================================================================

class TestLiveFeedEndpoints:
    """Tests for live market data feed management."""

    def test_live_start_market_closed(self, monkeypatch):
        """POST /api/live/start should return market_closed when outside hours."""
        monkeypatch.setattr("routes.live.settings.is_market_open", lambda: False)
        monkeypatch.setattr("routes.live.LiveFeedManager.is_running", lambda: False)
        response = client.post("/api/v1/live/start")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "market_closed"
        assert data["market_open"] is False

    def test_live_start_already_running(self, monkeypatch):
        """POST /api/live/start should return already_running."""
        monkeypatch.setattr("routes.live.settings.is_market_open", lambda: True)
        monkeypatch.setattr("routes.live.LiveFeedManager.is_running", lambda: True)
        response = client.post("/api/v1/live/start")
        assert response.status_code == 200
        assert response.json()["status"] == "already_running"

    def test_live_start_success(self, monkeypatch):
        """POST /api/live/start should start monitoring."""
        monkeypatch.setattr("routes.live.settings.is_market_open", lambda: True)
        call_count = {"n": 0}
        def _is_running():
            call_count["n"] += 1
            # First call (guard check) returns False, second call (after start) returns True
            return call_count["n"] > 1
        monkeypatch.setattr("routes.live.LiveFeedManager.is_running", _is_running)
        monkeypatch.setattr("routes.live.LiveFeedManager.start_monitoring", lambda: None)
        response = client.post("/api/v1/live/start")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"

    def test_live_stop(self, monkeypatch):
        """POST /api/live/stop should stop monitoring."""
        monkeypatch.setattr("routes.live.LiveFeedManager.stop_monitoring", lambda: None)
        monkeypatch.setattr("routes.live.LiveFeedManager.is_running", lambda: False)
        monkeypatch.setattr("routes.live.settings.is_market_open", lambda: False)
        response = client.post("/api/v1/live/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
        assert data["running"] is False

    def test_live_status_full(self, monkeypatch):
        """GET /api/live/status should return comprehensive status."""
        monkeypatch.setattr("routes.live.settings.is_market_open", lambda: True)
        monkeypatch.setattr("routes.live.LiveFeedManager.is_running", lambda: True)
        monkeypatch.setattr("routes.live.LiveFeedManager.get_last_update_time", lambda: "2026-02-19 14:00:00")
        monkeypatch.setattr("routes.live.LiveFeedManager.get_session_stats", lambda: {"tickers": 30, "updates": 150})
        response = client.get("/api/v1/live/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["running"] is True
        assert data["market_open"] is True
        assert "hours" in data
        assert "stats" in data


# =============================================================================
# SIMULATION (TIME TRAVEL) ENDPOINTS
# =============================================================================

class TestSimulationEndpoints:
    """Tests for time travel simulation lifecycle."""

    def test_simulation_start(self, monkeypatch):
        """POST /api/simulate/start should activate simulation mode."""
        set_calls = []
        monkeypatch.setattr("routes.simulation.TimeUtils.set_simulation", lambda dt: set_calls.append(dt))
        monkeypatch.setattr("routes.shared.purge_all_caches", lambda: None)

        response = client.post("/api/v1/simulate/start", json={"date": "2025-06-15"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["date"] == "2025-06-15"
        assert len(set_calls) == 1

    def test_simulation_start_no_date(self):
        """POST /api/simulate/start without date should return 400."""
        response = client.post("/api/v1/simulate/start", json={})
        assert response.status_code == 400
        assert "Date required" in response.json()["detail"]

    def test_simulation_start_invalid_date(self):
        """POST /api/simulate/start with bad date should return 400."""
        response = client.post("/api/v1/simulate/start", json={"date": "not-a-date"})
        assert response.status_code == 400
        assert "Invalid format" in response.json()["detail"]

    def test_simulation_stop(self, monkeypatch):
        """POST /api/simulate/stop should deactivate simulation."""
        monkeypatch.setattr("routes.simulation.TimeUtils.clear_simulation", lambda: None)
        monkeypatch.setattr("routes.shared.purge_all_caches", lambda: None)

        response = client.post("/api/v1/simulate/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "live"

    def test_simulation_status_inactive(self, monkeypatch):
        """GET /api/simulation/status when not simulating."""
        monkeypatch.setattr("routes.simulation.TimeUtils.is_simulating", lambda: False)
        response = client.get("/api/v1/simulation/status")
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False
        assert data["simulating"] is False
        assert data["date"] is None

    def test_simulation_status_active(self, monkeypatch):
        """GET /api/simulation/status when simulating."""
        import datetime
        monkeypatch.setattr("routes.simulation.TimeUtils.is_simulating", lambda: True)
        monkeypatch.setattr("routes.simulation.TimeUtils.get_simulation_date", lambda: datetime.datetime(2025, 6, 15))
        response = client.get("/api/v1/simulation/status")
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is True
        assert data["date"] == "2025-06-15"
