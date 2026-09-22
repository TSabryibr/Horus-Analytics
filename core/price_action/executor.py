from __future__ import annotations
"""Latest-bar evaluation for the EGX price-action catalog."""


from typing import Iterable

import pandas as pd

from .catalog import get_price_action_strategy, list_price_action_strategies
from .indicators import add_price_action_features, validate_ohlcv_frame
from .models import PriceActionSignal, PriceActionSignalType, PriceActionStrategyFamily
from . import patterns, warnings
from .scoring import build_signal_score


INTRADAY_TARGETED_REL_VOL_MIN = 1.15
INTRADAY_TRIGGER_CLOSE_FRACTION_MIN = 0.55
INTRADAY_CLEARANCE_ATR_MULTIPLIER = 0.10
INTRADAY_STOP_BUFFER_ATR_MULTIPLIER = 0.25
INTRADAY_ENHANCED_AVG_TURNOVER_MIN = 11_000.0
INTRADAY_ENHANCED_BAR_TURNOVER_MIN = 12_000.0


def _latest(frame: pd.DataFrame) -> pd.Series:
    return frame.iloc[-1]


def _liquidity_ok(row: pd.Series) -> bool:
    return float(row.get("Avg_Turnover", 0.0) or 0.0) >= 1_000.0


def _close_position_in_range(row: pd.Series) -> float:
    high = float(row.get("High", 0.0) or 0.0)
    low = float(row.get("Low", 0.0) or 0.0)
    close = float(row.get("Close", 0.0) or 0.0)
    bar_range = max(high - low, 1e-9)
    return (close - low) / bar_range


def _intraday_trigger_quality_ok(
    row: pd.Series,
    *,
    relative_volume: float,
    liquidity_ok: bool,
    min_rel_volume: float = INTRADAY_TARGETED_REL_VOL_MIN,
    min_close_fraction: float = INTRADAY_TRIGGER_CLOSE_FRACTION_MIN,
) -> bool:
    return bool(
        liquidity_ok
        and relative_volume >= min_rel_volume
        and _close_position_in_range(row) >= min_close_fraction
    )


def _cleared_level(close: float, level: float, atr: float, *, clearance_atr: float = INTRADAY_CLEARANCE_ATR_MULTIPLIER) -> bool:
    return close >= level + (atr * clearance_atr)


def _intraday_stop_from_structure(close: float, structure_level: float, atr: float) -> float:
    buffered_structure = structure_level - (atr * INTRADAY_STOP_BUFFER_ATR_MULTIPLIER)
    return min(close - (atr * 0.7), buffered_structure)


def _preferred_intraday_session_ok(frame: pd.DataFrame) -> bool:
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.empty:
        return True
    timestamp = pd.Timestamp(frame.index[-1])
    minutes_since_midnight = (timestamp.hour * 60) + timestamp.minute
    return 10 * 60 + 15 <= minutes_since_midnight <= 13 * 60 + 30


def _enhanced_intraday_ticker_quality_ok(
    row: pd.Series,
    *,
    min_avg_turnover: float = INTRADAY_ENHANCED_AVG_TURNOVER_MIN,
    min_bar_turnover: float = INTRADAY_ENHANCED_BAR_TURNOVER_MIN,
) -> bool:
    avg_turnover = float(row.get("Avg_Turnover", 0.0) or 0.0)
    bar_turnover = float(row.get("Turnover", 0.0) or 0.0)
    return bool(avg_turnover >= min_avg_turnover and bar_turnover >= min_bar_turnover)


def _buy_signal(
    *,
    ticker: str,
    strategy_id: str,
    setup_name: str,
    family: PriceActionStrategyFamily,
    entry_price: float,
    stop_loss: float,
    target_1: float,
    target_2: float | None,
    confirmations: Iterable[str],
    warning_labels: Iterable[str],
    explanation: str,
    liquidity_ok: bool,
    relative_volume: float,
) -> PriceActionSignal:
    warning_tuple = tuple(warning_labels)
    return PriceActionSignal(
        signal_type=PriceActionSignalType.BUY if not warning_tuple else PriceActionSignalType.BUY_CANDIDATE,
        timeframe_family=family,
        ticker=ticker,
        setup_name=setup_name,
        strategy_id=strategy_id,
        explanation=explanation,
        score=float(
            build_signal_score(
                confirmations=len(tuple(confirmations)),
                warnings=len(warning_tuple),
                liquidity_ok=liquidity_ok,
                relative_volume=relative_volume,
            )
        ),
        entry_price=entry_price,
        stop_loss=stop_loss,
        target_1=target_1,
        target_2=target_2,
        confirmations=tuple(confirmations),
        warnings=warning_tuple,
        avoidance_flags=(),
    )


def _warning_signal(
    *,
    ticker: str,
    strategy_id: str,
    setup_name: str,
    family: PriceActionStrategyFamily,
    explanation: str,
    warning_label: str,
) -> PriceActionSignal:
    return PriceActionSignal(
        signal_type=PriceActionSignalType.WARNING_ONLY,
        timeframe_family=family,
        ticker=ticker,
        setup_name=setup_name,
        strategy_id=strategy_id,
        explanation=explanation,
        score=25.0,
        warnings=(warning_label,),
    )


def _blocked_intraday_signal(*, ticker: str, strategy_id: str, setup_name: str) -> PriceActionSignal:
    return PriceActionSignal(
        signal_type=PriceActionSignalType.BLOCKED,
        timeframe_family=PriceActionStrategyFamily.INTRADAY,
        ticker=ticker,
        setup_name=setup_name,
        strategy_id=strategy_id,
        explanation="Intraday EGX data is required before this setup can be evaluated.",
        score=0.0,
        warnings=("Intraday data unavailable",),
        avoidance_flags=("INTRADAY_DATA_UNAVAILABLE",),
    )


def evaluate_price_action_strategy(
    frame: pd.DataFrame,
    *,
    strategy_id: str,
    ticker: str,
    intraday_data_available: bool = False,
) -> PriceActionSignal | None:
    validate_ohlcv_frame(frame)
    strategy = get_price_action_strategy(strategy_id)
    if strategy is None:
        raise ValueError(f"unknown price-action strategy: {strategy_id}")
    if strategy.family is PriceActionStrategyFamily.INTRADAY and not intraday_data_available:
        return _blocked_intraday_signal(ticker=ticker, strategy_id=strategy.strategy_id, setup_name=strategy.display_name)

    enriched = add_price_action_features(frame)
    row = _latest(enriched)
    close = float(row["Close"])
    atr = max(float(row.get("ATR", 0.0) or 0.0), 0.01)
    rel_vol = float(row.get("Rel_Volume", 0.0) or 0.0)
    liquidity_ok = _liquidity_ok(row)

    if strategy_id == "ascending_triangle_breakout":
        if patterns.is_recent_breakout(enriched, window=10) and patterns.has_rising_lows(enriched, window=6) and rel_vol >= 1.0:
            stop = close - atr
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 1.5),
                target_2=close + (atr * 2.5),
                confirmations=("Resistance cleared", "Lows kept rising", "Relative volume confirmed"),
                warning_labels=(),
                explanation="Price cleared resistance after rising lows with supportive participation.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "bullish_channel_breakout":
        if patterns.has_descending_highs(enriched.iloc[:-1], window=6) and patterns.is_recent_breakout(enriched, window=6):
            stop = close - atr
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 1.5),
                target_2=close + (atr * 2.2),
                confirmations=("Channel pressure ended", "Breakout close held"),
                warning_labels=(),
                explanation="The short-term downward channel resolved upward and produced a breakout close.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "box_consolidation_breakout":
        if patterns.is_box_consolidation(enriched, window=8) and patterns.is_recent_breakout(enriched, window=8):
            stop = close - atr
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 1.5),
                target_2=close + (atr * 2.0),
                confirmations=("Tight box formed", "Higher high printed"),
                warning_labels=(),
                explanation="A tight consolidation resolved upward with a clean higher-high breakout.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "trend_structure_continuation":
        if patterns.is_higher_high_higher_low(enriched, window=6) and patterns.is_recent_breakout(enriched, window=5):
            stop = close - (atr * 1.5)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 2.0),
                target_2=close + (atr * 3.0),
                confirmations=("Trend structure intact", "Prior swing high reclaimed"),
                warning_labels=(),
                explanation="The higher-high higher-low sequence stayed intact and continuation triggered above prior structure.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "double_bottom_neckline_reclaim":
        if patterns.is_double_bottom_neckline_reclaim(enriched):
            base_low = float(enriched.iloc[:-1].tail(10)["Low"].min())
            stop = min(close - (atr * 1.25), base_low)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 2.0),
                target_2=close + (atr * 3.0),
                confirmations=("Two aligned lows held", "Neckline reclaimed", "Reclaim zone held"),
                warning_labels=(),
                explanation="A double-bottom style base reclaimed the neckline and held above it, signaling a slower bullish reversal.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "inverse_head_and_shoulders_reclaim":
        if patterns.is_inverse_head_and_shoulders_reclaim(enriched):
            shoulder_support = float(enriched.iloc[:-1].tail(11)["Low"].min())
            stop = min(close - (atr * 1.25), shoulder_support)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 2.1),
                target_2=close + (atr * 3.2),
                confirmations=("Three-trough base formed", "Head stayed below both shoulders", "Neckline reclaimed"),
                warning_labels=(),
                explanation="A broader inverse head-and-shoulders base reclaimed the neckline and held, signaling a slower bullish reversal.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "inside_bar_trend_breakout":
        if patterns.has_prior_uptrend(enriched.iloc[:-1], lookback=6) and patterns.is_inside_bar_breakout(enriched):
            inside_bar_low = float(enriched.iloc[-2]["Low"])
            stop = min(close - atr, inside_bar_low)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 1.5),
                target_2=close + (atr * 2.3),
                confirmations=("Prior uptrend intact", "Inside bar compressed", "Mother bar high reclaimed"),
                warning_labels=(),
                explanation="A daily inside bar compressed after an uptrend and then broke upward through the mother bar high.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "fakey_false_break_reversal":
        if patterns.is_fakey_bullish_reversal(enriched):
            false_break_low = float(enriched.iloc[-2]["Low"])
            stop = min(close - atr, false_break_low)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 1.7),
                target_2=close + (atr * 2.5),
                confirmations=("False break rejected", "Support reclaimed", "Structure flipped back up"),
                warning_labels=(),
                explanation="Price false-broke lower, snapped back above the structure, and confirmed the reversal through local resistance.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "support_reclaim_bullish_engulfing":
        if patterns.support_reclaim_with_engulfing(enriched):
            reversal_low = float(enriched.iloc[-2:]["Low"].min())
            stop = min(close - atr, reversal_low)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 1.5),
                target_2=close + (atr * 2.2),
                confirmations=("Support held", "Bullish engulfing printed", "Local swing high reclaimed"),
                warning_labels=(),
                explanation="Support held, a bullish engulfing reversal appeared, and price reclaimed nearby structure instead of fading.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "symmetrical_triangle_expansion":
        if patterns.is_symmetrical_triangle_breakout(enriched) and rel_vol >= 0.9:
            recent_support = float(enriched.iloc[:-1].tail(8)["Low"].min())
            stop = min(close - atr, recent_support)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 1.6),
                target_2=close + (atr * 2.4),
                confirmations=("Triangle compressed", "Upper boundary cleared", "Participation stayed supportive"),
                warning_labels=(),
                explanation="Converging highs and lows compressed price, then the triangle resolved upward through resistance.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "intraday_support_reclaim_bullish_confirmation":
        reclaim_level = float(enriched.iloc[-2]["High"])
        if (
            patterns.intraday_support_reclaim_confirmation(enriched)
            and _intraday_trigger_quality_ok(row, relative_volume=rel_vol, liquidity_ok=liquidity_ok)
            and _cleared_level(close, reclaim_level, atr)
        ):
            reclaim_low = float(enriched.iloc[-2:]["Low"].min())
            stop = _intraday_stop_from_structure(close, reclaim_low, atr)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + atr,
                target_2=close + (atr * 1.5),
                confirmations=("Support held intraday", "Reclaim bar recovered structure", "Follow-through confirmed"),
                warning_labels=(),
                explanation="Intraday support was reclaimed and the recovery bar pushed through nearby structure instead of fading.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "intraday_resistance_break_retest_reentry":
        resumed_level = float(enriched.iloc[-2]["High"])
        if (
            patterns.intraday_breakout_retest_reentry(enriched)
            and _intraday_trigger_quality_ok(row, relative_volume=rel_vol, liquidity_ok=liquidity_ok)
            and _preferred_intraday_session_ok(enriched)
            and _enhanced_intraday_ticker_quality_ok(row)
            and _cleared_level(close, resumed_level, atr)
        ):
            retest_low = float(enriched.iloc[-2]["Low"])
            stop = _intraday_stop_from_structure(close, retest_low, atr)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 0.95),
                target_2=close + (atr * 1.45),
                confirmations=("Resistance broke cleanly", "Retest held", "Re-entry bar resumed upward"),
                warning_labels=(),
                explanation="The breakout held on retest and the next bar resumed upward from the reclaimed level.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "intraday_higher_high_higher_low_continuation":
        prior_pivot_high = float(enriched.iloc[:-1].tail(5)["High"].iloc[:-1].max())
        if (
            patterns.intraday_higher_high_higher_low_continuation(enriched)
            and _intraday_trigger_quality_ok(row, relative_volume=rel_vol, liquidity_ok=liquidity_ok)
            and _cleared_level(close, prior_pivot_high, atr)
        ):
            recent_higher_low = float(enriched.iloc[:-1].tail(5)["Low"].min())
            stop = _intraday_stop_from_structure(close, recent_higher_low, atr)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + (atr * 0.95),
                target_2=close + (atr * 1.4),
                confirmations=("Higher low stayed intact", "Prior pivot high cleared", "Participation stayed supportive"),
                warning_labels=(),
                explanation="Intraday micro structure stayed constructive and the latest bar continued through the prior pivot high.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "intraday_selling_trap_reclaim":
        reclaimed_level = float(enriched.iloc[-2]["High"])
        if (
            patterns.intraday_selling_trap_reclaim(enriched)
            and _intraday_trigger_quality_ok(row, relative_volume=rel_vol, liquidity_ok=liquidity_ok)
            and _preferred_intraday_session_ok(enriched)
            and _enhanced_intraday_ticker_quality_ok(row)
            and _cleared_level(close, reclaimed_level, atr)
        ):
            failed_break_low = float(enriched.iloc[-2]["Low"])
            stop = _intraday_stop_from_structure(close, failed_break_low, atr)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + atr,
                target_2=close + (atr * 1.5),
                confirmations=("Breakdown failed", "Support was reclaimed", "Trap reversed upward"),
                warning_labels=(),
                explanation="A failed intraday breakdown snapped back through support and reversed the selling trap.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "intraday_trendline_break_reversal":
        break_level = float(enriched.iloc[-2]["High"])
        if (
            patterns.intraday_trendline_break_reversal(enriched)
            and _intraday_trigger_quality_ok(row, relative_volume=rel_vol, liquidity_ok=liquidity_ok)
            and _cleared_level(close, break_level, atr)
        ):
            reversal_low = float(enriched.iloc[-1]["Low"])
            stop = _intraday_stop_from_structure(close, reversal_low, atr)
            return _buy_signal(
                ticker=ticker,
                strategy_id=strategy.strategy_id,
                setup_name=strategy.display_name,
                family=strategy.family,
                entry_price=close,
                stop_loss=stop,
                target_1=close + atr,
                target_2=close + (atr * 1.5),
                confirmations=("Descending pressure eased", "Trendline break confirmed", "Reversal close held"),
                warning_labels=(),
                explanation="The short-term descending intraday structure broke upward and confirmed a local reversal with a closing break.",
                liquidity_ok=liquidity_ok,
                relative_volume=rel_vol,
            )
        return None

    if strategy_id == "descending_triangle_warning" and warnings.detect_descending_triangle_warning(enriched):
        return _warning_signal(
            ticker=ticker,
            strategy_id=strategy.strategy_id,
            setup_name=strategy.display_name,
            family=strategy.family,
            explanation="Price is pressing flat support while highs continue to step down.",
            warning_label="Descending triangle pressure",
        )

    if strategy_id == "rising_wedge_warning" and warnings.detect_rising_wedge_warning(enriched):
        return _warning_signal(
            ticker=ticker,
            strategy_id=strategy.strategy_id,
            setup_name=strategy.display_name,
            family=strategy.family,
            explanation="The advance is narrowing into a wedge, which raises exhaustion risk.",
            warning_label="Rising wedge exhaustion",
        )

    if strategy_id == "failed_breakdown_trap_warning" and warnings.detect_failed_breakdown_trap(enriched):
        return _warning_signal(
            ticker=ticker,
            strategy_id=strategy.strategy_id,
            setup_name=strategy.display_name,
            family=strategy.family,
            explanation="A breakdown failed quickly and the structure was reclaimed.",
            warning_label="Failed breakdown trap",
        )

    if strategy_id == "failed_breakout_warning" and warnings.detect_failed_breakout_warning(enriched):
        return _warning_signal(
            ticker=ticker,
            strategy_id=strategy.strategy_id,
            setup_name=strategy.display_name,
            family=strategy.family,
            explanation="The breakout could not hold above its trigger level and is now a caution signal.",
            warning_label="Failed breakout rejection",
        )

    if strategy_id == "bull_trap_breakout_warning" and warnings.detect_bull_trap_breakout_warning(enriched):
        return _warning_signal(
            ticker=ticker,
            strategy_id=strategy.strategy_id,
            setup_name=strategy.display_name,
            family=strategy.family,
            explanation="An upside breakout failed quickly and late breakout buyers are now exposed.",
            warning_label="Bull trap breakout failure",
        )

    if strategy_id == "double_top_neckline_failure" and warnings.detect_double_top_neckline_failure(enriched):
        return _warning_signal(
            ticker=ticker,
            strategy_id=strategy.strategy_id,
            setup_name=strategy.display_name,
            family=strategy.family,
            explanation="A mature double-top structure has now lost its neckline, which raises distribution and trend-failure risk.",
            warning_label="Double top neckline failure",
        )

    if strategy_id == "reversal_structure_shift_warning" and warnings.detect_reversal_structure_shift(enriched):
        return _warning_signal(
            ticker=ticker,
            strategy_id=strategy.strategy_id,
            setup_name=strategy.display_name,
            family=strategy.family,
            explanation="The prior uptrend has lost structure and failed to maintain support.",
            warning_label="Reversal structure shift",
        )

    if strategy.warning_only:
        return None
    return None


def evaluate_price_action_catalog(
    frame: pd.DataFrame,
    *,
    ticker: str,
    families: tuple[PriceActionStrategyFamily, ...] | None = None,
    include_warning_only: bool = True,
    intraday_data_available: bool = False,
) -> list[PriceActionSignal]:
    selected = list_price_action_strategies(include_warning_only=include_warning_only)
    if families is not None:
        selected = [strategy for strategy in selected if strategy.family in families]

    results: list[PriceActionSignal] = []
    for strategy in selected:
        signal = evaluate_price_action_strategy(
            frame,
            strategy_id=strategy.strategy_id,
            ticker=ticker,
            intraday_data_available=intraday_data_available,
        )
        if signal is not None:
            results.append(signal)
    return results
