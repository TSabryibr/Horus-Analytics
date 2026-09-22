# Horus Analytics II Phase 13 Analytics Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/analytics/page.tsx`
- `frontend/src/app/analytics/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 13 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Goal

This design defines the next frontend runtime decomposition wave for `frontend/src/app/analytics/page.tsx`.

The objective is to turn the route into a thin composition shell while preserving:

- the current route path
- analytics bootstrap fetch behavior
- current visible loading and empty states
- current search-overrides-filter behavior
- current status and minimum-score filter behavior
- current sort behavior
- current column-visibility behavior
- fresh-scan trigger and scan-status polling behavior
- Telegram signal-card broadcast behavior
- current table-row rendering semantics

The route currently mixes five separate concerns in one file:

1. analytics payload normalization and bootstrap fetch behavior
2. fresh-scan trigger and scan-status polling behavior
3. row-level Telegram broadcast behavior
4. filter, sort, and column-visibility state
5. shell, filter, and table rendering

Phase 13 should separate those concerns into explicit seams without changing what the page does.

## 2. Why This Route Is Next

`frontend/src/app/analytics/page.tsx` is the highest-value untreated frontend runtime route after the completed portfolio, settings, live, simulation, optimization, Telegram, Oracle, Audit, and Status decompositions.

It is the right next boundary because:

- it is still a medium-large route at about 378 lines
- it mixes read-side table state with two separate action seams
- it owns both scan refresh and row-level Telegram broadcast behavior
- it carries several derived table behaviors that should be testable outside the route
- it already has route-level test anchors that make extraction safer

The file currently combines:

- analytics payload normalization
- bootstrap fetch and route loading behavior
- scan refresh trigger
- scan-status polling loop
- row broadcast action logic
- date formatting helpers
- search, filter, minimum-score, sort, and column-visibility state
- large filter controls render block
- large table render block

That makes the route harder to change safely because one edit can affect fetch semantics, action semantics, and table behavior at once.

## 3. Scope

Primary source file:

- `frontend/src/app/analytics/page.tsx`

Primary extraction target areas:

- `frontend/src/app/analytics/hooks/`
- `frontend/src/app/analytics/components/`
- `frontend/src/app/analytics/lib/`

In scope:

- payload normalization
- bootstrap fetch and loading behavior
- status and last-updated state
- search, filter, score, sort, and column-visibility behavior
- fresh scan trigger and scan-status polling
- Telegram signal-card broadcast behavior
- shell extraction
- filter controls extraction
- table extraction

Out of scope:

- visual redesign of the analytics route
- backend endpoint changes
- API contract changes for analytics refresh, analytics status, or Telegram broadcast
- replacing `AnalyticsRow.tsx` with a different row abstraction
- changing visible wording except where required for structural extraction

## 4. Target Boundary

After decomposition, `frontend/src/app/analytics/page.tsx` should keep only:

- top-level composition
- lightweight wiring between extracted hooks and components

Everything else should move behind explicit seams.

### Route responsibilities that should leave the page

- analytics payload normalization helpers
- bootstrap fetch and status/last-updated updates
- fresh-scan and scan-status polling behavior
- row broadcast action behavior
- filter, score, sort, and column-visibility state
- derived filtered and sorted rows
- large shell/header render block
- large filter-controls render block
- large table render block

### Route responsibilities that may remain

- top-level section ordering
- composition of extracted components
- small glue code if needed for composition

## 5. Recommended Approach

Three approaches were considered:

### Option 1. Full capability split in one phase

Move runtime/table-state behavior and command behavior behind separate hooks and extract the shell, filters, and table into focused components.

Pros:

- strongest structural result
- addresses both action seams in the same checkpoint
- matches the successful Phase 4 through Phase 12 frontend decomposition pattern

Cons:

- larger first diff than a read-only extraction

### Option 2. Read-side split first, actions later

Extract fetch, filters, sort, and table rendering first and leave scan refresh and Telegram broadcast behavior in the route.

Pros:

- lower first diff

Cons:

- leaves the highest-risk behavioral seams in the route
- weakens the checkpoint value

### Option 3. Table-components first

Extract JSX into components but leave all fetch, polling, filter, and action logic in the route.

Pros:

- makes the file look smaller quickly

Cons:

- weak boundary
- poor long-term testability
- keeps the route responsible for the real complexity

### Recommended option

Option 1.

This route is not just a table page. It is a runtime and control surface with active scan refresh plus row-level broadcast behavior. The route should only be considered decomposed if both action seams leave the page with the table-state logic.

## 6. Target Module Map

### `frontend/src/app/analytics/page.tsx`

Owns:

- top-level composition
- wiring extracted hooks to extracted components

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
- pure filter and sort helpers if kept independent from React state

### `frontend/src/app/analytics/components/AnalyticsShell.tsx`

Owns:

- page frame
- header
- refresh button
- top status and last-updated copy

### `frontend/src/app/analytics/components/AnalyticsFilters.tsx`

Owns:

- search box
- status filter
- score slider
- column menu

### `frontend/src/app/analytics/components/AnalyticsTable.tsx`

Owns:

- table header
- sort interactions
- loading state row
- empty state row
- row list composition

### `frontend/src/app/analytics/components/AnalyticsRow.tsx`

Owns:

- row-level presentational rendering
- row-level broadcast button trigger through `onBroadcast`

## 7. Data Flow

The intended runtime flow is:

1. `page.tsx` reads analytics table state through `useAnalyticsRuntime`
2. `useAnalyticsRuntime` exposes the loaded rows plus display-ready filtered and sorted rows
3. `page.tsx` reads scan and broadcast behavior through `useAnalyticsActions`
4. `useAnalyticsActions` owns the refresh trigger, polling loop, and row broadcast action
5. `page.tsx` passes display-ready props into `AnalyticsShell`, `AnalyticsFilters`, and `AnalyticsTable`
6. `AnalyticsTable` renders `AnalyticsRow` without owning async orchestration

This keeps behavior in hooks, pure shaping in `analyticsTransforms`, and rendering in components.

## 8. Error Handling And Contract Preservation

The decomposition must preserve the current visible behavior for:

- initial loading state
- fetch failures that currently log without crashing the route
- manual refresh behavior
- scan-status polling behavior
- search-overrides-filter semantics
- empty-result rendering
- row broadcast success and failure behavior

Key rule:

- no backend API contract changes
- no analytics refresh or analytics status contract changes
- no Telegram signal-card payload contract changes
- no changes to visible route outcomes beyond structural extraction

## 9. Testing Strategy

Existing route protection to keep green:

- `frontend/src/app/analytics/page.test.tsx`

New direct seam tests:

- `frontend/src/app/analytics/hooks/useAnalyticsRuntime.test.tsx`
  - payload normalization
  - search overriding filters
  - status and score filtering
  - sort behavior
  - column-toggle behavior
- `frontend/src/app/analytics/hooks/useAnalyticsActions.test.tsx`
  - refresh success and failure
  - scan-status polling completion and error behavior
  - row broadcast success and failure mapping
- `frontend/src/app/analytics/components/AnalyticsShell.test.tsx`
- `frontend/src/app/analytics/components/AnalyticsFilters.test.tsx`
- `frontend/src/app/analytics/components/AnalyticsTable.test.tsx`

Release gate for the Phase 13 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

## 10. Execution Sequencing

Recommended implementation order:

1. extract `analyticsTransforms.ts`
2. extract `useAnalyticsRuntime.ts`
3. extract `useAnalyticsActions.ts`
4. extract `AnalyticsShell.tsx`
5. extract `AnalyticsFilters.tsx`
6. extract `AnalyticsTable.tsx`
7. slim `page.tsx` to composition only
8. run broader frontend verification and write checkpoint docs

This ordering stabilizes pure helpers and runtime/action contracts before moving the large filter and table UI blocks.

## 11. Exit Criteria

Phase 13 should be considered complete when:

- `frontend/src/app/analytics/page.tsx` is primarily composition and lightweight wiring
- analytics bootstrap and table-state behavior live in `useAnalyticsRuntime`
- scan refresh and row broadcast behavior live in `useAnalyticsActions`
- shell, filters, and table rendering live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and core components
- the frontend verification gate passes

## 12. Risks And Mitigations

### Risk: search-overrides-filter behavior drifts during extraction

Mitigation:

- lock the behavior with direct runtime tests
- keep the existing route tests green while extraction proceeds

### Risk: refresh polling behavior changes subtly

Mitigation:

- isolate polling behavior in `useAnalyticsActions`
- test completion and failure paths directly

### Risk: over-engineering a medium route

Mitigation:

- keep only the minimum seam set
- reuse `AnalyticsRow.tsx` rather than replacing it with a new abstraction
