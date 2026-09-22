from core.settings import settings
import datetime
import json
from types import SimpleNamespace

from database import SignalGuardState, SignalOutcome, SignalRecommendation, SignalRun
from core import TimeUtils
from core.signals.runs import (
    get_guard_state,
    run_daily_signals_logic,
    run_walkforward_validation_logic,
    serialize_guard_state,
    set_guard_state,
)
from routes.signals import _build_recommendation, _recommendation_source_module


def test_set_guard_state_and_serialize_round_trip():
    state = set_guard_state(
        is_blocked=True,
        reason="degraded",
        source="WFA",
        details={"validation_run_id": 7},
        now_fn=lambda: datetime.datetime(2026, 3, 17, 12, 0, 0),
    )

    serialized = serialize_guard_state(state)

    assert serialized["is_blocked"] is True
    assert serialized["reason"] == "degraded"
    assert serialized["source"] == "WFA"
    assert serialized["details"] == {"validation_run_id": 7}


def test_run_daily_signals_logic_returns_existing_without_force():
    existing = SignalRun.create(
        run_date=datetime.date(2026, 2, 11),
        scan_type="DAILY",
        status="COMPLETED",
        started_at=datetime.datetime(2026, 2, 11, 14, 0, 0),
        completed_at=datetime.datetime(2026, 2, 11, 14, 5, 0),
    )
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)

    req = SimpleNamespace(
        run_date="2026-02-11",
        scan_type="DAILY",
        force=False,
        model_version=None,
        index="EGX30",
        ignore_guard=False,
    )

    result = run_daily_signals_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        evaluate_data_freshness_fn=lambda **kwargs: {"overall_ok": True},
        get_market_signals_fn=lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not scan")),
        build_recommendation_fn=lambda *args, **kwargs: None,
    )

    assert result["status"] == "existing"
    assert result["run"]["id"] == existing.id


def test_run_daily_signals_logic_returns_existing_for_matching_intraday_run_key_without_force():
    existing = SignalRun.create(
        run_date=datetime.date(2026, 2, 11),
        scan_type="INTRADAY",
        run_key="2026-02-11:INTRADAY:11:00",
        status="COMPLETED",
        started_at=datetime.datetime(2026, 2, 11, 11, 0, 0),
        completed_at=datetime.datetime(2026, 2, 11, 11, 1, 0),
    )
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)

    req = SimpleNamespace(
        run_date="2026-02-11",
        scan_type="INTRADAY",
        run_key="2026-02-11:INTRADAY:11:00",
        force=False,
        model_version=None,
        index="EGX30",
        ignore_guard=False,
    )

    result = run_daily_signals_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        evaluate_data_freshness_fn=lambda **kwargs: {"overall_ok": True},
        get_market_signals_fn=lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not scan")),
        build_recommendation_fn=lambda *args, **kwargs: None,
    )

    assert result["status"] == "existing"
    assert result["run"]["id"] == existing.id


def test_run_daily_signals_logic_allows_multiple_intraday_runs_with_distinct_run_keys():
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)

    built = []

    def _build_recommendation(signal, run, regime):
        built.append((signal["Ticker"], run.run_key, regime))
        return SignalRecommendation(
            run=run,
            ticker=signal["Ticker"],
            side="BUY",
            entry_price=10.0,
            stop_loss=9.0,
            target_price=11.0,
            score=7,
            confidence=70.0,
            state="ACTIVE",
        )

    def _run_req(run_key: str):
        return SimpleNamespace(
            run_date="2026-02-13",
            scan_type="INTRADAY",
            run_key=run_key,
            force=False,
            model_version=None,
            index="EGX30",
            ignore_guard=False,
        )

    scan_calls = []

    def _scan(**kwargs):
        scan_calls.append(kwargs)
        return (
            [{
                "Ticker": f"TST{len(scan_calls)}",
                "Signal_Type": "BUY",
                "Entry_Price": 10.0,
                "Stop_Loss": 9.0,
                "Target_Price": 11.0,
                "Score": 7,
            }],
            [{"Ticker": "AAA"}, {"Ticker": "BBB"}],
            50.0,
            "CAUTIOUS",
        )

    first = run_daily_signals_logic(
        _run_req("2026-02-13:INTRADAY:11:00"),
        emit_audit_event_fn=lambda **kwargs: None,
        evaluate_data_freshness_fn=lambda **kwargs: {"overall_ok": True},
        get_market_signals_fn=_scan,
        build_recommendation_fn=_build_recommendation,
    )
    second = run_daily_signals_logic(
        _run_req("2026-02-13:INTRADAY:11:05"),
        emit_audit_event_fn=lambda **kwargs: None,
        evaluate_data_freshness_fn=lambda **kwargs: {"overall_ok": True},
        get_market_signals_fn=_scan,
        build_recommendation_fn=_build_recommendation,
    )

    assert first["status"] == "completed"
    assert second["status"] == "completed"
    assert first["run"]["id"] != second["run"]["id"]
    assert SignalRun.select().where(
        (SignalRun.run_date == datetime.date(2026, 2, 13)) &
        (SignalRun.scan_type == "INTRADAY")
    ).count() == 2
    assert [call["is_intraday"] for call in scan_calls] == [True, True]
    assert [item[1] for item in built] == ["2026-02-13:INTRADAY:11:00", "2026-02-13:INTRADAY:11:05"]


def test_run_daily_signals_logic_supports_pre_close_scan_type():
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    scan_calls = []

    req = SimpleNamespace(
        run_date="2026-02-14",
        scan_type="PRE_CLOSE",
        run_key="2026-02-14:PRE_CLOSE",
        force=False,
        model_version=None,
        index="EGX30",
        ignore_guard=False,
    )

    result = run_daily_signals_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        evaluate_data_freshness_fn=lambda **kwargs: {"overall_ok": True},
        get_market_signals_fn=lambda **kwargs: scan_calls.append(kwargs) or (
            [{
                "Ticker": "PCLS",
                "Signal_Type": "BUY",
                "Entry_Price": 10.0,
                "Stop_Loss": 9.0,
                "Target_Price": 11.0,
                "Score": 8,
            }],
            [{"Ticker": "AAA"}],
            55.0,
            "BULLISH",
        ),
        build_recommendation_fn=lambda signal, run, regime: SignalRecommendation(
            run=run,
            ticker=signal["Ticker"],
            side="BUY",
            entry_price=10.0,
            stop_loss=9.0,
            target_price=11.0,
            score=8,
            confidence=80.0,
            state="ACTIVE",
        ),
    )

    assert result["status"] == "completed"
    run = SignalRun.get_by_id(result["run"]["id"])
    assert run.scan_type == "PRE_CLOSE"
    assert run.run_key == "2026-02-14:PRE_CLOSE"
    assert scan_calls == [{"index_choice": "EGX30", "is_intraday": False, "is_pre_close": True}]


def test_run_daily_signals_logic_blocks_on_freshness():
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    req = SimpleNamespace(
        run_date="2026-02-12",
        scan_type="DAILY",
        force=True,
        model_version=None,
        index="EGX30",
        ignore_guard=False,
    )

    result = run_daily_signals_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        evaluate_data_freshness_fn=lambda **kwargs: {"overall_ok": False, "issues": ["stale"]},
        get_market_signals_fn=lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not scan")),
        build_recommendation_fn=lambda *args, **kwargs: None,
        now_fn=lambda: datetime.datetime(2026, 2, 12, 14, 0, 0),
    )

    assert result["status"] == "blocked"
    assert result["block_type"] == "freshness"
    assert result["block_reason"] == "stale"


def test_run_walkforward_validation_logic_auto_blocks_guard():
    run = SignalRun.create(run_date=TimeUtils.today() - datetime.timedelta(days=1), scan_type="DAILY", status="COMPLETED")
    rec = SignalRecommendation.create(
        run=run,
        ticker="FAIL",
        side="BUY",
        entry_price=100,
        stop_loss=90,
        target_price=110,
        score=8,
        confidence=80,
        state="ACTIVE",
    )
    SignalOutcome.create(
        recommendation=rec,
        run=run,
        ticker="FAIL",
        outcome_status="CLOSED",
        pnl_pct=-1.0,
        exit_date=TimeUtils.now(),
    )
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)

    req = SimpleNamespace(
        window_days=3650,
        min_closed_signals=1,
        min_win_rate_pct=80.0,
        min_avg_pnl_pct=0.0,
        min_week_win_rate_pct=None,
        max_consecutive_weak_weeks=2,
        auto_block=True,
        auto_unblock=True,
    )

    result = run_walkforward_validation_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
    )

    assert result["status"] == "fail"
    assert result["guard_action"] == "blocked"
    assert result["guard_state"]["is_blocked"] is True


def test_get_guard_state_creates_publish_record():
    state = get_guard_state()
    assert isinstance(state, SignalGuardState)
    assert state.name == "PUBLISH"


def test_build_recommendation_drops_candidates_below_min_signal_score(monkeypatch):
    monkeypatch.setattr(settings, "MIN_SIGNAL_SCORE", 8.0, raising=False)
    monkeypatch.setattr(settings, "MIN_SIGNAL_CONFIDENCE", 0.0, raising=False)
    run = SignalRun.create(run_date=datetime.date(2026, 2, 15), scan_type="DAILY", status="RUNNING")
    signal = {
        "Ticker": "COMI",
        "Signal_Type": "BUY",
        "Entry_Price": 100.0,
        "Stop_Loss": 95.0,
        "Target_Price": 110.0,
        "Score": 7,
    }
    rec = _build_recommendation(signal, run=run, regime="BULLISH")
    assert rec is None


def test_build_recommendation_drops_candidates_below_min_signal_confidence(monkeypatch):
    monkeypatch.setattr(settings, "MIN_SIGNAL_SCORE", 0.0, raising=False)
    monkeypatch.setattr(settings, "MIN_SIGNAL_CONFIDENCE", 75.0, raising=False)
    run = SignalRun.create(run_date=datetime.date(2026, 2, 16), scan_type="DAILY", status="RUNNING")
    signal = {
        "Ticker": "COMI",
        "Signal_Type": "BUY",
        "Entry_Price": 100.0,
        "Stop_Loss": 95.0,
        "Target_Price": 110.0,
        "Score": 8,
        "Confidence": 70.0,
    }
    rec = _build_recommendation(signal, run=run, regime="BULLISH")
    assert rec is None


def test_build_recommendation_marks_scanner_source_module(monkeypatch):
    monkeypatch.setattr(settings, "MIN_SIGNAL_SCORE", 0.0, raising=False)
    monkeypatch.setattr(settings, "MIN_SIGNAL_CONFIDENCE", 0.0, raising=False)
    run = SignalRun.create(run_date=datetime.date(2026, 2, 17), scan_type="DAILY", status="RUNNING")
    signal = {
        "Ticker": "COMI",
        "Signal_Type": "BUY",
        "Entry_Price": 100.0,
        "Stop_Loss": 95.0,
        "Target_Price": 110.0,
        "Score": 8,
    }

    rec = _build_recommendation(signal, run=run, regime="BULLISH")

    assert rec is not None
    rationale = json.loads(rec.rationale_json)
    assert rationale["source_module"] == "SCANNER"
    assert rationale["signal_side"] == "BUY"
    assert _recommendation_source_module(rec) == "SCANNER"
