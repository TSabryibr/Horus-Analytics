from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from core.signals.SignalTelemetryTracker import telemetry_tracker
from database import LegacySignalOutcome

router = APIRouter(prefix="/api/v1/telemetry", tags=["Signal Telemetry"])

@router.get("/stats", response_model=Dict[str, Any])
def get_telemetry_stats():
    """
    Returns closed-beta signal intelligence statistics including win rate, target hit counts, and average realized PnL.
    """
    return telemetry_tracker.get_telemetry_summary()

@router.get("/signals", response_model=List[Dict[str, Any]])
def list_telemetry_signals(limit: int = 50):
    """
    Returns historical signal outcomes with max gain, drawdown, and realized outcome status.
    """
    outcomes = (
        LegacySignalOutcome.select()
        .order_by(LegacySignalOutcome.updated_at.desc())
        .limit(limit)
    )
    result = []
    for item in outcomes:
        result.append({
            "id": item.id,
            "ticker": item.ticker,
            "signal_date": str(item.signal_date),
            "entry_price": item.entry_price,
            "max_price": item.max_price,
            "min_price": item.min_price,
            "current_price": item.current_price,
            "max_gain_pct": item.max_gain_pct,
            "max_drawdown_pct": item.max_drawdown_pct,
            "realized_pnl_pct": item.realized_pnl_pct,
            "target_1_hit": item.target_1_hit,
            "target_2_hit": item.target_2_hit,
            "stop_loss_hit": item.stop_loss_hit,
            "outcome_status": item.outcome_status,
            "updated_at": str(item.updated_at)
        })
    return result

@router.get("/suppressions", response_model=List[Dict[str, Any]])
def list_telemetry_suppressions(limit: int = 50):
    """
    Returns recent signal suppression logs detailing why signals were intercepted by risk gates or kill switches.
    """
    from database import SignalSuppressionLog
    logs = (
        SignalSuppressionLog.select()
        .order_by(SignalSuppressionLog.created_at.desc())
        .limit(limit)
    )
    result = []
    for item in logs:
        result.append({
            "id": item.id,
            "ticker": item.ticker,
            "price": item.price,
            "score": item.score,
            "suppression_tag": item.suppression_tag,
            "kill_reason": item.kill_reason,
            "created_at": str(item.created_at)
        })
    return result

@router.get("/forward-test", response_model=Dict[str, Any])
def get_forward_test_metrics():
    """
    Returns empirical forward-test performance metrics including realized win rate %, TP1/TP2/SL hit counts, and active shadow signals.
    """
    from core.signals.ShadowLiveRunner import shadow_runner
    return shadow_runner.get_forward_test_metrics()

@router.get("/reasoning-feed", response_model=List[Dict[str, Any]])
def get_reasoning_feed(limit: int = 50):
    """
    Returns unified real-time reasoning feed combining valid dispatches, shadow logs, and risk-suppressed events.
    """
    from database import LegacySignalOutcome, SignalSuppressionLog
    events = []
    
    outcomes = LegacySignalOutcome.select().order_by(LegacySignalOutcome.updated_at.desc()).limit(limit)

    for o in outcomes:
        events.append({
            "type": "SIGNAL_DISPATCHED",
            "ticker": o.ticker,
            "price": o.entry_price,
            "status": o.outcome_status,
            "details": f"Target 1: {o.target_1_hit}, Target 2: {o.target_2_hit}, SL: {o.stop_loss_hit}",
            "timestamp": str(o.updated_at)
        })
        
    suppressions = SignalSuppressionLog.select().order_by(SignalSuppressionLog.created_at.desc()).limit(limit)
    for s in suppressions:
        events.append({
            "type": "SIGNAL_SUPPRESSED",
            "ticker": s.ticker,
            "price": s.price,
            "status": s.suppression_tag,
            "details": s.kill_reason,
            "timestamp": str(s.created_at)
        })

    events.sort(key=lambda x: str(x.get("timestamp")), reverse=True)
    return events[:limit]
