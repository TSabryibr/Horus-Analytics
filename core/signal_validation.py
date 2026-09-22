from __future__ import annotations
"""
EGX long-signal validation helpers.

This seam turns abnormal participation into a reusable validation layer so
iterative and vectorized signal paths can share the same institutional-quality
gate.
"""

from core.settings import settings

from typing import Any

import numpy as np
import pandas as pd

from core.market_profiles import EGX30_TREND_PROFILE, MarketProfile


def validate_long_signal(
    row: pd.Series,
    settings: Any,
    profile: MarketProfile = EGX30_TREND_PROFILE,
) -> dict[str, Any]:
    """Validate one long candidate and return reusable VSA-style metadata."""
    try:
        if row is None or (isinstance(row, pd.Series) and row.empty):
            return {"is_valid": False, "veto_reason": "empty_input"}

        metrics = _extract_long_validation_metrics(row, settings, profile)
        is_valid = bool(
            metrics["volume_confirmed"]
            and metrics["turnover_confirmed"]
            and metrics["efi_confirmed"]
            and metrics["candle_quality_confirmed"]
        )

        return {
            "is_valid": is_valid,
            "veto_reason": None if is_valid else _first_failed_reason(metrics),
            **metrics,
        }
    except Exception as e:
        # H3.3 Resilience: Never let a single row validation crash the scanner
        from core.audit import log_event
        log_event("SYSTEM", "VALIDATION_ERROR", f"Failed to validate row: {e}", level="ERROR")
        return {"is_valid": False, "veto_reason": "validation_error"}


def validate_long_signals(
    frame: pd.DataFrame,
    settings: Any,
    profile: MarketProfile = EGX30_TREND_PROFILE,
) -> pd.DataFrame:
    """Validate a batch of long candidates with vectorized pandas masks."""

    volume_mult_20 = _series_or_default(frame, "Rel_Vol", 0.0).astype(float)
    turnover = _current_turnover_series(frame).astype(float)
    efi = _series_or_default(frame, "EFI", 0.0).astype(float)
    close_quality = _close_location_quality(frame)

    volume_confirmed = volume_mult_20 >= profile.volume_confirmation_threshold
    turnover_confirmed = turnover >= _resolve_turnover_floor(settings, profile)
    efi_confirmed = efi > 0
    candle_quality_confirmed = close_quality >= 0.6

    is_valid = volume_confirmed & turnover_confirmed & efi_confirmed & candle_quality_confirmed
    veto_reason = np.select(
        [
            ~volume_confirmed,
            ~turnover_confirmed,
            ~efi_confirmed,
            ~candle_quality_confirmed,
        ],
        [
            "volume_confirmation",
            "turnover_floor",
            "efi_confirmation",
            "candle_quality",
        ],
        default="",
    )

    return pd.DataFrame(
        {
            "is_valid": is_valid,
            "veto_reason": pd.Series(veto_reason, index=frame.index).replace("", None),
            "volume_mult_20": volume_mult_20,
            "turnover": turnover,
            "volume_confirmed": volume_confirmed,
            "turnover_confirmed": turnover_confirmed,
            "efi_confirmed": efi_confirmed,
            "candle_quality_confirmed": candle_quality_confirmed,
            "candle_close_quality": close_quality,
            "volume_threshold": profile.volume_confirmation_threshold,
            "turnover_floor": _resolve_turnover_floor(settings, profile),
            "profile_name": profile.name,
        },
        index=frame.index,
    )


def _extract_long_validation_metrics(
    row: pd.Series,
    settings: Any,
    profile: MarketProfile,
) -> dict[str, Any]:
    """Build the shared validation metrics dictionary for one row."""

    volume_mult_20 = float(_coerce_number(row.get("Rel_Vol"), 0.0))
    turnover = float(_coerce_number(_current_turnover_value(row), 0.0))
    efi = float(_coerce_number(row.get("EFI"), 0.0))
    candle_close_quality = float(_coerce_number(_close_location_value(row), 0.0))
    turnover_floor = _resolve_turnover_floor(settings, profile)

    volume_confirmed = volume_mult_20 >= profile.volume_confirmation_threshold
    turnover_confirmed = turnover >= turnover_floor
    efi_confirmed = efi > 0
    candle_quality_confirmed = candle_close_quality >= 0.6

    return {
        "volume_mult_20": volume_mult_20,
        "turnover": turnover,
        "volume_threshold": profile.volume_confirmation_threshold,
        "turnover_floor": turnover_floor,
        "volume_confirmed": volume_confirmed,
        "turnover_confirmed": turnover_confirmed,
        "efi_confirmed": efi_confirmed,
        "candle_quality_confirmed": candle_quality_confirmed,
        "candle_close_quality": candle_close_quality,
        "profile_name": profile.name,
    }


def _resolve_turnover_floor(settings: Any, profile: MarketProfile) -> float:
    """Use the stricter of strategy liquidity floor and profile floor."""

    base_floor = float(_resolve_setting(settings, "MIN_TURNOVER", profile.turnover_floor))
    return max(base_floor, float(profile.turnover_floor))


def _resolve_setting(settings: Any, key: str, default: Any) -> Any:
    if isinstance(settings, dict) and key in settings:
        return settings[key]
    fallback = getattr(settings, key, default)
    if isinstance(settings, dict) or settings is None:
        return fallback
    return getattr(settings, key, fallback)


def _current_turnover_value(row: pd.Series) -> float | Any:
    """Prefer current turnover when available, otherwise fall back to the average."""

    turnover = row.get("Turnover")
    if turnover is None or pd.isna(turnover):
        return row.get("Avg_Turnover", 0.0)
    return turnover


def _current_turnover_series(frame: pd.DataFrame) -> pd.Series:
    """Vectorized turnover selection with fallback to average turnover."""

    turnover = _series_or_default(frame, "Turnover", np.nan)
    avg_turnover = _series_or_default(frame, "Avg_Turnover", 0.0)
    return turnover.where(~turnover.isna(), avg_turnover)


def _close_location_value(row: pd.Series) -> float:
    """Return where the close sits inside the candle range."""

    high = _coerce_number(row.get("High"), np.nan)
    low = _coerce_number(row.get("Low"), np.nan)
    close = _coerce_number(row.get("Close"), np.nan)
    if any(pd.isna(v) for v in (high, low, close)):
        return 1.0
    rng = high - low
    if rng <= 0:
        return 1.0
    return float((close - low) / rng)


def _close_location_quality(frame: pd.DataFrame) -> pd.Series:
    """Vectorized candle-close quality with graceful fallback when OHLC is absent."""

    if not {"High", "Low", "Close"}.issubset(frame.columns):
        return pd.Series([1.0] * len(frame), index=frame.index, dtype=float)

    high = frame["High"].astype(float)
    low = frame["Low"].astype(float)
    close = frame["Close"].astype(float)
    rng = high - low
    quality = pd.Series([1.0] * len(frame), index=frame.index, dtype=float)
    valid = rng > 0
    quality.loc[valid] = ((close.loc[valid] - low.loc[valid]) / rng.loc[valid]).astype(float)
    return quality


def _series_or_default(frame: pd.DataFrame, column: str, default: float) -> pd.Series:
    """Return a frame column or a default-valued Series when absent."""

    if column in frame.columns:
        return frame[column]
    return pd.Series([default] * len(frame), index=frame.index)


def _first_failed_reason(metrics: dict[str, Any]) -> str:
    """Return the first validation reason in priority order."""

    if not metrics["volume_confirmed"]:
        return "volume_confirmation"
    if not metrics["turnover_confirmed"]:
        return "turnover_floor"
    if not metrics["efi_confirmed"]:
        return "efi_confirmation"
    return "candle_quality"


def _coerce_number(value: Any, default: float) -> float:
    """Convert numeric-like input while tolerating NaN and None."""

    if value is None or pd.isna(value):
        return default
    return float(value)
