# Horus Analytics II Phase 10 Oracle Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-10-oracle-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 10
Status: Complete on 2026-03-18
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 10 Oracle decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/oracle/page.tsx` into a thin route shell without changing the route path, Oracle context consumption, active-index behavior, AI report rendering semantics, Oracle refresh/provider semantics, or AI daily report broadcast behavior.

Phase 10 Oracle work should leave five things true:

1. The route page is no longer the primary home of Oracle runtime derivation and display shaping.
2. The route page is no longer the primary home of refresh and broadcast command behavior.
3. The AI report, macro, and squeeze surfaces are extracted into focused panels.
4. Pure formatting and dedupe helpers are isolated behind a small transform seam.
5. The extraction pattern remains consistent with the Phase 4 through Phase 9 frontend decomposition track.

## 2. In Scope

Primary source file:

- `frontend/src/app/oracle/page.tsx`

Primary extraction target areas:

- `frontend/src/app/oracle/hooks/`
- `frontend/src/app/oracle/lib/`
- `frontend/src/app/oracle/components/`

Primary route responsibilities to preserve:

- active index switching for `EGX30`, `EGX70`, and `EGX100`
- AI report summary/finding/reasoning rendering behavior
- Oracle refresh behavior
- no-cache AI report refresh behavior
- provider refresh behavior
- AI daily report broadcast behavior
- macro health rendering
- squeeze rendering and empty-state behavior

Out of scope for this Phase 10 slice:

- visual redesign of the Oracle page
- backend endpoint changes
- changing `useOracleData`
- replacing the current chart placeholder with a real chart
- changing Oracle business semantics
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/oracle/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/oracle/hooks/useOracleRuntime.test.tsx`
- `frontend/src/app/oracle/hooks/useOracleActions.test.tsx`
- selected component tests for shell, AI report panel, macro panel, and squeeze panel

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/oracle/hooks/useOracleRuntime.ts`

Owns:

- active index state
- derived macro selection
- squeeze candidate normalization
- AI report summary/finding/reasoning shaping
- provider/freshness/direction badge metadata
- chart data shaping

### `frontend/src/app/oracle/hooks/useOracleActions.ts`

Owns:

- refresh action
- no-cache refresh action
- provider refresh action
- AI report broadcast action
- action feedback and loading state

### `frontend/src/app/oracle/lib/oracleTransforms.ts`

Owns:

- pure report-line normalization and dedupe helpers
- truncation helpers
- small display-shaping helpers

### `frontend/src/app/oracle/components/`

Target components:

- `OracleShell.tsx`
- `OracleAiReportPanel.tsx`
- `OracleMacroPanel.tsx`
- `OracleSqueezePanel.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Oracle decomposition in this order:

1. `F10-P1` Pure transforms and runtime extraction
2. `F10-P2` Route shell and action seam extraction
3. `F10-P3` Panel extraction
4. `F10-P4` Route slimdown and checkpoint closeout

This order is intentional:

- pure transforms move first because they stabilize the shaping contract
- runtime derivation moves before panels so the render surfaces consume display-ready data
- action extraction follows once route state is stabilized
- final slimdown happens only after the route is fully covered by seams

## 6. Work Packages

### F10-P1. Pure Transforms and Runtime Extraction

Status: Completed on 2026-03-18

Purpose:

Establish the pure shaping helpers and isolate the Oracle-derived runtime behavior before moving action and panel logic.

Target files:

- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/lib/oracleTransforms.ts`
- `frontend/src/app/oracle/hooks/useOracleRuntime.ts`

Tasks:

1. Move report-line normalization, dedupe, and truncation helpers into `oracleTransforms.ts`.
2. Move active-index state and derived macro selection into `useOracleRuntime`.
3. Move squeeze normalization and AI report shaping into `useOracleRuntime`.
4. Add direct tests for active-index switching, dedupe behavior, squeeze normalization, and fallback shaping.

Deliverables:

- shared Oracle transforms
- runtime seam for display-ready Oracle state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/oracle/page.test.tsx src/app/oracle/hooks/useOracleRuntime.test.tsx`

Acceptance criteria:

- display shaping is no longer primarily route-local
- pure helper logic is no longer defined inline in the route
- current route-level Oracle tests stay green

### F10-P2. Route Shell and Action Extraction

Status: Completed on 2026-03-18

Purpose:

Separate the compact action seam and the shared page chrome once runtime shaping is stable.

Target files:

- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/hooks/useOracleActions.ts`
- `frontend/src/app/oracle/components/OracleShell.tsx`

Tasks:

1. Extract the page frame, header, refresh button, and top-level layout chrome into `OracleShell`.
2. Move refresh, no-cache refresh, provider refresh, and AI report broadcast behavior into `useOracleActions`.
3. Add direct tests for refresh dispatch, provider refresh dispatch, and broadcast success/failure mapping.
4. Keep current loading/disabled semantics intact.

Deliverables:

- shared Oracle shell
- dedicated Oracle action seam
- direct action seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/oracle/page.test.tsx src/app/oracle/hooks/useOracleActions.test.tsx src/app/oracle/components/OracleShell.test.tsx`

Acceptance criteria:

- Oracle action behavior is no longer primarily route-local
- shell chrome is no longer defined inline in the route
- current route-level Oracle behavior remains stable

### F10-P3. Panel Extraction

Status: Completed on 2026-03-18

Purpose:

Finish the structural decomposition by extracting the three major dashboard surfaces into focused presentational panels.

Target files:

- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/components/OracleAiReportPanel.tsx`
- `frontend/src/app/oracle/components/OracleMacroPanel.tsx`
- `frontend/src/app/oracle/components/OracleSqueezePanel.tsx`

Tasks:

1. Extract the AI report surface into `OracleAiReportPanel`.
2. Extract the active-index selector and macro health surface into `OracleMacroPanel`.
3. Extract the squeeze candidates and empty state into `OracleSqueezePanel`.
4. Add direct tests for the major rendering branches in each panel.

Deliverables:

- extracted Oracle report panel
- extracted Oracle macro panel
- extracted Oracle squeeze panel
- direct panel coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/oracle/page.test.tsx src/app/oracle/components/OracleAiReportPanel.test.tsx src/app/oracle/components/OracleMacroPanel.test.tsx src/app/oracle/components/OracleSqueezePanel.test.tsx`

Acceptance criteria:

- the three dashboard sections are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level Oracle behavior remains stable

### F10-P4. Route Slimdown and Closeout

Status: Completed on 2026-03-18

Purpose:

Remove remaining route-local residue, finish seam coverage, and define the frontend checkpoint for this Phase 10 slice.

Target files:

- `frontend/src/app/oracle/page.tsx`
- all new hook/component test files
- Phase 10 checkpoint docs

Tasks:

1. Remove dead or duplicated helper bodies from the route once seams are live.
2. Keep `page.tsx` focused on composition and minimal wiring only.
3. Run the full frontend baseline and browser checks.
4. Write the Phase 10 checkpoint summary and update the roadmap status.

Deliverables:

- materially thinner Oracle route page
- expanded direct seam coverage
- Phase 10 checkpoint artifacts

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- `frontend/src/app/oracle/page.tsx` is primarily a route shell and composition layer
- runtime and actions are isolated behind explicit seams
- the frontend baseline remains green
- Oracle has direct hook/component seam tests alongside route anchors

## 7. Verification Matrix

Each package must declare:

1. protected behavior
2. direct seam tests added or updated
3. route-level tests kept green
4. release gates impacted

Expected verification progression:

- package-level route-plus-seam subsets during `F10-P1` through `F10-P3`
- full frontend lint/test/build/e2e gate during `F10-P4`

## 8. Route Slimdown Target

The Phase 10 structural target is:

- `frontend/src/app/oracle/page.tsx` owns composition only
- runtime derivation lives in `useOracleRuntime`
- command behavior lives in `useOracleActions`
- AI report, macro, and squeeze surfaces live in extracted panels
- pure helpers live in `oracleTransforms`

The route should not remain the home of dedupe logic, provider badge shaping, action feedback handling, or large render blocks once the phase closes.

## 9. Risks And Controls

### Risk: shaping behavior drifts during extraction

Control:

- move pure helpers first
- keep route tests green while adding direct runtime coverage

### Risk: action feedback or disabled-state behavior drifts

Control:

- extract `useOracleActions` behind route tests
- add direct action tests for success and failure mapping

### Risk: over-engineering a medium-sized page

Control:

- keep only the minimum seam set
- avoid adding extra abstraction beyond transforms, runtime, actions, shell, and three panels

## 10. Exit Criteria

Phase 10 should be considered complete when:

- `frontend/src/app/oracle/page.tsx` is primarily composition and lightweight wiring
- pure shaping logic is isolated in `oracleTransforms.ts`
- runtime derivation and actions live behind explicit hooks
- AI report, macro, and squeeze rendering live in extracted panels
- route tests remain green
- direct seam tests cover the extracted hooks and core panels
- the frontend verification gate passes
