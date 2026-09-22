from core.settings import settings
import os
from typing import Any, Callable, Optional, List, Dict

from core.analyzers import TreasuryLedger
from fastapi import HTTPException

from core import PositionTracker, TelegramBot_Alerts, TimeUtils, RiskManager, WalkForwardValidation
from database import Portfolio, Position
from core.exclusions import is_excluded_ticker, normalize_ticker

from .identity import resolve_portfolio_id


def _get_portfolio_mgmt_setting(name: str, default: Any) -> Any:
    return getattr(settings, name, default)


def tp2_from_tp1(tp1: float, *, env_get_fn: Callable[[str, str], str] = os.getenv) -> float:
    raw = _get_portfolio_mgmt_setting("PORTFOLIO_MGMT_TP2_PCT", None)
    if raw is None:
        raw = env_get_fn("SIGNAL_TP2_PCT", "4")
    try:
        pct = float(raw)
    except ValueError:
        pct = 4.0
    if tp1 <= 0:
        return 0.0
    return tp1 * (1 + max(0.0, pct) / 100.0)


def parse_holding_input(
    row,
    *,
    normalize_ticker_fn: Callable[[str], str] = normalize_ticker,
    is_excluded_ticker_fn: Callable[[str], bool] = is_excluded_ticker,
    sl_pct: float = settings.SL_PCT,
    tp1_pct: float = settings.TP1_PCT,
):
    ticker = normalize_ticker_fn(row.ticker)
    if not ticker:
        raise ValueError("Ticker is required")
    if is_excluded_ticker_fn(ticker):
        raise ValueError(f"{ticker} is blacklisted")

    shares = row.shares
    entry = row.entry_price
    total_cost = row.total_cost

    if shares is None and entry is not None and total_cost is not None and entry > 0:
        shares = total_cost / entry
    if entry is None and shares is not None and total_cost is not None and shares > 0:
        entry = total_cost / shares

    if shares is None or entry is None:
        raise ValueError("Provide either (shares + entry_price) or (total_cost + shares/entry_price)")

    shares_int = int(round(float(shares)))
    entry_f = float(entry)
    if shares_int <= 0:
        raise ValueError("Shares must be > 0")
    if entry_f <= 0:
        raise ValueError("Entry price must be > 0")

    sl = float(row.stop_loss) if row.stop_loss is not None else entry_f * (1 - (sl_pct / 100.0))
    tp = float(row.target_price) if row.target_price is not None else entry_f * (1 + (tp1_pct / 100.0))

    return {
        "ticker": ticker,
        "shares": shares_int,
        "entry_price": entry_f,
        "stop_loss": sl,
        "target_price": tp,
        "currency": (row.currency or "EGP").upper(),
        "sector": row.sector,
        "notes": row.notes,
    }


def calculate_kelly_position_size(
    entry_price: float,
    stop_loss: float,
    target_price: float,
    total_capital: float = 100000.0,
    win_rate: float = 0.55,
    kelly_fraction: float = 0.25,
) -> dict:
    if entry_price <= 0 or stop_loss <= 0 or target_price <= 0 or entry_price <= stop_loss or target_price <= entry_price:
        return {
            "kelly_pct": 0.0,
            "recommended_shares": 0,
            "recommended_amount": 0.0,
            "risk_reward_ratio": 0.0,
        }

    risk_per_share = entry_price - stop_loss
    reward_per_share = target_price - entry_price
    b = reward_per_share / risk_per_share

    p = max(0.1, min(0.9, win_rate))
    q = 1.0 - p
    f_star = (p * b - q) / b

    if f_star <= 0:
        return {
            "kelly_pct": 0.0,
            "recommended_shares": 0,
            "recommended_amount": 0.0,
            "risk_reward_ratio": round(b, 2),
        }

    f_adjusted = max(0.0, min(0.20, f_star * kelly_fraction))
    recommended_amount = total_capital * f_adjusted
    recommended_shares = int(recommended_amount / entry_price) if entry_price > 0 else 0

    return {
        "kelly_pct": round(f_adjusted * 100.0, 2),
        "recommended_shares": recommended_shares,
        "recommended_amount": round(recommended_amount, 2),
        "risk_reward_ratio": round(b, 2),
    }


def build_portfolio_management_report(
    *,
    portfolio_id: Optional[int],
    refresh_prices: bool = False,
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    get_portfolio_fn: Callable[[int], Any] = lambda target_id: Portfolio.get_or_none(Portfolio.id == target_id),
    update_live_prices_fn: Callable[[], Any] = PositionTracker.update_live_prices,
    is_excluded_ticker_fn: Callable[[str], bool] = is_excluded_ticker,
    analyze_portfolio_fn: Callable[[int], Any] = RiskManager.analyze_portfolio,
    now_fn: Callable[[], Any] = TimeUtils.now,
    tp2_from_tp1_fn: Callable[[float], float] = tp2_from_tp1,
):
    target_id = resolve_portfolio_id_fn(portfolio_id)
    if not target_id:
        raise HTTPException(404, "No user portfolio found")

    portfolio = get_portfolio_fn(target_id)
    if not portfolio:
        raise HTTPException(404, "Portfolio not found")

    if refresh_prices:
        try:
            update_live_prices_fn()
        except Exception:
            pass

    open_positions = list(
        Position.select()
        .where((Position.status == "OPEN") & (Position.portfolio == portfolio.id))
        .order_by(Position.ticker.asc())
    )

    total_cost = 0.0
    market_value = 0.0
    total_unrealized = 0.0
    winners = 0
    losers = 0
    rows = []
    action_items = []

    for pos in open_positions:
        if is_excluded_ticker_fn(pos.ticker):
            continue
        entry = float(pos.entry_price or 0.0)
        shares = int(pos.shares or 0)
        current = float(pos.current_price if pos.current_price is not None else entry)
        sl = float(pos.stop_loss or 0.0)
        tp1 = float(pos.target_price or 0.0)
        tp2 = tp2_from_tp1_fn(tp1)

        cost = entry * shares
        value = current * shares
        pnl = value - cost
        pnl_pct = (pnl / cost * 100.0) if cost > 0 else 0.0

        total_cost += cost
        market_value += value
        total_unrealized += pnl
        if pnl > 0:
            winners += 1
        elif pnl < 0:
            losers += 1

        dist_to_sl_pct = ((current - sl) / current * 100.0) if current > 0 and sl > 0 else None
        dist_to_tp1_pct = ((tp1 - current) / current * 100.0) if current > 0 and tp1 > 0 else None

        total_cap = (float(portfolio.cash_egp or 0.0) + market_value) if (portfolio.cash_egp or market_value) else 100000.0
        kelly_sizing = calculate_kelly_position_size(
            entry_price=entry,
            stop_loss=sl,
            target_price=tp1,
            total_capital=total_cap,
        )

        action = "HOLD_MONITOR"
        priority = 3
        reason = "Within plan thresholds."
        if sl > 0 and current <= sl:
            action = "EXIT_IMMEDIATELY"
            priority = 1
            reason = "Price is at/below stop loss."
        elif tp1 > 0 and current >= tp1:
            action = "TAKE_PROFIT_REVIEW"
            priority = 1
            reason = "Price reached TP1."
        elif pnl_pct <= -float(_get_portfolio_mgmt_setting("PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT", 3.0)):
            action = "REDUCE_RISK_REVIEW"
            priority = 2
            reason = "Drawdown exceeded configured risk threshold."
        elif dist_to_tp1_pct is not None and 0 <= dist_to_tp1_pct <= float(_get_portfolio_mgmt_setting("PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT", 1.0)):
            action = "PREPARE_TP_EXECUTION"
            priority = 2
            reason = "Price is within configured TP proximity threshold."

        row = {
            "ticker": pos.ticker,
            "shares": shares,
            "entry_price": round(entry, 4),
            "current_price": round(current, 4),
            "stop_loss": round(sl, 4),
            "target_price": round(tp1, 4),
            "target_price_2": round(tp2, 4),
            "cost_basis": round(cost, 2),
            "market_value": round(value, 2),
            "unrealized_pnl": round(pnl, 2),
            "unrealized_pnl_pct": round(pnl_pct, 2),
            "distance_to_sl_pct": round(dist_to_sl_pct, 2) if dist_to_sl_pct is not None else None,
            "distance_to_tp1_pct": round(dist_to_tp1_pct, 2) if dist_to_tp1_pct is not None else None,
            "kelly_pct": kelly_sizing["kelly_pct"],
            "recommended_shares": kelly_sizing["recommended_shares"],
            "risk_reward_ratio": kelly_sizing["risk_reward_ratio"],
            "action": action,
            "action_reason": reason,
            "currency": pos.currency or "EGP",
            "sector": pos.sector,
            "notes": pos.notes,
        }
        rows.append(row)
        if action != "HOLD_MONITOR":
            action_items.append({"priority": priority, **row})

    risk = analyze_portfolio_fn(portfolio.id)
    risk_status = risk.get("status", "UNKNOWN") if isinstance(risk, dict) else "UNKNOWN"
    risk_score = risk.get("health_score", 0) if isinstance(risk, dict) else 0
    risk_heat = risk.get("heat", 0.0) if isinstance(risk, dict) else 0.0
    risk_recommendations = risk.get("recommendations", []) if isinstance(risk, dict) else []

    total_positions = len(rows)
    unrealized_pct = (total_unrealized / total_cost * 100.0) if total_cost > 0 else 0.0
    action_items = sorted(action_items, key=lambda x: (x["priority"], x["ticker"]))

    return {
        "portfolio": {
            "id": portfolio.id,
            "name": portfolio.name,
            "type": portfolio.type,
            "cash_egp": round(float(portfolio.cash_egp or 0.0), 2),
            "cash_usd": round(float(portfolio.cash_usd or 0.0), 2),
        },
        "snapshot_at": now_fn().isoformat(),
        "summary": {
            "open_positions": total_positions,
            "winners": winners,
            "losers": losers,
            "total_cost_basis": round(total_cost, 2),
            "market_value": round(market_value, 2),
            "unrealized_pnl": round(total_unrealized, 2),
            "unrealized_pnl_pct": round(unrealized_pct, 2),
            "action_items": len(action_items),
        },
        "risk": {
            "status": risk_status,
            "health_score": risk_score,
            "heat": risk_heat,
            "recommendations": risk_recommendations,
        },
        "positions": rows,
        "action_items": action_items,
    }


def format_portfolio_management_report(report: dict, include_positions: int = 15):
    p = report.get("portfolio", {})
    s = report.get("summary", {})
    risk = report.get("risk", {})
    actions = report.get("action_items", [])
    rows = report.get("positions", [])

    lines = [
        "PORTFOLIO MANAGEMENT REPORT",
        f"Portfolio: {p.get('name', 'Unknown')} (#{p.get('id', '?')})",
        f"As of: {report.get('snapshot_at', '-')}",
        "",
        "Summary",
        f"Open Positions: {s.get('open_positions', 0)} | Winners: {s.get('winners', 0)} | Losers: {s.get('losers', 0)}",
        f"Cost Basis: {s.get('total_cost_basis', 0):,.2f} | Market Value: {s.get('market_value', 0):,.2f}",
        f"Unrealized PnL: {s.get('unrealized_pnl', 0):,.2f} ({s.get('unrealized_pnl_pct', 0):.2f}%)",
        "",
        "Risk View",
        f"Status: {risk.get('status', 'UNKNOWN')} | Health Score: {risk.get('health_score', 0)} | Heat: {risk.get('heat', 0)}%",
        "",
    ]

    action_limit = max(1, int(_get_portfolio_mgmt_setting("PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT", 10)))
    risk_recommendation_limit = max(1, int(_get_portfolio_mgmt_setting("PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT", 8)))
    positions_limit = max(1, int(include_positions))

    if actions:
        lines.append("Action Items")
        for item in actions[:action_limit]:
            lines.append(
                f"- {item['ticker']}: {item['action']} | Price {item['current_price']:.4f} | "
                f"SL {item['stop_loss']:.4f} | TP1 {item['target_price']:.4f} | TP2 {item['target_price_2']:.4f}"
            )
            lines.append(f"  Reason: {item['action_reason']}")
        lines.append("")
    else:
        lines.append("Action Items: No urgent actions. Continue monitoring.")
        lines.append("")

    risk_recs = risk.get("recommendations", [])
    if risk_recs:
        lines.append("Risk Recommendations")
        for rec in risk_recs[:risk_recommendation_limit]:
            lines.append(f"- {rec.get('severity', 'INFO')} {rec.get('title', 'Recommendation')}: {rec.get('message', '')}")
        lines.append("")

    lines.append(f"Positions Snapshot (Top {positions_limit})")
    for row in rows[:positions_limit]:
        lines.append(
            f"- {row['ticker']} | Sh {row['shares']} | Entry {row['entry_price']:.4f} | "
            f"Last {row['current_price']:.4f} | SL {row['stop_loss']:.4f} | "
            f"TP1 {row['target_price']:.4f} | TP2 {row['target_price_2']:.4f} | "
            f"PnL {row['unrealized_pnl']:.2f} ({row['unrealized_pnl_pct']:.2f}%)"
        )
    if not rows:
        lines.append("- No open positions in this portfolio.")

    return "\n".join(lines)


def split_telegram_message(text: str, max_len: int = 3500):
    if len(text) <= max_len:
        return [text]
    chunks = []
    current = ""
    for line in text.split("\n"):
        candidate = f"{current}\n{line}".strip() if current else line
        if len(candidate) > max_len and current:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def intake_portfolio_holdings_command(
    req,
    *,
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    parse_holding_input_fn: Callable[[Any], dict] = parse_holding_input,
    get_trade_permission_fn: Callable[..., dict] = WalkForwardValidation.get_trade_permission,
    update_live_prices_fn: Callable[[], Any] = PositionTracker.update_live_prices,
    build_report_fn: Callable[..., dict] = build_portfolio_management_report,
    now_fn: Callable[[], Any] = TimeUtils.now,
):
    target_id = resolve_portfolio_id_fn(req.portfolio_id)
    if not target_id:
        raise HTTPException(404, "No user portfolio found")
    if not req.holdings:
        raise HTTPException(400, "Holdings list is required")

    created = 0
    updated = 0
    errors = []

    for row in req.holdings:
        try:
            parsed = parse_holding_input_fn(row)
            gate = get_trade_permission_fn(parsed["ticker"], fail_closed=True)
            if not gate.get("allowed", False):
                errors.append(f"{parsed['ticker']}: WFA gate blocked ({gate.get('reason', 'blocked')})")
                continue

            existing = Position.get_or_none(
                (Position.portfolio == target_id) &
                (Position.status == "OPEN") &
                (Position.ticker == parsed["ticker"])
            )
            if existing:
                existing.shares = parsed["shares"]
                existing.entry_price = parsed["entry_price"]
                existing.stop_loss = parsed["stop_loss"]
                existing.target_price = parsed["target_price"]
                existing.currency = parsed["currency"]
                existing.sector = parsed["sector"]
                existing.notes = parsed["notes"] or existing.notes
                if existing.current_price is None:
                    existing.current_price = parsed["entry_price"]
                existing.save()
                updated += 1
            else:
                Position.create(
                    portfolio=target_id,
                    ticker=parsed["ticker"],
                    shares=parsed["shares"],
                    entry_price=parsed["entry_price"],
                    stop_loss=parsed["stop_loss"],
                    target_price=parsed["target_price"],
                    current_price=parsed["entry_price"],
                    status="OPEN",
                    currency=parsed["currency"],
                    sector=parsed["sector"],
                    notes=parsed["notes"] or "Managed portfolio intake",
                    entry_date=now_fn(),
                )
                created += 1
        except Exception as exc:
            ticker_label = getattr(row, "ticker", "UNKNOWN")
            errors.append(f"{ticker_label}: {exc}")

    if req.refresh_prices:
        try:
            update_live_prices_fn()
        except Exception:
            pass

    report = build_report_fn(portfolio_id=target_id, refresh_prices=False)
    return {
        "status": "completed" if not errors else "partial",
        "portfolio_id": target_id,
        "created": created,
        "updated": updated,
        "errors": errors,
        "report_summary": report.get("summary", {}),
    }


def send_portfolio_management_report_command(
    *,
    report: dict,
    include_positions: int,
    chat_id: Optional[str],
    format_report_fn: Callable[[dict, int], str] = format_portfolio_management_report,
    split_message_fn: Callable[[str, int], list[str]] = split_telegram_message,
    send_message_fn: Callable[..., Any] = TelegramBot_Alerts.send_message,
):
    message = format_report_fn(report, include_positions)
    chunk_max_len = max(500, min(4096, int(_get_portfolio_mgmt_setting("PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN", 3500))))
    chunks = split_message_fn(message, max_len=chunk_max_len)

    responses = []
    sent = 0
    failed = 0
    for chunk in chunks:
        res = send_message_fn(chunk, chat_id=chat_id)
        responses.append(res)
        if res and res.get("ok"):
            sent += 1
        else:
            failed += 1

    return {
        "status": "sent" if failed == 0 else ("partial" if sent > 0 else "failed"),
        "portfolio": report.get("portfolio"),
        "summary": report.get("summary"),
        "chunks_total": len(chunks),
        "chunks_sent": sent,
        "chunks_failed": failed,
        "responses": responses,
    }


def get_portfolio_rebalancing_command(
    *,
    portfolio_id: Optional[int],
    model: str,
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    get_rebalancing_fn: Callable[..., Any] = TreasuryLedger.get_rebalancing_recommendations,
):
    target_id = resolve_portfolio_id_fn(portfolio_id)
    if not target_id:
        raise HTTPException(404, "Portfolio not found")
    return get_rebalancing_fn(portfolio_id=target_id, target_model=model)


def trigger_portfolio_snapshot_command(
    *,
    portfolio_id: Optional[int],
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    take_snapshot_fn: Callable[..., dict] = TreasuryLedger.take_snapshot,
):
    target_id = resolve_portfolio_id_fn(portfolio_id)
    if not target_id:
        raise HTTPException(404, "Portfolio not found")
    result = take_snapshot_fn(portfolio_id=target_id)
    if result.get("status") == "error":
        raise HTTPException(500, result.get("message"))
    return result


def build_sandbox_management_report(
    *,
    holdings: List[dict],
    portfolio_name: str = "Sandbox Audit",
    cash_egp: float = 0.0,
    cash_usd: float = 0.0,
    is_excluded_ticker_fn: Callable[[str], bool] = is_excluded_ticker,
    now_fn: Callable[[], Any] = TimeUtils.now,
    tp2_from_tp1_fn: Callable[[float], float] = tp2_from_tp1,
) -> dict:
    """Generate in-memory health audit & Kelly sizing report for sandbox evaluation without DB mutation."""
    total_cost = 0.0
    market_value = 0.0
    total_unrealized = 0.0
    winners = 0
    losers = 0
    rows = []
    action_items = []

    for item in holdings:
        ticker = str(item.get("ticker") or "").upper().strip()
        if not ticker or is_excluded_ticker_fn(ticker):
            continue

        shares = int(item.get("shares") or 0)
        entry = float(item.get("entry_price") or 0.0)
        current = float(item.get("current_price") or entry)
        sl = float(item.get("stop_loss") or 0.0)
        tp1 = float(item.get("target_price") or 0.0)
        tp2 = float(item.get("target_price_2") or tp2_from_tp1_fn(tp1))

        cost = entry * shares
        value = current * shares
        pnl = value - cost
        pnl_pct = (pnl / cost * 100.0) if cost > 0 else 0.0

        total_cost += cost
        market_value += value
        total_unrealized += pnl
        if pnl > 0:
            winners += 1
        elif pnl < 0:
            losers += 1

        dist_to_sl_pct = ((current - sl) / current * 100.0) if current > 0 and sl > 0 else None
        dist_to_tp1_pct = ((tp1 - current) / current * 100.0) if current > 0 and tp1 > 0 else None

        total_cap = (cash_egp + market_value) if (cash_egp or market_value) else 100000.0
        kelly_sizing = calculate_kelly_position_size(
            entry_price=entry,
            stop_loss=sl,
            target_price=tp1,
            total_capital=total_cap,
        )

        action = "HOLD_MONITOR"
        priority = 3
        reason = "Within plan thresholds."
        if sl > 0 and current <= sl:
            action = "EXIT_IMMEDIATELY"
            priority = 1
            reason = "Price is at/below stop loss."
        elif tp1 > 0 and current >= tp1:
            action = "TAKE_PROFIT_REVIEW"
            priority = 1
            reason = "Price reached TP1."
        elif pnl_pct <= -3.0:
            action = "REDUCE_RISK_REVIEW"
            priority = 2
            reason = "Drawdown exceeded configured risk threshold."
        elif dist_to_tp1_pct is not None and 0 <= dist_to_tp1_pct <= 1.0:
            action = "PREPARE_TP_EXECUTION"
            priority = 2
            reason = "Price is within configured TP proximity threshold."

        row = {
            "ticker": ticker,
            "shares": shares,
            "entry_price": round(entry, 4),
            "current_price": round(current, 4),
            "stop_loss": round(sl, 4),
            "target_price": round(tp1, 4),
            "target_price_2": round(tp2, 4),
            "cost_basis": round(cost, 2),
            "market_value": round(value, 2),
            "unrealized_pnl": round(pnl, 2),
            "unrealized_pnl_pct": round(pnl_pct, 2),
            "distance_to_sl_pct": round(dist_to_sl_pct, 2) if dist_to_sl_pct is not None else None,
            "distance_to_tp1_pct": round(dist_to_tp1_pct, 2) if dist_to_tp1_pct is not None else None,
            "kelly_pct": kelly_sizing["kelly_pct"],
            "recommended_shares": kelly_sizing["recommended_shares"],
            "risk_reward_ratio": kelly_sizing["risk_reward_ratio"],
            "action": action,
            "action_reason": reason,
            "currency": item.get("currency") or "EGP",
            "sector": item.get("sector"),
            "notes": item.get("notes"),
        }
        rows.append(row)
        if action != "HOLD_MONITOR":
            action_items.append({"priority": priority, **row})

    unrealized_pct = (total_unrealized / total_cost * 100.0) if total_cost > 0 else 0.0
    action_items = sorted(action_items, key=lambda x: (x["priority"], x["ticker"]))

    # In-memory heuristic score (0-100) based on winning ratio and stop loss integrity
    health_score = 75
    if len(rows) > 0:
        win_ratio = winners / len(rows)
        health_score = int(50 + (win_ratio * 40) - (len(action_items) * 5))
        health_score = max(10, min(95, health_score))

    heat = round((total_cost / total_cap * 100.0) if total_cap > 0 else 0.0, 2)

    return {
        "portfolio": {
            "id": None,
            "name": portfolio_name,
            "type": "SANDBOX",
            "cash_egp": round(float(cash_egp), 2),
            "cash_usd": round(float(cash_usd), 2),
        },
        "snapshot_at": now_fn().isoformat(),
        "summary": {
            "open_positions": len(rows),
            "winners": winners,
            "losers": losers,
            "total_cost_basis": round(total_cost, 2),
            "market_value": round(market_value, 2),
            "unrealized_pnl": round(total_unrealized, 2),
            "unrealized_pnl_pct": round(unrealized_pct, 2),
            "action_items": len(action_items),
        },
        "risk": {
            "status": "HEALTHY" if health_score >= 70 else "WARNING",
            "health_score": health_score,
            "heat": heat,
            "recommendations": [item["action_reason"] for item in action_items[:3]],
        },
        "positions": rows,
        "action_items": action_items,
    }


def subscriber_import_command(
    *,
    file_bytes: bytes,
    filename: str,
    portfolio_name: Optional[str] = None,
    mode: str = "create_new",  # "create_new" | "sandbox" | "overwrite"
    portfolio_id: Optional[int] = None,
    starting_cash_egp: float = 0.0,
    starting_cash_usd: float = 0.0,
    refresh_prices: bool = True,
    parse_file_fn: Callable[[bytes, str], List[dict]] = None,
    parse_holding_input_fn: Callable[[Any], dict] = parse_holding_input,
    get_trade_permission_fn: Callable[..., dict] = WalkForwardValidation.get_trade_permission,
    update_live_prices_fn: Callable[[], Any] = PositionTracker.update_live_prices,
    build_report_fn: Callable[..., dict] = build_portfolio_management_report,
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    now_fn: Callable[[], Any] = TimeUtils.now,
):
    """Execute complete subscriber onboarding intake supporting new book creation, sandbox audit, or overwrite."""
    if parse_file_fn is None:
        from core.portfolio.template_generator import parse_subscriber_intake_file
        parse_file_fn = parse_subscriber_intake_file

    parsed_holdings = parse_file_fn(file_bytes, filename)
    if not parsed_holdings:
        raise HTTPException(status_code=400, detail="No valid holding rows found in uploaded file")

    if mode == "sandbox":
        report = build_sandbox_management_report(
            holdings=parsed_holdings,
            portfolio_name=portfolio_name or "Subscriber Sandbox Audit",
            cash_egp=starting_cash_egp,
            cash_usd=starting_cash_usd,
            now_fn=now_fn,
        )
        return {
            "status": "success",
            "mode": "sandbox",
            "portfolio_id": None,
            "portfolio_name": portfolio_name or "Subscriber Sandbox Audit",
            "created": 0,
            "updated": 0,
            "errors": [],
            "report": report,
            "holdings": parsed_holdings,
        }

    # Database mutation modes
    target_id: Optional[int] = None
    target_name: str = ""

    if mode == "create_new":
        clean_name = portfolio_name.strip() if portfolio_name and portfolio_name.strip() else ""
        if not clean_name:
            stem = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip().title()
            clean_name = f"Subscriber - {stem}" if not stem.lower().startswith("subscriber") else stem
        
        new_p = Portfolio.create(name=clean_name, type="USER", auto_manage=False)
        target_id = new_p.id
        target_name = new_p.name
    else:  # "overwrite"
        target_id = resolve_portfolio_id_fn(portfolio_id)
        if not target_id:
            raise HTTPException(404, "No portfolio found to overwrite")
        p_obj = Portfolio.get_or_none(Portfolio.id == target_id)
        target_name = p_obj.name if p_obj else f"Portfolio #{target_id}"

    # Ingest positions
    created = 0
    updated = 0
    errors = []

    for item in parsed_holdings:
        try:
            parsed = parse_holding_input_fn(item)
            gate = get_trade_permission_fn(parsed["ticker"], fail_closed=True)
            if not gate.get("allowed", False):
                errors.append(f"{parsed['ticker']}: WFA gate blocked ({gate.get('reason', 'blocked')})")
                continue

            existing = Position.get_or_none(
                (Position.portfolio == target_id) &
                (Position.status == "OPEN") &
                (Position.ticker == parsed["ticker"])
            )
            if existing:
                existing.shares = parsed["shares"]
                existing.entry_price = parsed["entry_price"]
                existing.stop_loss = parsed["stop_loss"]
                existing.target_price = parsed["target_price"]
                existing.currency = parsed["currency"]
                existing.sector = parsed["sector"]
                existing.notes = parsed["notes"] or existing.notes
                if existing.current_price is None:
                    existing.current_price = parsed["entry_price"]
                existing.save()
                updated += 1
            else:
                Position.create(
                    portfolio=target_id,
                    ticker=parsed["ticker"],
                    shares=parsed["shares"],
                    entry_price=parsed["entry_price"],
                    stop_loss=parsed["stop_loss"],
                    target_price=parsed["target_price"],
                    current_price=parsed["entry_price"],
                    status="OPEN",
                    currency=parsed["currency"],
                    sector=parsed["sector"],
                    notes=parsed["notes"] or "Subscriber Intake",
                    entry_date=now_fn(),
                )
                created += 1
        except Exception as exc:
            errors.append(f"{item.get('ticker', 'UNKNOWN')}: {exc}")

    if refresh_prices:
        try:
            update_live_prices_fn()
        except Exception:
            pass

    report = build_report_fn(portfolio_id=target_id, refresh_prices=False)

    return {
        "status": "created" if mode == "create_new" else ("completed" if not errors else "partial"),
        "mode": mode,
        "portfolio_id": target_id,
        "portfolio_name": target_name,
        "created": created,
        "updated": updated,
        "errors": errors,
        "report": report,
        "holdings": parsed_holdings,
    }

