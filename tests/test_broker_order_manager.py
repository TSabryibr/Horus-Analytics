import pytest
from unittest.mock import MagicMock, patch
from core.risk.kill_switch import set_kill_switch, is_kill_switch_active
from core.market.ThndrBrokerClient import ThndrBrokerClient
from core.signals.OrderManager import OrderManager
from database import BrokerOrder, db
import pandas as pd

@pytest.fixture(autouse=True)
def setup_kill_switch_state(monkeypatch, tmp_path):
    # Setup temporary file-backed state for kill switch
    state_file = tmp_path / "kill_switch.state"
    import core.risk.kill_switch
    monkeypatch.setattr(core.risk.kill_switch, "STATE_FILE", state_file)
    set_kill_switch(False)

def test_submit_order_kill_switch_active(monkeypatch):
    set_kill_switch(True)
    
    initial_count = BrokerOrder.select().count()
    result = OrderManager.submit_live_order(1, "COMI", "BUY", 100, 15.50)
    
    assert result["success"] is False
    assert result["reason"] == "emergency_kill_switch_active"
    assert BrokerOrder.select().count() == initial_count

def test_submit_order_success_and_reconcile(monkeypatch):
    # Mock DataManager
    import pandas as pd
    mock_df = pd.DataFrame([{"Close": 15.50}])
    monkeypatch.setattr("core.DataManager.DataManager.get_intraday_data", lambda ticker, limit, refresh_if_stale: mock_df)
    
    initial_count = BrokerOrder.select().count()
    result = OrderManager.submit_live_order(1, "COMI", "BUY", 200, 15.00)
    
    assert result["success"] is True
    assert result["state"] == "SUBMITTED"
    assert BrokerOrder.select().count() == initial_count + 1
    
    order = BrokerOrder.get_by_id(result["order_id"])
    assert order.symbol == "COMI"
    assert order.side == "BUY"
    assert order.quantity == 200
    
    # Check that immediate reconciliation during submit_live_order completed the fill!
    assert order.state == "FILLED"
    assert order.filled_price >= 15.50
    assert order.slippage_bps > 0

def test_submit_order_broker_rejection(monkeypatch):
    # Mock ThndrBrokerClient order placement failure
    mock_place_order = MagicMock(return_value={"success": False, "reason": "insufficient_funds"})
    monkeypatch.setattr(ThndrBrokerClient, "place_order", mock_place_order)
    monkeypatch.setattr(ThndrBrokerClient, "_ensure_authenticated", lambda self: True)
    
    result = OrderManager.submit_live_order(1, "COMI", "BUY", 100, 10.00)
    
    assert result["success"] is False
    assert result["state"] == "REJECTED"
    assert result["reason"] == "insufficient_funds"
    
    order = BrokerOrder.get_by_id(result["order_id"])
    assert order.state == "REJECTED"

def test_reconcile_broker_rejected_status(monkeypatch):
    # Create a local submitted order
    order = BrokerOrder.create(
        portfolio=1,
        symbol="COMI",
        side="BUY",
        quantity=50,
        price=10.0,
        state="SUBMITTED",
        broker_order_id="MOCK-123"
    )
    
    # Mock query_order_status to return REJECTED
    mock_status = MagicMock(return_value={"success": True, "status": "REJECTED"})
    monkeypatch.setattr(ThndrBrokerClient, "query_order_status", mock_status)
    monkeypatch.setattr(ThndrBrokerClient, "_ensure_authenticated", lambda self: True)
    
    success = OrderManager.reconcile_order(order.id)
    assert success is False
    
    refreshed_order = BrokerOrder.get_by_id(order.id)
    assert refreshed_order.state == "REJECTED"
