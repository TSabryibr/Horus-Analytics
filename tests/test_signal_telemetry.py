import pytest
import time
from unittest.mock import MagicMock, patch
from core.signals.StreamHealthWatchdog import StreamHealthWatchdog
from core.signals.SignalTelemetryTracker import SignalTelemetryTracker
from core.analyzers.MomentumBreakoutScanner import detect_manipulation
from database import LegacySignalOutcome, db

def test_stream_health_watchdog():
    watchdog = StreamHealthWatchdog(max_stale_seconds=0.2)
    assert watchdog.get_status()["healthy"] is True

    # Record a tick
    watchdog.record_tick()
    assert watchdog.get_status()["stale_duration_sec"] < 0.2

    # Simulate stale state
    watchdog.last_tick_time = time.time() - 1.0
    status = watchdog.get_status()
    assert status["healthy"] is False
    assert status["stale_duration_sec"] >= 1.0

def test_signal_telemetry_tracker_lifecycle():
    tracker = SignalTelemetryTracker()
    
    from database import Signal
    sig = Signal.create(
        ticker="SWDY",
        price=100.0,
        score=7,
        signal_type="⚡ BREAKOUT",
        rationale='{"Target_1": 110.0, "Target_2": 120.0, "Stop_Loss": 95.0}'
    )
    outcome = tracker.record_signal_entry("SWDY", price=100.0, signal_obj=sig)
    assert outcome is not None
    assert outcome.ticker == "SWDY"
    assert outcome.entry_price == 100.0
    assert outcome.outcome_status == "ACTIVE"

    # Simulate tick move up to 112.0 (TP1 hit)
    tracker.update_price_tick("SWDY", 112.0)

    tracker.update_price_tick("SWDY", 112.0)
    updated = LegacySignalOutcome.get_by_id(outcome.id)
    assert updated.max_price == 112.0
    assert updated.target_1_hit is True
    assert updated.outcome_status == "WIN_TP1"

    # Fetch summary
    summary = tracker.get_telemetry_summary()
    assert summary["total_signals"] >= 1
    assert summary["tp1_hits"] >= 1

def test_dynamic_telemetry_feedback_tuning(monkeypatch):
    # Setup poor historical telemetry for ticker "FAKESHIP" (2 losses)
    LegacySignalOutcome.create(ticker="FAKESHIP", entry_price=10.0, max_price=10.0, min_price=8.0, current_price=8.0, stop_loss_hit=True, outcome_status="LOSS_SL")
    LegacySignalOutcome.create(ticker="FAKESHIP", entry_price=10.0, max_price=10.0, min_price=8.0, current_price=8.0, stop_loss_hit=True, outcome_status="LOSS_SL")

    # Breakout with rel_volume=1.0 (between standard 0.8 and dynamic 1.2 threshold)
    is_manip, tag, reason = detect_manipulation(
        rel_volume=1.0,
        price_move_pct=4.0,
        breakout=True,
        avg_turnover=5000000.0,
        ticker="FAKESHIP"
    )
    assert is_manip is True
    assert tag == "⚠️ DYNAMIC_TELEMETRY_TRAP"
    assert "1.20 dynamic threshold" in reason
