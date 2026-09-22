"""
BROADCAST RELIABILITY TESTS
===========================
Targeted regression tests for intermittent failures in the 3 broadcast workflows:
- INTRADAY
- DAILY (PRE-CLOSE / DAILY SIGNAL)
- HORUS MomentumBreakoutScanner
"""

from core.settings import settings
import datetime
import io
import pytest
import requests


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def _make_signal(ticker: str):
    return {
        "Ticker": ticker,
        "Signal_Type": "RSI_REVERSAL",
        "Entry_Price": 50.0,
        "Stop_Loss": 47.0,
        "Target_Price": 55.0,
        "Target_Price_2": 57.0,
        "Score": 8,
        "RSI": 32.5,
        "Volume_x": 2.1,
        "Date": datetime.datetime(2026, 3, 9, 11, 0, 0),
        "Alpha_Rationale": ["test"],
    }


@pytest.fixture(autouse=True)
def _isolate_dedup_file(tmp_path, monkeypatch):
    from core import AlertManager
    from utils.redis_client import redis_client
    dedup_file = tmp_path / "sent_signals.json"
    monkeypatch.setattr(AlertManager, "DEDUP_FILE", str(dedup_file), raising=False)
    monkeypatch.setattr(redis_client, "get", lambda *a, **kw: None)
    monkeypatch.setattr(redis_client, "set", lambda *a, **kw: True)



@pytest.fixture(autouse=True)
def _reset_scheduler_memory():
    import core.scheduling

    with core.scheduling._NO_SIGNAL_NOTICE_LOCK:
        core.scheduling._NO_SIGNAL_NOTICE_KEYS.clear()
    with core.scheduling._AI_DAILY_REPORT_LOCK:
        core.scheduling._AI_DAILY_REPORT_PENDING_DATES.clear()
        core.scheduling._AI_DAILY_REPORT_SENT_DATES.clear()
    with core.scheduling._DAILY_SIGNAL_LOCK:
        core.scheduling._DAILY_SIGNAL_PENDING_DATES.clear()
        core.scheduling._DAILY_SIGNAL_COMPLETED_DATES.clear()
    yield
    with core.scheduling._NO_SIGNAL_NOTICE_LOCK:
        core.scheduling._NO_SIGNAL_NOTICE_KEYS.clear()
    with core.scheduling._AI_DAILY_REPORT_LOCK:
        core.scheduling._AI_DAILY_REPORT_PENDING_DATES.clear()
        core.scheduling._AI_DAILY_REPORT_SENT_DATES.clear()
    with core.scheduling._DAILY_SIGNAL_LOCK:
        core.scheduling._DAILY_SIGNAL_PENDING_DATES.clear()
        core.scheduling._DAILY_SIGNAL_COMPLETED_DATES.clear()


@pytest.fixture(autouse=True)
def _default_scheduler_run_completed(request, monkeypatch):
    unpatched_tests = {
        "test_persist_scheduler_signal_run_preserves_existing_daily_run_with_signals",
        "test_scheduled_daily_signal_scan_skips_when_existing_daily_run_has_signals",
    }
    if request.node.name in unpatched_tests:
        return
    monkeypatch.setattr(
        "core.scheduling._persist_scheduler_signal_run",
        lambda **kwargs: {"status": "completed", "run": {"id": 123}},
    )


def test_dedup_normalizes_scan_label_and_ticker_case(tmp_path, monkeypatch):
    from core import AlertManager
    dedup_file = tmp_path / "sent_signals.json"
    monkeypatch.setattr("core.AlertManager.DEDUP_FILE", str(dedup_file))
    monkeypatch.setattr("core.TimeUtils.today", lambda: datetime.date(2026, 3, 9))

    first = AlertManager.filter_new_signals([{"Ticker": "COMI"}], " INTRADAY ")
    second = AlertManager.filter_new_signals([{"Ticker": "comi"}], "INTRADAY")

    assert len(first) == 1
    assert second == []


def test_dedup_logs_drop_reason_for_suppressed_repeat(tmp_path, monkeypatch, caplog):
    from core import AlertManager
    dedup_file = tmp_path / "sent_signals.json"
    monkeypatch.setattr("core.AlertManager.DEDUP_FILE", str(dedup_file))
    monkeypatch.setattr("core.TimeUtils.today", lambda: datetime.date(2026, 3, 9))
    monkeypatch.setattr("core.TimeUtils.now", lambda: datetime.datetime(2026, 3, 9, 11, 0, 0))

    AlertManager.filter_new_signals([{"Ticker": "COMI", "Score": 8}], "INTRADAY")

    with caplog.at_level("INFO", logger="horus.alerts"):
        second = AlertManager.filter_new_signals([{"Ticker": "COMI", "Score": 8}], "INTRADAY")

    assert second == []
    assert "label=INTRADAY" in caplog.text
    assert "dropped_tickers=['COMI']" in caplog.text
    assert "repeat_cooldown" in caplog.text


def test_send_message_falls_back_to_plain_text_on_markdown_parse_error(monkeypatch):
    from core import TelegramBot_Alerts
    calls = []
    responses = [
        _FakeResponse({"ok": False, "description": "Bad Request: can't parse entities"}),
        _FakeResponse({"ok": True, "result": {"message_id": 1}}),
    ]

    def _fake_post(url, json=None, timeout=10):
        calls.append({"url": url, "json": dict(json or {}), "timeout": timeout})
        return responses.pop(0)

    monkeypatch.setattr("requests.post", _fake_post)
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token")
    monkeypatch.setattr(settings, "CHAT_ID", "chat")

    res = TelegramBot_Alerts.send_message("*bad_markdown_[")

    assert res.get("ok") is True
    assert len(calls) == 2
    assert calls[0]["json"].get("parse_mode") == "Markdown"
    assert "parse_mode" not in calls[1]["json"]


def test_send_image_falls_back_to_plain_caption_on_markdown_parse_error(monkeypatch):
    from core import TelegramBot_Alerts
    calls = []
    responses = [
        _FakeResponse({"ok": False, "description": "Bad Request: can't parse entities"}),
        _FakeResponse({"ok": True, "result": {"message_id": 2}}),
    ]

    def _fake_post(url, files=None, data=None, timeout=None):
        calls.append(
            {
                "url": url,
                "data": dict(data or {}),
                "timeout": timeout,
            }
        )
        return responses.pop(0)

    monkeypatch.setattr("requests.post", _fake_post)
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token")
    monkeypatch.setattr(settings, "CHAT_ID", "chat")

    res = TelegramBot_Alerts.send_image(io.BytesIO(b"img"), caption="*bad_markdown_[")

    assert res.get("ok") is True
    assert len(calls) == 2
    assert calls[0]["data"].get("parse_mode") == "Markdown"
    assert "parse_mode" not in calls[1]["data"]


def test_send_message_redacts_bot_token_from_transport_failures(monkeypatch, caplog):
    from core import TelegramBot_Alerts

    token = "123456:SECRET_TOKEN"

    def _raise_timeout(*args, **kwargs):
        raise requests.exceptions.ConnectTimeout(
            "HTTPSConnectionPool(host='api.telegram.org', port=443): "
            "Max retries exceeded with url: /bot123456:SECRET_TOKEN/sendMessage"
        )

    monkeypatch.setattr("requests.post", _raise_timeout)
    monkeypatch.setattr("core.TelegramBot_Alerts.time.sleep", lambda _seconds: None)
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", token)
    monkeypatch.setattr(settings, "CHAT_ID", "chat")

    with caplog.at_level("WARNING", logger="horus.telegram"):
        res = TelegramBot_Alerts.send_message("hello")

    assert res.get("ok") is False
    assert token not in str(res.get("description") or "")
    assert token not in caplog.text
    assert "/bot<redacted>/" in caplog.text
    assert not [record for record in caplog.records if record.levelname == "ERROR"]


def test_send_message_preserves_retryable_telegram_api_error(monkeypatch):
    from core import TelegramBot_Alerts

    calls = []
    sleeps = []

    def _rate_limited(url, json=None, timeout=10):
        calls.append({"url": url, "json": dict(json or {}), "timeout": timeout})
        return _FakeResponse(
            {
                "ok": False,
                "error_code": 429,
                "description": "Too Many Requests: retry after 1",
                "parameters": {"retry_after": 1},
            }
        )

    monkeypatch.setattr("requests.post", _rate_limited)
    monkeypatch.setattr("core.TelegramBot_Alerts.time.sleep", lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token")
    monkeypatch.setattr(settings, "CHAT_ID", "chat")

    res = TelegramBot_Alerts.send_message("hello")

    assert res == {"ok": False, "description": "429: Too Many Requests: retry after 1"}
    assert len(calls) == 3
    assert sleeps == [1, 1]


def test_handle_commands_uses_actual_token_from_config_dict(monkeypatch):
    from core import TelegramBot_Alerts

    requested_urls = []

    def _capture_url(url, *args, **kwargs):
        requested_urls.append(url)
        raise KeyboardInterrupt("stop")

    monkeypatch.setattr(
        "core.TelegramBot_Alerts._current_telegram_config",
        lambda: {"token": "real_token", "chat_id": "real_chat"},
    )
    monkeypatch.setattr("core.TelegramBot_Alerts.requests.get", _capture_url)

    with pytest.raises(KeyboardInterrupt):
        TelegramBot_Alerts.handle_commands()

    assert requested_urls == ["https://api.telegram.org/botreal_token/getUpdates"]


def test_scheduled_scan_logic_uses_default_scan_label_when_blank(
    setup_test_db,
    monkeypatch,
):
    import api
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 11, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr("api.get_excluded_tickers_upper", lambda: set())
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kw: ([_make_signal("EAST")], [], 55.0, "BULLISH"),
    )
    monkeypatch.setattr(
        "core.scheduling._persist_scheduler_signal_run",
        lambda **kwargs: {"status": "completed", "run": {"id": 123}},
    )
    seen_labels = []
    original_filter = core.scheduling.AlertManager.filter_new_signals

    def _capture_labels(signals, scan_label):
        seen_labels.append(scan_label)
        return original_filter(signals, scan_label)

    monkeypatch.setattr("core.scheduling.AlertManager.filter_new_signals", _capture_labels)
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_alert", lambda *args, **kwargs: {"ok": True})
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_image", lambda *args, **kwargs: {"ok": True})

    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="")

    assert "INTRADAY" in seen_labels


def test_pre_close_scan_keeps_prior_day_candidates_for_broadcast(
    setup_test_db,
    monkeypatch,
):
    import api
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 13, 10, 0)
    stale_sig_dt = datetime.datetime(2026, 3, 8, 14, 30, 0)
    stale_signal = _make_signal("ALUM")
    stale_signal["Date"] = stale_sig_dt
    stale_signal["Confirmation"] = "PRE-CLOSE"

    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "MARKET_END_TIME", "13:30")
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_DAILY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kw: ([stale_signal], [], 55.0, "BULLISH"),
    )
    monkeypatch.setattr(
        "core.ReportGenerator.create_horus_signal_card",
        lambda **kwargs: io.BytesIO(b"FAKE"),
    )

    messages = []
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda msg, **kwargs: messages.append(msg) or {"ok": True})
    monkeypatch.setattr("core.AlertManager.broadcast_image", lambda *args, **kwargs: {"ok": True})

    core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="PRE-CLOSE")

    assert any("ALUM" in m for m in messages)


def test_daily_signal_broadcasts_no_signal_notice_once(
    setup_test_db,
    monkeypatch,
):
    import api
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 14, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_DAILY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kw: ([], [], 42.0, "CAUTIOUS"),
    )

    messages = []
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda msg, **kwargs: messages.append(msg) or {"ok": True})
    monkeypatch.setattr("core.AlertManager.broadcast_image", lambda *args, **kwargs: {"ok": True})

    core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="DAILY SIGNAL")
    core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="DAILY SIGNAL")

    no_signal_msgs = [m for m in messages if "NO ELIGIBLE SIGNALS" in m.upper()]
    assert len(no_signal_msgs) == 1


def test_pre_close_broadcasts_no_signal_notice_once(
    setup_test_db,
    monkeypatch,
):
    import api
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 13, 10, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_DAILY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kw: ([], [], 42.0, "CAUTIOUS"),
    )

    messages = []
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda msg, **kwargs: messages.append(msg) or {"ok": True})
    monkeypatch.setattr("core.AlertManager.broadcast_image", lambda *args, **kwargs: {"ok": True})

    core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="PRE-CLOSE")
    core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="PRE-CLOSE")

    no_signal_msgs = [m for m in messages if "NO ELIGIBLE SIGNALS" in m.upper()]
    assert len(no_signal_msgs) == 1
    assert any("PRE-CLOSE" in m.upper() for m in no_signal_msgs)


def test_intraday_suppresses_no_signal_notice_by_default(
    setup_test_db,
    monkeypatch,
):
    import api
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 11, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(settings, "TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS", False, raising=False)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kw: ([], [], 42.0, "CAUTIOUS"),
    )

    messages = []
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda msg, **kwargs: messages.append(msg) or {"ok": True})
    monkeypatch.setattr("core.AlertManager.broadcast_image", lambda *args, **kwargs: {"ok": True})

    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")
    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

    no_signal_msgs = [m for m in messages if "NO ELIGIBLE SIGNALS" in m.upper()]
    assert len(no_signal_msgs) == 0

    # Explicitly opted-in
    monkeypatch.setattr(settings, "TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS", True, raising=False)
    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")
    no_signal_msgs = [m for m in messages if "NO ELIGIBLE SIGNALS" in m.upper()]
    assert len(no_signal_msgs) == 1
    assert any("INTRADAY" in m.upper() for m in no_signal_msgs)


def test_intraday_no_signal_notice_respects_main_channel_none_policy(
    setup_test_db,
    monkeypatch,
):
    import api
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 11, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "none", raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kw: ([], [], 42.0, "CAUTIOUS"),
    )

    messages = []
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda msg, **kwargs: messages.append(msg) or {"ok": True})
    monkeypatch.setattr("core.AlertManager.broadcast_image", lambda *args, **kwargs: {"ok": True})

    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

    assert messages == []


def test_intraday_broadcasts_status_when_all_signals_were_already_sent(
    setup_test_db,
    monkeypatch,
):
    import api
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 11, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kw: ([_make_signal("EAST")], [], 55.0, "BULLISH"),
    )
    monkeypatch.setattr(
        "core.ReportGenerator.create_horus_signal_card",
        lambda **kwargs: io.BytesIO(b"FAKE"),
    )

    messages = []
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_alert", lambda msg, **kwargs: messages.append(msg) or {"ok": True})
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_image", lambda *args, **kwargs: {"ok": True})

    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")
    messages.clear()
    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

    # By default, intraday suppresses no-signal notice even after dedup
    assert messages == []

    # When opted-in, it broadcasts notice
    monkeypatch.setattr(settings, "TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS", True, raising=False)
    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")
    assert any("ALREADY SENT EARLIER TODAY" in m.upper() for m in messages)


def test_blocked_signal_run_does_not_broadcast_stale_scanner_output(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 11, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", True)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kw: ([_make_signal("EAST")], [], 55.0, "BULLISH"),
    )
    monkeypatch.setattr(
        "core.scheduling._persist_scheduler_signal_run",
        lambda **kwargs: {
            "status": "blocked",
            "block_type": "freshness",
            "block_reason": "freshness_gate_failed",
            "message": "Run blocked by data freshness gate.",
        },
    )

    messages = []
    images = []
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_alert", lambda msg, **kwargs: messages.append(msg) or {"ok": True})
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_image", lambda img, caption="", **kwargs: images.append(caption) or {"ok": True})
    monkeypatch.setattr(
        "core.scheduling.AlertManager.filter_new_signals",
        lambda *args, **kwargs: pytest.fail("blocked runs must not enter Telegram dedup"),
    )

    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

    assert messages == []
    assert images == []


def test_pre_close_heat_block_broadcasts_watchlist_only(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 13, 10, 0)
    signal = _make_signal("ALUM")
    signal["Confirmation"] = "PRE-CLOSE"

    monkeypatch.setenv("SIGNAL_AUTO_EXECUTION_ENABLED", "1")
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "MARKET_END_TIME", "13:30")
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_DAILY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kw: ([signal], [], 55.0, "BULLISH"),
    )
    monkeypatch.setattr(
        "core.ReportGenerator.create_horus_signal_card",
        lambda **kwargs: io.BytesIO(b"FAKE"),
    )
    monkeypatch.setattr(
        "core.scheduling._persist_scheduler_signal_run",
        lambda **kwargs: {"status": "completed", "run": {"id": 123}},
    )
    monkeypatch.setattr(
        "core.scheduling.SignalExecutor.execute_run",
        lambda run_id: {
            "status": "blocked",
            "message": "Portfolio heat limit reached",
            "blocked_reason": "heat_limit_reached",
        },
    )

    messages = []
    captions = []
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_alert", lambda msg, **kwargs: messages.append(msg) or {"ok": True})
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_image", lambda img, caption="", **kwargs: captions.append(caption) or {"ok": True})

    core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="PRE-CLOSE")

    assert any("WATCHLIST ONLY" in m.upper() for m in messages)
    assert any("HEAT LIMIT" in m.upper() for m in messages)
    assert captions and all("WATCHLIST ONLY" in c.upper() for c in captions)


def test_scheduler_logs_dedup_filter_reason(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 11, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kw: ([_make_signal("EAST")], [], 55.0, "BULLISH"),
    )
    monkeypatch.setattr(
        "core.ReportGenerator.create_horus_signal_card",
        lambda **kwargs: io.BytesIO(b"FAKE"),
    )
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_alert", lambda *args, **kwargs: {"ok": True})
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_image", lambda *args, **kwargs: {"ok": True})

    logs = []
    monkeypatch.setattr("core.scheduling.logger.info", lambda msg: logs.append(msg))

    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")
    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

    assert any("dedup filtered all" in str(rec).lower() for rec in logs)


def test_scheduler_wrappers_log_skip_reasons(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling

    logs = []
    monkeypatch.setattr("core.scheduling.logger.info", lambda msg: logs.append(msg))
    monkeypatch.setattr("core.scheduling.logger.warning", lambda msg: logs.append(msg))

    monkeypatch.setattr(settings, "is_market_open", lambda: False)
    core.scheduling.scheduled_intraday_scan()
    assert any("market is closed" in str(m).lower() for m in logs)

    logs.clear()
    core.scheduling._PRE_CLOSE_COMPLETED_DATES.clear()
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda action_name: False)
    core.scheduling.scheduled_pre_close_scan()
    assert any("pipeline gate blocked" in str(m).lower() for m in logs)

    logs.clear()
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda action_name: False)
    core.scheduling.scheduled_daily_signal_scan()
    assert any("pipeline gate blocked" in str(m).lower() for m in logs)


def test_daily_signal_scan_uses_daily_history_path(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling

    captured_kwargs = []
    monkeypatch.setattr("core.TimeUtils.today", lambda: datetime.date(2026, 3, 9))
    monkeypatch.setattr("core.TimeUtils.now", lambda: datetime.datetime(2026, 3, 9, 15, 0, 0))
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda action_name: True)
    monkeypatch.setattr("core.scheduling._ensure_scheduler_data_ready", lambda scan_label: True, raising=False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_DAILY", False)
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_alert", lambda *args, **kwargs: {"ok": True})

    def _fake_market_signals(**kwargs):
        captured_kwargs.append(kwargs)
        return ([], [], 0.0, "BULLISH")

    monkeypatch.setattr("core.DailyScanner.get_market_signals", _fake_market_signals)

    core.scheduling.scheduled_daily_signal_scan()

    assert captured_kwargs
    assert captured_kwargs[0]["is_intraday"] is False
    assert captured_kwargs[0].get("is_pre_close") is False


def test_daily_signal_scan_skips_until_history_is_ready(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling

    logs = []
    scans = []
    monkeypatch.setattr("core.TimeUtils.today", lambda: datetime.date(2026, 3, 9))
    monkeypatch.setattr("core.TimeUtils.now", lambda: datetime.datetime(2026, 3, 9, 15, 0, 0))
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda action_name: True)
    monkeypatch.setattr("core.scheduling._ensure_scheduler_data_ready", lambda scan_label: False, raising=False)
    monkeypatch.setattr("core.scheduling.logger.info", lambda msg, *args: logs.append((msg, args)))
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kwargs: scans.append(kwargs) or ([], [], 0.0, "BULLISH"),
    )

    core.scheduling.scheduled_daily_signal_scan()

    assert scans == []
    assert any("data not ready" in str(msg).lower() for msg, _args in logs)


def test_daily_signal_scan_triggers_telegram_warning_after_max_retries(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling
    from core.scheduling import _DAILY_SIGNAL_RETRY_COUNTS, _DATA_WAITING_NOTICE_SENT_DATES

    _DAILY_SIGNAL_RETRY_COUNTS.clear()
    _DATA_WAITING_NOTICE_SENT_DATES.clear()

    monkeypatch.setenv("DAILY_SIGNAL_MAX_RETRIES", "2")
    monkeypatch.setenv("DAILY_SIGNAL_FORCE_ON_TIMEOUT", "0")
    monkeypatch.setattr("core.TimeUtils.today", lambda: datetime.date(2026, 3, 9))
    monkeypatch.setattr("core.TimeUtils.now", lambda: datetime.datetime(2026, 3, 9, 15, 0, 0))
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda action_name: True)

    monkeypatch.setattr("core.scheduling._scheduler_freshness", lambda *args: {})
    monkeypatch.setattr("core.scheduling._daily_signal_history_ready", lambda *args: False)
    monkeypatch.setattr("core.scheduling._sync_scheduler_data", lambda *args: None)

    alerts = []
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_alert", lambda msg, **kw: alerts.append(msg))

    core.scheduling.scheduled_daily_signal_scan()
    warning_alerts = [a for a in alerts if "Daily signal scan failed" in a]
    assert warning_alerts == []

    core.scheduling.scheduled_daily_signal_scan()
    warning_alerts = [a for a in alerts if "Daily signal scan failed" in a]
    assert len(warning_alerts) == 1
    assert "Daily signal scan failed after 2 retries" in warning_alerts[0]


def test_daily_signal_scan_forces_fallback_on_timeout(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling
    from core.scheduling import _DAILY_SIGNAL_RETRY_COUNTS

    _DAILY_SIGNAL_RETRY_COUNTS.clear()

    monkeypatch.setenv("DAILY_SIGNAL_MAX_RETRIES", "1")
    monkeypatch.setenv("DAILY_SIGNAL_FORCE_ON_TIMEOUT", "1")
    monkeypatch.setattr("core.TimeUtils.today", lambda: datetime.date(2026, 3, 9))
    monkeypatch.setattr("core.TimeUtils.now", lambda: datetime.datetime(2026, 3, 9, 15, 0, 0))
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda action_name: True)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_DAILY", False)

    monkeypatch.setattr("core.scheduling._scheduler_freshness", lambda *args: {})
    monkeypatch.setattr("core.scheduling._daily_signal_history_ready", lambda *args: False)
    monkeypatch.setattr("core.scheduling._sync_scheduler_data", lambda *args: None)
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_alert", lambda *args, **kw: {"ok": True})

    scans = []
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kwargs: scans.append(kwargs) or ([], [], 0.0, "BULLISH"),
    )
    monkeypatch.setattr(
        "core.scheduling._persist_scheduler_signal_run",
        lambda **kwargs: {"status": "completed", "run": {"id": 123}},
    )

    core.scheduling.scheduled_daily_signal_scan()
    assert len(scans) == 1


def test_intraday_scan_skips_registered_holiday(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling
    from database import Holiday

    now = datetime.datetime(2026, 5, 28, 11, 0, 0)
    Holiday.create(date=now.date(), description="Exchange holiday")

    logs = []
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr("core.scheduling.logger.info", lambda msg: logs.append(msg))
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda action_name: True)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kwargs: pytest.fail("holiday scan must not reach scanner"),
    )

    core.scheduling.scheduled_intraday_scan()

    assert any("market is closed" in str(m).lower() for m in logs)


def test_trade_monitor_blocks_when_intraday_prices_are_stale(monkeypatch):
    import core.pipeline

    monkeypatch.setattr(
        "core.pipeline.refresh_pipeline_state",
        lambda force=False: {
            "pipeline_state": "DEGRADED",
            "freshness": {
                "market_open": True,
                "intraday_ok": False,
                "intraday_live_ratio": 0.0,
            },
        },
    )
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", False, raising=False)

    assert core.pipeline.pipeline_allows_active_ops("scheduled_trade_monitor") is False


def test_daily_ai_report_waits_for_current_history_after_close(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 15, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_AI_REPORT", True)
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token")
    monkeypatch.setattr(settings, "CHAT_ID", "chat")

    stale_freshness = {
        "run_date": "2026-03-09",
        "overall_ok": False,
        "last_updated": "2026-03-08",
        "history": {
            "ok": False,
            "last_updated": "2026-03-08",
            "expected_last_working_day": "2026-03-09",
            "kpis": {"fresh_ratio": 0.0},
        },
    }
    monkeypatch.setattr(
        core.scheduling,
        "evaluate_freshness",
        lambda realm, run_date, scan_type="DAILY": stale_freshness,
        raising=False,
    )

    generated = []
    sent = []
    monkeypatch.setattr(
        "core.scheduling.ai_report.get_ai_daily_report",
        lambda **kwargs: generated.append(kwargs) or {"status": "success"},
    )
    monkeypatch.setattr("core.scheduling._build_ai_report_telegram_message", lambda payload: "report")
    monkeypatch.setattr(
        "core.scheduling.TelegramBot_Alerts.send_message",
        lambda message: sent.append(message) or {"ok": True},
    )

    core.scheduling.scheduled_daily_ai_report_dispatch()

    assert generated == []
    assert sent == []


def test_daily_ai_report_sends_when_history_is_fresh_despite_snapshot_cache_warning(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 15, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_AI_REPORT", True)
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token")
    monkeypatch.setattr(settings, "CHAT_ID", "chat")
    monkeypatch.setattr(
        core.scheduling,
        "evaluate_freshness",
        lambda realm, run_date, scan_type="DAILY": {
            "run_date": "2026-03-09",
            "overall_ok": True,
            "last_updated": "2026-03-09",
            "history": {
                "ok": True,
                "last_updated": "2026-03-09",
                "expected_last_working_day": "2026-03-09",
            },
        },
        raising=False,
    )

    sent = []
    monkeypatch.setattr(
        "core.scheduling.ai_report.get_ai_daily_report",
        lambda **kwargs: {
            "status": "success",
            "snapshot_degraded": True,
            "snapshot_degradation": {
                "issues": [
                    {"module": "strategy", "reason": "freshness_stale"},
                ],
            },
        },
    )
    monkeypatch.setattr("core.scheduling._build_ai_report_telegram_message", lambda payload: "report")
    monkeypatch.setattr(
        "core.scheduling.TelegramBot_Alerts.send_message",
        lambda message: sent.append(message) or {"ok": True},
    )

    core.scheduling.scheduled_daily_ai_report_dispatch()

    assert sent == ["report"]
    assert core.scheduling._ai_daily_report_was_sent("2026-03-09")
    assert not core.scheduling._ai_daily_report_is_pending("2026-03-09")


def test_persist_scheduler_signal_run_preserves_existing_daily_run_with_signals(monkeypatch):
    import core.scheduling
    from database import SignalRun

    captured = []
    monkeypatch.setattr("core.TimeUtils.today", lambda: datetime.date(2026, 3, 9))
    monkeypatch.setattr("core.TimeUtils.now", lambda: datetime.datetime(2026, 3, 9, 15, 0, 0))
    SignalRun.create(
        run_date=datetime.date(2026, 3, 9),
        scan_type="DAILY",
        run_key="2026-03-09:DAILY:CONFIRMED",
        status="COMPLETED",
        signals_count=5,
    )
    monkeypatch.setattr(
        "core.scheduling.signals.run_daily_signals_logic",
        lambda req, **kwargs: captured.append(req) or {"status": "completed", "run": {"id": 1}},
    )

    core.scheduling._persist_scheduler_signal_run(
        scan_label="DAILY SIGNAL",
        is_intraday=False,
        signals_list=[],
        monitored=[],
        breadth=0.0,
        regime="CAUTIOUS",
    )

    assert len(captured) == 1
    assert captured[0].scan_type == "DAILY"
    assert captured[0].run_key == "2026-03-09:DAILY:CONFIRMED"
    assert captured[0].force is False


def test_scheduled_daily_signal_scan_skips_when_existing_daily_run_has_signals(monkeypatch):
    import core.scheduling
    from database import SignalRun

    calls = []
    run_date = datetime.date(2026, 3, 9)
    monkeypatch.setattr("core.TimeUtils.today", lambda: run_date)
    monkeypatch.setattr("core.TimeUtils.now", lambda: datetime.datetime(2026, 3, 9, 15, 0, 0))
    monkeypatch.setattr("core.scheduling._pipeline.pipeline_allows_active_ops", lambda job_name: True)
    monkeypatch.setattr("core.scheduling._ensure_scheduler_data_ready", lambda scan_label: True)
    monkeypatch.setattr("core.scheduling.scheduled_scan_logic", lambda **kwargs: calls.append(kwargs) or True)
    SignalRun.create(
        run_date=run_date,
        scan_type="DAILY",
        run_key="2026-03-09:DAILY:PREVIEW",
        status="COMPLETED",
        signals_count=5,
    )

    core.scheduling.scheduled_daily_signal_scan()

    assert calls == []
    assert core.scheduling._daily_signal_was_completed("2026-03-09")


def test_pending_ai_report_dispatches_once_after_admin_data_update(
    setup_test_db,
    monkeypatch,
):
    import core.scheduling

    now = datetime.datetime(2026, 3, 9, 15, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now.date())
    monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_AI_REPORT", True)
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token")
    monkeypatch.setattr(settings, "CHAT_ID", "chat")

    stale_freshness = {
        "run_date": "2026-03-09",
        "overall_ok": False,
        "last_updated": "2026-03-08",
        "history": {
            "ok": False,
            "last_updated": "2026-03-08",
            "expected_last_working_day": "2026-03-09",
        },
    }
    fresh_freshness = {
        "run_date": "2026-03-09",
        "overall_ok": True,
        "last_updated": "2026-03-09",
        "history": {
            "ok": True,
            "last_updated": "2026-03-09",
            "expected_last_working_day": "2026-03-09",
        },
    }
    freshness_checks = [stale_freshness, fresh_freshness, fresh_freshness]
    monkeypatch.setattr(
        core.scheduling,
        "evaluate_freshness",
        lambda realm, run_date, scan_type="DAILY": freshness_checks.pop(0),
        raising=False,
    )

    generated = []
    sent = []
    monkeypatch.setattr(
        "core.scheduling.ai_report.get_ai_daily_report",
        lambda **kwargs: generated.append(kwargs) or {"status": "success"},
    )
    monkeypatch.setattr("core.scheduling._build_ai_report_telegram_message", lambda payload: "report")
    monkeypatch.setattr(
        "core.scheduling.TelegramBot_Alerts.send_message",
        lambda message: sent.append(message) or {"ok": True},
    )

    core.scheduling.scheduled_daily_ai_report_dispatch()
    core.scheduling.maybe_dispatch_pending_ai_daily_report_after_data_update()
    core.scheduling.maybe_dispatch_pending_ai_daily_report_after_data_update()

    assert len(generated) == 1
    assert sent == ["report"]


def test_format_signal_alert_tolerates_missing_or_non_numeric_fields():
    from core import TelegramBot_Alerts
    signals = [
        {
            "Ticker": "COMI",
            "Entry_Price": "bad-number",
            "Target_Price": None,
            "Stop_Loss": None,
            "Volume_x": None,
        }
    ]

    msg = TelegramBot_Alerts.format_signal_alert(signals)

    assert isinstance(msg, str)
    assert "COMI" in msg
