from __future__ import annotations
"""Deterministic price-action pattern helpers for EGX strategies."""


import pandas as pd


def _tail(frame: pd.DataFrame, size: int) -> pd.DataFrame:
    if len(frame) <= size:
        return frame.copy()
    return frame.tail(size)


def _close_fraction_in_range(row: pd.Series) -> float:
    high = float(row["High"])
    low = float(row["Low"])
    close = float(row["Close"])
    bar_range = max(high - low, 1e-9)
    return (close - low) / bar_range


def has_rising_lows(frame: pd.DataFrame, *, window: int = 6) -> bool:
    segment = _tail(frame, window)
    if len(segment) < window:
        return False
    lows = segment["Low"].reset_index(drop=True)
    first_half = lows.iloc[: window // 2].min()
    second_half = lows.iloc[window // 2 :].min()
    return bool(second_half > first_half)


def has_descending_highs(frame: pd.DataFrame, *, window: int = 6) -> bool:
    segment = _tail(frame, window)
    if len(segment) < window:
        return False
    highs = segment["High"].reset_index(drop=True)
    return bool(highs.iloc[-1] < highs.iloc[0] and highs.iloc[-2:].max() < highs.iloc[:2].max())


def resistance_level(frame: pd.DataFrame, *, window: int = 10) -> float | None:
    segment = _tail(frame.iloc[:-1], window)
    if segment.empty:
        return None
    return float(segment["High"].max())


def support_level(frame: pd.DataFrame, *, window: int = 10) -> float | None:
    segment = _tail(frame.iloc[:-1], window)
    if segment.empty:
        return None
    return float(segment["Low"].min())


def is_recent_breakout(frame: pd.DataFrame, *, window: int = 10, tolerance: float = 0.0) -> bool:
    level = resistance_level(frame, window=window)
    if level is None:
        return False
    close = float(frame.iloc[-1]["Close"])
    return close > level * (1.0 + tolerance)


def is_box_consolidation(frame: pd.DataFrame, *, window: int = 8, max_width_pct: float = 0.08) -> bool:
    segment = _tail(frame.iloc[:-1], window)
    if len(segment) < window:
        return False
    box_high = float(segment["High"].max())
    box_low = float(segment["Low"].min())
    center = max((box_high + box_low) / 2.0, 1e-9)
    width_pct = (box_high - box_low) / center
    return width_pct <= max_width_pct


def is_symmetrical_triangle(
    frame: pd.DataFrame,
    *,
    window: int = 8,
    compression_ratio: float = 0.8,
) -> bool:
    segment = _tail(frame, window)
    if len(segment) < window:
        return False
    highs = segment["High"].reset_index(drop=True)
    lows = segment["Low"].reset_index(drop=True)
    first_range = float(highs.iloc[:3].max() - lows.iloc[:3].min())
    last_range = float(highs.iloc[-3:].max() - lows.iloc[-3:].min())
    return bool(
        has_descending_highs(segment, window=window)
        and has_rising_lows(segment, window=window)
        and last_range < first_range * compression_ratio
    )


def is_higher_high_higher_low(frame: pd.DataFrame, *, window: int = 6) -> bool:
    segment = _tail(frame, window)
    if len(segment) < window:
        return False
    highs = segment["High"].reset_index(drop=True)
    lows = segment["Low"].reset_index(drop=True)
    return bool(highs.iloc[-1] > highs.iloc[0] and lows.iloc[-1] > lows.iloc[0])


def is_rising_wedge(frame: pd.DataFrame, *, window: int = 8) -> bool:
    segment = _tail(frame, window)
    if len(segment) < window:
        return False
    highs = segment["High"].reset_index(drop=True)
    lows = segment["Low"].reset_index(drop=True)
    range_start = highs.iloc[0] - lows.iloc[0]
    range_end = highs.iloc[-1] - lows.iloc[-1]
    return bool(highs.iloc[-1] > highs.iloc[0] and lows.iloc[-1] > lows.iloc[0] and range_end < range_start)


def is_inside_bar(frame: pd.DataFrame) -> bool:
    if len(frame) < 2:
        return False
    mother_bar = frame.iloc[-2]
    inside_bar = frame.iloc[-1]
    return bool(
        float(inside_bar["High"]) <= float(mother_bar["High"])
        and float(inside_bar["Low"]) >= float(mother_bar["Low"])
    )


def has_prior_uptrend(frame: pd.DataFrame, *, lookback: int = 6) -> bool:
    segment = _tail(frame, lookback)
    if len(segment) < lookback:
        return False
    closes = segment["Close"].reset_index(drop=True)
    lows = segment["Low"].reset_index(drop=True)
    return bool(closes.iloc[-1] > closes.iloc[0] and lows.iloc[-1] > lows.iloc[0])


def is_inside_bar_breakout(frame: pd.DataFrame, *, tolerance: float = 0.0) -> bool:
    if len(frame) < 3:
        return False
    setup = frame.iloc[-3:-1]
    trigger = frame.iloc[-1]
    if not is_inside_bar(setup):
        return False
    mother_bar_high = float(setup.iloc[0]["High"])
    return bool(float(trigger["Close"]) > mother_bar_high * (1.0 + tolerance))


def is_bullish_engulfing(frame: pd.DataFrame) -> bool:
    if len(frame) < 2:
        return False
    prev_bar = frame.iloc[-2]
    curr_bar = frame.iloc[-1]
    prev_open = float(prev_bar["Open"])
    prev_close = float(prev_bar["Close"])
    curr_open = float(curr_bar["Open"])
    curr_close = float(curr_bar["Close"])
    return bool(
        prev_close < prev_open
        and curr_close > curr_open
        and curr_open <= prev_close
        and curr_close >= prev_open
    )


def support_reclaim_with_engulfing(
    frame: pd.DataFrame,
    *,
    support_window: int = 10,
    reclaim_lookback: int = 4,
    tolerance_pct: float = 0.015,
) -> bool:
    if len(frame) < max(reclaim_lookback + 3, 5):
        return False
    support = support_level(frame.iloc[:-2], window=support_window)
    if support is None:
        return False
    support_bar = frame.iloc[-3]
    engulf_bar = frame.iloc[-2]
    latest_bar = frame.iloc[-1]
    support_touch = float(min(support_bar["Low"], engulf_bar["Low"])) <= support * (1.0 + tolerance_pct)
    if not support_touch or not is_bullish_engulfing(frame.iloc[-3:-1]):
        return False
    prior_high = float(_tail(frame.iloc[:-1], reclaim_lookback)["High"].max())
    return bool(float(latest_bar["Close"]) > prior_high)


def intraday_support_reclaim_confirmation(
    frame: pd.DataFrame,
    *,
    support_window: int = 6,
    reclaim_lookback: int = 3,
    tolerance_pct: float = 0.003,
) -> bool:
    if len(frame) < max(support_window, reclaim_lookback + 3):
        return False
    support = support_level(frame.iloc[:-2], window=support_window)
    if support is None:
        return False
    reclaim_bar = frame.iloc[-2]
    trigger_bar = frame.iloc[-1]
    support_tested = float(reclaim_bar["Low"]) <= support * (1.0 + tolerance_pct)
    reclaimed = float(reclaim_bar["Close"]) >= support and float(trigger_bar["Close"]) > float(reclaim_bar["High"])
    micro_pivot = float(_tail(frame.iloc[:-1], reclaim_lookback)["High"].max())
    return bool(support_tested and reclaimed and float(trigger_bar["Close"]) >= micro_pivot)


def intraday_breakout_retest_reentry(
    frame: pd.DataFrame,
    *,
    resistance_window: int = 6,
    tolerance_pct: float = 0.005,
    breakout_close_fraction_min: float = 0.65,
    trigger_close_fraction_min: float = 0.60,
) -> bool:
    if len(frame) < 4:
        return False
    breakout_context = frame.iloc[:-2]
    resistance = resistance_level(breakout_context, window=resistance_window)
    if resistance is None:
        return False
    breakout_bar = frame.iloc[-3]
    retest_bar = frame.iloc[-2]
    trigger_bar = frame.iloc[-1]
    breakout_clear = resistance * (1.0 + tolerance_pct)
    resumed_clear = float(retest_bar["High"]) * (1.0 + (tolerance_pct / 2.0))
    broke_out = (
        float(breakout_bar["Close"]) >= breakout_clear
        and float(breakout_bar["Close"]) > float(breakout_bar["Open"])
        and _close_fraction_in_range(breakout_bar) >= breakout_close_fraction_min
    )
    retest_held = (
        float(retest_bar["Low"]) >= resistance * (1.0 - tolerance_pct)
        and float(retest_bar["Close"]) >= resistance * (1.0 + (tolerance_pct / 4.0))
    )
    resumed = (
        float(trigger_bar["Close"]) >= resumed_clear
        and _close_fraction_in_range(trigger_bar) >= trigger_close_fraction_min
    )
    return bool(broke_out and retest_held and resumed)


def intraday_higher_high_higher_low_continuation(frame: pd.DataFrame, *, window: int = 5) -> bool:
    if len(frame) < window + 1:
        return False
    structure = _tail(frame.iloc[:-1], window)
    if len(structure) < window:
        return False
    higher_low_intact = float(structure["Low"].iloc[-1]) > float(structure["Low"].iloc[0])
    prior_pivot_high = float(structure["High"].iloc[:-1].max())
    trigger_bar = frame.iloc[-1]
    return bool(higher_low_intact and float(trigger_bar["Close"]) > prior_pivot_high)


def intraday_selling_trap_reclaim(
    frame: pd.DataFrame,
    *,
    support_window: int = 6,
    tolerance_pct: float = 0.003,
) -> bool:
    if len(frame) < 3:
        return False
    support = support_level(frame.iloc[:-2], window=support_window)
    if support is None:
        return False
    breakdown_bar = frame.iloc[-2]
    trigger_bar = frame.iloc[-1]
    broke_down = float(breakdown_bar["Low"]) < support and float(breakdown_bar["Close"]) < support * (1.0 + tolerance_pct)
    reclaimed = float(trigger_bar["Close"]) > support and float(trigger_bar["Close"]) > float(breakdown_bar["High"])
    return bool(broke_down and reclaimed)


def is_fakey_bullish_reversal(
    frame: pd.DataFrame,
    *,
    support_window: int = 10,
    tolerance_pct: float = 0.01,
) -> bool:
    if len(frame) < 4:
        return False
    setup = frame.iloc[-4:-2]
    rejection_bar = frame.iloc[-2]
    trigger_bar = frame.iloc[-1]
    if not is_inside_bar(setup):
        return False
    mother_bar = setup.iloc[0]
    inside_bar = setup.iloc[1]
    support = support_level(frame.iloc[:-2], window=support_window)
    if support is None:
        return False
    false_break = float(rejection_bar["Low"]) < float(inside_bar["Low"])
    support_context = float(rejection_bar["Low"]) <= support * (1.0 + tolerance_pct)
    reclaimed = float(rejection_bar["Close"]) >= float(inside_bar["Low"]) and float(trigger_bar["Close"]) > float(mother_bar["High"])
    return bool(false_break and support_context and reclaimed)


def is_double_bottom_neckline_reclaim(
    frame: pd.DataFrame,
    *,
    base_window: int = 10,
    low_tolerance_pct: float = 0.02,
    support_tolerance_pct: float = 0.02,
) -> bool:
    if len(frame) < 7:
        return False
    base = _tail(frame.iloc[:-2], base_window)
    if len(base) < 5:
        return False
    support = float(base["Low"].min())
    midpoint = float(base["High"].median())
    first_low = float(base.iloc[: len(base) // 2]["Low"].min())
    second_low = float(base.iloc[len(base) // 2 :]["Low"].min())
    lows_aligned = abs(first_low - second_low) / max(support, 1e-9) <= low_tolerance_pct
    support_respected = second_low <= support * (1.0 + support_tolerance_pct)
    reclaim_bar = frame.iloc[-2]
    confirm_bar = frame.iloc[-1]
    neckline_slice = base.iloc[max((len(base) // 2) - 1, 0) :]
    neckline = float(neckline_slice["High"].max())
    reclaimed = float(reclaim_bar["Close"]) > neckline or float(confirm_bar["Close"]) > neckline
    held = float(confirm_bar["Low"]) >= midpoint and float(confirm_bar["Close"]) >= float(reclaim_bar["Close"])
    return bool(lows_aligned and support_respected and reclaimed and held)


def is_inverse_head_and_shoulders_reclaim(
    frame: pd.DataFrame,
    *,
    base_window: int = 11,
    shoulder_tolerance_pct: float = 0.03,
    head_depth_pct: float = 0.025,
) -> bool:
    if len(frame) < 8:
        return False
    base = _tail(frame.iloc[:-2], base_window)
    if len(base) < 7:
        return False
    left_segment = base.iloc[: max(len(base) // 3, 2)]
    head_segment = base.iloc[max(len(base) // 3, 1) : max((2 * len(base)) // 3, 3)]
    right_segment = base.iloc[max((2 * len(base)) // 3, len(base) - 3) :]
    if left_segment.empty or head_segment.empty or right_segment.empty:
        return False

    left_shoulder = float(left_segment["Low"].min())
    head_low = float(head_segment["Low"].min())
    right_shoulder = float(right_segment["Low"].min())
    shoulders_aligned = abs(left_shoulder - right_shoulder) / max(left_shoulder, 1e-9) <= shoulder_tolerance_pct
    deeper_head = head_low < min(left_shoulder, right_shoulder) * (1.0 - head_depth_pct)
    right_shoulder_respected = right_shoulder > head_low

    left_peak = float(left_segment["High"].max())
    right_peak = float(right_segment["High"].max())
    neckline = min(left_peak, right_peak)
    reclaim_bar = frame.iloc[-2]
    confirm_bar = frame.iloc[-1]
    reclaimed = float(reclaim_bar["Close"]) > neckline or float(confirm_bar["Close"]) > neckline
    held = float(confirm_bar["Low"]) >= min(float(reclaim_bar["Low"]), right_shoulder)
    return bool(shoulders_aligned and deeper_head and right_shoulder_respected and reclaimed and held)


def is_bull_trap_breakout_failure(
    frame: pd.DataFrame,
    *,
    resistance_window: int = 8,
    tolerance_pct: float = 0.0,
) -> bool:
    if len(frame) < 3:
        return False
    prior = frame.iloc[:-2]
    resistance = resistance_level(prior, window=resistance_window)
    if resistance is None:
        return False
    breakout_bar = frame.iloc[-2]
    failure_bar = frame.iloc[-1]
    broke_out = float(breakout_bar["Close"]) > resistance * (1.0 + tolerance_pct)
    failed = float(failure_bar["Close"]) < resistance and float(failure_bar["Low"]) < float(breakout_bar["Low"])
    return bool(broke_out and failed)


def is_double_top_neckline_failure(
    frame: pd.DataFrame,
    *,
    base_window: int = 10,
    top_tolerance_pct: float = 0.03,
    close_tolerance_pct: float = 0.003,
) -> bool:
    if len(frame) < 7:
        return False
    base = _tail(frame.iloc[:-1], base_window)
    if len(base) < 6:
        return False
    first_half = base.iloc[: len(base) // 2]
    second_half = base.iloc[len(base) // 2 :]
    if first_half.empty or second_half.empty:
        return False

    first_top = float(first_half["High"].max())
    second_top = float(second_half["High"].max())
    tops_aligned = abs(first_top - second_top) / max(first_top, 1e-9) <= top_tolerance_pct
    neckline_slice = base.iloc[max((len(base) // 2) - 1, 0) :]
    neckline = float(neckline_slice["Low"].min())
    latest_close = float(frame.iloc[-1]["Close"])
    latest_low = float(frame.iloc[-1]["Low"])
    broke_neckline = latest_close <= neckline * (1.0 + close_tolerance_pct) and latest_low < neckline
    return bool(tops_aligned and broke_neckline)


def is_symmetrical_triangle_breakout(
    frame: pd.DataFrame,
    *,
    window: int = 8,
    tolerance_pct: float = 0.0,
) -> bool:
    if len(frame) < window + 1:
        return False
    setup = frame.iloc[:-1]
    if not is_symmetrical_triangle(setup, window=window):
        return False
    boundary_segment = _tail(setup, window).tail(max(window // 2, 3))
    if boundary_segment.empty:
        return False
    resistance = float(boundary_segment["High"].max())
    trigger_bar = frame.iloc[-1]
    return bool(float(trigger_bar["Close"]) > resistance * (1.0 + tolerance_pct))


def intraday_trendline_break_reversal(
    frame: pd.DataFrame,
    *,
    window: int = 6,
    tolerance_pct: float = 0.0,
) -> bool:
    if len(frame) < window + 1:
        return False
    setup = _tail(frame.iloc[:-1], window)
    if len(setup) < window or not has_descending_highs(setup, window=window):
        return False
    trigger_bar = frame.iloc[-1]
    recent_boundary = float(setup.tail(max(window // 2, 3))["High"].max())
    return bool(float(trigger_bar["Close"]) > recent_boundary * (1.0 + tolerance_pct))
