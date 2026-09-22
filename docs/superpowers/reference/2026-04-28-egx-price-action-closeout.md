# EGX Price Action Pack Closeout

Date: 2026-04-28
Status: PAS-P8 closeout
Scope: EGX-only price action strategy pack

## 1. Outcome

The first EGX price action pack is now wired end to end inside Horus:

- research extraction catalog
- backend price action runtime
- backtest and promotion gates
- strategy APIs
- scanner profile integration
- Strategy page lab surface
- scanner and strategy UI polish for `PRICE_ACTION` profiles

The implementation remains long-only for executable entries. Bearish concepts
are exposed as warnings, blockers, or score reducers rather than short trades.

## 2. Implemented Strategy IDs

Tradable entries:

- `ascending_triangle_breakout`
- `bullish_channel_breakout`
- `box_consolidation_breakout`
- `trend_structure_continuation`
- `inside_bar_trend_breakout`
- `fakey_false_break_reversal`
- `symmetrical_triangle_expansion`
- `support_reclaim_bullish_engulfing`
- `double_bottom_neckline_reclaim`
- `inverse_head_and_shoulders_reclaim`
- `intraday_bullish_channel_reclaim`
- `breakout_retest_hold`
- `intraday_support_reclaim_bullish_confirmation`
- `intraday_resistance_break_retest_reentry`
- `intraday_higher_high_higher_low_continuation`
- `intraday_selling_trap_reclaim`
- `intraday_trendline_break_reversal`

Warning-only profiles:

- `descending_triangle_warning`
- `rising_wedge_warning`
- `failed_breakdown_trap_warning`
- `failed_breakout_warning`
- `bull_trap_breakout_warning`
- `double_top_neckline_failure`
- `reversal_structure_shift_warning`

## 3. EGX30 Expansion Backtest Snapshot

Backtest run date: `2026-04-29`

Config:

- market: `EGX30`
- window: `2025-01-01` to `2026-04-28`
- capital: `100000`
- commission: `0.05%`
- slippage: `0.1%`

Tradable expansion batch results:

- `inside_bar_trend_breakout`: `READY`, `175` trades, `12.9389%` return,
  `1.471542` profit factor, `2.0591%` max drawdown
- `fakey_false_break_reversal`: `READY`, `21` trades, `2.0125%` return,
  `1.630276` profit factor, `0.9227%` max drawdown
- `symmetrical_triangle_expansion`: `READY`, `87` trades, `9.1446%` return,
  `1.523448` profit factor, `2.6109%` max drawdown
- `support_reclaim_bullish_engulfing`: `READY`, `84` trades, `7.747%` return,
  `1.534798` profit factor, `2.9884%` max drawdown
- `double_bottom_neckline_reclaim`: `READY`, `260` trades, `39.6471%` return,
  `1.709354` profit factor, `4.3476%` max drawdown
- `inverse_head_and_shoulders_reclaim`: `READY`, `85` trades, `20.9801%`
  return, `1.988546` profit factor, `3.8958%` max drawdown

Warning-only expansion profiles:

- `bull_trap_breakout_warning`
- `double_top_neckline_failure`

These remain non-promotable trade profiles by design.

## 4. Data and Execution Limits

- The pack is EGX-only in v1.
- Intraday strategies remain hard-gated behind intraday EGX data availability.
- A `2026-04-29` intraday readiness review confirmed that liquid EGX30 names do
  have intraday OHLCV coverage, with sample names showing roughly `7k` to
  `11k` recent bars and sample coverage starting around `2026-02-10` to
  `2026-02-11`.
- The current full-market intraday backtest loop is substantially heavier than
  the daily pack and should be treated as a performance and workflow follow-up
  before broad intraday promotion decisions.
- A sampled intraday backtest mode was added on `2026-04-29` with bounded
  `ticker_limit`, `max_bars_per_ticker`, `max_trades`, and
  `recent_sessions_only` controls for faster research loops.
- Sampled intraday runs are explicitly marked `SAMPLED_INTRADAY` and are not
  promotion-eligible.
- Warning-only profiles do not create executable short entries.
- Promotion is required before scanner eligibility.
- Scanner defaults remain on existing Horus Core behavior unless a supported
  profile is explicitly selected or activated.

## 5. Intraday Research Snapshot

Sampled intraday run date: `2026-04-29`

Execution mode:

- market: `EGX30`
- window: `2026-02-10` to `2026-04-28`
- capital: `100000`
- commission: `0.05%`
- slippage: `0.1%`
- execution mode: `SAMPLED_INTRADAY`
- ticker limit: `5`
- max bars per ticker: `800`
- recent sessions only: `5`

Sampled results for the five new intraday additions:

- `intraday_support_reclaim_bullish_confirmation`: `DRAFT`, `204` trades,
  `-11.4726%` return, `0.0493` profit factor, `11.4878%` max drawdown
- `intraday_resistance_break_retest_reentry`: `DRAFT`, `43` trades, `-2.6265%`
  return, `0.050729` profit factor, `2.6265%` max drawdown
- `intraday_higher_high_higher_low_continuation`: `DRAFT`, `86` trades,
  `-5.4054%` return, `0.094652` profit factor, `5.5327%` max drawdown
- `intraday_selling_trap_reclaim`: `DRAFT`, `63` trades, `-3.7507%` return,
  `0.05213` profit factor, `3.7507%` max drawdown
- `intraday_trendline_break_reversal`: `DRAFT`, `51` trades, `-3.0562%`
  return, `0.073764` profit factor, `3.0562%` max drawdown

Current interpretation:

- the sampled intraday batch is firing often enough to evaluate
- liquidity coverage remained acceptable in the sample
- none of the five passed expectancy or profit-factor gates
- these strategies should remain research-only until execution assumptions,
  filters, or EGX intraday handling improve materially

Hardening follow-up run date: `2026-04-29`

Adjustment summary:

- added a minimum `Rel_Volume >= 1.15` quality gate
- required stronger trigger-bar closes and modest structure clearance
- widened structure-based stops slightly with ATR buffering
- trimmed first targets to better match observed intraday follow-through

Follow-up sampled results on the same bounded EGX30 research slice:

- `intraday_support_reclaim_bullish_confirmation`: `DRAFT`, `101` trades,
  `-5.375%` return, `0.051` profit factor, `5.375%` max drawdown
- `intraday_resistance_break_retest_reentry`: `DRAFT`, `22` trades,
  `-1.0504%` return, `0.082946` profit factor, `1.0861%` max drawdown
- `intraday_higher_high_higher_low_continuation`: `DRAFT`, `67` trades,
  `-3.6233%` return, `0.079859` profit factor, `3.6882%` max drawdown
- `intraday_selling_trap_reclaim`: `DRAFT`, `29` trades, `-1.5446%` return,
  `0.063497` profit factor, `1.5446%` max drawdown
- `intraday_trendline_break_reversal`: `DRAFT`, `37` trades, `-1.9781%`
  return, `0.080582` profit factor, `1.9781%` max drawdown

Interpretation of the hardening pass:

- the targeted filters cut signal volume materially across all five setups
- drawdowns improved meaningfully versus the first sampled pass
- the batch is still not viable as a promotable intraday group
- further work should focus on stronger session filters, entry timing, or
  rejecting the weakest setups rather than broadening the catalog further

Session and ticker-quality follow-up run date: `2026-04-29`

Adjustment summary:

- added a light preferred-session window for the two shortlisted survivors
- added a stronger ticker-quality gate using average turnover and setup-bar
  turnover
- limited this pass to:
  - `intraday_resistance_break_retest_reentry`
  - `intraday_selling_trap_reclaim`

Follow-up sampled results on the same bounded EGX30 research slice:

- `intraday_resistance_break_retest_reentry`: `DRAFT`, `17` trades,
  `-0.5438%` return, `0.148731` profit factor, `0.5865%` max drawdown
- `intraday_selling_trap_reclaim`: `DRAFT`, `20` trades, `-1.3438%` return,
  `0.026821` profit factor, `1.3438%` max drawdown

Interpretation of the survivor pass:

- `intraday_resistance_break_retest_reentry` improved again on trade count,
  return, and drawdown, but still failed expectancy and profit-factor gates
- `intraday_selling_trap_reclaim` reduced activity but still showed weak trade
  economics and does not currently justify more promotion-oriented tuning
- the cleanest next research candidate is
  `intraday_resistance_break_retest_reentry`
- `intraday_selling_trap_reclaim` should be treated as near-reject unless a
  materially different entry model changes the picture

Refined breakout-sequence follow-up run date: `2026-04-30`

Adjustment summary:

- tightened `intraday_resistance_break_retest_reentry` at the pattern level
- required a cleaner breakout close before the retest
- required the retest to hold and close more cleanly above reclaimed resistance
- kept the existing session and ticker-quality survivor gates in place
- formally de-emphasized `intraday_selling_trap_reclaim` as a research-only
  near-reject candidate

Follow-up sampled result on the same bounded EGX30 research slice:

- `intraday_resistance_break_retest_reentry`: `DRAFT`, `0` trades, `0.0%`
  return, `0.0` profit factor, `0.0%` max drawdown

Interpretation of the refined breakout pass:

- the stricter breakout-sequence model over-constrained the setup on the
  sampled slice
- this did reduce false positives completely, but it also removed usable
  opportunity flow
- `intraday_resistance_break_retest_reentry` remains the cleanest intraday
  research candidate conceptually, but this specific refined version should be
  treated as too strict rather than promotion-ready
- `intraday_selling_trap_reclaim` should remain de-emphasized unless a
  materially different entry thesis is proposed

## 6. Deferred or Rejected Concepts

Deferred:

- engulfing reversal confirmation
- pin bar reversal confirmation
- double top / double bottom reversal
- separate bullish rectangle continuation profile

Rejected for v1:

- indicator bundle strategies
- AI or machine-learning scalping
- crypto or forex-specific market assumptions
- proprietary TradingView indicator recipes

These decisions are documented in
`docs/superpowers/reference/2026-04-28-egx-price-action-extraction-catalog.md`.

## 7. Verification Completed

Backend regression:

```text
.\.venv313\Scripts\python.exe -m pytest tests/test_price_action_models.py tests/test_price_action_executor.py tests/test_price_action_routes.py tests/test_scanner_and_data.py tests/test_strategy_and_system.py tests/test_signal_validation.py -q
```

Result:

- `79 passed in 81.98s`

Frontend regression:

```text
cmd /c npm test --prefix frontend -- --runInBand --testPathPatterns src/app/strategy/page.test.tsx src/app/strategy/components/PriceActionLabPanel.test.tsx src/app/scanner/components/ScannerControls.test.tsx
```

Result:

- `3 passed, 19 tests total`

Import safety:

```text
.\.venv313\Scripts\python.exe -m py_compile core\price_action\__init__.py core\price_action\models.py core\price_action\catalog.py core\price_action\indicators.py core\price_action\patterns.py core\price_action\warnings.py core\price_action\scoring.py core\price_action\executor.py core\price_action\backtest.py core\price_action\scanner.py
```

Result:

- passed with no output

Source hygiene:

- extraction catalog was checked for disallowed copied phrasing and scope drift
- no long PDF passages were intentionally stored in the reference catalog

## 8. Test Coverage Notes

Current dedicated test files present in the repository:

- `tests/test_price_action_models.py`
- `tests/test_price_action_executor.py`
- `tests/test_price_action_routes.py`

Related integration and regression coverage:

- `tests/test_scanner_and_data.py`
- `tests/test_strategy_and_system.py`
- `tests/test_signal_validation.py`
- `frontend/src/app/strategy/components/PriceActionLabPanel.test.tsx`
- `frontend/src/app/scanner/components/ScannerControls.test.tsx`
- `frontend/src/app/strategy/page.test.tsx`

Planned-but-not-separate test files from the original implementation plan,
including dedicated `patterns`, `warnings`, and `backtest` suites, were not
split out as standalone files in this pass. Their behavior is covered through
the existing executor, route, scanner, and page-level tests instead.

## 9. Recommended Next Moves

- add standalone backend suites for `patterns`, `warnings`, and `backtest`
  behavior if we want tighter fault isolation
- expand strategy result visualization on the Strategy page
- add a short operator guide for catalog -> backtest -> promote -> activate
  workflow
- review intraday execution assumptions before promoting any of the new
  intraday setups
- only broaden the catalog after EGX historical behavior looks stable under the
  current promotion gates
