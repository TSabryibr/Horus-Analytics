from core.settings import settings
import datetime
import json

import core.scheduling


def _sample_signal(ticker: str = "COMI"):
    return {
        "Ticker": ticker,
        "Signal_Type": "BUY",
        "Entry_Price": 10.0,
        "Stop_Loss": 9.0,
        "Target_Price": 11.0,
        "Score": 8,
        "Confirmation": "CONFIRMED",
    }


def test_scheduled_scan_logic_persists_intraday_run_with_time_key(monkeypatch):
    now_dt = datetime.datetime(2026, 2, 18, 11, 5, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now_dt)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now_dt.date())
    monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kwargs: ([_sample_signal("INTRA")], [{"Ticker": "AAA"}], 50.0, "BULLISH"),
    )

    captured = {}

    def _fake_run_logic(req, **kwargs):
        captured["scan_type"] = req.scan_type
        captured["run_key"] = req.run_key
        captured["payload"] = kwargs["get_market_signals_fn"]()
        return {"status": "completed", "run": {"id": 7}}

    monkeypatch.setattr("core.scheduling.signals.run_daily_signals_logic", _fake_run_logic)

    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

    assert captured["scan_type"] == "INTRADAY"
    assert captured["run_key"] == "2026-02-18:INTRADAY:11:05"
    assert captured["payload"][0][0]["Ticker"] == "INTRA"


def test_scheduled_scan_logic_persists_pre_close_run(monkeypatch):
    now_dt = datetime.datetime(2026, 2, 18, 14, 10, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now_dt)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now_dt.date())
    monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_DAILY", False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kwargs: ([_sample_signal("PREC")], [{"Ticker": "AAA"}], 60.0, "CAUTIOUS"),
    )

    captured = {}

    def _fake_run_logic(req, **kwargs):
        captured["scan_type"] = req.scan_type
        captured["run_key"] = req.run_key
        captured["payload"] = kwargs["get_market_signals_fn"]()
        return {"status": "completed", "run": {"id": 8}}

    monkeypatch.setattr("core.scheduling.signals.run_daily_signals_logic", _fake_run_logic)

    core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="PRE-CLOSE")

    assert captured["scan_type"] == "PRE_CLOSE"
    assert captured["run_key"] == "2026-02-18:PRE_CLOSE"
    assert captured["payload"][0][0]["Ticker"] == "PREC"


def test_scheduled_daily_reconciles_pre_close_before_broadcast_dedup(monkeypatch):
    now_dt = datetime.datetime(2026, 2, 18, 15, 0, 0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now_dt)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now_dt.date())
    monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_DAILY", False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(settings, "MARKET_END_TIME", "14:30")
    sample = _sample_signal("COMI")
    sample["Date"] = now_dt.isoformat()
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kwargs: ([sample], [{"Ticker": "AAA"}], 60.0, "BULLISH"),
    )

    def _fake_run_logic(req, **kwargs):
        return {"status": "completed", "run": {"id": 91}}

    captured = {}
    monkeypatch.setattr("core.scheduling.signals.run_daily_signals_logic", _fake_run_logic)
    monkeypatch.setattr(
        "core.scheduling._reconcile_scheduler_pre_close_previews",
        lambda **kwargs: captured.update(kwargs) or {"status": "completed", "summary": {}},
    )
    monkeypatch.setattr(
        "core.scheduling.AlertManager.filter_new_signals",
        lambda items, _label: [],
    )

    core.scheduling.scheduled_scan_logic(is_intraday=False, scan_label="DAILY SIGNAL")

    assert captured["final_daily_tickers"] == {"COMI"}
    assert captured["run_date"] == now_dt.date()


def test_scheduler_pre_close_reconcile_processes_cancelled_followups(monkeypatch):
    run_date = datetime.date(2026, 2, 18)
    monkeypatch.setattr(
        "core.scheduling.reconcile_pre_close_previews",
        lambda **kwargs: {
            "status": "completed",
            "summary": {
                "confirmed_lifecycles": 0,
                "cancelled_lifecycles": 1,
                "cancelled_pending_entries": 0,
            },
        },
    )
    processed = {}
    monkeypatch.setattr(
        "core.scheduling.process_signal_followups",
        lambda **kwargs: processed.update(kwargs) or {"status": "completed", "summary": {"sent": 1}},
    )

    result = core.scheduling._reconcile_scheduler_pre_close_previews(
        final_daily_tickers=set(),
        run_date=run_date,
    )

    assert result["status"] == "completed"
    assert processed["limit"] >= 1
    assert processed["send_message_fn"] is core.scheduling.TelegramBot_Alerts.send_message


def test_scheduled_scan_logic_executes_horus_for_completed_intraday_run_when_auto_trade_enabled(monkeypatch):
    now_dt = datetime.datetime(2026, 2, 18, 11, 5, 0)
    monkeypatch.setenv("SIGNAL_AUTO_EXECUTION_ENABLED", "1")
    monkeypatch.setattr("core.TimeUtils.now", lambda: now_dt)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now_dt.date())
    monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kwargs: ([_sample_signal("INTRA")], [{"Ticker": "AAA"}], 50.0, "BULLISH"),
    )

    executed = {}

    monkeypatch.setattr(
        "core.scheduling.signals.run_daily_signals_logic",
        lambda req, **kwargs: {"status": "completed", "run": {"id": 17}},
    )
    monkeypatch.setattr("core.scheduling.execute_run_for_horus", lambda run_id: executed.setdefault("run_id", run_id))

    core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY")

    assert executed["run_id"] == 17


def test_scheduled_scan_logic_does_not_execute_horus_without_signal_execution_gate(monkeypatch):
    now_dt = datetime.datetime(2026, 2, 18, 11, 5, 0)
    monkeypatch.delenv("SIGNAL_AUTO_EXECUTION_ENABLED", raising=False)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now_dt)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now_dt.date())
    monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr(settings, "SIGNAL_AUTO_EXECUTION_ENABLED", False, raising=False)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kwargs: ([_sample_signal("INTRA")], [{"Ticker": "AAA"}], 50.0, "BULLISH"),
    )
    monkeypatch.setattr(
        "core.scheduling.signals.run_daily_signals_logic",
        lambda req, **kwargs: {"status": "completed", "run": {"id": 17}},
    )
    calls = {"execute": 0}
    monkeypatch.setattr("core.scheduling.execute_run_for_horus", lambda _run_id: calls.__setitem__("execute", calls["execute"] + 1))

    assert core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY") is True
    assert calls["execute"] == 0


def test_scheduled_intraday_scan_executes_pending_horus_daily_entries_when_market_opens(monkeypatch):
    now_dt = datetime.datetime(2026, 2, 18, 11, 5, 0)
    monkeypatch.setenv("SIGNAL_AUTO_EXECUTION_ENABLED", "1")
    monkeypatch.setattr("core.TimeUtils.now", lambda: now_dt)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now_dt.date())
    monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: False)
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda label="": True)
    monkeypatch.setattr(settings, "get_market_close_hour_minute", lambda: (14, 30))
    monkeypatch.setattr(settings, "PRE_CLOSE_OFFSET_MINS", 20)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", False)

    calls = {"pending": 0, "scan": 0}
    monkeypatch.setattr("core.scheduling.execute_pending_daily_entries_for_horus", lambda: calls.__setitem__("pending", calls["pending"] + 1) or {"status": "completed"})
    monkeypatch.setattr("core.scheduling.scheduled_scan_logic", lambda **kwargs: calls.__setitem__("scan", calls["scan"] + 1))

    core.scheduling.scheduled_intraday_scan()

    assert calls == {"pending": 1, "scan": 1}


def test_scheduled_intraday_scan_skips_pending_without_signal_execution_gate(monkeypatch):
    now_dt = datetime.datetime(2026, 2, 18, 11, 5, 0)
    monkeypatch.delenv("SIGNAL_AUTO_EXECUTION_ENABLED", raising=False)
    monkeypatch.setattr("core.TimeUtils.now", lambda: now_dt)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now_dt.date())
    monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: False)
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda label="": True)
    monkeypatch.setattr(settings, "get_market_close_hour_minute", lambda: (14, 30))
    monkeypatch.setattr(settings, "PRE_CLOSE_OFFSET_MINS", 20)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", False)

    calls = {"pending": 0, "scan": 0}
    monkeypatch.setattr(
        "core.scheduling.execute_pending_daily_entries_for_horus",
        lambda: calls.__setitem__("pending", calls["pending"] + 1),
    )
    monkeypatch.setattr("core.scheduling.scheduled_scan_logic", lambda **kwargs: calls.__setitem__("scan", calls["scan"] + 1))

    core.scheduling.scheduled_intraday_scan()

    assert calls == {"pending": 0, "scan": 1}


def test_scheduled_intraday_scan_skips_during_replay(monkeypatch):
    monkeypatch.setattr("core.TimeUtils.is_replay", lambda: True)
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda label="": True)

    calls = {"scan": 0}
    monkeypatch.setattr("core.scheduling.scheduled_scan_logic", lambda **kwargs: calls.__setitem__("scan", calls["scan"] + 1))

    core.scheduling.scheduled_intraday_scan()

    assert calls == {"scan": 0}


def test_scheduled_trade_monitor_runs_horus_monitor_when_auto_trade_enabled(monkeypatch):
    monkeypatch.setenv("SIGNAL_AUTO_EXECUTION_ENABLED", "1")
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda label="": True)

    calls = {"system": 0, "horus": 0}
    monkeypatch.setattr("core.scheduling.AutoTrader.monitor_positions", lambda: calls.__setitem__("system", calls["system"] + 1))
    monkeypatch.setattr("core.scheduling.monitor_horus_positions", lambda: calls.__setitem__("horus", calls["horus"] + 1))

    core.scheduling.scheduled_trade_monitor()

    assert calls == {"system": 1, "horus": 1}


def test_scheduled_trade_monitor_runs_system_monitor_when_auto_trade_enabled(monkeypatch):
    monkeypatch.setenv("SIGNAL_AUTO_EXECUTION_ENABLED", "1")
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda label="": True)

    calls = {"system_monitor": 0}
    monkeypatch.setattr("core.scheduling.monitor_system_positions", lambda: calls.__setitem__("system_monitor", calls["system_monitor"] + 1))
    monkeypatch.setattr("core.scheduling.monitor_published_signal_lifecycles", lambda: None)
    monkeypatch.setattr("core.scheduling.process_signal_followups", lambda **kwargs: None)

    core.scheduling.scheduled_trade_monitor()

    assert calls == {"system_monitor": 1}


def test_scheduled_scan_logic_executes_run_via_signal_executor(monkeypatch):
    from core.scheduling.scans.runner import scheduled_scan_logic

    executed_runs = []
    monkeypatch.setenv("SIGNAL_AUTO_EXECUTION_ENABLED", "1")
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr("core.scheduling.scans.runner._USE_LEGACY_EXECUTOR", False)
    monkeypatch.setattr("core.scheduling.scans.runner._background_ops_paused_for_time_travel", lambda: False)
    monkeypatch.setattr("core.TimeUtils.today", lambda: datetime.date(2026, 2, 18))
    monkeypatch.setattr("core.scheduling.scans.runner.TimeUtils.today", lambda: datetime.date(2026, 2, 18))
    sample_signals = [
        {"Ticker": "HRHO", "Signal_Type": "BUY", "Entry_Price": 50.0, "Score": 8.0, "Stop_Loss": 47.0, "Target_Price": 55.0}
    ]
    monkeypatch.setattr("core.DailyScanner.get_market_signals", lambda *args, **kwargs: (sample_signals, 10, 70, "BULLISH"))
    monkeypatch.setattr(
        "core.scheduling._persist_scheduler_signal_run",
        lambda *args, **kwargs: {"status": "completed", "run": {"id": 1234}},
    )
    monkeypatch.setattr(
        "core.scheduling.execute_run_for_horus",
        lambda run_id: executed_runs.append(run_id) or {"status": "success"},
    )
    monkeypatch.setattr("core.AlertManager.broadcast_alert", lambda *args, **kwargs: {"ok": True})
    monkeypatch.setattr("core.AlertManager.broadcast_image", lambda *args, **kwargs: {"ok": True})

    scheduled_scan_logic(is_intraday=True)

    assert executed_runs == [1234]


def test_scheduled_trade_monitor_runs_signal_followups_without_auto_trade(monkeypatch):
    monkeypatch.delenv("SIGNAL_AUTO_EXECUTION_ENABLED", raising=False)
    monkeypatch.setattr("core.TimeUtils.is_replay", lambda: False)
    monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: False)
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda label="": True)

    calls = {"system": 0, "horus": 0, "lifecycle": 0, "followups": 0}
    monkeypatch.setattr("core.scheduling.AutoTrader.monitor_positions", lambda: calls.__setitem__("system", calls["system"] + 1))
    monkeypatch.setattr("core.scheduling.monitor_horus_positions", lambda: calls.__setitem__("horus", calls["horus"] + 1))
    monkeypatch.setattr("core.scheduling.monitor_published_signal_lifecycles", lambda: calls.__setitem__("lifecycle", calls["lifecycle"] + 1))
    monkeypatch.setattr(
        "core.scheduling.process_signal_followups",
        lambda **kwargs: calls.__setitem__("followups", calls["followups"] + 1),
    )

    core.scheduling.scheduled_trade_monitor()

    assert calls == {"system": 0, "horus": 0, "lifecycle": 1, "followups": 1}


def test_scheduled_trade_monitor_skips_during_replay(monkeypatch):
    monkeypatch.setattr("core.TimeUtils.is_replay", lambda: True)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda label="": True)

    calls = {"system": 0, "horus": 0}
    monkeypatch.setattr("core.scheduling.AutoTrader.monitor_positions", lambda: calls.__setitem__("system", calls["system"] + 1))
    monkeypatch.setattr("core.scheduling.monitor_horus_positions", lambda: calls.__setitem__("horus", calls["horus"] + 1))

    core.scheduling.scheduled_trade_monitor()

    assert calls == {"system": 0, "horus": 0}


def test_scheduled_scan_logic_publishes_type_one_lifecycle_when_main_channel_none(monkeypatch):
    from database import Client, PublishedSignalLifecycle, SignalDelivery, SignalRecommendation, SignalRun

    now_dt = datetime.datetime(2026, 2, 18, 11, 5, 0)
    sample = _sample_signal("COMI")
    sample["Target_Price_2"] = 12.0
    monkeypatch.setattr("core.TimeUtils.now", lambda: now_dt)
    monkeypatch.setattr("core.TimeUtils.today", lambda: now_dt.date())
    monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", False)
    monkeypatch.setattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", True)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "none", raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "-100main", raising=False)
    monkeypatch.setattr(
        "core.DailyScanner.get_market_signals",
        lambda **kwargs: ([sample], [{"Ticker": "AAA"}], 50.0, "BULLISH"),
    )

    subscriber = Client.create(
        name="Type One Client",
        subscription_tier="SIGNALS_ONLY",
        telegram_chat_id="100200300",
    )

    def _fake_run_logic(req, **kwargs):
        scanner_signals, _monitored, _breadth, _regime = kwargs["get_market_signals_fn"]()
        run = SignalRun.create(
            run_date=now_dt.date(),
            scan_type=req.scan_type,
            run_key=req.run_key,
            status="COMPLETED",
            completed_at=now_dt,
        )
        for raw in scanner_signals:
            SignalRecommendation.create(
                run=run,
                ticker=raw["Ticker"],
                side="BUY",
                entry_price=raw["Entry_Price"],
                stop_loss=raw["Stop_Loss"],
                target_price=raw["Target_Price"],
                score=raw["Score"],
                confidence=86,
                state="ACTIVE",
                rationale_json=json.dumps({"target_price_2": raw.get("Target_Price_2")}),
            )
        return {"status": "completed", "run": {"id": run.id}}

    sent = []
    main_channel_messages = []
    monkeypatch.setattr("core.scheduling.signals.run_daily_signals_logic", _fake_run_logic)
    monkeypatch.setattr("core.scheduling.AlertManager.filter_new_signals", lambda items, _label: list(items))
    monkeypatch.setattr("core.scheduling.AlertManager.broadcast_alert", lambda message, **kwargs: main_channel_messages.append(message) or {"ok": True})
    monkeypatch.setattr(
        "core.signals.publishing.TelegramBot_Alerts.send_message",
        lambda message, **kwargs: sent.append((message, kwargs)) or {"ok": True, "result": {"message_id": 44}},
    )

    assert core.scheduling.scheduled_scan_logic(is_intraday=True, scan_label="INTRADAY") is True

    assert main_channel_messages == []
    assert len(sent) == 1
    assert sent[0][1]["chat_id"] == "100200300"

    delivery = SignalDelivery.get(
        (SignalDelivery.destination_type == "SUBSCRIBER")
        & (SignalDelivery.destination_id == str(subscriber.id))
    )
    lifecycle = PublishedSignalLifecycle.get(PublishedSignalLifecycle.delivery == delivery)
    assert delivery.status == "SENT"
    assert lifecycle.ticker == "COMI"
    assert lifecycle.state == "PUBLISHED"
    assert lifecycle.target_price_2 == 12.0


def test_scheduled_trade_monitor_skips_when_market_closed(monkeypatch):
    monkeypatch.setattr("core.TimeUtils.is_replay", lambda: False)
    monkeypatch.setattr("core.TimeUtils.is_simulating", lambda: False)
    monkeypatch.setattr(settings, "is_market_open", lambda: False)
    monkeypatch.setattr(settings, "AUTO_TRADE_ENABLED", True)
    monkeypatch.setattr("core.pipeline.pipeline_allows_active_ops", lambda label="": True)

    calls = {"system": 0, "horus": 0}
    monkeypatch.setattr("core.scheduling.AutoTrader.monitor_positions", lambda: calls.__setitem__("system", calls["system"] + 1))
    monkeypatch.setattr("core.scheduling.monitor_horus_positions", lambda: calls.__setitem__("horus", calls["horus"] + 1))

    core.scheduling.scheduled_trade_monitor()

    assert calls == {"system": 0, "horus": 0}


def test_subscriber_delivery_failures_auto_deactivate(setup_test_db, monkeypatch):
    from database import Client, SignalRun, SignalRecommendation
    from core.signals.publishing import publish_signal_run_logic
    from core.signals.models import PublishSignalsRequest

    client = Client.create(
        name="Test Bad Telegram Client",
        subscription_tier="SIGNALS_ONLY",
        telegram_chat_id="999888777",
    )

    run = SignalRun.create(
        run_date=datetime.date(2026, 3, 10),
        scan_type="DAILY",
        status="COMPLETED",
        completed_at=datetime.datetime(2026, 3, 10, 15, 0, 0),
    )
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=50.0,
        stop_loss=45.0,
        target_price=60.0,
        score=9,
        confidence=90.0,
        state="ACTIVE",
    )

    fail_response = {"ok": False, "description": "Bad Request: chat not found"}
    success_response = {"ok": True, "result": {"message_id": 123}}

    should_fail = True
    tg_calls = []
    def _fake_send_message(msg, chat_id=None):
        tg_calls.append(chat_id)
        if should_fail:
            return fail_response
        return success_response

    monkeypatch.setattr("core.signals.publishing.TelegramBot_Alerts.send_message", _fake_send_message)
    monkeypatch.setattr("core.signals.publishing.settings.TELEGRAM_TOKEN", "token", raising=False)
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

    # 1. First failure
    publish_signal_run_logic(req)
    client = Client.get_by_id(client.id)
    assert client.delivery_fail_count == 1
    assert client.delivery_paused is False

    # 2. Second failure
    publish_signal_run_logic(req)
    client = Client.get_by_id(client.id)
    assert client.delivery_fail_count == 2
    assert client.delivery_paused is False

    # 3. Third failure -> should auto-deactivate
    publish_signal_run_logic(req)
    client = Client.get_by_id(client.id)
    assert client.delivery_fail_count == 3
    assert client.delivery_paused is True

    # 4. Next run -> subscriber should be excluded (delivery_paused == True)
    tg_calls.clear()
    import pytest
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        publish_signal_run_logic(req)
    assert excinfo.value.status_code == 404
    assert "999888777" not in tg_calls

    # 5. Reset client and verify success resets fail count
    client.delivery_paused = False
    client.delivery_fail_count = 2
    client.save()

    should_fail = False
    publish_signal_run_logic(req)
    client = Client.get_by_id(client.id)
    assert client.delivery_fail_count == 0
    assert client.delivery_paused is False

