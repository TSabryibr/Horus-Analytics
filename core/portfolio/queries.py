from typing import Any, Callable, Optional

from fastapi import HTTPException

from core.analyzers import TreasuryLedger
from core import PositionTracker, RiskManager, TimeUtils
from database import Portfolio, Position, Trade, PortfolioSnapshot
from core.exclusions import filter_excluded_from_payload

from .identity import resolve_portfolio_id


def _normalize_trade_exit_reason(row: dict[str, Any]) -> dict[str, Any]:
    reason = str(row.get("reason") or "").upper().replace(" ", "_")
    if reason != "STOP_LOSS":
        return row

    try:
        entry_price = float(row.get("entry_price") or 0.0)
        exit_price = float(row.get("exit_price") or 0.0)
        pnl_pct = float(row.get("pnl_pct") or 0.0)
    except (TypeError, ValueError):
        return row

    normalized = dict(row)
    if exit_price > entry_price or pnl_pct > 0:
        normalized["reason"] = "TRAILING_STOP"
    elif abs(exit_price - entry_price) < 0.000001 or abs(pnl_pct) < 0.005:
        normalized["reason"] = "BREAKEVEN_STOP"
    return normalized


def get_portfolio_query(
    *,
    portfolio_id: Optional[int],
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    get_hoard_status_fn: Callable[..., Any] = TreasuryLedger.get_hoard_status,
    filter_payload_fn: Callable[[Any], Any] = filter_excluded_from_payload,
):
    target_id = resolve_portfolio_id_fn(portfolio_id)
    if not target_id:
        raise HTTPException(404, "No user portfolio found")

    payload = get_hoard_status_fn(portfolio_id=target_id)
    if isinstance(payload, dict) and payload.get("status") == "error":
        raise HTTPException(status_code=400, detail=payload.get("message"))
    return filter_payload_fn(payload)


def get_positions_query(
    *,
    portfolio_id: Optional[int],
    now_fn: Callable[[], Any] = TimeUtils.now,
    filter_payload_fn: Callable[[Any], Any] = filter_excluded_from_payload,
):
    query = Position.select().where(
        (Position.status == "OPEN") &
        (Position.entry_date <= now_fn())
    )
    if portfolio_id:
        query = query.where(Position.portfolio == portfolio_id)
    return filter_payload_fn(list(query.dicts()))


def get_trades_query(
    *,
    limit: int,
    portfolio_id: Optional[int],
    now_fn: Callable[[], Any] = TimeUtils.now,
    filter_payload_fn: Callable[[Any], Any] = filter_excluded_from_payload,
):
    query = Trade.select().where(Trade.exit_date <= now_fn())
    if portfolio_id:
        query = query.where(Trade.portfolio == portfolio_id)
    trades = list(query.order_by(Trade.exit_date.desc()).limit(limit).dicts())
    return filter_payload_fn([_normalize_trade_exit_reason(row) for row in trades])


def _select_first_portfolio_id() -> Optional[int]:
    any_portfolio = Portfolio.select().order_by(Portfolio.id.asc()).first()
    return any_portfolio.id if any_portfolio else None


def _resolve_existing_portfolio_id(
    *,
    portfolio_id: Optional[int],
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]],
    select_first_portfolio_id_fn: Callable[[], Optional[int]],
) -> Optional[int]:
    target_id = resolve_portfolio_id_fn(portfolio_id)
    if target_id:
        return target_id
    return select_first_portfolio_id_fn()


def get_portfolio_metrics_query(
    *,
    portfolio_id: Optional[int],
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    select_first_portfolio_id_fn: Callable[[], Optional[int]] = _select_first_portfolio_id,
    update_live_prices_fn: Callable[[], Any] = PositionTracker.update_live_prices,
    now_fn: Callable[[], Any] = TimeUtils.now,
):
    target_id = _resolve_existing_portfolio_id(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=resolve_portfolio_id_fn,
        select_first_portfolio_id_fn=select_first_portfolio_id_fn,
    )
    if not target_id:
        raise HTTPException(404, "Portfolio not found")

    update_live_prices_fn()
    now_ref = now_fn()

    trade_query = Trade.select().where(Trade.exit_date <= now_ref)
    trade_query = trade_query.where(Trade.portfolio == target_id)
    trades = list(trade_query.dicts())

    pos_query = Position.select().where(
        (Position.status == "OPEN") &
        (Position.entry_date <= now_ref)
    )
    pos_query = pos_query.where(Position.portfolio == target_id)
    open_positions = list(pos_query.dicts())

    unrealized_pnl = sum(
        (position["current_price"] - position["entry_price"]) * position["shares"]
        for position in open_positions
        if position["current_price"] and position["entry_price"]
    )

    if not trades:
        return {
            "win_rate": 0,
            "total_pnl": round(unrealized_pnl, 2),
            "realized_pnl": 0,
            "unrealized_pnl": round(unrealized_pnl, 2),
            "profit_factor": 0,
            "total_trades": 0,
        }

    from pandas import DataFrame

    df = DataFrame(trades)
    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] <= 0]
    win_rate = (len(wins) / len(df)) * 100
    realized_pnl = df["pnl"].sum()
    profit_factor = wins["pnl"].sum() / abs(losses["pnl"].sum()) if losses["pnl"].sum() != 0 else 99.0

    return {
        "win_rate": round(win_rate, 2),
        "total_pnl": round(realized_pnl + unrealized_pnl, 2),
        "realized_pnl": round(realized_pnl, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "profit_factor": round(profit_factor, 2),
        "total_trades": len(df),
    }


def get_equity_curve_query(
    *,
    portfolio_id: Optional[int],
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    select_first_portfolio_id_fn: Callable[[], Optional[int]] = _select_first_portfolio_id,
    now_fn: Callable[[], Any] = TimeUtils.now,
    get_portfolio_metrics_query_fn: Callable[..., dict[str, Any]] = get_portfolio_metrics_query,
):
    target_id = _resolve_existing_portfolio_id(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=resolve_portfolio_id_fn,
        select_first_portfolio_id_fn=select_first_portfolio_id_fn,
    )
    if not target_id:
        raise HTTPException(404, "Portfolio not found")

    base_equity = 1000000.0

    now_ref = now_fn()
    query = Trade.select().where(Trade.exit_date <= now_ref)
    query = query.where(Trade.portfolio == target_id)
    trades = list(query.order_by(Trade.exit_date).dicts())
    curve_data = [{"date": "Baseline", "equity": base_equity}]

    if not trades:
        metrics = get_portfolio_metrics_query_fn(portfolio_id=target_id)
        curve_data.append({
            "date": now_fn().strftime("%Y-%m-%d"),
            "equity": base_equity + metrics["unrealized_pnl"],
        })
        return curve_data

    from pandas import DataFrame

    df = DataFrame(trades)
    df["cumulative_pnl"] = df["pnl"].cumsum()
    curve = df.groupby("exit_date")["cumulative_pnl"].last().reset_index()
    for _, row in curve.iterrows():
        curve_data.append({"date": str(row["exit_date"]), "equity": base_equity + row["cumulative_pnl"]})
    return curve_data


def get_portfolio_report_query(
    *,
    portfolio_id: Optional[int],
    trades_limit: int = 20,
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    select_first_portfolio_id_fn: Callable[[], Optional[int]] = _select_first_portfolio_id,
    update_live_prices_fn: Callable[[], Any] = PositionTracker.update_live_prices,
    now_fn: Callable[[], Any] = TimeUtils.now,
    get_portfolio_metrics_query_fn: Callable[..., dict[str, Any]] = get_portfolio_metrics_query,
    get_equity_curve_query_fn: Callable[..., list[dict[str, Any]]] = get_equity_curve_query,
    get_trades_query_fn: Callable[..., list[dict[str, Any]]] = get_trades_query,
):
    target_id = _resolve_existing_portfolio_id(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=resolve_portfolio_id_fn,
        select_first_portfolio_id_fn=select_first_portfolio_id_fn,
    )
    if not target_id:
        raise HTTPException(404, "Portfolio not found")

    metrics = get_portfolio_metrics_query_fn(
        portfolio_id=target_id,
        resolve_portfolio_id_fn=resolve_portfolio_id_fn,
        select_first_portfolio_id_fn=select_first_portfolio_id_fn,
        update_live_prices_fn=update_live_prices_fn,
        now_fn=now_fn,
    )
    curve = get_equity_curve_query_fn(
        portfolio_id=target_id,
        resolve_portfolio_id_fn=resolve_portfolio_id_fn,
        select_first_portfolio_id_fn=select_first_portfolio_id_fn,
        now_fn=now_fn,
        get_portfolio_metrics_query_fn=lambda **kwargs: metrics,
    )
    trades = get_trades_query_fn(
        limit=trades_limit,
        portfolio_id=target_id,
        now_fn=now_fn,
        filter_payload_fn=lambda payload: payload,
    )

    return {
        "metrics": metrics,
        "curve": curve,
        "trades": trades,
    }


def get_portfolio_analysis_query(
    *,
    portfolio_id: Optional[int],
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    select_first_portfolio_id_fn: Callable[[], Optional[int]] = _select_first_portfolio_id,
    update_live_prices_fn: Callable[[], Any] = PositionTracker.update_live_prices,
    analyze_portfolio_fn: Callable[[int], Any] = RiskManager.analyze_portfolio,
):
    target_id = _resolve_existing_portfolio_id(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=resolve_portfolio_id_fn,
        select_first_portfolio_id_fn=select_first_portfolio_id_fn,
    )
    if not target_id:
        raise HTTPException(404, "Portfolio not found")

    try:
        update_live_prices_fn()
    except Exception:
        pass

    return analyze_portfolio_fn(target_id)
