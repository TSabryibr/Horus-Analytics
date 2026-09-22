# Horus Analytics II Phase 17 Strategy Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/strategy/page.tsx`
- `frontend/src/app/strategy/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 17
Status: Proposed design
Owner model: Single owner

## 1. Goal

Phase 17 should turn `frontend/src/app/strategy/page.tsx` into a thin route shell without changing:

- the route path
- strategy refresh behavior
- AI proposal rendering semantics
- manual-mode toggle behavior
- manual override slider behavior
- strategy apply and manual apply payload semantics
- success and error toast behavior

The route currently mixes two distinct responsibilities in one file:

1. read-side proposal and regime rendering
2. write-side apply and manual-override behavior

The decomposition should leave those responsibilities behind explicit seams that are directly testable.

## 2. Scope

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
- unrelated frontend route decomposition

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
- small regime and display helpers that remain pure

### `frontend/src/app/strategy/components/`

Target components:

- `StrategyShell.tsx`
- `StrategyTerrainPanel.tsx`
- `StrategyReasoningPanel.tsx`
- `StrategyControlsPanel.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Design Rules

The decomposition should follow four rules:

1. Hooks own async orchestration and mutable route state.
2. Pure payload and display helpers live in transforms.
3. Components stay display-oriented and receive explicit props.
4. `page.tsx` should not keep apply behavior, payload shaping, or large panel render blocks once seams are live.

This keeps the strategy route consistent with the decomposition pattern already used in the frontend track.

## 6. Recommended Extraction Sequence

Execute the Strategy decomposition in this order:

1. `F17-P1` Pure transforms and runtime extraction
2. `F17-P2` Action seam and shell extraction
3. `F17-P3` Terrain, reasoning, and controls extraction
4. `F17-P4` Closeout and checkpoint

This order is intentional:

- runtime and pure shaping move first because they stabilize manual-mode and payload semantics
- the action seam moves next because apply and manual override are the highest-risk behavior seam
- display surfaces move after runtime and actions are explicit
- closeout happens only after the route is structurally reduced to composition plus wiring

## 7. Testing And Safety

Minimum new anchors:

- `frontend/src/app/strategy/hooks/useStrategyRuntime.test.tsx`
- `frontend/src/app/strategy/hooks/useStrategyActions.test.tsx`
- selected component tests for:
  - `StrategyShell`
  - `StrategyTerrainPanel`
  - `StrategyReasoningPanel`
  - `StrategyControlsPanel`

Existing route protection to keep green:

- `frontend/src/app/strategy/page.test.tsx`

Release gate for the Phase 17 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Safety rules:

- no backend API contract changes
- no semantic changes to strategy apply payloads
- no semantic changes to manual-override payloads
- preserve current visible loading, toast, mode-toggle, and proposal/manual rendering behavior while extracting

## 8. Phase 17 Completion Definition

Phase 17 should be considered complete when:

- `frontend/src/app/strategy/page.tsx` is primarily composition and lightweight wiring
- manual-mode, manual params, toast state, and payload shaping live behind `useStrategyRuntime`
- apply and refresh behavior live behind `useStrategyActions`
- shell, terrain, reasoning, and controls surfaces live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and primary components
- the frontend verification gate passes

## 9. Recommended Next Move After This Spec

Write the Phase 17 implementation plan next, then start `F17-P1` by extracting `strategyTransforms.ts` and `useStrategyRuntime.ts` before touching the apply seam or the larger UI blocks.
