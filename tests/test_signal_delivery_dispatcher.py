import pytest
import time
from unittest.mock import MagicMock, patch
from core.signals.SignalDispatcher import SignalDispatcher
from database import Signal, db

def test_signal_delivery_valid_dispatch(monkeypatch):
    # Mock analyze_stock to return a valid breakout signal
    mock_signal = {
        "Score": 5,
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
    tick_payload = {"ticker": "COMI", "price": 15.50, "volume": 50000, "timestamp": time.time()}
    dispatcher._process_tick(tick_payload)

    # Assert Telegram message was sent
    mock_telegram.assert_called_once()
    sent_text = mock_telegram.call_args[0][0]
    assert "COMI" in sent_text
    assert "15.50" in sent_text

    # Assert Webhook was broadcasted
    mock_webhook.assert_called_once_with("EGX_SIGNAL_ALERT", mock_signal)

def test_signal_delivery_suppressed_by_risk_gate(monkeypatch):
    # Mock analyze_stock to return a manipulated breakout signal
    mock_signal = {
        "Score": 5,
        "Status": "⚠️ LOW_VOL_BREAKOUT",
        "Manipulation_Flag": "LOW_VOL_BREAKOUT",
        "Projected_Return_%": 12.0,
        "PPP_Hurdle_%": 4.0
    }
    monkeypatch.setattr("core.signals.SignalDispatcher.analyze_stock", MagicMock(return_value=mock_signal))
    
    mock_telegram = MagicMock()
    mock_webhook = MagicMock()
    monkeypatch.setattr("core.signals.SignalDispatcher.send_message", mock_telegram)
    monkeypatch.setattr("core.signals.SignalDispatcher.send_webhook", mock_webhook)

    dispatcher = SignalDispatcher()
    tick_payload = {"ticker": "COMI", "price": 15.50, "volume": 1000, "timestamp": time.time()}
    dispatcher._process_tick(tick_payload)

    # Dispatches should be suppressed
    mock_telegram.assert_not_called()
    mock_webhook.assert_not_called()
