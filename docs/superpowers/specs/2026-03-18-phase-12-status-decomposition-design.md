# Horus Analytics II Phase 12 Status Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/status/page.tsx`
- `frontend/src/app/status/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 12 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Goal

This design defines the next frontend runtime decomposition wave for `frontend/src/app/status/page.tsx`.

The objective is to turn the route into a thin composition shell while preserving:

- the current route path
- full-status fetch behavior
- last-refresh behavior
- runtime-state badge behavior
- sync-status polling behavior
- sync-start action behavior
- current visible sync status messaging
- current visible observability, freshness, scheduler, and diagnostics rendering semantics

The route currently mixes four separate concerns in one file:

1. full-status fetch/runtime state
2. sync-status polling and transition handling
3. sync-start action behavior
4. large observability/dashboard render blocks

Phase 12 should separate those concerns into explicit seams without changing what the page does.

## 2. Why This Route Is Next

`frontend/src/app/status/page.tsx` is the strongest remaining untreated frontend runtime target after the completed portfolio, settings, live, simulation, optimization, Telegram, Oracle, and Audit decompositions.

It is the right next boundary because:

- it is currently the largest untreated frontend route at about 421 lines
- it owns both read-side status polling and operational sync behavior
- it mixes runtime derivation with sync-state transition logic
- it coordinates several independent dashboard surfaces from one component
- it already has route-level test anchors that make structural extraction safer

The file currently combines:

- full-status fetch
- refresh behavior
- sync-status polling
- sync-start action flow
- transition handling for `RUNNING`, `COMPLETED`, and `ERROR`
- provider/freshness/runtime-state derivation
- large overview/freshness/scheduler/diagnostics render blocks

That makes the route harder to change safely because one edit can affect passive observability reads, active sync controls, and multiple dashboard surfaces at once.

## 3. Scope

Primary source file:

- `frontend/src/app/status/page.tsx`

Primary extraction target areas:

- `frontend/src/app/status/hooks/`
- `frontend/src/app/status/components/`
- `frontend/src/app/status/lib/`

In scope:

- full-status fetch and loading behavior
- last-refresh behavior
- runtime-state derivation inputs and display shaping
- sync-status polling
- sync-start action behavior
- sync transition and message behavior
- route shell extraction
- overview, freshness, scheduler, and diagnostics panel extraction

Out of scope:

- visual redesign of the status route
- backend endpoint changes
- sync API contract changes
- changing runtime-surface semantics
- changing visible wording except where required for structural extraction

## 4. Target Boundary

After decomposition, `frontend/src/app/status/page.tsx` should keep only:

- top-level composition
- lightweight wiring between extracted hooks and panels

Everything else should move behind explicit seams.

### Route responsibilities that should leave the page

- full-status fetch logic
- loading and last-refresh orchestration
- sync-status polling logic
- sync-start action logic
- sync transition handling and message mapping
- provider/freshness/runtime badge derivation
- large overview render block
- large freshness/sync-controls render block
- large scheduler render block
- large diagnostics render block

### Route responsibilities that may remain

- top-level section ordering
- composition of extracted panels
- small glue code if needed for composition

## 5. Recommended Approach

Three approaches were considered:

### Option 1. Full capability split in one phase

Move full-status/runtime behavior and sync control behavior behind separate hooks and extract the major UI regions into focused panels.

Pros:

- strongest structural result
- addresses both read-side and operational complexity together
- matches the successful Phase 4 through Phase 11 frontend decomposition pattern

Cons:

- larger first diff than a read-only extraction

### Option 2. Read-side status first, sync controls later

Extract the passive runtime side first and leave sync polling/start behavior route-local.

Pros:

- lower first diff

Cons:

- leaves the highest-risk mutable behavior in the route
- weakens the checkpoint value

### Option 3. Panel-components first

Move JSX into components but leave runtime and sync logic in the route.

Pros:

- makes the file look smaller quickly

Cons:

- weak boundary
- poor long-term testability
- leaves the route responsible for the real complexity

### Recommended option

Option 1.

The status page is not complex just because it has several dashboard panels. It is complex because it mixes passive observability polling with active operational sync behavior. The correct boundary has to pull both runtime and action behavior out of the route in the same wave.

## 6. Target Module Map

### `frontend/src/app/status/page.tsx`

Owns:

- top-level composition
- wiring extracted hooks to extracted panels

### `frontend/src/app/status/hooks/useStatusRuntime.ts`

Owns:

- full-status fetch
- loading state
- last-refresh state
- runtime-state derivation inputs
- provider/freshness display shaping
- top-card data shaping

### `frontend/src/app/status/hooks/useStatusSync.ts`

Owns:

- sync-status polling
- sync-start action behavior
- transition handling for `RUNNING`, `COMPLETED`, and `ERROR`
- syncing flag
- sync status message state

### `frontend/src/app/status/lib/statusTransforms.ts`

Owns:

- pure KPI card shaping helpers
- freshness row shaping helpers
- scheduler row shaping helpers
- diagnostics label and metadata helpers

### `frontend/src/app/status/components/StatusShell.tsx`

Owns:

- page frame
- title and header chrome
- force-refresh action
- loading-state shell

### `frontend/src/app/status/components/StatusOverviewPanel.tsx`

Owns:

- engine, database, Telegram, and scheduler KPI cards

### `frontend/src/app/status/components/StatusFreshnessPanel.tsx`

Owns:

- history and intraday freshness surface
- sync controls
- sync-status messaging surface

### `frontend/src/app/status/components/StatusSchedulerPanel.tsx`

Owns:

- scheduler/jobs surface

### `frontend/src/app/status/components/StatusDiagnosticsPanel.tsx`

Owns:

- runtime metadata
- provider/source diagnostics
- health detail rows

## 7. Data Flow

The intended runtime flow is:

1. `page.tsx` reads full-status state through `useStatusRuntime`
2. `useStatusRuntime` exposes current status data plus display-ready runtime/freshness metadata
3. `page.tsx` reads sync-state and sync actions through `useStatusSync`
4. `useStatusSync` polls sync status, manages transition messages, and exposes the sync-start action
5. `page.tsx` passes display-ready props into `StatusShell`, `StatusOverviewPanel`, `StatusFreshnessPanel`, `StatusSchedulerPanel`, and `StatusDiagnosticsPanel`
6. panels render without owning async orchestration

This keeps behavior in hooks, pure shaping in `statusTransforms`, and rendering in components.

## 8. Error Handling And Contract Preservation

The decomposition must preserve the current visible behavior for:

- initial loading state
- fetch failures that currently log without crashing the route
- manual refresh behavior
- sync-status polling behavior
- sync-start action outcomes
- `RUNNING` to `COMPLETED` transition behavior
- sync error messaging
- no-data or partial-data cases in overview, freshness, scheduler, and diagnostics surfaces

Key rule:

- no backend API contract changes
- no sync endpoint contract changes
- no semantic changes to sync-start or sync-status behavior
- no changes to visible route outcomes beyond structural extraction

## 9. Testing Strategy

Existing route protection to keep green:

- `frontend/src/app/status/page.test.tsx`

New direct seam tests:

- `frontend/src/app/status/hooks/useStatusRuntime.test.tsx`
  - fetch success/failure
  - refresh action
  - last-refresh updates
  - derived runtime-state shaping
- `frontend/src/app/status/hooks/useStatusSync.test.tsx`
  - sync-status `RUNNING`, `COMPLETED`, and `ERROR` transitions
  - start-sync success path
  - already-running path
  - failure path
- `frontend/src/app/status/components/StatusShell.test.tsx`
- `frontend/src/app/status/components/StatusOverviewPanel.test.tsx`
- `frontend/src/app/status/components/StatusFreshnessPanel.test.tsx`
- `frontend/src/app/status/components/StatusSchedulerPanel.test.tsx`
- `frontend/src/app/status/components/StatusDiagnosticsPanel.test.tsx`

Release gate for the Phase 12 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

## 10. Execution Sequencing

Recommended implementation order:

1. extract `statusTransforms.ts`
2. extract `useStatusRuntime.ts`
3. extract `useStatusSync.ts`
4. extract `StatusShell.tsx`
5. extract `StatusOverviewPanel.tsx`
6. extract `StatusFreshnessPanel.tsx`
7. extract `StatusSchedulerPanel.tsx`
8. extract `StatusDiagnosticsPanel.tsx`
9. slim `page.tsx` to composition only
10. run broader frontend verification and write checkpoint docs

This ordering stabilizes pure helpers and runtime/action contracts before moving the large UI blocks.

## 11. Exit Criteria

Phase 12 should be considered complete when:

- `frontend/src/app/status/page.tsx` is primarily composition and lightweight wiring
- full-status runtime behavior lives in `useStatusRuntime`
- sync polling and sync-start action behavior live in `useStatusSync`
- overview, freshness, scheduler, and diagnostics rendering live in extracted panels
- existing route tests remain green
- direct seam tests cover the extracted hooks and core panels
- the frontend verification gate passes

## 12. Risks And Mitigations

### Risk: sync transition behavior drifts during extraction

Mitigation:

- isolate transition mapping and message rules early
- lock the sync seam with direct tests

### Risk: runtime badge or freshness semantics drift

Mitigation:

- keep route tests green while adding direct runtime coverage
- move shaping logic into pure helpers first if needed

### Risk: over-engineering a medium-large page

Mitigation:

- keep only the minimum seam set
- avoid adding extra abstraction beyond runtime, sync, transforms, shell, and the four main panels
