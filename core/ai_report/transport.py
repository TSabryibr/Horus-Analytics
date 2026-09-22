from __future__ import annotations

import logging
import re
from typing import Any

from core import TimeUtils

from .boundary import dedupe_recommendations, dedupe_strings

logger = logging.getLogger("horus.ai_report.transport")


def _sanitize_telegram_text(value: object) -> str:
    text = str(value or "")
    for ch in ("`", "*", "_", "[", "]"):
        text = text.replace(ch, "")
    return " ".join(text.split()).strip()


def _format_status_label(value: object, default: str) -> str:
    text = str(value or default).replace("_", " ")
    return _sanitize_telegram_text(text).upper() or default


def _normalize_report_language(language: object = None) -> str:
    normalized = str(language or "EN").strip().upper() or "EN"
    return normalized if normalized in {"EN", "AR"} else "EN"


_ARABIC_STATUS_LABELS = {
    "AGGRESSIVE": "هجومي",
    "ALLOW": "مسموح",
    "BALANCED": "متوازن",
    "BEARISH": "هابط",
    "BLOCK EXECUTION": "إيقاف التنفيذ",
    "BULLISH": "صاعد",
    "CAPITAL PRESERVATION": "حفظ رأس المال",
    "CAUTIOUS": "حذر",
    "DEFENSIVE": "دفاعي",
    "FULL BULL": "صعود قوي",
    "HEALTHY DOWNTREND": "اتجاه هابط منظم",
    "HEALTHY UPTREND": "اتجاه صاعد صحي",
    "HIGH": "مرتفع",
    "HOLD": "احتفاظ",
    "LOW": "منخفض",
    "MEDIUM": "متوسط",
    "NEUTRAL": "محايد",
    "NORMAL": "طبيعي",
    "RISK OFF": "خفض المخاطر",
    "SELL": "بيع",
    "STRONGLY BULLISH": "صاعد بقوة",
    "TREND FOLLOWING": "متابعة الاتجاه",
    "TRENDFOLLOWING": "متابعة الاتجاه",
    "VERY HIGH": "مرتفع جداً",
    "WATCH": "مراقبة",
    "WATCH ONLY": "مراقبة فقط",
}

_ARABIC_ACTION_LABELS = {
    "BUY": "شراء",
    "SELL": "بيع",
    "HOLD": "احتفاظ",
    "WATCH": "مراقبة",
    "CASH": "سيولة",
}

_ARABIC_PHRASE_REPLACEMENTS = (
    ("Horus Analytics - EGX", "حورس للتحليلات - البورصة المصرية"),
    ("Portfolio 'Horus'", "محفظة حورس"),
    ("risk/reward", "العائد إلى المخاطرة"),
    ("risk reward", "العائد إلى المخاطرة"),
    ("risk cap", "حد المخاطرة"),
    ("Risk Cap", "حد المخاطرة"),
    ("per trade", "لكل صفقة"),
    ("Selectivity", "انتقائية الفرص"),
    ("Entry", "الدخول"),
    ("Above", "أعلى من"),
    ("Trap break", "كسر مصيدة"),
    ("Breakout low", "قاع الاختراق"),
    ("R:R", "عائد/مخاطرة"),
    ("Horus", "حورس"),
)


def _format_arabic_status_label(value: object, default: str) -> str:
    key = _format_status_label(value, default)
    if key in _ARABIC_STATUS_LABELS:
        return _ARABIC_STATUS_LABELS[key]
    return _arabicize_report_text(key) or _ARABIC_STATUS_LABELS.get(default, default)


def _format_arabic_action_label(value: object, default: str = "WATCH") -> str:
    key = _format_status_label(value, default)
    return _ARABIC_ACTION_LABELS.get(key, _format_arabic_status_label(key, default))


def _regex_value(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _arabic_symbol_list(value: object) -> str:
    text = _sanitize_telegram_text(value)
    text = re.sub(r"\s+and\s+", " و", text, flags=re.IGNORECASE)
    return text.replace(", ", "، ").strip(" .")


def _apply_arabic_phrase_replacements(text: str) -> str:
    translated = text
    for source, target in sorted(_ARABIC_PHRASE_REPLACEMENTS, key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(re.escape(source), target, translated, flags=re.IGNORECASE)
    return translated


def _arabicize_report_text(value: object) -> str:
    text = _sanitize_telegram_text(value)
    if not text:
        return ""
    normalized = text.upper()

    if normalized.startswith("MARKET STRUCTURE:"):
        regime = _format_arabic_status_label(_regex_value(r"Regime is ([^,(.;|]+)", text) or "NEUTRAL", "NEUTRAL")
        macro = _format_arabic_status_label(_regex_value(r"Macro is ([^,(.;|]+)", text) or "NEUTRAL", "NEUTRAL")
        volatility = _format_arabic_status_label(_regex_value(r"Volatility is ([^,(.;|]+)", text) or "NORMAL", "NORMAL")
        score = _regex_value(r"Score:\s*([0-9.]+)", text)
        parts = [f"حالة السوق: {regime}"]
        if score:
            parts.append(f"درجة النظام: {score}")
        parts.extend([f"الاتجاه العام: {macro}", f"التذبذب: {volatility}"])
        return "هيكل السوق: " + "، ".join(parts) + "."

    if normalized.startswith("EXECUTION PROFILE:"):
        raw_mode = _regex_value(r"EXECUTION PROFILE:\s*([^|.;]+)", text)
        mode = _format_arabic_status_label(raw_mode or "BALANCED", "BALANCED")
        selectivity_raw = _regex_value(r"Selectivity:\s*([^|.;]+)", text)
        selectivity = _format_arabic_status_label(selectivity_raw or "MEDIUM", "MEDIUM")
        risk_cap = _regex_value(r"Risk Cap:\s*([0-9.]+%?)", text)
        pieces = [mode, f"انتقائية الفرص: {selectivity}"]
        if risk_cap:
            pieces.append(f"حد المخاطرة: {risk_cap.strip()} لكل صفقة")
        return "ملف التنفيذ: " + "، ".join(pieces) + "."

    if normalized.startswith("WHALE FLOW:"):
        accumulation = _regex_value(r"([0-9.]+%)\s+accumulation rate", text)
        targets = _regex_value(r"top institutional targets\s+(.+?)(?:\.|$)", text)
        pieces = []
        if accumulation:
            pieces.append(f"معدل التجميع: {accumulation}")
        if targets:
            pieces.append(f"أبرز الأهداف المؤسسية: {_arabic_symbol_list(targets)}")
        return "تدفقات المؤسسات: " + "، ".join(pieces) + "." if pieces else "تدفقات المؤسسات: لا توجد قراءة كافية."

    if normalized.startswith("SQUEEZE ALERT:"):
        names = _regex_value(r"SQUEEZE ALERT:\s*(.+?)\s+coiling", text)
        bandwidth = _regex_value(r"bandwidths\s*([<>=\s0-9.]+)", text)
        name_text = _arabic_symbol_list(names) if names else "بعض الأسهم"
        if bandwidth:
            return f"تنبيه ضغط سعري: {name_text} في نطاق ضيق؛ نطاقات التذبذب {bandwidth.strip()}، ما يرجح حركة قوية قريبة."
        return f"تنبيه ضغط سعري: {name_text} في نطاق ضيق، ما يرجح حركة قوية قريبة."

    if normalized.startswith("DISTRIBUTION RISK:"):
        bull_traps = _regex_value(r"Bull traps\s*\((\d+)\)", text)
        bear_traps = _regex_value(r"bear traps\s*\((\d+)\)", text)
        trap_text = (
            f"عدد مصائد الصعود ({bull_traps}) أعلى من مصائد الهبوط ({bear_traps})"
            if bull_traps and bear_traps
            else "إشارات المصائد تحتاج متابعة"
        )
        return f"مخاطر التوزيع: {trap_text}؛ تجنب مطاردة الصعود الحاد قبل تأكيد أحجام التداول."

    if normalized.startswith("CONCENTRATION RISK:"):
        positions = _regex_value(r"currently has\s*(\d+)\s*positions", text)
        sectors = _regex_value(r"leading sectors\s*\((.+?)\)", text)
        position_text = f"لا تحتوي حالياً على مراكز مفتوحة" if positions == "0" else f"تحتوي حالياً على {positions or '-'} مراكز"
        sector_text = ""
        if sectors:
            sector_text = f" بين القطاعات القيادية ({_apply_arabic_phrase_replacements(sectors).replace(', ', '، ')})"
        return f"مخاطر التركز: محفظة حورس {position_text}؛ يجب تنويع أي دخول جديد{sector_text}."

    if normalized.startswith("SQUEEZE VOLATILITY:"):
        names = _regex_value(r"SQUEEZE VOLATILITY:\s*(.+?)\s+may exhibit", text)
        name_text = _arabic_symbol_list(names) if names else "بعض الأسهم"
        return f"تذبذب الضغط السعري: {name_text} قد يتحرك بعنف في الاتجاهين قبل وضوح الاتجاه."

    translated = _apply_arabic_phrase_replacements(text)
    for key, label in sorted(_ARABIC_STATUS_LABELS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(rf"\b{re.escape(key)}\b", label, translated, flags=re.IGNORECASE)
    for key, label in _ARABIC_ACTION_LABELS.items():
        translated = re.sub(rf"\b{re.escape(key)}\b", label, translated, flags=re.IGNORECASE)
    translated = re.sub(r"\s+and\s+", " و", translated, flags=re.IGNORECASE)
    return translated.replace(", ", "، ")


def build_ai_report_telegram_message(report_payload: dict[str, Any], *, language: str = "EN") -> str:
    normalized_language = _normalize_report_language(language)
    market_direction = report_payload.get("market_direction") or {}
    execution_profile = report_payload.get("execution_profile") or {}
    daily_report = report_payload.get("daily_report") or {}
    summary_items = dedupe_strings(list(daily_report.get("summary") or []), limit=4)
    recommendations = dedupe_recommendations(list(report_payload.get("recommendations") or []))
    stance_recommendations = [
        rec for rec in recommendations if _sanitize_telegram_text(rec.get("ticker", "")).upper() == "CASH"
    ]
    setup_recommendations = [
        rec for rec in recommendations if _sanitize_telegram_text(rec.get("ticker", "")).upper() != "CASH"
    ][:4]
    warnings = dedupe_strings(list(report_payload.get("risk_warnings") or []), limit=3)

    label = _format_status_label(market_direction.get("label", "NEUTRAL"), "NEUTRAL")
    confidence = float(market_direction.get("confidence", 0.0) or 0.0)
    mode = _format_status_label(execution_profile.get("mode", "BALANCED"), "BALANCED")
    selectivity = _format_status_label(execution_profile.get("selectivity", "MEDIUM"), "MEDIUM")
    max_risk = float(execution_profile.get("max_risk_per_trade_pct", 1.0) or 1.0)

    if normalized_language == "AR":
        label_display = _format_arabic_status_label(market_direction.get("label", "NEUTRAL"), "NEUTRAL")
        mode_display = _format_arabic_status_label(execution_profile.get("mode", "BALANCED"), "BALANCED")
        selectivity_display = _format_arabic_status_label(execution_profile.get("selectivity", "MEDIUM"), "MEDIUM")
        lines = [
            "*تقرير حورس اليومي للسوق بالذكاء الاصطناعي*",
            f"`{TimeUtils.now().strftime('%Y-%m-%d %H:%M')}`",
            "",
            f"*حالة السوق:* `{label_display}`  |  *الثقة:* `{confidence:.1f}%`",
            f"*أسلوب التنفيذ:* `{mode_display}`  |  *انتقائية الفرص:* `{selectivity_display}`  |  *المخاطرة لكل صفقة:* `{max_risk:.2f}%`",
            "",
            "*الملخص التنفيذي*",
        ]
    else:
        lines = [
            "*HORUS AI DAILY MARKET REPORT*",
            f"`{TimeUtils.now().strftime('%Y-%m-%d %H:%M')}`",
            "",
            f"*Regime:* `{label}`  |  *Confidence:* `{confidence:.1f}%`",
            f"*Execution:* `{mode}`  |  *Selectivity:* `{selectivity}`  |  *Risk/Trade:* `{max_risk:.2f}%`",
            "",
            "*Executive Summary*",
        ]

    bullet = "•"
    if summary_items:
        for item in summary_items:
            summary_text = _arabicize_report_text(item) if normalized_language == "AR" else _sanitize_telegram_text(item)
            lines.append(f"{bullet} {summary_text}")
    else:
        lines.append(
            f"{bullet} لا توجد نقاط ملخص متاحة."
            if normalized_language == "AR"
            else f"{bullet} No summary points available."
        )

    if stance_recommendations:
        lines.append("")
        lines.append("*موقف التنفيذ*" if normalized_language == "AR" else "*Execution Stance*")
        for rec in stance_recommendations[:2]:
            ticker = _sanitize_telegram_text(rec.get("ticker", "CASH")).upper() or "CASH"
            action = _sanitize_telegram_text(rec.get("action", "HOLD")).upper() or "HOLD"
            rec_conf = float(rec.get("confidence", 0.0) or 0.0)
            if normalized_language == "AR":
                lines.append(f"{bullet} `{ticker}` {_format_arabic_action_label(action, 'HOLD')} | الثقة: `{rec_conf:.0f}%`")
            else:
                lines.append(f"{bullet} `{ticker}` {action} `{rec_conf:.0f}%`")

    lines.append("")
    lines.append("*أفضل الفرص*" if normalized_language == "AR" else "*Top Setups*")
    if setup_recommendations:
        for rec in setup_recommendations:
            ticker = _sanitize_telegram_text(rec.get("ticker", "N/A")).upper() or "N/A"
            action = _sanitize_telegram_text(rec.get("action", "WATCH")).upper() or "WATCH"
            rec_conf = float(rec.get("confidence", 0.0) or 0.0)
            entry = _sanitize_telegram_text(rec.get("entry_zone", "N/A")) or "N/A"
            stop = _sanitize_telegram_text(rec.get("stop_loss", "N/A")) or "N/A"
            target = _sanitize_telegram_text(rec.get("take_profit", "N/A")) or "N/A"
            if normalized_language == "AR":
                action_label = _format_arabic_action_label(action, "WATCH")
                entry = _arabicize_report_text(entry)
                target = _arabicize_report_text(target)
                lines.append(
                    f"{bullet} `{ticker}` {action_label} | الثقة: `{rec_conf:.0f}%` | الدخول: `{entry}` | وقف الخسارة: `{stop}` | الهدف: `{target}`"
                )
            else:
                lines.append(
                    f"{bullet} `{ticker}` {action} `{rec_conf:.0f}%` | Entry: `{entry}` | SL: `{stop}` | TP: `{target}`"
                )
    else:
        lines.append(
            f"{bullet} لا توجد فرص قابلة للتنفيذ."
            if normalized_language == "AR"
            else f"{bullet} No actionable setups."
        )

    if warnings:
        lines.append("")
        lines.append("*رادار المخاطر*" if normalized_language == "AR" else "*Risk Radar*")
        for warning in warnings:
            warning_text = _arabicize_report_text(warning) if normalized_language == "AR" else _sanitize_telegram_text(warning)
            lines.append(f"{bullet} {warning_text}")

    lines.append("")
    lines.append(
        "*الانضباط:* تحقق من السيولة، التزم بوقف الخسارة، ولا تجبر فرصاً ضعيفة."
        if normalized_language == "AR"
        else "*Discipline:* Validate volume, keep stops hard, avoid forcing low-edge setups."
    )

    message = "\n".join(lines).strip()
    if len(message) > 3900:
        message = f"{message[:3890]}\n..."
    return message
