# Horus Analytics II Phase 13 Analytics Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-13-analytics-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 13
Status: Complete
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 13 Analytics decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/analytics/page.tsx` into a thin route shell without changing the route path, analytics bootstrap semantics, search-overrides-filter behavior, sort and column-toggle behavior, fresh-scan polling behavior, or Telegram signal-card broadcast behavior.

Phase 13 Analytics work should leave six things true:

1. The route page is no longer the primary home of analytics bootstrap fetch and status shaping.
2. The route page is no longer the primary home of search, filter, sort, and column-visibility behavior.
3. The route page is no longer the primary home of fresh-scan and row-broadcast command behavior.
4. The shell, filter controls, and table rendering are extracted into focused components.
5. Pure analytics shaping helpers are isolated behind a small transform seam.
6. The extraction pattern remains consistent with the Phase 4 through Phase 12 frontend decomposition track.

## 2. In Scope

Primary source file:

- `frontend/src/app/analytics/page.tsx`

Primary extraction target areas:

- `frontend/src/app/analytics/hooks/`
- `frontend/src/app/analytics/lib/`
- `frontend/src/app/analytics/components/`

Primary route responsibilities to preserve:

- analytics bootstrap fetch behavior
- loading and empty states
- status and last-updated state
- search-overrides-filter behavior
- status filter behavior
- minimum-score filter behavior
- sort behavior
- column-visibility behavior
- fresh-scan trigger and scan-status polling behavior
- Telegram signal-card broadcast behavior
- current row rendering semantics

Out of scope for this Phase 13 slice:

- visual redesign of the analytics page
- backend endpoint changes
- analytics refresh/status API contract changes
- Telegram signal-card API contract changes
- replacing `AnalyticsRow.tsx` with a different row abstraction
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/analytics/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/analytics/hooks/useAnalyticsRuntime.test.tsx`
- `frontend/src/app/analytics/hooks/useAnalyticsActions.test.tsx`
- selected component tests for shell, filters, and table

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/analytics/hooks/useAnalyticsRuntime.ts`

Owns:

- bootstrap fetch
- loading state
- status and last-updated state
- search text
- status filter
- minimum-score filter
- sort config
- column-visibility state
- filtered and sorted rows

### `frontend/src/app/analytics/hooks/useAnalyticsActions.ts`

Owns:

- refresh trigger
- scan-status polling loop
- Telegram signal-card broadcast action
- action feedback and loading transitions

### `frontend/src/app/analytics/lib/analyticsTransforms.ts`

Owns:

- analytics payload normalization
- numeric sort coercion
- last-updated formatting
- pure filter and sort helpers

### `frontend/src/app/analytics/components/`

Target components:

- `AnalyticsShell.tsx`
- `AnalyticsFilters.tsx`
- `AnalyticsTable.tsx`

Existing presentational unit retained:

- `AnalyticsRow.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Analytics decomposition in this order:

1. `F13-P1` Pure transforms and runtime extraction
2. `F13-P2` Action seam and shell extraction
3. `F13-P3` Filters and table extraction
4. `F13-P4` Route slimdown and checkpoint closeout

This order is intentional:

- pure transforms move first because they stabilize payload and sort/filter shaping contracts
- runtime/table-state extraction moves before UI components so the render surfaces consume display-ready state
- action extraction follows once route state ownership is explicit
- final slimdown happens only after the route is fully covered by seams

## 6. Work Packages

### F13-P1. Pure Transforms and Runtime Extraction

Status: Complete

Purpose:

Establish the pure shaping helpers and isolate the analytics bootstrap/runtime behavior before moving action and UI logic.

Target files:

- `frontend/src/app/analytics/page.tsx`
- `frontend/src/app/analytics/lib/analyticsTransforms.ts`
- `frontend/src/app/analytics/hooks/useAnalyticsRuntime.ts`

Tasks:

1. Move payload normalization, numeric sort coercion, and last-updated formatting helpers into `analyticsTransforms.ts`.
2. Move bootstrap fetch, loading state, status/last-updated state, and table-state behavior into `useAnalyticsRuntime`.
3. Move search, status filter, minimum-score, sort config, column-visibility, and derived filtered/sorted rows into `useAnalyticsRuntime`.
4. Add direct tests for payload normalization, search-overrides-filter behavior, filtering, sort behavior, and column-toggle state.

Deliverables:

- shared Analytics transforms
- runtime seam for display-ready analytics table state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/analytics/page.test.tsx src/app/analytics/hooks/useAnalyticsRuntime.test.tsx`

Acceptance criteria:

- bootstrap/runtime behavior is no longer primarily route-local
- pure helper logic is no longer defined inline in the route
- current route-level Analytics tests stay green

### F13-P2. Action Seam and Shell Extraction

Status: Complete

Purpose:

Separate the command-heavy behavior and shared page chrome once runtime/table state is stable.

Target files:

- `frontend/src/app/analytics/page.tsx`
- `frontend/src/app/analytics/hooks/useAnalyticsActions.ts`
- `frontend/src/app/analytics/components/AnalyticsShell.tsx`

Tasks:

1. Extract the page frame, header, refresh button, and top status copy into `AnalyticsShell`.
2. Move fresh-scan trigger, scan-status polling, and Telegram signal-card broadcast behavior into `useAnalyticsActions`.
3. Keep current loading/disabled semantics intact for refresh and row broadcast behavior.
4. Add direct tests for refresh success/failure, scan polling completion/error behavior, and row broadcast success/failure mapping.

Deliverables:

- shared Analytics shell
- dedicated Analytics action seam
- direct action seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/analytics/page.test.tsx src/app/analytics/hooks/useAnalyticsActions.test.tsx src/app/analytics/components/AnalyticsShell.test.tsx`

Acceptance criteria:

- command behavior is no longer primarily route-local
- shell chrome is no longer defined inline in the route
- current route-level Analytics behavior remains stable

### F13-P3. Filters and Table Extraction

Status: Complete

Purpose:

Finish the structural decomposition by extracting the filter controls and table surface into focused components.

Target files:

- `frontend/src/app/analytics/page.tsx`
- `frontend/src/app/analytics/components/AnalyticsFilters.tsx`
- `frontend/src/app/analytics/components/AnalyticsTable.tsx`

Tasks:

1. Extract the search, status filter, score slider, and column menu into `AnalyticsFilters`.
2. Extract the table header, sort interactions, loading row, empty row, and row-list composition into `AnalyticsTable`.
3. Keep `AnalyticsRow.tsx` as the row-level presentational unit and pass `onBroadcast` through cleanly.
4. Add direct tests for filter rendering and table loading/empty/sort branches.

Deliverables:

- extracted Analytics filters component
- extracted Analytics table component
- direct component coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/analytics/page.test.tsx src/app/analytics/components/AnalyticsFilters.test.tsx src/app/analytics/components/AnalyticsTable.test.tsx`

Acceptance criteria:

- filter and table surfaces are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level Analytics behavior remains stable

### F13-P4. Route Slimdown and Closeout

Status: Complete

Purpose:

Remove remaining route-local residue, finish seam coverage, and define the frontend checkpoint for this Phase 13 slice.

Target files:

- `frontend/src/app/analytics/page.tsx`
- all new hook/component test files
- Phase 13 checkpoint docs

Tasks:

1. Remove remaining route-local helper or state residue once the seams are live.
2. Ensure `page.tsx` is primarily composition plus lightweight wiring.
3. Run the broader frontend verification gate.
4. Write the Phase 13 checkpoint summary and update the top-level roadmap.

Deliverables:

- slimmed Analytics route shell
- complete seam-focused test surface
- Phase 13 checkpoint summary
- updated top-level roadmap

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- the route is materially thinner and acts as a composition shell
- all Analytics seam and route tests are green
- frontend baseline and browser baseline are green

## 7. Verification Matrix

Each package must declare:

1. The smallest fast test slice that proves the extraction did not break the active contract
2. The broader route-level test anchor that remains green
3. The final checkpoint commands required before Phase 13 is closed

### Fast slices by package

`F13-P1`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/analytics/page.test.tsx src/app/analytics/hooks/useAnalyticsRuntime.test.tsx`

`F13-P2`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/analytics/page.test.tsx src/app/analytics/hooks/useAnalyticsActions.test.tsx src/app/analytics/components/AnalyticsShell.test.tsx`

`F13-P3`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/analytics/page.test.tsx src/app/analytics/components/AnalyticsFilters.test.tsx src/app/analytics/components/AnalyticsTable.test.tsx`

`F13-P4`

- full frontend checkpoint commands

## 8. Risk Notes

### Risk: search-overrides-filter behavior drifts during extraction

Mitigation:

- keep the route test green
- add direct runtime tests for search taking precedence over score/status filters

### Risk: scan polling semantics change subtly

Mitigation:

- isolate polling in `useAnalyticsActions`
- test completion, error, and timeout-safe behavior directly

### Risk: over-engineering a medium route

Mitigation:

- keep only the minimum seam set
- reuse `AnalyticsRow.tsx`
- do not introduce extra abstraction beyond runtime, actions, transforms, shell, filters, and table

## 9. Checkpoint Definition

Phase 13 should be considered complete when:

- `frontend/src/app/analytics/page.tsx` is primarily composition and lightweight wiring
- analytics bootstrap and table-state behavior live in `useAnalyticsRuntime`
- scan refresh and row broadcast behavior live in `useAnalyticsActions`
- shell, filters, and table rendering live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and core components
- the frontend verification gate passes

## 10. Notes For Execution

Keep behavior changes out of this slice. If a bug is found during extraction, fix it only if:

1. it is required to preserve the current visible contract, or
2. it is small enough to lock with a direct regression test in the same package

If broader analytics UX or API changes are desired, defer them to a later phase after the structural seam work is complete.

## 11. Recommended Next Move After This Plan

Phase 13 is complete. The next highest-value untreated frontend route is `frontend/src/app/sectors/page.tsx`, which should be the next design/spec target in the frontend runtime stability track.
