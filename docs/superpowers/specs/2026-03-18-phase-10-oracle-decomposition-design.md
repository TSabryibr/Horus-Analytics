# Horus Analytics II Phase 10 Oracle Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 10 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Goal

This design defines the next frontend runtime decomposition wave for `frontend/src/app/oracle/page.tsx`.

The objective is to turn the route into a thin composition shell while preserving:

- the current route path
- Oracle data consumption through `useOracleData`
- active index switching behavior for `EGX30`, `EGX70`, and `EGX100`
- AI daily report rendering semantics
- Oracle refresh, force-refresh, and provider-refresh behavior
- AI daily report broadcast behavior
- macro-health and squeeze rendering behavior

The route currently mixes three separate concerns in one file:

1. Oracle runtime state and derived display shaping
2. AI report action flows
3. dashboard panel rendering

Phase 10 should separate those concerns into explicit seams without changing what the page does.

## 2. Why This Route Is Next

`frontend/src/app/oracle/page.tsx` is the strongest remaining frontend runtime target after the completed portfolio, settings, live, simulation, optimization, and Telegram decompositions.

It is the right next boundary because:

- it is still a non-trivial route at about 512 lines
- it mixes derived report-shaping logic with command actions
- it owns both market-selection state and AI report action behavior
- it has multiple large dashboard sections with independent responsibilities
- it already has route-level test anchors that make extraction safer

The file currently combines:

- active market index selection
- AI report metadata derivation and display shaping
- summary/finding/reasoning dedupe logic
- squeeze payload normalization
- price/bandwidth display formatting
- Oracle refresh and provider-refresh commands
- AI daily report broadcast behavior
- large AI report, macro, and squeeze render blocks

That makes the route harder to change safely because one edit can affect data shaping, action behavior, and panel rendering at once.

## 3. Scope

Primary source file:

- `frontend/src/app/oracle/page.tsx`

Primary extraction target areas:

- `frontend/src/app/oracle/hooks/`
- `frontend/src/app/oracle/components/`
- `frontend/src/app/oracle/lib/`

In scope:

- active index state and macro selection
- squeeze candidate normalization
- AI report summary/finding/reasoning shaping
- refresh, no-cache refresh, provider refresh, and broadcast flows
- route shell extraction
- AI report panel extraction
- macro panel extraction
- squeeze panel extraction

Out of scope:

- visual redesign of the Oracle route
- backend endpoint changes
- changes to `useOracleData`
- replacing the current chart placeholder with a real chart implementation
- changing AI report business rules or Oracle provider semantics
- changing visible wording except where required for structural extraction

## 4. Target Boundary

After decomposition, `frontend/src/app/oracle/page.tsx` should keep only:

- top-level composition
- lightweight wiring between extracted hooks and panels

Everything else should move behind explicit seams.

### Route responsibilities that should leave the page

- report-line normalization and dedupe helpers
- squeeze candidate normalization
- active macro selection and derived display metadata
- AI report action behavior
- large AI report rendering block
- macro panel rendering block
- squeeze panel rendering block

### Route responsibilities that may remain

- top-level section ordering
- composition of extracted panels
- small glue code if needed for composition

## 5. Recommended Approach

Three approaches were considered:

### Option 1. Full capability split in one phase

Move runtime derivation and actions behind separate hooks and extract the main dashboard panels into focused components.

Pros:

- strongest structural result
- fits the actual shape of the page
- keeps both read-side derivation and the compact action seam in scope

Cons:

- larger first diff than a panel-only extraction

### Option 2. Read-side split first, actions later

Extract the dashboard derivation and display panels first and leave refresh/broadcast flows in the route.

Pros:

- lower first diff

Cons:

- leaves the one behavior-heavy seam in the route
- produces a weaker checkpoint

### Option 3. Panel-components only

Extract JSX into components but leave all state and actions in the route.

Pros:

- makes the file look smaller quickly

Cons:

- weak boundary
- poor long-term testability
- keeps the route responsible for both shaping and actions

### Recommended option

Option 1.

The Oracle page is smaller than settings, live, or Telegram, so it should be possible to finish the route in one focused decomposition wave without introducing unnecessary extra layers.

## 6. Target Module Map

### `frontend/src/app/oracle/page.tsx`

Owns:

- top-level composition
- wiring extracted hooks to extracted panels

### `frontend/src/app/oracle/hooks/useOracleRuntime.ts`

Owns:

- active index state
- derived macro selection
- squeeze normalization
- AI report summary/finding/reasoning shaping
- label/color metadata for direction, freshness, and provider
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
- small display-shaping helpers that do not need React state

### `frontend/src/app/oracle/components/OracleShell.tsx`

Owns:

- page frame
- header
- refresh button
- top-level layout chrome

### `frontend/src/app/oracle/components/OracleAiReportPanel.tsx`

Owns:

- report header and status badges
- summary and cross-tab findings
- recommendations
- direction reasoning
- risk warnings
- execution profile
- next checklist

### `frontend/src/app/oracle/components/OracleMacroPanel.tsx`

Owns:

- EGX30/EGX70/EGX100 selector
- macro health surface
- correlation/message display
- chart placeholder surface

### `frontend/src/app/oracle/components/OracleSqueezePanel.tsx`

Owns:

- squeeze candidate rendering
- empty-state rendering

## 7. Data Flow

The intended runtime flow is:

1. `page.tsx` reads Oracle context through `useOracleRuntime`
2. `useOracleRuntime` turns raw context data into display-ready state
3. `useOracleActions` exposes command handlers for refresh and broadcast behavior
4. `page.tsx` passes the resulting props into `OracleShell`, `OracleAiReportPanel`, `OracleMacroPanel`, and `OracleSqueezePanel`
5. panels render without owning async orchestration

This keeps behavior in hooks, pure shaping in `oracleTransforms`, and rendering in components.

## 8. Error Handling And Contract Preservation

The decomposition must preserve the current visible behavior for:

- missing Oracle data
- missing AI report data
- squeeze empty state
- broadcast failure feedback
- network failure during AI report broadcast
- disabled loading behavior for refresh-related buttons

Key rule:

- no backend API contract changes
- no context contract changes to `useOracleData`
- no semantic changes to refresh/provider/broadcast behavior
- no changes to current visible route outcomes beyond structural extraction

## 9. Testing Strategy

Existing route protection to keep green:

- `frontend/src/app/oracle/page.test.tsx`

New direct seam tests:

- `frontend/src/app/oracle/hooks/useOracleRuntime.test.tsx`
  - active-index switching
  - summary dedupe
  - squeeze normalization
  - fallback/default shaping
- `frontend/src/app/oracle/hooks/useOracleActions.test.tsx`
  - refresh dispatch
  - provider refresh dispatch
  - broadcast success/failure mapping
- `frontend/src/app/oracle/components/OracleShell.test.tsx`
- `frontend/src/app/oracle/components/OracleAiReportPanel.test.tsx`
- `frontend/src/app/oracle/components/OracleMacroPanel.test.tsx`
- `frontend/src/app/oracle/components/OracleSqueezePanel.test.tsx`

Release gate for the Phase 10 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

## 10. Execution Sequencing

Recommended implementation order:

1. extract `oracleTransforms.ts`
2. extract `useOracleRuntime.ts`
3. extract `OracleShell.tsx`
4. extract `useOracleActions.ts`
5. extract `OracleAiReportPanel.tsx`
6. extract `OracleMacroPanel.tsx`
7. extract `OracleSqueezePanel.tsx`
8. slim `page.tsx` to composition only
9. run broader frontend verification and write checkpoint docs

This ordering reduces risk by locking pure transforms and runtime derivation before moving the heavier panel rendering.

## 11. Exit Criteria

Phase 10 should be considered complete when:

- `frontend/src/app/oracle/page.tsx` is primarily composition and lightweight wiring
- runtime derivation and actions live behind explicit hooks
- the three major dashboard areas live in extracted panels
- existing route tests remain green
- direct seam tests cover the extracted hooks and core panels
- the frontend verification gate passes

## 12. Risks And Mitigations

### Risk: report shaping drifts during extraction

Mitigation:

- move pure normalization/dedupe helpers into `oracleTransforms.ts` first
- lock behavior with direct transform/runtime tests

### Risk: action feedback semantics drift

Mitigation:

- extract `useOracleActions.ts` behind current route tests
- add direct action tests for success and failure mapping

### Risk: the page gets over-engineered relative to its size

Mitigation:

- keep only the minimum seam set
- avoid inventing extra hooks or utilities beyond runtime, actions, panels, and pure transforms
