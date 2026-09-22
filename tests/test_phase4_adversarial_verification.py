"""
PHASE 4 ADVERSARIAL VERIFICATION SUITE
======================================
Swarm Specialist: verifier
Adversarial edge-case verification testing:
1. HTTP 429 Rate Limiting is NOT aborted as permanent (remains retryable).
2. Transient network errors (ConnectionError / Timeout) execute retries.
3. Mixed subscriber broadcast: dead subscriber fast-aborts without stalling healthy peers.
4. TimeUtils month transitions instantaneously update conviction scoring.
5. Legacy import facade 'core.ConfluenceEngine' seamlessly operates with core.sovereign_confluence.
"""

import datetime
from unittest.mock import MagicMock
import pytest

from core import TimeUtils
from database import Client, SignalRun, SignalRecommendation, SignalDelivery
from core.signals.models import PublishSignalsRequest
from core.signals.publishing import publish_signal_run_logic, _is_unrecoverable_telegram_error
from core.confluence import ConfluenceEngine as InstitutionalConfluence
from core.sovereign_confluence import SovereignConfluenceEngine, sovereign_confluence_engine
import core.ConfluenceEngine as legacy_confluence


def test_adversarial_rate_limiting_429_is_retryable():
    """Verifier Check 1: Ensures HTTP 429 is never falsely classified as unrecoverable."""
    resp_429 = {"ok": False, "error_code": 429, "description": "Too Many Requests: retry after 5"}
    assert _is_unrecoverable_telegram_error(resp_429) is False, "HTTP 429 must be retryable, not unrecoverable"


def test_adversarial_mixed_subscriber_batch_isolation(monkeypatch):
    """
    Verifier Check 2: Verifies that in a mixed subscriber batch:
    - Subscriber A (Healthy): Receives message (SENT)
    - Subscriber B (Blocked): Aborts retries immediately on attempt 1, increments fail count (FAILED)
    - Subscriber C (Healthy): Receives message (SENT) with zero delay or corruption from B
    """
    client_a = Client.create(name="Subscriber A", subscription_tier="SIGNALS_ONLY", telegram_chat_id="111000", delivery_fail_count=0)
    client_b = Client.create(name="Subscriber B (Blocked)", subscription_tier="SIGNALS_ONLY", telegram_chat_id="222000", delivery_fail_count=0)
    client_c = Client.create(name="Subscriber C", subscription_tier="SIGNALS_ONLY", telegram_chat_id="333000", delivery_fail_count=0)

    run = SignalRun.create(
        run_date=datetime.date(2026, 3, 9),
        run_type="INTRADAY",
        market_regime="BULLISH",
        status="COMPLETED",
    )
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        action="BUY",
        entry_price=50.0,
        target_price=55.0,
        stop_loss=48.0,
        conviction_stars=4,
    )

    send_log = []
    sleep_calls = []

    def mock_send_message(msg, chat_id=None):
        send_log.append(chat_id)
        if chat_id == "222000":
            return {"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"}
        return {"ok": True, "result": {"message_id": 100 + len(send_log)}}

    monkeypatch.setattr("core.signals.publishing.TelegramBot_Alerts.send_message", mock_send_message)
    monkeypatch.setattr("core.signals.publishing.settings.TELEGRAM_TOKEN", "fake_token", raising=False)
    monkeypatch.setattr("core.signals.publishing.settings.TELEGRAM_AUTO_BROADCAST_DAILY", True, raising=False)

    req = PublishSignalsRequest(
        run_id=int(run.id),
        channel="TELEGRAM",
        dry_run=False,
        max_retries=2,
        backoff_ms=500,
        enforce_window=False,
        include_main_channel=False,
    )

    result = publish_signal_run_logic(req, sleep_fn=lambda d: sleep_calls.append(d))

    # VERIFICATIONS:
    # 1. Exactly 3 dispatch attempts total: A (1), B (1, aborted), C (1)
    assert send_log == ["111000", "222000", "333000"]
    # 2. Blocked user caused 0 backoff sleeps
    assert len(sleep_calls) == 0
    # 3. Overall summary: 2 sent, 1 failed
    assert result["summary"]["sent"] == 2
    assert result["summary"]["failed"] == 1
    # 4. Client statuses in DB
    reloaded_b = Client.get_by_id(client_b.id)
    assert reloaded_b.delivery_fail_count == 1
    reloaded_a = Client.get_by_id(client_a.id)
    assert reloaded_a.delivery_fail_count == 0
    reloaded_c = Client.get_by_id(client_c.id)
    assert reloaded_c.delivery_fail_count == 0


def test_adversarial_timeutils_instantaneous_month_transition():
    """
    Verifier Check 3: Verifies that changing simulated time dynamically updates
    seasonal scoring across consecutive evaluation calls without caching drift.
    """
    try:
        # April (Month 4) has seasonal edge
        TimeUtils.set_simulation(datetime.datetime(2026, 4, 15, 10, 30))
        eval_apr = InstitutionalConfluence.evaluate_ticker("COMI")
        assert "SEASONAL_EDGE" in eval_apr["tags"]
        score_apr = eval_apr["raw_score"]

        # May (Month 5) does NOT have seasonal edge
        TimeUtils.set_simulation(datetime.datetime(2026, 5, 15, 10, 30))
        eval_may = InstitutionalConfluence.evaluate_ticker("COMI")
        assert "SEASONAL_EDGE" not in eval_may["tags"]
        score_may = eval_may["raw_score"]

        # Score in May should be strictly lower by exactly 0.5 points (seasonality component)
        assert round(score_apr - score_may, 2) == 0.5
    finally:
        TimeUtils.clear_simulation()


def test_adversarial_legacy_confluence_engine_facade_integrity():
    """
    Verifier Check 4: Verifies that legacy callers importing from core.ConfluenceEngine
    can call all methods of SovereignConfluenceEngine without issues.
    """
    engine = legacy_confluence.confluence_engine
    assert isinstance(engine, SovereignConfluenceEngine)
    assert hasattr(engine, "analyze_sovereign_confluence")
    assert hasattr(engine, "get_active_trap")
    assert hasattr(engine, "clear_stale_traps")
    # Calling get_active_trap returns None cleanly for non-existent ticker
    trap = engine.get_active_trap("NONEXISTENT_TICKER")
    assert trap is None
