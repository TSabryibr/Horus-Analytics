# Horus Analytics II Pine `request.security` MTF Import Implementation Plan

Date: 2026-04-03
Based on:

- `docs/superpowers/specs/2026-04-03-pine-request-security-mtf-import-design.md`
- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `core/pine_lab/expression_eval.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`
- `frontend/src/app/components/pineRuntimeFeatures.ts`
- `frontend/src/app/optimization/page.test.tsx`
- `tests/test_pine_profile_promotion.py`

Track: Pine `request.security` MTF Import
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved Pine `request.security` MTF import design into a safe implementation sequence for Horus Strategy Lab.

The implementation must leave seven things true:

1. Safe same-symbol higher-timeframe `request.security(...)` forms are accepted by preflight.
2. The Pine evaluator can compute the imported higher-timeframe expression deterministically.
3. Preflight and runtime remain aligned through one shared capability model.
4. Cross-symbol imports remain blocked explicitly.
5. Repaint/lookahead variants remain blocked explicitly.
6. Pine Lab diagnostics become more precise by showing supported MTF import capability.
7. Existing Pine profile promotion and Pine backtest behavior does not regress.

## 2. In Scope

Primary backend targets:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `core/pine_lab/expression_eval.py`
- `core/pine_lab/executor.py`
- targeted backend tests under `tests/`

Primary frontend targets:

- `frontend/src/app/components/pineRuntimeFeatures.ts`
- `frontend/src/app/optimization/page.test.tsx`

Primary workflow capabilities to add:

- parser acceptance for safe same-symbol MTF imports
- evaluator support for deterministic higher-timeframe expression import
- signal-plan execution using imported higher-timeframe series
- Pine diagnostics for supported MTF import capability

Out of scope for this phase:

- cross-symbol imports
- repaint semantics
- `lookahead_on`
- full `barmerge` parity
- custom wrapper-function security emulation
- `strategy.short`
- `strategy.exit(...)`

## 3. Current Constraints

These existing facts shape the rollout:

1. `core/pine_lab/capabilities.py` currently blocks `request.security(...)` wholesale.
2. `core/pine_lab/parser.py` already resolves generalized expression plans and is the correct seam for admission rules.
3. `core/pine_lab/expression_eval.py` is the correct seam for deterministic imported-series evaluation.
4. `core/pine_lab/executor.py` already prefers normalized expression-plan execution when `entry_expression` and `exit_expression` exist.
5. `tests/test_pine_profile_promotion.py` is already the strongest backend integration seam for Pine preflight/backtest behavior.
6. `frontend/src/app/optimization/page.test.tsx` already covers Pine Lab diagnostics and should remain the primary UI regression seam.

The rollout must extend those seams rather than create a parallel Pine runtime path.

## 4. Execution Rules

These rules apply across all work packages:

1. No `request.security(...)` form may be marked as supported in preflight unless runtime evaluation exists for it.
2. No unsupported cross-symbol or repaint behavior may be softened into best-effort execution.
3. No change may broaden Horus Pine execution beyond the current long-only entry/flat-exit model.
4. No frontend copy may imply full TradingView `request.security` parity.
5. No Pine Lab result should regress from `READY` back to `BLOCKED` for currently supported non-MTF Pine scripts.

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

### UI seam

- `frontend/src/app/components/pineRuntimeFeatures.ts`
- `frontend/src/app/optimization/page.test.tsx`

### Test seams

- `tests/test_pine_profile_promotion.py`

## 6. Work Package Sequence

Execute this slice in the following order:

1. `PSM-P1` Parser admission and precise blockers
2. `PSM-P2` Deterministic MTF evaluator support
3. `PSM-P3` Executor integration and runtime backtests
4. `PSM-P4` Pine Lab diagnostics expansion
5. `PSM-P5` Regression hardening and closeout

This order is intentional:

- safe admission rules must exist before runtime tests can express the new contract
- evaluator support must exist before executor integration can be trusted
- UI messaging should reflect stable backend behavior, not speculative support

## 7. Work Packages

### PSM-P1. Parser Admission and Precise Blockers

Purpose:

Teach preflight to accept safe same-symbol higher-timeframe `request.security(...)` calls while preserving precise blockers for unsupported variants.

Target files:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `tests/test_pine_profile_promotion.py`

Tasks:

1. Replace the blanket `request.security` block with structured validation for:
   - same symbol only
   - literal timeframe only
   - higher timeframe only
   - supported inner expression only
2. Keep explicit blockers for:
   - alternate symbols
   - repaint/lookahead variants
   - unsupported inner expressions
3. Ensure mixed scripts become partially unblocked but still block only for the remaining unsupported security semantics.
4. Add red-first tests using representative ALGOX-style MTF imports.

Deliverables:

- structured `request.security` preflight validation
- precise block reasons preserved

Verification:

- focused Pine preflight tests

Acceptance criteria:

- safe same-symbol MTF imports no longer block solely because `request.security(...)` appears
- unsupported security variants still block with precise reasons

### PSM-P2. Deterministic MTF Evaluator Support

Purpose:

Add deterministic runtime evaluation for supported `request.security(...)` nodes.

Target files:

- `core/pine_lab/expression_eval.py`
- focused backend tests in `tests/test_pine_profile_promotion.py`

Tasks:

1. Evaluate imported higher-timeframe `close`.
2. Evaluate imported higher-timeframe inner expressions built from already-supported nodes.
3. Resample to the higher timeframe deterministically.
4. Forward-fill imported results onto the base index.
5. Reject unsupported lower-timeframe or ambiguous imports.

Deliverables:

- evaluator support for deterministic same-symbol MTF imports

Verification:

- deterministic unit/integration tests against known bar data

Acceptance criteria:

- the expression engine can evaluate supported `request.security(...)` nodes without fallback logic

### PSM-P3. Executor Integration and Runtime Backtests

Purpose:

Make the Pine executor actually run backtests whose entry/exit plans depend on supported higher-timeframe imports.

Target files:

- `core/pine_lab/executor.py`
- `tests/test_pine_profile_promotion.py`

Tasks:

1. Add red-first backtest tests for representative strategies such as:
   - higher-timeframe `close` import
   - higher-timeframe EMA import
   - mixed supported MTF plus local indicator conditions
2. Verify the executor continues to use the normalized expression-plan path.
3. Preserve existing non-MTF execution behavior.
4. Ensure backtest responses continue to expose compatibility/ranking/alignment payloads correctly.

Deliverables:

- runtime backtest support for supported MTF signal plans

Verification:

- backend integration tests for Pine preflight plus backtest

Acceptance criteria:

- supported MTF-import scripts can reach `READY` and complete backtests successfully

### PSM-P4. Pine Lab Diagnostics Expansion

Purpose:

Reflect the new MTF import support clearly in Pine Lab diagnostics and shared feature summaries.

Target files:

- `frontend/src/app/components/pineRuntimeFeatures.ts`
- `frontend/src/app/optimization/page.test.tsx`

Tasks:

1. Add a feature label for:
   - `Same-symbol higher-timeframe security imports`
2. Ensure scripts that still block on repaint/lookahead or alternate symbols show those exact blockers while also surfacing supported nodes.
3. Keep shared Pine feature mapping consistent between Pine Lab and any shared profile details surfaces already using it.

Deliverables:

- updated Pine diagnostics
- updated supported runtime feature labels

Verification:

- frontend optimization tests

Acceptance criteria:

- Pine Lab clearly shows what is newly supported and what is still blocked

### PSM-P5. Regression Hardening and Closeout

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

- stable backend and frontend test coverage for the new MTF slice

Verification:

- targeted pytest and frontend test commands

Acceptance criteria:

- all new `request.security` MTF support is protected by focused regression coverage

## 8. Suggested Verification Commands

Backend:

- `.\.venv313\Scripts\python -m pytest tests/test_pine_profile_promotion.py -q`

Frontend:

- `npm --prefix frontend run test -- --runInBand src/app/optimization/page.test.tsx`

Broader follow-up if needed:

- `.\.venv313\Scripts\python -m pytest tests/test_pine_profile_promotion.py tests/test_scanner_and_data.py -k "pine_scanner_profile or pine_profile" -q`

## 9. Rollout Notes

This phase should be presented as:

- deterministic same-symbol MTF signal import support
- unchanged execution-model conservatism

That means the correct product outcome is:

- fewer `request.security`-related preflight blocks
- more accurate diagnostics
- no false claim of TradingView-equivalent repaint or cross-symbol semantics
