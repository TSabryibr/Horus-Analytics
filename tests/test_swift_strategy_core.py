from pathlib import Path
import re


SWIFT_PATH = Path("docs/Swift.pine")


def _swift_source() -> str:
    return SWIFT_PATH.read_text(encoding="utf-8")


def test_swift_strategy_core_avoids_lookahead_on_security_calls():
    source = _swift_source()

    assert "barmerge.lookahead_on" not in source


def test_swift_strategy_core_does_not_leave_exit_triggers_hardcoded_false():
    source = _swift_source()

    assert not re.search(r"^lxTrigger\s*=\s*false\s*$", source, re.MULTILINE)
    assert not re.search(r"^sxTrigger\s*=\s*false\s*$", source, re.MULTILINE)


def test_swift_strategy_core_uses_trade_type_gates():
    source = _swift_source()

    assert re.search(
        r"allowLongTrades\s*=\s*tradeType\s*==\s*'LONG'\s*or\s*tradeType\s*==\s*'BOTH'",
        source,
    )
    assert re.search(
        r"allowShortTrades\s*=\s*tradeType\s*==\s*'SHORT'\s*or\s*tradeType\s*==\s*'BOTH'",
        source,
    )


def test_swift_strategy_core_uses_short_entry_webhook_message():
    source = _swift_source()

    short_entry_block = re.search(
        r"if strategy\.position_size >= 0 and shortE and barstate\.isconfirmed(?P<body>[\s\S]*?)if armShortExits",
        source,
    )

    assert short_entry_block is not None
    assert "alert_message    = i_seMsg" in short_entry_block.group("body")


def test_swift_strategy_core_defines_strategy_guardrail_inputs():
    source = _swift_source()

    assert "G_GUARDRAILS" in source
    assert "Enable Guardrails" in source
    assert "Max Drawdown %" in source
    assert "Max Daily Loss %" in source
    assert "Max Filled Orders / Day" in source


def test_swift_strategy_core_applies_builtin_risk_guardrails():
    source = _swift_source()

    assert "strategy.risk.max_drawdown" in source
    assert "strategy.risk.max_intraday_loss" in source
    assert "strategy.risk.max_intraday_filled_orders" in source


def test_swift_strategy_core_arms_all_long_exits_while_trade_is_active():
    source = _swift_source()

    assert "armLongExits" in source
    assert "armLongExits  = strategy.position_size > 0 and condition >=  1.0 and condition <  1.3" in source
    assert "if armLongExits" in source


def test_swift_strategy_core_arms_all_short_exits_while_trade_is_active():
    source = _swift_source()

    assert "armShortExits" in source
    assert "armShortExits = strategy.position_size < 0 and condition <= -1.0 and condition > -1.3" in source
    assert "if armShortExits" in source


def test_swift_strategy_core_defines_trade_management_inputs():
    source = _swift_source()

    assert "G_TRADE_MGMT" in source
    assert "Move Stop To Breakeven After TP1" in source
    assert "Breakeven Buffer %" in source
    assert "Promote Stop To TP1 After TP2" in source


def test_swift_strategy_core_promotes_stops_after_partial_profit():
    source = _swift_source()

    assert "breakEvenLongLine" in source
    assert "breakEvenShortLine" in source
    assert "baseSlLine" in source
    assert "math.max(baseSlLine, tp1Line)" in source
    assert "math.min(baseSlLine, tp1Line)" in source


def test_swift_strategy_core_defines_position_sizing_inputs():
    source = _swift_source()

    assert "G_POSITION" in source
    assert "Use Risk-Based Position Sizing" in source
    assert "Risk Per Trade %" in source
    assert "Max Position Value %" in source


def test_swift_strategy_core_calculates_qty_from_equity_and_stop_distance():
    source = _swift_source()

    assert "f_calc_position_size" in source
    assert "strategy.equity * (i_riskPct / 100)" in source
    assert "math.abs(_entryPrice - _stopPrice)" in source
    assert "maxPositionValue = strategy.equity * (i_maxPositionPct / 100)" in source


def test_swift_strategy_core_passes_explicit_entry_qty_values():
    source = _swift_source()

    assert "longEntryQty" in source
    assert "shortEntryQty" in source
    assert "qty              = longEntryQty" in source
    assert "qty              = shortEntryQty" in source


def test_swift_strategy_core_defines_signal_filter_inputs():
    source = _swift_source()

    assert "G_FILTERS" in source
    assert "Use EMA Trend Filter" in source
    assert "Use RSI Exhaustion Filter" in source


def test_swift_strategy_core_applies_signal_filters_only_to_entries():
    source = _swift_source()

    assert "longFiltersPass" in source
    assert "shortFiltersPass" in source
    assert "leTrigger        = allowLongTrades and rawLongTrigger and longFiltersPass and entryCooldownPass and volatilityFilterPass" in source
    assert "seTrigger        = allowShortTrades and rawShortTrigger and shortFiltersPass and entryCooldownPass and volatilityFilterPass" in source
    assert "lxTrigger        = rawShortTrigger" in source
    assert "sxTrigger        = rawLongTrigger" in source


def test_swift_strategy_core_uses_existing_ema_and_rsi_series_for_filter_logic():
    source = _swift_source()

    assert "longFiltersPass  = (not i_useTrendFilter or emaBull) and (not i_useRsiFilter or not rsiOb)" in source
    assert "shortFiltersPass = (not i_useTrendFilter or not emaBull) and (not i_useRsiFilter or not rsiOs)" in source


def test_swift_strategy_core_declares_filter_inputs_before_trigger_filter_usage():
    source = _swift_source()

    assert source.index("i_useTrendFilter") < source.index("longFiltersPass")
    assert source.index("i_useRsiFilter") < source.index("shortFiltersPass")


def test_swift_strategy_core_defines_entry_cooldown_input():
    source = _swift_source()

    assert "G_ENTRY_FLOW" in source
    assert "Bars Cooldown After Exit" in source


def test_swift_strategy_core_gates_entries_during_cooldown_window():
    source = _swift_source()

    assert "var int cooldownUntilBar = na" in source
    assert "cooldownActive   = not na(cooldownUntilBar[1]) and bar_index <= cooldownUntilBar[1]" in source
    assert "entryCooldownPass = i_cooldownBars <= 0 or not cooldownActive" in source
    assert "leTrigger        = allowLongTrades and rawLongTrigger and longFiltersPass and entryCooldownPass and volatilityFilterPass" in source
    assert "seTrigger        = allowShortTrades and rawShortTrigger and shortFiltersPass and entryCooldownPass and volatilityFilterPass" in source
    assert "cooldownUntilBar := longX or shortX or longSL or shortSL or longTimeX or shortTimeX ? bar_index + i_cooldownBars : nz(cooldownUntilBar[1])" in source


def test_swift_strategy_core_defines_atr_volatility_filter_inputs():
    source = _swift_source()

    assert "G_VOL_FILTER" in source
    assert "Use ATR Volatility Filter" in source
    assert "Min ATR %" in source
    assert "Max ATR %" in source


def test_swift_strategy_core_uses_atr_percent_for_entry_filtering():
    source = _swift_source()

    assert "atrPct = close > 0 ? (atrValue / close) * 100 : 0.0" in source
    assert "volatilityFilterPass = not i_useAtrVolatilityFilter or (atrPct >= i_minAtrPct and atrPct <= i_maxAtrPct)" in source
    assert "leTrigger        = allowLongTrades and rawLongTrigger and longFiltersPass and entryCooldownPass and volatilityFilterPass" in source
    assert "seTrigger        = allowShortTrades and rawShortTrigger and shortFiltersPass and entryCooldownPass and volatilityFilterPass" in source


def test_swift_strategy_core_defines_time_exit_input():
    source = _swift_source()

    assert "G_TIME_EXIT" in source
    assert "Max Bars In Trade" in source


def test_swift_strategy_core_closes_positions_after_max_bars():
    source = _swift_source()

    assert "var int activeEntryBar = na" in source
    assert "barsInTrade = not na(activeEntryBar[1]) ? bar_index - activeEntryBar[1] : 0" in source
    assert "timeExitTrigger = i_maxBarsInTrade > 0 and strategy.position_size != 0 and not na(activeEntryBar[1]) and barsInTrade >= i_maxBarsInTrade" in source
    assert "longTimeX     = timeExitTrigger and condition[1] >=  1.0 and condition ==  0.0 and not longX and not longSL" in source
    assert "shortTimeX    = timeExitTrigger and condition[1] <= -1.0 and condition ==  0.0 and not shortX and not shortSL" in source
    assert "if longX or longTimeX" in source
    assert "if shortX or shortTimeX" in source
