"""
ANALYSIS REPORTS PACKAGE
========================
Modular weekly & monthly analytics report generation, market metrics aggregation,
signal & lifecycle outcome reviews, and multi-lingual Telegram delivery.
"""

from core.DataManager import DataManager
from routes.data import evaluate_data_freshness_logic

from .periods import (
    _ALLOWED_PERIODS,
    _ANALYSIS_REPORT_CACHE,
    _analysis_cache_ttl_sec,
    _build_cache_key,
    _cache_is_fresh,
    _coerce_float,
    _count_trading_days,
    _default_period_end,
    _final_weekday_for_market_week,
    _is_trading_day,
    _last_trading_day_of_month,
    _last_trading_day_on_or_before,
    _market_weekend_set,
    _monthly_start_from_end,
    _parse_date,
    _parse_period,
    _resolve_period_window,
    _weekly_start_from_end,
    is_final_trading_day_of_month,
    is_final_trading_day_of_week,
)
from .market_summary import (
    _aggregate_market_summary,
    _load_market_window,
)
from .signals import (
    _aggregate_portfolio_signal_review,
    _aggregate_published_lifecycle_review,
    _aggregate_signal_review,
    _apply_legacy_signal_fallback,
    _hours_between,
    _lifecycle_breakdown_rows,
    _resolve_report_portfolio,
    _resolved_lifecycle_exit_price,
    _signed_signal_return_pct,
)
from .delivery import (
    _AR_ANALYSIS_STATUS_LABELS,
    _arabic_analysis_status,
    _arabicize_analysis_text,
    _normalize_report_language,
    _sanitize_telegram_text,
    build_analysis_report_telegram_message,
)
from .router import (
    AnalysisBroadcastRequest,
    broadcast_analysis_report,
    build_analysis_report,
    dispatch_analysis_report,
    get_analysis_report,
    router,
)

__all__ = [
    # Router & Endpoints
    "router",
    "AnalysisBroadcastRequest",
    "build_analysis_report",
    "dispatch_analysis_report",
    "get_analysis_report",
    "broadcast_analysis_report",
    # Periods & Dates
    "_ANALYSIS_REPORT_CACHE",
    "_ALLOWED_PERIODS",
    "_coerce_float",
    "_market_weekend_set",
    "_is_trading_day",
    "_last_trading_day_on_or_before",
    "_last_trading_day_of_month",
    "_final_weekday_for_market_week",
    "is_final_trading_day_of_week",
    "is_final_trading_day_of_month",
    "_parse_period",
    "_parse_date",
    "_weekly_start_from_end",
    "_monthly_start_from_end",
    "_count_trading_days",
    "_default_period_end",
    "_resolve_period_window",
    "_analysis_cache_ttl_sec",
    "_cache_is_fresh",
    "_build_cache_key",
    # Market Summary
    "_load_market_window",
    "_aggregate_market_summary",
    # Signals
    "_resolve_report_portfolio",
    "_signed_signal_return_pct",
    "_hours_between",
    "_resolved_lifecycle_exit_price",
    "_lifecycle_breakdown_rows",
    "_aggregate_signal_review",
    "_apply_legacy_signal_fallback",
    "_aggregate_published_lifecycle_review",
    "_aggregate_portfolio_signal_review",
    # Delivery
    "_sanitize_telegram_text",
    "_normalize_report_language",
    "_AR_ANALYSIS_STATUS_LABELS",
    "_arabic_analysis_status",
    "_arabicize_analysis_text",
    "build_analysis_report_telegram_message",
    # External dependencies imported for test monkeypatching
    "DataManager",
    "evaluate_data_freshness_logic",
]
