# Horus Analytics II Phase 12 Status Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-12-status-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 12
Status: Complete
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 12 Status decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/status/page.tsx` into a thin route shell without changing the route path, full-status fetch semantics, last-refresh behavior, runtime-state badge behavior, sync-status polling behavior, sync-start behavior, or current visible observability, freshness, scheduler, and diagnostics rendering.

Phase 12 Status work should leave six things true:

1. The route page is no longer the primary home of full-status fetch and refresh orchestration.
2. The route page is no longer the primary home of sync-status polling and transition behavior.
3. The route page is no longer the primary home of sync-start action handling and sync-status messaging.
4. The overview, freshness, scheduler, and diagnostics surfaces are extracted into focused panels.
5. Pure status shaping helpers are isolated behind a small transform seam.
6. The extraction pattern remains consistent with the Phase 4 through Phase 11 frontend decomposition track.

## 2. In Scope

Primary source file:

- `frontend/src/app/status/page.tsx`

Primary extraction target areas:

- `frontend/src/app/status/hooks/`
- `frontend/src/app/status/lib/`
- `frontend/src/app/status/components/`

Primary route responsibilities to preserve:

- full-status fetch behavior
- last-refresh behavior
- runtime-state badge behavior
- force-refresh behavior
- sync-status polling behavior
- sync-start action behavior
- `RUNNING`, `COMPLETED`, and `ERROR` transition handling
- sync status message behavior
- current visible overview, freshness, scheduler, and diagnostics rendering semantics

Out of scope for this Phase 12 slice:

- visual redesign of the status page
- backend endpoint changes
- sync API contract changes
- changing runtime-state or freshness semantics
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/status/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/status/hooks/useStatusRuntime.test.tsx`
- `frontend/src/app/status/hooks/useStatusSync.test.tsx`
- selected component tests for shell, overview, freshness, scheduler, and diagnostics panels

## 4. Target Module Map

The decomposition should converge on this internal shape:

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

### `frontend/src/app/status/components/`

Target components:

- `StatusShell.tsx`
- `StatusOverviewPanel.tsx`
- `StatusFreshnessPanel.tsx`
- `StatusSchedulerPanel.tsx`
- `StatusDiagnosticsPanel.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Status decomposition in this order:

1. `F12-P1` Pure transforms and runtime extraction
2. `F12-P2` Sync behavior and shell extraction
3. `F12-P3` Overview, freshness, scheduler, and diagnostics panel extraction
4. `F12-P4` Route slimdown and checkpoint closeout

This order is intentional:

- pure transforms move first because they stabilize status/freshness/scheduler shaping contracts
- runtime fetch/refresh moves before panels so the UI consumes display-ready state
- sync extraction follows once runtime ownership is explicit
- final slimdown happens only after the route is fully covered by seams

## 6. Work Packages

### F12-P1. Pure Transforms and Runtime Extraction

Status: Complete

Purpose:

Establish the pure shaping helpers and isolate the full-status bootstrap/runtime behavior before moving sync logic and panel rendering.

Target files:

- `frontend/src/app/status/page.tsx`
- `frontend/src/app/status/lib/statusTransforms.ts`
- `frontend/src/app/status/hooks/useStatusRuntime.ts`

Tasks:

1. Move KPI, freshness, scheduler, and diagnostics shaping helpers into `statusTransforms.ts`.
2. Move full-status fetch, loading state, last-refresh state, and refresh behavior into `useStatusRuntime`.
3. Move runtime-state derivation inputs and display-ready status shaping into `useStatusRuntime`.
4. Add direct tests for fetch success/failure, refresh behavior, last-refresh updates, and derived runtime-state behavior.

Deliverables:

- shared Status transforms
- runtime seam for display-ready status state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/status/page.test.tsx src/app/status/hooks/useStatusRuntime.test.tsx`

Acceptance criteria:

- bootstrap/runtime behavior is no longer primarily route-local
- pure helper logic is no longer defined inline in the route
- current route-level Status tests stay green

### F12-P2. Sync Behavior and Shell Extraction

Status: Complete

Purpose:

Separate the sync polling/action behavior and shared page chrome once runtime state is stable.

Target files:

- `frontend/src/app/status/page.tsx`
- `frontend/src/app/status/hooks/useStatusSync.ts`
- `frontend/src/app/status/components/StatusShell.tsx`

Tasks:

1. Extract the page frame, title, force-refresh action, and loading shell into `StatusShell`.
2. Move sync-status polling, sync-start action, transition handling, sync status messages, and cleanup behavior into `useStatusSync`.
3. Keep current sync transition semantics and messaging behavior intact.
4. Add direct tests for sync transitions, start-sync behavior, and shell rendering.

Deliverables:

- shared Status shell
- dedicated Status sync seam
- direct sync seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/status/page.test.tsx src/app/status/hooks/useStatusSync.test.tsx src/app/status/components/StatusShell.test.tsx`

Acceptance criteria:

- sync behavior is no longer primarily route-local
- header and refresh chrome are no longer defined inline in the route
- current route-level Status behavior remains stable

### F12-P3. Overview, Freshness, Scheduler, and Diagnostics Panel Extraction

Status: Complete

Purpose:

Finish the structural decomposition by extracting the four major dashboard surfaces into focused panels.

Target files:

- `frontend/src/app/status/page.tsx`
- `frontend/src/app/status/components/StatusOverviewPanel.tsx`
- `frontend/src/app/status/components/StatusFreshnessPanel.tsx`
- `frontend/src/app/status/components/StatusSchedulerPanel.tsx`
- `frontend/src/app/status/components/StatusDiagnosticsPanel.tsx`

Tasks:

1. Extract the KPI card surface into `StatusOverviewPanel`.
2. Extract the data freshness and sync-control surface into `StatusFreshnessPanel`.
3. Extract the scheduler/jobs surface into `StatusSchedulerPanel`.
4. Extract the runtime/provider detail surface into `StatusDiagnosticsPanel`.
5. Add direct tests for the major rendering branches in each panel.

Deliverables:

- extracted Status overview panel
- extracted Status freshness panel
- extracted Status scheduler panel
- extracted Status diagnostics panel
- direct panel coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/status/page.test.tsx src/app/status/components/StatusOverviewPanel.test.tsx src/app/status/components/StatusFreshnessPanel.test.tsx src/app/status/components/StatusSchedulerPanel.test.tsx src/app/status/components/StatusDiagnosticsPanel.test.tsx`

Acceptance criteria:

- the four dashboard sections are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level Status behavior remains stable

### F12-P4. Route Slimdown and Closeout

Status: Complete

Purpose:

Remove remaining route-local residue, finish seam coverage, and define the frontend checkpoint for this Phase 12 slice.

Target files:

- `frontend/src/app/status/page.tsx`
- all new hook/component test files
- Phase 12 checkpoint docs

Tasks:

1. Remove dead or duplicated helper bodies from the route once seams are live.
2. Keep `page.tsx` focused on composition and minimal wiring only.
3. Run the full frontend baseline and browser checks.
4. Write the Phase 12 checkpoint summary and update the roadmap status.

Deliverables:

- materially thinner Status route page
- expanded direct seam coverage
- Phase 12 checkpoint artifacts

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- `frontend/src/app/status/page.tsx` is primarily a route shell and composition layer
- runtime and sync behavior are isolated behind explicit seams
- the frontend baseline remains green
- Status has direct hook/component seam tests alongside route anchors

## 7. Verification Matrix

Each package must declare:

1. protected behavior
2. direct seam tests added or updated
3. route-level tests kept green
4. release gates impacted

Expected verification progression:

- package-level route-plus-seam subsets during `F12-P1` through `F12-P3`
- full frontend lint/test/build/e2e gate during `F12-P4`

## 8. Route Slimdown Target

The Phase 12 structural target is:

- `frontend/src/app/status/page.tsx` owns composition only
- full-status runtime behavior lives in `useStatusRuntime`
- sync polling and action behavior live in `useStatusSync`
- overview, freshness, scheduler, and diagnostics surfaces live in extracted panels
- pure helpers live in `statusTransforms`

The route should not remain the home of fetch logic, sync transition logic, sync action behavior, or large render blocks once the phase closes.

## 9. Risks And Controls

### Risk: sync transition behavior drifts during extraction

Control:

- isolate transition mapping and message rules early
- keep route tests green while adding direct sync coverage

### Risk: runtime badge or freshness shaping drifts

Control:

- move pure helpers first
- lock runtime shaping with direct tests

### Risk: over-engineering a medium-large route

Control:

- keep only the minimum seam set
- avoid adding extra abstraction beyond runtime, sync, transforms, shell, and four panels

## 10. Exit Criteria

Phase 12 should be considered complete when:

- `frontend/src/app/status/page.tsx` is primarily composition and lightweight wiring
- full-status runtime behavior lives in `useStatusRuntime`
- sync polling and sync-start action behavior live in `useStatusSync`
- overview, freshness, scheduler, and diagnostics rendering live in extracted panels
- route tests remain green
- direct seam tests cover the extracted hooks and core panels
- the frontend verification gate passes

Phase 12 is complete. The route is reduced to composition over `useStatusRuntime`, `useStatusSync`, `StatusShell`, `StatusOverviewPanel`, `StatusFreshnessPanel`, `StatusSchedulerPanel`, and `StatusDiagnosticsPanel`, with the checkpoint recorded in `docs/superpowers/reference/2026-03-18-phase-12-status-checkpoint-summary.md`.
