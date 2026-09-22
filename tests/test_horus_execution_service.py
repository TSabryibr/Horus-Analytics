from core.settings import settings
import json
import pytest

from database import HorusExecution, Portfolio, Position, SignalRecommendation, SignalRun


def _make_run(scan_type="INTRADAY", run_key="2026-02-20:INTRADAY:11:00"):
    return SignalRun.create(run_date="2026-02-20", scan_type=scan_type, run_key=run_key, status="COMPLETED")


def _make_recommendation(run, ticker="COMI", entry=100.0, sl=90.0, tp=120.0, tp2=130.0):
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


def test_execute_run_for_horus_opens_new_position_and_records_lifecycle(monkeypatch):
    from core.horus.executor import execute_run_for_horus

    horus = Portfolio.create(name="Horus", type="USER")
    run = _make_run()
    rec = _make_recommendation(run)

    monkeypatch.setattr("core.horus.executor.settings.ACCOUNT_BALANCE", 100000, raising=False)
    monkeypatch.setattr("core.horus.executor.settings.RISK_PER_TRADE", 2.0, raising=False)

    add_calls = {}
    sent_messages = []

    def _add_position(**kwargs):
        add_calls["payload"] = kwargs
        return True

    monkeypatch.setattr("core.horus.executor.PositionTracker.add_position", _add_position)
    monkeypatch.setattr("core.horus.executor.PositionTracker.update_position", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not update")))
    monkeypatch.setattr(
        "core.horus.executor.TelegramBot_Alerts.send_message",
        lambda message: sent_messages.append(message) or {"ok": True, "result": {"message_id": 77}},
    )

    with pytest.deprecated_call(match="execute_run_for_horus is deprecated"):
        result = execute_run_for_horus(run.id)

    assert result["status"] == "completed"
    assert result["summary"] == {"opened": 1, "updated": 0, "failed": 0, "skipped": 0}
    assert add_calls["payload"]["ticker"] == rec.ticker
    assert add_calls["payload"]["shares"] == 200
    assert add_calls["payload"]["portfolio_id"] == horus.id
    assert add_calls["payload"]["tp2"] == 130.0
    assert len(sent_messages) == 1

    execution = HorusExecution.get(HorusExecution.portfolio == horus, HorusExecution.recommendation == rec)
    assert execution.state == "OPEN"
    assert execution.trigger_source == "INTRADAY"
    assert execution.planned_entry_price == 100.0
    assert execution.actual_entry_price == 100.0
    assert execution.active_stop_loss == 90.0
    assert execution.active_target_price == 120.0
    assert execution.open_message_id == "77"


def test_execute_run_for_horus_updates_existing_open_position_instead_of_duplicating(monkeypatch):
    from core.horus.executor import execute_run_for_horus

    horus = Portfolio.create(name="Horus", type="USER")
    original_run = _make_run(run_key="2026-02-20:INTRADAY:10:55")
    original_rec = _make_recommendation(original_run, entry=100.0, sl=90.0, tp=120.0, tp2=124.0)
    Position.create(
        portfolio=horus,
        ticker="COMI",
        shares=200,
        entry_price=100.0,
        stop_loss=90.0,
        target_price=120.0,
        target_price_2=124.0,
        status="OPEN",
    )
    execution = HorusExecution.create(
        portfolio=horus,
        run=original_run,
        recommendation=original_rec,
        ticker="COMI",
        state="OPEN",
        trigger_source="INTRADAY",
        planned_entry_price=100.0,
        actual_entry_price=100.0,
        active_stop_loss=90.0,
        active_target_price=120.0,
    )

    new_run = _make_run(run_key="2026-02-20:INTRADAY:11:00")
    new_rec = _make_recommendation(new_run, entry=102.0, sl=95.0, tp=130.0, tp2=138.0)

    update_calls = {}
    sent_messages = []
    monkeypatch.setattr("core.horus.executor.PositionTracker.add_position", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not add")))
    monkeypatch.setattr(
        "core.horus.executor.PositionTracker.update_position",
        lambda **kwargs: update_calls.setdefault("payload", kwargs) or True,
    )
    monkeypatch.setattr(
        "core.horus.executor.TelegramBot_Alerts.send_message",
        lambda message: sent_messages.append(message) or {"ok": True, "result": {"message_id": 88}},
    )

    with pytest.deprecated_call(match="execute_run_for_horus is deprecated"):
        result = execute_run_for_horus(new_run.id)

    assert result["summary"] == {"opened": 0, "updated": 1, "failed": 0, "skipped": 0}
    assert update_calls["payload"]["ticker"] == "COMI"
    assert update_calls["payload"]["portfolio_id"] == horus.id
    assert update_calls["payload"]["sl"] == 95.0
    assert update_calls["payload"]["tp"] == 130.0
    assert update_calls["payload"]["tp2"] == 138.0
    assert len(sent_messages) == 1

    execution = HorusExecution.get_by_id(execution.id)
    assert execution.state == "UPDATED"
    assert execution.recommendation == new_rec
    assert execution.active_stop_loss == 95.0
    assert execution.active_target_price == 130.0
    assert execution.update_message_id == "88"
    details = json.loads(execution.details_json or "{}")
    assert details["previous"]["stop_loss"] == 90.0
    assert details["updated"]["stop_loss"] == 95.0


def test_execute_run_for_horus_does_not_send_telegram_when_position_open_fails(monkeypatch):
    from core.horus.executor import execute_run_for_horus

    horus = Portfolio.create(name="Horus", type="USER")
    run = _make_run()
    rec = _make_recommendation(run, ticker="FWRY", entry=50.0, sl=47.0, tp=58.0, tp2=61.0)

    monkeypatch.setattr("core.horus.executor.settings.ACCOUNT_BALANCE", 100000, raising=False)
    monkeypatch.setattr("core.horus.executor.settings.RISK_PER_TRADE", 2.0, raising=False)
    monkeypatch.setattr("core.horus.executor.PositionTracker.add_position", lambda **kwargs: False)

    sent_messages = []
    monkeypatch.setattr(
        "core.horus.executor.TelegramBot_Alerts.send_message",
        lambda message: sent_messages.append(message) or {"ok": True, "result": {"message_id": 99}},
    )

    with pytest.deprecated_call(match="execute_run_for_horus is deprecated"):
        result = execute_run_for_horus(run.id)

    assert result["summary"] == {"opened": 0, "updated": 0, "failed": 1, "skipped": 0}
    assert sent_messages == []

    execution = HorusExecution.get(HorusExecution.portfolio == horus, HorusExecution.recommendation == rec)
    assert execution.state == "FAILED"
    assert execution.open_message_id is None


def test_execute_run_for_horus_daily_run_creates_pending_open_instead_of_opening_position(monkeypatch):
    from core.horus.executor import execute_run_for_horus

    horus = Portfolio.create(name="Horus", type="USER")
    run = _make_run(scan_type="DAILY", run_key="2026-02-20:DAILY")
    rec = _make_recommendation(run, ticker="HRHO", entry=40.0, sl=37.0, tp=46.0, tp2=49.0)

    monkeypatch.setattr("core.horus.executor.PositionTracker.add_position", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not add")))
    monkeypatch.setattr("core.horus.executor.TelegramBot_Alerts.send_message", lambda message: (_ for _ in ()).throw(AssertionError("should not notify")))

    with pytest.deprecated_call(match="execute_run_for_horus is deprecated"):
        result = execute_run_for_horus(run.id)

    assert result["status"] == "completed"
    assert result["summary"] == {"opened": 0, "updated": 0, "failed": 0, "skipped": 1}

    execution = HorusExecution.get(HorusExecution.portfolio == horus, HorusExecution.recommendation == rec)
    assert execution.state == "PENDING_OPEN"
    assert execution.trigger_source == "DAILY_NEXT_OPEN"
    assert execution.planned_entry_price == 40.0
    assert execution.actual_entry_price is None


def test_execute_pending_daily_entries_for_horus_opens_gap_adjusted_trade_within_threshold(monkeypatch):
    from core.horus.executor import execute_pending_daily_entries_for_horus

    horus = Portfolio.create(name="Horus", type="USER")
    run = _make_run(scan_type="DAILY", run_key="2026-02-20:DAILY")
    rec = _make_recommendation(run, ticker="SWDY", entry=100.0, sl=95.0, tp=112.0, tp2=118.0)
    execution = HorusExecution.create(
        portfolio=horus,
        run=run,
        recommendation=rec,
        ticker="SWDY",
        state="PENDING_OPEN",
        trigger_source="DAILY_NEXT_OPEN",
        planned_entry_price=100.0,
        actual_entry_price=None,
        active_stop_loss=95.0,
        active_target_price=112.0,
    )

    monkeypatch.setattr("core.horus.executor.settings.ACCOUNT_BALANCE", 100000, raising=False)
    monkeypatch.setattr("core.horus.executor.settings.RISK_PER_TRADE", 2.0, raising=False)

    add_calls = {}
    sent_messages = []
    monkeypatch.setattr(
        "core.horus.executor._get_next_open_price",
        lambda ticker: (101.0, "2026-02-21T10:00:00"),
    )
    monkeypatch.setattr(
        "core.horus.executor.PositionTracker.add_position",
        lambda **kwargs: add_calls.setdefault("payload", kwargs) or True,
    )
    monkeypatch.setattr(
        "core.horus.executor.TelegramBot_Alerts.send_message",
        lambda message: sent_messages.append(message) or {"ok": True, "result": {"message_id": 123}},
    )

    with pytest.deprecated_call(match="execute_pending_daily_entries_for_horus is deprecated"):
        result = execute_pending_daily_entries_for_horus()

    assert result["status"] == "completed"
    assert result["summary"] == {"opened": 1, "skipped": 0, "failed": 0}
    assert add_calls["payload"]["ticker"] == "SWDY"
    assert add_calls["payload"]["entry_price"] == 101.0
    assert add_calls["payload"]["shares"] == 198
    assert len(sent_messages) == 1

    execution = HorusExecution.get_by_id(execution.id)
    assert execution.state == "OPEN"
    assert execution.actual_entry_price == 101.0
    assert round(float(execution.gap_pct or 0.0), 4) == 1.0
    assert execution.gap_adjusted is True
    assert execution.open_message_id == "123"


def test_execute_pending_daily_entries_for_horus_skips_when_gap_exceeds_threshold(monkeypatch):
    from core.horus.executor import execute_pending_daily_entries_for_horus

    horus = Portfolio.create(name="Horus", type="USER")
    run = _make_run(scan_type="DAILY", run_key="2026-02-20:DAILY")
    rec = _make_recommendation(run, ticker="ORWE", entry=100.0, sl=95.0, tp=112.0, tp2=118.0)
    execution = HorusExecution.create(
        portfolio=horus,
        run=run,
        recommendation=rec,
        ticker="ORWE",
        state="PENDING_OPEN",
        trigger_source="DAILY_NEXT_OPEN",
        planned_entry_price=100.0,
        actual_entry_price=None,
        active_stop_loss=95.0,
        active_target_price=112.0,
    )

    sent_messages = []
    monkeypatch.setattr(
        "core.horus.executor._get_next_open_price",
        lambda ticker: (102.0, "2026-02-21T10:00:00"),
    )
    monkeypatch.setattr("core.horus.executor.PositionTracker.add_position", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not add")))
    monkeypatch.setattr(
        "core.horus.executor.TelegramBot_Alerts.send_message",
        lambda message: sent_messages.append(message) or {"ok": True, "result": {"message_id": 124}},
    )

    with pytest.deprecated_call(match="execute_pending_daily_entries_for_horus is deprecated"):
        result = execute_pending_daily_entries_for_horus(max_gap_pct=1.5)

    assert result["status"] == "completed"
    assert result["summary"] == {"opened": 0, "skipped": 1, "failed": 0}
    assert len(sent_messages) == 1

    execution = HorusExecution.get_by_id(execution.id)
    assert execution.state == "SKIPPED"
    assert execution.skip_message_id == "124"
    assert round(float(execution.gap_pct or 0.0), 4) == 2.0
