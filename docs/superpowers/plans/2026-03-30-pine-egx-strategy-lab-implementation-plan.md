# Horus Analytics II Pine EGX Strategy Lab Implementation Plan

Date: 2026-03-30
Based on:

- `docs/superpowers/specs/2026-03-30-pine-egx-strategy-lab-design.md`
- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/components/OptimizationShell.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.ts`
- `frontend/src/app/scanner/page.tsx`
- `frontend/src/app/scanner/hooks/useScannerRuntime.ts`
- `frontend/src/app/scanner/hooks/useScannerExecution.ts`
- `routes/strategy.py`
- `routes/scanner.py`
- `core/DailyScanner.py`
- `core/SignalEngine.py`
- `PortfolioSimulator.py`
- `database.py`

Track: Pine Research Runtime, EGX Backtesting, and Scanner Profile Promotion
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved Pine EGX Strategy Lab design into an implementation sequence that fits the current Horus architecture.

The implementation must leave seven things true:

1. Existing Horus-native optimization flows keep working without payload or behavior regressions.
2. Pine scripts go through a preflight compatibility gate before any backtest runs.
3. Pine backtests run on EGX data using Horus execution assumptions rather than silent TradingView approximations.
4. Result ranking supports both pure performance and combined score.
5. Scanner profile promotion is additive and does not replace the current scanner engine.
6. Scanner start and DailyScanner execution can select a promoted Pine profile explicitly.
7. Unsupported or ambiguous Pine behavior fails clearly and testably.

## 2. In Scope

Primary backend targets:

- `routes/strategy.py`
- `routes/scanner.py`
- `core/DailyScanner.py`
- `PortfolioSimulator.py` if shared simulation seams are reusable
- new Pine runtime seams under `core/`
- profile persistence updates in `database.py` or a closely related storage seam

Primary frontend targets:

- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/components/OptimizationShell.tsx`
- new Pine Lab components and hooks under `frontend/src/app/optimization/`
- `frontend/src/app/scanner/page.tsx`
- `frontend/src/app/scanner/components/ScannerControls.tsx`
- `frontend/src/app/scanner/hooks/useScannerRuntime.ts`
- `frontend/src/app/scanner/hooks/useScannerExecution.ts`

Primary workflow capabilities to add:

- Pine preflight
- Pine backtest
- Pine ranking and recommendation
- Pine scanner profile creation
- scanner profile selection during scan execution

Out of scope for this phase:

- MT4 or MT5 support
- full TradingView parity
- automatic live activation of promoted Pine profiles
- broad scanner UI redesign unrelated to profile selection
- strategy replacement of the current Horus engine
- broker execution or order routing

## 3. Current Constraints

These existing facts shape the rollout:

1. `frontend/src/app/optimization/page.tsx` only supports `SIMULATOR` and `OPTIMIZER`.
2. `frontend/src/app/scanner/hooks/useScannerExecution.ts` currently starts scans with only `index` and `intraday`.
3. `routes/scanner.py` passes only `index_choice` and `is_intraday` into `DailyScanner.get_market_signals(...)`.
4. `core/DailyScanner.py` currently uses Horus-native signal logic and has no external strategy profile seam.
5. `routes/strategy.py` currently supports only numeric Horus params for backtests.
6. `database.py` does not currently define a scanner profile model for promoted Pine strategies.

The plan must address each of those constraints explicitly rather than hiding them inside one oversized feature package.

## 4. Execution Rules

These rules apply across all work packages:

1. No Pine execution without a preflight gate.
2. No new Pine behavior should live only inside route handlers; parsing, compatibility, execution, ranking, and profile storage must have reusable seams.
3. No scanner promotion without explicit persistence and retrieval behavior.
4. No scanner execution branch should silently switch logic; selected scanner profile must be explicit in request, runtime, and diagnostics.
5. No unsupported Pine feature may be silently ignored in a way that changes trade behavior.
6. No frontend mode or scanner-control expansion without direct tests.
7. Prefer additive changes to existing routes and components rather than rewriting working optimization or scanner surfaces.

## 5. Target Module Map

The implementation should converge on this shape.

### Backend runtime seams

- `core/pine_lab/models.py`
- `core/pine_lab/parser.py`
- `core/pine_lab/capabilities.py`
- `core/pine_lab/signal_normalizer.py`
- `core/pine_lab/executor.py`
- `core/pine_lab/ranking.py`
- `core/pine_lab/profiles.py`

### Backend route seams

- `routes/strategy.py`
- `routes/scanner.py`

### Backend persistence seams

- `database.py`
- optional extraction helper under `core/` if profile storage logic grows beyond one file

### Frontend optimization seams

- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/hooks/usePinePreflight.ts`
- `frontend/src/app/optimization/hooks/usePineBacktest.ts`
- `frontend/src/app/optimization/hooks/usePineProfilePromotion.ts`

### Frontend scanner seams

- `frontend/src/app/scanner/components/ScannerControls.tsx`
- `frontend/src/app/scanner/hooks/useScannerRuntime.ts`
- `frontend/src/app/scanner/hooks/useScannerExecution.ts`

The route pages should remain composition owners. New behavior should be pushed behind focused hooks and runtime helpers.

## 6. Work Package Sequence

Execute this slice in the following order:

1. `PSL-P1` Contract scaffolding and profile persistence
2. `PSL-P2` Pine preflight parser and compatibility gate
3. `PSL-P3` EGX executor and ranking service
4. `PSL-P4` Optimization Pine Lab UI
5. `PSL-P5` Scanner profile selection and execution integration
6. `PSL-P6` Hardening, promotion gates, and closeout

This order is intentional:

- profile and API scaffolding must exist before UI wiring can land cleanly
- preflight must exist before any backtest execution
- ranking belongs on top of a stable backtest contract
- scanner integration should consume a stable stored profile rather than raw Pine text pasted at runtime
- hardening closes the loop after both research and scanner flows are wired

## 7. Work Packages

### PSL-P1. Contract Scaffolding and Profile Persistence

Purpose:

Create the foundational storage and API shapes so Pine research can exist as a first-class capability.

Target files:

- `database.py`
- `routes/strategy.py`
- new `core/pine_lab/models.py`
- new `core/pine_lab/profiles.py`
- targeted tests

Tasks:

1. Define normalized runtime models for:
   - preflight result
   - backtest result
   - ranking result
   - promoted scanner profile
2. Add a persistence seam for promoted Pine scanner profiles.
3. Decide and implement the storage contract:
   - preferred: new Peewee model in `database.py`
   - fallback: explicit JSON-backed registry only if database storage proves infeasible
4. Add route placeholders or initial handlers for:
   - `POST /api/v1/strategy/pine/preflight`
   - `POST /api/v1/strategy/pine/backtest`
   - `POST /api/v1/strategy/pine/create-scanner-profile`
5. Add read-side support for listing available scanner profiles if the scanner UI will need it immediately.

Deliverables:

- normalized Pine runtime contract
- persistent scanner-profile storage seam
- initial Pine route contract

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_strategy_and_system.py -q`

Acceptance criteria:

- Pine routes exist behind explicit handlers
- promoted profiles can be created and retrieved through a stable backend seam
- existing strategy routes remain backward compatible

### PSL-P2. Pine Preflight Parser and Compatibility Gate

Purpose:

Block unsupported Pine behavior before execution and surface trustable operator feedback.

Target files:

- `core/pine_lab/parser.py`
- `core/pine_lab/capabilities.py`
- `routes/strategy.py`
- targeted tests

Tasks:

1. Implement Pine source parsing focused on:
   - script type detection
   - entry/exit detection
   - long/short capability detection
   - unsupported feature discovery
2. Define explicit capability categories:
   - supported
   - limited
   - blocked
3. Reject:
   - visual-only indicators
   - ambiguous entry or exit logic
   - unsupported order semantics
   - constructs Horus cannot reproduce reliably
4. Make preflight responses return:
   - compatibility score
   - readiness state
   - unsupported features
   - operator-readable messages
5. Add test fixtures for:
   - compatible strategy
   - signal-capable indicator
   - blocked visual indicator
   - unsupported platform-specific behavior

Deliverables:

- reusable Pine parser seam
- explicit compatibility vocabulary
- stable preflight route behavior

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_pine_preflight.py -q`

Acceptance criteria:

- no Pine backtest can run without successful or limited preflight
- unsupported features are surfaced explicitly rather than ignored
- compatibility responses are deterministic and test-backed

### PSL-P3. EGX Executor and Ranking Service

Purpose:

Turn compatible Pine logic into EGX backtest results and ranking outputs.

Target files:

- `core/pine_lab/signal_normalizer.py`
- `core/pine_lab/executor.py`
- `core/pine_lab/ranking.py`
- `routes/strategy.py`
- `PortfolioSimulator.py` only if shared backtest helpers can be reused safely
- targeted tests

Tasks:

1. Normalize Pine entry and exit logic into Horus trade-event primitives.
2. Reuse existing Horus execution assumptions where practical:
   - capital
   - slippage
   - commission
   - EGX history loading
3. Define the initial execution contract clearly:
   - bar-based execution
   - deterministic fill assumptions
   - long-first support unless short support is validated cleanly
4. Return a normalized backtest payload that includes:
   - metrics
   - assumptions
   - equity curve
   - trades
   - compatibility metadata
5. Implement ranking outputs:
   - pure performance score
   - alignment score
   - combined score
   - recommendation summary
6. Add alignment logic against Horus signals over the same window.

Deliverables:

- Pine signal-normalization seam
- EGX backtest executor
- ranking and recommendation seam

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_pine_backtest.py tests/test_pine_ranking.py -q`

Acceptance criteria:

- Pine backtest responses are stable and consumable by the frontend
- both pure and combined ranking outputs exist
- ranking math is test-backed and operator-explainable

### PSL-P4. Optimization Pine Lab UI

Purpose:

Expose Pine research cleanly inside the existing optimization route without regressing current modes.

Target files:

- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/components/OptimizationShell.tsx`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/hooks/usePinePreflight.ts`
- `frontend/src/app/optimization/hooks/usePineBacktest.ts`
- `frontend/src/app/optimization/hooks/usePineProfilePromotion.ts`
- related tests

Tasks:

1. Extend optimization mode support to include `PINE_LAB`.
2. Add Pine Lab controls for:
   - source input
   - market selection
   - timeframe
   - date range
   - capital
   - slippage
   - commission
3. Add preflight action and compatibility report rendering.
4. Add backtest action and results rendering:
   - leaderboard
   - recommendation summary
   - equity curve
   - trade log
5. Add promotion action wired to the scanner-profile creation route.
6. Keep current `SIMULATOR` and `OPTIMIZER` flows untouched.

Deliverables:

- third optimization mode
- Pine Lab panel and hooks
- frontend support for Pine preflight, backtest, and promotion

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/optimization/page.test.tsx src/app/optimization/components/PineLabPanel.test.tsx`

Acceptance criteria:

- Pine Lab mode renders and operates independently of existing optimization modes
- failed preflight prevents backtest action
- recommendation and promotion UI states are test-backed

### PSL-P5. Scanner Profile Selection and Execution Integration

Purpose:

Let operators select a promoted Pine profile from the scanner surface and run scans explicitly against it.

Target files:

- `frontend/src/app/scanner/page.tsx`
- `frontend/src/app/scanner/components/ScannerControls.tsx`
- `frontend/src/app/scanner/hooks/useScannerRuntime.ts`
- `frontend/src/app/scanner/hooks/useScannerExecution.ts`
- `routes/scanner.py`
- `core/DailyScanner.py`
- new `core/pine_lab/profiles.py` helpers if needed
- targeted tests

Tasks:

1. Extend scanner UI state to include selected strategy profile.
2. Add scanner-controls UI for choosing:
   - default Horus logic
   - promoted Pine profiles
3. Extend scanner-start requests to include a selected profile identifier.
4. Extend `routes/scanner.py` to pass the selected profile into the scanner runtime.
5. Add an execution seam in `core/DailyScanner.py` so scanner behavior can choose between:
   - native Horus strategy
   - promoted Pine strategy profile
6. Ensure scanner result metadata makes the active profile visible.

Deliverables:

- scanner profile selector
- explicit scanner profile request contract
- DailyScanner profile-selection seam

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py tests/test_pine_profile_promotion.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner/page.test.tsx src/app/scanner/hooks/useScannerExecution.test.tsx`

Acceptance criteria:

- scanner runs explicitly against the chosen profile
- Horus default remains the fallback when no Pine profile is selected
- scanner diagnostics can show which profile produced the signals

### PSL-P6. Hardening, Promotion Gates, and Closeout

Purpose:

Make the full Pine research-to-scanner workflow trustworthy enough to ship.

Target files:

- `routes/strategy.py`
- `core/pine_lab/*`
- `routes/scanner.py`
- frontend result surfaces if additive messaging is needed
- targeted tests and docs

Tasks:

1. Enforce promotion gates:
   - minimum trade count
   - positive total return
   - max drawdown ceiling
   - compatibility-score floor
   - data-coverage floor
2. Improve operator-facing failure states for:
   - parse failure
   - compatibility failure
   - execution failure
   - promotion failure
3. Add end-to-end workflow coverage:
   - preflight
   - backtest
   - recommend
   - create profile
   - scan with profile
4. Update any operator-facing documentation needed for Pine Lab and scanner profile use.

Deliverables:

- enforced promotion gates
- full workflow hardening
- end-to-end regression coverage

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_pine_preflight.py tests/test_pine_backtest.py tests/test_pine_ranking.py tests/test_pine_profile_promotion.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/optimization/page.test.tsx src/app/scanner/page.test.tsx`

Acceptance criteria:

- no profile can be promoted without passing defined quality bars
- full workflow failures are understandable to operators
- scanner can consume a promoted profile without regressing default behavior

## 8. Testing Strategy

Keep these existing route anchors green while expanding coverage:

- `frontend/src/app/optimization/page.test.tsx`
- `frontend/src/app/scanner/page.test.tsx`
- `frontend/src/app/scanner/hooks/useScannerExecution.test.tsx`

Add new backend tests:

- `tests/test_pine_preflight.py`
- `tests/test_pine_backtest.py`
- `tests/test_pine_ranking.py`
- `tests/test_pine_profile_promotion.py`

Add new frontend tests:

- `frontend/src/app/optimization/components/PineLabPanel.test.tsx`
- targeted hook tests for Pine preflight, backtest, and promotion

The test progression should be:

1. lock contract seams first
2. add runtime tests for parser and executor
3. add UI tests once route wiring lands
4. add one end-to-end operator-path test last

## 9. Risk Controls

### Risk: Pine compatibility expands faster than trust can keep up

Control:

- make preflight mandatory
- keep capability reporting explicit

### Risk: scanner profile support sprawls into a scanner rewrite

Control:

- isolate profile selection behind one request/runtime seam
- keep Horus default path intact

### Risk: promoted profiles are stored inconsistently

Control:

- establish one canonical persistence model before UI promotion ships

### Risk: result scoring becomes opaque

Control:

- keep pure and combined rankings both visible
- keep score inputs explicit in the backend contract

## 10. Closeout Criteria

This implementation plan is complete when:

1. Pine Lab exists as a third optimization mode.
2. Pine scripts can be preflighted and backtested on EGX.
3. Ranking supports both performance-only and combined scoring.
4. Winning profiles can be promoted into persistent scanner profiles.
5. Scanner execution can explicitly select and run a promoted profile.
6. Existing Horus-native optimization and scanner flows remain intact.

## 11. Summary

The correct delivery path is:

1. establish storage and route contracts
2. build a strict preflight gate
3. build a trustworthy EGX executor and ranking layer
4. expose Pine research in the optimization UI
5. wire promoted profiles into scanner selection
6. harden the workflow before calling it done

That sequence gets Horus to the real product goal without pretending the missing seams already exist:

find the best Pine-driven EGX strategy, recommend it, store it as a scanner profile, and let operators run the scanner against it deliberately.
