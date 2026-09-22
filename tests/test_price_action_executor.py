from __future__ import annotations

import pandas as pd

from core.price_action.executor import evaluate_price_action_catalog, evaluate_price_action_strategy
from core.price_action.models import PriceActionSignalType, PriceActionStrategyFamily


def _frame(rows: list[dict[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close", "Volume"])


def _intraday_frame(rows: list[dict[str, float]], *, start: str = "2026-02-10 10:00") -> pd.DataFrame:
    frame = _frame(rows)
    frame.index = pd.date_range(start, periods=len(frame), freq="5min")
    return frame


def test_ascending_triangle_breakout_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.8, "Low": 9.2, "Close": 10.2, "Volume": 1000},
            {"Open": 10.1, "High": 10.9, "Low": 9.4, "Close": 10.3, "Volume": 1000},
            {"Open": 10.3, "High": 11.0, "Low": 9.6, "Close": 10.4, "Volume": 1000},
            {"Open": 10.4, "High": 10.95, "Low": 9.8, "Close": 10.5, "Volume": 1000},
            {"Open": 10.5, "High": 10.98, "Low": 10.0, "Close": 10.6, "Volume": 1000},
            {"Open": 10.6, "High": 11.0, "Low": 10.2, "Close": 10.7, "Volume": 1000},
            {"Open": 10.7, "High": 11.1, "Low": 10.5, "Close": 11.2, "Volume": 2500},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="ascending_triangle_breakout", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.timeframe_family == PriceActionStrategyFamily.SWING
    assert signal.entry_price == 11.2


def test_intraday_strategy_blocks_when_intraday_data_is_unavailable():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.4, "Low": 9.9, "Close": 10.2, "Volume": 1000},
            {"Open": 10.2, "High": 10.5, "Low": 10.0, "Close": 10.3, "Volume": 1200},
            {"Open": 10.3, "High": 10.6, "Low": 10.1, "Close": 10.5, "Volume": 1400},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="intraday_bullish_channel_reclaim", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BLOCKED
    assert signal.avoidance_flags == ("INTRADAY_DATA_UNAVAILABLE",)


def test_intraday_support_reclaim_bullish_confirmation_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 10.6, "High": 10.7, "Low": 10.2, "Close": 10.3, "Volume": 1100},
            {"Open": 10.3, "High": 10.45, "Low": 10.05, "Close": 10.15, "Volume": 1100},
            {"Open": 10.15, "High": 10.35, "Low": 9.95, "Close": 10.05, "Volume": 1100},
            {"Open": 10.06, "High": 10.15, "Low": 9.9, "Close": 10.08, "Volume": 1200},
            {"Open": 10.08, "High": 10.22, "Low": 9.96, "Close": 10.18, "Volume": 1400},
            {"Open": 10.18, "High": 10.42, "Low": 10.1, "Close": 10.4, "Volume": 1800},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_support_reclaim_bullish_confirmation",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Intraday Support Reclaim With Bullish Confirmation"


def test_intraday_resistance_break_retest_reentry_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.2, "Low": 9.95, "Close": 10.1, "Volume": 1000},
            {"Open": 10.1, "High": 10.25, "Low": 10.0, "Close": 10.12, "Volume": 1000},
            {"Open": 10.12, "High": 10.28, "Low": 10.02, "Close": 10.14, "Volume": 1000},
            {"Open": 10.14, "High": 10.42, "Low": 10.1, "Close": 10.38, "Volume": 1500},
            {"Open": 10.38, "High": 10.4, "Low": 10.24, "Close": 10.3, "Volume": 1300},
            {"Open": 10.3, "High": 10.5, "Low": 10.28, "Close": 10.48, "Volume": 1700},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_resistance_break_retest_reentry",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Intraday Resistance Break Retest Re-entry"


def test_intraday_higher_high_higher_low_continuation_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.2, "Low": 9.95, "Close": 10.1, "Volume": 1000},
            {"Open": 10.1, "High": 10.35, "Low": 10.0, "Close": 10.28, "Volume": 1100},
            {"Open": 10.28, "High": 10.32, "Low": 10.08, "Close": 10.15, "Volume": 1000},
            {"Open": 10.15, "High": 10.42, "Low": 10.12, "Close": 10.36, "Volume": 1200},
            {"Open": 10.36, "High": 10.38, "Low": 10.2, "Close": 10.26, "Volume": 1100},
            {"Open": 10.26, "High": 10.55, "Low": 10.24, "Close": 10.52, "Volume": 1700},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_higher_high_higher_low_continuation",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Intraday Higher-High Higher-Low Continuation"


def test_intraday_selling_trap_reclaim_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 10.5, "High": 10.55, "Low": 10.25, "Close": 10.35, "Volume": 1000},
            {"Open": 10.35, "High": 10.42, "Low": 10.15, "Close": 10.22, "Volume": 1000},
            {"Open": 10.22, "High": 10.3, "Low": 10.02, "Close": 10.12, "Volume": 1000},
            {"Open": 10.1, "High": 10.16, "Low": 9.92, "Close": 9.98, "Volume": 1400},
            {"Open": 10.0, "High": 10.24, "Low": 9.98, "Close": 10.22, "Volume": 1800},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_selling_trap_reclaim",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Intraday Selling Trap Reclaim"


def test_intraday_trendline_break_reversal_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 10.5, "High": 10.7, "Low": 10.3, "Close": 10.55, "Volume": 1000},
            {"Open": 10.55, "High": 10.65, "Low": 10.28, "Close": 10.48, "Volume": 1000},
            {"Open": 10.48, "High": 10.58, "Low": 10.24, "Close": 10.4, "Volume": 1000},
            {"Open": 10.4, "High": 10.5, "Low": 10.22, "Close": 10.36, "Volume": 1000},
            {"Open": 10.36, "High": 10.44, "Low": 10.18, "Close": 10.3, "Volume": 1000},
            {"Open": 10.3, "High": 10.48, "Low": 10.26, "Close": 10.46, "Volume": 1700},
            {"Open": 10.46, "High": 10.62, "Low": 10.4, "Close": 10.6, "Volume": 1900},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_trendline_break_reversal",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Trendline Break Intraday Reversal"


def test_intraday_support_reclaim_bullish_confirmation_rejects_weak_trigger_bar():
    frame = _frame(
        [
            {"Open": 10.6, "High": 10.7, "Low": 10.2, "Close": 10.3, "Volume": 1100},
            {"Open": 10.3, "High": 10.45, "Low": 10.05, "Close": 10.15, "Volume": 1100},
            {"Open": 10.15, "High": 10.35, "Low": 9.95, "Close": 10.05, "Volume": 1100},
            {"Open": 10.06, "High": 10.15, "Low": 9.9, "Close": 10.08, "Volume": 1200},
            {"Open": 10.08, "High": 10.22, "Low": 9.96, "Close": 10.18, "Volume": 1400},
            {"Open": 10.18, "High": 10.42, "Low": 10.1, "Close": 10.2, "Volume": 1200},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_support_reclaim_bullish_confirmation",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is None


def test_intraday_resistance_break_retest_reentry_rejects_low_relative_volume():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.2, "Low": 9.95, "Close": 10.1, "Volume": 1200},
            {"Open": 10.1, "High": 10.25, "Low": 10.0, "Close": 10.12, "Volume": 1200},
            {"Open": 10.12, "High": 10.28, "Low": 10.02, "Close": 10.14, "Volume": 1200},
            {"Open": 10.14, "High": 10.42, "Low": 10.1, "Close": 10.38, "Volume": 1500},
            {"Open": 10.38, "High": 10.4, "Low": 10.24, "Close": 10.3, "Volume": 1300},
            {"Open": 10.3, "High": 10.5, "Low": 10.28, "Close": 10.48, "Volume": 1200},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_resistance_break_retest_reentry",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is None


def test_intraday_resistance_break_retest_reentry_rejects_weak_breakout_close():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.2, "Low": 9.95, "Close": 10.1, "Volume": 1000},
            {"Open": 10.1, "High": 10.25, "Low": 10.0, "Close": 10.12, "Volume": 1000},
            {"Open": 10.12, "High": 10.28, "Low": 10.02, "Close": 10.14, "Volume": 1000},
            {"Open": 10.14, "High": 10.42, "Low": 10.1, "Close": 10.31, "Volume": 1500},
            {"Open": 10.31, "High": 10.36, "Low": 10.26, "Close": 10.3, "Volume": 1300},
            {"Open": 10.3, "High": 10.5, "Low": 10.28, "Close": 10.48, "Volume": 1700},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_resistance_break_retest_reentry",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is None


def test_intraday_resistance_break_retest_reentry_rejects_sloppy_retest_close():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.2, "Low": 9.95, "Close": 10.1, "Volume": 1000},
            {"Open": 10.1, "High": 10.25, "Low": 10.0, "Close": 10.12, "Volume": 1000},
            {"Open": 10.12, "High": 10.28, "Low": 10.02, "Close": 10.14, "Volume": 1000},
            {"Open": 10.14, "High": 10.42, "Low": 10.1, "Close": 10.38, "Volume": 1500},
            {"Open": 10.38, "High": 10.4, "Low": 10.24, "Close": 10.27, "Volume": 1300},
            {"Open": 10.27, "High": 10.5, "Low": 10.25, "Close": 10.48, "Volume": 1700},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_resistance_break_retest_reentry",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is None


def test_intraday_trendline_break_reversal_rejects_marginal_clearance():
    frame = _frame(
        [
            {"Open": 10.5, "High": 10.7, "Low": 10.3, "Close": 10.55, "Volume": 1000},
            {"Open": 10.55, "High": 10.65, "Low": 10.28, "Close": 10.48, "Volume": 1000},
            {"Open": 10.48, "High": 10.58, "Low": 10.24, "Close": 10.4, "Volume": 1000},
            {"Open": 10.4, "High": 10.5, "Low": 10.22, "Close": 10.36, "Volume": 1000},
            {"Open": 10.36, "High": 10.44, "Low": 10.18, "Close": 10.3, "Volume": 1000},
            {"Open": 10.3, "High": 10.48, "Low": 10.26, "Close": 10.46, "Volume": 1700},
            {"Open": 10.46, "High": 10.62, "Low": 10.4, "Close": 10.5, "Volume": 1900},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_trendline_break_reversal",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is None


def test_intraday_resistance_break_retest_reentry_rejects_late_session_signal():
    frame = _intraday_frame(
        [
            {"Open": 10.0, "High": 10.2, "Low": 9.95, "Close": 10.1, "Volume": 1000},
            {"Open": 10.1, "High": 10.25, "Low": 10.0, "Close": 10.12, "Volume": 1000},
            {"Open": 10.12, "High": 10.28, "Low": 10.02, "Close": 10.14, "Volume": 1000},
            {"Open": 10.14, "High": 10.42, "Low": 10.1, "Close": 10.38, "Volume": 1500},
            {"Open": 10.38, "High": 10.4, "Low": 10.24, "Close": 10.3, "Volume": 1300},
            {"Open": 10.3, "High": 10.5, "Low": 10.28, "Close": 10.48, "Volume": 1700},
        ],
        start="2026-02-10 13:20",
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_resistance_break_retest_reentry",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is None


def test_intraday_selling_trap_reclaim_rejects_weak_ticker_quality():
    frame = _intraday_frame(
        [
            {"Open": 10.5, "High": 10.55, "Low": 10.25, "Close": 10.35, "Volume": 700},
            {"Open": 10.35, "High": 10.42, "Low": 10.15, "Close": 10.22, "Volume": 700},
            {"Open": 10.22, "High": 10.3, "Low": 10.02, "Close": 10.12, "Volume": 700},
            {"Open": 10.1, "High": 10.16, "Low": 9.92, "Close": 9.98, "Volume": 950},
            {"Open": 10.0, "High": 10.24, "Low": 9.98, "Close": 10.22, "Volume": 1100},
        ]
    )

    signal = evaluate_price_action_strategy(
        frame,
        strategy_id="intraday_selling_trap_reclaim",
        ticker="COMI",
        intraday_data_available=True,
    )

    assert signal is None


def test_failed_breakout_warning_emits_warning_only_signal():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.4, "Low": 9.8, "Close": 10.2, "Volume": 1000},
            {"Open": 10.2, "High": 10.5, "Low": 10.0, "Close": 10.3, "Volume": 1000},
            {"Open": 10.3, "High": 10.55, "Low": 10.1, "Close": 10.35, "Volume": 1000},
            {"Open": 10.35, "High": 10.6, "Low": 10.2, "Close": 10.4, "Volume": 1000},
            {"Open": 10.4, "High": 10.65, "Low": 10.25, "Close": 10.45, "Volume": 1000},
            {"Open": 10.45, "High": 10.7, "Low": 10.3, "Close": 10.5, "Volume": 1000},
            {"Open": 10.5, "High": 10.9, "Low": 10.45, "Close": 10.85, "Volume": 1500},
            {"Open": 10.82, "High": 10.84, "Low": 10.3, "Close": 10.35, "Volume": 1500},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="failed_breakout_warning", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.WARNING_ONLY
    assert "Failed breakout rejection" in signal.warnings


def test_double_bottom_neckline_reclaim_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 11.4, "High": 11.6, "Low": 11.0, "Close": 11.2, "Volume": 1000},
            {"Open": 11.2, "High": 11.3, "Low": 10.8, "Close": 10.9, "Volume": 1000},
            {"Open": 10.9, "High": 11.0, "Low": 10.3, "Close": 10.45, "Volume": 1000},
            {"Open": 10.5, "High": 10.8, "Low": 10.2, "Close": 10.25, "Volume": 1000},
            {"Open": 10.25, "High": 10.9, "Low": 10.1, "Close": 10.65, "Volume": 1000},
            {"Open": 10.6, "High": 11.0, "Low": 10.4, "Close": 10.9, "Volume": 1000},
            {"Open": 10.9, "High": 11.2, "Low": 10.2, "Close": 10.35, "Volume": 1200},
            {"Open": 10.35, "High": 11.3, "Low": 10.3, "Close": 11.25, "Volume": 2000},
            {"Open": 11.2, "High": 11.45, "Low": 11.0, "Close": 11.3, "Volume": 1800},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="double_bottom_neckline_reclaim", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Double Bottom Neckline Reclaim"


def test_inverse_head_and_shoulders_reclaim_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 12.2, "High": 12.4, "Low": 11.6, "Close": 11.8, "Volume": 1000},
            {"Open": 11.8, "High": 12.0, "Low": 11.2, "Close": 11.3, "Volume": 1000},
            {"Open": 11.3, "High": 11.9, "Low": 11.0, "Close": 11.6, "Volume": 1000},
            {"Open": 11.6, "High": 11.8, "Low": 10.7, "Close": 10.9, "Volume": 1000},
            {"Open": 10.9, "High": 11.7, "Low": 10.6, "Close": 11.5, "Volume": 1000},
            {"Open": 11.5, "High": 11.7, "Low": 11.1, "Close": 11.3, "Volume": 1000},
            {"Open": 11.3, "High": 11.8, "Low": 11.0, "Close": 11.55, "Volume": 1000},
            {"Open": 11.55, "High": 11.95, "Low": 11.3, "Close": 11.85, "Volume": 1300},
            {"Open": 11.86, "High": 12.15, "Low": 11.7, "Close": 12.05, "Volume": 1900},
            {"Open": 12.02, "High": 12.2, "Low": 11.9, "Close": 12.12, "Volume": 1800},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="inverse_head_and_shoulders_reclaim", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Inverse Head And Shoulders Reclaim"


def test_inside_bar_trend_breakout_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.5, "Low": 9.6, "Close": 10.1, "Volume": 1000},
            {"Open": 10.1, "High": 10.7, "Low": 9.8, "Close": 10.3, "Volume": 1000},
            {"Open": 10.3, "High": 10.9, "Low": 10.0, "Close": 10.5, "Volume": 1000},
            {"Open": 10.5, "High": 11.1, "Low": 10.2, "Close": 10.7, "Volume": 1000},
            {"Open": 10.7, "High": 11.3, "Low": 10.4, "Close": 10.9, "Volume": 1000},
            {"Open": 10.9, "High": 11.5, "Low": 10.6, "Close": 11.1, "Volume": 1000},
            {"Open": 11.05, "High": 11.4, "Low": 10.9, "Close": 11.15, "Volume": 900},
            {"Open": 11.12, "High": 11.7, "Low": 11.0, "Close": 11.65, "Volume": 1800},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="inside_bar_trend_breakout", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Inside Bar Trend Breakout"


def test_fakey_false_break_reversal_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 10.8, "High": 11.0, "Low": 10.3, "Close": 10.5, "Volume": 1200},
            {"Open": 10.5, "High": 10.8, "Low": 10.2, "Close": 10.4, "Volume": 1200},
            {"Open": 10.4, "High": 10.7, "Low": 10.1, "Close": 10.35, "Volume": 1200},
            {"Open": 10.35, "High": 10.6, "Low": 10.0, "Close": 10.25, "Volume": 1200},
            {"Open": 10.25, "High": 10.55, "Low": 10.0, "Close": 10.2, "Volume": 1100},
            {"Open": 10.2, "High": 10.48, "Low": 10.08, "Close": 10.3, "Volume": 1000},
            {"Open": 10.28, "High": 10.35, "Low": 9.9, "Close": 10.18, "Volume": 1500},
            {"Open": 10.22, "High": 10.7, "Low": 10.12, "Close": 10.62, "Volume": 2200},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="fakey_false_break_reversal", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Fakey False-Break Reversal"


def test_support_reclaim_bullish_engulfing_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 11.2, "High": 11.5, "Low": 10.8, "Close": 11.0, "Volume": 1000},
            {"Open": 11.0, "High": 11.2, "Low": 10.6, "Close": 10.8, "Volume": 1000},
            {"Open": 10.8, "High": 11.0, "Low": 10.4, "Close": 10.6, "Volume": 1000},
            {"Open": 10.6, "High": 10.9, "Low": 10.3, "Close": 10.5, "Volume": 1000},
            {"Open": 10.5, "High": 10.8, "Low": 10.2, "Close": 10.4, "Volume": 1000},
            {"Open": 10.4, "High": 10.7, "Low": 10.1, "Close": 10.3, "Volume": 1000},
            {"Open": 10.35, "High": 10.42, "Low": 10.12, "Close": 10.18, "Volume": 1200},
            {"Open": 10.14, "High": 10.65, "Low": 10.1, "Close": 10.55, "Volume": 1800},
            {"Open": 10.58, "High": 10.95, "Low": 10.5, "Close": 10.9, "Volume": 1700},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="support_reclaim_bullish_engulfing", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Support Reclaim With Bullish Engulfing"


def test_symmetrical_triangle_expansion_emits_buy_signal():
    frame = _frame(
        [
            {"Open": 12.0, "High": 12.6, "Low": 10.4, "Close": 11.6, "Volume": 1000},
            {"Open": 11.6, "High": 12.4, "Low": 10.6, "Close": 11.5, "Volume": 1000},
            {"Open": 11.5, "High": 12.2, "Low": 10.8, "Close": 11.45, "Volume": 1000},
            {"Open": 11.45, "High": 12.0, "Low": 11.0, "Close": 11.4, "Volume": 1000},
            {"Open": 11.4, "High": 11.8, "Low": 11.2, "Close": 11.45, "Volume": 1000},
            {"Open": 11.45, "High": 11.7, "Low": 11.3, "Close": 11.5, "Volume": 1000},
            {"Open": 11.5, "High": 11.65, "Low": 11.4, "Close": 11.52, "Volume": 1000},
            {"Open": 11.52, "High": 11.6, "Low": 11.46, "Close": 11.55, "Volume": 1000},
            {"Open": 11.56, "High": 12.1, "Low": 11.5, "Close": 12.05, "Volume": 1800},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="symmetrical_triangle_expansion", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.BUY
    assert signal.setup_name == "Symmetrical Triangle Expansion"


def test_bull_trap_breakout_warning_emits_warning_only_signal():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.4, "Low": 9.8, "Close": 10.2, "Volume": 1000},
            {"Open": 10.2, "High": 10.5, "Low": 10.0, "Close": 10.3, "Volume": 1000},
            {"Open": 10.3, "High": 10.55, "Low": 10.1, "Close": 10.35, "Volume": 1000},
            {"Open": 10.35, "High": 10.6, "Low": 10.2, "Close": 10.4, "Volume": 1000},
            {"Open": 10.4, "High": 10.65, "Low": 10.25, "Close": 10.45, "Volume": 1000},
            {"Open": 10.45, "High": 10.7, "Low": 10.3, "Close": 10.5, "Volume": 1000},
            {"Open": 10.5, "High": 10.95, "Low": 10.45, "Close": 10.88, "Volume": 1700},
            {"Open": 10.86, "High": 10.9, "Low": 10.32, "Close": 10.34, "Volume": 1800},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="bull_trap_breakout_warning", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.WARNING_ONLY
    assert "Bull trap breakout failure" in signal.warnings


def test_double_top_neckline_failure_emits_warning_only_signal():
    frame = _frame(
        [
            {"Open": 10.4, "High": 10.8, "Low": 10.1, "Close": 10.6, "Volume": 1000},
            {"Open": 10.6, "High": 11.0, "Low": 10.3, "Close": 10.9, "Volume": 1000},
            {"Open": 10.9, "High": 11.25, "Low": 10.6, "Close": 11.1, "Volume": 1000},
            {"Open": 11.1, "High": 11.18, "Low": 10.5, "Close": 10.7, "Volume": 1000},
            {"Open": 10.7, "High": 10.95, "Low": 10.4, "Close": 10.85, "Volume": 1000},
            {"Open": 10.85, "High": 11.22, "Low": 10.55, "Close": 11.08, "Volume": 1000},
            {"Open": 11.08, "High": 11.15, "Low": 10.35, "Close": 10.42, "Volume": 1700},
        ]
    )

    signal = evaluate_price_action_strategy(frame, strategy_id="double_top_neckline_failure", ticker="COMI")

    assert signal is not None
    assert signal.signal_type == PriceActionSignalType.WARNING_ONLY
    assert "Double top neckline failure" in signal.warnings


def test_catalog_evaluation_filters_to_requested_family():
    frame = _frame(
        [
            {"Open": 10.0, "High": 10.8, "Low": 9.2, "Close": 10.2, "Volume": 1000},
            {"Open": 10.1, "High": 10.9, "Low": 9.4, "Close": 10.3, "Volume": 1000},
            {"Open": 10.3, "High": 11.0, "Low": 9.6, "Close": 10.4, "Volume": 1000},
            {"Open": 10.4, "High": 10.95, "Low": 9.8, "Close": 10.5, "Volume": 1000},
            {"Open": 10.5, "High": 10.98, "Low": 10.0, "Close": 10.6, "Volume": 1000},
            {"Open": 10.6, "High": 11.0, "Low": 10.2, "Close": 10.7, "Volume": 1000},
            {"Open": 10.7, "High": 11.1, "Low": 10.5, "Close": 11.2, "Volume": 2500},
        ]
    )

    signals = evaluate_price_action_catalog(
        frame,
        ticker="COMI",
        families=(PriceActionStrategyFamily.SWING,),
        include_warning_only=False,
    )

    assert signals
    assert all(signal.timeframe_family == PriceActionStrategyFamily.SWING for signal in signals)
