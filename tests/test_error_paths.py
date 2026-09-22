"""
ERROR PATH TESTS
================
Tests for error handling across all route modules — bad inputs,
missing resources, internal errors.
"""

from core.settings import settings
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api import app
from database import Portfolio, Position

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# SETTINGS ERROR PATHS
# =============================================================================

class TestSettingsErrors:
    """Error paths in settings routes."""

    def test_settings_post_internal_error(self, monkeypatch):
        """POST /api/settings should return 500 on unexpected exception."""
        monkeypatch.setattr(
            "routes.settings.settings.update",
            MagicMock(side_effect=RuntimeError("Disk full")),
        )
        response = client.post("/api/v1/settings", json={"SL_PCT": 3.0})
        assert response.status_code == 500
        assert "Disk full" in response.json()["detail"]

    def test_telegram_test_alert_failure(self, monkeypatch):
        """POST /api/telegram/test should return error on send failure."""
        monkeypatch.setattr(
            "routes.settings.TelegramBot_Alerts.send_message",
            lambda msg: {"ok": False, "description": "Unauthorized"},
        )
        monkeypatch.setattr(
            "routes.settings.TelegramBot_Alerts.send_message",
            lambda msg, token=None, chat_id=None: {"ok": False, "description": "Unauthorized"},
        )
        response = client.post("/api/v1/telegram/test")
        assert response.status_code == 400
        assert "telegram error" in response.json()["detail"].lower()
        assert "unauthorized" in response.json()["detail"].lower()


# =============================================================================
# PORTFOLIO ERROR PATHS
# =============================================================================

class TestPortfolioErrors:
    """Error paths in portfolio routes."""

    def test_close_nonexistent_position(self):
        """POST /api/portfolio/close for non-existent ticker returns gracefully."""
        p = Portfolio.create(name="Error Test Portfolio", type="USER")
        response = client.post("/api/v1/portfolio/close", json={
            "portfolio_id": p.id,
            "ticker": "PHANTOM",
            "price": 10.0,
        })
        # TreasuryLedger.melt_gold handles missing position gracefully (returns 200 with error msg)
        assert response.status_code == 400

    def test_delete_nonexistent_portfolio(self):
        """DELETE /api/portfolios/{id} for non-existent ID should return error."""
        response = client.delete("/api/v1/portfolios/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# =============================================================================
# DATA ERROR PATHS
# =============================================================================

class TestDataErrors:
    """Error paths in data routes."""

    def test_data_freshness_invalid_date_format(self):
        """GET /api/data/freshness with bad date should return 400."""
        response = client.get("/api/v1/data/freshness", params={
            "run_date": "not-a-date",
            "scan_type": "DAILY",
        })
        assert response.status_code == 400
        assert "YYYY-MM-DD" in response.json()["detail"]

    def test_ticker_data_returns_404_for_unknown(self, monkeypatch):
        """GET /api/data/ticker/{ticker} for unknown ticker should return 404."""
        monkeypatch.setattr(
            "routes.data.DataManager.get_stock_data",
            lambda ticker, **kwargs: None,
        )
        response = client.get("/api/v1/data/ticker/NONEXISTENT")
        assert response.status_code == 404


# =============================================================================
# SCANNER ERROR PATHS
# =============================================================================

class TestScannerErrors:
    """Error paths in scanner routes."""

    def test_scanner_run_deprecated_detail(self):
        """GET /api/scanner/run should include migration message."""
        response = client.get("/api/v1/scanner/run")
        assert response.status_code == 400
        assert "POST" in response.json()["detail"]


# =============================================================================
# STRATEGY ERROR PATHS
# =============================================================================

class TestStrategyErrors:
    """Error paths in strategy routes."""

    def test_apply_empty_manual_payload(self):
        """POST /api/strategy/apply with only manual=true but no keys should fail."""
        response = client.post("/api/v1/strategy/apply", json={"manual": True})
        assert response.status_code == 400
        assert "No params provided" in response.json()["detail"]

    def test_backtest_bad_capital(self, monkeypatch):
        """POST /api/strategy/backtest with non-numeric capital should return error."""
        monkeypatch.setattr(
            "routes.strategy.PortfolioSimulator.run_simulation",
            MagicMock(side_effect=ValueError("Invalid capital")),
        )
        response = client.post("/api/v1/strategy/backtest", json={
            "capital": "not_a_number",
        })
        assert response.status_code == 400
        assert "capital must be numeric" in response.json()["detail"]
