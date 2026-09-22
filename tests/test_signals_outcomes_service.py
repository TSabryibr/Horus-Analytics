import datetime
from types import SimpleNamespace

from fastapi import HTTPException

from database import (
    Portfolio,
    PublishedSignalLifecycle,
    SignalAuditEvent,
    SignalDelivery,
    SignalOutcome,
    SignalRecommendation,
    SignalRun,
    SignalValidationRun,
    Trade,
)
from core import TimeUtils
from core.signals.runs import set_guard_state
from core.signals.outcomes import (
    get_signal_audit_summary,
    get_signal_calibration,
    get_signal_outcomes,
    get_walkforward_validation_latest,
    list_signal_audit_events,
    project_published_signal_lifecycle_outcome,
    rebuild_signal_outcomes,
)
from core.signals.workspace import get_signals_sla, get_workspace_signal_performance


def test_list_signal_audit_events_rejects_invalid_since():
    try:
        list_signal_audit_events(since="bad-timestamp")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail["error_reason"] == "invalid_since"
    else:
        raise AssertionError("expected invalid_since HTTPException")


def test_rebuild_signal_outcomes_returns_noop_without_completed_runs():
    result = rebuild_signal_outcomes(
        SimpleNamespace(run_id=None, from_date=None, to_date=None),
        rebuild_outcomes_for_run_fn=lambda _run: (_ for _ in ()).throw(AssertionError("should not rebuild")),
    )

    assert result["status"] == "noop"
    assert result["results"] == []


def test_get_signal_calibration_returns_empty_shape():
    result = get_signal_calibration(window=30, include_breakdowns=True)

    assert result["closed_signals"] == 0
    assert result["confidence_bins"] == []
    assert result["regime_breakdown"] == {}
    assert result["sector_breakdown"] == {}


def test_get_signal_outcomes_filters_closed_rows():
    run = SignalRun.create(run_date=TimeUtils.today(), status="COMPLETED")
    rec = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=80,
        state="ACTIVE",
    )
    SignalOutcome.create(
        recommendation=rec,
        run=run,
        ticker="COMI",
        outcome_status="CLOSED",
        pnl=10.0,
        pnl_pct=5.0,
        computed_at=TimeUtils.now(),
    )

    result = get_signal_outcomes(outcome_status="closed", limit=10)

    assert result["count"] == 1
    assert result["outcomes"][0]["ticker"] == "COMI"
    assert result["outcomes"][0]["outcome_status"] == "CLOSED"


def test_get_workspace_signal_performance_defaults_windows_and_returns_guard():
    portfolio = Portfolio.create(name="Workspace Portfolio", type="USER")
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)

    result = get_workspace_signal_performance(portfolio_id=portfolio.id, windows=" , ")

    assert [window["window_days"] for window in result["windows"]] == [30, 60, 90]
    assert result["portfolio"]["id"] == portfolio.id
    assert result["guard_state"]["name"] == "PUBLISH"


def test_get_signals_sla_counts_runs_deliveries_and_validation():
    run = SignalRun.create(
        run_date=TimeUtils.today(),
        status="COMPLETED",
        started_at=TimeUtils.now(),
        completed_at=TimeUtils.now(),
    )
    portfolio = Portfolio.create(name="SLA Portfolio", type="USER")
    SignalDelivery.create(run=run, portfolio=portfolio, channel="TELEGRAM", status="SENT")
    SignalValidationRun.create(
        run_date=TimeUtils.today(),
        status="PASS",
        window_days=30,
        closed_signals=3,
        win_rate_pct=66.7,
        avg_pnl_pct=2.3,
    )
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)

    result = get_signals_sla(days=7)

    assert result["runs"]["total"] == 1
    assert result["deliveries"]["sent"] == 1
    assert result["latest_validation"]["status"] == "PASS"


def test_get_walkforward_validation_latest_returns_guard_state():
    SignalValidationRun.create(
        run_date=TimeUtils.today(),
        status="PASS",
        window_days=90,
        closed_signals=5,
        win_rate_pct=60.0,
        avg_pnl_pct=1.2,
        details_json='{"mode":"auto"}',
    )
    set_guard_state(is_blocked=True, reason="weak performance", source="WFA", details={"validation_run_id": 1})

    result = get_walkforward_validation_latest()

    assert result["status"] == "ok"
    assert result["validation"]["details"] == {"mode": "auto"}
    assert result["guard_state"]["is_blocked"] is True


def test_project_published_signal_lifecycle_outcome_creates_closed_and_no_trade_rows():
    run = SignalRun.create(run_date=TimeUtils.today(), status="COMPLETED")
    portfolio = Portfolio.create(name="Lifecycle Outcome Portfolio", type="USER")
    rec_closed = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8,
        confidence=80.0,
        state="ACTIVE",
    )
    rec_expired = SignalRecommendation.create(
        run=run,
        ticker="HRHO",
        side="BUY",
        entry_price=50.0,
        stop_loss=47.0,
        target_price=55.0,
        score=7,
        confidence=72.0,
        state="ACTIVE",
    )
    delivery = SignalDelivery.create(
        run=run,
        portfolio=portfolio,
        channel="TELEGRAM",
        status="SENT",
        provider_message_id="42",
        sent_at=TimeUtils.now(),
    )
    closed_lifecycle = PublishedSignalLifecycle.create(
        recommendation=rec_closed,
        run=run,
        delivery=delivery,
        portfolio=portfolio,
        ticker="COMI",
        side="BUY",
        lane="swing",
        source_module="SCANNER",
        operating_mode="MANUAL",
        channel="TELEGRAM",
        published_message_id="42",
        state="TP2_HIT",
        resolution_source="AUTO",
        published_at=datetime.datetime(2026, 4, 22, 10, 0, 0),
        opened_at=datetime.datetime(2026, 4, 22, 10, 5, 0),
        closed_at=datetime.datetime(2026, 4, 22, 12, 0, 0),
        entry_price_planned=100.0,
        entry_price_filled=100.0,
        stop_loss_initial=95.0,
        stop_loss_active=100.0,
        target_price_1=110.0,
        target_price_2=115.0,
        close_price=115.0,
        close_reason="TP2_HIT",
    )
    expired_lifecycle = PublishedSignalLifecycle.create(
        recommendation=rec_expired,
        run=run,
        delivery=delivery,
        portfolio=portfolio,
        ticker="HRHO",
        side="BUY",
        lane="intraday",
        source_module="SCANNER",
        operating_mode="MANUAL",
        channel="TELEGRAM",
        published_message_id="43",
        state="EXPIRED",
        resolution_source="AUTO",
        published_at=datetime.datetime(2026, 4, 22, 10, 0, 0),
        closed_at=datetime.datetime(2026, 4, 22, 16, 0, 0),
        entry_price_planned=50.0,
        stop_loss_initial=47.0,
        stop_loss_active=47.0,
        target_price_1=55.0,
        target_price_2=57.0,
        close_reason="ENTRY_NOT_REACHED",
    )

    closed_outcome = project_published_signal_lifecycle_outcome(closed_lifecycle)
    expired_outcome = project_published_signal_lifecycle_outcome(expired_lifecycle)

    assert closed_outcome.outcome_status == "CLOSED"
    assert round(float(closed_outcome.pnl_pct), 4) == 15.0
    assert expired_outcome.outcome_status == "NO_TRADE"
    assert expired_outcome.entry_price is None
