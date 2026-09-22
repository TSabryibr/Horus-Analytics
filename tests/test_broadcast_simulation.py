"""
BROADCAST SIMULATION TEST
=========================
End-to-end simulation test for the Horus signal broadcast pipeline.

Tests all 3 scan types (Intraday, Pre-Close, Daily Signal), the deduplication
logic per scan_label, Telegram broadcast payloads, signal card generation,
and scheduler trigger routing.

All Telegram calls are mocked — no real messages are ever sent.
"""
from core.settings import settings
import api
import pytest
import datetime
import json
import os
import io
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Helpers: Fake signal factory
# ---------------------------------------------------------------------------

def _make_signal(
    ticker: str,
    signal_type: str = "RSI_REVERSAL",
    entry: float = 50.0,
    stop_loss: float = 47.0,
    target: float = 55.0,
    target2: float = 57.0,
    score: int = 8,
    rsi: float = 32.5,
    volume_x: float = 2.1,
    confirmation: str = "PROVISIONAL",
    sector: str = "Banking",
    date: datetime.datetime | None = None,
):
    """Create a fake signal dict matching the DailyScanner output schema."""
    if date is None:
        from core import TimeUtils
        date = TimeUtils.now()
    return {
        "Ticker": ticker,
        "Signal_Type": signal_type,
        "Entry_Price": entry,
        "Stop_Loss": stop_loss,
        "Target_Price": target,
        "Target_Price_2": target2,
        "Score": score,
        "RSI": rsi,
        "Volume_x": volume_x,
        "Volume_Spike": volume_x,
        "Confirmation": confirmation,
        "Sector": sector,
        "Date": date,
        "Alpha_Rationale": [f"{signal_type} triggered", f"Volume spike {volume_x}x"],
    }


def _dedup_file_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sent_signals.json")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_dedup():
    """Ensure dedup file is clean before and after each test."""
    from utils.redis_client import redis_client
    redis_client.clear()
    path = _dedup_file_path()
    if os.path.exists(path):
        os.remove(path)
    yield
    redis_client.clear()
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def broadcast_spy(monkeypatch):
    """Spy on all broadcast calls without actually sending anything."""
    messages_sent = []
    images_sent = []

    def _fake_send_message(msg, chat_id=None, token=None):
        messages_sent.append(msg)
        return {"status": "ok", "mocked": True}

    def _fake_send_image(buf, caption=""):
        images_sent.append(caption)
        return {"status": "ok", "mocked": True}

    monkeypatch.setattr("core.TelegramBot_Alerts.send_message", _fake_send_message)
    monkeypatch.setattr("core.TelegramBot_Alerts.send_message", lambda msg: _fake_send_message(msg))
    monkeypatch.setattr("core.TelegramBot_Alerts.send_image", _fake_send_image)

    return {"messages": messages_sent, "images": images_sent}


@pytest.fixture
def enable_broadcasts(monkeypatch):
    """Enable all broadcast toggles in """
    monkeypatch.setattr(settings, "TELEGRAM_ENABLED", True)
    monkeypatch.setattr(settings, "DISCORD_ENABLED", False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", True)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_DAILY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(settings, "ENABLE_INTRADAY_ALERTS", True)


@pytest.fixture
def mock_report_card(monkeypatch):
    """Mock signal card generation to return a tiny fake image buffer."""
    fake_buf = io.BytesIO(b"FAKE_IMAGE_DATA")

    def _fake_card(**kwargs):
        return io.BytesIO(b"FAKE_IMAGE_DATA")

    monkeypatch.setattr("core.ReportGenerator.create_horus_signal_card", _fake_card)
    return _fake_card


@pytest.fixture
def bypass_pipeline_gate(monkeypatch):
    """Bypass the data freshness pipeline gate."""
    _ok = lambda **kwargs: {"overall_ok": True, "issues": [], "reason": None}
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda label="": True)
    monkeypatch.setattr("core.scheduling._ensure_scheduler_data_ready", lambda scan_label: True)
    # Patch at import origin AND at the already-imported reference inside runs.py
    monkeypatch.setattr("routes.data.evaluate_data_freshness_logic", _ok)
    monkeypatch.setattr("routes.signals.evaluate_data_freshness_logic", _ok, raising=False)
    monkeypatch.setattr("core.signals.runs.evaluate_data_freshness_logic", _ok)



@pytest.fixture
def mock_market_open(monkeypatch):
    """Make the system think the market is open."""
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")
    monkeypatch.setattr(settings, "get_market_close_hour_minute", lambda: (14, 30))
    monkeypatch.setattr(settings, "PRE_CLOSE_OFFSET_MINS", 20)


# ===========================================================================
# TEST CLASS 1: Intraday Broadcast + Deduplication
# ===========================================================================

class TestIntradayBroadcastFlow:
    """
    Phase 1a: 2 stocks (COMI, EAST) detected → both broadcast
    Phase 1b: 15 min later, 3 stocks (COMI, EAST, HRHO) → only HRHO broadcasts (dedup)
    """

    def test_intraday_batch1_broadcasts_both_signals(
        self,
        setup_test_db,
        broadcast_spy,
        enable_broadcasts,
        mock_report_card,
        bypass_pipeline_gate,
        monkeypatch,
    ):
        import api
        import core.scheduling
        from core import TimeUtils
        now = datetime.datetime(2026, 3, 5, 11, 0, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now)
        monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())

        signals_batch1 = [
            _make_signal("COMI", entry=52.30, confirmation="PROVISIONAL", date=now),
            _make_signal("EAST", signal_type="MACD_CROSS", entry=18.50, confirmation="PROVISIONAL", date=now),
        ]

        monkeypatch.setattr(
            "core.DailyScanner.get_market_signals",
            lambda **kw: (signals_batch1, [], 55.0, "BULLISH"),
        )

        core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

        msgs = broadcast_spy["messages"]
        imgs = broadcast_spy["images"]

        # Should have: regime header + individual signal broadcasts + full summary
        assert any("[INTRADAY ALERT]" in m for m in msgs), f"Missing INTRADAY ALERT header. Messages: {msgs}"
        assert any("COMI" in m for m in msgs), f"COMI not found in broadcasts. Messages: {msgs}"
        assert any("EAST" in m for m in msgs), f"EAST not found in broadcasts. Messages: {msgs}"

        # Signal cards should have been generated
        assert len(imgs) == 2, f"Expected 2 signal cards, got {len(imgs)}: {imgs}"

    def test_intraday_batch2_dedup_only_new(
        self,
        setup_test_db,
        broadcast_spy,
        enable_broadcasts,
        mock_report_card,
        bypass_pipeline_gate,
        monkeypatch,
    ):
        import api
        import core.scheduling
        from core import TimeUtils
        now = datetime.datetime(2026, 3, 5, 11, 0, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now)
        monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())

        # --- Phase A: First batch (seeds dedup state) ---
        signals_batch1 = [
            _make_signal("COMI", confirmation="PROVISIONAL", date=now),
            _make_signal("EAST", confirmation="PROVISIONAL", date=now),
        ]
        monkeypatch.setattr(
            "core.DailyScanner.get_market_signals",
            lambda **kw: (signals_batch1, [], 55.0, "BULLISH"),
        )
        core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

        # Reset spy
        broadcast_spy["messages"].clear()
        broadcast_spy["images"].clear()

        # --- Phase B: 15 min later - 3 stocks, 2 are dupes ---
        now2 = datetime.datetime(2026, 3, 5, 11, 15, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now2)

        signals_batch2 = [
            _make_signal("COMI", confirmation="PROVISIONAL", date=now2),
            _make_signal("EAST", confirmation="PROVISIONAL", date=now2),
            _make_signal("HRHO", signal_type="BREAKOUT", entry=4.20, confirmation="PROVISIONAL", date=now2),
        ]
        monkeypatch.setattr(
            "core.DailyScanner.get_market_signals",
            lambda **kw: (signals_batch2, [], 55.0, "BULLISH"),
        )
        core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

        msgs = broadcast_spy["messages"]
        imgs = broadcast_spy["images"]

        # The pipeline has TWO broadcast phases:
        # 1) Pre-dedup "HIGH CONVICTION" messages (lines 115-128 of api.py) — fires for ALL signals
        # 2) Post-dedup cards + [FULL SUMMARY] — only fires for NEW (non-dedup) signals
        #
        # We validate dedup through the FULL SUMMARY and signal cards (post-dedup outputs):
        
        # The FULL SUMMARY should only contain HRHO (the new ticker)
        summary_msgs = [m for m in msgs if "FULL SUMMARY" in m]
        assert len(summary_msgs) == 1, f"Expected 1 FULL SUMMARY message, got {len(summary_msgs)}"
        assert "HRHO" in summary_msgs[0], f"HRHO should be in FULL SUMMARY. Got: {summary_msgs[0]}"
        assert "COMI" not in summary_msgs[0], f"COMI should NOT be in FULL SUMMARY (dedup). Got: {summary_msgs[0]}"
        assert "EAST" not in summary_msgs[0], f"EAST should NOT be in FULL SUMMARY (dedup). Got: {summary_msgs[0]}"
        
        # Only 1 signal card should be generated (HRHO)
        assert len(imgs) == 1, f"Expected 1 signal card (HRHO only), got {len(imgs)}: {imgs}"

    def test_dedup_file_contains_correct_state(
        self,
        setup_test_db,
        broadcast_spy,
        enable_broadcasts,
        mock_report_card,
        bypass_pipeline_gate,
        monkeypatch,
    ):
        import api
        import core.scheduling
        from core import TimeUtils
        now = datetime.datetime(2026, 3, 5, 11, 0, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now)
        monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())

        signals = [
            _make_signal("COMI", confirmation="PROVISIONAL", date=now),
            _make_signal("EAST", confirmation="PROVISIONAL", date=now),
        ]
        monkeypatch.setattr(
            "core.DailyScanner.get_market_signals",
            lambda **kw: (signals, [], 55.0, "BULLISH"),
        )
        core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

        path = _dedup_file_path()
        assert os.path.exists(path), "Dedup file should exist after broadcast"

        with open(path) as f:
            state = json.load(f)

        today_str = "2026-03-05"
        assert today_str in state, f"Today's date not in dedup state: {state}"
        assert "INTRADAY" in state[today_str], f"INTRADAY label missing: {state[today_str]}"
        assert set(state[today_str]["INTRADAY"]) == {"COMI", "EAST"}, \
            f"Unexpected dedup tickers: {state[today_str]['INTRADAY']}"


# ===========================================================================
# TEST CLASS 2: Pre-Close Broadcast
# ===========================================================================

class TestPreCloseBroadcastFlow:
    """
    4 tickers broadcast under PRE-CLOSE label.
    Since PRE-CLOSE is a separate dedup namespace, even tickers from INTRADAY reappear.
    """

    def test_pre_close_broadcasts_all_four(
        self,
        setup_test_db,
        broadcast_spy,
        enable_broadcasts,
        mock_report_card,
        bypass_pipeline_gate,
        monkeypatch,
    ):
        import api
        import core.scheduling
        from core import TimeUtils
        now = datetime.datetime(2026, 3, 5, 14, 10, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now)
        monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
        monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")

        signals = [
            _make_signal("COMI", confirmation="PRE-CLOSE", date=now),
            _make_signal("EAST", confirmation="PRE-CLOSE", date=now),
            _make_signal("HRHO", confirmation="PRE-CLOSE", date=now),
            _make_signal("SWDY", signal_type="VOLUME_BREAKOUT", entry=9.80, confirmation="PRE-CLOSE", date=now),
        ]
        monkeypatch.setattr(
            "core.DailyScanner.get_market_signals",
            lambda **kw: (signals, [], 60.0, "BULLISH"),
        )

        core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="PRE-CLOSE")

        msgs = broadcast_spy["messages"]
        imgs = broadcast_spy["images"]

        # Header should say DAILY CLOSE REPORT (since is_intraday=False)
        assert any("[DAILY CLOSE REPORT]" in m for m in msgs), \
            f"Missing [DAILY CLOSE REPORT] header. Messages: {msgs}"

        # All 4 tickers should appear in signal cards (capped at 3 cards, but summary has all)
        assert any("FULL SUMMARY" in m for m in msgs), f"Missing FULL SUMMARY message. Messages: {msgs}"

        # Signal cards capped at 3
        assert len(imgs) == 4, f"Expected 4 signal cards (all signals), got {len(imgs)}"

    def test_pre_close_dedup_separate_from_intraday(
        self,
        setup_test_db,
        broadcast_spy,
        enable_broadcasts,
        mock_report_card,
        bypass_pipeline_gate,
        monkeypatch,
    ):
        import api
        import core.scheduling
        from core import TimeUtils
        now = datetime.datetime(2026, 3, 5, 11, 0, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now)
        monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
        monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")

        # Seed INTRADAY dedup with COMI
        intraday_signals = [_make_signal("COMI", confirmation="PROVISIONAL", date=now)]
        monkeypatch.setattr(
            "core.DailyScanner.get_market_signals",
            lambda **kw: (intraday_signals, [], 55.0, "BULLISH"),
        )
        core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

        broadcast_spy["messages"].clear()
        broadcast_spy["images"].clear()

        # Now run PRE-CLOSE with same COMI — should NOT be blocked
        now2 = datetime.datetime(2026, 3, 5, 14, 10, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now2)

        pre_close_signals = [_make_signal("COMI", confirmation="PRE-CLOSE", date=now2)]
        monkeypatch.setattr(
            "core.DailyScanner.get_market_signals",
            lambda **kw: (pre_close_signals, [], 55.0, "BULLISH"),
        )
        core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="PRE-CLOSE")

        msgs = broadcast_spy["messages"]
        # COMI should still broadcast under PRE-CLOSE since it's a different dedup label
        assert any("COMI" in m for m in msgs), \
            f"COMI should broadcast under PRE-CLOSE (separate dedup). Messages: {msgs}"


# ===========================================================================
# TEST CLASS 3: Daily Signal Broadcast
# ===========================================================================

class TestDailySignalBroadcastFlow:
    """
    Daily signal scan after market close with CONFIRMED signals.
    """

    def test_daily_signal_broadcasts_confirmed(
        self,
        setup_test_db,
        broadcast_spy,
        enable_broadcasts,
        mock_report_card,
        bypass_pipeline_gate,
        monkeypatch,
    ):
        import api
        import core.scheduling
        from core import TimeUtils
        # After market close
        now = datetime.datetime(2026, 3, 5, 15, 0, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now)
        monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
        monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")

        signals = [
            _make_signal("COMI", confirmation="PRE-CLOSE", date=now),
            _make_signal("HRHO", signal_type="GOLDEN_CROSS", confirmation="PRE-CLOSE", date=now),
            _make_signal("SWDY", signal_type="RSI_DIVERGENCE", confirmation="PRE-CLOSE", date=now),
        ]
        monkeypatch.setattr(
            "core.DailyScanner.get_market_signals",
            lambda **kw: (signals, [], 58.0, "BULLISH"),
        )

        core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="DAILY SIGNAL")

        msgs = broadcast_spy["messages"]
        imgs = broadcast_spy["images"]

        # Header
        assert any("[DAILY CLOSE REPORT]" in m for m in msgs), \
            f"Missing header. Messages: {msgs}"

        # Since time > MARKET_END_TIME, PRE-CLOSE signals should get relabeled to CONFIRMED
        # (This is handled by the stale guardrail in scheduled_scan_logic)

        # Signal cards
        assert len(imgs) == 3, f"Expected 3 signal cards, got {len(imgs)}"

    def test_daily_signal_saves_to_database(
        self,
        setup_test_db,
        broadcast_spy,
        enable_broadcasts,
        mock_report_card,
        bypass_pipeline_gate,
        monkeypatch,
    ):
        import api
        import core.scheduling
        from core import TimeUtils
        from database import Signal

        now = datetime.datetime(2026, 3, 5, 15, 0, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now)
        monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
        monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")

        signals = [
            _make_signal("COMI", confirmation="PRE-CLOSE", date=now),
        ]
        monkeypatch.setattr(
            "core.DailyScanner.get_market_signals",
            lambda **kw: (signals, [], 58.0, "BULLISH"),
        )

        core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="DAILY SIGNAL")

        # Check DB
        db_signals = list(Signal.select().where(Signal.ticker == "COMI"))
        assert len(db_signals) >= 1, f"Expected COMI in Signal table, found {len(db_signals)}"
        assert db_signals[0].signal_type == "RSI_REVERSAL"
        assert db_signals[0].source == "RUN:DAILY"


# ===========================================================================
# TEST CLASS 4: Scheduler Trigger Routing
# ===========================================================================

class TestSchedulerTriggers:
    """
    Verify that each scheduler function routes to scheduled_scan_logic
    with the correct is_intraday + scan_label parameters.
    """

    def test_scheduled_intraday_scan_routes_correctly(
        self,
        setup_test_db,
        bypass_pipeline_gate,
        mock_market_open,
        monkeypatch,
    ):
        import api
        import core.scheduling
        from core import TimeUtils
        # Set time to mid-market (not near close)
        now = datetime.datetime(2026, 3, 5, 11, 0, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now)
        monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())

        calls = []
        original_logic = core.scheduling.scheduled_scan_logic

        def _spy(is_intraday, scan_label=""):
            calls.append({"is_intraday": is_intraday, "scan_label": scan_label})

        monkeypatch.setattr("core.scheduling.scheduled_scan_logic", _spy)
        core.scheduling.scheduled_intraday_scan()

        assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
        assert calls[0]["is_intraday"] is True
        assert calls[0]["scan_label"] == "INTRADAY"

    def test_scheduled_pre_close_scan_routes_correctly(
        self,
        setup_test_db,
        bypass_pipeline_gate,
        monkeypatch,
    ):
        import api
        import core.scheduling

        calls = []

        def _spy(is_intraday, scan_label="", **kwargs):
            calls.append({"is_intraday": is_intraday, "scan_label": scan_label})

        monkeypatch.setattr("core.scheduling.scheduled_scan_logic", _spy)
        core.scheduling.scheduled_pre_close_scan()

        assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
        assert calls[0]["is_intraday"] is False
        assert calls[0]["scan_label"] == "PRE-CLOSE"

    def test_scheduled_daily_signal_scan_routes_correctly(
        self,
        setup_test_db,
        bypass_pipeline_gate,
        monkeypatch,
    ):
        import api
        import core.scheduling

        calls = []

        def _spy(is_intraday, scan_label="", **kwargs):
            calls.append({"is_intraday": is_intraday, "scan_label": scan_label, **kwargs})

        monkeypatch.setattr("core.scheduling.scheduled_scan_logic", _spy)
        core.scheduling.scheduled_daily_signal_scan()

        assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
        assert calls[0]["is_intraday"] is False
        assert calls[0]["scan_label"] == "DAILY SIGNAL"
        assert calls[0].get("preview_only") is True

    def test_scheduled_morning_daily_signal_scan_routes_correctly(
        self,
        setup_test_db,
        bypass_pipeline_gate,
        monkeypatch,
    ):
        import core.scheduling
        from core import TimeUtils

        calls = []

        def _spy(is_intraday, scan_label="", **kwargs):
            calls.append({"is_intraday": is_intraday, "scan_label": scan_label, **kwargs})
            return True

        # Ensure pre-market time (09:30 AM on a Sunday - EGX trading day)
        fixed_now = TimeUtils.now().replace(hour=9, minute=30, second=0)
        # Ensure it's not a weekend in EGX (Sun=6, Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5)
        # Roll back to Sunday if current weekday is Fri/Sat
        while fixed_now.weekday() in (4, 5):
            fixed_now -= datetime.timedelta(days=1)

        monkeypatch.setattr(TimeUtils, "now", lambda: fixed_now)
        monkeypatch.setattr("core.scheduling.scheduled_scan_logic", _spy)

        res = core.scheduling.scheduled_morning_daily_signal_scan()
        assert res is True
        assert len(calls) == 1, f"Expected 1 call, got {len(calls)}"
        assert calls[0]["is_intraday"] is False
        assert calls[0]["scan_label"] == "DAILY SIGNAL"
        assert calls[0].get("preview_only") is False

    def test_intraday_scan_skips_near_close(
        self,
        setup_test_db,
        bypass_pipeline_gate,
        mock_market_open,
        monkeypatch,
    ):
        """Intraday scan should skip near close only if pre-close has completed today."""
        import api
        import core.scheduling
        from core import TimeUtils
        # Set time to 14:15, which is within 20min (PRE_CLOSE_OFFSET_MINS) of 14:30
        now = datetime.datetime(2026, 3, 5, 14, 15, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now)

        calls = []

        def _spy(is_intraday, scan_label="", _late_data=False):
            calls.append({"is_intraday": is_intraday, "scan_label": scan_label})

        monkeypatch.setattr("core.scheduling.scheduled_scan_logic", _spy)
        
        # Reset and mark pre-close completed -> should skip
        run_date = now.date().isoformat()
        core.scheduling._PRE_CLOSE_COMPLETED_DATES.clear()
        core.scheduling._mark_pre_close_completed(run_date)
        
        core.scheduling.scheduled_intraday_scan()
        assert len(calls) == 0, f"Intraday scan should be skipped near close when pre-close completed, but got: {calls}"

        # Clear completion mark -> should run to maintain coverage
        core.scheduling._PRE_CLOSE_COMPLETED_DATES.clear()
        core.scheduling.scheduled_intraday_scan()
        assert len(calls) == 1, "Intraday scan should run near close if pre-close is not completed yet"
        assert calls[0]["is_intraday"] is True


    def test_intraday_scan_skips_during_time_travel_backfill(
        self,
        setup_test_db,
        bypass_pipeline_gate,
        mock_market_open,
        monkeypatch,
    ):
        import core.scheduling

        now = datetime.datetime(2026, 3, 5, 11, 0, 0)
        monkeypatch.setattr("core.TimeUtils.now", lambda: now)
        monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: True)

        calls = []

        def _spy(is_intraday, scan_label=""):
            calls.append({"is_intraday": is_intraday, "scan_label": scan_label})

        monkeypatch.setattr("core.scheduling.scheduled_scan_logic", _spy)
        core.scheduling.scheduled_intraday_scan()

        assert calls == []


# ===========================================================================
# TEST CLASS 5: Format & Summary Verification
# ===========================================================================

class TestFormatAndSummary:
    """Verify that TelegramBot_Alerts.format_signal_alert produces correct output."""

    def test_format_signal_alert_output(self):
        from core import TelegramBot_Alerts
        signals = [
            _make_signal("COMI", entry=52.30, stop_loss=49.80, target=56.0),
            _make_signal("EAST", entry=18.50, stop_loss=17.20, target=20.0),
        ]

        result = TelegramBot_Alerts.format_signal_alert(signals)

        assert isinstance(result, str), "format_signal_alert should return a string"
        assert "COMI" in result, "COMI should be in the formatted output"
        assert "EAST" in result, "EAST should be in the formatted output"
        assert len(result) > 50, f"Output too short: {result}"
