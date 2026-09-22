from __future__ import annotations

import datetime
import json
from typing import Any, Optional

from fastapi import HTTPException
from core.settings import settings

SIGNALS_ONLY = "SIGNALS_ONLY"
SIGNALS_PLUS_PORTFOLIO_RECS = "SIGNALS_PLUS_PORTFOLIO_RECS"
MANAGED_ADVISORY = "MANAGED_ADVISORY"

SUBSCRIPTION_TIERS = {
    SIGNALS_ONLY,
    SIGNALS_PLUS_PORTFOLIO_RECS,
    MANAGED_ADVISORY,
}

ADVISORY_TIERS = {
    SIGNALS_PLUS_PORTFOLIO_RECS,
    MANAGED_ADVISORY,
}

MANAGED_TIERS = {
    MANAGED_ADVISORY,
}

SUBSCRIPTION_TIER_RANK = {
    SIGNALS_ONLY: 1,
    SIGNALS_PLUS_PORTFOLIO_RECS: 2,
    MANAGED_ADVISORY: 3,
}

MAIN_CHANNEL_BROADCAST_LEVELS = {"none", "type_1", "type_2", "type_3"}
MAIN_CHANNEL_BROADCAST_RANK = {
    "none": 0,
    "type_1": 1,
    "type_2": 2,
    "type_3": 3,
}

ADVISORY_DISCLAIMER = "Advisory only. No automatic execution was performed by Horus."
REPORT_LANGUAGES = {"EN", "AR"}


def subscription_error(
    status_code: int,
    error_reason: str,
    message: str,
    **context: Any,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "error_type": "subscription",
            "error_reason": error_reason,
            "message": message,
            **context,
        },
    )


def normalize_tier(value: str) -> str:
    tier = str(value or SIGNALS_ONLY).upper().strip()
    if tier not in SUBSCRIPTION_TIERS:
        raise subscription_error(
            422,
            "invalid_subscription_tier",
            "Subscription tier is invalid.",
            subscription_tier=value,
            allowed_tiers=sorted(SUBSCRIPTION_TIERS),
        )
    return tier


def service_tier_rank(tier: str) -> int:
    return SUBSCRIPTION_TIER_RANK[normalize_tier(tier)]


def subscriber_entitled_to_service(subscriber_tier: str, service_tier: str) -> bool:
    return service_tier_rank(subscriber_tier) >= service_tier_rank(service_tier)


def normalize_main_channel_broadcast_level(value: Optional[str]) -> str:
    level = str(value or "none").strip().lower()
    aliases = {
        "": "none",
        "off": "none",
        "disabled": "none",
        "type1": "type_1",
        "type_1": "type_1",
        "type 1": "type_1",
        "type2": "type_2",
        "type_2": "type_2",
        "type 2": "type_2",
        "type3": "type_3",
        "type_3": "type_3",
        "type 3": "type_3",
    }
    level = aliases.get(level, level)
    if level not in MAIN_CHANNEL_BROADCAST_LEVELS:
        raise subscription_error(
            422,
            "invalid_main_channel_broadcast_level",
            "Main channel broadcast level is invalid.",
            broadcast_level=value,
            allowed_levels=sorted(MAIN_CHANNEL_BROADCAST_LEVELS),
        )
    return level


def main_channel_includes_service(broadcast_level: Optional[str], service_tier: str) -> bool:
    level = normalize_main_channel_broadcast_level(broadcast_level)
    return MAIN_CHANNEL_BROADCAST_RANK[level] >= service_tier_rank(service_tier)


def automated_main_channel_signal_allowed(service_tier: str = SIGNALS_ONLY) -> bool:
    level = getattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "none")
    try:
        return main_channel_includes_service(level, service_tier)
    except HTTPException:
        return False


def normalize_report_language(value: Optional[str]) -> str:
    language = str(value or "EN").strip().upper() or "EN"
    aliases = {
        "ENGLISH": "EN",
        "ENG": "EN",
        "ARABIC": "AR",
        "ARA": "AR",
        "العربية": "AR",
    }
    language = aliases.get(language, language)
    if language not in REPORT_LANGUAGES:
        raise subscription_error(
            422,
            "invalid_report_language",
            "Report language must be EN or AR.",
            report_language=value,
            allowed_languages=sorted(REPORT_LANGUAGES),
        )
    return language


def subscription_plan_label(tier: str, language: Optional[str] = None) -> str:
    normalized_language = normalize_report_language(language or "EN")
    labels_en = {
        SIGNALS_ONLY: "Type 1 - Market Signals",
        SIGNALS_PLUS_PORTFOLIO_RECS: "Type 2 - Market Signals + Portfolio Recommendations",
        MANAGED_ADVISORY: "Type 3 - Market Signals + Managed Advisory",
    }
    labels_ar = {
        SIGNALS_ONLY: "النوع 1 - إشارات السوق",
        SIGNALS_PLUS_PORTFOLIO_RECS: "النوع 2 - إشارات السوق + توصيات المحفظة",
        MANAGED_ADVISORY: "النوع 3 - إشارات السوق + الاستشارات المدارة",
    }
    normalized = normalize_tier(tier)
    labels = labels_ar if normalized_language == "AR" else labels_en
    return labels.get(normalized, normalized)


def subscription_benefits(tier: str, language: Optional[str] = None) -> list[str]:
    normalized = normalize_tier(tier)
    if normalize_report_language(language or "EN") == "AR":
        benefits = [
            "إشارات سوق مميزة على تيليجرام",
            "مناطق دخول مع وقف الخسارة وهدف 1 وهدف 2 والدرجة والثقة والأفق",
        ]
        if normalized in ADVISORY_TIERS:
            benefits.extend(
                [
                    "تقارير توصيات المحفظة للمحافظ المرتبطة",
                    "إرشاد للمراكز المفتوحة: إغلاق أو احتفاظ أو تحديث وقف الخسارة/الأهداف أو تعديل الحجم",
                ]
            )
        if normalized in MANAGED_TIERS:
            benefits.extend(
                [
                    "تقارير استشارية استباقية بعد تشغيل الإشارات والمراجعات المجدولة",
                    "تحديد حجم المراكز مع مراعاة النقد وضوابط المخاطر",
                ]
            )
        return benefits

    benefits = [
        "Premium market signals on Telegram",
        "Signal entries with stop loss, TP1, TP2, score, confidence, and horizon",
    ]
    if normalized in ADVISORY_TIERS:
        benefits.extend(
            [
                "Portfolio recommendation reports for linked portfolios",
                "Open-position guidance: close, hold, update SL/TP, or resize",
            ]
        )
    if normalized in MANAGED_TIERS:
        benefits.extend(
            [
                "Proactive portfolio advisory reports after signal runs and scheduled reviews",
                "Cash-aware position sizing and risk controls",
            ]
        )
    return benefits


def _default_report_language() -> str:
    try:
        return normalize_report_language(getattr(settings, "TELEGRAM_REPORT_LANGUAGE", "EN"))
    except HTTPException:
        return "EN"


def normalize_risk_profile(value: Optional[str]) -> str:
    profile = str(value or "BALANCED").upper().strip()
    if profile not in {"CONSERVATIVE", "BALANCED", "AGGRESSIVE"}:
        raise subscription_error(
            422,
            "invalid_risk_profile",
            "Risk profile must be CONSERVATIVE, BALANCED, or AGGRESSIVE.",
            risk_profile=value,
        )
    return profile


def _safe_int_setting(name: str, default: int) -> int:
    try:
        return int(getattr(settings, name, default))
    except (TypeError, ValueError):
        return default


def _safe_float_setting(name: str, default: float) -> float:
    try:
        return float(getattr(settings, name, default))
    except (TypeError, ValueError):
        return default


def _clean_optional(value: Optional[str]) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _json_object(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _positive_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _increment(bucket: dict[str, int], key: str) -> None:
    bucket[key] = int(bucket.get(key, 0) or 0) + 1
