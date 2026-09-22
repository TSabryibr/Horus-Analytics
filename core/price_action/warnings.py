from __future__ import annotations
"""Warning-only detectors for EGX price-action strategies."""


import pandas as pd

from . import patterns


def detect_descending_triangle_warning(frame: pd.DataFrame) -> bool:
    support = patterns.support_level(frame, window=8)
    if support is None:
        return False
    close = float(frame.iloc[-1]["Close"])
    near_support = close <= support * 1.01
    return near_support and patterns.has_descending_highs(frame, window=6)


def detect_rising_wedge_warning(frame: pd.DataFrame) -> bool:
    return patterns.is_rising_wedge(frame, window=8)


def detect_failed_breakdown_trap(frame: pd.DataFrame) -> bool:
    if len(frame) < 3:
        return False
    support = patterns.support_level(frame.iloc[:-1], window=8)
    if support is None:
        return False
    previous = frame.iloc[-2]
    current = frame.iloc[-1]
    broke_down = float(previous["Low"]) < support and float(previous["Close"]) < support
    reclaimed = float(current["Close"]) > support
    return broke_down and reclaimed


def detect_failed_breakout_warning(frame: pd.DataFrame) -> bool:
    if len(frame) < 3:
        return False
    prior_frame = frame.iloc[:-1]
    resistance = patterns.resistance_level(prior_frame, window=8)
    if resistance is None:
        return False
    previous = frame.iloc[-2]
    current = frame.iloc[-1]
    broke_out = float(previous["Close"]) > resistance
    failed = float(current["Close"]) < resistance
    return broke_out and failed


def detect_bull_trap_breakout_warning(frame: pd.DataFrame) -> bool:
    return patterns.is_bull_trap_breakout_failure(frame, resistance_window=8)


def detect_double_top_neckline_failure(frame: pd.DataFrame) -> bool:
    return patterns.is_double_top_neckline_failure(frame, base_window=10)


def detect_reversal_structure_shift(frame: pd.DataFrame) -> bool:
    support = patterns.support_level(frame, window=8)
    if support is None:
        return False
    return (not patterns.is_higher_high_higher_low(frame, window=6)) and float(frame.iloc[-1]["Close"]) < support
