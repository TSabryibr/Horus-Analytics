# EGX Price Action Extraction Catalog

Date: 2026-04-28
Status: PAS-P1 extraction plus 2026-04-29 implementation refresh
Source plan: `docs/superpowers/plans/2026-04-28-egx-price-action-strategy-pack-implementation-plan.md`

## 1. Method

This catalog is a one-time extraction pass from six operator-supplied PDFs.

The source files were reviewed directly in a local browser-based PDF viewer.
Because several of the PDFs are highly visual and lightly structured, this pass
captures:

- pattern and setup families that can be rewritten as measurable EGX rules
- warning concepts that fit Horus avoidance logic
- setup themes that are too indicator-heavy, too discretionary, or too
  non-EGX-specific for v1

This document intentionally avoids copying long source text. It records original
Horus-facing summaries only.

## 2. Source Coverage

Reviewed source files:

- `642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf`
  Coverage: visual pattern glossary and example pages for triangle, wedge,
  rectangle, and pennant continuations.
- `573291545-Price-Action-Setup-Ebook.pdf`
  Coverage: channel and box-style setups, trap callouts, breakout examples, and
  higher-high continuation logic.
- `700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf`
  Coverage: reversal-oriented table of contents and chapter themes around trend
  shifts, engulfing, pin bars, and double top/bottom style reversals.
- `880862988-High-Probability-Scalping-Strategy-Playbook.pdf`
  Coverage: table of contents showing breakout, momentum, mean reversion,
  ranging vs trending, and entry/exit timing themes; heavy use of indicator and
  AI sections.
- `733203264-High-Win-Rate-Day-Trading-Setups-High-Win-Rate-Day-Trading-Robbinson-Marcel-2022-2d3241b9e950c5dd0f21d96918c65f4e-Anna-s-Archive.pdf`
  Coverage: table of contents showing breakout/consolidation filters, mean
  reversion, trend following, reversal scalping, pivot bands, RSI and
  Bollinger-style intraday entries.
- `809567256-Day-Trading-Entries-and-Exits-The-Best-Day-Trading-Entry-and-Exit-Signals-for-Forex-Stocks-and-Cryptocurrency-in-2024-High-Harnett-David-Z-Li.pdf`
  Coverage: table of contents showing entry/exit structure, trailing stops,
  RSI-based entries, oscillator entries, volatility-based entries, trend
  following, and advanced indicator combinations.

## 3. EGX Suitability Rules

A source idea is considered EGX-v1 suitable only when it can be expressed with:

- OHLCV bar data
- rolling highs and lows
- basic moving averages or ATR if needed
- relative volume
- support and resistance structure
- simple market-structure state such as higher highs and higher lows

The following are not EGX-v1 defaults:

- AI or machine-learning strategy logic
- proprietary indicator packages
- multi-indicator stacks with unclear robustness
- crypto-specific or perpetual-market assumptions
- non-measurable discretionary language

## 4. Accepted Setup Candidates

### PA-SW-01 Ascending Triangle Breakout

- Family: `SWING`
- Primary source inspiration:
  `642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf`
- Regime: bullish continuation
- Required data: daily OHLCV
- Horus rule sketch:
  price forms a flat resistance band with rising swing lows, then closes above
  resistance with relative-volume confirmation.
- Entry idea:
  trigger on confirmed close above resistance or next-session hold above the
  breakout band.
- Risk model:
  stop below the last higher low or ATR-based structural stop.
- Horus use:
  strong swing candidate; also suitable as a scanner-ready continuation profile.
- Status: `ACCEPTED`

### PA-SW-02 Bullish Channel Breakout

- Family: `SWING`
- Primary source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
- Regime: bullish reversal into continuation
- Required data: daily OHLCV
- Horus rule sketch:
  price declines or drifts inside a downward-sloping channel, then breaks and
  closes above the upper trendline.
- Entry idea:
  breakout close plus confirmation that the next bar does not immediately fail.
- Risk model:
  stop below the breakout bar low or lower channel boundary.
- Horus use:
  swing setup with clear explanation text and a useful warning if the move fades
  back into the channel.
- Status: `ACCEPTED`

### PA-SW-03 Box Consolidation Higher-High Breakout

- Family: `SWING`
- Primary source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
- Regime: bullish consolidation
- Required data: daily OHLCV
- Horus rule sketch:
  price compresses into a horizontal box after an advance, then prints a higher
  high through the upper boundary.
- Entry idea:
  trigger on breakout close above the box high.
- Risk model:
  stop below the opposite side of the box or the prior breakout pivot.
- Horus use:
  compact EGX continuation setup; useful for cleaner liquid names.
- Status: `ACCEPTED`

### PA-POS-01 Higher-High Higher-Low Trend Continuation

- Family: `POSITION`
- Primary source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
  and `700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf`
- Regime: established uptrend
- Required data: daily OHLCV
- Horus rule sketch:
  detect a sequence of higher highs and higher lows, then allow entries only
  when price reclaims or extends through the prior swing high.
- Entry idea:
  buy on structure continuation after a controlled pullback.
- Risk model:
  stop below the last confirmed higher low; wider ATR buffer than swing setups.
- Horus use:
  position-trading profile with regime alignment and slower turnover.
- Status: `ACCEPTED`

### PA-INTRA-01 Intraday Bullish Channel Reclaim

- Family: `INTRADAY`
- Primary source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
- Regime: intraday reversal into continuation
- Required data: intraday OHLCV
- Horus rule sketch:
  price trades inside a short-term downward channel, reclaims the upper
  boundary, and confirms with follow-through rather than immediate rejection.
- Entry idea:
  trigger only when intraday data is available and the reclaim bar closes above
  the channel.
- Risk model:
  stop below reclaim low or lower channel edge.
- Horus use:
  intraday-only candidate; must stay hard-gated until intraday EGX feed quality
  is confirmed in implementation.
- Status: `ACCEPTED_WITH_DATA_GATE`

### PA-INTRA-02 Breakout Retest Hold

- Family: `INTRADAY`
- Primary source inspiration:
  `809567256-Day-Trading-Entries-and-Exits-The-Best-Day-Trading-Entry-and-Exit-Signals-for-Forex-Stocks-and-Cryptocurrency-in-2024-High-Harnett-David-Z-Li.pdf`
  and `880862988-High-Probability-Scalping-Strategy-Playbook.pdf`
- Regime: momentum continuation
- Required data: intraday OHLCV
- Horus rule sketch:
  after a breakout through intraday resistance, price retests the level without
  losing it and resumes upward.
- Entry idea:
  trigger on reclaim or hold after the retest.
- Risk model:
  stop just below the retest low with tight ATR filter.
- Horus use:
  high-signal intraday candidate that maps well to warning and blocker logic.
- Status: `ACCEPTED_WITH_DATA_GATE`

### PA-INTRA-03 Intraday Support Reclaim With Bullish Confirmation

- Family: `INTRADAY`
- Primary source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
- Regime: intraday support-led reversal
- Required data: intraday OHLCV
- Horus rule sketch:
  price tests intraday support, reclaims it, then closes through nearby micro
  structure rather than stalling in place.
- Entry idea:
  trigger only after support is reclaimed and the next bar confirms upward.
- Risk model:
  stop below reclaim low or the failed support probe.
- Horus use:
  cleaner intraday support-bounce setup than a candle-only reversal rule.
- Runtime id: `intraday_support_reclaim_bullish_confirmation`
- Status: `IMPLEMENTED_2026_04_29`

### PA-INTRA-04 Intraday Resistance Break Retest Re-entry

- Family: `INTRADAY`
- Primary source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
- Regime: intraday breakout continuation
- Required data: intraday OHLCV
- Horus rule sketch:
  resistance breaks, price retests the broken level, holds, and then resumes
  upward.
- Entry idea:
  trigger on the resumption bar after a successful hold of the retest zone.
- Risk model:
  stop below the retest low with a tight intraday buffer.
- Horus use:
  strong intraday continuation and re-entry profile for liquid EGX names.
- Runtime id: `intraday_resistance_break_retest_reentry`
- Status: `IMPLEMENTED_2026_04_29`

### PA-INTRA-05 Intraday Higher-High / Higher-Low Continuation

- Family: `INTRADAY`
- Primary source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
- Regime: micro trend continuation
- Required data: intraday OHLCV
- Horus rule sketch:
  a higher low forms intraday, remains intact, and the next pivot high break
  continues the move.
- Entry idea:
  trigger on the close through the prior intraday pivot high.
- Risk model:
  stop below the most recent higher low.
- Horus use:
  compact micro-structure continuation setup for active names.
- Runtime id: `intraday_higher_high_higher_low_continuation`
- Status: `IMPLEMENTED_2026_04_29`

### PA-INTRA-06 Intraday Selling Trap Reclaim

- Family: `INTRADAY`
- Primary source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
- Regime: failed breakdown reversal
- Required data: intraday OHLCV
- Horus rule sketch:
  a downside intraday break fails quickly and price reclaims the broken support
  or range floor.
- Entry idea:
  trigger after the reclaim closes back above the failed breakdown area.
- Risk model:
  stop below the failed-break low.
- Horus use:
  useful trap-reversal profile that complements the warning-only failed-break
  concepts.
- Runtime id: `intraday_selling_trap_reclaim`
- Status: `IMPLEMENTED_2026_04_29`

### PA-INTRA-07 Trendline Break Intraday Reversal

- Family: `INTRADAY`
- Primary source inspiration:
  `809567256-Day-Trading-Entries-and-Exits-The-Best-Day-Trading-Entry-and-Exit-Signals-for-Forex-Stocks-and-Cryptocurrency-in-2024-High-Harnett-David-Z-Li.pdf`
- Regime: short-term intraday reversal
- Required data: intraday OHLCV
- Horus rule sketch:
  descending local pressure breaks upward and the break is confirmed by a close
  rather than a wick alone.
- Entry idea:
  trigger on confirmed break of the recent descending boundary.
- Risk model:
  stop below the reversal bar low or nearby local support.
- Horus use:
  intraday reversal setup that can be expressed with structure only, without
  carrying over indicator-specific source logic.
- Runtime id: `intraday_trendline_break_reversal`
- Status: `IMPLEMENTED_2026_04_29`

## 5. Accepted Warning and Avoidance Concepts

### PA-WARN-01 Descending Triangle Breakdown Risk

- Family: `SWING` warning
- Source inspiration:
  `642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf`
- Rule sketch:
  flat support with repeated lower highs into support.
- Horus effect:
  lower long score or block new longs when price is pressuring support and has
  not reclaimed structure.
- Status: `ACCEPTED`

### PA-WARN-02 Rising Wedge Exhaustion Risk

- Family: `POSITION` warning
- Source inspiration:
  `642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf`
- Rule sketch:
  narrowing upward wedge into resistance with momentum loss.
- Horus effect:
  avoid chasing late-stage position entries; warn about exhaustion.
- Status: `ACCEPTED`

### PA-WARN-03 Selling Trap / Failed Breakdown Avoidance

- Family: `INTRADAY` and `SWING` warning
- Source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
- Rule sketch:
  a downside break inside a bullish structure fails quickly and is reversed.
- Horus effect:
  avoid bearish interpretation of failed breaks; can upgrade long setups after
  reclaim confirmation.
- Status: `ACCEPTED`

### PA-WARN-04 Failed Breakout Rejection

- Family: `SWING`
- Source inspiration:
  multiple books, especially the setup and entries/exit sources
- Rule sketch:
  price closes above a breakout line but immediately falls back under it on the
  next bar or two with weak volume support.
- Horus effect:
  block or downgrade breakout candidates.
- Status: `ACCEPTED`

### PA-WARN-05 Reversal Structure Shift

- Family: `POSITION`
- Source inspiration:
  `700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf`
- Rule sketch:
  uptrend loses higher-low structure, then breaks swing support and fails to
  reclaim.
- Horus effect:
  avoidance warning rather than short entry.
- Status: `ACCEPTED`

## 6. Second-Pass Candidate Additions

These were identified during a second pass over the converted HTML sources.
They look additive to the current pack and can be considered for the next
catalog expansion after the present runtime is stable.

### PA-SW-04 Inside Bar Trend Breakout

- Family: `SWING`
- Primary source inspiration:
  `362430524-Price-Action-Trading.pdf`
- Regime: trend continuation after short compression
- Required data: daily OHLCV
- Horus rule sketch:
  after an established uptrend, a narrow inside bar forms and the next session
  breaks the mother bar high with follow-through.
- Entry idea:
  trigger on a confirmed break of the mother bar high, preferably in the
  direction of the prevailing trend.
- Risk model:
  stop below the inside bar low or mother bar midpoint if the structure is
  wider.
- Horus use:
  compact daily continuation setup that fits EGX swing names better than lower
  timeframe inside-bar trading.
- Runtime id: `inside_bar_trend_breakout`
- Status: `IMPLEMENTED_2026_04_29`

### PA-SW-05 Fakey False-Break Reversal

- Family: `SWING`
- Primary source inspiration:
  `362430524-Price-Action-Trading.pdf`
- Regime: false-break reversal from support or resistance
- Required data: daily OHLCV
- Horus rule sketch:
  price breaks one side of an inside-bar or small-range structure, quickly
  rejects that break, and closes back through the range in the opposite
  direction.
- Entry idea:
  trigger only when the false break is obvious and the recovery bar closes back
  into or through the structure.
- Risk model:
  stop beyond the false-break extreme.
- Horus use:
  strong reversal or trap-cleanup setup that can work as both a tradable long
  and a blocker for breakout chasing.
- Runtime id: `fakey_false_break_reversal`
- Status: `IMPLEMENTED_2026_04_29`

### PA-SW-06 Symmetrical Triangle Expansion

- Family: `SWING`
- Primary source inspiration:
  `642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf`
- Regime: volatility compression into directional expansion
- Required data: daily OHLCV
- Horus rule sketch:
  converging lower highs and higher lows compress price into a triangle, then a
  breakout with follow-through resolves the structure.
- Entry idea:
  trigger on breakout plus hold or retest, rather than on a first wick outside
  the pattern.
- Risk model:
  stop on the opposite side of the retest area or under the last internal swing
  low.
- Horus use:
  useful when EGX names coil before trend continuation or reversal, provided
  the breakout bar is confirmed.
- Runtime id: `symmetrical_triangle_expansion`
- Status: `IMPLEMENTED_2026_04_29`

### PA-SW-07 Support Reclaim With Bullish Engulfing

- Family: `SWING`
- Primary source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
- Regime: support-led reversal inside a broader bullish structure
- Required data: daily OHLCV
- Horus rule sketch:
  price revisits a known support area, prints a bullish engulfing-style
  reversal, then reclaims the nearest prior swing high.
- Entry idea:
  trigger only when the support reaction is followed by structure improvement,
  not on the candlestick alone.
- Risk model:
  stop below the reclaim candle or support shelf.
- Horus use:
  gives Horus a cleaner support-bounce profile than a generic candlestick-only
  reversal rule.
- Runtime id: `support_reclaim_bullish_engulfing`
- Status: `IMPLEMENTED_2026_04_29`

### PA-POS-02 Double Bottom Neckline Reclaim

- Family: `POSITION`
- Primary source inspiration:
  `642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf`
  and `700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf`
- Regime: base formation after a downtrend
- Required data: daily OHLCV
- Horus rule sketch:
  price forms two major lows around a support zone, then reclaims the neckline
  and holds above it instead of failing immediately.
- Entry idea:
  trigger on neckline reclaim plus retest hold.
- Risk model:
  stop below the second low or the neckline retest zone, depending on the
  quality of the base.
- Horus use:
  strong candidate for slower reversal names transitioning from decline to
  accumulation.
- Runtime id: `double_bottom_neckline_reclaim`
- Status: `IMPLEMENTED_2026_04_29`

### PA-POS-03 Inverse Head And Shoulders Reclaim

- Family: `POSITION`
- Primary source inspiration:
  `642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf`
- Regime: bearish-to-bullish structure transition
- Required data: daily OHLCV
- Horus rule sketch:
  price forms a left shoulder, deeper head, and higher right shoulder, then
  breaks the neckline and survives a retest.
- Entry idea:
  trigger on neckline breakout hold or first clean retest.
- Risk model:
  stop below the right shoulder low.
- Horus use:
  slower position-style reversal profile where market structure matters more
  than speed.
- Runtime id: `inverse_head_and_shoulders_reclaim`
- Status: `IMPLEMENTED_2026_04_29`

### PA-WARN-06 Bull Trap / Breakout Buyer Trap

- Family: `SWING` warning
- Source inspiration:
  `573291545-Price-Action-Setup-Ebook.pdf`
- Rule sketch:
  an apparent upside breakout attracts buyers, then quickly loses the breakout
  level and leaves late entries trapped.
- Horus effect:
  block late breakout longs and add caution when post-breakout closes weaken.
- Runtime id: `bull_trap_breakout_warning`
- Status: `IMPLEMENTED_2026_04_29`

### PA-WARN-07 Double Top Neckline Failure

- Family: `POSITION` warning
- Source inspiration:
  `700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf`
- Rule sketch:
  price forms two major highs, fails to create fresh momentum on the second
  high, then breaks or retests the neckline weakly.
- Horus effect:
  downgrade long continuation assumptions and flag possible trend transition.
- Runtime id: `double_top_neckline_failure`
- Status: `IMPLEMENTED_2026_04_29`

## 7. Deferred But Promising Concepts

### D1 Engulfing Reversal Confirmation

- Source inspiration:
  reversal book themes
- Reason to defer:
  good warning candidate, but needs clearer calibration so it does not flood
  Horus with single-candle noise.

### D2 Pin Bar Reversal Confirmation

- Source inspiration:
  reversal book themes
- Reason to defer:
  measurable, but likely better as a confirmation layer than a standalone EGX
  strategy in v1.

### D3 Double Top / Double Bottom Reversal

- Source inspiration:
  reversal book themes
- Reason to defer:
  useful, but pattern-quality scoring needs more structure than the first
  implementation slice.

### D4 Bullish Rectangle Continuation

- Source inspiration:
  `642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf`
- Reason to defer:
  overlaps heavily with the accepted box-consolidation breakout setup and does
  not need a separate v1 profile yet.

## 8. Rejected for EGX V1

### R1 Indicator Bundle Strategies

- Source inspiration:
  day-trading, scalping, and entry/exit books
- Examples of theme, not copied rules:
  multi-indicator stacks, proprietary scripts, AI-labeled indicator packages,
  and oscillator bundles.
- Reason rejected:
  too far from the price-action-first EGX pack and too dependent on proprietary
  or overfit combinations.

### R2 AI / Machine-Learning Scalping

- Source inspiration:
  scalping and entry/exit books
- Reason rejected:
  outside scope, not price-action-native, and not suitable for a first EGX
  implementation slice.

### R3 Crypto / Forex-Specific Market Assumptions

- Source inspiration:
  setup, scalping, day-trading, and entry/exit books
- Reason rejected:
  24-hour market behavior, perpetual intraday liquidity, and non-EGX volatility
  assumptions do not transfer cleanly.

### R4 Proprietary TradingView Indicator Recipes

- Source inspiration:
  day-trading and entry/exit books
- Reason rejected:
  many are indicator-specific, version-specific, or rely on vendor logic rather
  than transparent price structure.

## 9. V1 Shortlist

Initial implementation shortlist:

- `PA-SW-01` Ascending Triangle Breakout
- `PA-SW-02` Bullish Channel Breakout
- `PA-SW-03` Box Consolidation Higher-High Breakout
- `PA-POS-01` Higher-High Higher-Low Trend Continuation
- `PA-INTRA-01` Intraday Bullish Channel Reclaim
- `PA-INTRA-02` Breakout Retest Hold
- `PA-WARN-01` Descending Triangle Breakdown Risk
- `PA-WARN-02` Rising Wedge Exhaustion Risk
- `PA-WARN-03` Selling Trap / Failed Breakdown Avoidance
- `PA-WARN-04` Failed Breakout Rejection
- `PA-WARN-05` Reversal Structure Shift

## 10. Recommended Backend Direction

For PAS-P2, the first code catalog should stay intentionally small:

- implement all three accepted swing/position entries first
- wire warning concepts in parallel because they are central to the design
- keep both intraday entries behind a hard data-availability gate
- add engulfing, pin bar, inside-bar, fakey, and structured double
  top/bottom-style profiles only after the first backtest and scanner
  integration pass is stable

## 11. Notes for PAS-P2

Suggested first code identifiers:

- `ascending_triangle_breakout`
- `bullish_channel_breakout`
- `box_consolidation_breakout`
- `trend_structure_continuation`
- `descending_triangle_warning`
- `rising_wedge_warning`
- `failed_breakdown_trap_warning`
- `failed_breakout_warning`
- `reversal_structure_shift_warning`

These ids are stable enough for backend contracts and still readable in API and
scanner payloads.

## 12. Expansion Batch Status

The second-pass expansion batch is now implemented in the runtime:

- `PA-SW-04` Inside Bar Trend Breakout
- `PA-SW-05` Fakey False-Break Reversal
- `PA-SW-06` Symmetrical Triangle Expansion
- `PA-SW-07` Support Reclaim With Bullish Engulfing
- `PA-POS-02` Double Bottom Neckline Reclaim
- `PA-POS-03` Inverse Head And Shoulders Reclaim
- `PA-WARN-06` Bull Trap / Breakout Buyer Trap
- `PA-WARN-07` Double Top Neckline Failure

These are now available through the strategy catalog, evaluator, and scanner
promotion flow where applicable.

## 13. Intraday Expansion Status

The intraday expansion batch is now implemented in the runtime:

- `PA-INTRA-03` Intraday Support Reclaim With Bullish Confirmation
- `PA-INTRA-04` Intraday Resistance Break Retest Re-entry
- `PA-INTRA-05` Intraday Higher-High / Higher-Low Continuation
- `PA-INTRA-06` Intraday Selling Trap Reclaim
- `PA-INTRA-07` Trendline Break Intraday Reversal

Operational note from a `2026-04-29` review:

- intraday EGX data is present for liquid EGX30 names
- sample liquid names showed roughly `7k` to `11k` recent intraday bars each
- sample coverage began around `2026-02-10` or `2026-02-11` for the reviewed
  liquid names
- the current full-market intraday backtest loop is materially heavier than the
  daily pack and should be treated as a runtime/performance follow-up before
  broad promotion decisions

## 14. EGX30 Backtest Snapshot For Implemented Expansion Entries

Backtest run date: `2026-04-29`

Config used:

- market: `EGX30`
- date range: `2025-01-01` to `2026-04-28`
- capital: `100000`
- commission: `0.05%`
- slippage: `0.1%`

Tradable expansion entries:

- `inside_bar_trend_breakout`
  - state: `READY`
  - trades: `175`
  - total return: `12.9389%`
  - profit factor: `1.471542`
  - max drawdown: `2.0591%`

- `fakey_false_break_reversal`
  - state: `READY`
  - trades: `21`
  - total return: `2.0125%`
  - profit factor: `1.630276`
  - max drawdown: `0.9227%`

- `symmetrical_triangle_expansion`
  - state: `READY`
  - trades: `87`
  - total return: `9.1446%`
  - profit factor: `1.523448`
  - max drawdown: `2.6109%`

- `support_reclaim_bullish_engulfing`
  - state: `READY`
  - trades: `84`
  - total return: `7.747%`
  - profit factor: `1.534798`
  - max drawdown: `2.9884%`

- `double_bottom_neckline_reclaim`
  - state: `READY`
  - trades: `260`
  - total return: `39.6471%`
  - profit factor: `1.709354`
  - max drawdown: `4.3476%`

- `inverse_head_and_shoulders_reclaim`
  - state: `READY`
  - trades: `85`
  - total return: `20.9801%`
  - profit factor: `1.988546`
  - max drawdown: `3.8958%`

Warning-only expansion profiles:

- `bull_trap_breakout_warning`
- `double_top_neckline_failure`

These are intentionally not backtested through the tradable promotion path,
because the backtest service rejects warning-only profiles by design.
