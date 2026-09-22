# Horus Analytics II EGX Price Action Strategy Pack Design

Date: 2026-04-28
Status: Proposed
Authoring mode: Brainstorming-approved design

Based on:

- `core/SignalEngine.py`
- `core/signal_validation.py`
- `core/pine_lab/profiles.py`
- `routes/strategy.py`
- `routes/scanner.py`
- `frontend/src/app/strategy/components/StrategyShell.tsx`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `docs/superpowers/specs/2026-03-30-pine-egx-strategy-lab-design.md`
- `docs/superpowers/specs/2026-04-01-backtester-pine-profile-integration-design.md`

## 1. Purpose

This design defines a one-time EGX-only price action strategy pack for Horus.

The source material is a set of six trading PDFs supplied by the operator:

- `642655932-Price-Action-Patterns-2-0-Ebook-josh-trade-1.pdf`
- `573291545-Price-Action-Setup-Ebook.pdf`
- `700292689-Secrets-On-Reversal-Trading-Frank-Miller.pdf`
- `880862988-High-Probability-Scalping-Strategy-Playbook.pdf`
- `733203264-High-Win-Rate-Day-Trading-Setups-High-Win-Rate-Day-Trading-Robbinson-Marcel-2022-2d3241b9e950c5dd0f21d96918c65f4e-Anna-s-Archive.pdf`
- `809567256-Day-Trading-Entries-and-Exits-The-Best-Day-Trading-Entry-and-Exit-Signals-for-Forex-Stocks-and-Cryptocurrency-in-2024-High-Harnett-David-Z-Li.pdf`

The books are research inputs only. Horus will store original rule definitions,
not copied book text or long excerpts.

## 2. Product Outcome

Horus should gain a curated EGX Price Action Strategy Pack with three signal
families:

- Intraday strategies for fast continuation, reversal, range, and volume-driven
  opportunities.
- Swing strategies for multi-day breakout, pullback, retest, and reversal
  setups.
- Position strategies for slower trend, accumulation, and regime-aligned setups.

The pack should produce long trade candidates only. Bearish or short-side ideas
from the source material become warnings, avoidance flags, score reducers, and
entry blockers rather than executable short entries.

## 3. Goals

This work should leave these things true:

1. EGX price action setups from the supplied books are converted into original,
   measurable Horus rules.
2. Strategies are grouped by intraday, swing, and position trading intent.
3. Long entries are supported; bearish logic is warning-only in v1.
4. Each strategy can explain why it fired, why it was blocked, and what warnings
   were present.
5. Candidate strategies are backtested and gated before scanner promotion.
6. Existing SignalEngine, Pine Lab, scanner, and strategy flows keep working.

## 4. Non-Goals

This design does not attempt to:

- Build a reusable PDF ingestion pipeline for future books.
- Add crypto, forex, US equities, or non-EGX markets.
- Store or republish long copyrighted passages from the PDFs.
- Create live short-selling entries.
- Replace the existing Horus signal engine or Pine Lab.
- Promote untested strategies directly to live alerts.
- Support subjective visual-only chart patterns that cannot be expressed with
  available EGX data.

## 5. Source Extraction Workflow

The extraction process is manual and controlled:

1. Review the six PDFs and capture candidate setups in a local research table.
2. Normalize each setup into Horus fields:
   `setup_name`, `timeframe_family`, `market_regime`, `entry_conditions`,
   `confirmation`, `avoidance_rules`, `exit_rules`, `risk_model`,
   `required_data`, and `confidence_notes`.
3. Remove duplicates, vague discretionary setups, and rules that need data Horus
   does not have.
4. Rewrite retained setups as original Horus rule definitions.
5. Implement the final set as versioned strategy definitions.
6. Backtest each strategy family before any scanner promotion.

The extraction artifact should preserve lightweight source attribution by book
filename/title and high-level concept, without copying expressive source text.

## 6. Recommended Approach

Use a curated Horus-native strategy pack.

Alternative approaches were considered:

- Pine Lab first: useful when rules map cleanly to Pine profiles, but less
  suitable for discretionary price action setups.
- Signal overlay only: safer and smaller, but it would not create the requested
  intraday, swing, and position strategy library.

The recommended approach is Horus-native strategy definitions with a warning
overlay. This gives Horus explainable, testable EGX rules while allowing bearish
patterns to act as safety brakes.

## 7. Architecture

Add a focused backend package:

```text
core/price_action/
  __init__.py
  catalog.py
  models.py
  indicators.py
  patterns.py
  warnings.py
  scoring.py
  executor.py
  backtest.py
```

Responsibilities:

- `catalog.py` owns strategy definitions and metadata.
- `models.py` defines typed strategy, signal, warning, and evaluation payloads.
- `indicators.py` computes shared EGX OHLCV features.
- `patterns.py` detects candle, breakout, retest, pullback, range, and reversal
  structures.
- `warnings.py` detects bearish warning-only conditions.
- `scoring.py` combines confirmations, warnings, liquidity, regime, and risk
  quality into a score.
- `executor.py` evaluates strategies on latest bars and returns structured
  signals.
- `backtest.py` adapts the pack to Horus backtesting and promotion gates.

This package should be additive. Existing `core/SignalEngine.py` can call into
it later, but the new logic should not be mixed directly into the legacy signal
functions.

## 8. Strategy Families

### Intraday

Intraday strategies should target fast EGX opportunities, using available
intraday bars when present and falling back to explicit unavailable-data errors
when they are not.

Expected setup types:

- Opening range expansion.
- Range breakout with relative volume confirmation.
- Pullback continuation near short moving averages.
- Failed breakout warning.
- High-volume reversal warning.

### Swing

Swing strategies should target multi-day moves using daily EGX bars.

Expected setup types:

- Breakout and close above prior resistance.
- Pullback and retest after breakout.
- Reversal from support with volume confirmation.
- Trend continuation after compression.
- Distribution or failed retest warning.

### Position

Position strategies should target slower trades aligned with broad market and
stock-level structure.

Expected setup types:

- Higher-high and higher-low trend continuation.
- Accumulation range breakout.
- Regime-aligned leadership setup.
- Extended move exhaustion warning.
- Slow distribution warning.

The exact final strategies are decided during extraction. The pack should prefer
fewer high-quality measurable strategies over a large collection of weakly
defined patterns.

## 9. Signal Contract

Each evaluated strategy should return a structured payload:

```json
{
  "signal_type": "BUY_CANDIDATE",
  "timeframe_family": "SWING",
  "ticker": "COMI",
  "setup_name": "Breakout Retest Continuation",
  "entry_price": 83.5,
  "stop_loss": 79.9,
  "target_1": 88.4,
  "target_2": 93.1,
  "score": 78,
  "confirmations": ["Resistance reclaimed", "Relative volume confirmed"],
  "warnings": ["Market regime is cautious"],
  "avoidance_flags": [],
  "explanation": "Price reclaimed prior resistance and retested above it with acceptable liquidity."
}
```

Allowed `signal_type` values in v1:

- `BUY`
- `BUY_CANDIDATE`
- `WARNING_ONLY`
- `BLOCKED`

Bearish strategy output must never produce a short entry. It may:

- lower score
- block a long candidate
- create a warning-only alert
- mark an existing setup as risky
- explain why Horus avoided a trade

## 10. Promotion Gates

Before a strategy can become scanner-eligible, it must pass gates such as:

- minimum trade count
- positive expectancy
- profit factor threshold
- maximum drawdown cap
- minimum liquidity coverage
- acceptable warning conflict rate
- stable performance across EGX30 and broader EGX universes where applicable
- no lookahead or unavailable-data dependency

Failed strategies stay in research or draft state and can still be inspected,
but they cannot drive live scanner output.

## 11. API Design

Extend `routes/strategy.py` with additive endpoints:

- `GET /api/v1/strategy/price-action/catalog`
  Lists families, setup names, metadata, and readiness state.

- `POST /api/v1/strategy/price-action/evaluate`
  Evaluates selected strategies for selected tickers/universe and returns
  structured signals, warnings, and blocked candidates.

- `POST /api/v1/strategy/price-action/backtest`
  Runs historical tests for a strategy, family, or full pack.

- `POST /api/v1/strategy/price-action/promote`
  Promotes a passing strategy into a scanner-eligible profile.

These endpoints should use the same defensive validation style already present
in `routes/strategy.py`.

## 12. Frontend Surface

The first implementation can expose the pack inside the existing Strategy or
Optimization areas rather than creating a new top-level app section.

Minimum useful UI:

- strategy family filter: intraday, swing, position
- strategy catalog table
- run/backtest action
- readiness state
- metrics summary
- generated signal previews
- warnings and blocked-candidate explanations
- promote action for passing strategies

The UI should make it clear that bearish outputs are warnings and avoidance
signals, not short trades.

## 13. Error Handling

The pack should fail explicitly when:

- intraday data is unavailable for intraday-only setups
- required OHLCV fields are missing
- a setup needs more historical bars than available
- a strategy definition is malformed
- backtest windows are too short
- promotion gates are not met

Errors should return actionable messages and should not affect existing strategy
or scanner endpoints.

## 14. Testing

Testing should be layered:

1. Unit tests for candle classification, pattern helpers, warnings, scoring, and
   ATR/risk calculations.
2. Synthetic fixture tests proving each setup fires and stays quiet correctly.
3. Backtest tests proving each family returns stable metrics and trade logs.
4. Promotion tests proving weak strategies remain draft/research only.
5. Route tests for catalog, evaluation, backtest, and promotion endpoints.
6. Regression tests around existing SignalEngine, Pine Lab, scanner, and
   strategy APIs.

## 15. Success Criteria

The first release is successful when:

- Horus has a compact EGX price action strategy catalog.
- At least one intraday, one swing, and one position setup can be evaluated.
- Bearish patterns are visible as warnings or blockers.
- Backtesting produces trustworthy metrics for each implemented setup.
- Only passing strategies can become scanner-eligible.
- Existing live, scanner, strategy, and Pine Lab flows remain stable.

## 16. Open Implementation Decisions

These can be resolved during implementation planning:

- Exact number of strategies included in v1.
- Whether the catalog is stored as Python definitions, JSON, or both.
- Whether scanner promotion reuses `ScannerStrategyProfile` or gets a
  price-action-specific profile type.
- Whether intraday setups require a hard intraday-data gate or can offer
  daily-bar approximations for research only.
