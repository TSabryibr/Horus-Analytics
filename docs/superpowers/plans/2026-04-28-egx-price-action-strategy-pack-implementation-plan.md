# Horus Analytics II EGX Price Action Strategy Pack Implementation Plan

Date: 2026-04-28
Based on:

- `docs/superpowers/specs/2026-04-28-egx-price-action-strategy-pack-design.md`
- `core/SignalEngine.py`
- `core/signal_validation.py`
- `core/pine_lab/profiles.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`
- `routes/scanner.py`
- `database.py`
- `tests/test_strategy_and_system.py`
- `tests/test_scanner_and_data.py`
- `frontend/src/app/strategy/components/StrategyShell.tsx`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`

Track: EGX Price Action Research Runtime, Backtesting, and Scanner Promotion
Status: Proposed plan
Owner model: Single owner

## 1. Planning Goal

This plan turns the approved EGX Price Action Strategy Pack design into an
ordered implementation sequence.

The implementation must leave eight things true:

1. The six supplied PDFs are used as one-time research inputs only.
2. Horus stores original, measurable EGX strategy definitions, not copied book
   text or long excerpts.
3. The strategy pack supports intraday, swing, and position families.
4. Long entries can become candidates; bearish logic only creates warnings,
   avoidance flags, blockers, or score reductions.
5. Each strategy emits structured explanations and stable signal contracts.
6. Backtesting and promotion gates exist before scanner eligibility.
7. Scanner integration is additive and does not replace Horus Core or Pine Lab.
8. Existing strategy, scanner, SignalEngine, Pine Lab, and signal lifecycle
   tests remain stable.

## 2. In Scope

Primary backend targets:

- new `core/price_action/__init__.py`
- new `core/price_action/catalog.py`
- new `core/price_action/models.py`
- new `core/price_action/indicators.py`
- new `core/price_action/patterns.py`
- new `core/price_action/warnings.py`
- new `core/price_action/scoring.py`
- new `core/price_action/executor.py`
- new `core/price_action/backtest.py`
- `routes/strategy.py`
- `routes/scanner.py`
- `database.py` only if the existing `ScannerStrategyProfile` contract cannot
  represent price-action profiles cleanly

Primary research/documentation targets:

- new `docs/superpowers/reference/2026-04-28-egx-price-action-extraction-catalog.md`
- optional new `core/price_action/research_catalog.py` or JSON catalog if the
  extracted definitions need a code-readable seed layer before final cataloging

Primary frontend targets:

- `frontend/src/app/strategy/components/StrategyShell.tsx`
- new or existing strategy components under `frontend/src/app/strategy/components/`
- `frontend/src/app/strategy/hooks/useStrategyRuntime.ts`
- `frontend/src/app/strategy/hooks/useStrategyActions.ts`
- optional Optimization surface updates under `frontend/src/app/optimization/`
  if the Strategy page becomes crowded

Primary test targets:

- new `tests/test_price_action_models.py`
- new `tests/test_price_action_patterns.py`
- new `tests/test_price_action_warnings.py`
- new `tests/test_price_action_executor.py`
- new `tests/test_price_action_backtest.py`
- new `tests/test_price_action_routes.py`
- `tests/test_scanner_and_data.py`
- `tests/test_strategy_and_system.py`
- targeted frontend tests if UI work lands in this slice

Out of scope:

- reusable PDF ingestion
- non-EGX markets
- short-selling execution
- broker routing changes
- broad SignalEngine rewrite
- broad Pine Lab changes
- storing copyrighted source passages in Horus
- enabling untested strategies in live scanner output

## 3. Execution Rules

These rules apply across all work packages:

1. Do not implement live scanner integration before extraction, contracts, and
   backtest gates exist.
2. Do not store long copied text from the PDFs. Extraction artifacts must be
   paraphrased into operator notes and measurable conditions.
3. Use EGX OHLCV and Horus context only. If a setup needs unavailable data, mark
   it unsupported or research-only.
4. Intraday strategies must explicitly fail or stay disabled when intraday data
   is unavailable.
5. Bearish logic must not emit executable short entries in v1.
6. New route handlers should stay thin and call reusable `core/price_action`
   services.
7. Promotion should reuse `ScannerStrategyProfile` if practical by adding a
   distinct `source_type`, such as `PRICE_ACTION`, rather than creating a new
   persistence model.
8. Existing Pine profile behavior must not be broadened or weakened to fit
   price-action profiles.
9. Frontend labels must make warning-only behavior explicit.
10. Each work package should leave targeted tests runnable before moving to the
    next package.

## 4. Target Module Map

### Research Artifact

- `docs/superpowers/reference/2026-04-28-egx-price-action-extraction-catalog.md`

Owns:

- extracted setup names
- source file attribution by filename/title only
- timeframe family
- measurable conditions
- warnings and blockers
- unsupported or rejected concepts
- confidence notes

### Backend Runtime

- `core/price_action/models.py`
- `core/price_action/indicators.py`
- `core/price_action/patterns.py`
- `core/price_action/warnings.py`
- `core/price_action/scoring.py`
- `core/price_action/catalog.py`
- `core/price_action/executor.py`

Owns:

- typed strategy definitions
- OHLCV feature computation
- pattern detection
- bearish warning detection
- score construction
- latest-bar evaluation
- structured signal payloads

### Backtesting and Promotion

- `core/price_action/backtest.py`
- `core/price_action/profiles.py` if profile logic grows beyond catalog/backtest
- `routes/strategy.py`
- `database.py` only if schema changes are required

Owns:

- historical evaluation
- promotion-gate summaries
- profile serialization
- scanner-eligible profile creation

### Scanner Integration

- `routes/scanner.py`
- optional `core/price_action/scanner.py`

Owns:

- selected or active price-action profile execution
- daily/intraday eligibility checks
- warning-only result propagation
- signal shape compatibility with current scanner output

### Frontend Surface

- `frontend/src/app/strategy/hooks/useStrategyRuntime.ts`
- `frontend/src/app/strategy/hooks/useStrategyActions.ts`
- `frontend/src/app/strategy/components/StrategyShell.tsx`
- optional new price-action components under `frontend/src/app/strategy/components/`

Owns:

- catalog display
- family filters
- backtest/evaluate actions
- metrics and readiness state
- warning-only labeling
- promotion action for passing strategies

## 5. Work Package Sequence

Execute this rollout in this order:

1. `PAS-P1` Source extraction catalog and v1 strategy shortlist
2. `PAS-P2` Backend contracts, models, and catalog scaffold
3. `PAS-P3` Pattern, warning, scoring, and executor runtime
4. `PAS-P4` Backtest runner and promotion gates
5. `PAS-P5` Strategy API endpoints
6. `PAS-P6` Scanner profile integration
7. `PAS-P7` Frontend strategy-pack surface
8. `PAS-P8` Hardening, regression, and closeout

This order is intentional:

- extraction determines what should be implemented
- contracts protect the scanner/API before behavior exists
- runtime logic must be testable before backtesting
- promotion gates must exist before scanner eligibility
- UI work should consume stable backend contracts
- hardening closes the loop after all surfaces are wired

## 6. Work Packages

### PAS-P1. Source Extraction Catalog and V1 Strategy Shortlist

Purpose:

Convert the six PDFs into a compact, copyright-safe, EGX-measurable research
catalog before any runtime code lands.

Target files:

- `docs/superpowers/reference/2026-04-28-egx-price-action-extraction-catalog.md`
- optional scratch notes under `scratch/` if temporary extraction notes are
  needed and kept out of commits

Tasks:

1. Review the six PDFs and capture candidate setups without copying long source
   text.
2. Normalize each candidate into:
   - setup name
   - timeframe family
   - market regime
   - entry conditions
   - confirmation conditions
   - bearish warnings and blockers
   - exits and risk model
   - required data
   - rejection reason if unsupported
3. Remove duplicates and vague discretionary rules.
4. Select a v1 shortlist with at least:
   - one intraday setup
   - one swing setup
   - one position setup
   - one warning-only bearish detector per family where practical
5. Mark intraday candidates that require true intraday data.
6. Add acceptance notes showing why retained setups can be expressed with EGX
   OHLCV data.

Deliverables:

- curated extraction catalog
- v1 strategy shortlist
- rejected/unsupported setup list

Verification:

- PowerShell: `Select-String -Path docs/superpowers/reference/2026-04-28-egx-price-action-extraction-catalog.md -Pattern "verbatim|copy|quote|short entry|crypto|forex|US equities"`

Acceptance criteria:

- catalog is paraphrased and implementation-ready
- retained setups have measurable EGX rules
- unsupported setups are explicitly rejected or deferred
- v1 contains intraday, swing, and position coverage

### PAS-P2. Backend Contracts, Models, and Catalog Scaffold

Purpose:

Create the price-action package and stable data contracts before implementing
strategy behavior.

Target files:

- `core/price_action/__init__.py`
- `core/price_action/models.py`
- `core/price_action/catalog.py`
- `tests/test_price_action_models.py`

Tasks:

1. Define enum-like constants or typed literals for:
   - timeframe family
   - signal type
   - readiness state
   - warning severity
   - profile source type
2. Define dataclasses or lightweight typed models for:
   - strategy definition
   - warning definition
   - evaluation context
   - evaluated signal
   - blocked candidate
   - promotion summary
3. Build an initial catalog from the PAS-P1 shortlist.
4. Add catalog lookup by strategy id, family, and readiness.
5. Add serialization helpers returning API-safe dicts.
6. Ensure bearish definitions cannot declare executable short entries.

Deliverables:

- importable `core.price_action` package
- stable catalog contract
- first model tests

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_price_action_models.py -q`

Acceptance criteria:

- strategy catalog loads without database access
- every catalog item has family, source attribution, required data, and rule
  metadata
- warning-only strategy definitions cannot be serialized as short entries

### PAS-P3. Pattern, Warning, Scoring, and Executor Runtime

Purpose:

Implement the reusable runtime that evaluates latest EGX bars into structured
signals, warnings, or blocked candidates.

Target files:

- `core/price_action/indicators.py`
- `core/price_action/patterns.py`
- `core/price_action/warnings.py`
- `core/price_action/scoring.py`
- `core/price_action/executor.py`
- `tests/test_price_action_patterns.py`
- `tests/test_price_action_warnings.py`
- `tests/test_price_action_executor.py`

Tasks:

1. Add shared OHLCV feature calculation:
   - ATR
   - relative volume
   - rolling highs/lows
   - candle body/range metrics
   - simple moving averages or EMAs only where required by selected setups
2. Implement retained pattern helpers from PAS-P1.
3. Implement bearish warning detectors as warning-only logic.
4. Build scoring from confirmations, warnings, liquidity, risk quality, and
   setup-specific weights.
5. Build executor functions that accept a ticker, OHLCV frame, strategy id or
   family, and evaluation mode.
6. Return `BUY`, `BUY_CANDIDATE`, `WARNING_ONLY`, or `BLOCKED` payloads.
7. Add synthetic fixture tests for fire, no-fire, warning, and blocked cases.

Deliverables:

- reusable indicator and pattern helpers
- warning-only detectors
- latest-bar strategy executor
- structured signal payload tests

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_price_action_patterns.py tests/test_price_action_warnings.py tests/test_price_action_executor.py -q`

Acceptance criteria:

- each v1 strategy can be evaluated on synthetic OHLCV data
- bearish warnings never return executable short entries
- blocked candidates explain their blocker
- output uses scanner-compatible price, stop, target, score, and explanation
  fields

### PAS-P4. Backtest Runner and Promotion Gates

Purpose:

Backtest price-action strategies under Horus assumptions and prevent weak
strategies from becoming scanner-eligible.

Target files:

- `core/price_action/backtest.py`
- optional `core/price_action/profiles.py`
- `tests/test_price_action_backtest.py`
- `tests/test_price_action_profiles.py` if a profile seam is created

Tasks:

1. Implement historical evaluation over one ticker and universe-level frames.
2. Use signal contract output to create simulated trades with:
   - entry
   - stop loss
   - target 1
   - optional target 2
   - horizon or exit rules from the catalog
3. Calculate summary metrics:
   - trade count
   - win rate
   - expectancy
   - profit factor
   - total return
   - max drawdown
   - warning conflict rate
4. Implement promotion gates from the design.
5. Build promotion summaries compatible with the current Pine profile style
   where possible.
6. Keep failed strategies inspectable but not scanner-eligible.

Deliverables:

- backtest runner
- promotion summary builder
- promotion gate tests

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_price_action_backtest.py -q`

Acceptance criteria:

- passing and failing strategies are distinguished deterministically
- low trade count, negative expectancy, excessive drawdown, and warning
  conflicts block promotion
- backtest summaries are API-serializable

### PAS-P5. Strategy API Endpoints

Purpose:

Expose the price-action pack through additive strategy endpoints while keeping
existing strategy and Pine routes stable.

Target files:

- `routes/strategy.py`
- `tests/test_price_action_routes.py`
- `tests/test_strategy_and_system.py`

Tasks:

1. Add `GET /api/v1/strategy/price-action/catalog`.
2. Add `POST /api/v1/strategy/price-action/evaluate`.
3. Add `POST /api/v1/strategy/price-action/backtest`.
4. Add `POST /api/v1/strategy/price-action/promote`.
5. Validate:
   - EGX-only universe choices
   - family and strategy ids
   - date windows
   - intraday data availability
   - promotion gate state
6. Reuse existing route error-handling style.
7. Ensure Pine routes and native `/api/v1/strategy/backtest` still behave the
   same.

Deliverables:

- additive price-action API
- route validation and error contracts
- backend route tests

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_price_action_routes.py tests/test_strategy_and_system.py -q`

Acceptance criteria:

- catalog, evaluate, backtest, and promote endpoints return stable payloads
- invalid market, unsupported strategy, unavailable intraday data, and failed
  promotion gates return clear errors
- existing strategy tests remain green

### PAS-P6. Scanner Profile Integration

Purpose:

Allow passing price-action strategies to become scanner-eligible profiles
without replacing Horus Core or Pine profiles.

Target files:

- `routes/scanner.py`
- `core/price_action/backtest.py`
- optional `core/price_action/profiles.py`
- `database.py` only if a schema extension is needed
- `tests/test_scanner_and_data.py`
- `tests/test_price_action_routes.py`

Tasks:

1. Reuse `ScannerStrategyProfile` with `source_type="PRICE_ACTION"` if it can
   store the needed catalog/profile metadata.
2. If extra metadata is required, prefer existing JSON fields before adding a
   migration.
3. Add a scanner execution seam for selected price-action profiles.
4. Preserve current Horus Core behavior when no price-action profile is
   selected.
5. Preserve Pine profile behavior and daily-only validation.
6. Normalize price-action output into current scanner signal fields:
   - `Ticker`
   - `Signal_Type`
   - `Signal_Setup`
   - `Entry_Price`
   - `Stop_Loss`
   - `Target_Price`
   - `Target_Price_2`
   - `Score`
   - warning and avoidance metadata
7. Ensure warning-only outputs do not create `Signal` records as buy signals.

Deliverables:

- scanner-compatible price-action profile execution
- source-specific scanner profile metadata
- scanner tests for selected price-action profile runs

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_scanner_and_data.py tests/test_price_action_routes.py -q`

Acceptance criteria:

- selected price-action profiles run through scanner without invoking Horus Core
  signal logic
- warning-only outputs are visible but do not become buy trades
- existing Pine scanner tests remain stable

### PAS-P7. Frontend Strategy-Pack Surface

Purpose:

Give the operator a usable Strategy page surface for catalog review, evaluation,
backtests, warnings, readiness, and promotion.

Target files:

- `frontend/src/app/strategy/hooks/useStrategyRuntime.ts`
- `frontend/src/app/strategy/hooks/useStrategyActions.ts`
- `frontend/src/app/strategy/components/StrategyShell.tsx`
- new `frontend/src/app/strategy/components/PriceActionStrategyPanel.tsx`
- new `frontend/src/app/strategy/components/PriceActionCatalogTable.tsx`
- new `frontend/src/app/strategy/components/PriceActionResultPanel.tsx`
- targeted tests under `frontend/src/app/strategy/`

Tasks:

1. Load the price-action catalog from the new API.
2. Add family filters for intraday, swing, and position.
3. Show readiness and required data.
4. Add evaluate/backtest actions.
5. Show metrics, signals, warnings, blockers, and explanations.
6. Add promotion action only when backend gates pass.
7. Label bearish output as warnings/avoidance, not short trades.
8. Keep existing Strategy proposal/manual-override behavior intact.

Deliverables:

- operator-facing price-action panel
- catalog and result components
- frontend tests for the new UI states

Verification:

- `cmd /c npm test -- --runInBand --testPathPatterns src/app/strategy/page.test.tsx src/app/strategy/components/PriceActionStrategyPanel.test.tsx`

Acceptance criteria:

- user can review catalog, run evaluation/backtest, inspect warnings, and
  promote passing strategies
- warning-only states are visibly distinct from buy candidates
- existing Strategy route tests remain green

### PAS-P8. Hardening, Regression, and Closeout

Purpose:

Run the broader verification set and close risk around route compatibility,
scanner behavior, frontend state, and data availability.

Target files:

- files touched by PAS-P1 through PAS-P7
- optional closeout note under `docs/superpowers/reference/`

Tasks:

1. Run targeted backend regression tests.
2. Run targeted frontend tests if PAS-P7 lands.
3. Verify import/compile safety for the new package.
4. Confirm no PDF source passages were committed.
5. Confirm live scanner defaults still use Horus Core unless a profile is
   explicitly selected or active by supported source type.
6. Add closeout notes with implemented strategy ids, skipped setups, and
   verification results.

Deliverables:

- final regression pass
- closeout summary
- documented v1 strategy ids and limitations

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_price_action_models.py tests/test_price_action_patterns.py tests/test_price_action_warnings.py tests/test_price_action_executor.py tests/test_price_action_backtest.py tests/test_price_action_routes.py tests/test_scanner_and_data.py tests/test_strategy_and_system.py -q`
- `cmd /c npm test -- --runInBand --testPathPatterns src/app/strategy/page.test.tsx src/app/strategy/components/PriceActionStrategyPanel.test.tsx`
- `.\.venv313\Scripts\python.exe -m py_compile core\\price_action\\models.py core\\price_action\\catalog.py core\\price_action\\indicators.py core\\price_action\\patterns.py core\\price_action\\warnings.py core\\price_action\\scoring.py core\\price_action\\executor.py core\\price_action\\backtest.py`

Acceptance criteria:

- all targeted tests pass or any residual failures are documented with cause
- scanner defaults are unchanged
- price-action profiles cannot bypass promotion gates
- closeout notes identify what made v1 and what was rejected/deferred

## 7. Risks and Controls

Risk: PDF concepts are discretionary and not measurable.

Control: PAS-P1 rejects vague setups before runtime work starts.

Risk: intraday setups are designed before reliable intraday EGX data is
available.

Control: intraday required-data gates are explicit in catalog, API, and tests.

Risk: bearish warnings accidentally behave like short entries.

Control: model tests, executor tests, scanner tests, and frontend labels enforce
warning-only behavior.

Risk: scanner profile storage becomes tangled with Pine profile assumptions.

Control: reuse `ScannerStrategyProfile` only through source-specific helper
functions and preserve Pine-specific activation rules.

Risk: the strategy pack overfits the books instead of EGX history.

Control: promotion gates require backtest metrics before scanner eligibility.

Risk: route handlers grow too large.

Control: keep route code as validation and orchestration; runtime behavior lives
under `core/price_action`.

## 8. Recommended Execution Notes

Start with PAS-P1 and PAS-P2 in one small implementation slice. That gives the
project a reviewed extraction artifact and an importable catalog contract before
any scanner or UI behavior changes.

Keep the first implemented catalog intentionally small. A good v1 target is
three to six long setups total plus warning detectors, not every concept in the
books.

Use daily-bar swing and position setups as the first executable path. Intraday
setups should be cataloged immediately, but execution should remain gated until
the available intraday data path is confirmed against Horus data quality.

## 9. Recommended Next Move After This Plan

Begin implementation with `PAS-P1`:

- create the extraction catalog
- review the six PDFs as research sources
- shortlist the first intraday, swing, and position setups
- mark unsupported or data-dependent setups before backend code begins

After PAS-P1 is complete, implement PAS-P2 so the selected setups have a stable
Horus catalog contract.
