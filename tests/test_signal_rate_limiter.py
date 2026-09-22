import pytest
import time
from unittest.mock import MagicMock, patch
from core.analyzers.MomentumBreakoutScanner import detect_manipulation
from core.signals.SignalDispatcher import SignalDispatcher

def test_detect_manipulation_hard_turnover_floor():
    # Breakout on stock with turnover below 1.5M EGP (e.g. 500k EGP)
    is_manip, tag, reason = detect_manipulation(
        rel_volume=2.0,
        price_move_pct=4.0,
        breakout=True,
        avg_turnover=500000.0 # 500k EGP
    )
    assert is_manip is True
    assert tag == "⚠️ ILLIQUID_TURNOVER_TRAP"
    assert "hard liquidity floor" in reason

    # Breakout on stock with adequate turnover (e.g. 5.0M EGP)
    is_manip_ok, tag_ok, _ = detect_manipulation(
        rel_volume=2.0,
        price_move_pct=4.0,
        breakout=True,
        avg_turnover=5000000.0 # 5.0M EGP
    )
    assert is_manip_ok is False
    assert tag_ok == ""

def test_signal_dispatcher_rate_limiting_cooldown(monkeypatch):
    mock_signal = {
        "Score": 6,
        "Status": "⚡ BREAKOUT - CONFIRMED",
        "Manipulation_Flag": "CLEAR",
        "Projected_Return_%": 12.0,
        "PPP_Hurdle_%": 4.0,
        "Stop_Loss": 14.50,
        "Target_1": 16.50,
        "Target_2": 18.00
    }
    monkeypatch.setattr("core.signals.SignalDispatcher.analyze_stock", MagicMock(return_value=mock_signal))
    
    mock_telegram = MagicMock()
    mock_webhook = MagicMock()
    monkeypatch.setattr("core.signals.SignalDispatcher.send_message", mock_telegram)
    monkeypatch.setattr("core.signals.SignalDispatcher.send_webhook", mock_webhook)

    dispatcher = SignalDispatcher()
    dispatcher.cooldown_sec = 60 # Set 60 second cooldown for testing

    tick_payload = {"ticker": "COMI", "price": 15.50, "volume": 50000, "timestamp": time.time()}

    # First tick -> Alert dispatched
    dispatcher._process_tick(tick_payload)
    assert mock_telegram.call_count == 1
    assert mock_webhook.call_count == 1

    # Second tick immediately after -> Alert rate-limited (suppressed)
    dispatcher._process_tick(tick_payload)
    assert mock_telegram.call_count == 1
    assert mock_webhook.call_count == 1

    # Simulate time passing beyond cooldown
    dispatcher._last_alert_time["COMI"] = time.time() - 65

    # Third tick after cooldown -> Alert dispatched again
    dispatcher._process_tick(tick_payload)
    assert mock_telegram.call_count == 2
    assert mock_webhook.call_count == 2
