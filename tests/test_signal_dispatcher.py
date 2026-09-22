import pytest
import zmq
import json
import time
from unittest.mock import MagicMock, patch
from core.signals.SignalDispatcher import SignalDispatcher
from core.signals.OrderManager import OrderManager
from database import BrokerOrder, db

@pytest.fixture(autouse=True)
def setup_kill_switch_state(monkeypatch):
    # Disable kill switch to allow orders
    import core.risk.kill_switch
    monkeypatch.setattr(core.risk.kill_switch, "is_kill_switch_active", lambda: False)

def test_signal_dispatcher_valid_trigger(monkeypatch):
    # Mock analyze_stock to return a high-scoring valid signal
    mock_signal = {
        "Score": 5,
        "Status": "⚡ STRONG BUY",
        "Manipulation_Flag": "CLEAR",
        "Projected_Return_%": 15.0,
        "PPP_Hurdle_%": 5.0,
        "Stop_Loss": 14.50,
        "Target_2": 18.00
    }
    mock_analyze = MagicMock(return_value=mock_signal)
    monkeypatch.setattr("core.signals.SignalDispatcher.analyze_stock", mock_analyze)

    # Mock OrderManager submit_live_order
    mock_submit = MagicMock(return_value={"success": True, "order_id": 999})
    monkeypatch.setattr(OrderManager, "submit_live_order", mock_submit)

    dispatcher = SignalDispatcher()
    
    # Process simulated tick manually to verify routing logic
    tick_payload = {"ticker": "COMI", "price": 15.50, "volume": 10000, "timestamp": time.time()}
    dispatcher._process_tick(tick_payload)

    # Verify analyze_stock was called with the correct ticker
    mock_analyze.assert_called_once_with("COMI", include_live=True)

    # Dispatcher only publishes signals; live order execution is owned by
    # AutoTrader. _process_tick must NOT place orders directly.
    mock_submit.assert_not_called()

def test_signal_dispatcher_invalid_by_risk_gate(monkeypatch):
    # Mock analyze_stock to return a manipulated breakout signal
    mock_signal = {
        "Score": 5,
        "Status": "⚠️ LOW_VOL_BREAKOUT",
        "Manipulation_Flag": "LOW_VOL_BREAKOUT",
        "Projected_Return_%": 15.0,
        "PPP_Hurdle_%": 5.0,
    }
    mock_analyze = MagicMock(return_value=mock_signal)
    monkeypatch.setattr("core.signals.SignalDispatcher.analyze_stock", mock_analyze)

    mock_submit = MagicMock()
    monkeypatch.setattr(OrderManager, "submit_live_order", mock_submit)

    dispatcher = SignalDispatcher()
    tick_payload = {"ticker": "COMI", "price": 15.50, "volume": 1000, "timestamp": time.time()}
    dispatcher._process_tick(tick_payload)

    # Order should be rejected by risk gates (ManipulationSentry active)
    mock_submit.assert_not_called()

def test_signal_dispatcher_low_score_rejected(monkeypatch):
    # Mock analyze_stock to return a weak signal (score 2)
    mock_signal = {
        "Score": 2,
        "Status": "⏳ ACCUMULATION PHASE",
        "Manipulation_Flag": "CLEAR",
        "Projected_Return_%": 2.0,
        "PPP_Hurdle_%": 5.0,
    }
    mock_analyze = MagicMock(return_value=mock_signal)
    monkeypatch.setattr("core.signals.SignalDispatcher.analyze_stock", mock_analyze)

    mock_submit = MagicMock()
    monkeypatch.setattr(OrderManager, "submit_live_order", mock_submit)

    dispatcher = SignalDispatcher()
    tick_payload = {"ticker": "COMI", "price": 15.50, "volume": 1000, "timestamp": time.time()}
    dispatcher._process_tick(tick_payload)

    # Order should be rejected due to low score
    mock_submit.assert_not_called()
