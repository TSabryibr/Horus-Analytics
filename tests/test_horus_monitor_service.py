from core.settings import settings
import json
import datetime
import pytest

from database import (
    HorusExecution,
    Portfolio,
    Position,
    PublishedSignalLifecycle,
    PublishedSignalLifecycleEvent,
    SignalDelivery,
    SignalRecommendation,
    SignalRun,
    Trade,
)


def _make_run():
    return SignalRun.create(run_date="2026-02-20", scan_type="INTRADAY", run_key="2026-02-20:INTRADAY:11:00", status="COMPLETED")


def _make_recommendation(run, ticker="COMI", entry=100.0, sl=95.0, tp=110.0, tp2=115.0):
    return SignalRecommendation.create(
        run=run,
        ticker=ticker,
        side="BUY",
        entry_price=entry,
        stop_loss=sl,
        target_price=tp,
        score=8,
        confidence=80.0,
        rationale_json=json.dumps({"target_price_2": tp2}),
        state="ACTIVE",
    )


def _make_published_lifecycle(
    run,
    recommendation,
    *,
    state="PUBLISHED",
    lane="swing",
    published_at=None,
    expires_at=None,
):
    portfolio = Portfolio.create(name=f"Lifecycle {recommendation.ticker}", type="USER")
    delivery = SignalDelivery.create(
        run=run,
        portfolio=portfolio,
        channel="TELEGRAM",
        status="SENT",
        provider_message_id=f"msg-{recommendation.ticker}",
        sent_at=published_at or datetime.datetime(2026, 2, 20, 11, 0, 0),
    )
    return PublishedSignalLifecycle.create(
        recommendation=recommendation,
        run=run,
        delivery=delivery,
        portfolio=portfolio,
        ticker=recommendation.ticker,
        side=recommendation.side,
        lane=lane,
        source_module="SCANNER",
        operating_mode="MANUAL",
        channel="TELEGRAM",
        published_message_id=delivery.provider_message_id,
        state=state,
        resolution_source="AUTO",
        published_at=published_at or delivery.sent_at,
        expires_at=expires_at or datetime.datetime(2026, 2, 25, 11, 0, 0),
        opened_at=datetime.datetime(2026, 2, 20, 11, 2, 0) if state in {"OPEN", "TP1_HIT"} else None,
        tp1_hit_at=datetime.datetime(2026, 2, 20, 11, 4, 0) if state == "TP1_HIT" else None,
        entry_price_planned=float(recommendation.entry_price),
        entry_price_filled=float(recommendation.entry_price) if state in {"OPEN", "TP1_HIT"} else None,
        stop_loss_initial=float(recommendation.stop_loss),
        stop_loss_active=float(recommendation.entry_price if state == "TP1_HIT" else recommendation.stop_loss),
        target_price_1=float(recommendation.target_price),
        target_price_2=115.0,
        details_json=json.dumps({"confidence": float(recommendation.confidence)}),
    )


def test_monitor_horus_positions_closes_on_stop_loss_and_sends_single_close_message(monkeypatch):
    from core.horus.monitor import monitor_horus_positions

    horus = Portfolio.create(name="Horus", type="USER")
    run = _make_run()
    rec = _make_recommendation(run, ticker="COMI", entry=100.0, sl=95.0, tp=110.0)
    Position.create(
        portfolio=horus,
        ticker="COMI",
        shares=100,
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        status="OPEN",
        entry_date=datetime.datetime(2026, 2, 20, 11, 0, 0),
    )
    execution = HorusExecution.create(
        portfolio=horus,
        run=run,
        recommendation=rec,
        ticker="COMI",
        state="OPEN",
        trigger_source="INTRADAY",
        planned_entry_price=100.0,
        actual_entry_price=100.0,
        active_stop_loss=95.0,
        active_target_price=110.0,
    )

    monkeypatch.setattr("core.settings.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_3", raising=False)
    monkeypatch.setattr(
        "core.horus.monitor.DataManager.get_intraday_data",
        lambda ticker, limit=1, refresh_if_stale=False: __import__("pandas").DataFrame(
            [{"Open": 100.0, "High": 101.0, "Low": 94.5, "Close": 95.0}],
            index=[datetime.datetime(2026, 2, 20, 11, 5, 0)],
        ),
    )

    sent_messages = []
    monkeypatch.setattr(
        "core.horus.monitor.TelegramBot_Alerts.send_message",
        lambda message: sent_messages.append(message) or {"ok": True, "result": {"message_id": 201}},
    )

    with pytest.deprecated_call(match="monitor_horus_positions is deprecated"):
        result = monitor_horus_positions()
    with pytest.deprecated_call(match="monitor_horus_positions is deprecated"):
        result_again = monitor_horus_positions()

    assert result["summary"] == {"closed": 1, "updated": 0, "failed": 0}
    assert result_again["summary"] == {"closed": 0, "updated": 0, "failed": 0}
    assert len(sent_messages) == 1

    execution = HorusExecution.get_by_id(execution.id)
    assert execution.state == "CLOSED"
    assert execution.close_reason == "STOP_LOSS"
    assert execution.close_message_id == "201"
    trade = Trade.get(Trade.portfolio == horus, Trade.ticker == "COMI")
    assert trade.reason == "STOP_LOSS"


def test_monitor_horus_positions_blocks_close_message_from_type_1_main_channel(monkeypatch):
    from core.horus.monitor import monitor_horus_positions

    horus = Portfolio.create(name="Horus", type="USER")
    run = _make_run()
    rec = _make_recommendation(run, ticker="COMI", entry=100.0, sl=95.0, tp=110.0)
    Position.create(
        portfolio=horus,
        ticker="COMI",
        shares=100,
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        status="OPEN",
        entry_date=datetime.datetime(2026, 2, 20, 11, 0, 0),
    )
    execution = HorusExecution.create(
        portfolio=horus,
        run=run,
        recommendation=rec,
        ticker="COMI",
        state="OPEN",
        trigger_source="INTRADAY",
        planned_entry_price=100.0,
        actual_entry_price=100.0,
        active_stop_loss=95.0,
        active_target_price=110.0,
    )

    monkeypatch.setattr("core.settings.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(
        "core.horus.monitor.DataManager.get_intraday_data",
        lambda ticker, limit=1, refresh_if_stale=False: __import__("pandas").DataFrame(
            [{"Open": 100.0, "High": 101.0, "Low": 94.5, "Close": 95.0}],
            index=[datetime.datetime(2026, 2, 20, 11, 5, 0)],
        ),
    )

    sent_messages = []
    monkeypatch.setattr(
        "core.horus.monitor.TelegramBot_Alerts.send_message",
        lambda message: sent_messages.append(message) or {"ok": True, "result": {"message_id": 201}},
    )

    with pytest.deprecated_call(match="monitor_horus_positions is deprecated"):
        result = monitor_horus_positions()

    assert result["summary"] == {"closed": 1, "updated": 0, "failed": 0}
    assert sent_messages == []
    execution = HorusExecution.get_by_id(execution.id)
    assert execution.state == "CLOSED"
    assert execution.close_message_id is None


def test_system_monitor_blocks_exit_card_from_type_1_main_channel(monkeypatch):
    from core.signals.system_monitor import SystemMonitor

    monkeypatch.setattr("core.settings.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr("core.signals.system_monitor.ReportGenerator.create_exit_card", lambda *args, **kwargs: object())

    images = []
    alerts = []
    messages = []
    monkeypatch.setattr("core.signals.system_monitor.AlertManager.broadcast_image", lambda card, caption="": images.append(caption) or {"ok": True})
    monkeypatch.setattr("core.signals.system_monitor.AlertManager.broadcast_alert", lambda message: alerts.append(message) or {"ok": True})
    monkeypatch.setattr("core.signals.system_monitor.TelegramBot_Alerts.send_message", lambda message: messages.append(message) or {"ok": True})

    SystemMonitor._notify_exit("EGTS", 19.9217, 21.69, -8.15, "STOP_LOSS")

    assert images == []
    assert alerts == []
    assert messages == []


def test_system_monitor_allows_exit_card_for_type_3_main_channel(monkeypatch):
    from core.signals.system_monitor import SystemMonitor

    monkeypatch.setattr("core.settings.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_3", raising=False)
    monkeypatch.setattr("core.signals.system_monitor.ReportGenerator.create_exit_card", lambda *args, **kwargs: object())

    images = []
    monkeypatch.setattr("core.signals.system_monitor.AlertManager.broadcast_image", lambda card, caption="": images.append(caption) or {"ok": True})

    SystemMonitor._notify_exit("EGTS", 19.9217, 21.69, -8.15, "STOP_LOSS")

    assert len(images) == 1
    assert "STOP LOSS HIT" in images[0]


def test_monitor_horus_positions_closes_on_target(monkeypatch):
    from core.horus.monitor import monitor_horus_positions

    horus = Portfolio.create(name="Horus", type="USER")
    run = _make_run()
    rec = _make_recommendation(run, ticker="SWDY", entry=100.0, sl=95.0, tp=110.0)
    Position.create(
        portfolio=horus,
        ticker="SWDY",
        shares=100,
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        status="OPEN",
        entry_date=datetime.datetime(2026, 2, 20, 11, 0, 0),
    )
    execution = HorusExecution.create(
        portfolio=horus,
        run=run,
        recommendation=rec,
        ticker="SWDY",
        state="OPEN",
        trigger_source="INTRADAY",
        planned_entry_price=100.0,
        actual_entry_price=100.0,
        active_stop_loss=95.0,
        active_target_price=110.0,
    )

    monkeypatch.setattr(
        "core.horus.monitor.DataManager.get_intraday_data",
        lambda ticker, limit=1, refresh_if_stale=False: __import__("pandas").DataFrame(
            [{"Open": 100.0, "High": 111.0, "Low": 99.0, "Close": 110.5}],
            index=[datetime.datetime(2026, 2, 20, 11, 5, 0)],
        ),
    )
    monkeypatch.setattr(
        "core.horus.monitor.TelegramBot_Alerts.send_message",
        lambda message: {"ok": True, "result": {"message_id": 202}},
    )

    with pytest.deprecated_call(match="monitor_horus_positions is deprecated"):
        result = monitor_horus_positions()

    assert result["summary"] == {"closed": 1, "updated": 0, "failed": 0}
    execution = HorusExecution.get_by_id(execution.id)
    assert execution.state == "CLOSED"
    assert execution.close_reason == "TARGET"
    trade = Trade.get(Trade.portfolio == horus, Trade.ticker == "SWDY")
    assert trade.reason == "TARGET"
    assert round(float(trade.exit_price), 4) == 110.0


def test_monitor_horus_positions_ratchets_trailing_and_then_closes_on_trailing_stop(monkeypatch):
    from core.horus.monitor import monitor_horus_positions

    horus = Portfolio.create(name="Horus", type="USER")
    run = _make_run()
    rec = _make_recommendation(run, ticker="ORWE", entry=100.0, sl=95.0, tp=115.0)
    Position.create(
        portfolio=horus,
        ticker="ORWE",
        shares=100,
        entry_price=100.0,
        stop_loss=95.0,
        target_price=115.0,
        status="OPEN",
        entry_date=datetime.datetime(2026, 2, 20, 11, 0, 0),
    )
    execution = HorusExecution.create(
        portfolio=horus,
        run=run,
        recommendation=rec,
        ticker="ORWE",
        state="OPEN",
        trigger_source="INTRADAY",
        planned_entry_price=100.0,
        actual_entry_price=100.0,
        active_stop_loss=95.0,
        active_target_price=115.0,
        details_json=json.dumps({"trailing_pct": 2.0, "trailing_armed": True}),
    )

    frames = [
        __import__("pandas").DataFrame(
            [{"Open": 100.0, "High": 108.0, "Low": 104.0, "Close": 107.0}],
            index=[datetime.datetime(2026, 2, 20, 11, 5, 0)],
        ),
        __import__("pandas").DataFrame(
            [{"Open": 107.0, "High": 107.5, "Low": 104.5, "Close": 105.0}],
            index=[datetime.datetime(2026, 2, 20, 11, 10, 0)],
        ),
    ]
    monkeypatch.setattr(
        "core.horus.monitor.DataManager.get_intraday_data",
        lambda ticker, limit=1, refresh_if_stale=False: frames.pop(0),
    )
    monkeypatch.setattr(
        "core.horus.monitor.TelegramBot_Alerts.send_message",
        lambda message: {"ok": True, "result": {"message_id": 203}},
    )

    with pytest.deprecated_call(match="monitor_horus_positions is deprecated"):
        first = monitor_horus_positions()
    execution_after_update = HorusExecution.get_by_id(execution.id)
    assert first["summary"] == {"closed": 0, "updated": 1, "failed": 0}
    assert round(float(execution_after_update.active_stop_loss), 2) == 104.86

    with pytest.deprecated_call(match="monitor_horus_positions is deprecated"):
        second = monitor_horus_positions()
    execution_closed = HorusExecution.get_by_id(execution.id)
    assert second["summary"] == {"closed": 1, "updated": 0, "failed": 0}
    assert execution_closed.state == "CLOSED"
    assert execution_closed.close_reason == "TRAILING_STOP"


def test_monitor_published_signal_lifecycles_opens_when_entry_is_reached():
    from core.signals.lifecycle import monitor_published_signal_lifecycles

    run = _make_run()
    rec = _make_recommendation(run, ticker="COMI", entry=100.0, sl=95.0, tp=110.0, tp2=115.0)
    lifecycle = _make_published_lifecycle(run, rec, state="PUBLISHED")

    result = monitor_published_signal_lifecycles(
        now_fn=lambda: datetime.datetime(2026, 2, 20, 11, 5, 0),
        latest_bar_fn=lambda ticker: (
            {"Open": 99.5, "High": 100.5, "Low": 99.0, "Close": 100.2},
            datetime.datetime(2026, 2, 20, 11, 5, 0),
        ),
    )

    assert result["summary"]["opened"] == 1
    lifecycle = PublishedSignalLifecycle.get_by_id(lifecycle.id)
    assert lifecycle.state == "OPEN"
    assert lifecycle.entry_price_filled == 100.0
    event = PublishedSignalLifecycleEvent.get(PublishedSignalLifecycleEvent.lifecycle == lifecycle)
    assert event.event_type == "OPENED"


def test_monitor_published_signal_lifecycles_moves_stop_to_breakeven_after_tp1():
    from core.signals.lifecycle import monitor_published_signal_lifecycles

    run = _make_run()
    rec = _make_recommendation(run, ticker="SWDY", entry=100.0, sl=95.0, tp=110.0, tp2=115.0)
    lifecycle = _make_published_lifecycle(run, rec, state="OPEN")

    result = monitor_published_signal_lifecycles(
        now_fn=lambda: datetime.datetime(2026, 2, 20, 11, 6, 0),
        latest_bar_fn=lambda ticker: (
            {"Open": 108.0, "High": 110.5, "Low": 107.5, "Close": 110.0},
            datetime.datetime(2026, 2, 20, 11, 6, 0),
        ),
    )

    assert result["summary"]["tp1_hit"] == 1
    lifecycle = PublishedSignalLifecycle.get_by_id(lifecycle.id)
    assert lifecycle.state == "TP1_HIT"
    assert lifecycle.stop_loss_active == 100.0
    latest_event = (
        PublishedSignalLifecycleEvent.select()
        .where(PublishedSignalLifecycleEvent.lifecycle == lifecycle)
        .order_by(PublishedSignalLifecycleEvent.id.desc())
        .get()
    )
    assert latest_event.event_type == "TP1_HIT"


def test_monitor_published_signal_lifecycles_closes_tp2_marks_ambiguity_and_expires():
    from core.signals.lifecycle import monitor_published_signal_lifecycles

    run = _make_run()
    rec_tp2 = _make_recommendation(run, ticker="ORWE", entry=100.0, sl=95.0, tp=110.0, tp2=115.0)
    rec_ambiguous = _make_recommendation(run, ticker="HRHO", entry=50.0, sl=47.0, tp=55.0, tp2=57.0)
    rec_expired = _make_recommendation(run, ticker="ETEL", entry=20.0, sl=18.0, tp=24.0, tp2=25.0)

    lifecycle_tp2 = _make_published_lifecycle(run, rec_tp2, state="TP1_HIT")
    lifecycle_ambiguous = _make_published_lifecycle(run, rec_ambiguous, state="OPEN")
    lifecycle_expired = _make_published_lifecycle(
        run,
        rec_expired,
        state="PUBLISHED",
        expires_at=datetime.datetime(2026, 2, 20, 10, 59, 0),
    )

    def latest_bar(ticker):
        if ticker == "ORWE":
            return (
                {"Open": 112.0, "High": 115.5, "Low": 111.0, "Close": 115.0},
                datetime.datetime(2026, 2, 20, 11, 7, 0),
            )
        if ticker == "HRHO":
            return (
                {"Open": 52.0, "High": 55.5, "Low": 46.5, "Close": 50.5},
                datetime.datetime(2026, 2, 20, 11, 8, 0),
            )
        return None

    result = monitor_published_signal_lifecycles(
        now_fn=lambda: datetime.datetime(2026, 2, 20, 11, 9, 0),
        latest_bar_fn=latest_bar,
    )

    assert result["summary"]["closed_tp2"] == 1
    assert result["summary"]["ambiguous"] == 1
    assert result["summary"]["expired"] == 1

    lifecycle_tp2 = PublishedSignalLifecycle.get_by_id(lifecycle_tp2.id)
    lifecycle_ambiguous = PublishedSignalLifecycle.get_by_id(lifecycle_ambiguous.id)
    lifecycle_expired = PublishedSignalLifecycle.get_by_id(lifecycle_expired.id)

    assert lifecycle_tp2.state == "TP2_HIT"
    assert lifecycle_tp2.close_reason == "TP2_HIT"
    assert lifecycle_ambiguous.state == "AMBIGUOUS"
    assert lifecycle_expired.state == "EXPIRED"
