from __future__ import annotations

import pytest

from core.price_action import (
    PRICE_ACTION_CATALOG,
    PriceActionSignal,
    PriceActionSignalType,
    PriceActionStrategy,
    PriceActionStrategyFamily,
    PriceActionSourceAttribution,
    get_price_action_strategy,
    list_price_action_strategies,
)


def _source() -> PriceActionSourceAttribution:
    return PriceActionSourceAttribution(
        title="Source",
        filename="source.pdf",
        concept="concept",
    )


def test_intraday_strategies_must_declare_a_data_gate():
    with pytest.raises(ValueError, match="data_gate"):
        PriceActionStrategy(
            strategy_id="test_intraday",
            display_name="Test Intraday",
            family=PriceActionStrategyFamily.INTRADAY,
            summary="summary",
            regime="TEST",
            source_attributions=(_source(),),
            required_data=("intraday_ohlcv",),
            entry_conditions=("condition",),
            confirmation_conditions=("confirm",),
            avoidance_rules=("avoid",),
            exit_rules=("exit",),
            risk_model="risk",
        )


def test_warning_only_strategies_cannot_allow_long_entries():
    with pytest.raises(ValueError, match="warning-only"):
        PriceActionStrategy(
            strategy_id="warning_test",
            display_name="Warning Test",
            family=PriceActionStrategyFamily.SWING,
            summary="summary",
            regime="TEST",
            source_attributions=(_source(),),
            required_data=("daily_ohlcv",),
            entry_conditions=("condition",),
            confirmation_conditions=("confirm",),
            avoidance_rules=("avoid",),
            exit_rules=("exit",),
            risk_model="WARNING_ONLY",
            warning_only=True,
            long_entry_allowed=True,
        )


def test_trade_candidate_signals_require_trade_levels():
    with pytest.raises(ValueError, match="entry_price, stop_loss, target_1"):
        PriceActionSignal(
            signal_type=PriceActionSignalType.BUY_CANDIDATE,
            timeframe_family=PriceActionStrategyFamily.SWING,
            ticker="COMI",
            setup_name="Setup",
            strategy_id="strategy",
            explanation="valid explanation",
        )


def test_warning_only_signals_cannot_include_execution_prices():
    with pytest.raises(ValueError, match="warning-only"):
        PriceActionSignal(
            signal_type=PriceActionSignalType.WARNING_ONLY,
            timeframe_family=PriceActionStrategyFamily.SWING,
            ticker="COMI",
            setup_name="Setup",
            strategy_id="strategy",
            explanation="valid explanation",
            entry_price=10.0,
        )


def test_blocked_signals_require_avoidance_flags():
    with pytest.raises(ValueError, match="avoidance flag"):
        PriceActionSignal(
            signal_type=PriceActionSignalType.BLOCKED,
            timeframe_family=PriceActionStrategyFamily.SWING,
            ticker="COMI",
            setup_name="Setup",
            strategy_id="strategy",
            explanation="blocked for a reason",
        )


def test_catalog_contains_three_families_and_warning_profiles():
    families = {strategy.family for strategy in PRICE_ACTION_CATALOG}
    assert families == {
        PriceActionStrategyFamily.INTRADAY,
        PriceActionStrategyFamily.SWING,
        PriceActionStrategyFamily.POSITION,
    }
    assert any(strategy.warning_only for strategy in PRICE_ACTION_CATALOG)


def test_catalog_lookup_and_filters_work():
    intraday = list_price_action_strategies(family=PriceActionStrategyFamily.INTRADAY)
    tradable_intraday = list_price_action_strategies(
        family=PriceActionStrategyFamily.INTRADAY,
        include_warning_only=False,
    )

    assert len(intraday) == 7
    assert len(tradable_intraday) == 7
    assert get_price_action_strategy("ascending_triangle_breakout") is not None
    assert get_price_action_strategy("double_bottom_neckline_reclaim") is not None
    assert get_price_action_strategy("inverse_head_and_shoulders_reclaim") is not None
    assert get_price_action_strategy("inside_bar_trend_breakout") is not None
    assert get_price_action_strategy("fakey_false_break_reversal") is not None
    assert get_price_action_strategy("support_reclaim_bullish_engulfing") is not None
    assert get_price_action_strategy("symmetrical_triangle_expansion") is not None
    assert get_price_action_strategy("intraday_support_reclaim_bullish_confirmation") is not None
    assert get_price_action_strategy("intraday_resistance_break_retest_reentry") is not None
    assert get_price_action_strategy("intraday_higher_high_higher_low_continuation") is not None
    assert get_price_action_strategy("intraday_selling_trap_reclaim") is not None
    assert get_price_action_strategy("intraday_trendline_break_reversal") is not None
    assert get_price_action_strategy("bull_trap_breakout_warning") is not None
    assert get_price_action_strategy("double_top_neckline_failure") is not None
    assert get_price_action_strategy("missing_strategy") is None
