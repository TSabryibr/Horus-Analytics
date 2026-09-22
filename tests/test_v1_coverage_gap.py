"""
V1 API COVERAGE GAP TESTS
==========================
Filling the gaps for previously undocumented or lightly tested V1 endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api import app

client = TestClient(app, raise_server_exceptions=False)

class TestV1CoverageGap:
    """Tests for endpoints identified as coverage gaps in Phase 7/8."""

    # =========================================================================
    # DATA SYNC ENDPOINTS
    # =========================================================================

    def test_get_data_tickers(self):
        """GET /api/v1/data/tickers should return list of available tickers."""
        response = client.get("/api/v1/data/tickers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_sync_status(self):
        """GET /api/v1/data/sync/status should return background sync state."""
        response = client.get("/api/v1/data/sync/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_start_sync_success(self, monkeypatch):
        """POST /api/v1/data/sync/start should trigger manual sync (auth required)."""
        # Mock background task and auth
        monkeypatch.setattr("core.auth.get_api_key", lambda: "mock-key")
        monkeypatch.setattr("routes.data._run_data_sync_task", lambda days: None)
        
        response = client.post("/api/v1/data/sync/start", headers={"X-API-Key": "mock-key"})
        
        # If already running it returns started: False
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_sync_completion_wakes_pending_ai_daily_report(self, monkeypatch):
        """Manual data sync completion should retry a pending AI daily report."""
        import routes.data

        synced = []
        signal_attempts = []
        report_attempts = []
        states = []
        cache_invalidations = []

        monkeypatch.setattr(
            "routes.data.sync_all",
            lambda force_history_recent_days: synced.append(force_history_recent_days),
        )
        monkeypatch.setattr(
            "data_engine.freshness.invalidate_freshness_cache",
            lambda: cache_invalidations.append(True),
        )
        monkeypatch.setattr(
            "core.scheduling.maybe_run_pending_daily_signal_after_data_update",
            lambda: signal_attempts.append(True) or {"status": "completed"},
        )
        monkeypatch.setattr(
            "core.scheduling.maybe_dispatch_pending_ai_daily_report_after_data_update",
            lambda: report_attempts.append(True) or {"status": "sent"},
        )
        monkeypatch.setattr("routes.data._set_data_sync_state", lambda **updates: states.append(updates))

        routes.data._run_data_sync_task(force_history_recent_days=3)

        assert synced == [3]
        assert cache_invalidations == [True]
        assert signal_attempts == [True]
        assert report_attempts == [True]
        assert states[-1]["status"] == "COMPLETED"

    # =========================================================================
    # STRATEGY METRICS ENDPOINTS
    # =========================================================================

    def test_get_strategy_health(self):
        """GET /api/v1/strategy/health should return accuracy check results."""
        response = client.get("/api/v1/strategy/health")
        assert response.status_code == 200
        data = response.json()
        assert "win_rate" in data

    # =========================================================================
    # SYSTEM AUDIT ENDPOINTS
    # =========================================================================

    def test_get_system_audit(self, monkeypatch):
        """GET /api/v1/system/audit should return institutional logs (mocked auth)."""
        monkeypatch.setattr("core.auth.get_api_key", lambda: "mock-key")
        monkeypatch.setattr("routes.audit.get_recent_logs", lambda limit, category: [{"id": 1, "msg": "test"}])
        
        response = client.get("/api/v1/system/audit", headers={"X-API-Key": "mock-key"})
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert len(data["logs"]) > 0

    # =========================================================================
    # ARBITRAGE EXECUTION ENDPOINTS
    # =========================================================================

    def test_execute_arbitrage_failure_no_auth(self, monkeypatch):
        """POST /api/v1/execute-arbitrage should fail without valid T212 env vars."""
        monkeypatch.setenv("T212_API_KEY", "")
        monkeypatch.setenv("T212_API_SECRET", "")
        # Mock internal auth specifically for this test
        monkeypatch.setattr("core.auth.get_api_key", lambda: "mock-key")
        
        payload = {
            "leader": "COMI",
            "follower": "HRHO",
            "type": "Positive",
            "z_score": 2.5
        }
        response = client.post("/api/v1/execute-arbitrage", json=payload, headers={"X-API-Key": "mock-key"})
        assert response.status_code == 401
        assert "credentials missing" in response.json()["detail"].lower()

    @patch("requests.post")
    def test_execute_arbitrage_mocked_success(self, mock_post, monkeypatch):
        """POST /api/v1/execute-arbitrage should succeed with mocked backend."""
        monkeypatch.setenv("T212_API_KEY", "test-key")
        monkeypatch.setenv("T212_API_SECRET", "test-secret")
        monkeypatch.setattr("core.auth.get_api_key", lambda: "mock-key")
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"orderId": "test-123"}
        mock_post.return_value = mock_response
        
        payload = {
            "leader": "COMI",
            "follower": "HRHO",
            "type": "Positive",
            "z_score": 2.5
        }
        response = client.post("/api/v1/execute-arbitrage", json=payload, headers={"X-API-Key": "mock-key"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
