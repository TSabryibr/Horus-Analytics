# Horus Analytics II Phase 20 Seasonality Decomposition Design

Date: 2026-03-19
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/seasonality/page.tsx`
- `frontend/src/app/seasonality/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 20
Status: Proposed design
Owner model: Single owner

## 1. Goal

Phase 20 should turn `frontend/src/app/seasonality/page.tsx` into a thin route shell without changing:

- the route path
- market stats initial load behavior
- ticker search and Enter-key submit behavior
- refresh behavior for both market and ticker data
- current top-performers table rendering and click-to-search behavior
- verdict card rendering (optimal exit month, danger zone month, summary)
- monthly breakdown grid rendering and bar visualization
- current loading skeleton and empty-state behavior

The route currently mixes two distinct responsibilities in one file:

1. read-side data fetching (market stats and ticker seasonality) with inline fetch functions
2. display-side rendering of three large UI sections (leaders table, verdict card, monthly grid)

The decomposition should leave those responsibilities behind explicit seams that are directly testable.

## 2. Scope

Primary source file:

- `frontend/src/app/seasonality/page.tsx`

Primary extraction target areas:

- `frontend/src/app/seasonality/hooks/`
- `frontend/src/app/seasonality/lib/`
- `frontend/src/app/seasonality/components/`

Primary route responsibilities to preserve:

- market stats fetch on mount
- ticker stats fetch on mount and on Enter-key search
- refresh button triggering both fetches
- top-performers table with click-to-search behavior
- verdict card with best/worst month and summary
- monthly breakdown grid with visual bars
- loading skeleton states
- empty-state rendering when no ticker data

Out of scope for this Phase 20 slice:

- visual redesign of the seasonality route
- backend endpoint changes
- seasonality payload contract changes
- decomposing unrelated frontend routes

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/seasonality/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/seasonality/hooks/useSeasonalityRuntime.test.tsx`
- selected component tests for shell, leaders table, verdict card, and monthly grid

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/seasonality/hooks/useSeasonalityRuntime.ts`

Owns:

- market stats state and fetch
- ticker stats state and fetch
- search ticker state
- loading states for both market and ticker
- refresh behavior (combined market + ticker re-fetch)

### `frontend/src/app/seasonality/lib/seasonalityTransforms.ts`

Owns:

- month names constant
- current month label derivation
- return formatting helpers (sign prefix)

### `frontend/src/app/seasonality/components/`

Target components:

- `SeasonalityShell.tsx` — page frame, header, search input, and refresh button
- `SeasonalityLeadersTable.tsx` — current month top performers table with click-to-search
- `SeasonalityVerdictCard.tsx` — ticker verdict with best/worst months and summary
- `SeasonalityMonthlyGrid.tsx` — full monthly breakdown grid with visual bars

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Design Rules

The decomposition should follow four rules:

1. Hooks own async orchestration and mutable route state.
2. Pure formatting and constant helpers live in transforms.
3. Components stay display-oriented and receive explicit props.
4. `page.tsx` should not keep fetch functions, large render blocks, or inline constants once seams are live.

## 6. Recommended Extraction Sequence

Execute the Seasonality decomposition in this order:

1. `F20-P1` Pure transforms and runtime extraction
2. `F20-P2` Shell and display component extraction
3. `F20-P3` Closeout and checkpoint

This order is intentional:

- runtime and pure helpers move first because they stabilize fetch and state semantics
- display surfaces move after runtime is explicit
- closeout happens only after the route is structurally reduced to composition plus wiring

Note: this phase uses three packages instead of four because the seasonality page is simpler than prior targets — no modal or write-side action seam is needed.

## 7. Testing And Safety

Minimum new anchors:

- `frontend/src/app/seasonality/hooks/useSeasonalityRuntime.test.tsx`
- selected component tests for:
  - `SeasonalityShell`
  - `SeasonalityLeadersTable`
  - `SeasonalityVerdictCard`
  - `SeasonalityMonthlyGrid`

Existing route protection to keep green:

- `frontend/src/app/seasonality/page.test.tsx`

Release gate for the Phase 20 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Safety rules:

- no backend API contract changes
- no semantic changes to market stats or ticker fetch behavior
- no semantic changes to search or refresh behavior
- preserve current visible loading, verdict, leaders, and monthly-grid behavior while extracting

## 8. Phase 20 Completion Definition

Phase 20 should be considered complete when:

- `frontend/src/app/seasonality/page.tsx` is primarily composition and lightweight wiring
- market stats, ticker stats, search state, and loading states live behind `useSeasonalityRuntime`
- month names and formatting helpers live in `seasonalityTransforms`
- shell, leaders table, verdict card, and monthly grid live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hook and primary components
- the frontend verification gate passes

## 9. Recommended Next Move After This Spec

Write the Phase 20 implementation plan next, then start `F20-P1` by extracting `seasonalityTransforms.ts` and `useSeasonalityRuntime.ts` before touching the larger UI blocks.
