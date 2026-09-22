from core.settings import settings
import json
import warnings
from typing import Any, Optional


from core import PositionTracker, TelegramBot_Alerts, TimeUtils
from core.DataManager import DataManager
from database import HorusExecution, Portfolio, Position, SignalRecommendation, SignalRun

from .identity import get_horus_portfolio
from .telegram import build_open_message, build_skip_message, build_update_message, recommendation_target2


def _calculate_shares(entry_price: float, stop_loss: float) -> int:
    account_size = float(getattr(settings, "ACCOUNT_BALANCE", 100000) or 100000)
    risk_per_trade_pct = float(getattr(settings, "RISK_PER_TRADE", 2.0) or 2.0)
    risk_amount = account_size * (risk_per_trade_pct / 100.0)
    risk_per_share = float(entry_price) - float(stop_loss)

    if risk_per_share <= 0:
        shares = 100
    else:
        shares = int(risk_amount / risk_per_share)

    max_cost = account_size * 0.20
    if shares * float(entry_price) > max_cost:
        shares = int(max_cost / float(entry_price))

    return max(0, shares)


def _trigger_source(run: SignalRun) -> str:
    scan_type = str(run.scan_type or "INTRADAY").upper()
    if scan_type == "DAILY":
        return "DAILY_NEXT_OPEN"
    if scan_type == "PRE_CLOSE":
        return "PRE_CLOSE"
    return "INTRADAY"


def _active_execution_for_ticker(portfolio: Portfolio, ticker: str) -> Optional[HorusExecution]:
    return (
        HorusExecution.select()
        .where(
            (HorusExecution.portfolio == portfolio) &
            (HorusExecution.ticker == ticker) &
            (HorusExecution.state.in_(["OPEN", "UPDATED"]))
        )
        .order_by(HorusExecution.updated_at.desc())
        .first()
    )


def _persist_failed_execution(portfolio: Portfolio, run: SignalRun, rec: SignalRecommendation, reason: str) -> HorusExecution:
    return HorusExecution.create(
        portfolio=portfolio,
        run=run,
        recommendation=rec,
        ticker=rec.ticker,
        state="FAILED",
        trigger_source=_trigger_source(run),
        planned_entry_price=rec.entry_price,
        actual_entry_price=None,
        active_stop_loss=rec.stop_loss,
        active_target_price=rec.target_price,
        details_json=json.dumps({"reason": reason}),
        created_at=TimeUtils.now(),
        updated_at=TimeUtils.now(),
    )


def _gap_pct(planned_entry: float, actual_entry: float) -> float:
    if not planned_entry:
        return 0.0
    return abs((float(actual_entry) - float(planned_entry)) / float(planned_entry)) * 100.0


def _get_next_open_price(ticker: str) -> tuple[Optional[float], Optional[str]]:
    intra_df = DataManager.get_intraday_data(ticker, limit=1, refresh_if_stale=False)
    if intra_df is None or intra_df.empty:
        return None, None
    first_bar = intra_df.iloc[0]
    open_price = first_bar.get("Open")
    if open_price is None:
        return None, None
    first_ts = intra_df.index[0]
    return float(open_price), first_ts.isoformat() if hasattr(first_ts, "isoformat") else str(first_ts)


def execute_run_for_horus(run_id: int) -> dict[str, Any]:
    warnings.warn("execute_run_for_horus is deprecated. Use core.signals.executor.SignalExecutor instead.", DeprecationWarning, stacklevel=2)
    run = SignalRun.get_by_id(run_id)

    portfolio = get_horus_portfolio()
    if not portfolio:
        return {
            "status": "skipped",
            "summary": {"opened": 0, "updated": 0, "failed": 0, "skipped": 1},
            "message": "Horus portfolio not found",
        }

    recommendations = list(
        SignalRecommendation.select()
        .where((SignalRecommendation.run == run) & (SignalRecommendation.state == "ACTIVE"))
        .order_by(SignalRecommendation.score.desc(), SignalRecommendation.confidence.desc())
    )

    summary = {"opened": 0, "updated": 0, "failed": 0, "skipped": 0}

    for rec in recommendations:
        existing_position = Position.get_or_none(
            (Position.portfolio == portfolio) &
            (Position.ticker == rec.ticker) &
            (Position.status == "OPEN")
        )
        existing_execution = _active_execution_for_ticker(portfolio, rec.ticker)
        tp2 = recommendation_target2(rec)

        if str(run.scan_type or "").upper() == "DAILY":
            HorusExecution.create(
                portfolio=portfolio,
                run=run,
                recommendation=rec,
                ticker=rec.ticker,
                state="PENDING_OPEN",
                trigger_source="DAILY_NEXT_OPEN",
                planned_entry_price=float(rec.entry_price),
                actual_entry_price=None,
                active_stop_loss=float(rec.stop_loss),
                active_target_price=float(rec.target_price),
                details_json=json.dumps({}),
                created_at=TimeUtils.now(),
                updated_at=TimeUtils.now(),
            )
            summary["skipped"] += 1
            continue

        if existing_position and existing_execution:
            previous = {
                "stop_loss": float(existing_execution.active_stop_loss or existing_position.stop_loss or 0.0),
                "target_price": float(existing_execution.active_target_price or existing_position.target_price or 0.0),
                "target_price_2": float(existing_position.target_price_2 or 0.0),
            }
            updated = PositionTracker.update_position(
                ticker=rec.ticker,
                sl=float(rec.stop_loss),
                tp=float(rec.target_price),
                tp2=float(tp2) if tp2 is not None else None,
                portfolio_id=portfolio.id,
            )
            if updated:
                existing_execution.run = run
                existing_execution.recommendation = rec
                existing_execution.state = "UPDATED"
                existing_execution.trigger_source = _trigger_source(run)
                existing_execution.active_stop_loss = float(rec.stop_loss)
                existing_execution.active_target_price = float(rec.target_price)
                existing_execution.details_json = json.dumps(
                    {
                        "previous": previous,
                        "updated": {
                            "stop_loss": float(rec.stop_loss),
                            "target_price": float(rec.target_price),
                            "target_price_2": float(tp2 or 0.0),
                        },
                    }
                )
                existing_execution.updated_at = TimeUtils.now()
                existing_execution.save()
                tg_resp = TelegramBot_Alerts.send_message(build_update_message(portfolio, rec, existing_execution))
                if tg_resp.get("ok"):
                    message_id = ((tg_resp.get("result") or {}).get("message_id"))
                    existing_execution.update_message_id = str(message_id) if message_id is not None else None
                    existing_execution.save()
                summary["updated"] += 1
            else:
                _persist_failed_execution(portfolio, run, rec, "position_update_failed")
                summary["failed"] += 1
            continue

        shares = _calculate_shares(float(rec.entry_price), float(rec.stop_loss))
        if shares <= 0:
            _persist_failed_execution(portfolio, run, rec, "position_size_zero")
            summary["failed"] += 1
            continue

        opened = PositionTracker.add_position(
            ticker=rec.ticker,
            shares=shares,
            entry_price=float(rec.entry_price),
            sl=float(rec.stop_loss),
            tp=float(rec.target_price),
            tp2=float(tp2) if tp2 is not None else None,
            portfolio_id=portfolio.id,
        )
        if not opened:
            _persist_failed_execution(portfolio, run, rec, "position_open_failed")
            summary["failed"] += 1
            continue

        execution = HorusExecution.create(
            portfolio=portfolio,
            run=run,
            recommendation=rec,
            ticker=rec.ticker,
            state="OPEN",
            trigger_source=_trigger_source(run),
            planned_entry_price=float(rec.entry_price),
            actual_entry_price=float(rec.entry_price),
            active_stop_loss=float(rec.stop_loss),
            active_target_price=float(rec.target_price),
            details_json=json.dumps({"shares": shares}),
            created_at=TimeUtils.now(),
            updated_at=TimeUtils.now(),
        )
        tg_resp = TelegramBot_Alerts.send_message(build_open_message(portfolio, rec, shares, execution))
        if tg_resp.get("ok"):
            message_id = ((tg_resp.get("result") or {}).get("message_id"))
            execution.open_message_id = str(message_id) if message_id is not None else None
            execution.save()
        summary["opened"] += 1

    return {"status": "completed", "summary": summary}


def execute_pending_daily_entries_for_horus(max_gap_pct: float = 1.5) -> dict[str, Any]:
    warnings.warn("execute_pending_daily_entries_for_horus is deprecated. Use core.signals.executor.SignalExecutor instead.", DeprecationWarning, stacklevel=2)
    portfolio = get_horus_portfolio()

    if not portfolio:
        return {"status": "skipped", "summary": {"opened": 0, "skipped": 0, "failed": 0}, "message": "Horus portfolio not found"}

    pendings = list(
        HorusExecution.select()
        .where((HorusExecution.portfolio == portfolio) & (HorusExecution.state == "PENDING_OPEN"))
        .order_by(HorusExecution.created_at.asc())
    )

    summary = {"opened": 0, "skipped": 0, "failed": 0}

    for execution in pendings:
        rec = execution.recommendation
        if rec is None:
            execution.state = "FAILED"
            execution.details_json = json.dumps({"reason": "missing_recommendation"})
            execution.updated_at = TimeUtils.now()
            execution.save()
            summary["failed"] += 1
            continue

        open_price, open_ts = _get_next_open_price(rec.ticker)
        if open_price is None:
            execution.state = "FAILED"
            execution.details_json = json.dumps({"reason": "missing_open_price"})
            execution.updated_at = TimeUtils.now()
            execution.save()
            summary["failed"] += 1
            continue

        gap_pct = _gap_pct(float(execution.planned_entry_price or rec.entry_price), float(open_price))
        execution.actual_entry_price = float(open_price)
        execution.gap_pct = float(gap_pct)
        execution.updated_at = TimeUtils.now()

        if gap_pct > float(max_gap_pct):
            execution.state = "SKIPPED"
            execution.gap_adjusted = False
            execution.details_json = json.dumps({"reason": "gap_threshold_exceeded", "open_ts": open_ts})
            execution.save()
            tg_resp = TelegramBot_Alerts.send_message(build_skip_message(portfolio, rec, execution))
            if tg_resp.get("ok"):
                message_id = ((tg_resp.get("result") or {}).get("message_id"))
                execution.skip_message_id = str(message_id) if message_id is not None else None
                execution.save()
            summary["skipped"] += 1
            continue

        tp2 = recommendation_target2(rec)
        shares = _calculate_shares(float(open_price), float(rec.stop_loss))
        if shares <= 0:
            execution.state = "FAILED"
            execution.details_json = json.dumps({"reason": "position_size_zero", "open_ts": open_ts})
            execution.save()
            summary["failed"] += 1
            continue

        opened = PositionTracker.add_position(
            ticker=rec.ticker,
            shares=shares,
            entry_price=float(open_price),
            sl=float(rec.stop_loss),
            tp=float(rec.target_price),
            tp2=float(tp2) if tp2 is not None else None,
            portfolio_id=portfolio.id,
        )
        if not opened:
            execution.state = "FAILED"
            execution.details_json = json.dumps({"reason": "position_open_failed", "open_ts": open_ts})
            execution.save()
            summary["failed"] += 1
            continue

        execution.state = "OPEN"
        execution.gap_adjusted = bool(abs(float(open_price) - float(execution.planned_entry_price or rec.entry_price)) > 1e-9)
        execution.details_json = json.dumps(
            {
                "open_ts": open_ts,
                "gap_adjusted": execution.gap_adjusted,
                "shares": shares,
            }
        )
        execution.save()
        tg_resp = TelegramBot_Alerts.send_message(build_open_message(portfolio, rec, shares, execution))
        if tg_resp.get("ok"):
            message_id = ((tg_resp.get("result") or {}).get("message_id"))
            execution.open_message_id = str(message_id) if message_id is not None else None
            execution.save()
        summary["opened"] += 1

    return {"status": "completed", "summary": summary}
