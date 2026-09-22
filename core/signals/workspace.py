from typing import Optional
import datetime
from typing import Any, Callable

from fastapi import HTTPException

from core import TimeUtils
from database import Portfolio, SignalDelivery, SignalRecommendation, SignalRun, SignalValidationRun, Trade

from .boundary import error_context, validation_error
from core.signals.guard import get_guard_state, serialize_guard_state, serialize_run


def portfolio_window_metrics(
    portfolio_id: int,
    window_days: int,
    *,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
    today_fn: Callable[[], datetime.date] = TimeUtils.today,
):
    since_dt = now_fn() - datetime.timedelta(days=window_days)
    trades = list(
        Trade.select().where(
            (Trade.portfolio == portfolio_id)
            & (Trade.exit_date >= since_dt)
        )
    )
    total = len(trades)
    wins = [trade for trade in trades if (trade.pnl or 0) > 0]
    losses = [trade for trade in trades if (trade.pnl or 0) <= 0]
    total_pnl = round(sum(float(trade.pnl or 0.0) for trade in trades), 2)
    avg_pnl_pct = round(sum(float(trade.pnl_pct or 0.0) for trade in trades) / total, 4) if total else 0.0
    win_rate = round((len(wins) / total) * 100, 2) if total else 0.0
    gross_win = sum(float(trade.pnl or 0.0) for trade in wins)
    gross_loss = sum(float(trade.pnl or 0.0) for trade in losses)
    if gross_loss < 0:
        profit_factor = round(gross_win / abs(gross_loss), 4) if abs(gross_loss) > 0 else 99.0
    else:
        profit_factor = 99.0 if gross_win > 0 else 0.0

    since_date = since_dt.date()
    delivered_runs = list(
        SignalDelivery.select(SignalDelivery, SignalRun)
        .join(SignalRun)
        .where(
            (SignalDelivery.portfolio == portfolio_id)
            & (SignalDelivery.status.in_(["SENT", "DRY_RUN"]))
            & (SignalRun.run_date >= since_date)
        )
    )
    delivered_run_ids = [delivery.run.id for delivery in delivered_runs if delivery.run]
    rec_count = 0
    rec_tickers = set()
    if delivered_run_ids:
        recs = list(
            SignalRecommendation.select().where(SignalRecommendation.run.in_(delivered_run_ids))
        )
        rec_count = len(recs)
        rec_tickers = {rec.ticker for rec in recs}
    linked_trades = [trade for trade in trades if trade.ticker in rec_tickers]
    linked_count = len(linked_trades)

    return {
        "window_days": window_days,
        "from_date": since_date.strftime("%Y-%m-%d"),
        "to_date": today_fn().strftime("%Y-%m-%d"),
        "trades": total,
        "win_rate_pct": win_rate,
        "total_pnl": total_pnl,
        "avg_pnl_pct": avg_pnl_pct,
        "profit_factor": profit_factor,
        "delivered_runs": len(set(delivered_run_ids)),
        "recommendations_delivered": rec_count,
        "linked_trades": linked_count,
        "signal_link_rate_pct": round((linked_count / total) * 100, 2) if total else 0.0,
    }


def get_workspace_signal_performance(
    *,
    portfolio_id: int,
    windows: str = "30,60,90",
    error_context_fn: Callable[..., dict] = error_context,
    validation_error_fn: Callable[..., dict] = validation_error,
    portfolio_window_metrics_fn: Callable[[int, int], dict] = portfolio_window_metrics,
    get_guard_state_fn=get_guard_state,
    serialize_guard_state_fn: Callable[[Any], dict] = serialize_guard_state,
):
    portfolio = Portfolio.get_or_none((Portfolio.id == portfolio_id) & (Portfolio.type == "USER"))
    if not portfolio:
        raise HTTPException(
            status_code=404,
            detail=error_context_fn(
                "not_found",
                "user_portfolio_not_found",
                "USER portfolio not found",
                portfolio_id=portfolio_id,
            ),
        )

    parsed = []
    for token in windows.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            window = int(token)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=validation_error_fn(
                    "invalid_windows_token",
                    f"Invalid window '{token}'",
                    parameter="windows",
                    invalid_token=token,
                ),
            ) from exc
        if window < 1 or window > 3650:
            raise HTTPException(
                status_code=400,
                detail=validation_error_fn(
                    "windows_value_out_of_range",
                    f"Window out of range '{token}'",
                    parameter="windows",
                    invalid_token=token,
                    min=1,
                    max=3650,
                ),
            )
        parsed.append(window)
    if not parsed:
        parsed = [30, 60, 90]

    reports = [portfolio_window_metrics_fn(portfolio_id, window) for window in sorted(set(parsed))]
    return {
        "portfolio": {"id": portfolio.id, "name": portfolio.name, "type": portfolio.type},
        "windows": reports,
        "guard_state": serialize_guard_state_fn(get_guard_state_fn()),
    }


def get_signals_sla(
    *,
    days: int = 30,
    validation_error_fn: Callable[..., dict] = validation_error,
    today_fn: Callable[[], datetime.date] = TimeUtils.today,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
    get_guard_state_fn=get_guard_state,
    serialize_guard_state_fn: Callable[[Any], dict] = serialize_guard_state,
    serialize_run_fn: Callable[[SignalRun], dict] = serialize_run,
):
    if days < 1:
        raise HTTPException(
            status_code=400,
            detail=validation_error_fn(
                "days_out_of_range",
                "days must be >= 1",
                parameter="days",
                provided=days,
                min=1,
            ),
        )

    since_date = today_fn() - datetime.timedelta(days=days - 1)
    runs = list(
        SignalRun.select()
        .where(SignalRun.run_date >= since_date)
        .order_by(SignalRun.run_date.desc())
    )
    by_status = {}
    for run in runs:
        by_status[run.status] = by_status.get(run.status, 0) + 1

    run_ids = [run.id for run in runs]
    deliveries_query = SignalDelivery.select()
    if run_ids:
        deliveries_query = deliveries_query.where(SignalDelivery.run.in_(run_ids))
    else:
        deliveries_query = deliveries_query.where(SignalDelivery.id == -1)
    deliveries = list(deliveries_query)

    delivery_by_status = {}
    for delivery in deliveries:
        delivery_by_status[delivery.status] = delivery_by_status.get(delivery.status, 0) + 1

    sent = delivery_by_status.get("SENT", 0)
    failed = delivery_by_status.get("FAILED", 0)
    success_rate = 100.0
    if sent + failed > 0:
        success_rate = round((sent / (sent + failed)) * 100, 2)

    latest_run = runs[0] if runs else None
    today_run = next((run for run in runs if run.run_date == today_fn()), None)
    latest_validation = SignalValidationRun.select().order_by(SignalValidationRun.created_at.desc()).first()

    latencies = [
        float(d.latency_ms)
        for d in deliveries
        if getattr(d, "latency_ms", None) is not None and d.latency_ms >= 0
    ]
    avg_latency_ms = round(float(sum(latencies) / len(latencies)), 2) if latencies else None

    return {
        "window_days": days,
        "from_date": since_date.strftime("%Y-%m-%d"),
        "to_date": today_fn().strftime("%Y-%m-%d"),
        "runs": {
            "total": len(runs),
            "by_status": by_status,
            "latest": serialize_run_fn(latest_run) if latest_run else None,
            "today_status": today_run.status if today_run else "MISSING",
        },
        "deliveries": {
            "total": len(deliveries),
            "by_status": delivery_by_status,
            "sent": sent,
            "failed": failed,
            "success_rate_pct": success_rate,
            "failed_pending_retry": delivery_by_status.get("FAILED", 0),
            "avg_latency_ms": avg_latency_ms,
            "latency_sample_count": len(latencies),
        },
        "guard_state": serialize_guard_state_fn(get_guard_state_fn()),
        "latest_validation": (
            {
                "id": latest_validation.id,
                "run_date": latest_validation.run_date.strftime("%Y-%m-%d"),
                "status": latest_validation.status,
                "window_days": latest_validation.window_days,
                "closed_signals": latest_validation.closed_signals,
                "win_rate_pct": latest_validation.win_rate_pct,
                "avg_pnl_pct": latest_validation.avg_pnl_pct,
                "degradation_reason": latest_validation.degradation_reason,
                "created_at": latest_validation.created_at.isoformat() if latest_validation.created_at else None,
            }
            if latest_validation
            else None
        ),
    }
