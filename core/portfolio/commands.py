from typing import Any, Callable
import os
import json

from fastapi import HTTPException

from core.analyzers import TreasuryLedger
from core import PositionTracker
from database import Portfolio, Position, SignalAuditEvent
from core.exclusions import is_excluded_ticker, normalize_ticker

from .identity import enforce_manual_entry_gate, resolve_portfolio_id


def _emit_operator_event(
    event_type: str,
    *,
    severity: str = "INFO",
    message: str | None = None,
    details: dict[str, Any] | None = None,
    portfolio_id: int | None = None,
    ticker: str | None = None,
) -> None:
    try:
        portfolio = Portfolio.get_or_none(Portfolio.id == portfolio_id) if portfolio_id else None
        SignalAuditEvent.create(
            event_type=(event_type or "").upper().strip() or "OPERATOR_EVENT",
            severity=(severity or "INFO").upper().strip() or "INFO",
            actor_type="OPERATOR",
            actor_id=None,
            portfolio=portfolio,
            entity_type="TICKER" if ticker else "PORTFOLIO",
            entity_id=str(ticker or portfolio_id or ""),
            message=message,
            details_json=json.dumps(details or {}, default=str),
        )
    except Exception:
        pass


def add_trade_command(
    req: Any,
    *,
    resolve_portfolio_id_fn: Callable[[int | None], int | None] = resolve_portfolio_id,
    enforce_manual_entry_gate_fn: Callable[[str], tuple[str, dict[str, Any]]] = enforce_manual_entry_gate,
    add_gold_fn: Callable[..., dict[str, Any]] | None = None,
):
    resolved_add_gold_fn = add_gold_fn or TreasuryLedger.add_gold
    target_id = resolve_portfolio_id_fn(req.portfolio_id)
    if not target_id:
        raise HTTPException(404, "No user portfolio found")

    try:
        symbol, gate = enforce_manual_entry_gate_fn(req.ticker)
    except HTTPException as exc:
        _emit_operator_event(
            "OPERATOR_DEVIATION",
            severity="WARN",
            message="Manual trade blocked by entry gate.",
            details={
                "category": "invalid_manual_trade",
                "ticker": str(getattr(req, "ticker", "") or "").upper(),
                "error": exc.detail,
            },
            portfolio_id=target_id,
            ticker=str(getattr(req, "ticker", "") or "").upper(),
        )
        raise

    payload = {
        "ticker": symbol,
        "shares": req.shares,
        "price": req.price,
        "type": req.type,
        "portfolio_id": target_id,
    }
    for attr, field in (("sl", "sl"), ("tp", "tp"), ("tp2", "tp2"), ("date", "date")):
        if hasattr(req, attr):
            value = getattr(req, attr)
            if value is not None:
                payload[field] = value

    result = resolved_add_gold_fn(**payload)
    if isinstance(result, dict) and result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Add operation failed"))
    _emit_operator_event(
        "OPERATOR_MANUAL_OVERRIDE",
        severity="INFO",
        message="Manual trade added.",
        details={
            "category": "manual_trade_taken",
            "action": "ADD",
            "ticker": symbol,
            "shares": int(req.shares),
            "price": float(req.price),
            "gate_reason": gate.get("reason") if isinstance(gate, dict) else None,
        },
        portfolio_id=target_id,
        ticker=symbol,
    )
    return result


def close_trade_command(
    req: Any,
    *,
    resolve_portfolio_id_fn: Callable[[int | None], int | None] = resolve_portfolio_id,
    melt_gold_fn: Callable[..., dict[str, Any]] | None = None,
):
    resolved_melt_gold_fn = melt_gold_fn or TreasuryLedger.melt_gold
    target_id = resolve_portfolio_id_fn(req.portfolio_id)
    if not target_id:
        raise HTTPException(404, "No user portfolio found")

    result = resolved_melt_gold_fn(req.ticker, req.shares, req.price, portfolio_id=target_id)
    if isinstance(result, dict) and result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Close operation failed"))
    _emit_operator_event(
        "OPERATOR_MANUAL_OVERRIDE",
        severity="INFO",
        message="Manual trade closed.",
        details={
            "category": "manual_trade_taken",
            "action": "CLOSE",
            "ticker": str(req.ticker or "").upper(),
            "shares": int(req.shares) if req.shares is not None else None,
            "price": float(req.price),
        },
        portfolio_id=target_id,
        ticker=str(req.ticker or "").upper(),
    )
    return result


def update_trade_command(
    req: Any,
    *,
    resolve_portfolio_id_fn: Callable[[int | None], int | None] = resolve_portfolio_id,
    update_position_fn: Callable[..., bool] | None = None,
):
    resolved_update_position_fn = update_position_fn or PositionTracker.update_position
    target_id = resolve_portfolio_id_fn(req.portfolio_id)
    if not target_id:
        raise HTTPException(404, "No user portfolio found")
    symbol = str(req.ticker or "").upper()
    existing = Position.get_or_none(
        Position.portfolio == target_id,
        Position.ticker == symbol,
        Position.status == "OPEN",
    )
    previous = {
        "stop_loss": float(getattr(existing, "stop_loss", 0.0) or 0.0) if existing else None,
        "target_price": float(getattr(existing, "target_price", 0.0) or 0.0) if existing else None,
        "target_price_2": float(getattr(existing, "target_price_2", 0.0) or 0.0) if existing else None,
    }

    payload = {
        "ticker": req.ticker,
        "shares": req.shares,
        "entry_price": req.price,
        "sl": req.sl,
        "tp": req.tp,
        "portfolio_id": target_id,
    }
    tp2 = getattr(req, "tp2", None)
    if tp2 is not None:
        payload["tp2"] = tp2

    success = resolved_update_position_fn(**payload)
    if success:
        _emit_operator_event(
            "OPERATOR_MANUAL_OVERRIDE",
            severity="INFO",
            message="Manual position update applied.",
            details={
                "category": "manual_trade_taken",
                "action": "UPDATE",
                "ticker": symbol,
                "previous": previous,
                "new_stop_loss": float(req.sl) if req.sl is not None else None,
                "new_target_price": float(req.tp) if req.tp is not None else None,
                "new_target_price_2": float(tp2) if tp2 is not None else None,
            },
            portfolio_id=target_id,
            ticker=symbol,
        )
        if req.sl is not None:
            _emit_operator_event(
                "OPERATOR_DEVIATION",
                severity="INFO",
                message="Manual stop-loss modification recorded.",
                details={
                    "category": "stop_modification",
                    "ticker": symbol,
                    "previous_stop_loss": previous.get("stop_loss"),
                    "new_stop_loss": float(req.sl),
                },
                portfolio_id=target_id,
                ticker=symbol,
            )
            if existing and previous.get("stop_loss") is not None and float(req.sl) < previous["stop_loss"]:
                _emit_operator_event(
                    "OPERATOR_DEVIATION",
                    severity="WARN",
                    message="Stop-loss widened on manual update.",
                    details={
                        "category": "exit_rule_violation",
                        "ticker": symbol,
                        "previous_stop_loss": previous.get("stop_loss"),
                        "new_stop_loss": float(req.sl),
                        "reason": "manual_stop_widening",
                    },
                    portfolio_id=target_id,
                    ticker=symbol,
                )
        return {"status": "success", "message": "Position updated"}
    raise HTTPException(status_code=500, detail="Failed to update position")


def _write_genesis_lock_file():
    with open("genesis.lock", "w") as handle:
        handle.write("LOCKED")


def _aggregate_genesis_holdings(holdings: list[tuple[str, float, float]]) -> list[tuple[str, float, float]]:
    aggregated: dict[str, dict[str, float]] = {}
    for symbol, shares, price in holdings:
        current = aggregated.setdefault(symbol, {"shares": 0.0, "cost": 0.0})
        current["shares"] += shares
        current["cost"] += shares * price

    return [
        (symbol, values["shares"], values["cost"] / values["shares"])
        for symbol, values in aggregated.items()
        if values["shares"] > 0
    ]


def initialize_portfolio_genesis_command(
    req: Any,
    *,
    resolve_portfolio_id_fn: Callable[[int | None], int | None] = resolve_portfolio_id,
    get_portfolio_fn: Callable[[int], Any] = lambda portfolio_id: Portfolio.get_or_none(Portfolio.id == portfolio_id),
    create_portfolio_fn: Callable[..., Any] = Portfolio.create,
    normalize_ticker_fn: Callable[[str], str] = normalize_ticker,
    is_excluded_ticker_fn: Callable[[str], bool] = is_excluded_ticker,
    add_gold_fn: Callable[..., dict[str, Any]] = TreasuryLedger.add_gold,
    write_lock_file_fn: Callable[[], Any] = _write_genesis_lock_file,
):
    target_id = req.portfolio_id or resolve_portfolio_id_fn(None)
    portfolio = get_portfolio_fn(target_id) if target_id else None

    if not portfolio:
        if req.portfolio_id:
            raise HTTPException(404, "Portfolio not found")
        portfolio = create_portfolio_fn(name="My Portfolio", type="USER")

    portfolio.cash_egp = req.egp_balance
    portfolio.cash_usd = req.usd_balance
    portfolio.save()

    added_count = 0
    errors: list[str] = []

    if req.holdings:
        pending_holdings: list[tuple[str, float, float]] = []
        for holding in req.holdings:
            symbol = normalize_ticker_fn(holding.ticker)
            if not symbol:
                errors.append("UNKNOWN: Ticker is required")
                continue
            if is_excluded_ticker_fn(symbol):
                errors.append(f"{symbol}: blacklisted ticker")
                continue
            pending_holdings.append((symbol, holding.shares, holding.price))

        for symbol, shares, price in _aggregate_genesis_holdings(pending_holdings):
            result = add_gold_fn(
                ticker=symbol,
                shares=shares,
                price=price,
                type="EXISTING",
                portfolio_id=portfolio.id,
            )
            if isinstance(result, dict) and result.get("status") == "success":
                added_count += 1
            else:
                message = result.get("message") if isinstance(result, dict) else "Add operation failed"
                errors.append(f"{symbol}: {message}")

    write_lock_file_fn()

    return {
        "status": "success",
        "cash_egp": portfolio.cash_egp,
        "cash_usd": portfolio.cash_usd,
        "holdings_added": added_count,
        "errors": errors,
    }


def batch_positions_command(
    req: Any,
    *,
    resolve_portfolio_id_fn: Callable[[int | None], int | None] = resolve_portfolio_id,
    melt_gold_fn: Callable[..., dict[str, Any]] = TreasuryLedger.melt_gold,
    update_position_fn: Callable[..., bool] = PositionTracker.update_position,
):
    target_id = resolve_portfolio_id_fn(getattr(req, "portfolio_id", None))
    if not target_id:
        raise HTTPException(404, "No user portfolio found")

    action = str(getattr(req, "action", "") or "").upper().strip()
    tickers = [str(t or "").upper().strip() for t in getattr(req, "tickers", []) if str(t or "").strip()]
    if not tickers:
        raise HTTPException(400, "No tickers provided for batch action")

    results = []
    errors = []

    for ticker in tickers:
        pos = Position.get_or_none(
            Position.portfolio == target_id,
            Position.ticker == ticker,
            Position.status == "OPEN",
        )
        if not pos:
            errors.append(f"{ticker}: Position not found or not OPEN")
            continue

        curr_price = pos.current_price if pos.current_price is not None else (pos.entry_price or 0.0)
        shares = pos.shares or 0

        if action == "MOVE_STOPS_BREAKEVEN":
            entry_p = pos.entry_price or 0.0
            pos.stop_loss = entry_p
            pos.save()
            results.append({"ticker": ticker, "status": "updated", "action": "MOVE_STOPS_BREAKEVEN", "new_sl": entry_p})

        elif action == "SCALE_OUT_50":
            sell_shares = max(int(shares * 0.5), 1)
            try:
                melt_gold_fn(ticker, sell_shares, curr_price, portfolio_id=target_id)
                results.append({"ticker": ticker, "status": "scaled_out_50", "sold_shares": sell_shares, "price": curr_price})
            except Exception as exc:
                errors.append(f"{ticker}: Failed to scale out 50%: {exc}")

        elif action == "FLATTEN":
            try:
                melt_gold_fn(ticker, shares, curr_price, portfolio_id=target_id)
                results.append({"ticker": ticker, "status": "flattened", "sold_shares": shares, "price": curr_price})
            except Exception as exc:
                errors.append(f"{ticker}: Failed to flatten: {exc}")

        else:
            errors.append(f"{ticker}: Unsupported action '{action}'")

    return {
        "status": "success" if results and not errors else ("partial" if results else "error"),
        "action": action,
        "portfolio_id": target_id,
        "processed_count": len(results),
        "results": results,
        "errors": errors,
    }


def apply_rebalancing_command(
    req: Any,
    *,
    resolve_portfolio_id_fn: Callable[[int | None], int | None] = resolve_portfolio_id,
    get_rebalancing_fn: Callable[..., Any] = TreasuryLedger.get_rebalancing_recommendations,
    melt_gold_fn: Callable[..., dict[str, Any]] = TreasuryLedger.melt_gold,
    add_gold_fn: Callable[..., dict[str, Any]] = TreasuryLedger.add_gold,
):
    target_id = resolve_portfolio_id_fn(getattr(req, "portfolio_id", None))
    if not target_id:
        raise HTTPException(404, "No user portfolio found")

    model = str(getattr(req, "model", "EQUAL_WEIGHT") or "EQUAL_WEIGHT").upper()
    recs = get_rebalancing_fn(portfolio_id=target_id, target_model=model)

    executed = []
    errors = []

    for item in recs:
        action = item.get("action")
        ticker = item.get("ticker")
        shares = int(item.get("shares_delta") or item.get("shares") or 0)
        price = float(item.get("current_price") or 0.0)

        if shares <= 0 or price <= 0:
            continue

        if action == "TRIM":
            try:
                melt_gold_fn(ticker, shares, price, portfolio_id=target_id)
                executed.append({"ticker": ticker, "action": "TRIM", "shares": shares, "price": price})
            except Exception as exc:
                errors.append(f"Trim {ticker} failed: {exc}")
        elif action == "ADD":
            try:
                add_gold_fn(ticker=ticker, shares=shares, price=price, type="REBALANCE", portfolio_id=target_id)
                executed.append({"ticker": ticker, "action": "ADD", "shares": shares, "price": price})
            except Exception as exc:
                errors.append(f"Add {ticker} failed: {exc}")

    return {
        "status": "success" if executed else ("no_action_needed" if not errors else "error"),
        "model": model,
        "portfolio_id": target_id,
        "executed_count": len(executed),
        "executed": executed,
        "errors": errors,
    }


def seed_demo_portfolio_command(
    *,
    portfolio_id: int,
    get_portfolio_fn: Callable[[int], Any] = lambda candidate_id: Portfolio.get_or_none(Portfolio.id == candidate_id),
    is_excluded_ticker_fn: Callable[[str], bool] = is_excluded_ticker,
    create_position_fn: Callable[..., Any] = Position.create,
):
    try:
        portfolio = get_portfolio_fn(portfolio_id)
        if not portfolio:
            raise HTTPException(404, "Not found")
        if portfolio.positions.count() > 0:
            return {"status": "skipped"}
        if is_excluded_ticker_fn("COMI"):
            return {"status": "skipped", "reason": "COMI is blacklisted"}

        create_position_fn(
            portfolio=portfolio,
            ticker="COMI",
            shares=500,
            entry_price=85.50,
            stop_loss=82.00,
            target_price=95.00,
            current_price=88.20,
            status="OPEN",
            sector="Banking",
        )
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
