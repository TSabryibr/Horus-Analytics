import pytest
import time
from unittest.mock import MagicMock, patch
from core.analyzers.MomentumBreakoutScanner import detect_manipulation
from core.signals.SignalDispatcher import SignalDispatcher
from database import SignalSuppressionLog, db

def test_l2_bid_depth_gate():
    # Breakout with bid depth (500 shares) < 3x tick volume (200 shares -> 3x is 600)
    is_manip, tag, reason = detect_manipulation(
        rel_volume=2.0,
        price_move_pct=4.0,
        breakout=True,
        avg_turnover=5000000.0,
        bid_depth_shares=500,
        tick_volume=200
    )
    assert is_manip is True
    assert tag == "⚠️ L2_BID_DEPTH_TRAP"
    assert "L2 Bid Depth" in reason

    # Breakout with adequate bid depth (1000 shares) >= 3x tick volume (200 shares)
    is_manip_ok, tag_ok, _ = detect_manipulation(
        rel_volume=2.0,
        price_move_pct=4.0,
        breakout=True,
        avg_turnover=5000000.0,
        bid_depth_shares=1000,
        tick_volume=200
    )
    assert is_manip_ok is False
    assert tag_ok == ""

def test_signal_suppression_logging(monkeypatch):
    mock_signal = {
        "Score": 3, # Low score -> Suppressed
        "Status": "⚠️ LOW_SCORE",
        "Manipulation_Flag": "CLEAR",
        "Projected_Return_%": 2.0,
        "PPP_Hurdle_%": 4.0
    }
    monkeypatch.setattr("core.signals.SignalDispatcher.analyze_stock", MagicMock(return_value=mock_signal))

    dispatcher = SignalDispatcher()
    tick_payload = {"ticker": "EKHO", "price": 20.0, "volume": 1000, "timestamp": time.time()}

    # Clear prior suppression logs for clean assertion
    SignalSuppressionLog.delete().execute()

    dispatcher._process_tick(tick_payload)

    suppressions = list(SignalSuppressionLog.select().where(SignalSuppressionLog.ticker == "EKHO"))
    assert len(suppressions) >= 1
    log_item = suppressions[0]
    assert log_item.ticker == "EKHO"
    assert log_item.score == 3
    assert log_item.suppression_tag in ["PPP_FAILURE", "LOW_SCORE", "LIQUIDITY_TRAP"]
