# Horus Analytics II Backtester Pine Profile Integration Implementation Plan

Date: 2026-04-01
Based on:

- `docs/superpowers/specs/2026-04-01-backtester-pine-profile-integration-design.md`
- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.ts`
- `frontend/src/app/optimization/components/BacktestLabPanel.tsx`
- `frontend/src/app/optimization/components/OptimizationResultsPanel.tsx`
- `frontend/src/app/optimization/page.test.tsx`
- `frontend/src/app/optimization/components/BacktestLabPanel.test.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.test.tsx`
- `frontend/src/app/optimization/hooks/usePineProfilePromotion.ts`
- `routes/strategy.py`

Track: Backtester Pine Profile Integration
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan adds Pine profile support to the existing Optimization Backtester without breaking the native Horus simulator path.

The final implementation must leave seven things true:

1. The Backtester supports two explicit sources: `Horus Strategy` and `Pine Profile`.
2. The current Horus simulator path continues working exactly as it does today.
3. Pine profile mode can select any saved Pine profile, including `DRAFT`, `READY`, and `ACTIVE`.
4. Pine profile logic stays read-only in Backtester mode.
5. Pine backtest run settings remain editable for the current run.
6. `DRAFT` Pine profiles show a visible warning but still execute.
7. Existing Backtester and Pine Lab behavior remain stable under regression tests.

## 2. In Scope

Primary frontend targets:

- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.ts`
- `frontend/src/app/optimization/components/BacktestLabPanel.tsx`
- `frontend/src/app/optimization/components/OptimizationResultsPanel.tsx`
- `frontend/src/app/optimization/page.test.tsx`
- `frontend/src/app/optimization/components/BacktestLabPanel.test.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.test.tsx`

Primary backend/API touch points:

- `routes/strategy.py`
- optional Pine profile read contract if the current registry payload is insufficient for Backtester-selected script loading

Primary workflow capabilities to add:

- Backtest source switching in Backtester
- Pine profile registry loading inside Backtester mode
- Pine profile selection and validation
- Pine backtest execution routing from Backtester
- result labeling for Pine-sourced runs
- `DRAFT` warning UX

Out of scope for this phase:

- editing Pine scripts from the Backtester
- profile promotion or activation from the Backtester
- merging Backtester and Pine Lab into one view
- replacing the native Horus simulator
- new Pine runtime semantics beyond what Pine Lab already supports

## 3. Current Constraints

These existing facts shape the rollout:

1. `frontend/src/app/optimization/page.tsx` already separates `SIMULATOR`, `OPTIMIZER`, and `PINE_LAB` modes and wires the existing Backtester through `useBacktestLab`.
2. `frontend/src/app/optimization/hooks/useBacktestLab.ts` currently assumes only the native Horus simulator flow and posts exclusively to `/api/v1/strategy/backtest`.
3. `frontend/src/app/optimization/components/BacktestLabPanel.tsx` currently renders Horus-only controls such as RSI and trailing-stop parameters.
4. `frontend/src/app/optimization/components/OptimizationResultsPanel.tsx` currently expects native backtest output and does not label source type.
5. Pine profile selection and registry loading already exist elsewhere in the app through `/api/v1/strategy/pine/scanner-profiles`.
6. `routes/strategy.py` already exposes `POST /api/v1/strategy/pine/backtest` and `GET /api/v1/strategy/pine/scanner-profiles`.
7. The working tree is already dirty with Pine runtime work, so the rollout should avoid unnecessary file churn and keep each slice well bounded.

The implementation must address those constraints directly.

## 4. Execution Rules

These rules apply across the whole rollout:

1. The existing Horus Backtester path must remain the default source.
2. The Backtester must not silently switch sources; the selected source must be explicit in the UI.
3. Pine profile mode must not allow script editing.
4. Pine profile mode must not hide profile state; users should always see whether a selected profile is `DRAFT`, `READY`, or `ACTIVE`.
5. `DRAFT` profiles must be allowed to run, but the warning must be prominent and persistent before the run.
6. If no Pine profile is selected, the run button must stay disabled in Pine mode.
7. No unrelated Pine Lab profile-management behavior should be pulled into Backtester.
8. No existing Backtester test coverage should regress.

## 5. Target Module Map

The implementation should converge on this shape.

### Frontend state seams

- `frontend/src/app/optimization/hooks/useBacktestLab.ts`

### Frontend control surface seams

- `frontend/src/app/optimization/components/BacktestLabPanel.tsx`
- `frontend/src/app/optimization/page.tsx`

### Frontend result seams

- `frontend/src/app/optimization/components/OptimizationResultsPanel.tsx`

### API seams

- `routes/strategy.py`
- existing Pine profile registry contract
- existing Pine backtest contract

### Test seams

- `frontend/src/app/optimization/page.test.tsx`
- `frontend/src/app/optimization/components/BacktestLabPanel.test.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.test.tsx`
- optional backend contract tests only if payload/fetch behavior changes

## 6. Work Package Sequence

Execute this slice in the following order:

1. `BPI-P1` Backtest source state and Pine registry loading
2. `BPI-P2` Backtest control-surface updates for Pine profile mode
3. `BPI-P3` Pine execution routing from Backtester
4. `BPI-P4` Result labeling and warning states
5. `BPI-P5` Regression coverage and closeout

This order is intentional:

- source state must exist before the UI can branch cleanly
- the UI must be able to select Pine profiles before execution routing is meaningful
- execution routing should land before result-label polish so the visible states are grounded in real behavior
- regression coverage should close the loop across both Horus and Pine flows

## 7. Work Packages

### BPI-P1. Backtest Source State and Pine Registry Loading

Purpose:

Extend Backtester state so it can represent both Horus and Pine profile runs.

Target files:

- `frontend/src/app/optimization/hooks/useBacktestLab.ts`
- `frontend/src/app/optimization/page.tsx`
- targeted tests

Tasks:

1. Add `backtestSource: 'HORUS' | 'PINE_PROFILE'`.
2. Add `selectedPineProfileId`.
3. Add Pine registry state for Backtester mode.
4. Load Pine profile registry through the existing scanner-profile endpoint.
5. Keep registry loading independent from Pine Lab mode to avoid accidental coupling.
6. Preserve current Horus simulator state shape for the default path.

Deliverables:

- dual-source backtest state
- Pine registry loading in Backtester mode

Verification:

- hook tests for source switching and registry loading

Acceptance criteria:

- Backtester can load Pine profiles without affecting Horus mode
- existing simulator state still behaves the same by default

### BPI-P2. Backtest Control-Surface Updates for Pine Profile Mode

Purpose:

Update the Backtester panel so it cleanly branches between Horus and Pine controls.

Target files:

- `frontend/src/app/optimization/components/BacktestLabPanel.tsx`
- `frontend/src/app/optimization/page.tsx`
- targeted tests

Tasks:

1. Add `Backtest Source` toggle:
   - `Horus Strategy`
   - `Pine Profile`
2. In Horus mode:
   - keep current parameter sliders and trailing-stop controls unchanged
3. In Pine mode:
   - show Pine profile selector
   - show profile state badge
   - show market/timeframe context
   - show editable run settings for market/date/capital/commission/slippage
4. Disable `Init_Backtest` when Pine mode is selected and no profile is chosen.
5. Add `DRAFT` warning banner when the selected profile is draft.
6. Show quieter status treatment for `READY` and `ACTIVE`.

Deliverables:

- dual-source Backtester UI
- DRAFT warning UX
- disabled state when no Pine profile is selected

Verification:

- component/page tests for source toggle, profile selection, disabled run state, and draft warning

Acceptance criteria:

- users can clearly switch between Horus and Pine sources
- Pine mode is understandable without profile management controls leaking in

### BPI-P3. Pine Execution Routing From Backtester

Purpose:

Route Pine-sourced Backtester runs through the existing Pine backtest API while leaving Horus routing untouched.

Target files:

- `frontend/src/app/optimization/hooks/useBacktestLab.ts`
- optional API contract touch points if profile script access is insufficient
- targeted tests

Tasks:

1. Keep Horus mode posting to `/api/v1/strategy/backtest`.
2. Route Pine mode to `/api/v1/strategy/pine/backtest`.
3. For Pine mode, send:
   - selected profile script source
   - editable run settings from Backtester
4. If current registry payload lacks script source:
   - add the minimal payload expansion or targeted profile fetch needed
   - do not broaden unrelated data unnecessarily
5. Normalize error handling so Pine failures use the same Backtester error-banner style.

Deliverables:

- one hook that can execute both backtest paths
- stable Pine run payload from Backtester

Verification:

- hook/page tests proving endpoint switching by source
- optional backend contract tests if payload changes are required

Acceptance criteria:

- Horus mode still runs exactly as before
- Pine mode runs via the Pine backtest endpoint with the selected profile script

### BPI-P4. Result Labeling and Warning States

Purpose:

Make the output area clearly identify Pine-sourced backtests.

Target files:

- `frontend/src/app/optimization/components/OptimizationResultsPanel.tsx`
- `frontend/src/app/optimization/page.tsx`
- targeted tests

Tasks:

1. Add result metadata for source labeling:
   - `Backtest Source: Pine Profile`
   - selected profile name
   - selected profile state
2. Preserve existing Horus result presentation for native simulator runs.
3. Keep Pine mode warning state visible before execution when the selected profile is `DRAFT`.
4. Do not add activation or promotion actions to the result panel.

Deliverables:

- source-aware result display
- Pine profile context visible in results

Verification:

- page tests covering Pine result labeling and Horus result regression

Acceptance criteria:

- users can always tell whether a result came from Horus or a Pine profile
- selected profile identity is visible after Pine backtests

### BPI-P5. Regression Coverage and Closeout

Purpose:

Lock the feature down without destabilizing the rest of Optimization or Pine Lab.

Target files:

- `frontend/src/app/optimization/page.test.tsx`
- `frontend/src/app/optimization/components/BacktestLabPanel.test.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.test.tsx`
- optional backend tests only if API contracts changed

Tasks:

1. Add tests for:
   - source toggle behavior
   - Pine registry loading
   - disabled run state with no Pine profile selected
   - DRAFT banner visibility
   - Horus endpoint selection
   - Pine endpoint selection
   - result labeling for Pine profile runs
2. Re-run existing Optimization test suites.
3. Re-run existing Pine Lab tests that share the same area.
4. If API payload changes were introduced, add minimal backend contract coverage.

Deliverables:

- complete regression coverage for the new Backtester source path

Verification:

- optimization frontend test sweep
- any affected backend contract tests

Acceptance criteria:

- Backtester and Pine Lab both remain green
- source switching is covered by tests rather than manual assumptions

## 8. Risk Register

### Risk 1. Pine profile registry does not expose script source

Impact:

Backtester cannot run a selected profile through the Pine backtest route.

Mitigation:

Add the smallest possible script-source access path:

- either extend the existing registry payload minimally
- or add a targeted fetch endpoint

### Risk 2. BacktestLab hook becomes too crowded

Impact:

Horus and Pine concerns become tangled.

Mitigation:

If complexity grows during implementation, split Pine-specific run state into a helper while keeping one top-level hook contract for the page.

### Risk 3. Result panel becomes ambiguous

Impact:

Users may confuse Horus and Pine outputs.

Mitigation:

Make source labeling explicit and persistent in the results area.

### Risk 4. Pine mode leaks profile-management behavior into Backtester

Impact:

The page becomes harder to reason about and duplicates Pine Lab.

Mitigation:

Keep activation/promotion out of Backtester and limit the feature to selection plus execution.

## 9. Recommended Validation Commands

Frontend targeted:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns "src/app/optimization"`

If scanner-profile UI sharing is touched:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns "src/app/optimization|src/app/scanner/components/ScannerControls.test.tsx"`

Backend only if API contracts change:

- `./.venv313/Scripts/python -m pytest tests/test_pine_profile_promotion.py tests/test_strategy_and_system.py -q`

## 10. Recommended First Coding Slice

Start with `BPI-P1` and `BPI-P2` together as the safest first slice.

Why:

- they expose the new Backtester state clearly
- they allow UI review before any execution-path risk
- they keep the first implementation review focused on source selection and warning UX

That first slice should stop before wiring Pine execution routing if the UI/state contract still needs adjustment.

## 11. Success Criteria

This feature is successful when:

1. users can switch Backtester between `Horus Strategy` and `Pine Profile`
2. users can select any saved Pine profile, including `DRAFT`
3. Pine mode allows editing run settings without editing the script
4. `DRAFT` profiles show a warning but still run
5. Pine runs use the Pine backtest route from Backtester
6. Horus runs still use the native backtest route unchanged
7. the result area clearly labels Pine profile source and state
