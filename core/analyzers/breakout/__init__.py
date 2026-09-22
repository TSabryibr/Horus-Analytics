"""
MOMENTUM BREAKOUT SCANNER PACKAGE
=================================
Technical momentum scanning, pivot & resistance calculation, manipulation sentry,
institutional activity detection, and Excel reporting for the EGX market.
"""

from core import TimeUtils
from core.pre_scanner_middleware import DataValidationError, PreScannerMiddleware
from database import SignalStateArchive
from utils.currency_fetcher import get_parallel_usd_egp_rate, get_usd_trend_slope

from .pivots import (
    ATR_PERIOD,
    DATA_FOLDER,
    EMA_FAST,
    FORCE_PERIOD,
    LOOKBACK,
    MANIP_ABSORB_PRICE_MAX,
    MANIP_ABSORB_VOL_THRESHOLD,
    MANIP_LOW_VOL_PRICE_MIN,
    MANIP_LOW_VOL_THRESHOLD,
    MAX_SPREAD_PCT,
    MIN_AVG_VOLUME_20D,
    MIN_DATA_POINTS,
    MIN_TURNOVER_EGP,
    MOMENTUM_THRESHOLD,
    RSI_MAX,
    RSI_MIN,
    RSI_PERIOD,
    SL_BUFFER_PCT,
    TP1_PCT,
    TP2_RR_RATIO,
    TP3_RR_RATIO,
    TP4_RR_RATIO,
    USD_STOCKS,
    VOL_AVG_PERIOD,
    VOL_SPIKE_FACTOR,
    _prepare_analysis_frame,
    calculate_critical_points,
    find_pivot_highs,
    find_pivot_lows,
)
from .metrics import (
    _RECENT_BREAKOUT_TIMESTAMPS,
    detect_manipulation,
    estimate_bid_ask_spread,
)
from .excel import (
    export_scan_results_to_excel,
)
from .scanner import (
    _include_live_for_analysis,
    analyze_stock,
    analyze_stock_frame,
    scan_full_market,
)

__all__ = [
    # Constants
    "DATA_FOLDER",
    "LOOKBACK",
    "ATR_PERIOD",
    "FORCE_PERIOD",
    "MIN_DATA_POINTS",
    "MIN_TURNOVER_EGP",
    "VOL_SPIKE_FACTOR",
    "MOMENTUM_THRESHOLD",
    "RSI_PERIOD",
    "RSI_MIN",
    "RSI_MAX",
    "EMA_FAST",
    "VOL_AVG_PERIOD",
    "MAX_SPREAD_PCT",
    "MIN_AVG_VOLUME_20D",
    "MANIP_LOW_VOL_THRESHOLD",
    "MANIP_LOW_VOL_PRICE_MIN",
    "MANIP_ABSORB_VOL_THRESHOLD",
    "MANIP_ABSORB_PRICE_MAX",
    "SL_BUFFER_PCT",
    "TP1_PCT",
    "TP2_RR_RATIO",
    "TP3_RR_RATIO",
    "TP4_RR_RATIO",
    "USD_STOCKS",
    "_RECENT_BREAKOUT_TIMESTAMPS",
    # Pivots & Indicators
    "find_pivot_highs",
    "find_pivot_lows",
    "calculate_critical_points",
    "_prepare_analysis_frame",
    # Metrics & Sentry
    "estimate_bid_ask_spread",
    "detect_manipulation",
    # Scanner & Analysis
    "_include_live_for_analysis",
    "analyze_stock_frame",
    "analyze_stock",
    "scan_full_market",
    # Reporting
    "export_scan_results_to_excel",
    # Compatibility Re-exports for test monkeypatches
    "get_parallel_usd_egp_rate",
    "get_usd_trend_slope",
    "PreScannerMiddleware",
    "DataValidationError",
    "SignalStateArchive",
    "TimeUtils",
]
