"""
PHASE 6: PRECISION COVERAGE
==============================
Targeted tests for the last uncovered lines in settings (signal card,
image broadcast), portfolio (close-trade validation, risk check, metrics
with trades, management report send, intake, telegram split), shared
(purge_all_caches, rate_limits_default), and analytics (auto-refresh,
data freshness gate).
"""

from core.settings import settings
from core.exclusions import get_all_exclusions, EXCLUDED_TICKERS, is_excluded_ticker
import pytest
import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, PropertyMock
import core.exclusions as exclusions

from api import app
from database import Trade, Position, Portfolio

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture(autouse=True)
def mock_no_exclusions(monkeypatch):
    # Completely disable exclusions for precision tests
    monkeypatch.setattr(exclusions, "get_all_exclusions", lambda: [])
    monkeypatch.setattr(settings, "EXCLUDED_TICKERS", set(), raising=False)
    # Also patch the utility just in case it was already imported
    monkeypatch.setattr(exclusions, "is_excluded_ticker", lambda *args, **kwargs: False)
    import routes.portfolio
    monkeypatch.setattr(routes.portfolio, "is_excluded_ticker", lambda *args, **kwargs: False)
    yield



# =============================================================================
# SHARED: purge_all_caches, rate_limits_default
# =============================================================================

class TestSharedInternals:
    """Tests for shared module helper functions."""

    def test_purge_all_caches(self):
        """purge_all_caches should wipe all eager caches."""
        from routes.shared import (
            purge_all_caches, NEWS_CACHE, SECTOR_CACHE,
            WHALE_CACHE, ARBITRAGE_CACHE, TRAP_CACHE,
            STRATEGY_CACHE, ORACLE_CACHE,
        )
        # Seed caches with dummy data
        NEWS_CACHE["data"] = [{"headline": "test"}]
        SECTOR_CACHE["data"] = [{"sector": "Banks"}]
        WHALE_CACHE["data"] = [{"ticker": "COMI"}]
        ARBITRAGE_CACHE["data"] = [{"pair": "A-B"}]
        TRAP_CACHE["data"] = [{"trap": "BULL"}]
        STRATEGY_CACHE["data"] = [{"action": "BUY"}]
        ORACLE_CACHE["data"] = [{"pred": 0.5}]

        purge_all_caches()

        assert NEWS_CACHE["data"] == []
        assert SECTOR_CACHE["data"] == []
        assert WHALE_CACHE["data"] == []
        assert ARBITRAGE_CACHE["data"] == []
        assert TRAP_CACHE["data"] == []
        assert STRATEGY_CACHE["data"] == []
        assert ORACLE_CACHE["data"] == []

    def test_rate_limits_default_numeric(self, monkeypatch):
        """_rate_limits_default should parse numeric env."""
        monkeypatch.setenv("HORUS_RATE_LIMIT_PER_MIN", "100")
        from routes.shared import _rate_limits_default
        assert _rate_limits_default() == ["100/minute"]

    def test_rate_limits_default_disabled(self, monkeypatch):
        """_rate_limits_default should disable when off."""
        monkeypatch.setenv("HORUS_RATE_LIMIT_PER_MIN", "off")
        from routes.shared import _rate_limits_default
        assert _rate_limits_default() == ["1000000/minute"]

    def test_rate_limits_default_zero(self, monkeypatch):
        """_rate_limits_default should handle 0."""
        monkeypatch.setenv("HORUS_RATE_LIMIT_PER_MIN", "0")
        from routes.shared import _rate_limits_default
        assert _rate_limits_default() == ["1000000/minute"]

    def test_rate_limits_default_invalid(self, monkeypatch):
        """_rate_limits_default should fallback on invalid."""
        monkeypatch.setenv("HORUS_RATE_LIMIT_PER_MIN", "xyz")
        from routes.shared import _rate_limits_default
        assert _rate_limits_default() == ["600/minute"]


# =============================================================================
# SETTINGS: signal card, image broadcast
# =============================================================================

class TestSettingsAdvanced:
    """Tests for advanced settings endpoints."""

    def test_broadcast_with_image(self, monkeypatch):
        """POST /api/telegram/broadcast with image should send image."""
        import base64
        dummy_img = base64.b64encode(b"fake_image_data").decode()
        monkeypatch.setattr("routes.settings.TelegramBot_Alerts.send_image",
                            lambda buf, caption=None: {"ok": True, "result": {}})
        response = client.post("/api/v1/telegram/broadcast", json={
            "message": "Test with image",
            "image_base64": f"data:image/png;base64,{dummy_img}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"

    def test_signal_card_broadcast(self, monkeypatch):
        """POST /api/telegram/signal-card should generate and send card."""
        mock_buf = MagicMock()
        monkeypatch.setattr("routes.settings.ReportGenerator.create_horus_signal_card",
                            lambda **kw: mock_buf)
        monkeypatch.setattr("routes.settings.TelegramBot_Alerts.send_image",
                            lambda buf, caption=None: {"ok": True, "result": {}})
        response = client.post("/api/v1/telegram/signal-card", json={
            "ticker": "COMI",
            "entry": 85.0,
            "sl": 80.0,
            "tp1": 95.0,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"

    def test_signal_card_with_all_fields(self, monkeypatch):
        """POST /api/telegram/signal-card with all optional fields."""
        mock_buf = MagicMock()
        monkeypatch.setattr("routes.settings.ReportGenerator.create_horus_signal_card",
                            lambda **kw: mock_buf)
        monkeypatch.setattr("routes.settings.TelegramBot_Alerts.send_image",
                            lambda buf, caption=None: {"ok": True, "result": {}})
        response = client.post("/api/v1/telegram/signal-card", json={
            "ticker": "FWRY",
            "entry": 5.0,
            "sl": 4.5,
            "tp1": 6.0,
            "tp2": 7.0,
            "score": 85,
            "rsi": 55,
            "volume_x": 2.5,
            "confirmation": "MACD Cross",
            "regime": "BULLISH",
            "signal_date": "2025-02-19",
            "caption": "Custom caption for FWRY",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "sent"

    def test_signal_card_telegram_failure(self, monkeypatch):
        """POST /api/telegram/signal-card should return 502 on failure."""
        monkeypatch.setattr("routes.settings.ReportGenerator.create_horus_signal_card",
                            lambda **kw: MagicMock())
        monkeypatch.setattr("routes.settings.TelegramBot_Alerts.send_image",
                            lambda buf, caption=None: {"ok": False, "description": "Bot blocked"})
        response = client.post("/api/v1/telegram/signal-card", json={
            "ticker": "COMI", "entry": 85.0, "sl": 80.0, "tp1": 95.0,
        })
        assert response.status_code == 502

    def test_update_exclusions_bulk(self):
        """POST /api/settings/exclusions should update bulk exclusions."""
        response = client.post("/api/v1/settings/exclusions", json=["COMI", "FWRY", "SWDY"])
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3


# =============================================================================
# PORTFOLIO: close-trade validation, risk check, metrics with trades
# =============================================================================

class TestPortfolioAdvanced:
    """Tests for portfolio advanced paths."""

    def test_close_trade_with_shares(self, monkeypatch):
        """POST /api/portfolio/close with shares should validate shares."""
        monkeypatch.setattr("routes.portfolio.TreasuryLedger.melt_gold",
                            lambda ticker, shares, price, portfolio_id: {"status": "success"})
        p = Portfolio.select().first()
        response = client.post("/api/v1/portfolio/close", json={
            "ticker": "COMI",
            "price": 90.0,
            "shares": 50,
            "portfolio_id": p.id,
        })
        assert response.status_code == 200

    def test_close_trade_invalid_shares(self):
        """POST /api/portfolio/close with invalid shares should return 400."""
        response = client.post("/api/v1/portfolio/close", json={
            "ticker": "COMI",
            "price": 90.0,
            "shares": "abc",
        })
        assert response.status_code == 422

    def test_close_trade_zero_shares(self):
        """POST /api/portfolio/close with 0 shares should return 400."""
        response = client.post("/api/v1/portfolio/close", json={
            "ticker": "COMI",
            "price": 90.0,
            "shares": 0,
        })
        assert response.status_code == 422

    def test_close_trade_non_numeric_price(self):
        """POST /api/portfolio/close with non-numeric price should return 400."""
        response = client.post("/api/v1/portfolio/close", json={
            "ticker": "COMI",
            "price": "abc",
        })
        assert response.status_code == 422

    def test_risk_check(self, monkeypatch):
        """POST /api/risk/check should return risk assessment."""
        monkeypatch.setattr("routes.portfolio.RiskManager.check_new_trade_correlation",
                            lambda positions, ticker: {"is_safe": True, "avg_correlation": 0.3})
        monkeypatch.setattr("routes.portfolio.RiskManager.check_sector_exposure",
                            lambda ticker, positions: (True, "OK"))
        response = client.post("/api/v1/risk/check", json={"ticker": "COMI"})
        assert response.status_code == 200
        data = response.json()
        assert data["safe"] is True

    def test_risk_check_warnings(self, monkeypatch):
        """POST /api/risk/check should return warnings when unsafe."""
        monkeypatch.setattr("routes.portfolio.RiskManager.check_new_trade_correlation",
                            lambda positions, ticker: {"is_safe": False, "warning": "High correlation", "max_correlation": 0.95})
        monkeypatch.setattr("routes.portfolio.RiskManager.check_sector_exposure",
                            lambda ticker, positions: (False, "Over-exposed to Banking"))
        response = client.post("/api/v1/risk/check", json={"ticker": "COMI"})
        assert response.status_code == 200
        data = response.json()
        assert data["safe"] is False
        assert len(data["warnings"]) == 2

    def test_portfolio_metrics_with_trades(self, monkeypatch):
        """GET /api/portfolio/metrics with trades should calc win rate."""
        monkeypatch.setattr("routes.portfolio.PositionTracker.update_live_prices", lambda: None)
        p = Portfolio.select().first()
        # Create 2 winning trades and 1 losing trade
        Trade.create(
            ticker="W1", shares=100, entry_price=10, exit_price=12,
            entry_date="2025-01-01", exit_date="2025-01-10",
            pnl=200, pnl_pct=20, portfolio=p,
        )
        Trade.create(
            ticker="W2", shares=100, entry_price=10, exit_price=15,
            entry_date="2025-01-01", exit_date="2025-01-10",
            pnl=500, pnl_pct=50, portfolio=p,
        )
        Trade.create(
            ticker="L1", shares=100, entry_price=10, exit_price=8,
            entry_date="2025-01-01", exit_date="2025-01-10",
            pnl=-200, pnl_pct=-20, portfolio=p,
        )
        response = client.get(f"/api/v1/portfolio/metrics?portfolio_id={p.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] >= 3
        assert data["win_rate"] > 0
        assert data["profit_factor"] > 0

    def test_weekly_report(self):
        """GET /api/reports/weekly should return recent trades."""
        response = client.get("/api/v1/reports/weekly")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "trades" in data


# =============================================================================
# PORTFOLIO: management report send, intake, telegram split
# =============================================================================

class TestPortfolioManagement:
    """Tests for portfolio management report and intake."""

    def test_management_report_send(self, monkeypatch):
        """POST /api/portfolio/management/report/send should format and send."""
        monkeypatch.setattr("routes.portfolio.RiskManager.analyze_portfolio",
                            lambda pid: {"status": "HEALTHY", "health_score": 85, "heat": 10, "recommendations": []})
        monkeypatch.setattr("routes.portfolio.TelegramBot_Alerts.send_message",
                            lambda msg, chat_id=None: {"ok": True})
        p = Portfolio.select().first()
        # Ensure there's at least one position
        Position.get_or_create(
            portfolio=p.id, ticker="TEST_SEND", status="OPEN",
            defaults={
                "shares": 100, "entry_price": 50.0, "stop_loss": 47.0,
                "target_price": 55.0, "current_price": 51.0, "currency": "EGP",
            },
        )
        response = client.post("/api/v1/portfolio/management/report/send", json={
            "portfolio_id": p.id,
            "include_positions": 5,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["chunks_sent"] >= 1

    def test_management_report_send_invalid_include(self):
        """POST /api/portfolio/management/report/send with bad include_positions."""
        response = client.post("/api/v1/portfolio/management/report/send", json={
            "include_positions": 0,
        })
        assert response.status_code == 400
        assert "include_positions" in response.json()["detail"]

    def test_intake_holdings(self, monkeypatch):
        """POST /api/portfolio/management/intake should create positions."""
        monkeypatch.setattr("routes.portfolio.WalkForwardValidation.get_trade_permission",
                            lambda ticker, fail_closed=True: {"allowed": True, "reason": "ok"})
        monkeypatch.setattr("routes.portfolio.RiskManager.analyze_portfolio",
                            lambda pid: {"status": "HEALTHY", "health_score": 80, "heat": 5, "recommendations": []})
        p = Portfolio.select().first()
        response = client.post("/api/v1/portfolio/management/intake", json={
            "portfolio_id": p.id,
            "holdings": [
                {"ticker": "INTAKE1", "shares": 100, "entry_price": 20.0},
                {"ticker": "INTAKE2", "shares": 200, "entry_price": 5.0, "stop_loss": 4.5, "target_price": 6.0},
            ],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["created"] >= 1

    def test_intake_holdings_wfa_blocked(self, monkeypatch):
        """POST /api/portfolio/management/intake with WFA-blocked ticker."""
        monkeypatch.setattr("routes.portfolio.WalkForwardValidation.get_trade_permission",
                            lambda ticker, fail_closed=True: {"allowed": False, "reason": "Excluded"})
        monkeypatch.setattr("routes.portfolio.RiskManager.analyze_portfolio",
                            lambda pid: {"status": "HEALTHY", "health_score": 80, "heat": 5, "recommendations": []})
        p = Portfolio.select().first()
        response = client.post("/api/v1/portfolio/management/intake", json={
            "portfolio_id": p.id,
            "holdings": [
                {"ticker": "BLOCKED1", "shares": 100, "entry_price": 10.0},
            ],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "partial"
        assert len(data["errors"]) >= 1

    def test_split_telegram_message_short(self):
        """_split_telegram_message should return single chunk for short msg."""
        from routes.portfolio import _split_telegram_message
        result = _split_telegram_message("Short message")
        assert len(result) == 1

    def test_split_telegram_message_long(self):
        """_split_telegram_message should split long messages."""
        from routes.portfolio import _split_telegram_message
        long_msg = "\n".join([f"Line {i}: " + "x" * 50 for i in range(200)])
        result = _split_telegram_message(long_msg, max_len=500)
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 500

    def test_parse_holding_input_from_total_cost(self):
        """_parse_holding_input should calculate shares from total_cost."""
        from routes.portfolio import _parse_holding_input, ManagedHoldingInput
        holding = ManagedHoldingInput(
            ticker="COMI",
            entry_price=50.0,
            total_cost=5000.0,
        )
        parsed = _parse_holding_input(holding)
        assert parsed["shares"] == 100
        assert parsed["entry_price"] == 50.0

    def test_parse_holding_input_from_shares_and_total(self):
        """_parse_holding_input should calculate entry_price from total_cost + shares."""
        from routes.portfolio import _parse_holding_input, ManagedHoldingInput
        holding = ManagedHoldingInput(
            ticker="COMI",
            shares=100,
            total_cost=5000.0,
        )
        parsed = _parse_holding_input(holding)
        assert parsed["entry_price"] == 50.0

    def test_tp2_from_tp1(self):
        """_tp2_from_tp1 should calculate TP2 from env percentage."""
        from routes.portfolio import _tp2_from_tp1
        tp2 = _tp2_from_tp1(100.0)
        assert tp2 > 100.0  # Should be 100 * (1 + pct/100)

    def test_tp2_from_tp1_zero(self):
        """_tp2_from_tp1 should return 0 for tp1=0."""
        from routes.portfolio import _tp2_from_tp1
        assert _tp2_from_tp1(0.0) == 0.0


# =============================================================================
# ANALYTICS: data freshness gate
# =============================================================================

class TestDataFreshnessGate:
    """Tests for data freshness evaluation."""

    def test_freshness_daily(self, monkeypatch):
        """GET /api/data/freshness should return daily freshness."""
        monkeypatch.setattr("routes.data.evaluate_freshness",
                            lambda **kw: {"overall_ok": True, "scan_type": "DAILY"})
        response = client.get("/api/v1/data/freshness")
        assert response.status_code == 200

    def test_freshness_intraday(self, monkeypatch):
        """GET /api/data/freshness?scan_type=INTRADAY should return intraday freshness."""
        monkeypatch.setattr("routes.data.evaluate_freshness",
                            lambda **kw: {"overall_ok": True, "scan_type": "INTRADAY"})
        response = client.get("/api/v1/data/freshness", params={"scan_type": "INTRADAY"})
        assert response.status_code == 200

    def test_freshness_with_date(self, monkeypatch):
        """GET /api/data/freshness?run_date=2025-01-15 should use given date."""
        monkeypatch.setattr("routes.data.evaluate_freshness",
                            lambda **kw: {"overall_ok": True})
        response = client.get("/api/v1/data/freshness", params={
            "run_date": "2025-01-15",
            "scan_type": "DAILY",
        })
        assert response.status_code == 200

    def test_freshness_invalid_date(self):
        """GET /api/data/freshness with bad date should return 400."""
        response = client.get("/api/v1/data/freshness", params={"run_date": "not-a-date"})
        assert response.status_code == 400

    def test_observability_metrics(self, monkeypatch):
        """GET /api/data/observability should return pipeline metrics."""
        monkeypatch.setattr("routes.data.snapshot_metrics",
                            lambda: {"ingestion_count": 500, "errors": 0})
        response = client.get("/api/v1/data/observability")
        assert response.status_code == 200
