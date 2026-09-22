import pytest
import time
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from core.settings import settings
from core.risk.kill_switch import set_kill_switch, is_kill_switch_active
from core.market.ShadowExecutionGateway import ShadowExecutionGateway
from core.signals.executor import SignalExecutor
from database import SignalRun, SignalRecommendation, Portfolio, Position

def test_kill_switch_persistence(tmp_path, monkeypatch):
    # Setup temporary file-backed state for kill switch
    state_file = tmp_path / "kill_switch.state"
    import core.risk.kill_switch
    monkeypatch.setattr(core.risk.kill_switch, "STATE_FILE", state_file)
    
    # Initially False
    assert is_kill_switch_active() is False
    
    # Toggle True
    set_kill_switch(True)
    assert is_kill_switch_active() is True
    assert state_file.read_text(encoding="utf-8") == "true"
    
    # Toggle False
    set_kill_switch(False)
    assert is_kill_switch_active() is False
    assert state_file.read_text(encoding="utf-8") == "false"

def test_shadow_execution_gateway_kill_switch_active(tmp_path, monkeypatch):
    # Enable Kill Switch
    state_file = tmp_path / "kill_switch.state"
    import core.risk.kill_switch
    monkeypatch.setattr(core.risk.kill_switch, "STATE_FILE", state_file)
    set_kill_switch(True)
    
    report = ShadowExecutionGateway.place_shadow_order("COMI", 100, "BUY", 10.0)
    assert report["success"] is False
    assert report["reason"] == "emergency_kill_switch_active"

@patch("time.sleep") # Mock sleep to speed up unit test
def test_shadow_execution_gateway_slippage(mock_sleep, monkeypatch):
    # Disable Kill Switch
    import core.risk.kill_switch
    monkeypatch.setattr(core.risk.kill_switch, "is_kill_switch_active", lambda: False)
    
    # Mock DataManager to return simulated prices
    mock_get_intraday = MagicMock(return_value=None)
    mock_get_stock = MagicMock(return_value=MagicMock(empty=False, iloc=MagicMock(values=[MagicMock(Close=10.20)])))
    # We return a mock DataFrame that has a Close of 10.20
    import pandas as pd
    mock_df = pd.DataFrame([{"Close": 10.20}])
    monkeypatch.setattr("core.DataManager.DataManager.get_intraday_data", lambda ticker, limit, refresh_if_stale: None)
    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", lambda ticker, include_live: mock_df)
    
    # Run the shadow broker order simulation
    # Signal says 10.0, but market has drifted to 10.20. Order gets filled around 10.20 + drift.
    # Let's seed random to make execution deterministic
    import random
    random.seed(42)
    
    report = ShadowExecutionGateway.place_shadow_order("COMI", 100, "BUY", 10.0)
    assert report["success"] is True
    assert report["fill_price"] > 10.19
    assert report["slippage_bps"] > 0
    assert report["latency_ms"] >= 200

@patch("time.sleep")
def test_signal_executor_kill_switch_blocked(mock_sleep, monkeypatch):
    # Enable Kill Switch
    import core.risk.kill_switch
    monkeypatch.setattr(core.risk.kill_switch, "is_kill_switch_active", lambda: True)
    
    # Mock run, settings
    mock_run = MagicMock()
    mock_run.scan_type = "INTRADAY"
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr(settings, "is_live_execution_armed", lambda d: True)
    
    # Query peewee mock
    with patch("database.SignalRun.get_by_id", return_value=mock_run):
        res = SignalExecutor.execute_run(1)
        assert res["status"] == "blocked"
        assert "kill switch" in res["message"]

@patch("time.sleep")
def test_signal_executor_shadow_execution_success(mock_sleep, monkeypatch):
    # Disable Kill Switch
    import core.risk.kill_switch
    monkeypatch.setattr(core.risk.kill_switch, "is_kill_switch_active", lambda: False)
    
    # Enable auto trade
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr(settings, "is_live_execution_armed", lambda d: True)
    
    # Mock portfolio, run, recommendation
    mock_portfolio = MagicMock(id=1, name="Intraday Signals")
    mock_run = MagicMock(id=1, scan_type="INTRADAY")
    mock_rec = MagicMock(
        id=1,
        ticker="COMI",
        entry_price=10.0,
        stop_loss=9.50,
        target_price=11.0,
        target_price_2=11.5,
        side="BUY",
        rationale_json='{"signal_id": "SIG-COMI-123"}'
    )
    
    # Mock SignalExecutor helper functions to bypass complexity
    monkeypatch.setattr(SignalExecutor, "_resolve_execution_portfolio", lambda scan_type, recs: mock_portfolio)
    monkeypatch.setattr(SignalExecutor, "_check_operator_lockout", lambda p: (True, "", {}))
    monkeypatch.setattr(SignalExecutor, "_check_portfolio_heat", lambda p: (True, "", 0))
    monkeypatch.setattr(SignalExecutor, "_validate_signal", lambda r: (True, "", {}))
    monkeypatch.setattr(SignalExecutor, "_run_risk_gates", lambda p, ru, re: (True, "", {}))
    monkeypatch.setattr(SignalExecutor, "_is_market_open", lambda: True)
    
    # Mock peewee DB lookups
    monkeypatch.setattr("database.SignalRun.get_by_id", lambda run_id: mock_run)
    monkeypatch.setattr("database.SignalRecommendation.select", lambda: MagicMock(where=lambda cond: MagicMock(order_by=lambda *args: [mock_rec])))
    
    # Mock cross portfolio duplicate check to return None
    monkeypatch.setattr(SignalExecutor, "_find_cross_portfolio_signal_position", lambda p, t: None)
    monkeypatch.setattr(Position, "get_or_none", lambda *args, **kwargs: None)
    
    # Mock ShadowExecutionGateway to return dummy fill price
    mock_place_order = MagicMock(return_value={
        "success": True,
        "fill_price": 10.05,
        "slippage_bps": 50,
        "latency_ms": 350
    })
    monkeypatch.setattr("core.market.ShadowExecutionGateway.ShadowExecutionGateway.place_shadow_order", mock_place_order)
    
    # Mock PositionTracker.add_position and _persist_execution
    mock_add_position = MagicMock(return_value=True)
    monkeypatch.setattr("core.PositionTracker.add_position", mock_add_position)
    
    mock_execution = MagicMock()
    mock_execution.id = 123
    mock_execution.details_json = "{}"
    mock_execution.open_message_id = None
    mock_persist = MagicMock(return_value=mock_execution)
    monkeypatch.setattr(SignalExecutor, "_persist_execution", mock_persist)
    monkeypatch.setattr(SignalExecutor, "_send_main_channel_signal_message", lambda msg: {"ok": True})
    
    # Execute
    res = SignalExecutor.execute_run(1)
    assert res["status"] == "completed"
    assert res["summary"]["opened"] == 1
    
    # Verify shadow gateway was called
    mock_place_order.assert_called_once_with(
        ticker="COMI",
        shares=pytest.approx(1),  # Calculated shares can vary based on test settings
        side="BUY",
        theoretical_price=10.0,
        signal_id="SIG-COMI-123"
    )
    
    # Verify PositionTracker was called with the latency-adjusted fill price
    mock_add_position.assert_called_once()
    kwargs = mock_add_position.call_args[1]
    assert kwargs["entry_price"] == 10.05
    assert kwargs["slippage_bps"] == 50
    assert kwargs["latency_ms"] == 350
    assert kwargs["signal_id"] == "SIG-COMI-123"
