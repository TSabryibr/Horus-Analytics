import pandas as pd
import pytest
from core.PositionTracker import add_position, close_position, load_positions, update_live_prices, update_position
from database import Position, Trade, Portfolio
from core import TimeUtils
@pytest.fixture(autouse=True)
def no_exclusions(monkeypatch):
    monkeypatch.setattr("core.PositionTracker.is_excluded_ticker", lambda t: False)


@pytest.fixture
def mock_portfolio():
    return Portfolio.create(name="Default", type="USER")

def test_add_position(mock_portfolio):
    success = add_position("COMI", 100, 50.0, sl=48.0, tp=55.0, portfolio_id=mock_portfolio.id)
    assert success is True
    
    pos = Position.get(ticker="COMI")
    assert pos.shares == 100
    assert pos.entry_price == 50.0
    assert pos.stop_loss == 48.0
    assert pos.currency == "EGP"


def test_add_position_debits_portfolio_cash_when_cash_ledger_is_initialized(mock_portfolio):
    mock_portfolio.cash_egp = 500_000.0
    mock_portfolio.save()

    success = add_position("COMI", 100, 50.0, sl=48.0, tp=55.0, portfolio_id=mock_portfolio.id)

    assert success is True
    refreshed = Portfolio.get_by_id(mock_portfolio.id)
    assert refreshed.cash_egp == 495_000.0

def test_add_duplicate_position(mock_portfolio):
    add_position("COMI", 100, 50.0, portfolio_id=mock_portfolio.id)
    success = add_position("COMI", 50, 51.0, portfolio_id=mock_portfolio.id)
    assert success is False # Duplicate check prevents adding new row for same ticker

def test_close_position(mock_portfolio):
    add_position("COMI", 100, 50.0, portfolio_id=mock_portfolio.id)
    
    success = close_position("COMI", 55.0, reason="TARGET", portfolio_id=mock_portfolio.id)
    assert success is True
    
    # Check if position is gone from Open table
    assert not Position.select().where(Position.ticker == "COMI", Position.status == "OPEN").exists()
    
    # Check if trade is logged
    trade = Trade.get(ticker="COMI")
    assert trade.exit_price == 55.0
    assert trade.pnl == 500.0 # (55-50)*100
    assert trade.reason == "TARGET"


def test_close_position_credits_sale_proceeds_to_portfolio_cash(mock_portfolio):
    mock_portfolio.cash_egp = 500_000.0
    mock_portfolio.save()
    add_position("COMI", 100, 50.0, portfolio_id=mock_portfolio.id)

    success = close_position("COMI", 49.0, reason="STOP_LOSS", portfolio_id=mock_portfolio.id)

    assert success is True
    refreshed = Portfolio.get_by_id(mock_portfolio.id)
    assert refreshed.cash_egp == 499_900.0

def test_update_position(mock_portfolio):
    add_position("COMI", 100, 50.0, portfolio_id=mock_portfolio.id)
    
    success = update_position("COMI", sl=45.0, portfolio_id=mock_portfolio.id)
    assert success is True
    
    p = Position.get(ticker="COMI")
    assert p.stop_loss == 45.0

def test_load_positions(mock_portfolio):
    add_position("COMI", 100, 50.0, portfolio_id=mock_portfolio.id)
    add_position("AAPL", 10, 150.0, portfolio_id=mock_portfolio.id)
    
    positions = load_positions(portfolio_id=mock_portfolio.id)
    assert len(positions) == 2
    assert "COMI" in positions
    assert "AAPL" in positions


def test_add_position_blocked_when_blacklisted(mock_portfolio, monkeypatch):
    monkeypatch.setattr("core.PositionTracker.is_excluded_ticker", lambda t: t == "COMI")
    success = add_position("COMI", 100, 50.0, portfolio_id=mock_portfolio.id)
    assert success is False
    assert not Position.select().where(Position.ticker == "COMI").exists()


def test_update_live_prices_uses_read_only_intraday_and_skips_unchanged_saves(mock_portfolio, monkeypatch):
    position = Position.create(
        portfolio=mock_portfolio.id,
        ticker="COMI",
        shares=100,
        entry_price=50.0,
        stop_loss=48.0,
        target_price=55.0,
        current_price=51.0,
        status="OPEN",
        currency="EGP",
        entry_date=TimeUtils.now(),
    )
    intraday_df = pd.DataFrame({"Close": [51.0]}, index=pd.to_datetime(["2026-03-17 12:00:00"]))
    intraday_calls = []

    def fake_get_intraday_data(ticker, limit=None, refresh_if_stale=True):
        intraday_calls.append(
            {
                "ticker": ticker,
                "limit": limit,
                "refresh_if_stale": refresh_if_stale,
            }
        )
        return intraday_df

    monkeypatch.setattr("core.DataManager.DataManager.get_intraday_data", fake_get_intraday_data)
    monkeypatch.setattr(
        "core.DataManager.DataManager.get_stock_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("daily fallback should not run")),
    )

    def fail_save(self, *args, **kwargs):
        raise AssertionError("unchanged prices should not trigger writes")

    monkeypatch.setattr("core.PositionTracker.Position.save", fail_save)

    changed = update_live_prices()
    refreshed = Position.get_by_id(position.id)

    assert changed == 0
    assert refreshed.current_price == 51.0
    assert intraday_calls == [
        {
            "ticker": "COMI",
            "limit": 1,
            "refresh_if_stale": False,
        }
    ]


def test_update_live_prices_uses_non_live_daily_fallback_when_intraday_missing(mock_portfolio, monkeypatch):
    position = Position.create(
        portfolio=mock_portfolio.id,
        ticker="HRHO",
        shares=50,
        entry_price=20.0,
        stop_loss=18.0,
        target_price=24.0,
        current_price=20.0,
        status="OPEN",
        currency="EGP",
        entry_date=TimeUtils.now(),
    )
    daily_df = pd.DataFrame({"Close": [22.5]}, index=pd.to_datetime(["2026-03-17"]))
    stock_calls = []

    monkeypatch.setattr("core.DataManager.DataManager.get_intraday_data", lambda *args, **kwargs: None)

    def fake_get_stock_data(ticker, include_live=True, **kwargs):
        stock_calls.append(
            {
                "ticker": ticker,
                "include_live": include_live,
            }
        )
        return daily_df

    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", fake_get_stock_data)

    changed = update_live_prices()
    refreshed = Position.get_by_id(position.id)

    assert changed == 1
    assert refreshed.current_price == 22.5
    assert stock_calls == [
        {
            "ticker": "HRHO",
            "include_live": False,
        }
    ]
