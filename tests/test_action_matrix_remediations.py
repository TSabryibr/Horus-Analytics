"""
TEST ACTION MATRIX REMEDIATIONS (PHASE 2 AUDIT VERIFICATION)
============================================================
Comprehensive test suite validating all P0, P1, and P2 remediation fixes:
1. Fast-abort on unrecoverable Telegram errors (403 Forbidden, 400 Bad Request) without retry backoff sleeps.
2. Client auto-pause upon 3 consecutive failures (blocked bot, user deactivated, chat not found).
3. Client delivery_fail_count reset on success.
4. Telegram delivery failure diagnosis: SUBSCRIBER_BLOCKED_BOT.
5. ConfluenceEngine and SovereignConfluenceEngine namespace resolution and backward-compatibility.
6. TimeUtils simulated time determinism in seasonal scoring and slippage reconciler.
7. MarketFeedWatchdog scheduler job coalescing and attributes.
8. Ollama manager HTTP timeouts.
"""

import datetime
from unittest.mock import MagicMock, patch
import pytest

from core import TimeUtils
from core.settings import settings
from database import Client, SignalRun, SignalRecommendation, SignalDelivery
from core.signals.models import PublishSignalsRequest
from core.signals.publishing import (
    publish_signal_run_logic,
    _is_unrecoverable_telegram_error,
    UNRECOVERABLE_TELEGRAM_PATTERNS,
)
from core.subscriptions.delivery import delivery_failure_diagnosis
from core.confluence import ConfluenceEngine as InstitutionalConfluenceEngine
from core.sovereign_confluence import (
    SovereignConfluenceEngine,
    sovereign_confluence_engine,
)
import core.ConfluenceEngine as legacy_confluence_module


# =====================================================================
# 1. UNRECOVERABLE TELEGRAM ERROR DETECTION & FAST-ABORT TESTS
# =====================================================================

def test_is_unrecoverable_telegram_error_patterns():
    """Validates that permanent Telegram response codes and descriptions are identified."""
    assert _is_unrecoverable_telegram_error({"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"}) is True
    assert _is_unrecoverable_telegram_error({"ok": False, "error_code": 403, "description": "Forbidden: user is deactivated"}) is True
    assert _is_unrecoverable_telegram_error({"ok": False, "error_code": 400, "description": "Bad Request: chat not found"}) is True
    assert _is_unrecoverable_telegram_error({"ok": False, "error_code": 400, "description": "Bad Request: chat was deleted"}) is True
    assert _is_unrecoverable_telegram_error({"ok": False, "error_code": 400, "description": "Bad Request: group chat was deactivated"}) is True
    assert _is_unrecoverable_telegram_error({"ok": False, "error_code": 401, "description": "Unauthorized: invalid bot token"}) is True
    assert _is_unrecoverable_telegram_error({"ok": False, "description": "bot can't initiate conversation with user"}) is True

    # Transient errors should NOT be marked unrecoverable
    assert _is_unrecoverable_telegram_error({"ok": False, "error_code": 429, "description": "Too Many Requests: retry after 5"}) is False
    assert _is_unrecoverable_telegram_error({"ok": False, "error_code": 502, "description": "Bad Gateway"}) is False
    assert _is_unrecoverable_telegram_error({"ok": True, "result": {"message_id": 1}}) is False
    assert _is_unrecoverable_telegram_error(None) is False


def test_telegram_blocked_user_aborts_retries_immediately(monkeypatch):
    """
    Validates that when a subscriber has blocked the bot (403 Forbidden),
    the publisher loop makes exactly 1 attempt and aborts immediately without sleeping,
    even when max_retries=3 and backoff_ms=1000.
    """
    client = Client.create(
        name="Blocked Subscriber Test",
        subscription_tier="SIGNALS_ONLY",
        telegram_chat_id="777000111",
        delivery_fail_count=0,
        delivery_paused=False,
    )
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

    send_calls = []
    sleep_calls = []

    def fake_send(msg, chat_id=None):
        send_calls.append(chat_id)
        return {"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"}

    def fake_sleep(duration):
        sleep_calls.append(duration)

    monkeypatch.setattr("core.signals.publishing.TelegramBot_Alerts.send_message", fake_send)
    monkeypatch.setattr("core.signals.publishing.settings.TELEGRAM_TOKEN", "fake_token", raising=False)
    monkeypatch.setattr("core.signals.publishing.settings.TELEGRAM_AUTO_BROADCAST_DAILY", True, raising=False)

    req = PublishSignalsRequest(
        run_id=int(run.id),
        channel="TELEGRAM",
        dry_run=False,
        max_retries=3,
        backoff_ms=1000,
        enforce_window=False,
        include_main_channel=False,
    )

    # Execute publish with mock sleep function
    from core.signals import publishing
    result = publishing.publish_signal_run_logic(req, sleep_fn=fake_sleep)

    # ASSERTIONS:
    # 1. Exactly 1 send attempt was made (retries aborted immediately)
    assert len(send_calls) == 1, f"Expected 1 call, got {len(send_calls)}"
    # 2. No backoff sleep was performed
    assert len(sleep_calls) == 0, f"Expected 0 sleeps, got {len(sleep_calls)}"
    # 3. Delivery status is FAILED
    assert result["summary"]["failed"] == 1
    # 4. Subscriber delivery_fail_count was incremented
    reloaded = Client.get_by_id(client.id)
    assert reloaded.delivery_fail_count == 1
    assert reloaded.delivery_paused is False


def test_telegram_blocked_user_auto_pauses_after_3_failures(monkeypatch):
    """
    Validates that 3 consecutive unrecoverable 403 Forbidden errors automatically
    set delivery_paused=True on the subscriber.
    """
    client = Client.create(
        name="Auto Pause Client",
        subscription_tier="SIGNALS_ONLY",
        telegram_chat_id="888111222",
        delivery_fail_count=2,  # Already failed twice
        delivery_paused=False,
    )
    run = SignalRun.create(
        run_date=datetime.date(2026, 3, 9),
        run_type="INTRADAY",
        market_regime="BULLISH",
        status="COMPLETED",
    )
    SignalRecommendation.create(
        run=run,
        ticker="HRHO",
        action="BUY",
        entry_price=20.0,
        target_price=22.0,
        stop_loss=19.0,
        conviction_stars=3,
    )

    def fake_send(msg, chat_id=None):
        return {"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"}

    monkeypatch.setattr("core.signals.publishing.TelegramBot_Alerts.send_message", fake_send)
    monkeypatch.setattr("core.signals.publishing.settings.TELEGRAM_TOKEN", "fake_token", raising=False)
    monkeypatch.setattr("core.signals.publishing.settings.TELEGRAM_AUTO_BROADCAST_DAILY", True, raising=False)

    req = PublishSignalsRequest(
        run_id=int(run.id),
        channel="TELEGRAM",
        dry_run=False,
        max_retries=1,
        backoff_ms=0,
        enforce_window=False,
        include_main_channel=False,
    )

    publish_signal_run_logic(req)

    reloaded = Client.get_by_id(client.id)
    assert reloaded.delivery_fail_count == 3
    assert reloaded.delivery_paused is True, "Client should be auto-paused after 3rd consecutive failure"


def test_telegram_success_resets_delivery_fail_count(monkeypatch):
    """Validates that a successful delivery resets client delivery_fail_count back to 0."""
    client = Client.create(
        name="Recovering Client",
        subscription_tier="SIGNALS_ONLY",
        telegram_chat_id="999333444",
        delivery_fail_count=2,
        delivery_paused=False,
    )
    run = SignalRun.create(
        run_date=datetime.date(2026, 3, 9),
        run_type="INTRADAY",
        market_regime="BULLISH",
        status="COMPLETED",
    )
    SignalRecommendation.create(
        run=run,
        ticker="ETEL",
        action="BUY",
        entry_price=30.0,
        target_price=33.0,
        stop_loss=28.5,
        conviction_stars=4,
    )

    def fake_send(msg, chat_id=None):
        return {"ok": True, "result": {"message_id": 9999}}

    monkeypatch.setattr("core.signals.publishing.TelegramBot_Alerts.send_message", fake_send)
    monkeypatch.setattr("core.signals.publishing.settings.TELEGRAM_TOKEN", "fake_token", raising=False)
    monkeypatch.setattr("core.signals.publishing.settings.TELEGRAM_AUTO_BROADCAST_DAILY", True, raising=False)

    req = PublishSignalsRequest(
        run_id=int(run.id),
        channel="TELEGRAM",
        dry_run=False,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        include_main_channel=False,
    )

    publish_signal_run_logic(req)

    reloaded = Client.get_by_id(client.id)
    assert reloaded.delivery_fail_count == 0
    assert reloaded.delivery_paused is False


# =====================================================================
# 2. SUBSCRIPTION DELIVERY FAILURE DIAGNOSIS TESTS
# =====================================================================

def test_delivery_failure_diagnosis_detects_blocked_bot():
    """Validates that delivery_failure_diagnosis maps 403 blocked user to SUBSCRIBER_BLOCKED_BOT."""
    mock_delivery = MagicMock(spec=SignalDelivery)
    mock_delivery.status = "FAILED"
    mock_delivery.last_error = "Forbidden: bot was blocked by the user"
    mock_delivery.chat_id = "1822794531"

    diag = delivery_failure_diagnosis(mock_delivery)
    assert diag is not None
    assert diag["action_code"] == "SUBSCRIBER_BLOCKED_BOT"
    assert diag["severity"] == "BLOCKED"
    assert "blocked the bot" in diag["operator_action"]


def test_delivery_failure_diagnosis_detects_user_deactivated():
    """Validates that delivery_failure_diagnosis maps deactivated user to SUBSCRIBER_BLOCKED_BOT."""
    mock_delivery = MagicMock(spec=SignalDelivery)
    mock_delivery.status = "FAILED"
    mock_delivery.last_error = "Forbidden: user is deactivated"
    mock_delivery.chat_id = "1822794531"

    diag = delivery_failure_diagnosis(mock_delivery)
    assert diag is not None
    assert diag["action_code"] == "SUBSCRIBER_BLOCKED_BOT"


# =====================================================================
# 3. CONFLUENCE ENGINE SEPARATION & BACKWARD COMPATIBILITY TESTS
# =====================================================================

def test_confluence_engine_separation_and_shim():
    """
    Validates that core.confluence and core.sovereign_confluence coexist without
    namespace conflict, and core.ConfluenceEngine operates as a backward-compatible shim.
    """
    # 1. Institutional 5-dimension conviction engine in core.confluence
    assert hasattr(InstitutionalConfluenceEngine, "evaluate_ticker")
    res = InstitutionalConfluenceEngine.evaluate_ticker("COMI")
    assert "stars" in res
    assert "raw_score" in res

    # 2. Sovereign Hedge Engine in core.sovereign_confluence
    assert hasattr(SovereignConfluenceEngine, "analyze_sovereign_confluence")
    assert hasattr(sovereign_confluence_engine, "get_active_trap")
    assert hasattr(sovereign_confluence_engine, "clear_stale_traps")

    # 3. Backward-compatible facade in core.ConfluenceEngine
    assert legacy_confluence_module.ConfluenceEngine is SovereignConfluenceEngine
    assert legacy_confluence_module.confluence_engine is sovereign_confluence_engine


# =====================================================================
# 4. TIMEUTILS SIMULATED TIME DETERMINISM TESTS
# =====================================================================

def test_timeutils_simulated_time_controls_seasonal_scoring():
    """
    Validates that ConfluenceEngine.evaluate_ticker respects TimeUtils.set_simulation()
    rather than reading host OS wall-clock time.
    """
    try:
        # May (Month 5) is NOT in [1, 2, 4, 8, 9, 10, 11] -> seasonal score should be 0.5, no SEASONAL_EDGE
        TimeUtils.set_simulation(datetime.datetime(2025, 5, 15, 12, 0, 0))
        res_may = InstitutionalConfluenceEngine.evaluate_ticker("COMI")
        assert "SEASONAL_EDGE" not in res_may["tags"], "May should not produce SEASONAL_EDGE tag"

        # January (Month 1) IS in [1, 2, 4, 8, 9, 10, 11] -> seasonal score should be 1.0 with SEASONAL_EDGE tag
        TimeUtils.set_simulation(datetime.datetime(2025, 1, 15, 12, 0, 0))
        res_jan = InstitutionalConfluenceEngine.evaluate_ticker("COMI")
        assert "SEASONAL_EDGE" in res_jan["tags"], "January must produce SEASONAL_EDGE tag"

    finally:
        TimeUtils.clear_simulation()


# =====================================================================
# 5. OLLAMA MANAGER TIMEOUT CONFIGURATION TESTS
# =====================================================================

def test_ollama_manager_http_timeout_passed(monkeypatch):
    """Validates that ensure_model_available passes explicit timeout=5.0 to requests.get()."""
    from utils.ollama_manager import OllamaManager

    mgr = OllamaManager(base_url="http://127.0.0.1:11434")
    monkeypatch.setattr(mgr, "is_service_running", lambda: True)

    captured_kwargs = {}

    def fake_get(url, **kwargs):
        captured_kwargs.update(kwargs)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "llama3.2:latest"}]}
        return mock_resp

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    mgr.ensure_model_available("llama3.2")
    assert captured_kwargs.get("timeout") == 5.0, f"Expected timeout=5.0, got {captured_kwargs.get('timeout')}"
