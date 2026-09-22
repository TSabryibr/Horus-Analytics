import pytest
from database import Portfolio, Position, Trade, db
from core.portfolio.queries import get_equity_curve_query
from core.analyzers.TreasuryLedger import get_rebalancing_recommendations
from core.RiskManager import run_portfolio_stress_test
from core.portfolio.commands import batch_positions_command, apply_rebalancing_command
from types import SimpleNamespace


@pytest.fixture(autouse=True)
def setup_test_portfolio_db():
    db.connect(reuse_if_open=True)
    portfolio, _ = Portfolio.get_or_create(
        id=999,
        defaults={
            "name": "Enhancement Test Portfolio",
            "type": "USER",
            "cash_egp": 50000.0,
            "cash_usd": 1000.0,
        }
    )
    portfolio.cash_egp = 50000.0
    portfolio.cash_usd = 1000.0
    portfolio.save()
    Position.delete().where(Position.portfolio == portfolio.id).execute()
    Trade.delete().where(Trade.portfolio == portfolio.id).execute()

    # Create 2 test positions
    p1 = Position.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=1000,
        entry_price=80.0,
        current_price=85.0,
        stop_loss=76.0,
        target_price=95.0,
        status="OPEN",
        currency="EGP",
    )
    p2 = Position.create(
        portfolio=portfolio.id,
        ticker="EAST",
        shares=2000,
        entry_price=30.0,
        current_price=32.0,
        stop_loss=28.0,
        target_price=38.0,
        status="OPEN",
        currency="EGP",
    )

    yield portfolio

    Position.delete().where(Position.portfolio == portfolio.id).execute()
    Trade.delete().where(Trade.portfolio == portfolio.id).execute()
    Portfolio.delete().where(Portfolio.id == portfolio.id).execute()


def test_dynamic_equity_curve_baseline(setup_test_portfolio_db):
    portfolio = setup_test_portfolio_db
    curve = get_equity_curve_query(portfolio_id=portfolio.id)
    assert len(curve) >= 1
    # Starting base equity = cash (50,000) + cost basis (1000*80 + 2000*30 = 140,000) = 190,000
    baseline = curve[0]
    assert baseline["date"] == "Baseline"
    assert baseline["equity"] == 1000000.0


def test_rebalancing_models(setup_test_portfolio_db):
    portfolio = setup_test_portfolio_db
    # Test EQUAL_WEIGHT
    eq_recs = get_rebalancing_recommendations(portfolio_id=portfolio.id, target_model="EQUAL_WEIGHT")
    assert len(eq_recs) == 2
    assert all("target_pct" in r and "drift_pct" in r for r in eq_recs)

    # Test RISK_PARITY
    rp_recs = get_rebalancing_recommendations(portfolio_id=portfolio.id, target_model="RISK_PARITY")
    assert len(rp_recs) == 2

    # Test KELLY_WEIGHTED
    kw_recs = get_rebalancing_recommendations(portfolio_id=portfolio.id, target_model="KELLY_WEIGHTED")
    assert len(kw_recs) == 2


def test_rebalancing_consolidates_multiple_lots_of_same_ticker(setup_test_portfolio_db):
    portfolio = setup_test_portfolio_db
    # Add a 2nd lot of COMI and a 3rd lot of COMI at different prices
    Position.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=500,
        entry_price=82.0,
        current_price=85.0,
        stop_loss=78.0,
        target_price=95.0,
        status="OPEN",
        currency="EGP",
    )
    Position.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=300,
        entry_price=84.0,
        current_price=85.0,
        stop_loss=80.0,
        target_price=98.0,
        status="OPEN",
        currency="EGP",
    )

    # 4 Position rows in DB (3 COMI + 1 EAST), but only 2 unique tickers (COMI, EAST)
    recs = get_rebalancing_recommendations(portfolio_id=portfolio.id, target_model="EQUAL_WEIGHT")
    assert len(recs) == 2  # Must consolidate to 2 unique tickers!

    tickers = [r["ticker"] for r in recs]
    assert "COMI" in tickers
    assert "EAST" in tickers

    comi_rec = next(r for r in recs if r["ticker"] == "COMI")
    # Total shares should be 1000 + 500 + 300 = 1800
    assert comi_rec["current_shares"] == 1800


def test_rebalancing_multi_currency_usd_stock(setup_test_portfolio_db):
    portfolio = setup_test_portfolio_db
    # Add a USD stock (GTEX)
    Position.create(
        portfolio=portfolio.id,
        ticker="GTEX",
        shares=100000,
        entry_price=0.04,
        current_price=0.05,
        stop_loss=0.038,
        target_price=0.06,
        status="OPEN",
        currency="USD",
    )

    recs = get_rebalancing_recommendations(portfolio_id=portfolio.id, target_model="EQUAL_WEIGHT")
    gtex_rec = next((r for r in recs if r["ticker"] == "GTEX"), None)
    assert gtex_rec is not None
    assert gtex_rec["currency"] == "USD"
    assert gtex_rec["is_usd"] is True
    # Native price should be decimal USD price (< 1.0 USD for GTEX), not inflated to EGP
    assert 0.01 < gtex_rec["current_price"] < 1.0
    assert gtex_rec["current_price_egp"] > 0
    # Shares delta must be calculated in native terms (not millions due to dividing EGP by USD)
    assert gtex_rec["shares_delta"] < 1000000
    assert "delta_value_native" in gtex_rec
    assert "delta_value_egp" in gtex_rec


def test_portfolio_stress_test_monte_carlo(setup_test_portfolio_db):
    portfolio = setup_test_portfolio_db
    res = run_portfolio_stress_test(portfolio_id=portfolio.id, num_simulations=500, horizon_days=30)
    assert res["portfolio_id"] == portfolio.id
    assert res["net_worth_egp"] > 0
    assert res["var_95_egp"] > 0
    assert res["var_99_egp"] >= res["var_95_egp"]
    assert res["cvar_95_egp"] >= res["var_95_egp"]
    assert len(res["scenarios"]) >= 4
    assert "monte_carlo_distribution" in res
    assert "p5_loss_pct" in res["monte_carlo_distribution"]


def test_batch_move_stops_to_breakeven(setup_test_portfolio_db):
    portfolio = setup_test_portfolio_db
    req = SimpleNamespace(portfolio_id=portfolio.id, action="MOVE_STOPS_BREAKEVEN", tickers=["COMI", "EAST"])
    res = batch_positions_command(req)
    assert res["status"] == "success"
    assert res["processed_count"] == 2

    # Verify stop loss updated to entry price
    comi = Position.get(Position.portfolio == portfolio.id, Position.ticker == "COMI")
    assert comi.stop_loss == 80.0
    east = Position.get(Position.portfolio == portfolio.id, Position.ticker == "EAST")
    assert east.stop_loss == 30.0
