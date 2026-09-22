# Horus Analytics II Phase 18 Weekly Report Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-18-weekly-report-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 18
Status: Complete
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 18 Weekly Report decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/reports/weekly/page.tsx` into a thin route shell without changing the route path, the current period-toggle behavior, the current report-load and forced-refresh behavior, the current broadcast payload semantics, the current refresh-after-broadcast flow, the current error and feedback banner behavior, or the current summary and notes rendering semantics.

Phase 18 Weekly Report work should leave six things true:

1. The route page is no longer the primary home of period state, loading state, error state, or feedback state.
2. The route page is no longer the primary home of broadcast behavior.
3. The route page is no longer the primary home of fallback-array and formatting helpers.
4. The shell, overview, summary, and notes surfaces are extracted into focused components.
5. The extracted seams are directly testable without full route execution.
6. The extraction pattern remains consistent with the Phase 4 through Phase 17 frontend decomposition track.

## 2. In Scope

Primary source file:

- `frontend/src/app/reports/weekly/page.tsx`

Primary extraction target areas:

- `frontend/src/app/reports/weekly/hooks/`
- `frontend/src/app/reports/weekly/lib/`
- `frontend/src/app/reports/weekly/components/`

Primary route responsibilities to preserve:

- period selection
- initial report load
- forced refresh behavior
- broadcast behavior
- feedback and error messaging
- overview-card rendering
- market summary and signal review rendering
- warnings and notes rendering

Out of scope for this Phase 18 slice:

- visual redesign of the weekly report route
- backend endpoint changes
- report payload contract changes
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/reports/weekly/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/reports/weekly/hooks/useWeeklyReportRuntime.test.tsx`
- `frontend/src/app/reports/weekly/hooks/useWeeklyReportActions.test.tsx`
- selected component tests for shell, overview, summary panel, and notes panel

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/reports/weekly/hooks/useWeeklyReportRuntime.ts`

Owns:

- period state
- initial load and refresh behavior
- loading, error, and feedback state
- derived fallback arrays and summary accessors

### `frontend/src/app/reports/weekly/hooks/useWeeklyReportActions.ts`

Owns:

- broadcast request behavior
- broadcast loading state
- success and failure feedback mapping
- refresh-after-broadcast behavior

### `frontend/src/app/reports/weekly/lib/weeklyReportTransforms.ts`

Owns:

- fallback-array helpers
- numeric formatting helpers
- small pure report-summary shaping helpers

### `frontend/src/app/reports/weekly/components/`

Target components:

- `WeeklyReportShell.tsx`
- `WeeklyReportOverview.tsx`
- `WeeklyReportSummaryPanel.tsx`
- `WeeklyReportNotesPanel.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Weekly Report decomposition in this order:

1. `F18-P1` Pure transforms and runtime extraction
2. `F18-P2` Action seam and shell extraction
3. `F18-P3` Overview, summary, and notes extraction
4. `F18-P4` Closeout and checkpoint

This order is intentional:

- pure transforms and runtime state move first because they stabilize period, loading, and fallback semantics
- the action seam moves next because broadcast is the main command-side behavior
- the display surfaces move after runtime and action seams are explicit
- final slimdown happens only after the route is fully covered by seams

## 6. Work Packages

### F18-P1. Pure Transforms and Runtime Extraction

Status: Complete

Purpose:

Establish the pure shaping helpers and isolate period, loading, error, feedback, and report-state behavior before moving the broadcast seam or large render blocks.

Target files:

- `frontend/src/app/reports/weekly/page.tsx`
- `frontend/src/app/reports/weekly/lib/weeklyReportTransforms.ts`
- `frontend/src/app/reports/weekly/hooks/useWeeklyReportRuntime.ts`

Tasks:

1. Move fallback-array and small formatting helpers into `weeklyReportTransforms.ts`.
2. Move period state, report load behavior, refresh behavior, and loading/error/feedback state into `useWeeklyReportRuntime`.
3. Keep the route consuming runtime state through the hook instead of inline derivation.
4. Add direct tests for initial weekly load, monthly switch, refresh behavior, and error fallback.

Deliverables:

- shared weekly-report transforms
- runtime seam for weekly-report state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/reports/weekly/page.test.tsx src/app/reports/weekly/hooks/useWeeklyReportRuntime.test.tsx`

Acceptance criteria:

- period and report-load state are no longer primarily route-local
- pure helpers are no longer defined inline in the route
- current route-level report tests stay green

### F18-P2. Action Seam and Shell Extraction

Status: Complete

Purpose:

Separate broadcast behavior and pull the top-level shell, controls, and banners out of the route once runtime state is stable.

Target files:

- `frontend/src/app/reports/weekly/page.tsx`
- `frontend/src/app/reports/weekly/hooks/useWeeklyReportActions.ts`
- `frontend/src/app/reports/weekly/components/WeeklyReportShell.tsx`

Tasks:

1. Extract broadcast behavior into `useWeeklyReportActions`.
2. Preserve refresh-after-broadcast behavior behind the action seam.
3. Extract the page frame, period toggle, refresh/broadcast controls, and error/feedback banners into `WeeklyReportShell`.
4. Add direct tests for broadcast success/failure, refresh-after-broadcast, and shell rendering.

Deliverables:

- dedicated weekly-report action seam
- extracted shell
- direct action and shell tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/reports/weekly/page.test.tsx src/app/reports/weekly/hooks/useWeeklyReportActions.test.tsx src/app/reports/weekly/components/WeeklyReportShell.test.tsx`

Acceptance criteria:

- broadcast behavior is no longer primarily route-local
- top-level shell structure is no longer defined inline in the route
- current route-level report behavior remains stable

### F18-P3. Overview, Summary, and Notes Extraction

Status: Complete

Purpose:

Finish the primary structural decomposition by extracting the visible report surfaces into focused components.

Target files:

- `frontend/src/app/reports/weekly/page.tsx`
- `frontend/src/app/reports/weekly/components/WeeklyReportOverview.tsx`
- `frontend/src/app/reports/weekly/components/WeeklyReportSummaryPanel.tsx`
- `frontend/src/app/reports/weekly/components/WeeklyReportNotesPanel.tsx`

Tasks:

1. Extract the window/regime/signal-quality cards into `WeeklyReportOverview`.
2. Extract market summary and signal review rendering into `WeeklyReportSummaryPanel`.
3. Extract warnings and notes rendering into `WeeklyReportNotesPanel`.
4. Add direct tests for the extracted display surfaces.

Deliverables:

- extracted overview component
- extracted summary panel
- extracted notes panel
- direct component coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/reports/weekly/page.test.tsx src/app/reports/weekly/components/WeeklyReportOverview.test.tsx src/app/reports/weekly/components/WeeklyReportSummaryPanel.test.tsx src/app/reports/weekly/components/WeeklyReportNotesPanel.test.tsx`

Acceptance criteria:

- the main report display surfaces are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level report behavior remains stable

### F18-P4. Closeout and Checkpoint

Status: Complete

Purpose:

Finish seam coverage, run the broader frontend gate, and define the frontend checkpoint for this Phase 18 slice.

Target files:

- `frontend/src/app/reports/weekly/page.tsx`
- all new hook/component test files
- Phase 18 checkpoint docs

Tasks:

1. Run the broader frontend verification gate.
2. Write the Phase 18 checkpoint summary.
3. Update the top-level roadmap.
4. Confirm the route remains primarily composition plus lightweight wiring.

Deliverables:

- complete seam-focused test surface
- Phase 18 checkpoint summary
- updated top-level roadmap

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- all weekly-report seam and route tests are green
- frontend baseline and browser baseline are green
- the route is materially thinner and acts as a composition shell

## 7. Verification Matrix

Each package must declare:

1. The smallest fast test slice that proves the extraction did not break the active contract
2. The broader route-level test anchor that remains green
3. The final checkpoint commands required before Phase 18 is closed

### Fast slices by package

`F18-P1`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/reports/weekly/page.test.tsx src/app/reports/weekly/hooks/useWeeklyReportRuntime.test.tsx`

`F18-P2`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/reports/weekly/page.test.tsx src/app/reports/weekly/hooks/useWeeklyReportActions.test.tsx src/app/reports/weekly/components/WeeklyReportShell.test.tsx`

`F18-P3`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/reports/weekly/page.test.tsx src/app/reports/weekly/components/WeeklyReportOverview.test.tsx src/app/reports/weekly/components/WeeklyReportSummaryPanel.test.tsx src/app/reports/weekly/components/WeeklyReportNotesPanel.test.tsx`

`F18-P4`

- full frontend checkpoint commands

## 8. Risk Notes

### Risk: period and refresh behavior drift during extraction

Mitigation:

- keep the route test green
- add direct runtime tests for weekly load, monthly switch, and forced refresh

### Risk: broadcast feedback changes subtly

Mitigation:

- isolate broadcast behavior in `useWeeklyReportActions`
- test success, failure, and refresh-after-broadcast directly

### Risk: over-engineering a medium report route

Mitigation:

- keep only the minimum seam set
- retain the current summary-card and section patterns
- do not introduce extra abstraction beyond runtime, actions, transforms, shell, overview, summary, and notes

## 9. Checkpoint Definition

Phase 18 should be considered complete when:

- `frontend/src/app/reports/weekly/page.tsx` is primarily composition and lightweight wiring
- period, loading, error, feedback, and summary shaping live in `useWeeklyReportRuntime`
- broadcast and refresh-after-broadcast behavior live in `useWeeklyReportActions`
- shell, overview, summary, and notes surfaces live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and core components
- the frontend verification gate passes

## 10. Notes For Execution

Keep behavior changes out of this slice. If a bug is found during extraction, fix it only if:

1. it is required to preserve the current visible contract, or
2. it is small enough to lock with a direct regression test in the same package

If broader weekly-report UX or layout changes are desired, defer them to a later phase after the structural seam work is complete.

## 11. Recommended Next Move After This Plan

Phase 18 is complete. The next recommended move is to start the next frontend decomposition target on `frontend/src/app/whales/page.tsx`.
