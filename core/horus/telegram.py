import json
from typing import Optional

from database import HorusExecution, Portfolio, SignalRecommendation, Trade


def recommendation_target2(rec: SignalRecommendation) -> Optional[float]:
    if rec and rec.rationale_json:
        try:
            payload = json.loads(rec.rationale_json)
            raw_tp2 = payload.get("target_price_2")
            if raw_tp2 is not None:
                return float(raw_tp2)
        except Exception:
            pass
    if rec and rec.target_price:
        return float(rec.target_price) * 1.04
    return None


def build_open_message(portfolio: Portfolio, rec: SignalRecommendation, shares: int, execution: HorusExecution) -> str:
    tp2 = recommendation_target2(rec)
    details = json.loads(execution.details_json or "{}")
    gap_note = ""
    planned_p = float(execution.planned_entry_price or rec.entry_price or 0.0)
    actual_p = float(execution.actual_entry_price or rec.entry_price or 0.0)
    sl = float(rec.stop_loss or 0.0)
    tp1 = float(rec.target_price or 0.0)
    tp2_val = float(tp2 or 0.0)

    tp1_pct = ((tp1 - actual_p) / actual_p * 100) if actual_p > 0 and tp1 > 0 else 0.0
    tp2_pct = ((tp2_val - actual_p) / actual_p * 100) if actual_p > 0 and tp2_val > 0 else 0.0
    sl_pct = ((actual_p - sl) / actual_p * 100) if actual_p > 0 and sl > 0 else 0.0
    risk = actual_p - sl
    reward = tp1 - actual_p
    rr_ratio = (reward / risk) if risk > 0 and reward > 0 else 0.0
    rr_str = f"1 : {rr_ratio:.1f}" if rr_ratio > 0 else "N/A"

    if details.get("gap_adjusted"):
        gap_note = f"\n⚠️ Note: market opened with a gap, entry adjusted from {planned_p:.2f} LE"
    return (
        f"🟢 *HORUS POSITION OPEN*\n"
        f"HORUS OPEN\n"
        f"Workspace: {portfolio.name}\n"
        f"Ticker: *{rec.ticker}*\n"
        f"• Entry: *{actual_p:.2f} LE*\n"
        f"• Stop Loss: *{sl:.2f} LE* (-{sl_pct:.1f}%)\n"
        f"• Target 1: *{tp1:.2f} LE* (+{tp1_pct:.1f}%)\n"
        + (f"• Target 2: *{tp2_val:.2f} LE* (+{tp2_pct:.1f}%)\n" if tp2_val > 0 else "")
        + f"• Risk/Reward: *{rr_str}*\n"
        f"• Shares: {int(shares):,}"
        f"{gap_note}"
    )


def build_update_message(portfolio: Portfolio, rec: SignalRecommendation, execution: HorusExecution) -> str:
    details = json.loads(execution.details_json or "{}")
    previous = details.get("previous", {})
    return (
        f"🔄 *HORUS POSITION UPDATE*\n"
        f"HORUS UPDATE\n"
        f"Workspace: {portfolio.name}\n"
        f"Ticker: *{rec.ticker}*\n"
        f"• Stop Loss: {float(previous.get('stop_loss', 0.0)):.2f} -> *{float(rec.stop_loss):.2f} LE*\n"
        f"• Target 1: {float(previous.get('target_price', 0.0)):.2f} -> *{float(rec.target_price):.2f} LE*"
    )


def build_skip_message(portfolio: Portfolio, rec: SignalRecommendation, execution: HorusExecution) -> str:
    details = json.loads(execution.details_json or "{}")
    reason = str(details.get("reason") or "skipped").replace("_", " ")
    return (
        f"⚠️ *HORUS EXECUTION SKIPPED*\n"
        f"HORUS SKIP\n"
        f"Workspace: {portfolio.name}\n"
        f"Ticker: *{rec.ticker}*\n"
        f"• Reason: {reason}\n"
        f"• Signal Entry: {float(execution.planned_entry_price or rec.entry_price):.2f} LE\n"
        f"• Open Price: {float(execution.actual_entry_price or 0.0):.2f} LE"
    )


def build_close_message(portfolio: Portfolio, execution: HorusExecution, trade: Optional[Trade]) -> str:
    entry_price = float(execution.actual_entry_price or execution.planned_entry_price or 0.0)
    exit_price = float(trade.exit_price) if trade and trade.exit_price is not None else float(execution.active_stop_loss or execution.active_target_price or 0.0)
    pnl_pct = float(trade.pnl_pct) if trade and trade.pnl_pct is not None else 0.0
    pnl_sign = "🟢" if pnl_pct >= 0 else "🔴"
    return (
        f"{pnl_sign} *HORUS POSITION CLOSED*\n"
        f"HORUS CLOSE\n"
        f"Workspace: {portfolio.name}\n"
        f"Ticker: *{execution.ticker}*\n"
        f"• Reason: {str(execution.close_reason or 'CLOSED').replace('_', ' ').title()}\n"
        f"• Entry: *{entry_price:.2f} LE*\n"
        f"• Exit: *{exit_price:.2f} LE*\n"
        f"• PnL Return: *{pnl_pct:+.2f}%*"
    )
