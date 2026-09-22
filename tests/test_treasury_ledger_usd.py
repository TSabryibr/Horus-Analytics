from core.settings import settings
import pytest
from unittest.mock import patch, MagicMock
from core.analyzers.TreasuryLedger import add_gold, get_hoard_status, melt_gold
from database import Position, Portfolio, Trade
import datetime

@pytest.fixture
def mock_settings():
    with patch('core.settings.settings.ACCOUNT_BALANCE', 100000.0), \
         patch('core.settings.settings.ACCOUNT_BALANCE_USD', 10000.0), \
         patch('core.settings.settings.save_settings', return_value=None):
        yield

def test_add_gold_stores_exchange_rate(mock_settings):
    # Setup
    ticker = "TEST_USD_MIGR"
    shares = 100
    price = 10.0
    
    p = Portfolio.get_by_id(1)
    p.cash_egp = 100000.0
    p.save()
    
    # We mock get_parallel_usd_egp_rate to return 50.0
    with patch('core.PositionTracker.add_position', return_value=True), \
         patch('core.WalkForwardValidation.get_trade_permission', return_value={"allowed": True, "reason": "ok"}), \
         patch('core.analyzers.TreasuryLedger.get_parallel_usd_egp_rate', return_value=50.0):
        
        # Delete any pre-existing positions for ticker to keep test clean
        Position.delete().where(Position.ticker == ticker).execute()
        
        res = add_gold(ticker, shares, price, type="NEW")
        assert res["status"] == "success"
        
        # Verify Position in DB has the entry_usd_rate
        pos = Position.get_or_none(ticker=ticker, status="OPEN", portfolio=p)
        assert pos is not None
        assert pos.entry_usd_rate == 50.0

def test_add_gold_averaging_weighted_rate(mock_settings):
    ticker = "TEST_AVG_USD"
    p = Portfolio.get_by_id(1)
    p.cash_egp = 100000.0
    p.save()
    
    # Clean up
    Position.delete().where(Position.ticker == ticker).execute()
    
    # Mocking
    with patch('core.PositionTracker.add_position', return_value=True), \
         patch('core.WalkForwardValidation.get_trade_permission', return_value={"allowed": True, "reason": "ok"}), \
         patch('core.analyzers.TreasuryLedger.get_parallel_usd_egp_rate') as mock_rate:
        
        # Purchase 1: 100 shares at 10.0 EGP, rate = 50.0 EGP/USD. Total EGP cost = 1000 EGP ($20)
        mock_rate.return_value = 50.0
        add_gold(ticker, 100, 10.0, type="NEW")
        
        # Purchase 2: 100 shares at 20.0 EGP, rate = 60.0 EGP/USD. Total EGP cost = 2000 EGP ($33.333333333333336)
        # New shares = 200, average price = 15.0 EGP, total EGP cost = 3000 EGP ($53.333333333333336)
        # Expected weighted average entry usd rate: 3000 / 53.333333333333336 = 56.25 EGP/USD
        mock_rate.return_value = 60.0
        add_gold(ticker, 100, 20.0, type="NEW")
        
        pos = Position.get_or_none(ticker=ticker, status="OPEN", portfolio=p)
        assert pos is not None
        assert pos.shares == 200
        assert pos.entry_price == 15.0
        assert abs(pos.entry_usd_rate - 56.25) < 0.0001

def test_get_hoard_status_detects_devaluation_loss(mock_settings):
    p = Portfolio.get_by_id(1)
    p.cash_egp = 100000.0
    p.cash_usd = 10000.0
    p.save()
    
    ticker = "TEST_DEV"
    Position.delete().where(Position.ticker == ticker).execute()
    
    # Create position with entry rate 30.0 (low EGP devaluation)
    pos = Position.create(
        portfolio=p,
        ticker=ticker,
        shares=100,
        entry_price=10.0,
        stop_loss=8.0,
        target_price=15.0,
        status="OPEN",
        currency="EGP",
        entry_usd_rate=30.0,
        entry_date=datetime.datetime.now()
    )
    
    # Mock current price is 11.0 (EGP is profitable: +10% gain, PnL = +100 EGP)
    # But exchange rate went to 60.0 (high EGP devaluation: USD value is lower than at entry)
    # Entry USD cost = (100 * 10) / 30 = $33.33
    # Current USD value = (100 * 11) / 60 = $18.33
    # USD PnL = -$15.00 (loss!)
    with patch('core.analyzers.TreasuryLedger.get_live_price', return_value=11.0), \
         patch('core.analyzers.TreasuryLedger.get_parallel_usd_egp_rate', return_value=60.0):
        
        res = get_hoard_status()
        pos_data = [item for item in res["positions"] if item["ticker"] == ticker][0]
        
        assert pos_data["pnl_egp"] == 100.0
        assert pos_data["pnl_usd"] < 0
        assert pos_data["devaluation_loss"] is True
        assert pos_data["risk_status"] == "DEVALUATION_LOSS"

def test_melt_gold_stores_trade_usd_rates(mock_settings):
    p = Portfolio.get_by_id(1)
    p.save()
    
    ticker = "TEST_MELT_USD"
    Position.delete().where(Position.ticker == ticker).execute()
    Trade.delete().where(Trade.ticker == ticker).execute()
    
    pos = Position.create(
        portfolio=p,
        ticker=ticker,
        shares=100,
        entry_price=10.0,
        stop_loss=8.0,
        target_price=15.0,
        status="OPEN",
        currency="EGP",
        entry_usd_rate=45.0,
        entry_date=datetime.datetime.now()
    )
    
    with patch('core.analyzers.TreasuryLedger.get_parallel_usd_egp_rate', return_value=55.0):
        res = melt_gold(ticker, shares=100, price=12.0)
        assert res["status"] == "success"
        
        # Verify Trade record
        trade = Trade.get_or_none(ticker=ticker, portfolio=p)
        assert trade is not None
        assert trade.entry_usd_rate == 45.0
        assert trade.exit_usd_rate == 55.0
