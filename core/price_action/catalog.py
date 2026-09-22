from __future__ import annotations
"""Seed catalog for the EGX price-action strategy pack."""


from .models import (
    PriceActionSourceAttribution,
    PriceActionStrategy,
    PriceActionStrategyFamily,
    PriceActionStrategyStatus,
)


def _source(title: str, filename: str, concept: str) -> PriceActionSourceAttribution:
    return PriceActionSourceAttribution(title=title, filename=filename, concept=concept)


PRICE_ACTION_CATALOG: tuple[PriceActionStrategy, ...] = (
    PriceActionStrategy(
        strategy_id="ascending_triangle_breakout",
        display_name="Ascending Triangle Breakout",
        family=PriceActionStrategyFamily.SWING,
        summary="Bullish continuation through flat resistance with rising lows and volume confirmation.",
        regime="BULLISH_CONTINUATION",
        source_attributions=(
            _source(
                "Price Action Patterns 2.0",
                "642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf",
                "ascending triangle continuation",
            ),
        ),
        required_data=("daily_ohlcv", "relative_volume", "swing_structure"),
        entry_conditions=(
            "Resistance band stays broadly flat across multiple touches.",
            "Swing lows rise into resistance instead of breaking down.",
            "Price closes above resistance with relative-volume confirmation.",
        ),
        confirmation_conditions=(
            "Breakout bar closes in the upper part of its range.",
            "Next session holds above or quickly reclaims the breakout band.",
        ),
        avoidance_rules=(
            "Reject if breakout immediately falls back below resistance.",
            "Downgrade if turnover is below EGX liquidity thresholds.",
        ),
        exit_rules=(
            "Stop below the last higher low or a structural ATR buffer.",
            "Scale out into the first measured continuation target.",
        ),
        risk_model="STRUCTURAL_STOP_OR_ATR_BUFFER",
    ),
    PriceActionStrategy(
        strategy_id="bullish_channel_breakout",
        display_name="Bullish Channel Breakout",
        family=PriceActionStrategyFamily.SWING,
        summary="Downward channel exits upward and transitions from reversal into continuation.",
        regime="BULLISH_REVERSAL_CONTINUATION",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "bullish channel breakout",
            ),
        ),
        required_data=("daily_ohlcv", "trendline_structure", "relative_volume"),
        entry_conditions=(
            "Price drifts inside a declining channel without breaking major support.",
            "A bar closes above the upper channel boundary.",
        ),
        confirmation_conditions=(
            "The next bar does not collapse back inside the channel.",
            "Breakout participation is supported by acceptable relative volume.",
        ),
        avoidance_rules=(
            "Block if the breakout candle is fully retraced within one to two bars.",
            "Downgrade if the broader regime is already rolling over.",
        ),
        exit_rules=(
            "Stop below breakout bar low or lower channel support.",
            "Reduce risk if the move stalls at prior overhead resistance.",
        ),
        risk_model="CHANNEL_BREAK_STOP",
    ),
    PriceActionStrategy(
        strategy_id="box_consolidation_breakout",
        display_name="Box Consolidation Higher-High Breakout",
        family=PriceActionStrategyFamily.SWING,
        summary="Horizontal consolidation resolves upward after an established advance.",
        regime="BULLISH_CONSOLIDATION",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "box consolidation higher-high breakout",
            ),
        ),
        required_data=("daily_ohlcv", "range_structure", "relative_volume"),
        entry_conditions=(
            "Price compresses in a horizontal box after an advance.",
            "Breakout prints a higher high above the box boundary.",
        ),
        confirmation_conditions=(
            "Breakout closes above the range instead of only wicking through it.",
            "Volume or turnover is at least neutral to positive versus recent bars.",
        ),
        avoidance_rules=(
            "Block if repeated upper wicks show distribution into the range high.",
            "Downgrade if the box forms after an already extended parabolic move.",
        ),
        exit_rules=(
            "Stop below the opposite side of the box or last pivot low.",
            "Trail under successful retests once the breakout is accepted.",
        ),
        risk_model="BOX_STRUCTURE_STOP",
    ),
    PriceActionStrategy(
        strategy_id="trend_structure_continuation",
        display_name="Higher-High Higher-Low Trend Continuation",
        family=PriceActionStrategyFamily.POSITION,
        summary="Position profile that only participates when daily structure remains constructive.",
        regime="UPTREND_CONTINUATION",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "higher high continuation",
            ),
            _source(
                "Secrets On Reversal Trading",
                "700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf",
                "trend structure and reversal shift themes",
            ),
        ),
        required_data=("daily_ohlcv", "swing_structure", "market_regime"),
        entry_conditions=(
            "Daily structure maintains higher highs and higher lows.",
            "Price reclaims or extends through the prior swing high after a controlled pullback.",
        ),
        confirmation_conditions=(
            "Pullback holds above the last confirmed higher low.",
            "Liquidity stays strong enough for wider holding periods.",
        ),
        avoidance_rules=(
            "Block if higher-low structure is broken before continuation triggers.",
            "Downgrade if the broader market regime turns bearish.",
        ),
        exit_rules=(
            "Stop below the last confirmed higher low with wider ATR tolerance.",
            "Take defensive action when continuation fails to make a fresh high.",
        ),
        risk_model="STRUCTURE_PLUS_REGIME_STOP",
    ),
    PriceActionStrategy(
        strategy_id="double_bottom_neckline_reclaim",
        display_name="Double Bottom Neckline Reclaim",
        family=PriceActionStrategyFamily.POSITION,
        summary="Two aligned lows form a base and the neckline reclaim confirms a slower bullish reversal.",
        regime="BASE_REVERSAL_RECLAIM",
        source_attributions=(
            _source(
                "Price Action Patterns 2.0",
                "642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf",
                "double bottom neckline reclaim",
            ),
            _source(
                "Secrets On Reversal Trading",
                "700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf",
                "double bottom structure change",
            ),
        ),
        required_data=("daily_ohlcv", "support_resistance", "swing_structure"),
        entry_conditions=(
            "Price forms two meaningful lows around the same support zone.",
            "The neckline is reclaimed after the second low.",
            "Price holds above the reclaim zone instead of failing immediately.",
        ),
        confirmation_conditions=(
            "The second low does not materially undercut the first base low.",
            "The reclaim survives at least one follow-through or hold bar.",
        ),
        avoidance_rules=(
            "Reject weak bases where the second low collapses through support.",
            "Downgrade if neckline reclaim occurs with poor participation.",
        ),
        exit_rules=(
            "Stop below the second bottom or the reclaimed neckline shelf.",
            "Take defensive action if price loses the reclaim zone quickly.",
        ),
        risk_model="BASE_NECKLINE_RECLAIM_STOP",
    ),
    PriceActionStrategy(
        strategy_id="inverse_head_and_shoulders_reclaim",
        display_name="Inverse Head And Shoulders Reclaim",
        family=PriceActionStrategyFamily.POSITION,
        summary="A three-trough base with a deeper head reclaims the neckline and confirms a broader bullish reversal.",
        regime="BASE_REVERSAL_RECLAIM",
        source_attributions=(
            _source(
                "Price Action Patterns 2.0",
                "642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf",
                "inverse head and shoulders reclaim",
            ),
            _source(
                "Secrets On Reversal Trading",
                "700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf",
                "inverse head and shoulders structure change",
            ),
        ),
        required_data=("daily_ohlcv", "support_resistance", "swing_structure"),
        entry_conditions=(
            "Price forms a left shoulder, deeper head, and a right shoulder that respects the base.",
            "The neckline is reclaimed after the right shoulder completes.",
            "Price closes above the neckline and avoids immediate failure back into the base.",
        ),
        confirmation_conditions=(
            "The head is materially lower than both shoulders.",
            "The right shoulder holds near or above the left-shoulder support shelf.",
        ),
        avoidance_rules=(
            "Reject malformed bases where the right shoulder breaks the head decisively.",
            "Downgrade weak neckline reclaims that occur without steady participation.",
        ),
        exit_rules=(
            "Stop below the right shoulder or the neckline recovery shelf.",
            "Take defensive action if price loses the neckline soon after the reclaim.",
        ),
        risk_model="INVERSE_HNS_NECKLINE_RECLAIM_STOP",
    ),
    PriceActionStrategy(
        strategy_id="inside_bar_trend_breakout",
        display_name="Inside Bar Trend Breakout",
        family=PriceActionStrategyFamily.SWING,
        summary="Daily inside-bar compression resolves upward in the direction of an existing trend.",
        regime="BULLISH_CONTINUATION_COMPRESSION",
        source_attributions=(
            _source(
                "Price Action Trading",
                "362430524-Price-Action-Trading.pdf",
                "inside bar continuation breakout",
            ),
        ),
        required_data=("daily_ohlcv", "swing_structure", "range_structure"),
        entry_conditions=(
            "A prior uptrend is already in force.",
            "A narrow inside bar forms inside the mother bar range.",
            "The next session closes above the mother bar high.",
        ),
        confirmation_conditions=(
            "Breakout occurs in the direction of the prevailing trend.",
            "Breakout bar closes firmly above the mother bar high.",
        ),
        avoidance_rules=(
            "Reject low-quality inside bars that form against broken trend structure.",
            "Downgrade if the setup appears in low-liquidity drift.",
        ),
        exit_rules=(
            "Stop below the inside bar low or a nearby structural pivot.",
            "Scale out into the next expansion leg if momentum stalls.",
        ),
        risk_model="INSIDE_BAR_STRUCTURE_STOP",
    ),
    PriceActionStrategy(
        strategy_id="fakey_false_break_reversal",
        display_name="Fakey False-Break Reversal",
        family=PriceActionStrategyFamily.SWING,
        summary="A false downside break snaps back and launches a bullish reversal through local structure.",
        regime="BULLISH_TRAP_REVERSAL",
        source_attributions=(
            _source(
                "Price Action Trading",
                "362430524-Price-Action-Trading.pdf",
                "fakey false-break reversal",
            ),
        ),
        required_data=("daily_ohlcv", "range_structure", "support_resistance"),
        entry_conditions=(
            "An inside-bar or compact range structure forms near support.",
            "Price false-breaks lower and quickly reclaims the structure.",
            "The next bar confirms with a close through the mother bar high.",
        ),
        confirmation_conditions=(
            "The false break is obvious rather than marginal.",
            "Recovery occurs at or near a meaningful support area.",
        ),
        avoidance_rules=(
            "Reject if price stays below the broken structure after the false break.",
            "Downgrade if the reversal bar cannot close back into range.",
        ),
        exit_rules=(
            "Stop beyond the false-break extreme.",
            "Reduce risk if the first reclaim cannot hold.",
        ),
        risk_model="FALSE_BREAK_EXTREME_STOP",
    ),
    PriceActionStrategy(
        strategy_id="support_reclaim_bullish_engulfing",
        display_name="Support Reclaim With Bullish Engulfing",
        family=PriceActionStrategyFamily.SWING,
        summary="Support reaction strengthens into a bullish engulfing recovery and local structure reclaim.",
        regime="SUPPORT_LED_BULLISH_REVERSAL",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "support reclaim with bullish engulfing",
            ),
        ),
        required_data=("daily_ohlcv", "support_resistance", "swing_structure"),
        entry_conditions=(
            "Price revisits an established support zone.",
            "A bullish engulfing-style reversal appears at support.",
            "Price then reclaims the nearest local swing high.",
        ),
        confirmation_conditions=(
            "Support reaction occurs inside a broader constructive structure.",
            "Reclaim is confirmed by the closing price rather than only a wick.",
        ),
        avoidance_rules=(
            "Reject if support is broken and not reclaimed quickly.",
            "Downgrade if the engulfing candle forms without structure improvement.",
        ),
        exit_rules=(
            "Stop below the support shelf or reversal low.",
            "Scale out into prior resistance if the rebound stalls.",
        ),
        risk_model="SUPPORT_REVERSAL_STOP",
    ),
    PriceActionStrategy(
        strategy_id="symmetrical_triangle_expansion",
        display_name="Symmetrical Triangle Expansion",
        family=PriceActionStrategyFamily.SWING,
        summary="Converging highs and lows compress price before an upside expansion through the triangle ceiling.",
        regime="BULLISH_COMPRESSION_BREAKOUT",
        source_attributions=(
            _source(
                "Price Action Patterns 2.0",
                "642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf",
                "symmetrical triangle expansion",
            ),
        ),
        required_data=("daily_ohlcv", "range_structure", "trendline_structure", "relative_volume"),
        entry_conditions=(
            "Highs descend while lows rise, forming a visible compression structure.",
            "The trading range tightens rather than widening into disorder.",
            "Price closes above the upper triangle boundary.",
        ),
        confirmation_conditions=(
            "The breakout close clears recent triangle resistance instead of only wicking through it.",
            "Participation is neutral to positive versus recent bars.",
        ),
        avoidance_rules=(
            "Reject loose ranges that do not show clear compression.",
            "Downgrade if the breakout immediately slips back inside the triangle.",
        ),
        exit_rules=(
            "Stop below the most recent higher low or an ATR buffer under the breakout bar.",
            "Scale out if the expansion stalls near the first measured resistance zone.",
        ),
        risk_model="TRIANGLE_COMPRESSION_BREAKOUT_STOP",
    ),
    PriceActionStrategy(
        strategy_id="intraday_bullish_channel_reclaim",
        display_name="Intraday Bullish Channel Reclaim",
        family=PriceActionStrategyFamily.INTRADAY,
        summary="Short-term down channel is reclaimed and followed by intraday continuation.",
        regime="INTRADAY_REVERSAL_CONTINUATION",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "15-minute channel reclaim",
            ),
        ),
        required_data=("intraday_ohlcv", "trendline_structure", "relative_volume"),
        entry_conditions=(
            "Price trades inside a short-term downward intraday channel.",
            "A reclaim bar closes above the upper boundary.",
        ),
        confirmation_conditions=(
            "Follow-through appears instead of immediate rejection.",
            "Reclaim occurs with acceptable liquidity and turnover.",
        ),
        avoidance_rules=(
            "Block if reclaim fails on the next bar.",
            "Block if intraday data feed is unavailable or stale.",
        ),
        exit_rules=(
            "Stop below reclaim low or lower intraday channel edge.",
            "Tighten risk quickly if price stalls under nearby resistance.",
        ),
        risk_model="INTRADAY_RECLAIM_STOP",
        data_gate="REQUIRES_INTRADAY_EGX_FEED",
    ),
    PriceActionStrategy(
        strategy_id="breakout_retest_hold",
        display_name="Breakout Retest Hold",
        family=PriceActionStrategyFamily.INTRADAY,
        summary="Intraday resistance breaks, retests, and holds before continuation.",
        regime="INTRADAY_MOMENTUM_CONTINUATION",
        source_attributions=(
            _source(
                "Day Trading Entries and Exits",
                "809567256-Day-Trading-Entries-and-Exits-The-Best-Day-Trading-Entry-and-Exit-Signals-for-Forex-Stocks-and-Cryptocurrency-in-2024-High-Harnett-David-Z-Li.pdf",
                "breakout retest entry structure",
            ),
            _source(
                "High-Probability Scalping Strategy Playbook",
                "880862988-High-Probability-Scalping-Strategy-Playbook.pdf",
                "breakout and momentum theme",
            ),
        ),
        required_data=("intraday_ohlcv", "range_structure", "relative_volume"),
        entry_conditions=(
            "Price breaks above intraday resistance.",
            "Retest holds without losing the breakout level.",
        ),
        confirmation_conditions=(
            "Resumption bar reclaims or respects the retest zone.",
            "Breakout occurs in a liquid, tradeable context.",
        ),
        avoidance_rules=(
            "Block if retest slices through the breakout level and fails to reclaim it.",
            "Block if intraday data feed is unavailable or stale.",
        ),
        exit_rules=(
            "Stop just below retest low with a tight ATR tolerance.",
            "Take partial profits into the next intraday expansion leg.",
        ),
        risk_model="RETEST_LOW_PLUS_ATR_STOP",
        data_gate="REQUIRES_INTRADAY_EGX_FEED",
    ),
    PriceActionStrategy(
        strategy_id="intraday_support_reclaim_bullish_confirmation",
        display_name="Intraday Support Reclaim With Bullish Confirmation",
        family=PriceActionStrategyFamily.INTRADAY,
        summary="Intraday support is tested, reclaimed, and confirmed by a recovery through nearby structure.",
        regime="INTRADAY_SUPPORT_REVERSAL",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "intraday support reclaim with bullish confirmation",
            ),
        ),
        required_data=("intraday_ohlcv", "support_resistance", "swing_structure"),
        entry_conditions=(
            "Price revisits a visible intraday support zone.",
            "The support break does not persist and price closes back above the zone.",
            "The recovery bar reclaims nearby micro structure.",
        ),
        confirmation_conditions=(
            "Recovery is led by the closing price rather than a wick only.",
            "The reclaim occurs while liquidity remains acceptable.",
        ),
        avoidance_rules=(
            "Reject if support is lost and not recovered quickly.",
            "Downgrade if the rebound cannot clear the nearest micro pivot.",
        ),
        exit_rules=(
            "Stop below the reclaim low or failed support probe.",
            "Take partial profits into the next intraday resistance shelf.",
        ),
        risk_model="INTRADAY_SUPPORT_RECLAIM_STOP",
        data_gate="REQUIRES_INTRADAY_EGX_FEED",
    ),
    PriceActionStrategy(
        strategy_id="intraday_resistance_break_retest_reentry",
        display_name="Intraday Resistance Break Retest Re-entry",
        family=PriceActionStrategyFamily.INTRADAY,
        summary="Resistance breaks, retests as support, and offers a cleaner continuation re-entry.",
        regime="INTRADAY_BREAKOUT_RETEST_CONTINUATION",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "intraday resistance break retest re-entry",
            ),
        ),
        required_data=("intraday_ohlcv", "range_structure", "support_resistance"),
        entry_conditions=(
            "A clear intraday resistance level is broken.",
            "Price retests the broken level without losing it decisively.",
            "The next bar resumes upward from the retest zone.",
        ),
        confirmation_conditions=(
            "Retest low stays near or above the broken resistance line.",
            "The resumption close reclaims the retest bar high or local trigger zone.",
        ),
        avoidance_rules=(
            "Reject if the retest slices back through the breakout level.",
            "Downgrade if the retest turns into sideways drift rather than a clean hold.",
        ),
        exit_rules=(
            "Stop below the retest low.",
            "Scale out into the next intraday expansion or resistance shelf.",
        ),
        risk_model="INTRADAY_RETEST_REENTRY_STOP",
        data_gate="REQUIRES_INTRADAY_EGX_FEED",
    ),
    PriceActionStrategy(
        strategy_id="intraday_higher_high_higher_low_continuation",
        display_name="Intraday Higher-High Higher-Low Continuation",
        family=PriceActionStrategyFamily.INTRADAY,
        summary="Micro trend structure stays constructive and the next pivot high break continues the move.",
        regime="INTRADAY_TREND_CONTINUATION",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "intraday higher high higher low continuation",
            ),
        ),
        required_data=("intraday_ohlcv", "swing_structure", "relative_volume"),
        entry_conditions=(
            "Micro structure forms a higher low after an advance.",
            "The latest bar breaks the prior pivot high.",
            "The higher low remains intact into the trigger.",
        ),
        confirmation_conditions=(
            "Breakout occurs above an intact higher-low shelf.",
            "Relative participation remains at least neutral.",
        ),
        avoidance_rules=(
            "Reject if the higher low is broken before the trigger.",
            "Downgrade if the breakout bar closes back inside the prior pivot range.",
        ),
        exit_rules=(
            "Stop below the most recent higher low.",
            "Reduce risk if continuation stalls under the next intraday resistance band.",
        ),
        risk_model="INTRADAY_MICRO_STRUCTURE_STOP",
        data_gate="REQUIRES_INTRADAY_EGX_FEED",
    ),
    PriceActionStrategy(
        strategy_id="intraday_selling_trap_reclaim",
        display_name="Intraday Selling Trap Reclaim",
        family=PriceActionStrategyFamily.INTRADAY,
        summary="A downside break fails quickly and price reclaims the lost structure before continuation higher.",
        regime="INTRADAY_TRAP_REVERSAL",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "intraday selling trap reclaim",
            ),
        ),
        required_data=("intraday_ohlcv", "support_resistance", "range_structure"),
        entry_conditions=(
            "Price breaks down through intraday support or range lows.",
            "The breakdown fails and price closes back above the broken structure.",
            "The reclaim is followed by upward confirmation rather than renewed weakness.",
        ),
        confirmation_conditions=(
            "The failed break is obvious rather than marginal.",
            "The recovery bar closes inside or above the prior range.",
        ),
        avoidance_rules=(
            "Reject if price stays below the broken level after the breakdown.",
            "Downgrade if the reclaim cannot hold for at least one confirming bar.",
        ),
        exit_rules=(
            "Stop below the failed-break low.",
            "Take defensive action if price loses the reclaimed structure quickly.",
        ),
        risk_model="INTRADAY_TRAP_RECLAIM_STOP",
        data_gate="REQUIRES_INTRADAY_EGX_FEED",
    ),
    PriceActionStrategy(
        strategy_id="intraday_trendline_break_reversal",
        display_name="Trendline Break Intraday Reversal",
        family=PriceActionStrategyFamily.INTRADAY,
        summary="A short-term descending structure breaks upward and confirms a local intraday reversal.",
        regime="INTRADAY_TRENDLINE_REVERSAL",
        source_attributions=(
            _source(
                "Day Trading Entries and Exits",
                "809567256-Day-Trading-Entries-and-Exits-The-Best-Day-Trading-Entry-and-Exit-Signals-for-Forex-Stocks-and-Cryptocurrency-in-2024-High-Harnett-David-Z-Li.pdf",
                "intraday trendline break reversal",
            ),
        ),
        required_data=("intraday_ohlcv", "trendline_structure", "relative_volume"),
        entry_conditions=(
            "Short-term highs descend into a local reversal attempt.",
            "Price breaks the descending structure upward.",
            "The breakout is confirmed by a close rather than a wick-only poke.",
        ),
        confirmation_conditions=(
            "The reversal close clears recent descending highs.",
            "Liquidity or turnover remains acceptable during the break.",
        ),
        avoidance_rules=(
            "Reject if price immediately falls back under the broken structure.",
            "Downgrade if the break occurs without any improvement in local momentum.",
        ),
        exit_rules=(
            "Stop below the reversal bar low or last local support shelf.",
            "Scale out into the next resistance cluster if the reversal hesitates.",
        ),
        risk_model="INTRADAY_TRENDLINE_REVERSAL_STOP",
        data_gate="REQUIRES_INTRADAY_EGX_FEED",
    ),
    PriceActionStrategy(
        strategy_id="descending_triangle_warning",
        display_name="Descending Triangle Breakdown Risk",
        family=PriceActionStrategyFamily.SWING,
        summary="Repeated lower highs into flat support warn against fresh long exposure.",
        regime="BEARISH_PRESSURE",
        source_attributions=(
            _source(
                "Price Action Patterns 2.0",
                "642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf",
                "descending triangle risk",
            ),
        ),
        required_data=("daily_ohlcv", "swing_structure"),
        entry_conditions=("Support is tested repeatedly while highs step down.",),
        confirmation_conditions=("Price has not yet cleanly reclaimed broken structure.",),
        avoidance_rules=("Lower long scores when support pressure is unresolved.",),
        exit_rules=("No trade exit rules; warning-only profile.",),
        risk_model="WARNING_ONLY",
        warning_only=True,
        long_entry_allowed=False,
    ),
    PriceActionStrategy(
        strategy_id="rising_wedge_warning",
        display_name="Rising Wedge Exhaustion Risk",
        family=PriceActionStrategyFamily.POSITION,
        summary="Narrowing advance into resistance warns against chasing late-stage extensions.",
        regime="EXHAUSTION_RISK",
        source_attributions=(
            _source(
                "Price Action Patterns 2.0",
                "642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf",
                "rising wedge exhaustion",
            ),
        ),
        required_data=("daily_ohlcv", "trendline_structure"),
        entry_conditions=("Price advances in a narrowing wedge into resistance.",),
        confirmation_conditions=("Momentum quality weakens as the wedge matures.",),
        avoidance_rules=("Avoid late chase entries when the wedge is unresolved.",),
        exit_rules=("No trade exit rules; warning-only profile.",),
        risk_model="WARNING_ONLY",
        warning_only=True,
        long_entry_allowed=False,
    ),
    PriceActionStrategy(
        strategy_id="failed_breakdown_trap_warning",
        display_name="Selling Trap / Failed Breakdown Avoidance",
        family=PriceActionStrategyFamily.SWING,
        summary="Failed downside breaks can invalidate bearish interpretation and support later long upgrades.",
        regime="TRAP_REVERSAL",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "selling trap and failed breakdown theme",
            ),
        ),
        required_data=("daily_ohlcv", "range_structure"),
        entry_conditions=("A breakdown through support quickly reverses back into the structure.",),
        confirmation_conditions=("Reclaim holds instead of fading immediately.",),
        avoidance_rules=("Do not treat the initial breakdown as clean bearish confirmation.",),
        exit_rules=("No trade exit rules; warning-only profile.",),
        risk_model="WARNING_ONLY",
        warning_only=True,
        long_entry_allowed=False,
    ),
    PriceActionStrategy(
        strategy_id="failed_breakout_warning",
        display_name="Failed Breakout Rejection",
        family=PriceActionStrategyFamily.SWING,
        summary="Breakout that cannot hold above the trigger level should block or downgrade continuation entries.",
        regime="FAILED_CONTINUATION",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "breakout failure and rejection",
            ),
            _source(
                "Day Trading Entries and Exits",
                "809567256-Day-Trading-Entries-and-Exits-The-Best-Day-Trading-Entry-and-Exit-Signals-for-Forex-Stocks-and-Cryptocurrency-in-2024-High-Harnett-David-Z-Li.pdf",
                "entry failure theme",
            ),
        ),
        required_data=("daily_ohlcv", "range_structure", "relative_volume"),
        entry_conditions=("Price loses a recent breakout level within one to two bars.",),
        confirmation_conditions=("Volume support is weak or fading during the failure.",),
        avoidance_rules=("Block or downgrade continuation entries until the level is reclaimed.",),
        exit_rules=("No trade exit rules; warning-only profile.",),
        risk_model="WARNING_ONLY",
        warning_only=True,
        long_entry_allowed=False,
    ),
    PriceActionStrategy(
        strategy_id="bull_trap_breakout_warning",
        display_name="Bull Trap / Breakout Buyer Trap",
        family=PriceActionStrategyFamily.SWING,
        summary="An upside breakout that snaps back under resistance warns against chasing late buyers.",
        regime="BULL_TRAP_FAILURE",
        source_attributions=(
            _source(
                "Price Action Setups",
                "573291545-Price-Action-Setup-Ebook.pdf",
                "breakout buyer trap",
            ),
        ),
        required_data=("daily_ohlcv", "range_structure", "support_resistance"),
        entry_conditions=("Price briefly clears resistance and attracts breakout buyers.",),
        confirmation_conditions=("The next bar loses the breakout level instead of holding above it.",),
        avoidance_rules=("Block fragile breakout continuations until resistance is reclaimed cleanly.",),
        exit_rules=("No trade exit rules; warning-only profile.",),
        risk_model="WARNING_ONLY",
        warning_only=True,
        long_entry_allowed=False,
    ),
    PriceActionStrategy(
        strategy_id="double_top_neckline_failure",
        display_name="Double Top Neckline Failure",
        family=PriceActionStrategyFamily.POSITION,
        summary="A mature double top loses its neckline, warning that distribution may be replacing the prior uptrend.",
        regime="DISTRIBUTION_BREAKDOWN",
        source_attributions=(
            _source(
                "Price Action Patterns 2.0",
                "642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf",
                "double top neckline failure",
            ),
            _source(
                "Secrets On Reversal Trading",
                "700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf",
                "double top reversal failure",
            ),
        ),
        required_data=("daily_ohlcv", "support_resistance", "swing_structure"),
        entry_conditions=("Two highs form in the same resistance area and the neckline is then lost.",),
        confirmation_conditions=("The neckline failure follows the second top rather than random chop.",),
        avoidance_rules=("Avoid fresh longs until the neckline and trend structure are repaired.",),
        exit_rules=("No trade exit rules; warning-only profile.",),
        risk_model="WARNING_ONLY",
        warning_only=True,
        long_entry_allowed=False,
    ),
    PriceActionStrategy(
        strategy_id="reversal_structure_shift_warning",
        display_name="Reversal Structure Shift",
        family=PriceActionStrategyFamily.POSITION,
        summary="Loss of higher-low structure turns a healthy uptrend into an avoidance condition.",
        regime="STRUCTURE_BREAKDOWN",
        source_attributions=(
            _source(
                "Secrets On Reversal Trading",
                "700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf",
                "market structure shift",
            ),
        ),
        required_data=("daily_ohlcv", "swing_structure", "market_regime"),
        entry_conditions=("An uptrend loses higher-low structure and breaks swing support.",),
        confirmation_conditions=("Price fails to reclaim the lost support zone.",),
        avoidance_rules=("Treat the trend as impaired rather than opening a short trade.",),
        exit_rules=("No trade exit rules; warning-only profile.",),
        risk_model="WARNING_ONLY",
        warning_only=True,
        long_entry_allowed=False,
    ),
)


def list_price_action_strategies(
    *,
    family: PriceActionStrategyFamily | None = None,
    include_warning_only: bool = True,
    status: PriceActionStrategyStatus | None = None,
) -> list[PriceActionStrategy]:
    strategies = list(PRICE_ACTION_CATALOG)
    if family is not None:
        strategies = [strategy for strategy in strategies if strategy.family is family]
    if not include_warning_only:
        strategies = [strategy for strategy in strategies if not strategy.warning_only]
    if status is not None:
        strategies = [strategy for strategy in strategies if strategy.status is status]
    return strategies


def get_price_action_strategy(strategy_id: str) -> PriceActionStrategy | None:
    normalized = str(strategy_id or "").strip().lower()
    for strategy in PRICE_ACTION_CATALOG:
        if strategy.strategy_id == normalized:
            return strategy
    return None
