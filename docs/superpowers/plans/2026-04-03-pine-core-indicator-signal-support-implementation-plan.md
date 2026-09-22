# Horus Analytics II Pine Core Indicator Signal Support Implementation Plan

Date: 2026-04-03
Based on:

- `docs/superpowers/specs/2026-04-03-pine-core-indicator-signal-support-design.md`
- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `core/pine_lab/expression_eval.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/page.test.tsx`
- `tests/test_pine_profile_promotion.py`

Track: Pine Core Indicator Signal Support
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved Pine core-indicator signal-support design into a safe implementation sequence for Horus Strategy Lab.

The implementation must leave seven things true:

1. `ta.atr`, `ta.highest`, `ta.lowest`, `ta.wma`, and `ta.vwma` are accepted by preflight when used in supported long-only signal conditions.
2. The Pine executor can evaluate those same indicator nodes deterministically on EGX data.
3. Preflight and runtime remain aligned through one shared capability model.
4. Unsupported features such as `strategy.short`, `strategy.exit`, and `request.security` remain blocked explicitly.
5. Pine Lab diagnostics become more precise by showing the newly supported indicator features.
6. No fake Pine parity is implied by backend or UI messaging.
7. Existing Pine profile promotion and Pine backtest behavior does not regress.

## 2. In Scope

Primary backend targets:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `core/pine_lab/expression_eval.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`
- targeted backend tests under `tests/`

Primary frontend targets:

- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/components/pineRuntimeFeatures.ts`
- `frontend/src/app/optimization/page.test.tsx`

Primary workflow capabilities to add:

- capability acceptance for core indicator calls
- runtime evaluation for ATR/highest/lowest/WMA/VWMA
- signal-plan execution using those indicators
- Pine diagnostics for new supported runtime features

Out of scope for this phase:

- `strategy.short`
- `strategy.exit(...)`
- `request.security`
- pivots and structure functions
- Keltner channels
- linear regression and ALMA
- order-model changes

## 3. Current Constraints

These existing facts shape the rollout:

1. `core/pine_lab/capabilities.py` currently whitelists only a narrow set of functions.
2. `core/pine_lab/parser.py` already resolves generalized expression plans and blocks unsupported calls centrally.
3. `core/pine_lab/expression_eval.py` is the correct seam for adding real indicator series evaluation.
4. `core/pine_lab/executor.py` already prefers normalized expression-plan execution when `entry_expression` and `exit_expression` exist.
5. `tests/test_pine_profile_promotion.py` is already the strongest backend integration seam for Pine preflight/backtest behavior.
6. `frontend/src/app/optimization/page.test.tsx` already covers Pine Lab diagnostics and should remain the primary UI regression seam.

The rollout must extend those seams rather than create a parallel Pine runtime path.

## 4. Execution Rules

These rules apply across all work packages:

1. No newly supported indicator may be marked as supported in preflight unless runtime evaluation exists for it.
2. No unsupported execution/data feature may be softened into best-effort execution.
3. No change may broaden Horus Pine execution beyond the current long-only entry/flat-exit model.
4. No frontend copy may imply support for stop/limit semantics, shorting, or multi-timeframe data.
5. No Pine Lab result should regress from `READY` back to `BLOCKED` for currently supported SMA/EMA/RSI/MACD scripts.

## 5. Target Module Map

The implementation should converge on this shape.

### Capability seam

- `core/pine_lab/capabilities.py`

### Parser seam

- `core/pine_lab/parser.py`

### Evaluator seam

- `core/pine_lab/expression_eval.py`

### Runtime/executor seam

- `core/pine_lab/executor.py`

### API seam

- `routes/strategy.py`

### UI seam

- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/components/pineRuntimeFeatures.ts`

### Test seams

- `tests/test_pine_profile_promotion.py`
- `frontend/src/app/optimization/page.test.tsx`

## 6. Work Package Sequence

Execute this slice in the following order:

1. `PCI-P1` Capability and preflight acceptance
2. `PCI-P2` Core indicator evaluator support
3. `PCI-P3` Executor integration and runtime backtests
4. `PCI-P4` Pine Lab diagnostics expansion
5. `PCI-P5` Regression hardening and closeout

This order is intentional:

- capability checks must be updated before parser/runtime tests can express the new contract
- evaluator support must exist before executor integration can be trusted
- UI messaging should reflect stable backend behavior, not speculative support

## 7. Work Packages

### PCI-P1. Capability and Preflight Acceptance

Purpose:

Teach preflight to accept the new indicator calls in supported signal expressions while preserving precise blockers for unsupported features.

Target files:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `tests/test_pine_profile_promotion.py`

Tasks:

1. Add the following functions to the supported capability set:
   - `ta.atr`
   - `ta.highest`
   - `ta.lowest`
   - `ta.wma`
   - `ta.vwma`
2. Keep explicit blockers unchanged for:
   - `strategy.short`
   - `strategy.exit`
   - `request.security`
   - still-unsupported indicator calls
3. Ensure `supported_nodes` includes the new functions when present.
4. Add red-first tests proving mixed scripts become partially unblocked but still block on unsupported execution/data features.

Deliverables:

- broadened capability whitelist
- precise preflight block reasons preserved

Verification:

- focused Pine preflight tests

Acceptance criteria:

- scripts using the new indicators in supported signal conditions no longer block solely for those functions
- mixed scripts still block only for the remaining unsupported features

### PCI-P2. Core Indicator Evaluator Support

Purpose:

Add deterministic runtime evaluation for the new indicator nodes.

Target files:

- `core/pine_lab/expression_eval.py`
- focused backend tests in `tests/test_pine_profile_promotion.py` or a new evaluator-focused test file if needed

Tasks:

1. Implement `ta.atr(length)` evaluation.
2. Implement `ta.highest(series, length)` evaluation.
3. Implement `ta.lowest(series, length)` evaluation.
4. Implement `ta.wma(series, length)` evaluation.
5. Implement `ta.vwma(series, length)` evaluation.
6. Confirm supported series inputs:
   - `open`
   - `high`
   - `low`
   - `close`
   - `volume`
7. Keep output aligned to the underlying pandas index and compatible with comparisons/boolean logic.

Deliverables:

- evaluator support for five new indicator nodes

Verification:

- deterministic unit/integration tests against known bar data

Acceptance criteria:

- the expression engine can evaluate the new indicators without fallback logic

### PCI-P3. Executor Integration and Runtime Backtests

Purpose:

Make the Pine executor actually run backtests whose entry/exit plans depend on the new indicators.

Target files:

- `core/pine_lab/executor.py`
- `tests/test_pine_profile_promotion.py`

Tasks:

1. Add red-first backtest tests for representative strategies such as:
   - `close > ta.vwma(close, 20)`
   - `ta.atr(14) < threshold and close > ta.wma(close, 20)`
   - `close > ta.highest(high, 20)` or `close < ta.lowest(low, 10)` depending on valid signal patterns
2. Verify the executor continues to use the normalized expression-plan path.
3. Preserve existing SMA/EMA/RSI/MACD execution behavior.
4. Ensure backtest responses continue to expose compatibility/ranking/alignment payloads correctly.

Deliverables:

- runtime backtest support for the new indicator-based signal plans

Verification:

- backend integration tests for Pine preflight plus backtest

Acceptance criteria:

- newly supported indicator scripts can reach `READY` and complete backtests successfully

### PCI-P4. Pine Lab Diagnostics Expansion

Purpose:

Reflect the new indicator support clearly in Pine Lab diagnostics and shared feature summaries.

Target files:

- `frontend/src/app/components/pineRuntimeFeatures.ts`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/page.test.tsx`

Tasks:

1. Add feature labels for:
   - `ATR threshold conditions`
   - `Highest/lowest breakout conditions`
   - `WMA/VWMA trend conditions`
2. Ensure scripts that still block on `strategy.exit` or `request.security` show those exact blockers while also surfacing supported nodes.
3. Keep shared Pine feature mapping consistent between Pine Lab and any shared profile details surfaces already using it.

Deliverables:

- updated Pine diagnostics
- updated supported runtime feature labels

Verification:

- frontend optimization tests

Acceptance criteria:

- Pine Lab clearly shows what is newly supported and what is still blocked

### PCI-P5. Regression Hardening and Closeout

Purpose:

Stabilize the expanded Pine runtime and prove the slice did not regress adjacent Pine functionality.

Target files:

- `tests/test_pine_profile_promotion.py`
- optional additional backend Pine tests if needed
- `frontend/src/app/optimization/page.test.tsx`

Tasks:

1. Re-run the broader Pine backend suite.
2. Re-run the optimization frontend suite.
3. Confirm mixed unsupported scripts remain honestly blocked.
4. Confirm saved Pine profile flows still preserve compatibility data needed by the UI.

Deliverables:

- stable backend and frontend test coverage for the new indicator slice

Verification:

- targeted pytest and frontend test commands

Acceptance criteria:

- all new Pine core-indicator support is protected by focused regression coverage

## 8. Suggested Verification Commands

Backend:

- `.\.venv313\Scripts\python -m pytest tests/test_pine_profile_promotion.py -q`

Frontend:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns "src/app/optimization"`

Broader follow-up if needed:

- `.\.venv313\Scripts\python -m pytest tests/test_pine_profile_promotion.py tests/test_scanner_and_data.py -k "pine_scanner_profile or pine_profile" -q`

## 9. Rollout Notes

This phase should be presented as:

- broader Pine signal-language support
- unchanged execution-model conservatism

That means the correct product outcome is:

- fewer indicator-related preflight blocks
- more accurate diagnostics
- no false claim of TradingView-equivalent execution semantics
