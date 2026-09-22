from __future__ import annotations

import datetime
from typing import Any, Optional

from core import TimeUtils, RiskManager
from database import (
    Client,
    Portfolio,
    Position,
    SignalRecommendation,
    SignalRun,
)

from .tiers import (
    ADVISORY_DISCLAIMER,
    SIGNALS_ONLY,
    _default_report_language,
    _json_object,
    _positive_float,
    _safe_float_setting,
    normalize_report_language,
    normalize_tier,
    subscription_plan_label,
)
from .entitlements import (
    _client_by_id,
    _portfolio_by_id,
    ensure_advisory_entitlement,
    serialize_client,
    serialize_portfolio,
    subscription_state,
)


def build_portfolio_advisory_report(client_id: int, portfolio_id: int) -> dict[str, Any]:
    client = _client_by_id(client_id)
    portfolio = _portfolio_by_id(portfolio_id)
    ensure_advisory_entitlement(client, portfolio)

    run = latest_completed_signal_run()
    recommendations = latest_recommendations(run)
    recommendations_by_ticker = {str(rec.ticker or "").upper(): rec for rec in recommendations}

    positions = list(
        Position.select()
        .where((Position.portfolio == portfolio) & (Position.status == "OPEN"))
        .order_by(Position.ticker.asc())
    )
    held_tickers = {str(position.ticker or "").upper() for position in positions}
    actions = []
    for position in positions:
        action = _classify_position_action(position, recommendations_by_ticker.get(str(position.ticker or "").upper()))
        actions.append(action)

    for rec in recommendations:
        ticker = str(rec.ticker or "").upper()
        if ticker in held_tickers:
            continue
        actions.append(_classify_new_entry(rec, portfolio))

    risk = RiskManager.analyze_portfolio(portfolio.id)
    action_items = [item for item in actions if item.get("action") not in {"NO_ACTION"}]
    report = {
        "subscriber": serialize_client(client, include_portfolios=False),
        "portfolio": serialize_portfolio(portfolio),
        "run": _serialize_run(run),
        "generated_at": TimeUtils.now().isoformat(),
        "summary": {
            "open_positions": len(positions),
            "latest_recommendations": len(recommendations),
            "action_items": len(action_items),
            "subscription_state": subscription_state(client),
            "subscription_tier": normalize_tier(client.subscription_tier),
            "risk_status": risk.get("status", "UNKNOWN") if isinstance(risk, dict) else "UNKNOWN",
            "risk_score": risk.get("health_score", 0) if isinstance(risk, dict) else 0,
            "portfolio_heat": risk.get("heat", 0.0) if isinstance(risk, dict) else 0.0,
        },
        "actions": actions,
        "risk": risk if isinstance(risk, dict) else {"status": "UNKNOWN", "recommendations": []},
        "disclaimer": ADVISORY_DISCLAIMER,
    }
    return report


def latest_completed_signal_run() -> Optional[SignalRun]:
    return (
        SignalRun.select()
        .where(SignalRun.status == "COMPLETED")
        .order_by(SignalRun.run_date.desc(), SignalRun.completed_at.desc(), SignalRun.id.desc())
        .first()
    )


def latest_recommendations(run: Optional[SignalRun]) -> list[SignalRecommendation]:
    if run is None:
        return []
    return list(
        SignalRecommendation.select()
        .where((SignalRecommendation.run == run) & (SignalRecommendation.state == "ACTIVE"))
        .order_by(SignalRecommendation.score.desc(), SignalRecommendation.confidence.desc(), SignalRecommendation.id.desc())
    )


def _format_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "-"


def _format_decimal(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{number:,.4f}".rstrip("0").rstrip(".")


def _format_price_pair(current: Any, stop: Any) -> Optional[str]:
    current_text = _format_decimal(current)
    stop_text = _format_decimal(stop)
    if current_text == "-" or stop_text == "-":
        return None
    return f"Price/SL: {current_text} / {stop_text}"


def _arabic_advisory_status_label(value: Any, default: str = "غير معروف") -> str:
    labels = {
        "DAILY": "يومي",
        "PRE CLOSE": "قبل الإغلاق",
        "PRE_CLOSE": "قبل الإغلاق",
        "HEALTHY": "صحي",
        "UNKNOWN": "غير معروف",
        "WATCH": "مراقبة",
        "BUY": "شراء",
        "SELL": "بيع",
        "HOLD": "احتفاظ",
    }
    key = str(value or "").strip().upper()
    if not key:
        return default
    return labels.get(key, labels.get(key.replace("_", " "), key.replace("_", " ")))


def _arabic_advisory_reason(reason: str) -> str:
    text = str(reason or "").strip()
    if not text:
        return ""
    known = {
        "Position weight is above the configured subscriber risk cap.": "وزن المركز أعلى من حد المخاطرة المحدد للمشترك.",
        "Current price is at or below the stored stop loss.": "السعر الحالي عند مستوى وقف الخسارة المسجل أو دونه.",
        "Current price has reached TP1 and needs profit review.": "السعر وصل إلى الهدف الأول ويحتاج مراجعة جني أرباح.",
        "Latest Horus signal still supports the open position.": "إشارة حورس الأخيرة ما زالت تدعم المركز المفتوح.",
        "No active Horus signal currently matches this open position.": "لا توجد إشارة حورس نشطة تطابق هذا المركز حالياً.",
        "Fresh Horus signal is not currently represented in the portfolio.": "توجد إشارة حورس جديدة غير ممثلة حالياً في المحفظة.",
        "Fresh Horus signal exists but cash or risk distance does not support a new position.": "توجد إشارة حورس جديدة، لكن النقد المتاح أو مسافة المخاطرة لا يدعمان فتح مركز جديد.",
        "Open position drawdown exceeded the configured review threshold without a matching fresh signal.": "تراجع المركز المفتوح تجاوز حد المراجعة المحدد دون وجود إشارة حديثة مطابقة.",
    }
    return known.get(text, text.replace("Horus", "حورس"))


def _friendly_action_label(action: str, language: Optional[str] = None) -> str:
    normalized_language = normalize_report_language(language or "EN")
    labels_en = {
        "EXIT_NOW": "Exit now",
        "TAKE_PROFIT": "Take profit review",
        "REDUCE_SIZE": "Reduce size",
        "INCREASE_SIZE": "Increase size",
        "NEW_ENTRY": "New entry",
        "HOLD_WITH_SIGNAL": "Hold with signal",
        "HOLD_NO_SIGNAL": "Hold without fresh signal",
        "NO_ACTION": "No action",
    }
    labels_ar = {
        "EXIT_NOW": "خروج الآن",
        "TAKE_PROFIT": "مراجعة جني الأرباح",
        "REDUCE_SIZE": "تقليل الحجم",
        "INCREASE_SIZE": "زيادة الحجم",
        "NEW_ENTRY": "دخول جديد",
        "HOLD_WITH_SIGNAL": "احتفاظ مع إشارة",
        "HOLD_NO_SIGNAL": "احتفاظ بدون إشارة حديثة",
        "NO_ACTION": "لا إجراء",
    }
    labels = labels_ar if normalized_language == "AR" else labels_en
    return labels.get(str(action or "NO_ACTION").upper(), str(action or "NO_ACTION").replace("_", " ").title())


def _format_advisory_action_line(item: dict[str, Any]) -> str:
    action = str(item.get("action") or "NO_ACTION").upper()
    ticker = str(item.get("ticker") or "-").upper()
    action_icons = {
        "NEW_ENTRY": "🟢",
        "EXIT_NOW": "🛑",
        "TAKE_PROFIT": "🎯",
        "REDUCE_SIZE": "⚖️",
        "INCREASE_SIZE": "📈",
        "HOLD_WITH_SIGNAL": "🔹",
        "HOLD_NO_SIGNAL": "▫️",
        "NO_ACTION": "⚪",
    }
    icon = action_icons.get(action, "•")
    pieces = [f"- {icon} {ticker}: {_friendly_action_label(action)}"]
    reason = str(item.get("reason") or "").strip()

    if action == "REDUCE_SIZE":
        target_shares = item.get("recommended_shares")
        current_shares = int(item.get("shares") or 0)
        pieces.append(f"Target holding: {_format_int(target_shares)} shares")
        try:
            reduce_by = max(0, current_shares - int(target_shares))
        except (TypeError, ValueError):
            reduce_by = 0
        if reduce_by > 0:
            pieces.append(f"Reduce by: {_format_int(reduce_by)} shares")
        if item.get("position_weight_pct") is not None and item.get("max_position_weight_pct") is not None:
            pieces.append(
                f"Weight: {_format_decimal(item.get('position_weight_pct'))}% > cap {_format_decimal(item.get('max_position_weight_pct'))}%"
            )
    elif action == "EXIT_NOW":
        pieces.append("Review for full exit")
        price_pair = _format_price_pair(item.get("current_price"), item.get("stop_loss"))
        if price_pair:
            pieces.append(price_pair)
    elif action == "TAKE_PROFIT":
        pieces.append("Review profit taking")
        if item.get("target_price") is not None:
            pieces.append(f"TP1: {_format_decimal(item.get('target_price'))}")
    elif action == "NEW_ENTRY":
        pieces.append(f"Buy up to: {_format_int(item.get('recommended_shares'))} shares")
        if item.get("estimated_cost") is not None:
            pieces.append(f"Est. cost: {_format_decimal(item.get('estimated_cost'))} EGP")
        if item.get("entry_price") is not None:
            pieces.append(f"Entry: {_format_decimal(item.get('entry_price'))}")
    elif action == "NO_ACTION" and item.get("signal_match"):
        pieces[0] = f"- {icon} {ticker}: No new entry: cash/risk rules blocked this signal"
        if item.get("entry_price") is not None:
            pieces.append(f"Signal entry: {_format_decimal(item.get('entry_price'))}")
    else:
        if item.get("signal_match"):
            pieces.append("Signal: matched")
        if item.get("recommended_shares") not in (None, 0):
            pieces.append(f"Target holding: {_format_int(item.get('recommended_shares'))} shares")

    if item.get("suggested_stop_loss") is not None:
        pieces.append(f"SL: {_format_decimal(item.get('suggested_stop_loss'))}")
    if item.get("suggested_target_price") is not None:
        pieces.append(f"TP1: {_format_decimal(item.get('suggested_target_price'))}")
    if reason and action not in {"REDUCE_SIZE", "EXIT_NOW", "NO_ACTION"}:
        pieces.append(f"Reason: {reason}")
    return " | ".join(pieces)


def _format_advisory_action_line_ar(item: dict[str, Any]) -> str:
    action = str(item.get("action") or "NO_ACTION").upper()
    ticker = str(item.get("ticker") or "-").upper()
    action_icons = {
        "NEW_ENTRY": "🟢",
        "EXIT_NOW": "🛑",
        "TAKE_PROFIT": "🎯",
        "REDUCE_SIZE": "⚖️",
        "INCREASE_SIZE": "📈",
        "HOLD_WITH_SIGNAL": "🔹",
        "HOLD_NO_SIGNAL": "▫️",
        "NO_ACTION": "⚪",
    }
    icon = action_icons.get(action, "•")
    pieces = [f"- {icon} {ticker}: {_friendly_action_label(action, 'AR')}"]
    reason = _arabic_advisory_reason(str(item.get("reason") or "").strip())

    if action == "REDUCE_SIZE":
        target_shares = item.get("recommended_shares")
        current_shares = int(item.get("shares") or 0)
        pieces.append(f"الاحتفاظ المستهدف: {_format_int(target_shares)} سهم")
        try:
            reduce_by = max(0, current_shares - int(target_shares))
        except (TypeError, ValueError):
            reduce_by = 0
        if reduce_by > 0:
            pieces.append(f"تقليل بمقدار: {_format_int(reduce_by)} سهم")
        if item.get("position_weight_pct") is not None and item.get("max_position_weight_pct") is not None:
            pieces.append(
                f"الوزن: {_format_decimal(item.get('position_weight_pct'))}% > الحد {_format_decimal(item.get('max_position_weight_pct'))}%"
            )
    elif action == "EXIT_NOW":
        pieces.append("راجع الخروج الكامل")
        price_pair = _format_price_pair(item.get("current_price"), item.get("stop_loss"))
        if price_pair:
            pieces.append(price_pair.replace("Price/SL:", "السعر/وقف الخسارة:"))
    elif action == "TAKE_PROFIT":
        pieces.append("راجع جني الأرباح")
        if item.get("target_price") is not None:
            pieces.append(f"هدف 1: {_format_decimal(item.get('target_price'))}")
    elif action == "NEW_ENTRY":
        pieces.append(f"شراء حتى: {_format_int(item.get('recommended_shares'))} سهم")
        if item.get("estimated_cost") is not None:
            pieces.append(f"التكلفة التقديرية: {_format_decimal(item.get('estimated_cost'))} جنيه")
        if item.get("entry_price") is not None:
            pieces.append(f"الدخول: {_format_decimal(item.get('entry_price'))}")
    elif action == "NO_ACTION" and item.get("signal_match"):
        pieces[0] = f"- {icon} {ticker}: لا دخول جديد: قواعد النقد/المخاطر منعت الإشارة"
        if item.get("entry_price") is not None:
            pieces.append(f"دخول الإشارة: {_format_decimal(item.get('entry_price'))}")
    else:
        if item.get("signal_match"):
            pieces.append("الإشارة: مطابقة")
        if item.get("recommended_shares") not in (None, 0):
            pieces.append(f"الاحتفاظ المستهدف: {_format_int(item.get('recommended_shares'))} سهم")

    if item.get("suggested_stop_loss") is not None:
        pieces.append(f"وقف الخسارة: {_format_decimal(item.get('suggested_stop_loss'))}")
    if item.get("suggested_target_price") is not None:
        pieces.append(f"هدف 1: {_format_decimal(item.get('suggested_target_price'))}")
    if reason and action not in {"REDUCE_SIZE", "EXIT_NOW", "NO_ACTION"}:
        pieces.append(f"السبب: {reason}")
    return " | ".join(pieces)


def format_advisory_report_for_telegram(
    report: dict[str, Any],
    *,
    max_actions: int = 12,
    language: Optional[str] = None,
) -> str:
    normalized_language = normalize_report_language(
        language or (report.get("subscriber") or {}).get("report_language") or _default_report_language()
    )
    subscriber = report.get("subscriber") or {}
    portfolio = report.get("portfolio") or {}
    summary = report.get("summary") or {}
    run = report.get("run") or {}
    if normalized_language == "AR":
        lines = [
            "تقرير حورس الاستشاري للمحفظة",
            f"المشترك: {subscriber.get('name', 'غير معروف')} [{subscription_plan_label(subscriber.get('subscription_tier', SIGNALS_ONLY), 'AR')}]",
            f"المحفظة: {portfolio.get('name', 'غير معروف')} (#{portfolio.get('id', '?')})",
            f"تشغيل الإشارات: {_arabic_advisory_status_label(run.get('scan_type'), 'غير متاح')} {run.get('run_date', 'غير متاح')}",
            f"تم الإنشاء: {report.get('generated_at', '-')}",
            "",
            "الملخص",
            f"المراكز المفتوحة: {summary.get('open_positions', 0)} | التوصيات: {summary.get('latest_recommendations', 0)}",
            f"الإجراءات: {summary.get('action_items', 0)} | المخاطر: {_arabic_advisory_status_label(summary.get('risk_status'), 'غير معروف')} ({summary.get('risk_score', 0)})",
            "",
            "الإجراءات ذات الأولوية",
        ]
        actions = report.get("actions") or []
        if not actions:
            lines.append("- لا إجراء: لا توجد مراكز مرتبطة أو توصيات إشارة حالية.")
        for item in actions[:max_actions]:
            lines.append(_format_advisory_action_line_ar(item))
        if len(actions) > max_actions:
            lines.append(f"- تم إخفاء {len(actions) - max_actions} إجراء إضافي من معاينة تيليجرام.")
        lines.extend(["", "تأكيد الأسعار الحية قبل اتخاذ القرار. للاستشارة فقط. حورس لا ينفذ الصفقات تلقائياً."])
        return "\n".join(lines)

    lines = [
        "HORUS PORTFOLIO ADVISORY REPORT",
        f"Subscriber: {subscriber.get('name', 'Unknown')} [{subscriber.get('subscription_tier', '-')}]",
        f"Portfolio: {portfolio.get('name', 'Unknown')} (#{portfolio.get('id', '?')})",
        f"Signal Run: {run.get('scan_type', 'N/A')} {run.get('run_date', 'N/A')}",
        f"Generated: {report.get('generated_at', '-')}",
        "",
        "Summary",
        f"Open Positions: {summary.get('open_positions', 0)} | Recommendations: {summary.get('latest_recommendations', 0)}",
        f"Action Items: {summary.get('action_items', 0)} | Risk: {summary.get('risk_status', 'UNKNOWN')} ({summary.get('risk_score', 0)})",
        "",
        "Priority Actions",
    ]
    actions = report.get("actions") or []
    if not actions:
        lines.append("- NO_ACTION: No linked positions or current signal recommendations.")
    for item in actions[:max_actions]:
        lines.append(_format_advisory_action_line(item))
    if len(actions) > max_actions:
        lines.append(f"- {len(actions) - max_actions} additional action(s) hidden from Telegram preview.")
    lines.extend(["", "Confirm live prices before acting. " + ADVISORY_DISCLAIMER])
    return "\n".join(lines)


def _classify_position_action(position: Position, rec: Optional[SignalRecommendation]) -> dict[str, Any]:
    ticker = str(position.ticker or "").upper()
    current = _positive_float(position.current_price, _positive_float(position.entry_price, 0.0))
    entry = _positive_float(position.entry_price, 0.0)
    stop = _positive_float(position.stop_loss, 0.0)
    target = _positive_float(position.target_price, 0.0)
    shares = int(position.shares or 0)

    base = {
        "ticker": ticker,
        "shares": shares,
        "current_price": round(current, 4),
        "entry_price": round(entry, 4),
        "stop_loss": round(stop, 4),
        "target_price": round(target, 4),
        "signal_match": rec is not None,
        "recommended_shares": None,
    }
    if stop > 0 and current <= stop:
        return {
            **base,
            "action": "EXIT_NOW",
            "priority": 1,
            "reason": "Current price is at or below the stored stop loss.",
        }
    if target > 0 and current >= target:
        return {
            **base,
            "action": "TAKE_PROFIT",
            "priority": 1,
            "reason": "Current price has reached TP1 and needs profit review.",
        }
    overweight = _overweight_position_review(position, current)
    if overweight:
        return {
            **base,
            **overweight,
            "action": "REDUCE_SIZE",
            "priority": 2,
            "reason": "Position weight is above the configured subscriber risk cap.",
        }
    if rec is not None:
        suggested_stop = max(stop, float(rec.stop_loss or 0.0))
        suggested_target = _positive_float(rec.target_price, 0.0)
        recommended_updates = []
        if suggested_stop > stop:
            recommended_updates.append("RAISE_STOP")
        if suggested_target > 0 and target > 0 and abs(suggested_target - target) / target > 0.005:
            recommended_updates.append("UPDATE_TP")
        return {
            **base,
            "action": "HOLD_WITH_SIGNAL",
            "priority": 2,
            "reason": "Latest Horus signal still supports the open position.",
            "signal_id": rec.id,
            "score": float(rec.score or 0.0),
            "confidence": float(rec.confidence or 0.0),
            "recommended_updates": recommended_updates,
            "suggested_stop_loss": round(suggested_stop, 4) if suggested_stop > 0 else None,
            "suggested_target_price": round(suggested_target, 4) if suggested_target > 0 else None,
            "suggested_target_price_2": _rec_tp2(rec),
        }
    pnl_pct = ((current - entry) / entry * 100.0) if entry > 0 else 0.0
    if pnl_pct <= -_safe_float_setting("PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT", 3.0):
        return {
            **base,
            "action": "REDUCE_SIZE",
            "priority": 2,
            "reason": "Open position drawdown exceeded the configured review threshold without a matching fresh signal.",
        }
    return {
        **base,
        "action": "HOLD_NO_SIGNAL",
        "priority": 3,
        "reason": "No active Horus signal currently matches this open position.",
    }


def _classify_new_entry(rec: SignalRecommendation, portfolio: Portfolio) -> dict[str, Any]:
    shares = _recommended_shares_for_signal(rec, portfolio)
    action = "NEW_ENTRY" if shares > 0 else "NO_ACTION"
    reason = (
        "Fresh Horus signal is not currently represented in the portfolio."
        if shares > 0
        else "Fresh Horus signal exists but cash or risk distance does not support a new position."
    )
    return {
        "ticker": str(rec.ticker or "").upper(),
        "action": action,
        "priority": 2 if shares > 0 else 4,
        "reason": reason,
        "signal_match": True,
        "signal_id": rec.id,
        "side": rec.side,
        "entry_price": round(float(rec.entry_price or 0.0), 4),
        "stop_loss": round(float(rec.stop_loss or 0.0), 4),
        "target_price": round(float(rec.target_price or 0.0), 4),
        "target_price_2": _rec_tp2(rec),
        "score": float(rec.score or 0.0),
        "confidence": float(rec.confidence or 0.0),
        "recommended_shares": shares,
        "estimated_cost": round(shares * float(rec.entry_price or 0.0), 2),
    }


def _recommended_shares_for_signal(rec: SignalRecommendation, portfolio: Portfolio) -> int:
    entry = _positive_float(rec.entry_price, 0.0)
    stop = _positive_float(rec.stop_loss, 0.0)
    if entry <= 0 or stop <= 0 or entry <= stop:
        return 0
    cash = max(0.0, float(portfolio.cash_egp or 0.0))
    reserve_pct = max(0.0, min(_safe_float_setting("SUBSCRIPTION_CASH_RESERVE_PCT", 10.0), 95.0))
    available_cash = cash * (1.0 - reserve_pct / 100.0)
    if available_cash <= 0:
        return 0
    risk_pct = max(0.1, _safe_float_setting("RISK_PER_TRADE", 2.0))
    max_position_pct = max(1.0, min(_safe_float_setting("SUBSCRIPTION_MAX_POSITION_WEIGHT_PCT", 20.0), 100.0))
    equity = cash + _portfolio_market_value(portfolio)
    risk_amount = equity * (risk_pct / 100.0)
    max_cost = equity * (max_position_pct / 100.0)
    risk_per_share = entry - stop
    shares_by_risk = int(risk_amount / risk_per_share)
    shares_by_cash = int(min(available_cash, max_cost) / entry)
    return max(0, min(shares_by_risk, shares_by_cash))


def _overweight_position_review(position: Position, current: float) -> Optional[dict[str, Any]]:
    portfolio = getattr(position, "portfolio", None)
    if not portfolio or current <= 0:
        return None
    shares = int(position.shares or 0)
    if shares <= 0:
        return None
    equity = float(portfolio.cash_egp or 0.0) + _portfolio_market_value(portfolio)
    if equity <= 0:
        return None
    max_position_pct = max(1.0, min(_safe_float_setting("SUBSCRIPTION_MAX_POSITION_WEIGHT_PCT", 20.0), 100.0))
    position_value = shares * current
    weight_pct = position_value / equity * 100.0
    if weight_pct <= max_position_pct:
        return None
    target_value = equity * (max_position_pct / 100.0)
    recommended_shares = max(0, int(target_value / current))
    return {
        "position_weight_pct": round(weight_pct, 2),
        "max_position_weight_pct": round(max_position_pct, 2),
        "recommended_shares": recommended_shares,
    }


def _portfolio_market_value(portfolio: Portfolio) -> float:
    total = 0.0
    for position in Position.select().where((Position.portfolio == portfolio) & (Position.status == "OPEN")):
        current = _positive_float(position.current_price, _positive_float(position.entry_price, 0.0))
        total += current * int(position.shares or 0)
    return total


def _serialize_run(run: Optional[SignalRun]) -> Optional[dict[str, Any]]:
    if run is None:
        return None
    return {
        "id": run.id,
        "run_date": run.run_date.isoformat() if run.run_date else None,
        "scan_type": run.scan_type,
        "status": run.status,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "signals_count": int(run.signals_count or 0),
    }


def _rec_tp2(rec: SignalRecommendation) -> Optional[float]:
    try:
        payload = _json_object(rec.rationale_json)
        for key in ("target_price_2", "Target_Price_2", "tp2"):
            if payload.get(key) is not None:
                return round(float(payload[key]), 4)
    except Exception:
        pass
    target = _positive_float(rec.target_price, 0.0)
    if target <= 0:
        return None
    pct = _safe_float_setting("PORTFOLIO_MGMT_TP2_PCT", 4.0)
    return round(target * (1.0 + max(0.0, pct) / 100.0), 4)
