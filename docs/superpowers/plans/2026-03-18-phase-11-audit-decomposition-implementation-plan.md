# Horus Analytics II Phase 11 Audit Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-11-audit-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 11
Status: Complete
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 11 Audit decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/audit/page.tsx` into a thin route shell without changing the route path, audit fetch semantics, day-range/filter behavior, CSV export behavior, WebSocket stream behavior, or current visible chart, summary, and ledger behavior.

Phase 11 Audit work should leave six things true:

1. The route page is no longer the primary home of bootstrap fetch and loading orchestration.
2. The route page is no longer the primary home of WebSocket lifecycle and streamed-log merge behavior.
3. The route page is no longer the primary home of export and chart-shaping behavior.
4. The chart, summary, and ledger surfaces are extracted into focused panels.
5. Pure audit shaping helpers are isolated behind a small transform seam.
6. The extraction pattern remains consistent with the Phase 4 through Phase 10 frontend decomposition track.

## 2. In Scope

Primary source file:

- `frontend/src/app/audit/page.tsx`

Primary extraction target areas:

- `frontend/src/app/audit/hooks/`
- `frontend/src/app/audit/lib/`
- `frontend/src/app/audit/components/`

Primary route responsibilities to preserve:

- bootstrap fetch behavior
- day-range query switching
- strategy filtering
- expanded-row behavior
- CSV export semantics
- comparison chart shaping
- WebSocket subscription and cleanup behavior
- duplicate-suppression and bounded insertion behavior for streamed logs
- current visible chart, summary, and ledger rendering semantics

Out of scope for this Phase 11 slice:

- visual redesign of the audit page
- backend endpoint changes
- WebSocket payload contract changes
- changing audit metric semantics
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/audit/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/audit/hooks/useAuditRuntime.test.tsx`
- `frontend/src/app/audit/hooks/useAuditStream.test.tsx`
- selected component tests for shell, charts panel, summary panel, and ledger panel

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/audit/hooks/useAuditRuntime.ts`

Owns:

- bootstrap fetch
- loading state
- day-range state
- strategy-filter state
- expanded-row state
- CSV export behavior
- comparison/chart data shaping

### `frontend/src/app/audit/hooks/useAuditStream.ts`

Owns:

- WebSocket setup
- payload parsing
- duplicate suppression
- bounded log insertion
- cleanup behavior

### `frontend/src/app/audit/lib/auditTransforms.ts`

Owns:

- pure comparison-data shaping helpers
- CSV row shaping helpers
- badge and status helpers
- pure log-merge helpers if that reduces hook complexity cleanly

### `frontend/src/app/audit/components/`

Target components:

- `AuditShell.tsx`
- `AuditChartsPanel.tsx`
- `AuditSummaryPanel.tsx`
- `AuditLedgerPanel.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Audit decomposition in this order:

1. `F11-P1` Pure transforms and runtime extraction
2. `F11-P2` WebSocket stream extraction and shell extraction
3. `F11-P3` Charts, summary, and ledger panel extraction
4. `F11-P4` Route slimdown and checkpoint closeout

This order is intentional:

- pure transforms move first because they stabilize chart/export/log shaping contracts
- runtime fetch/export moves before panels so the UI consumes display-ready state
- stream extraction follows once runtime ownership is explicit
- final slimdown happens only after the route is fully covered by seams

## 6. Work Packages

### F11-P1. Pure Transforms and Runtime Extraction

Status: Complete

Purpose:

Establish the pure shaping helpers and isolate the audit bootstrap/runtime behavior before moving stream logic and panel rendering.

Target files:

- `frontend/src/app/audit/page.tsx`
- `frontend/src/app/audit/lib/auditTransforms.ts`
- `frontend/src/app/audit/hooks/useAuditRuntime.ts`

Tasks:

1. Move comparison-data shaping and export-row helpers into `auditTransforms.ts`.
2. Move bootstrap fetch, loading state, day-range state, strategy-filter state, and expanded-row state into `useAuditRuntime`.
3. Move export behavior into `useAuditRuntime`.
4. Add direct tests for fetch success/failure, day-range re-fetch, export behavior, and derived comparison data.

Deliverables:

- shared Audit transforms
- runtime seam for display-ready audit state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/audit/page.test.tsx src/app/audit/hooks/useAuditRuntime.test.tsx`

Acceptance criteria:

- bootstrap/runtime behavior is no longer primarily route-local
- pure helper logic is no longer defined inline in the route
- current route-level Audit tests stay green

### F11-P2. WebSocket Stream and Shell Extraction

Status: Complete

Purpose:

Separate the real-time stream behavior and shared page chrome once runtime state is stable.

Target files:

- `frontend/src/app/audit/page.tsx`
- `frontend/src/app/audit/hooks/useAuditStream.ts`
- `frontend/src/app/audit/components/AuditShell.tsx`

Tasks:

1. Extract the page frame, title, day-range controls, refresh button, export button, and loading shell into `AuditShell`.
2. Move WebSocket setup, payload parsing, duplicate suppression, bounded insertion, and cleanup into `useAuditStream`.
3. Keep current stream merge semantics and cleanup behavior intact.
4. Add direct tests for socket parsing, duplicate suppression, cleanup, and shell rendering.

Deliverables:

- shared Audit shell
- dedicated Audit stream seam
- direct stream seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/audit/page.test.tsx src/app/audit/hooks/useAuditStream.test.tsx src/app/audit/components/AuditShell.test.tsx`

Acceptance criteria:

- stream behavior is no longer primarily route-local
- header and control chrome are no longer defined inline in the route
- current route-level Audit behavior remains stable

### F11-P3. Charts, Summary, and Ledger Panel Extraction

Status: Complete

Purpose:

Finish the structural decomposition by extracting the three major dashboard surfaces into focused panels.

Target files:

- `frontend/src/app/audit/page.tsx`
- `frontend/src/app/audit/components/AuditChartsPanel.tsx`
- `frontend/src/app/audit/components/AuditSummaryPanel.tsx`
- `frontend/src/app/audit/components/AuditLedgerPanel.tsx`

Tasks:

1. Extract the chart surfaces into `AuditChartsPanel`.
2. Extract the KPI/sidebar/strategy-card surface into `AuditSummaryPanel`.
3. Extract the filterable expandable log table into `AuditLedgerPanel`.
4. Add direct tests for the major rendering branches in each panel.

Deliverables:

- extracted Audit charts panel
- extracted Audit summary panel
- extracted Audit ledger panel
- direct panel coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/audit/page.test.tsx src/app/audit/components/AuditChartsPanel.test.tsx src/app/audit/components/AuditSummaryPanel.test.tsx src/app/audit/components/AuditLedgerPanel.test.tsx`

Acceptance criteria:

- the three dashboard sections are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level Audit behavior remains stable

### F11-P4. Route Slimdown and Closeout

Status: Complete

Purpose:

Remove remaining route-local residue, finish seam coverage, and define the frontend checkpoint for this Phase 11 slice.

Target files:

- `frontend/src/app/audit/page.tsx`
- all new hook/component test files
- Phase 11 checkpoint docs

Tasks:

1. Remove dead or duplicated helper bodies from the route once seams are live.
2. Keep `page.tsx` focused on composition and minimal wiring only.
3. Run the full frontend baseline and browser checks.
4. Write the Phase 11 checkpoint summary and update the roadmap status.

Deliverables:

- materially thinner Audit route page
- expanded direct seam coverage
- Phase 11 checkpoint artifacts

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- `frontend/src/app/audit/page.tsx` is primarily a route shell and composition layer
- runtime and stream behavior are isolated behind explicit seams
- the frontend baseline remains green
- Audit has direct hook/component seam tests alongside route anchors

## 7. Verification Matrix

Each package must declare:

1. protected behavior
2. direct seam tests added or updated
3. route-level tests kept green
4. release gates impacted

Expected verification progression:

- package-level route-plus-seam subsets during `F11-P1` through `F11-P3`
- full frontend lint/test/build/e2e gate during `F11-P4`

## 8. Route Slimdown Target

The Phase 11 structural target is:

- `frontend/src/app/audit/page.tsx` owns composition only
- bootstrap and export behavior live in `useAuditRuntime`
- WebSocket lifecycle lives in `useAuditStream`
- chart, summary, and ledger surfaces live in extracted panels
- pure helpers live in `auditTransforms`

The route should not remain the home of fetch logic, stream merge logic, export shaping, or large render blocks once the phase closes.

## 9. Risks And Controls

### Risk: stream merge behavior drifts during extraction

Control:

- isolate duplicate suppression and merge helpers early
- keep route tests green while adding direct stream coverage

### Risk: export or chart shaping drifts

Control:

- move pure helpers first
- lock runtime shaping with direct tests

### Risk: over-engineering a medium-sized route

Control:

- keep only the minimum seam set
- avoid adding extra abstraction beyond runtime, stream, transforms, shell, and three panels

## 10. Exit Criteria

Phase 11 should be considered complete when:

- `frontend/src/app/audit/page.tsx` is primarily composition and lightweight wiring
- runtime fetch/export behavior lives in `useAuditRuntime`
- WebSocket stream behavior lives in `useAuditStream`
- charts, summary, and ledger rendering live in extracted panels
- route tests remain green
- direct seam tests cover the extracted hooks and core panels
- the frontend verification gate passes

Phase 11 is complete. The route is reduced to composition over `useAuditRuntime`, `useAuditStream`, `AuditShell`, `AuditChartsPanel`, `AuditSummaryPanel`, and `AuditLedgerPanel`, with the checkpoint recorded in `docs/superpowers/reference/2026-03-18-phase-11-audit-checkpoint-summary.md`.
