import pytest
from fastapi.testclient import TestClient
from api import app
from database import Portfolio, Position, Trade, db
from core import WalkForwardValidation
client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture
def test_portfolio():
    # Attempt to find or create
    p = Portfolio.create(name="Audit Test Portfolio", type="USER", cash_egp=100000)
    yield p
    # Clean up position and trade data for this portfolio to avoid side effects
    Position.delete().where(Position.portfolio == p.id).execute()
    Trade.delete().where(Trade.portfolio == p.id).execute()
    p.delete_instance()

def test_genesis_negative_balance(test_portfolio):
    """POST /api/portfolio/genesis should handle balances correctly."""
    response = client.post("/api/v1/portfolio/genesis", json={
        "portfolio_id": test_portfolio.id,
        "egp_balance": -1000,
        "usd_balance": 0,
        "holdings": []
    })
    # Now it returns 422 due to Pydantic Field(ge=0)
    assert response.status_code == 422

def test_close_trade_invalid_price(test_portfolio):
    """POST /api/trade/close should reject invalid prices."""
    response = client.post("/api/v1/trade/close", json={
        "ticker": "AAPL",
        "price": -150,
        "portfolio_id": test_portfolio.id
    })
    # Now it returns 422 due to Pydantic Field(gt=0)
    assert response.status_code == 422

def test_close_trade_blank_ticker_rejected_before_business_logic(test_portfolio, monkeypatch):
    """POST /api/trade/close with blank ticker should fail at request validation."""
    monkeypatch.setattr(
        "routes.portfolio.TreasuryLedger.melt_gold",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("melt_gold should not be called")),
    )

    response = client.post("/api/v1/trade/close", json={
        "ticker": "   ",
        "price": 150,
        "portfolio_id": test_portfolio.id,
    })

    assert response.status_code == 422

def test_close_trade_rejects_non_positive_portfolio_id(test_portfolio, monkeypatch):
    """POST /api/trade/close should reject zero/negative portfolio IDs."""
    monkeypatch.setattr(
        "routes.portfolio.TreasuryLedger.melt_gold",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("melt_gold should not be called")),
    )

    zero_response = client.post("/api/v1/trade/close", json={
        "ticker": "AAPL",
        "price": 150,
        "portfolio_id": 0,
    })
    negative_response = client.post("/api/v1/trade/close", json={
        "ticker": "AAPL",
        "price": 150,
        "portfolio_id": -1,
    })

    assert zero_response.status_code == 422
    assert negative_response.status_code == 422

def test_close_trade_insufficient_shares(test_portfolio):
    """POST /api/trade/close should handle insufficient shares (but return 400 for business logic)."""
    # Create a small position
    from database import Position
    Position.create(
        portfolio=test_portfolio,
        ticker="AAPL",
        shares=10,
        entry_price=150,
        stop_loss=140,
        target_price=170,
        status="OPEN"
    )

    response = client.post("/api/v1/trade/close", json={
        "ticker": "AAPL",
        "price": 160,
        "shares": 100, # Too many
        "portfolio_id": test_portfolio.id
    })
    # Business logic error should be 400 now (standardized)
    assert response.status_code == 400
    assert "not enough shares" in response.json()["detail"].lower()

def test_delete_non_existent_portfolio():
    """DELETE /api/portfolios/{id} should return 404 for missing portfolios."""
    # Ensure ID 99999 doesn't exist
    Portfolio.delete().where(Portfolio.id == 99999).execute()
    response = client.delete("/api/v1/portfolios/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_risk_check_missing_ticker():
    """POST /api/risk/check should require ticker."""
    response = client.post("/api/v1/risk/check", json={})
    assert response.status_code == 400

def test_risk_check_rejects_non_integer_portfolio_id():
    """POST /api/risk/check should reject invalid portfolio_id types."""
    response = client.post("/api/v1/risk/check", json={
        "ticker": "COMI",
        "portfolio_id": "bad",
    })
    assert response.status_code == 400
    assert "portfolio_id" in response.json()["detail"].lower()

def test_risk_check_rejects_non_positive_portfolio_id():
    """POST /api/risk/check should reject zero/negative portfolio IDs."""
    zero_response = client.post("/api/v1/risk/check", json={
        "ticker": "COMI",
        "portfolio_id": 0,
    })
    negative_response = client.post("/api/v1/risk/check", json={
        "ticker": "COMI",
        "portfolio_id": -1,
    })
    assert zero_response.status_code == 400
    assert negative_response.status_code == 400
    assert "portfolio_id" in zero_response.json()["detail"].lower()
    assert "portfolio_id" in negative_response.json()["detail"].lower()

def test_intake_invalid_ticker(test_portfolio):
    """POST /api/portfolio/management/intake should skip invalid/blacklisted tickers."""
    # Assuming WalkForwardValidation defaults to allowed: True for unknown, 
    # but we can check if it catches empty tickers
    response = client.post("/api/v1/portfolio/management/intake", json={
        "portfolio_id": test_portfolio.id,
        "holdings": [
            {"ticker": "", "shares": 100, "entry_price": 10.0}
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 0
    assert len(data["errors"]) > 0

def test_intake_calculation_logic(test_portfolio):
    """POST /api/portfolio/management/intake should derive shares from cost if missing."""
    response = client.post("/api/v1/portfolio/management/intake", json={
        "portfolio_id": test_portfolio.id,
        "holdings": [
            {"ticker": "COMI", "total_cost": 5000, "entry_price": 50.0}
        ]
    })
    assert response.status_code == 200
    pos = Position.get(Position.portfolio == test_portfolio.id, Position.ticker == "COMI")
    assert int(pos.shares) == 100
