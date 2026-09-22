import pytest
import time
from unittest.mock import MagicMock
from core.signals.ShadowLiveRunner import ShadowLiveRunner

def test_shadow_live_runner_processing(monkeypatch):
    mock_signal = {
        "Score": 7,
        "Status": "⚡ BREAKOUT - CONFIRMED",
        "Manipulation_Flag": "CLEAR",
        "Projected_Return_%": 15.0,
        "PPP_Hurdle_%": 4.0,
        "Stop_Loss": 45.0,
        "Target_1": 52.0,
        "Target_2": 58.0
    }
    monkeypatch.setattr("core.signals.ShadowLiveRunner.analyze_stock", MagicMock(return_value=mock_signal))

    runner = ShadowLiveRunner(shadow_mode=True)
    outcome = runner.process_shadow_tick("COMI", price=48.0)

    assert outcome is not None
    assert outcome.ticker == "COMI"
    assert outcome.entry_price == 48.0

    metrics = runner.get_forward_test_metrics()
    assert metrics["mode"] == "SHADOW_LIVE_FORWARD_TEST"
    assert metrics["total_forward_signals"] >= 1
