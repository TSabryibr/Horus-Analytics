"""
PORTFOLIO OPERATIONS TESTS
==========================
Tests for routes/portfolio.py — trade lifecycle, portfolio CRUD,
metrics, equity curve.
"""

from core.exclusions import get_all_exclusions
import pytest
from fastapi.testclient import TestClient

from api import app
from database import Portfolio, Position, Trade

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# TRADE LIFECYCLE
# =============================================================================

class TestTradeLifecycle:
    """Tests for buy / close / update trade endpoints."""

    def test_add_trade_blacklisted_ticker_blocked(self, monkeypatch):
        """POST /api/portfolio/add should reject blacklisted tickers."""
        monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: {"comi"})
        monkeypatch.setattr(
            "routes.portfolio.WalkForwardValidation.get_trade_permission",
            lambda ticker, fail_closed=True: {"allowed": True, "reason": "ok"},
        )
        p = Portfolio.create(name="Test Portfolio Blacklist", type="USER")

        response = client.post("/api/v1/portfolio/add", json={
            "portfolio_id": p.id,
            "ticker": "COMI",
            "shares": 100,
            "price": 50.0,
            "type": "EXISTING",
        })
        assert response.status_code == 403
        assert "blacklisted" in response.json()["detail"].lower()
        assert Position.select().where(Position.portfolio == p.id, Position.ticker == "COMI").count() == 0

    def test_add_trade_new_position(self, monkeypatch):
        """POST /api/portfolio/add should create a new position when WFA allows."""
        monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: set())
        monkeypatch.setattr(
            "routes.portfolio.WalkForwardValidation.get_trade_permission",
            lambda ticker, fail_closed=True: {"allowed": True, "reason": "ok"},
        )
        p = Portfolio.create(name="Test Portfolio A", type="USER")

        response = client.post("/api/v1/portfolio/add", json={
            "portfolio_id": p.id,
            "ticker": "COMI",
            "shares": 100,
            "price": 50.0,
            "type": "EXISTING",
            "sl": 47.0,
            "tp": 55.0,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify position was created in DB
        pos = Position.select().where(
            Position.portfolio == p.id,
            Position.ticker == "COMI",
            Position.status == "OPEN",
        ).first()
        assert pos is not None
        assert int(pos.shares) == 100

    def test_add_trade_rejects_non_positive_portfolio_id(self, monkeypatch):
        """POST /api/portfolio/add should reject zero/negative portfolio IDs."""
        monkeypatch.setattr(
            "routes.portfolio.WalkForwardValidation.get_trade_permission",
            lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("WFA should not be called")),
        )

        zero_response = client.post("/api/v1/portfolio/add", json={
            "portfolio_id": 0,
            "ticker": "COMI",
            "shares": 100,
            "price": 50.0,
            "type": "EXISTING",
        })
        negative_response = client.post("/api/v1/portfolio/add", json={
            "portfolio_id": -1,
            "ticker": "COMI",
            "shares": 100,
            "price": 50.0,
            "type": "EXISTING",
        })

        assert zero_response.status_code == 422
        assert negative_response.status_code == 422

    def test_add_trade_accepts_frontend_target_price_fields(self, monkeypatch):
        """POST /api/v1/portfolio/add should accept target_price naming from the frontend."""
        portfolio = Portfolio.create(name="Frontend Add Alias", type="USER")
        captured = {}

        monkeypatch.setattr(
            "routes.portfolio.WalkForwardValidation.get_trade_permission",
            lambda ticker, fail_closed=True: {"allowed": True, "reason": "ok"},
        )

        def fake_add_gold(**kwargs):
            captured.update(kwargs)
            return {"status": "success", "action": "created", "ticker": kwargs["ticker"]}

        monkeypatch.setattr("core.portfolio.commands.TreasuryLedger.add_gold", fake_add_gold)
        monkeypatch.setattr("routes.portfolio.TreasuryLedger.add_gold", fake_add_gold)

        response = client.post("/api/v1/portfolio/add", json={
            "portfolio_id": portfolio.id,
            "ticker": "COMI",
            "shares": 100,
            "price": 50.0,
            "sl": 47.0,
            "target_price": 55.0,
            "target_price_2": 60.0,
            "date": "2026-05-02",
            "type": "EXISTING",
        })

        assert response.status_code == 200
        assert captured["ticker"] == "COMI"
        assert captured["sl"] == 47.0
        assert captured["tp"] == 55.0
        assert captured["tp2"] == 60.0
        assert captured["date"] == "2026-05-02"
        assert captured["portfolio_id"] == portfolio.id

    def test_close_trade_full(self):
        """POST /api/portfolio/close should fully close a position."""
        p = Portfolio.create(name="Test Portfolio B", type="USER")
        Position.create(
            portfolio=p.id,
            ticker="FWRY",
            shares=200,
            entry_price=5.0,
            stop_loss=4.5,
            target_price=6.0,
            current_price=5.5,
            status="OPEN",
            currency="EGP",
        )

        response = client.post("/api/v1/portfolio/close", json={
            "portfolio_id": p.id,
            "ticker": "FWRY",
            "price": 5.8,
        })
        assert response.status_code == 200

        # Position should be CLOSED
        open_count = Position.select().where(
            Position.portfolio == p.id,
            Position.ticker == "FWRY",
            Position.status == "OPEN",
        ).count()
        assert open_count == 0

        # Trade record should exist
        trade = Trade.select().where(
            Trade.portfolio == p.id,
            Trade.ticker == "FWRY",
        ).first()
        assert trade is not None

    def test_update_trade_sl_tp(self, monkeypatch):
        """PUT /api/portfolio/update should modify SL and TP."""
        p = Portfolio.create(name="Test Portfolio C", type="USER")
        Position.create(
            portfolio=p.id,
            ticker="SWDY",
            shares=50,
            entry_price=20.0,
            stop_loss=18.0,
            target_price=24.0,
            current_price=21.0,
            status="OPEN",
            currency="EGP",
        )

        response = client.post("/api/v1/portfolio/update", json={
            "portfolio_id": p.id,
            "ticker": "SWDY",
            "sl": 19.0,
            "tp": 26.0,
        })
        assert response.status_code == 200

        # Verify updates persisted
        pos = Position.get(
            Position.portfolio == p.id,
            Position.ticker == "SWDY",
            Position.status == "OPEN",
        )
        assert float(pos.stop_loss) == 19.0
        assert float(pos.target_price) == 26.0

    def test_update_trade_rejects_noop_payload(self):
        """POST /api/portfolio/update should reject requests with no update fields."""
        p = Portfolio.create(name="Test Portfolio Update Noop", type="USER")
        Position.create(
            portfolio=p.id,
            ticker="NOOP",
            shares=10,
            entry_price=10.0,
            stop_loss=9.0,
            target_price=12.0,
            current_price=10.5,
            status="OPEN",
            currency="EGP",
        )

        response = client.post("/api/v1/portfolio/update", json={
            "portfolio_id": p.id,
            "ticker": "NOOP",
        })

        assert response.status_code == 422

    def test_update_trade_accepts_frontend_target_price_fields(self, monkeypatch):
        """POST /api/v1/portfolio/update should accept target_price naming from the frontend."""
        portfolio = Portfolio.create(name="Frontend Update Alias", type="USER")
        Position.create(
            portfolio=portfolio.id,
            ticker="COMI",
            shares=25,
            entry_price=20.0,
            stop_loss=18.0,
            target_price=24.0,
            current_price=21.0,
            status="OPEN",
            currency="EGP",
        )
        captured = {}

        def fake_update_position(**kwargs):
            captured.update(kwargs)
            return True

        monkeypatch.setattr("core.portfolio.commands.PositionTracker.update_position", fake_update_position)
        monkeypatch.setattr("routes.portfolio.PositionTracker.update_position", fake_update_position)

        response = client.post("/api/v1/portfolio/update", json={
            "portfolio_id": portfolio.id,
            "ticker": "COMI",
            "sl": 19.0,
            "target_price": 26.0,
            "target_price_2": 29.0,
        })

        assert response.status_code == 200
        assert captured["ticker"] == "COMI"
        assert captured["sl"] == 19.0
        assert captured["tp"] == 26.0
        assert captured["tp2"] == 29.0
        assert captured["portfolio_id"] == portfolio.id

    def test_update_trade_rejects_blank_ticker(self):
        """POST /api/portfolio/update should reject blank tickers instead of returning 500."""
        p = Portfolio.create(name="Test Portfolio Blank Ticker", type="USER")

        response = client.post("/api/v1/portfolio/update", json={
            "portfolio_id": p.id,
            "ticker": "   ",
            "sl": 9.5,
        })

        assert response.status_code == 422

    def test_update_trade_rejects_non_positive_portfolio_id(self, monkeypatch):
        """POST /api/portfolio/update should reject zero/negative portfolio IDs."""
        monkeypatch.setattr(
            "routes.portfolio.PositionTracker.update_position",
            lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("update_position should not be called")),
        )

        zero_response = client.post("/api/v1/portfolio/update", json={
            "portfolio_id": 0,
            "ticker": "COMI",
            "sl": 9.5,
        })
        negative_response = client.post("/api/v1/portfolio/update", json={
            "portfolio_id": -1,
            "ticker": "COMI",
            "sl": 9.5,
        })

        assert zero_response.status_code == 422
        assert negative_response.status_code == 422


# =============================================================================
# PORTFOLIO CRUD
# =============================================================================

class TestPortfolioCRUD:
    """Tests for portfolio create / delete / list."""

    def test_create_portfolio(self):
        """POST /api/portfolios should create a new portfolio."""
        response = client.post("/api/v1/portfolios", json={
            "name": "My Custom Portfolio",
            "type": "USER",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert "id" in data

    def test_create_portfolio_rejects_blank_name(self):
        """POST /api/portfolios should reject blank portfolio names."""
        before_count = Portfolio.select().count()

        response = client.post("/api/v1/portfolios", json={
            "name": "",
            "type": "USER",
        })

        assert response.status_code == 400
        assert "name" in response.json()["detail"].lower()
        assert Portfolio.select().count() == before_count

    def test_delete_user_portfolio(self):
        """DELETE /api/portfolios/{id} should delete a USER portfolio."""
        p = Portfolio.create(name="Deletable Portfolio", type="USER")

        response = client.delete(f"/api/v1/portfolios/{p.id}")
        assert response.status_code == 200

        # Should not exist anymore
        assert Portfolio.select().where(Portfolio.id == p.id).count() == 0

    def test_delete_system_portfolio_blocked(self):
        """DELETE /api/portfolios/{id} should block deletion of SYSTEM portfolios."""
        p = Portfolio.select().where(Portfolio.type == "SYSTEM").first()
        if not p:
            p = Portfolio.create(name="System Protected", type="SYSTEM")

        response = client.delete(f"/api/v1/portfolios/{p.id}")
        # Should be forbidden (400 or 403)
        assert response.status_code in [400, 403]

    def test_get_default_system_portfolio(self):
        """GET /api/v1/portfolios/default should return the persisted system default."""
        system_portfolio = Portfolio.create(name="System Default Route", type="SYSTEM")

        set_response = client.post("/api/v1/portfolios/default", json={"portfolio_id": system_portfolio.id})
        get_response = client.get("/api/v1/portfolios/default")

        assert set_response.status_code == 200
        assert get_response.status_code == 200
        assert get_response.json()["portfolio_id"] == system_portfolio.id
        assert get_response.json()["portfolio_name"] == "System Default Route"
        assert get_response.json()["portfolio_type"] == "SYSTEM"

    def test_set_default_system_portfolio_rejects_user_portfolio(self):
        """POST /api/v1/portfolios/default should reject USER portfolios."""
        user_portfolio = Portfolio.create(name="User Default Route", type="USER")

        response = client.post("/api/v1/portfolios/default", json={"portfolio_id": user_portfolio.id})

        assert response.status_code == 400
        assert response.json()["detail"] == "Only SYSTEM portfolios can be set as the global default"

    def test_get_default_system_portfolio_returns_null_shape_when_unset(self):
        """GET /api/v1/portfolios/default should return a null payload when no default is configured."""
        response = client.get("/api/v1/portfolios/default")

        assert response.status_code == 200
        assert response.json() == {
            "portfolio_id": None,
            "portfolio_name": None,
            "portfolio_type": None,
        }

    def test_list_portfolios_shows_intraday_simulation_book(self):
        Portfolio.create(name="Daily Simulation", type="SYSTEM")
        Portfolio.create(name="Intraday Simulation", type="SYSTEM")

        response = client.get("/api/v1/portfolios")

        assert response.status_code == 200
        names = {row["name"] for row in response.json()}
        assert "Daily Simulation" not in names
        assert "Intraday Simulation" in names
        assert "Intraday Signals" in names


# =============================================================================
# PORTFOLIO ANALYTICS
# =============================================================================

class TestPortfolioAnalytics:
    """Tests for portfolio metrics and equity curve."""

    def test_get_portfolio_metrics_structure(self):
        """GET /api/portfolio-metrics should return valid metric fields."""
        response = client.get("/api/v1/portfolio-metrics")
        assert response.status_code == 200
        data = response.json()
        # Should contain key metric fields
        assert isinstance(data, dict)

    def test_get_equity_curve(self):
        """GET /api/portfolio/curve should return equity curve data."""
        response = client.get("/api/v1/portfolio/curve")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_get_portfolio_report_bundle(self):
        """GET /api/v1/portfolio/report should return bundled report payload."""
        response = client.get("/api/v1/portfolio/report")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "curve" in data
        assert "trades" in data

    def test_get_portfolio_metrics_uses_existing_portfolio_when_default_id_missing(self):
        """GET /api/v1/portfolio-metrics should not hardcode portfolio ID 1."""
        Portfolio.delete().where(Portfolio.id == 1).execute()
        p = Portfolio.get_by_id(2)
        Trade.create(
            ticker="COMI",
            shares=100,
            entry_price=10.0,
            exit_price=12.5,
            entry_date="2025-01-01",
            exit_date="2025-01-05",
            pnl=250.0,
            pnl_pct=25.0,
            portfolio=p,
        )

        response = client.get("/api/v1/portfolio-metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 1
        assert data["realized_pnl"] == 250.0

    def test_get_equity_curve_uses_existing_portfolio_when_default_id_missing(self):
        """GET /api/v1/portfolio/curve should not hardcode portfolio ID 1."""
        Portfolio.delete().where(Portfolio.id == 1).execute()
        p = Portfolio.get_by_id(2)
        Trade.create(
            ticker="FWRY",
            shares=50,
            entry_price=20.0,
            exit_price=22.0,
            entry_date="2025-02-01",
            exit_date="2025-02-03",
            pnl=100.0,
            pnl_pct=10.0,
            portfolio=p,
        )

        response = client.get("/api/v1/portfolio/curve")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[-1]["equity"] == 1000100.0

    def test_get_trades_rejects_zero_limit(self):
        """GET /api/v1/trades should reject limit=0."""
        response = client.get("/api/v1/trades?limit=0")
        assert response.status_code == 422

    def test_get_trades_rejects_negative_limit(self):
        """GET /api/v1/trades should reject negative limits."""
        response = client.get("/api/v1/trades?limit=-5")
        assert response.status_code == 422

    @pytest.mark.parametrize("path", [
        "/api/v1/portfolio",
        "/api/v1/positions",
        "/api/v1/trades",
        "/api/v1/portfolio-metrics",
        "/api/v1/portfolio/curve",
    ])
    def test_read_endpoints_reject_non_positive_portfolio_id(self, path):
        """Core portfolio read endpoints should reject zero/negative portfolio_id values."""
        zero_response = client.get(f"{path}?portfolio_id=0")
        negative_response = client.get(f"{path}?portfolio_id=-1")

        assert zero_response.status_code == 422
        assert negative_response.status_code == 422
