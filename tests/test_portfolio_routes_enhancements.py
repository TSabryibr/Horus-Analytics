import pytest
from fastapi.testclient import TestClient
from api import app
from database import Portfolio, Position, db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_route_test_portfolio():
    db.connect(reuse_if_open=True)
    portfolio, _ = Portfolio.get_or_create(
        id=998,
        defaults={
            "name": "Route Test Portfolio",
            "type": "USER",
            "cash_egp": 100000.0,
            "cash_usd": 2000.0,
        }
    )
    Position.delete().where(Position.portfolio == portfolio.id).execute()

    Position.create(
        portfolio=portfolio.id,
        ticker="FWRY",
        shares=5000,
        entry_price=5.5,
        current_price=6.0,
        stop_loss=5.0,
        target_price=7.0,
        status="OPEN",
        currency="EGP",
    )

    yield portfolio

    Position.delete().where(Position.portfolio == portfolio.id).execute()
    Portfolio.delete().where(Portfolio.id == portfolio.id).execute()


def test_api_rebalance_models(setup_route_test_portfolio):
    portfolio = setup_route_test_portfolio
    res = client.get(f"/api/v1/portfolio/rebalance?portfolio_id={portfolio.id}&model=RISK_PARITY")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["ticker"] == "FWRY"
    assert data[0]["model"] == "RISK_PARITY"


def test_api_stress_test(setup_route_test_portfolio):
    portfolio = setup_route_test_portfolio
    res = client.get(f"/api/v1/portfolio/stress-test?portfolio_id={portfolio.id}&simulations=200&days=15")
    assert res.status_code == 200
    data = res.json()
    assert data["portfolio_id"] == portfolio.id
    assert "var_95_egp" in data
    assert "scenarios" in data
    assert len(data["scenarios"]) >= 4


def test_api_market_rate():
    res = client.get("/api/v1/market/rate")
    assert res.status_code == 200
    data = res.json()
    assert data["base"] == "USD"
    assert data["target"] == "EGP"
    assert float(data["rate"]) > 0


def test_api_batch_breakeven(setup_route_test_portfolio):
    portfolio = setup_route_test_portfolio
    payload = {
        "portfolio_id": portfolio.id,
        "action": "MOVE_STOPS_BREAKEVEN",
        "tickers": ["FWRY"],
    }
    res = client.post("/api/v1/portfolio/positions/batch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["processed_count"] == 1


def test_api_download_portfolio_template_xlsx():
    res = client.get("/api/v1/portfolio/template?format=xlsx")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "subscriber_portfolio_intake_template.xlsx" in res.headers.get("content-disposition", "")
    assert len(res.content) > 0


def test_api_download_portfolio_template_csv():
    res = client.get("/api/v1/portfolio/template?format=csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "subscriber_portfolio_intake_template.csv" in res.headers.get("content-disposition", "")
    assert b"Ticker,Shares,Entry_Price" in res.content


def test_api_subscriber_import_sandbox():
    csv_bytes = b"Ticker,Shares,Entry_Price\nCOMI,500,104.50\nABUK,1000,60.00\n"
    files = {"file": ("client_intake.csv", csv_bytes, "text/csv")}
    res = client.post("/api/v1/portfolio/subscriber/import?mode=sandbox&portfolio_name=Audit%20Test", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["mode"] == "sandbox"
    assert data["portfolio_id"] is None
    assert "report" in data
    assert data["report"]["summary"]["open_positions"] == 2


def test_api_subscriber_import_create_new():
    csv_bytes = b"Ticker,Shares,Entry_Price,Stop_Loss,Target_Price_1\nSWDY,1500,45.2,42.0,52.0\n"
    files = {"file": ("new_client.csv", csv_bytes, "text/csv")}
    res = client.post("/api/v1/portfolio/subscriber/import?mode=create_new&portfolio_name=VIP%20Client%20Omar", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "created"
    assert data["mode"] == "create_new"
    new_pid = data["portfolio_id"]
    assert new_pid is not None
    assert data["portfolio_name"] == "VIP Client Omar"

    # Clean up created test portfolio
    Position.delete().where(Position.portfolio == new_pid).execute()
    Portfolio.delete().where(Portfolio.id == new_pid).execute()


