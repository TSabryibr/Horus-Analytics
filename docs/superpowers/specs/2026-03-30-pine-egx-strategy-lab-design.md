# Horus Analytics II Pine EGX Strategy Lab Design

Date: 2026-03-30
Status: Proposed
Authoring mode: Brainstorming-approved design

Based on:

- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/components/OptimizationShell.tsx`
- `frontend/src/app/optimization/components/BacktestLabPanel.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.ts`
- `frontend/src/app/scanner/components/ScannerControls.tsx`
- `routes/strategy.py`
- `core/SignalEngine.py`
- `core/DailyScanner.py`
- `PortfolioSimulator.py`
- `docs/superpowers/specs/2026-03-18-phase-8-optimization-decomposition-design.md`

## 1. Purpose

This design defines a new Pine-first research workflow inside Horus that can:

- ingest Pine scripts that emit entry and exit signals
- preflight those scripts against Horus compatibility rules
- backtest them on EGX market data under Horus execution assumptions
- rank them by both pure backtest performance and a combined score
- recommend the best candidate for promotion into Horus as a new selectable scanner profile

The phase 1 goal is not general script execution across all platforms.

The phase 1 goal is specifically:

- Pine strategy and signal-capable Pine indicator evaluation for EGX
- inside the existing Horus optimization surface
- with promotion into the scanner as an additive profile, not a replacement

## 2. Product Outcome

The operator-facing outcome should be:

1. Open the Strategy Lab page.
2. Switch to a new Pine-focused mode.
3. Paste a Pine strategy or indicator that clearly defines entries and exits.
4. Run preflight to see whether Horus can execute it reliably on EGX data.
5. Backtest the compatible script.
6. Review leaderboard, metrics, trade log, equity curve, and Horus alignment data.
7. Promote the winning script into Horus as a new scanner profile.

That profile then becomes selectable alongside existing scanner behavior instead of mutating the current engine.

## 3. Design Goals

This package should leave six things true:

1. Horus can evaluate Pine scripts without breaking the existing numeric backtest flow.
2. The app rejects unsupported or ambiguous Pine behavior before any backtest runs.
3. EGX backtests use Horus execution assumptions rather than silent TradingView approximations.
4. The result surface ranks candidates by both pure performance and combined score.
5. Promotion creates a new scanner profile rather than replacing the current scanner engine.
6. Unsupported behavior fails explicitly instead of producing misleading results.

## 4. Non-Goals

Phase 1 does not attempt to:

- support MT4 or MT5 execution
- guarantee full TradingView parity across all Pine semantics
- replace the existing Horus scanner logic
- auto-activate Pine winners into live production without operator review
- support indicators that are visual-only and do not define executable entry and exit conditions
- redesign the optimization page outside the new Pine Lab capability

## 5. Current State

The current optimization surface already supports:

- `SIMULATOR` mode for Horus-native parameter backtests
- `OPTIMIZER` mode for AI optimizer control

Those flows are implemented in:

- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/components/OptimizationShell.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.ts`

The current backend route:

- `POST /api/v1/strategy/backtest`

accepts only Horus-native numeric parameters and runs `PortfolioSimulator.run_simulation(...)` from `routes/strategy.py`.

There is no existing Pine parser, compatibility checker, or script-to-scanner promotion layer in the codebase.

## 6. Recommended Approach

Three approaches were considered:

### Option 1. Native Pine-on-Horus runtime

Import Pine code into Horus, validate it against a supported execution contract, normalize the logic into Horus signal primitives, and run the backtest locally on EGX data.

Pros:

- strongest integration with the existing app
- best path to scanner profile promotion
- clean control over EGX assumptions
- supports ranking by both pure performance and Horus alignment

Cons:

- requires new parser, validation, and runtime layers
- requires explicit compatibility boundaries

### Option 2. External execution bridge

Use an outside engine for Pine-like execution and import results into Horus later.

Pros:

- can appear closer to TradingView behavior

Cons:

- weaker EGX control
- weaker scanner integration
- introduces an external dependency for a core workflow

### Option 3. Broad Pine-to-Python translation

Try to translate most Pine scripts directly into Python execution logic.

Pros:

- ambitious compatibility story

Cons:

- highest implementation risk
- hard to trust at edge cases
- likely to produce brittle behavior in a first release

### Recommendation

Use Option 1.

This gives Horus a first-class Pine research workflow that fits the current optimization and scanner architecture without overpromising full TradingView parity.

## 7. User Workflow

Phase 1 should introduce a third optimization mode:

- `SIMULATOR`
- `OPTIMIZER`
- `PINE_LAB`

The `PINE_LAB` workflow should be:

### 7.1 Input

Allow the operator to:

- paste Pine source code
- optionally upload a Pine file in a later increment
- choose EGX universe: `EGX30`, `EGX70`, `EGX100`, or `ALL`
- choose timeframe
- choose date range
- set capital
- set slippage and commission assumptions

### 7.2 Preflight

Before backtest, Horus should inspect the Pine script and return:

- detected script type
- detected long and short capability
- detected entry and exit constructs
- unsupported functions or ambiguous behavior
- compatibility score
- readiness verdict: `READY`, `LIMITED`, or `BLOCKED`

### 7.3 Backtest

When the script is compatible enough to run, Horus should execute it on EGX bars and return:

- summary metrics
- equity curve
- trades
- compatibility metadata
- Horus alignment metadata
- ranking outputs

### 7.4 Recommendation

Horus should recommend one winner while still showing the raw leaderboard.

The recommendation should not auto-change the live scanner.

### 7.5 Promotion

If the winner passes minimum promotion thresholds, Horus should create a new scanner profile that becomes selectable in scanner workflows.

## 8. Frontend Design

### 8.1 Optimization shell

Extend `frontend/src/app/optimization/components/OptimizationShell.tsx` to add a third mode button for Pine Lab.

Keep the existing `SIMULATOR` and `OPTIMIZER` flows untouched.

### 8.2 Route composition

Extend `frontend/src/app/optimization/page.tsx` to render a new Pine panel when mode is `PINE_LAB`.

Suggested component seam:

- `frontend/src/app/optimization/components/PineLabPanel.tsx`

Suggested hook seams:

- `frontend/src/app/optimization/hooks/usePinePreflight.ts`
- `frontend/src/app/optimization/hooks/usePineBacktest.ts`
- `frontend/src/app/optimization/hooks/usePineProfilePromotion.ts`

### 8.3 Pine Lab panel content

The panel should include:

- Pine source editor or textarea
- detected script badge
- market selector
- timeframe selector
- date range selector
- capital and execution assumption inputs
- `Preflight` action
- `Run Backtest` action
- compatibility report area
- leaderboard and recommendation area
- promotion action

### 8.4 Result presentation

The result surface should show:

- total return
- final value
- max drawdown
- win rate
- trade count
- consistency or Sharpe-like quality metric
- equity curve
- trade log
- Horus alignment summary
- pure performance rank
- combined score rank

The UI should clearly label which ranking is being shown so operators do not confuse "best return" with "best overall fit for Horus".

## 9. Backend API Contract

Keep the current route unchanged:

- `POST /api/v1/strategy/backtest`

Add Pine-specific routes in `routes/strategy.py`:

- `POST /api/v1/strategy/pine/preflight`
- `POST /api/v1/strategy/pine/backtest`
- `POST /api/v1/strategy/pine/create-scanner-profile`

### 9.1 Preflight request

Expected fields:

- `script_source`
- `market`
- `timeframe`
- `date_from`
- `date_to`
- optional execution assumptions

### 9.2 Preflight response

Return:

- `status`
- `script_type`
- `directionality`
- `detected_entries`
- `detected_exits`
- `unsupported_features`
- `compatibility_score`
- `readiness`
- `messages`

### 9.3 Backtest request

Expected fields:

- `script_source`
- `market`
- `timeframe`
- `date_from`
- `date_to`
- `capital`
- `commission_pct`
- `slippage_pct`

### 9.4 Backtest response

Return a normalized payload close to the existing optimization result contract:

- `status`
- `config`
- `metrics`
- `assumptions`
- `compatibility`
- `alignment`
- `rankings`
- `equity_curve`
- `trades`

### 9.5 Scanner profile creation request

Expected fields:

- `script_source`
- `profile_name`
- `market`
- `timeframe`
- `backtest_summary`
- `compatibility_summary`
- `ranking_summary`

### 9.6 Scanner profile creation response

Return:

- `status`
- `profile_id`
- `profile_name`
- `profile_state`
- `promotion_summary`

## 10. Runtime Architecture

Introduce a dedicated Pine runtime package under `core/`.

Suggested package:

- `core/pine_lab/`

Suggested modules:

- `models.py`
- `parser.py`
- `capabilities.py`
- `signal_normalizer.py`
- `executor.py`
- `ranking.py`
- `profiles.py`

### 10.1 `models.py`

Defines normalized objects such as:

- script metadata
- compatibility report
- signal event
- order event
- trade record
- backtest result
- scanner profile payload

### 10.2 `parser.py`

Responsible for:

- reading Pine source
- detecting script class
- extracting entry and exit constructs
- identifying features Horus can or cannot support

### 10.3 `capabilities.py`

Declares the Pine features Horus understands and those it explicitly rejects.

This is the contract that keeps phase 1 trustworthy.

### 10.4 `signal_normalizer.py`

Maps Pine entry and exit logic into Horus-normalized signal events that the executor can simulate on EGX data.

### 10.5 `executor.py`

Runs the actual EGX backtest using:

- Horus historical market data
- Horus execution assumptions
- deterministic long and exit behavior

Where practical, this layer should reuse existing execution or simulation utilities instead of duplicating all portfolio logic.

### 10.6 `ranking.py`

Calculates:

- pure performance score
- Horus alignment score
- combined score
- recommendation outcome

### 10.7 `profiles.py`

Creates and stores promoted Pine scanner profile definitions for later selection in the scanner flow.

## 11. Pine Compatibility Policy

Phase 1 should be broad enough to handle real Pine research use cases, but strict enough to stay trustworthy.

The system should accept Pine scripts only when Horus can determine executable trade behavior with confidence.

### 11.1 Accepted category

Accept:

- Pine strategies with explicit entry and exit logic
- Pine indicators only when they emit clear signal conditions that can be converted into entries and exits

### 11.2 Rejected category

Reject:

- visual-only indicators
- scripts whose trade logic depends on unsupported platform-only behavior
- scripts whose entries or exits are ambiguous after parsing
- constructs that cannot be mapped cleanly to Horus EGX execution assumptions

### 11.3 Trust rule

If Horus cannot reproduce behavior confidently enough, it must reject the script instead of approximating silently.

## 12. Scoring Model

The product should support two ranking views:

### 12.1 Pure performance rank

This rank is based on EGX backtest outcomes such as:

- total return
- drawdown control
- win rate
- trade count quality floor
- consistency or Sharpe-like metric

### 12.2 Combined score rank

This rank blends:

- performance score
- Horus alignment score

Recommended initial weighting:

- `70%` performance
- `30%` Horus alignment

This keeps market performance primary while still favoring strategies that fit Horus scanner behavior.

### 12.3 Recommendation behavior

The UI should show both rankings, but the default recommendation should use the combined score.

That makes the recommended winner more likely to be useful as a scanner profile rather than simply the highest-return backtest outlier.

## 13. Horus Alignment

Combined scoring requires a clear definition of Horus alignment.

Alignment should measure how often Pine-generated actionable signals agree with Horus-generated actionable signals over the same EGX market and time window.

The exact formula may evolve, but the initial contract should include:

- overlap rate of actionable entries
- directional agreement
- timing tolerance window
- disagreement count

The alignment score should remain informational for research and recommendation.

It should not override pure performance reporting.

## 14. Scanner Promotion Model

The winning Pine script should not overwrite the current scanner engine.

Instead, promotion should create a new additive scanner profile.

That profile should store:

- profile name
- source Pine script
- detected capabilities
- market scope
- timeframe
- backtest metrics
- compatibility summary
- ranking summary
- creation timestamp
- enabled or disabled status

This profile then becomes selectable in scanner workflows beside current Horus logic.

## 15. Promotion Gates

Promotion should be blocked unless minimum quality bars are met.

Suggested initial gates:

- minimum trade count
- positive total return
- max drawdown below a configured ceiling
- compatibility score above a configured minimum
- sufficient EGX data coverage

These thresholds should be explicit and operator-visible.

## 16. Error Handling

The system should fail early and explain why.

### 16.1 Preflight failure

Show:

- unsupported functions
- ambiguous trade constructs
- blocked execution reasons

### 16.2 Backtest failure

Differentiate between:

- parse failure
- compatibility failure
- market data failure
- execution failure

### 16.3 Promotion failure

Show whether promotion was blocked because of:

- failed gates
- missing metadata
- duplicate or invalid profile naming

## 17. Integration Points

Primary backend integration points:

- `routes/strategy.py`
- `PortfolioSimulator.py`
- `core/SignalEngine.py`
- `core/DailyScanner.py`

Primary frontend integration points:

- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/components/OptimizationShell.tsx`
- `frontend/src/app/optimization/components/BacktestLabPanel.tsx`
- `frontend/src/app/scanner/components/ScannerControls.tsx`

The key integration principle is:

- add Pine research and promotion as a new capability
- do not regress the existing Horus-native optimizer or scanner flows

## 18. Testing Strategy

### 18.1 Backend tests

Add tests that prove:

- preflight accepts compatible Pine strategies
- preflight rejects ambiguous or unsupported scripts
- backtest responses stay normalized and deterministic
- ranking outputs include both pure and combined scores
- promotion only succeeds when quality gates pass

Suggested targets:

- `tests/test_pine_preflight.py`
- `tests/test_pine_backtest.py`
- `tests/test_pine_ranking.py`
- `tests/test_pine_profile_promotion.py`

### 18.2 Frontend tests

Add tests that prove:

- Pine Lab mode renders correctly
- preflight and backtest flows display the expected states
- recommendation and leaderboard surfaces render correctly
- promotion actions show success and failure states

Suggested targets:

- `frontend/src/app/optimization/components/PineLabPanel.test.tsx`
- `frontend/src/app/optimization/page.test.tsx`

### 18.3 End-to-end checks

Add at least one operator-path test that validates:

1. paste Pine source
2. run preflight
3. run backtest
4. review recommendation
5. create scanner profile

## 19. Risks and Controls

### Risk: overpromised Pine compatibility

Control:

- use explicit capability reporting
- block unsupported behavior at preflight

### Risk: misleading backtests from silent approximations

Control:

- use Horus-compatible EGX execution rules
- reject unclear semantics

### Risk: Pine winners degrade scanner quality

Control:

- require promotion gates
- create additive profiles rather than replacing the engine

### Risk: feature sprawl into MT4 and MT5 too early

Control:

- keep phase 1 Pine-only
- design runtime seams so MT4 and MT5 can be added later without distorting the first delivery

## 20. Future Extensions

Once phase 1 is stable, future work may add:

- Pine file upload
- profile versioning and rollback
- side-by-side comparison of multiple Pine scripts
- MT4 and MT5 import through separate adapters
- hybrid scanner modes where Pine profiles act as confirm or reject layers

## 21. Summary

Phase 1 should add a Pine-first Strategy Lab to Horus that can:

- import Pine code with entry and exit logic
- validate compatibility before execution
- backtest on EGX under Horus rules
- rank strategies by performance and combined score
- recommend the best candidate
- create a new scanner profile from the winner

That is the smallest design that still reaches the real product goal:

find the best Pine-driven strategy for EGX and make it usable inside the Horus scanner without disrupting the current engine.
