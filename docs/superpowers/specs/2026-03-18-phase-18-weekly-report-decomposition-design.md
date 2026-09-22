# Horus Analytics II Phase 18 Weekly Report Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/reports/weekly/page.tsx`
- `frontend/src/app/reports/weekly/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 18
Status: Proposed design
Owner model: Single owner

## 1. Goal

Phase 18 should turn `frontend/src/app/reports/weekly/page.tsx` into a thin route shell without changing:

- the route path
- `period=weekly|monthly` selection behavior
- initial load and refresh behavior
- broadcast payload semantics
- refresh-after-broadcast behavior
- current error and feedback banner behavior
- current report-summary rendering semantics

The route currently mixes two distinct responsibilities in one file:

1. read-side report loading, period switching, and summary shaping
2. write-side broadcast behavior and post-broadcast refresh flow

The decomposition should leave those responsibilities behind explicit seams that are directly testable.

## 2. Scope

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
- window, regime-shift, and signal-quality summary rendering
- market summary and signal review rendering
- warnings and notes rendering

Out of scope for this Phase 18 slice:

- visual redesign of the weekly report route
- backend endpoint changes
- report payload contract changes
- decomposing unrelated frontend routes

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

- fallback arrays for warnings, notes, and summary lists
- numeric formatting helpers
- small pure display shaping helpers

### `frontend/src/app/reports/weekly/components/`

Target components:

- `WeeklyReportShell.tsx`
- `WeeklyReportOverview.tsx`
- `WeeklyReportSummaryPanel.tsx`
- `WeeklyReportNotesPanel.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Design Rules

The decomposition should follow four rules:

1. Hooks own async orchestration and mutable route state.
2. Pure formatting and fallback helpers live in transforms.
3. Components stay display-oriented and receive explicit props.
4. `page.tsx` should not keep fetch, broadcast, or large summary blocks inline once seams are live.

This keeps the weekly report route consistent with the decomposition pattern already used across the frontend track.

## 6. Recommended Extraction Sequence

Execute the Weekly Report decomposition in this order:

1. `F18-P1` Pure transforms and runtime extraction
2. `F18-P2` Action seam and shell extraction
3. `F18-P3` Overview, summary, and notes extraction
4. `F18-P4` Closeout and checkpoint

This order is intentional:

- runtime and pure shaping move first because they stabilize period selection and report-state semantics
- the action seam moves next because broadcast is the primary command-side behavior
- display surfaces move after runtime and actions are explicit
- closeout happens only after the route is structurally reduced to composition plus wiring

## 7. Testing And Safety

Minimum new anchors:

- `frontend/src/app/reports/weekly/hooks/useWeeklyReportRuntime.test.tsx`
- `frontend/src/app/reports/weekly/hooks/useWeeklyReportActions.test.tsx`
- selected component tests for:
  - `WeeklyReportShell`
  - `WeeklyReportOverview`
  - `WeeklyReportSummaryPanel`
  - `WeeklyReportNotesPanel`

Existing route protection to keep green:

- `frontend/src/app/reports/weekly/page.test.tsx`

Release gate for the Phase 18 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Safety rules:

- no backend API contract changes
- no semantic changes to `period=weekly|monthly`
- no semantic changes to `force_refresh=true` handling
- no semantic changes to broadcast payload behavior
- preserve current visible loading, feedback, period-toggle, and report-summary behavior while extracting

## 8. Phase 18 Completion Definition

Phase 18 should be considered complete when:

- `frontend/src/app/reports/weekly/page.tsx` is primarily composition and lightweight wiring
- period, loading, error, feedback, and report-summary shaping live behind `useWeeklyReportRuntime`
- broadcast and refresh-after-broadcast behavior live behind `useWeeklyReportActions`
- shell, overview, summary, and notes surfaces live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and primary components
- the frontend verification gate passes

## 9. Recommended Next Move After This Spec

Write the Phase 18 implementation plan next, then start `F18-P1` by extracting `weeklyReportTransforms.ts` and `useWeeklyReportRuntime.ts` before touching the broadcast seam or the larger UI blocks.
