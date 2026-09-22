# Horus Analytics II Phase 20 Seasonality Decomposition Implementation Plan

Date: 2026-03-19
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-19-phase-20-seasonality-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 20
Status: Proposed
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 20 Seasonality decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/seasonality/page.tsx` into a thin route shell without changing the route path, market stats load behavior, ticker search/Enter-key submit behavior, refresh behavior, top-performers table rendering and click-to-search, verdict card rendering, monthly breakdown grid rendering, or current loading and empty-state behavior.

Phase 20 Seasonality work should leave five things true:

1. The route page is no longer the primary home of fetch functions and loading state.
2. The route page is no longer the primary home of month name constants or formatting helpers.
3. The shell, leaders table, verdict card, and monthly grid are extracted into focused components.
4. The extracted seams are directly testable without full route execution.
5. The extraction pattern remains consistent with the Phase 4 through Phase 19 frontend decomposition track.

## 2. In Scope

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
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/seasonality/page.test.tsx` (5 tests)

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/seasonality/hooks/useSeasonalityRuntime.test.tsx`
- selected component tests for shell, leaders table, verdict card, and monthly grid

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/seasonality/hooks/useSeasonalityRuntime.ts`

Owns:

- market stats state and fetch
- ticker stats state and fetch
- search ticker state (input value and update handler)
- loading states for both market and ticker
- refresh behavior (combined market + ticker re-fetch)
- ticker search trigger (Enter-key or button click)

### `frontend/src/app/seasonality/lib/seasonalityTransforms.ts`

Owns:

- `MONTH_NAMES` constant
- `getCurrentMonthLabel()` derivation
- `formatReturn(value)` sign-prefix formatting helper

### `frontend/src/app/seasonality/components/`

Target components:

- `SeasonalityShell.tsx` — page frame, header, search input, and refresh button
- `SeasonalityLeadersTable.tsx` — current month top performers table with click-to-search
- `SeasonalityVerdictCard.tsx` — ticker verdict with best/worst months and summary
- `SeasonalityMonthlyGrid.tsx` — full monthly breakdown grid with visual bars

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Seasonality decomposition in this order:

1. `F20-P1` Pure transforms and runtime extraction
2. `F20-P2` Shell and display component extraction
3. `F20-P3` Closeout and checkpoint

This phase uses three packages instead of four because the seasonality page is simpler than prior targets — no modal or write-side action seam is needed.

## 6. Work Packages

### F20-P1. Pure Transforms and Runtime Extraction

Status: Pending

Purpose:

Establish the pure shaping helpers and isolate fetch, state, and search behavior before moving the large render blocks.

Target files:

- `frontend/src/app/seasonality/page.tsx`
- `frontend/src/app/seasonality/lib/seasonalityTransforms.ts` [NEW]
- `frontend/src/app/seasonality/hooks/useSeasonalityRuntime.ts` [NEW]

Tasks:

1. Create `seasonalityTransforms.ts` with `MONTH_NAMES`, `getCurrentMonthLabel()`, and `formatReturn()`.
2. Create `useSeasonalityRuntime.ts` with market/ticker state, fetch functions, search state, loading states, and refresh handler.
3. Update `page.tsx` to consume runtime state through the hook and transforms instead of inline logic.
4. Add direct tests for the runtime hook covering: initial fetch, search-triggered fetch, refresh, and error handling.

Deliverables:

- shared seasonality transforms
- runtime seam for seasonality route state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/seasonality/page.test.tsx src/app/seasonality/hooks/useSeasonalityRuntime.test.tsx`

Acceptance criteria:

- fetch and state behavior are no longer primarily route-local
- pure helpers and constants are no longer defined inline in the route
- current route-level seasonality tests stay green

### F20-P2. Shell and Display Component Extraction

Status: Pending

Purpose:

Extract the four main UI sections from the route into focused components, leaving the route as pure composition.

Target files:

- `frontend/src/app/seasonality/page.tsx`
- `frontend/src/app/seasonality/components/SeasonalityShell.tsx` [NEW]
- `frontend/src/app/seasonality/components/SeasonalityLeadersTable.tsx` [NEW]
- `frontend/src/app/seasonality/components/SeasonalityVerdictCard.tsx` [NEW]
- `frontend/src/app/seasonality/components/SeasonalityMonthlyGrid.tsx` [NEW]

Tasks:

1. Extract header, search input, and refresh button into `SeasonalityShell`.
2. Extract top-performers table into `SeasonalityLeadersTable` with `onTickerClick` callback.
3. Extract verdict card into `SeasonalityVerdictCard`.
4. Extract monthly breakdown grid into `SeasonalityMonthlyGrid`.
5. Slim the route page to composition of hook + components only.
6. Add direct tests for all four extracted components.

Deliverables:

- extracted shell, leaders table, verdict card, and monthly grid
- direct component tests
- thin route page

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/seasonality/page.test.tsx src/app/seasonality/hooks/useSeasonalityRuntime.test.tsx src/app/seasonality/components/SeasonalityShell.test.tsx src/app/seasonality/components/SeasonalityLeadersTable.test.tsx src/app/seasonality/components/SeasonalityVerdictCard.test.tsx src/app/seasonality/components/SeasonalityMonthlyGrid.test.tsx`

Acceptance criteria:

- the main seasonality display surfaces are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level seasonality behavior remains stable

### F20-P3. Closeout and Checkpoint

Status: Pending

Purpose:

Finish seam coverage, run the broader frontend gate, and define the frontend checkpoint for this Phase 20 slice.

Target files:

- `frontend/src/app/seasonality/page.tsx`
- all new hook/component test files
- Phase 20 checkpoint docs

Tasks:

1. Run the broader frontend verification gate.
2. Write the Phase 20 checkpoint summary.
3. Update the top-level roadmap.
4. Confirm the route remains primarily composition plus lightweight wiring.

Deliverables:

- complete seam-focused test surface
- Phase 20 checkpoint summary
- updated top-level roadmap

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- all seasonality seam and route tests are green
- frontend baseline and browser baseline are green
- the route is materially thinner and acts as a composition shell

## 7. Verification Matrix

Each package must declare:

1. The smallest fast test slice that proves the extraction did not break the active contract
2. The broader route-level test anchor that remains green
3. The final checkpoint commands required before Phase 20 is closed

### Fast slices by package

`F20-P1`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/seasonality/page.test.tsx src/app/seasonality/hooks/useSeasonalityRuntime.test.tsx`

`F20-P2`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/seasonality/page.test.tsx src/app/seasonality/hooks/useSeasonalityRuntime.test.tsx src/app/seasonality/components/SeasonalityShell.test.tsx src/app/seasonality/components/SeasonalityLeadersTable.test.tsx src/app/seasonality/components/SeasonalityVerdictCard.test.tsx src/app/seasonality/components/SeasonalityMonthlyGrid.test.tsx`

`F20-P3`

- full frontend checkpoint commands

## 8. Risk Notes

### Risk: fetch and state behavior drift during extraction

Mitigation:

- keep the route test green
- add direct runtime tests for initial load, search-triggered fetch, refresh, and error handling

### Risk: over-engineering a small seasonality route

Mitigation:

- keep only the minimum seam set (one hook, one transforms, four components)
- no modal or action seam needed since the page is read-only with a simple search
- three packages instead of four to match the route's actual complexity

## 9. Checkpoint Definition

Phase 20 should be considered complete when:

- `frontend/src/app/seasonality/page.tsx` is primarily composition and lightweight wiring
- market stats, ticker stats, search state, and loading states live behind `useSeasonalityRuntime`
- month names and formatting helpers live in `seasonalityTransforms`
- shell, leaders table, verdict card, and monthly grid live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hook and primary components
- the frontend verification gate passes

## 10. Notes For Execution

Keep behavior changes out of this slice. If a bug is found during extraction, fix it only if:

1. it is required to preserve the current visible contract, or
2. it is small enough to lock with a direct regression test in the same package

If broader seasonality UX or visualization changes are desired, defer them to a later phase after the structural seam work is complete.

## 11. Recommended Next Move After This Plan

Start `F20-P1` first. The highest-value first edit is to extract `seasonalityTransforms.ts` and `useSeasonalityRuntime.ts`, then move fetch functions, state, and constants out of `frontend/src/app/seasonality/page.tsx` before touching the larger UI blocks.
