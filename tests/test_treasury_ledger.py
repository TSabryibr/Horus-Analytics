from core.settings import settings
import pytest
from unittest.mock import patch, MagicMock
from core.analyzers.TreasuryLedger import  add_gold, get_hoard_status, detect_currency, melt_gold
from database import Position, Portfolio, Trade

@pytest.fixture
def mock_settings():
    with patch('core.settings.settings.ACCOUNT_BALANCE', 100000.0), \
         patch('core.settings.settings.ACCOUNT_BALANCE_USD', 10000.0), \
         patch('core.settings.settings.save_settings', return_value=None):
        yield

def test_detect_currency():
    assert detect_currency("COMI") == "EGP"
    assert detect_currency("EGBE") == "USD"
    assert detect_currency("MOIL") == "USD"

def test_add_gold_new_position(mock_settings):
    # Setup
    ticker = "TEST"
    shares = 100
    price = 10.0
    
    # Ensure portfolio has cash
    p = Portfolio.get_by_id(1)
    p.cash_egp = 100000.0
    p.save()
    
    # Mock PositionTracker.add_position to return True
    with patch('core.PositionTracker.add_position', return_value=True), \
         patch('core.WalkForwardValidation.get_trade_permission', return_value={"allowed": True, "reason": "ok"}):
        res = add_gold(ticker, shares, price, type="NEW")
        
        assert res["status"] == "success"
        assert res["action"] == "created"
        assert res["cost"] == 1000.0

def test_add_gold_insufficient_funds(mock_settings):
    p = Portfolio.get_by_id(1)
    p.cash_egp = 500.0
    p.save()
    
    with patch('core.WalkForwardValidation.get_trade_permission', return_value={"allowed": True, "reason": "ok"}):
        res = add_gold("TEST", 100, 10.0, type="NEW")
        assert res["status"] == "error"
        assert "Insufficient EGP Cash" in res["message"]

def test_add_gold_blocked_by_wfa_gate(mock_settings):
    p = Portfolio.get_by_id(1)
    p.cash_egp = 100000.0
    p.save()
    
    with patch('core.WalkForwardValidation.get_trade_permission', return_value={"allowed": False, "reason": "validation_loss_blocked"}):
        res = add_gold("TEST", 100, 10.0, type="NEW")
        assert res["status"] == "blocked"
        assert res["reason"] == "validation_loss_blocked"

def test_get_hoard_status_empty():
    # Clear portfolio cash in database to test empty
    p = Portfolio.get_by_id(1)
    p.cash_egp = 0.0
    p.cash_usd = 0.0
    p.save()
    
    res = get_hoard_status()
    assert res["status"] == "empty"

def test_get_hoard_status_active(mock_settings):
    # Seed portfolio cash in database
    p = Portfolio.get_by_id(1)
    p.cash_egp = 100000.0
    p.cash_usd = 10000.0
    p.save()
    
    # Manually create a position in the mock DB
    Position.create(
        portfolio=p,
        ticker="TEST",
        shares=100,
        entry_price=10.0,
        stop_loss=9.0,
        target_price=12.0,
        status="OPEN",
        currency="EGP"
    )
    
    with patch('core.analyzers.TreasuryLedger.get_live_price', return_value=11.0):
        res = get_hoard_status()
        assert res["status"] == "active"
        assert res["position_count"] == 1
        assert res["positions"][0]["ticker"] == "TEST"
        assert res["positions"][0]["pnl"] == 100.0 # (11-10)*100
