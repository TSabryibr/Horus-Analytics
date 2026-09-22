from __future__ import annotations

import datetime
from typing import Any, Optional

from core.horus.identity import resolve_preferred_user_portfolio
from database import (
    HorusExecution,
    Portfolio,
    Position,
    PublishedSignalFollowUp,
    PublishedSignalLifecycle,
    Signal,
    SignalDelivery,
    SignalOutcome,
    SignalRecommendation,
    SignalRun,
    Trade,
)
from .periods import _coerce_float


def _resolve_report_portfolio(portfolio_id: Optional[int]) -> Optional[Portfolio]:
    if portfolio_id is not None:
        return Portfolio.get_or_none(Portfolio.id == portfolio_id)
    return resolve_preferred_user_portfolio()


def _signed_signal_return_pct(side: Any, entry_price: Any, exit_price: Any) -> float:
    entry = _coerce_float(entry_price, 0.0)
    exit_value = _coerce_float(exit_price, 0.0)
    if entry <= 0 or exit_value <= 0:
        return 0.0
    if str(side or "BUY").upper() == "SELL":
        return round(((entry - exit_value) / entry) * 100.0, 4)
    return round(((exit_value - entry) / entry) * 100.0, 4)


def _hours_between(start_at: Optional[datetime.datetime], end_at: Optional[datetime.datetime]) -> Optional[float]:
    if start_at is None or end_at is None:
        return None
    delta_hours = (end_at - start_at).total_seconds() / 3600.0
    if delta_hours < 0:
        return None
    return round(delta_hours, 4)


def _resolved_lifecycle_exit_price(lifecycle: PublishedSignalLifecycle) -> float:
    state = str(lifecycle.state or "").upper()
    if state == "STOP_LOSS_HIT":
        return _coerce_float(lifecycle.close_price or lifecycle.stop_loss_active or lifecycle.stop_loss_initial, 0.0)
    if state == "TP2_HIT":
        return _coerce_float(lifecycle.close_price or lifecycle.target_price_2 or lifecycle.target_price_1, 0.0)
    return _coerce_float(
        lifecycle.close_price
        or lifecycle.target_price_2
        or lifecycle.target_price_1
        or lifecycle.stop_loss_active
        or lifecycle.stop_loss_initial,
        0.0,
    )


def _lifecycle_breakdown_rows(
    lifecycles: list[PublishedSignalLifecycle],
    *,
    key_fn,
) -> list[dict[str, Any]]:
    buckets: dict[str, list[PublishedSignalLifecycle]] = {}
    for lifecycle in lifecycles:
        key = str(key_fn(lifecycle) or "UNKNOWN").strip().upper() or "UNKNOWN"
        buckets.setdefault(key, []).append(lifecycle)

    rows: list[dict[str, Any]] = []
    for key in sorted(buckets.keys()):
        group = buckets[key]
        published_count = len(group)
        filled = sum(1 for lifecycle in group if lifecycle.opened_at is not None)
        tp1_hits = sum(1 for lifecycle in group if lifecycle.tp1_hit_at is not None)
        full_wins = sum(1 for lifecycle in group if str(lifecycle.state or "").upper() == "TP2_HIT")
        stop_hits = sum(1 for lifecycle in group if str(lifecycle.state or "").upper() == "STOP_LOSS_HIT")
        realized_returns = [
            _signed_signal_return_pct(
                lifecycle.side,
                lifecycle.entry_price_filled or lifecycle.entry_price_planned,
                _resolved_lifecycle_exit_price(lifecycle),
            )
            for lifecycle in group
            if str(lifecycle.state or "").upper() in {"TP2_HIT", "STOP_LOSS_HIT"}
        ]
        rows.append(
            {
                "key": key,
                "published_count": published_count,
                "fill_rate_pct": round((filled / published_count) * 100.0, 2) if published_count else 0.0,
                "tp1_hit_rate_pct": round((tp1_hits / published_count) * 100.0, 2) if published_count else 0.0,
                "full_win_rate_pct": round((full_wins / published_count) * 100.0, 2) if published_count else 0.0,
                "stop_loss_rate_pct": round((stop_hits / published_count) * 100.0, 2) if published_count else 0.0,
                "avg_realized_pnl_pct": round(sum(realized_returns) / len(realized_returns), 4) if realized_returns else 0.0,
            }
        )
    return rows


def _aggregate_signal_review(runs: list[SignalRun]) -> tuple[dict[str, Any], list[str], list[str], list[dict[str, Any]]]:
    notes: list[str] = []
    warnings: list[str] = []
    run_ids = [r.id for r in runs]
    run_count = len(runs)
    signals_generated = int(sum(int(r.signals_count or 0) for r in runs))

    review: dict[str, Any] = {
        "review_source": "SIGNAL_OUTCOME",
        "run_count": run_count,
        "signals_generated": signals_generated,
        "published_signals": 0,
        "closed_outcomes": 0,
        "open_outcomes": 0,
        "no_trade_outcomes": 0,
        "win_rate_pct": 0.0,
        "avg_pnl_pct": 0.0,
        "expectancy_pct": 0.0,
        "fill_rate_pct": 0.0,
        "expiry_rate_pct": 0.0,
        "tp1_hit_rate_pct": 0.0,
        "full_win_rate_pct": 0.0,
        "stop_loss_rate_pct": 0.0,
        "avg_time_to_open_hours": 0.0,
        "avg_time_to_resolution_hours": 0.0,
        "followup_total": 0,
        "followup_sent_rate_pct": 0.0,
        "followup_failure_rate_pct": 0.0,
        "followup_avg_retry_count": 0.0,
        "followup_pending_count": 0,
        "followup_suppressed_count": 0,
        "lane_breakdown": [],
        "source_module_breakdown": [],
        "operating_mode_breakdown": [],
        "best_tickers": [],
        "worst_tickers": [],
        "what_worked": [],
        "what_failed": [],
    }
    recommendations: list[dict[str, Any]] = []

    if not run_ids:
        notes.append("No completed daily signal runs were found for this period.")
        warnings.append("Signal review has limited confidence due to missing runs.")
        return review, notes, warnings, recommendations

    outcomes = list(
        SignalOutcome.select()
        .where(SignalOutcome.run.in_(run_ids))
    )
    for outcome in outcomes:
        status = str(outcome.outcome_status or "").upper()
        if status == "CLOSED":
            review["closed_outcomes"] += 1
        elif status == "OPEN":
            review["open_outcomes"] += 1
        else:
            review["no_trade_outcomes"] += 1

    closed = [
        o for o in outcomes
        if str(o.outcome_status or "").upper() == "CLOSED" and o.pnl_pct is not None
    ]
    pnl_values = [_coerce_float(o.pnl_pct) for o in closed]
    if pnl_values:
        wins = [p for p in pnl_values if p > 0]
        losses = [p for p in pnl_values if p <= 0]
        review["win_rate_pct"] = round((len(wins) / len(pnl_values)) * 100.0, 2)
        review["avg_pnl_pct"] = round(sum(pnl_values) / len(pnl_values), 4)
        avg_win = (sum(wins) / len(wins)) if wins else 0.0
        avg_loss = (sum(losses) / len(losses)) if losses else 0.0
        win_prob = len(wins) / len(pnl_values)
        review["expectancy_pct"] = round((win_prob * avg_win) + ((1 - win_prob) * avg_loss), 4)
    else:
        notes.append("No closed outcomes with PnL were found in the selected period.")
        warnings.append("Outcome sample is too small for a robust performance estimate.")

    by_ticker: dict[str, list[float]] = {}
    for outcome in closed:
        ticker = str(outcome.ticker or "").strip().upper()
        if not ticker:
            continue
        by_ticker.setdefault(ticker, []).append(_coerce_float(outcome.pnl_pct))

    if by_ticker:
        ranked = sorted(
            (
                {
                    "ticker": ticker,
                    "avg_pnl_pct": round(sum(vals) / len(vals), 4),
                    "count": len(vals),
                }
                for ticker, vals in by_ticker.items()
            ),
            key=lambda row: row["avg_pnl_pct"],
            reverse=True,
        )
        review["best_tickers"] = ranked[:3]
        review["worst_tickers"] = list(reversed(ranked[-3:]))

    if review["win_rate_pct"] >= 55:
        review["what_worked"].append("Win rate held above 55% in closed outcomes.")
    if review["best_tickers"]:
        top = review["best_tickers"][0]
        review["what_worked"].append(f"Best contributor: {top['ticker']} ({top['avg_pnl_pct']}% avg).")
    if review["win_rate_pct"] <= 45 and review["closed_outcomes"] > 0:
        review["what_failed"].append("Win rate was below 45% and requires tighter selectivity.")
    if review["no_trade_outcomes"] > review["closed_outcomes"]:
        review["what_failed"].append("High no-trade ratio suggests low conversion of signal opportunities.")
    if review["worst_tickers"]:
        weak = review["worst_tickers"][0]
        review["what_failed"].append(f"Weak contributor: {weak['ticker']} ({weak['avg_pnl_pct']}% avg).")

    latest_run = runs[-1]
    top_recommendations = list(
        SignalRecommendation.select()
        .where(SignalRecommendation.run == latest_run)
        .order_by(SignalRecommendation.score.desc())
        .limit(5)
    )
    for rec in top_recommendations:
        recommendations.append(
            {
                "ticker": str(rec.ticker or "").upper(),
                "action": str(rec.side or "BUY").upper(),
                "confidence": round(_coerce_float(rec.confidence, 0.0), 1),
                "entry_zone": round(_coerce_float(rec.entry_price), 4),
                "stop_loss": round(_coerce_float(rec.stop_loss), 4),
                "take_profit": round(_coerce_float(rec.target_price), 4),
            }
        )

    return review, notes, warnings, recommendations


def _apply_legacy_signal_fallback(
    review: dict[str, Any],
    notes: list[str],
    warnings: list[str],
    period_start: datetime.date,
    period_end: datetime.date,
) -> tuple[dict[str, Any], list[str], list[str]]:
    if int(review.get("run_count", 0)) > 0:
        return review, notes, warnings

    legacy_signals = list(
        Signal.select(Signal.ticker, Signal.date, Signal.signal_type, Signal.score)
        .where((Signal.date >= period_start) & (Signal.date <= period_end))
        .order_by(Signal.date.asc())
    )
    if not legacy_signals:
        return review, notes, warnings

    unique_dates = sorted({s.date for s in legacy_signals if s.date is not None})
    review["run_count"] = len(unique_dates)
    review["signals_generated"] = len(legacy_signals)
    review["review_source"] = "LEGACY_SIGNAL"

    by_ticker: dict[str, int] = {}
    for sig in legacy_signals:
        ticker = str(sig.ticker or "").strip().upper()
        if not ticker:
            continue
        by_ticker[ticker] = by_ticker.get(ticker, 0) + 1

    if by_ticker:
        top = sorted(by_ticker.items(), key=lambda item: item[1], reverse=True)[:3]
        review["what_worked"] = [f"Most active tickers (legacy): {', '.join(t for t, _ in top)}."]

    cleaned_notes = [
        n for n in notes
        if n != "No completed daily signal runs were found for this period."
    ]
    cleaned_warnings = [
        w for w in warnings
        if w != "Signal review has limited confidence due to missing runs."
    ]
    cleaned_notes.append(
        "No SignalRun records found; legacy Signal table was used for activity coverage."
    )
    cleaned_warnings.append(
        "Outcome metrics (win rate/PnL/expectancy) are unavailable without SignalRun/SignalOutcome history."
    )
    return review, cleaned_notes, cleaned_warnings


def _aggregate_published_lifecycle_review(
    portfolio: Portfolio,
    portfolio_runs: list[SignalRun],
    period_start: datetime.date,
    period_end: datetime.date,
) -> Optional[tuple[dict[str, Any], list[str], list[str], list[dict[str, Any]]]]:
    notes: list[str] = []
    warnings: list[str] = []
    recommendations: list[dict[str, Any]] = []
    since_dt = datetime.datetime.combine(period_start, datetime.time.min)
    until_dt = datetime.datetime.combine(period_end + datetime.timedelta(days=1), datetime.time.min)
    lifecycles = list(
        PublishedSignalLifecycle.select()
        .where(
            (PublishedSignalLifecycle.portfolio == portfolio)
            & (PublishedSignalLifecycle.published_at >= since_dt)
            & (PublishedSignalLifecycle.published_at < until_dt)
        )
        .order_by(PublishedSignalLifecycle.published_at.asc(), PublishedSignalLifecycle.id.asc())
    )
    if not lifecycles:
        return None

    published_count = len(lifecycles)
    closed_states = {"TP2_HIT", "STOP_LOSS_HIT"}
    unresolved_states = {"PUBLISHED", "OPEN", "TP1_HIT", "AMBIGUOUS"}
    no_trade_states = {"EXPIRED", "CANCELLED"}

    review: dict[str, Any] = {
        "review_source": "PUBLISHED_LIFECYCLE",
        "run_count": len(portfolio_runs),
        "signals_generated": published_count,
        "published_signals": published_count,
        "closed_outcomes": sum(1 for lifecycle in lifecycles if str(lifecycle.state or "").upper() in closed_states),
        "open_outcomes": sum(1 for lifecycle in lifecycles if str(lifecycle.state or "").upper() in unresolved_states),
        "no_trade_outcomes": sum(1 for lifecycle in lifecycles if str(lifecycle.state or "").upper() in no_trade_states),
        "win_rate_pct": 0.0,
        "avg_pnl_pct": 0.0,
        "expectancy_pct": 0.0,
        "fill_rate_pct": 0.0,
        "expiry_rate_pct": 0.0,
        "tp1_hit_rate_pct": 0.0,
        "full_win_rate_pct": 0.0,
        "stop_loss_rate_pct": 0.0,
        "avg_time_to_open_hours": 0.0,
        "avg_time_to_resolution_hours": 0.0,
        "followup_total": 0,
        "followup_sent_rate_pct": 0.0,
        "followup_failure_rate_pct": 0.0,
        "followup_avg_retry_count": 0.0,
        "followup_pending_count": 0,
        "followup_suppressed_count": 0,
        "lane_breakdown": [],
        "source_module_breakdown": [],
        "operating_mode_breakdown": [],
        "best_tickers": [],
        "worst_tickers": [],
        "what_worked": [],
        "what_failed": [],
    }

    filled_count = sum(1 for lifecycle in lifecycles if lifecycle.opened_at is not None)
    tp1_count = sum(1 for lifecycle in lifecycles if lifecycle.tp1_hit_at is not None)
    expiry_count = sum(1 for lifecycle in lifecycles if str(lifecycle.state or "").upper() == "EXPIRED")
    full_win_count = sum(1 for lifecycle in lifecycles if str(lifecycle.state or "").upper() == "TP2_HIT")
    stop_loss_count = sum(1 for lifecycle in lifecycles if str(lifecycle.state or "").upper() == "STOP_LOSS_HIT")
    ambiguous_count = sum(1 for lifecycle in lifecycles if str(lifecycle.state or "").upper() == "AMBIGUOUS")

    review["fill_rate_pct"] = round((filled_count / published_count) * 100.0, 2) if published_count else 0.0
    review["expiry_rate_pct"] = round((expiry_count / published_count) * 100.0, 2) if published_count else 0.0
    review["tp1_hit_rate_pct"] = round((tp1_count / published_count) * 100.0, 2) if published_count else 0.0
    review["full_win_rate_pct"] = round((full_win_count / published_count) * 100.0, 2) if published_count else 0.0
    review["stop_loss_rate_pct"] = round((stop_loss_count / published_count) * 100.0, 2) if published_count else 0.0

    open_durations = [
        hours
        for hours in (_hours_between(lifecycle.published_at, lifecycle.opened_at) for lifecycle in lifecycles)
        if hours is not None
    ]
    resolution_durations = [
        hours
        for hours in (_hours_between(lifecycle.published_at, lifecycle.closed_at) for lifecycle in lifecycles)
        if hours is not None
    ]
    review["avg_time_to_open_hours"] = round(sum(open_durations) / len(open_durations), 2) if open_durations else 0.0
    review["avg_time_to_resolution_hours"] = (
        round(sum(resolution_durations) / len(resolution_durations), 2) if resolution_durations else 0.0
    )

    closed_lifecycles = [
        lifecycle for lifecycle in lifecycles
        if str(lifecycle.state or "").upper() in closed_states
    ]
    realized_rows: list[dict[str, Any]] = []
    for lifecycle in closed_lifecycles:
        exit_price = _resolved_lifecycle_exit_price(lifecycle)
        pnl_pct = _signed_signal_return_pct(
            lifecycle.side,
            lifecycle.entry_price_filled or lifecycle.entry_price_planned,
            exit_price,
        )
        realized_rows.append(
            {
                "ticker": str(lifecycle.ticker or "").strip().upper(),
                "pnl_pct": pnl_pct,
            }
        )

    if realized_rows:
        pnl_values = [row["pnl_pct"] for row in realized_rows]
        wins = [value for value in pnl_values if value > 0]
        review["win_rate_pct"] = round((len(wins) / len(realized_rows)) * 100.0, 2)
        review["avg_pnl_pct"] = round(sum(pnl_values) / len(pnl_values), 4)
        review["expectancy_pct"] = round(sum(pnl_values) / published_count, 4) if published_count else 0.0

        by_ticker: dict[str, list[float]] = {}
        for row in realized_rows:
            if not row["ticker"]:
                continue
            by_ticker.setdefault(row["ticker"], []).append(row["pnl_pct"])
        ranked = sorted(
            (
                {
                    "ticker": ticker,
                    "avg_pnl_pct": round(sum(values) / len(values), 4),
                    "count": len(values),
                }
                for ticker, values in by_ticker.items()
            ),
            key=lambda item: item["avg_pnl_pct"],
            reverse=True,
        )
        review["best_tickers"] = ranked[:3]
        review["worst_tickers"] = list(reversed(ranked[-3:]))
    else:
        warnings.append("Published signals exist in this period, but none have reached a realized terminal trade outcome yet.")

    review["lane_breakdown"] = _lifecycle_breakdown_rows(lifecycles, key_fn=lambda lifecycle: lifecycle.lane)
    review["source_module_breakdown"] = _lifecycle_breakdown_rows(
        lifecycles,
        key_fn=lambda lifecycle: lifecycle.source_module,
    )
    review["operating_mode_breakdown"] = _lifecycle_breakdown_rows(
        lifecycles,
        key_fn=lambda lifecycle: lifecycle.operating_mode,
    )

    followups = list(
        PublishedSignalFollowUp.select()
        .where(
            (PublishedSignalFollowUp.portfolio == portfolio)
            & (PublishedSignalFollowUp.created_at >= since_dt)
            & (PublishedSignalFollowUp.created_at < until_dt)
        )
        .order_by(PublishedSignalFollowUp.created_at.asc(), PublishedSignalFollowUp.id.asc())
    )
    followup_total = len(followups)
    if followup_total:
        sent_count = sum(1 for followup in followups if str(followup.queue_state or "").upper() == "SENT")
        failed_count = sum(1 for followup in followups if str(followup.queue_state or "").upper() == "FAILED")
        pending_count = sum(
            1 for followup in followups
            if str(followup.queue_state or "").upper() in {"PENDING", "READY"}
        )
        suppressed_count = sum(1 for followup in followups if str(followup.queue_state or "").upper() == "SUPPRESSED")
        review["followup_total"] = followup_total
        review["followup_sent_rate_pct"] = round((sent_count / followup_total) * 100.0, 2)
        review["followup_failure_rate_pct"] = round((failed_count / followup_total) * 100.0, 2)
        review["followup_avg_retry_count"] = round(
            sum(int(followup.retry_count or 0) for followup in followups) / followup_total,
            2,
        )
        review["followup_pending_count"] = pending_count
        review["followup_suppressed_count"] = suppressed_count

    notes.append("Signal review is sourced from published Horus lifecycle records for this portfolio.")
    if review["followup_total"] > 0:
        notes.append("Delivery KPIs are sourced from published Horus lifecycle follow-up jobs for this portfolio.")
    if ambiguous_count:
        warnings.append(f"{ambiguous_count} published signal lifecycle case(s) remain ambiguous and may need admin review.")
    if review["fill_rate_pct"] >= 60:
        review["what_worked"].append("Published signal fill rate held above 60% in the selected period.")
    if review["tp1_hit_rate_pct"] >= 40:
        review["what_worked"].append("A healthy share of published signals progressed to TP1.")
    if review["best_tickers"]:
        top = review["best_tickers"][0]
        review["what_worked"].append(f"Best contributor: {top['ticker']} ({top['avg_pnl_pct']}% avg).")
    if review["stop_loss_rate_pct"] >= 35:
        review["what_failed"].append("Stop-loss frequency was elevated across published signals and needs tighter selectivity.")
    if review["expiry_rate_pct"] >= 30:
        review["what_failed"].append("Too many published signals expired before entry, which weakens conversion.")
    if review["worst_tickers"]:
        weak = review["worst_tickers"][0]
        review["what_failed"].append(f"Weak contributor: {weak['ticker']} ({weak['avg_pnl_pct']}% avg).")

    latest_run = portfolio_runs[-1] if portfolio_runs else None
    if latest_run:
        for rec in (
            SignalRecommendation.select()
            .where(SignalRecommendation.run == latest_run)
            .order_by(SignalRecommendation.score.desc())
            .limit(5)
        ):
            recommendations.append(
                {
                    "ticker": str(rec.ticker or "").upper(),
                    "action": str(rec.side or "BUY").upper(),
                    "confidence": round(_coerce_float(rec.confidence, 0.0), 1),
                    "entry_zone": round(_coerce_float(rec.entry_price), 4),
                    "stop_loss": round(_coerce_float(rec.stop_loss), 4),
                    "take_profit": round(_coerce_float(rec.target_price), 4),
                }
            )

    return review, notes, warnings, recommendations


def _aggregate_portfolio_signal_review(
    portfolio: Portfolio,
    period_start: datetime.date,
    period_end: datetime.date,
) -> tuple[dict[str, Any], list[str], list[str], list[dict[str, Any]]]:
    notes: list[str] = []
    warnings: list[str] = []
    recommendations: list[dict[str, Any]] = []
    since_dt = datetime.datetime.combine(period_start, datetime.time.min)
    until_dt = datetime.datetime.combine(period_end + datetime.timedelta(days=1), datetime.time.min)

    delivered_runs = list(
        SignalDelivery.select(SignalDelivery, SignalRun)
        .join(SignalRun)
        .where(
            (SignalDelivery.portfolio == portfolio)
            & (SignalDelivery.status.in_(["SENT", "DRY_RUN"]))
            & (SignalRun.run_date >= period_start)
            & (SignalRun.run_date <= period_end)
        )
    )
    delivered_run_ids = {delivery.run.id for delivery in delivered_runs if delivery.run}
    execution_run_ids = {
        execution.run.id
        for execution in (
            HorusExecution.select(HorusExecution, SignalRun)
            .join(SignalRun)
            .where(
                (HorusExecution.portfolio == portfolio)
                & (HorusExecution.run.is_null(False))
                & (SignalRun.run_date >= period_start)
                & (SignalRun.run_date <= period_end)
            )
        )
        if execution.run
    }
    run_ids = sorted(delivered_run_ids | execution_run_ids)
    portfolio_runs = (
        list(
            SignalRun.select()
            .where(SignalRun.id.in_(run_ids))
            .order_by(SignalRun.run_date.asc(), SignalRun.completed_at.asc())
        )
        if run_ids
        else []
    )
    lifecycle_review = _aggregate_published_lifecycle_review(
        portfolio=portfolio,
        portfolio_runs=portfolio_runs,
        period_start=period_start,
        period_end=period_end,
    )
    if lifecycle_review is not None:
        return lifecycle_review

    trades = list(
        Trade.select().where(
            (Trade.portfolio == portfolio)
            & (Trade.exit_date >= since_dt)
            & (Trade.exit_date < until_dt)
        )
    )
    open_positions = list(
        Position.select().where(
            (Position.portfolio == portfolio)
            & (Position.status == "OPEN")
            & (Position.entry_date < until_dt)
        )
    )

    review: dict[str, Any] = {
        "review_source": "PORTFOLIO_TRADE",
        "run_count": len(portfolio_runs),
        "signals_generated": int(sum(int(run.signals_count or 0) for run in portfolio_runs)),
        "published_signals": 0,
        "closed_outcomes": len(trades),
        "open_outcomes": len(open_positions),
        "no_trade_outcomes": 0,
        "win_rate_pct": 0.0,
        "avg_pnl_pct": 0.0,
        "expectancy_pct": 0.0,
        "fill_rate_pct": 0.0,
        "expiry_rate_pct": 0.0,
        "tp1_hit_rate_pct": 0.0,
        "full_win_rate_pct": 0.0,
        "stop_loss_rate_pct": 0.0,
        "avg_time_to_open_hours": 0.0,
        "avg_time_to_resolution_hours": 0.0,
        "followup_total": 0,
        "followup_sent_rate_pct": 0.0,
        "followup_failure_rate_pct": 0.0,
        "followup_avg_retry_count": 0.0,
        "followup_pending_count": 0,
        "followup_suppressed_count": 0,
        "lane_breakdown": [],
        "source_module_breakdown": [],
        "operating_mode_breakdown": [],
        "best_tickers": [],
        "worst_tickers": [],
        "what_worked": [],
        "what_failed": [],
    }

    pnl_values = [_coerce_float(trade.pnl_pct) for trade in trades if trade.pnl_pct is not None]
    if pnl_values:
        wins = [p for p in pnl_values if p > 0]
        losses = [p for p in pnl_values if p <= 0]
        review["win_rate_pct"] = round((len(wins) / len(pnl_values)) * 100.0, 2)
        review["avg_pnl_pct"] = round(sum(pnl_values) / len(pnl_values), 4)
        avg_win = (sum(wins) / len(wins)) if wins else 0.0
        avg_loss = (sum(losses) / len(losses)) if losses else 0.0
        win_prob = len(wins) / len(pnl_values)
        review["expectancy_pct"] = round((win_prob * avg_win) + ((1 - win_prob) * avg_loss), 4)

        by_ticker: dict[str, list[float]] = {}
        for trade in trades:
            ticker = str(trade.ticker or "").strip().upper()
            if not ticker or trade.pnl_pct is None:
                continue
            by_ticker.setdefault(ticker, []).append(_coerce_float(trade.pnl_pct))
        ranked = sorted(
            (
                {
                    "ticker": ticker,
                    "avg_pnl_pct": round(sum(vals) / len(vals), 4),
                    "count": len(vals),
                }
                for ticker, vals in by_ticker.items()
            ),
            key=lambda row: row["avg_pnl_pct"],
            reverse=True,
        )
        review["best_tickers"] = ranked[:3]
        review["worst_tickers"] = list(reversed(ranked[-3:]))
    elif review["run_count"] > 0:
        warnings.append("Selected portfolio has delivered runs but no closed trades in this period.")

    if review["signals_generated"] > 0:
        review["no_trade_outcomes"] = max(
            int(review["signals_generated"]) - int(review["closed_outcomes"]) - int(review["open_outcomes"]),
            0,
        )

    if review["win_rate_pct"] >= 55:
        review["what_worked"].append("Portfolio win rate held above 55% in the selected period.")
    if review["best_tickers"]:
        top = review["best_tickers"][0]
        review["what_worked"].append(f"Best contributor: {top['ticker']} ({top['avg_pnl_pct']}% avg).")
    if review["closed_outcomes"] > 0 and review["win_rate_pct"] <= 45:
        review["what_failed"].append("Portfolio win rate was below 45% and needs tighter execution selectivity.")
    if review["worst_tickers"]:
        weak = review["worst_tickers"][0]
        review["what_failed"].append(f"Weak contributor: {weak['ticker']} ({weak['avg_pnl_pct']}% avg).")

    latest_run = portfolio_runs[-1] if portfolio_runs else None
    if latest_run:
        for rec in (
            SignalRecommendation.select()
            .where(SignalRecommendation.run == latest_run)
            .order_by(SignalRecommendation.score.desc())
            .limit(5)
        ):
            recommendations.append(
                {
                    "ticker": str(rec.ticker or "").upper(),
                    "action": str(rec.side or "BUY").upper(),
                    "confidence": round(_coerce_float(rec.confidence, 0.0), 1),
                    "entry_zone": round(_coerce_float(rec.entry_price), 4),
                    "stop_loss": round(_coerce_float(rec.stop_loss), 4),
                    "take_profit": round(_coerce_float(rec.target_price), 4),
                }
            )
    elif review["closed_outcomes"] == 0 and review["open_outcomes"] == 0:
        notes.append("Selected portfolio has no delivered signal or trade activity in this period.")

    return review, notes, warnings, recommendations
