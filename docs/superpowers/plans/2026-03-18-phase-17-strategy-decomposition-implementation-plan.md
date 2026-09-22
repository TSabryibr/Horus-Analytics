# Horus Analytics II Phase 17 Strategy Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-17-strategy-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 17
Status: Complete
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 17 Strategy decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/strategy/page.tsx` into a thin route shell without changing the route path, the current strategy refresh behavior, the current AI proposal rendering semantics, the manual-mode toggle behavior, the manual override slider behavior, the strategy apply and manual apply payload semantics, or the current success and error toast behavior.

Phase 17 Strategy work should leave six things true:

1. The route page is no longer the primary home of manual-mode state, manual parameters, and toast state.
2. The route page is no longer the primary home of strategy apply and manual-override behavior.
3. The route page is no longer the primary home of payload shaping from `proposed_settings` and `changes`.
4. The shell, terrain, reasoning, and controls surfaces are extracted into focused components.
5. The extracted seams are directly testable without full route execution.
6. The extraction pattern remains consistent with the Phase 4 through Phase 16 frontend decomposition track.

## 2. In Scope

Primary source file:

- `frontend/src/app/strategy/page.tsx`

Primary extraction target areas:

- `frontend/src/app/strategy/hooks/`
- `frontend/src/app/strategy/lib/`
- `frontend/src/app/strategy/components/`

Primary route responsibilities to preserve:

- proposal loading and refresh behavior
- regime and volatility rendering
- reasoning rendering
- success and error toast behavior
- manual-mode toggle
- manual parameter editing
- AI proposal apply behavior
- manual override apply behavior

Out of scope for this Phase 17 slice:

- visual redesign of the strategy route
- backend endpoint changes
- strategy payload contract changes
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/strategy/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/strategy/hooks/useStrategyRuntime.test.tsx`
- `frontend/src/app/strategy/hooks/useStrategyActions.test.tsx`
- selected component tests for shell, terrain, reasoning, and controls

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/strategy/hooks/useStrategyRuntime.ts`

Owns:

- manual-mode state
- manual parameter state
- success and error toast state
- proposal-derived parameter shaping
- regime display helper state

### `frontend/src/app/strategy/hooks/useStrategyActions.ts`

Owns:

- apply strategy behavior
- apply manual overrides behavior
- refresh dispatch passthrough
- applying state

### `frontend/src/app/strategy/lib/strategyTransforms.ts`

Owns:

- payload shaping from `proposed_settings`
- fallback payload shaping from `changes`
- small pure regime and display helpers

### `frontend/src/app/strategy/components/`

Target components:

- `StrategyShell.tsx`
- `StrategyTerrainPanel.tsx`
- `StrategyReasoningPanel.tsx`
- `StrategyControlsPanel.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Strategy decomposition in this order:

1. `F17-P1` Pure transforms and runtime extraction
2. `F17-P2` Action seam and shell extraction
3. `F17-P3` Terrain, reasoning, and controls extraction
4. `F17-P4` Closeout and checkpoint

This order is intentional:

- pure transforms and runtime state move first because they stabilize manual-mode and payload semantics
- the action seam moves next because apply and manual override are the main command-side behavior
- the display surfaces move after runtime and action seams are explicit
- final slimdown happens only after the route is fully covered by seams

## 6. Work Packages

### F17-P1. Pure Transforms and Runtime Extraction

Status: Complete

Purpose:

Establish the pure shaping helpers and isolate manual-mode state, manual parameters, toast state, and proposal-derived payload shaping before moving the action seam or large render blocks.

Target files:

- `frontend/src/app/strategy/page.tsx`
- `frontend/src/app/strategy/lib/strategyTransforms.ts`
- `frontend/src/app/strategy/hooks/useStrategyRuntime.ts`

Tasks:

1. Move payload shaping from `proposed_settings` and fallback shaping from `changes` into `strategyTransforms.ts`.
2. Move manual-mode state, manual parameter state, success and error toast state, and regime helper behavior into `useStrategyRuntime`.
3. Keep the route consuming runtime state through the hook instead of inline derivation.
4. Add direct tests for manual-mode toggle, payload shaping, regime helper behavior, and empty fallback behavior.

Deliverables:

- shared strategy transforms
- runtime seam for strategy route state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/strategy/page.test.tsx src/app/strategy/hooks/useStrategyRuntime.test.tsx`

Acceptance criteria:

- manual-mode and payload shaping behavior are no longer primarily route-local
- pure strategy helpers are no longer defined inline in the route
- current route-level strategy tests stay green

### F17-P2. Action Seam and Shell Extraction

Status: Complete

Purpose:

Separate apply and refresh behavior and pull the top-level shell and toast rendering out of the route once runtime state is stable.

Target files:

- `frontend/src/app/strategy/page.tsx`
- `frontend/src/app/strategy/hooks/useStrategyActions.ts`
- `frontend/src/app/strategy/components/StrategyShell.tsx`

Tasks:

1. Extract AI proposal apply behavior into `useStrategyActions`.
2. Extract manual override apply behavior into `useStrategyActions`.
3. Extract the page frame, header shell, refresh action, and toast slots into `StrategyShell`.
4. Add direct tests for apply success/failure, manual apply success/failure, refresh passthrough, and shell rendering.

Deliverables:

- dedicated strategy action seam
- extracted shell
- direct action and shell tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/strategy/page.test.tsx src/app/strategy/hooks/useStrategyActions.test.tsx src/app/strategy/components/StrategyShell.test.tsx`

Acceptance criteria:

- apply and refresh behavior are no longer primarily route-local
- top-level shell structure is no longer defined inline in the route
- current route-level strategy behavior remains stable

### F17-P3. Terrain, Reasoning, and Controls Extraction

Status: Complete

Purpose:

Finish the primary structural decomposition by extracting the visible strategy surfaces into focused components.

Target files:

- `frontend/src/app/strategy/page.tsx`
- `frontend/src/app/strategy/components/StrategyTerrainPanel.tsx`
- `frontend/src/app/strategy/components/StrategyReasoningPanel.tsx`
- `frontend/src/app/strategy/components/StrategyControlsPanel.tsx`

Tasks:

1. Extract regime and volatility rendering into `StrategyTerrainPanel`.
2. Extract the reasoning surface into `StrategyReasoningPanel`.
3. Extract the proposal list, manual sliders, and apply CTA area into `StrategyControlsPanel`.
4. Add direct tests for the extracted display surfaces.

Deliverables:

- extracted terrain panel
- extracted reasoning panel
- extracted controls panel
- direct component coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/strategy/page.test.tsx src/app/strategy/components/StrategyTerrainPanel.test.tsx src/app/strategy/components/StrategyReasoningPanel.test.tsx src/app/strategy/components/StrategyControlsPanel.test.tsx`

Acceptance criteria:

- the main strategy display surfaces are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level strategy behavior remains stable

### F17-P4. Closeout and Checkpoint

Status: Complete

Purpose:

Finish seam coverage, run the broader frontend gate, and define the frontend checkpoint for this Phase 17 slice.

Target files:

- `frontend/src/app/strategy/page.tsx`
- all new hook/component test files
- Phase 17 checkpoint docs

Tasks:

1. Run the broader frontend verification gate.
2. Write the Phase 17 checkpoint summary.
3. Update the top-level roadmap.
4. Confirm the route remains primarily composition plus lightweight wiring.

Deliverables:

- complete seam-focused test surface
- Phase 17 checkpoint summary
- updated top-level roadmap

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- all strategy seam and route tests are green
- frontend baseline and browser baseline are green
- the route is materially thinner and acts as a composition shell

## 7. Verification Matrix

Each package must declare:

1. The smallest fast test slice that proves the extraction did not break the active contract
2. The broader route-level test anchor that remains green
3. The final checkpoint commands required before Phase 17 is closed

### Fast slices by package

`F17-P1`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/strategy/page.test.tsx src/app/strategy/hooks/useStrategyRuntime.test.tsx`

`F17-P2`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/strategy/page.test.tsx src/app/strategy/hooks/useStrategyActions.test.tsx src/app/strategy/components/StrategyShell.test.tsx`

`F17-P3`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/strategy/page.test.tsx src/app/strategy/components/StrategyTerrainPanel.test.tsx src/app/strategy/components/StrategyReasoningPanel.test.tsx src/app/strategy/components/StrategyControlsPanel.test.tsx`

`F17-P4`

- full frontend checkpoint commands

## 8. Risk Notes

### Risk: proposal payload semantics drift during extraction

Mitigation:

- isolate payload shaping in `strategyTransforms`
- test `proposed_settings` and `changes` shaping directly

### Risk: manual-mode and apply behavior change subtly

Mitigation:

- isolate apply behavior in `useStrategyActions`
- test AI apply, manual apply, and network error behavior directly

### Risk: over-engineering a medium strategy route

Mitigation:

- keep only the minimum seam set
- retain the current panels and control patterns
- do not introduce extra abstraction beyond runtime, actions, transforms, shell, terrain, reasoning, and controls

## 9. Checkpoint Definition

Phase 17 should be considered complete when:

- `frontend/src/app/strategy/page.tsx` is primarily composition and lightweight wiring
- manual-mode, manual params, toast state, and payload shaping live in `useStrategyRuntime`
- apply and refresh behavior live in `useStrategyActions`
- shell, terrain, reasoning, and controls surfaces live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and core components
- the frontend verification gate passes

## 10. Notes For Execution

Keep behavior changes out of this slice. If a bug is found during extraction, fix it only if:

1. it is required to preserve the current visible contract, or
2. it is small enough to lock with a direct regression test in the same package

If broader strategy UX or panel changes are desired, defer them to a later phase after the structural seam work is complete.

## 11. Recommended Next Move After This Plan

Phase 17 is complete. The next recommended move is to start the next frontend decomposition target on `frontend/src/app/reports/weekly/page.tsx`.
