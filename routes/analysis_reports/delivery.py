from __future__ import annotations

from typing import Any

from .periods import _coerce_float


def _sanitize_telegram_text(value: Any) -> str:
    text = str(value or "")
    for ch in ("`", "*", "_", "[", "]"):
        text = text.replace(ch, "")
    return " ".join(text.split()).strip()


def _normalize_report_language(language: object = None) -> str:
    normalized = str(language or "EN").strip().upper() or "EN"
    return normalized if normalized in {"EN", "AR"} else "EN"


_AR_ANALYSIS_STATUS_LABELS = {
    "BULLISH": "صاعد",
    "BEARISH": "هابط",
    "CAUTIOUS": "حذر",
    "NEUTRAL": "محايد",
    "FULL BULL": "صعود قوي",
    "HEALTHY UPTREND": "اتجاه صاعد صحي",
}


def _arabic_analysis_status(value: Any, default: str = "محايد") -> str:
    key = _sanitize_telegram_text(value or "").replace("_", " ").upper()
    if not key:
        return default
    return _AR_ANALYSIS_STATUS_LABELS.get(key, key)


def _arabicize_analysis_text(value: Any) -> str:
    text = _sanitize_telegram_text(value)
    if not text:
        return text
    replacements = {
        "limited benchmark history; volatility estimate unavailable.": "تاريخ المؤشر محدود؛ لا يمكن تقدير التذبذب بدقة.",
        "period is not fully complete; report reflects an in-progress window": "الفترة لم تكتمل بعد؛ يعرض التقرير نافذة قيد التنفيذ.",
        "Selected period is incomplete; interpretation should be conservative.": "الفترة المحددة غير مكتملة؛ يجب قراءة النتائج بتحفظ.",
        "Benchmark context is unavailable; report confidence is reduced.": "سياق المؤشر غير متاح؛ ثقة التقرير أقل من المعتاد.",
        "Freshness gate reports stale inputs; confidence should be reduced.": "بوابة حداثة البيانات تشير إلى مدخلات قديمة؛ يجب خفض الثقة في القراءة.",
        "Daily replay coverage is incomplete for this period": "تغطية إعادة تشغيل الإشارات اليومية غير مكتملة لهذه الفترة",
    }
    translated = text.replace("Horus", "حورس")
    for source, target in replacements.items():
        translated = translated.replace(source, target)
    for source, target in _AR_ANALYSIS_STATUS_LABELS.items():
        translated = translated.replace(source, target)
    return translated


def build_analysis_report_telegram_message(report_payload: dict[str, Any], *, language: str = "EN") -> str:
    normalized_language = _normalize_report_language(language)
    period_type = _sanitize_telegram_text(report_payload.get("period_type", "WEEKLY")).upper()
    period_start = _sanitize_telegram_text(report_payload.get("period_start", "N/A"))
    period_end = _sanitize_telegram_text(report_payload.get("period_end", "N/A"))
    market = report_payload.get("market_summary") or {}
    review = report_payload.get("signal_review") or {}
    warnings = list(report_payload.get("warnings") or [])[:3]
    notes = list(report_payload.get("notes") or [])[:2]

    if normalized_language == "AR":
        period_label = "الأسبوعي" if period_type == "WEEKLY" else "الشهري"
        lines = [
            f"*تقرير حورس التحليلي {period_label}*",
            f"`{period_start} -> {period_end}`",
            "",
            "*ملخص السوق*",
            f"- النظام: `{_arabic_analysis_status(market.get('regime_start', 'NEUTRAL'))}` -> `{_arabic_analysis_status(market.get('regime_end', 'NEUTRAL'))}`",
            f"- العائد: `{_coerce_float(market.get('period_return_pct'), 0.0):.2f}%`",
            f"- تغير الاتساع: `{_coerce_float(market.get('breadth_change_pct'), 0.0):.2f}pp`",
            f"- التذبذب: {_arabicize_analysis_text(market.get('volatility_context', 'غير متاح'))}",
            "",
            "*مراجعة الإشارات*",
            f"- التشغيلات: `{int(review.get('run_count', 0))}` | الإشارات: `{int(review.get('signals_generated', 0))}`",
            (
                f"- النتائج (مغلقة/مفتوحة/بدون تداول): `{int(review.get('closed_outcomes', 0))}`"
                f"/`{int(review.get('open_outcomes', 0))}`/`{int(review.get('no_trade_outcomes', 0))}`"
            ),
            f"- معدل الفوز: `{_coerce_float(review.get('win_rate_pct'), 0.0):.2f}%`",
            f"- متوسط الربح/الخسارة: `{_coerce_float(review.get('avg_pnl_pct'), 0.0):.2f}%`",
            f"- التوقع: `{_coerce_float(review.get('expectancy_pct'), 0.0):.2f}%`",
        ]
        best = review.get("best_tickers") or []
        worst = review.get("worst_tickers") or []
        if best:
            top = best[0]
            lines.append(
                f"- أفضل سهم: `{_sanitize_telegram_text(top.get('ticker', 'N/A')).upper()}` "
                f"({_coerce_float(top.get('avg_pnl_pct'), 0.0):.2f}%)"
            )
        if worst:
            weak = worst[0]
            lines.append(
                f"- أضعف سهم: `{_sanitize_telegram_text(weak.get('ticker', 'N/A')).upper()}` "
                f"({_coerce_float(weak.get('avg_pnl_pct'), 0.0):.2f}%)"
            )
        if warnings:
            lines.append("")
            lines.append("*تحذيرات*")
            for item in warnings:
                lines.append(f"- {_arabicize_analysis_text(item)}")
        if notes:
            lines.append("")
            lines.append("*ملاحظات*")
            for item in notes:
                lines.append(f"- {_arabicize_analysis_text(item)}")
        message = "\n".join(lines).strip()
        if len(message) > 3900:
            message = f"{message[:3890]}\n..."
        return message

    lines = [
        f"*HORUS {period_type} ANALYSIS REPORT*",
        f"`{period_start} -> {period_end}`",
        "",
        "*Market Summary*",
        f"- Regime: `{_sanitize_telegram_text(market.get('regime_start', 'NEUTRAL'))}` -> `{_sanitize_telegram_text(market.get('regime_end', 'NEUTRAL'))}`",
        f"- Return: `{_coerce_float(market.get('period_return_pct'), 0.0):.2f}%`",
        f"- Breadth change: `{_coerce_float(market.get('breadth_change_pct'), 0.0):.2f}pp`",
        f"- Volatility: {_sanitize_telegram_text(market.get('volatility_context', 'N/A'))}",
        "",
        "*Signal Review*",
        f"- Runs: `{int(review.get('run_count', 0))}` | Signals: `{int(review.get('signals_generated', 0))}`",
        (
            f"- Outcomes (Closed/Open/NoTrade): `{int(review.get('closed_outcomes', 0))}`"
            f"/`{int(review.get('open_outcomes', 0))}`/`{int(review.get('no_trade_outcomes', 0))}`"
        ),
        f"- Win rate: `{_coerce_float(review.get('win_rate_pct'), 0.0):.2f}%`",
        f"- Avg PnL: `{_coerce_float(review.get('avg_pnl_pct'), 0.0):.2f}%`",
        f"- Expectancy: `{_coerce_float(review.get('expectancy_pct'), 0.0):.2f}%`",
    ]
    if str(review.get("review_source") or "").upper() == "PUBLISHED_LIFECYCLE":
        lines.extend(
            [
                f"- Published: `{int(review.get('published_signals', 0))}` | Fill rate: `{_coerce_float(review.get('fill_rate_pct'), 0.0):.2f}%`",
                f"- TP1 hit: `{_coerce_float(review.get('tp1_hit_rate_pct'), 0.0):.2f}%` | Full wins: `{_coerce_float(review.get('full_win_rate_pct'), 0.0):.2f}%`",
                f"- Stops: `{_coerce_float(review.get('stop_loss_rate_pct'), 0.0):.2f}%` | Expiry: `{_coerce_float(review.get('expiry_rate_pct'), 0.0):.2f}%`",
                f"- Follow-ups sent/fail: `{_coerce_float(review.get('followup_sent_rate_pct'), 0.0):.2f}%`/`{_coerce_float(review.get('followup_failure_rate_pct'), 0.0):.2f}%`",
            ]
        )

    best = review.get("best_tickers") or []
    worst = review.get("worst_tickers") or []
    if best:
        top = best[0]
        lines.append(
            f"- Top ticker: `{_sanitize_telegram_text(top.get('ticker', 'N/A')).upper()}` "
            f"({_coerce_float(top.get('avg_pnl_pct'), 0.0):.2f}%)"
        )
    if worst:
        weak = worst[0]
        lines.append(
            f"- Weak ticker: `{_sanitize_telegram_text(weak.get('ticker', 'N/A')).upper()}` "
            f"({_coerce_float(weak.get('avg_pnl_pct'), 0.0):.2f}%)"
        )

    if warnings:
        lines.append("")
        lines.append("*Warnings*")
        for item in warnings:
            lines.append(f"- {_sanitize_telegram_text(item)}")

    if notes:
        lines.append("")
        lines.append("*Notes*")
        for item in notes:
            lines.append(f"- {_sanitize_telegram_text(item)}")

    message = "\n".join(lines).strip()
    if len(message) > 3900:
        message = f"{message[:3890]}\n..."
    return message
