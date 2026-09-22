# Horus Analytics II Phase 6 Live Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-6-live-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 6
Status: Complete on 2026-03-18
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 6 live decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/live/page.tsx` into a thin route shell without changing the route path, backend API contracts, websocket payload semantics, or live feed start/stop behavior.

Phase 6 live work should leave six things true:

1. The route page is no longer the primary home of ticker/bootstrap and intraday runtime orchestration.
2. Analytics refresh and status polling are directly testable through a dedicated seam.
3. Live feed start/stop controls are directly testable through a dedicated controls seam.
4. Sovereign websocket lifecycle behavior is directly testable through a dedicated alerts seam.
5. Chart and panel rendering are isolated behind focused presentational components.
6. The extraction pattern is reusable for the remaining frontend runtime routes after `live`.

## 2. In Scope

Primary source file:

- `frontend/src/app/live/page.tsx`

Primary extraction target areas:

- `frontend/src/app/live/hooks/`
- `frontend/src/app/live/lib/`
- `frontend/src/app/live/components/`

Primary route responsibilities to preserve:

- ticker bootstrap and current ticker selection
- intraday data fetch lifecycle and refresh sequencing
- analytics fetch, refresh, and status polling
- live feed start/stop actions and live-status display
- websocket sovereign-alert subscription and bounded alert buffer
- existing chart/panel display behavior

Out of scope for this Phase 6 slice:

- visual redesign of the live monitor page
- backend endpoint changes
- websocket payload schema changes
- chart semantics changes
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/live/page.test.tsx`
- `frontend/src/app/components/Sidebar.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/live/hooks/useLiveRuntime.test.tsx`
- `frontend/src/app/live/hooks/useLiveAnalytics.test.tsx`
- `frontend/src/app/live/hooks/useLiveControls.test.tsx`
- `frontend/src/app/live/hooks/useSovereignAlerts.test.tsx`
- selected component tests for extracted live panels

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/live/hooks/useLiveRuntime.ts`

Owns:

- ticker bootstrap
- current ticker state
- intraday fetch lifecycle
- refresh cadence state
- loading, error, and last-update state

### `frontend/src/app/live/hooks/useLiveAnalytics.ts`

Owns:

- analytics bootstrap and refresh
- analytics status polling
- empty-data fallback/retry behavior
- radar and analytics shaping for presentation

### `frontend/src/app/live/hooks/useLiveControls.ts`

Owns:

- live feed start action
- live feed stop action
- live-status refresh
- control action loading and status mapping

### `frontend/src/app/live/hooks/useSovereignAlerts.ts`

Owns:

- websocket subscription setup
- message parsing and sovereign-alert filtering
- bounded alert buffer
- cleanup and socket close behavior

### `frontend/src/app/live/lib/liveTransforms.ts`

Owns:

- candle parsing and normalization
- number and price formatting
- chart compression helpers
- small analytics display transforms

### `frontend/src/app/live/components/`

Target components:

- `LiveShell.tsx`
- `LiveChartPanel.tsx`
- `LiveAnalyticsPanel.tsx`
- `LiveStatusPanel.tsx`
- `SovereignAlertsPanel.tsx`

The route page should remain the route owner and composition point. These extracted units should not import the route file.

## 5. Package Sequence

Execute the live decomposition in this order:

1. `F6-P1` Runtime hook and live shell extraction
2. `F6-P2` Analytics seam and chart/panel extraction
3. `F6-P3` Controls and websocket seam extraction
4. `F6-P4` Route slimdown and checkpoint closeout

This order is intentional:

- the runtime seam removes the broadest route-local fetch lifecycle first
- analytics should move before websocket/control logic so the read-side path stabilizes early
- controls and websocket behavior move after the route already has clean runtime seams
- final slimdown should only happen after all high-risk orchestration is extracted and directly tested

## 6. Work Packages

### F6-P1. Runtime Hook and Live Shell Extraction

Status: Completed on 2026-03-18

Purpose:

Establish one reusable seam for live bootstrap and intraday runtime state before moving analytics or websocket logic.

Target files:

- `frontend/src/app/live/page.tsx`
- `frontend/src/app/live/hooks/useLiveRuntime.ts`
- `frontend/src/app/live/components/LiveShell.tsx`
- `frontend/src/app/live/lib/liveTransforms.ts`

Tasks:

1. Move ticker bootstrap, current ticker state, intraday fetch lifecycle, loading/error state, and last-update state into `useLiveRuntime`.
2. Move pure candle parsing/compression and formatting helpers into `liveTransforms.ts`.
3. Extract the page frame and top-level toolbar into `LiveShell`.
4. Keep the route page as the owner of hook wiring and panel composition.
5. Add direct tests for runtime load success, fetch failure, and abort-cleanup behavior.

Deliverables:

- first reusable live runtime hook
- thinner route shell
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/live/page.test.tsx src/app/live/hooks/useLiveRuntime.test.tsx`

Acceptance criteria:

- ticker bootstrap and intraday fetch logic no longer live inline in the route page
- current route-level live tests stay green
- runtime seam is directly testable without rendering the full page

### F6-P2. Analytics Seam and Chart/Panel Extraction

Status: Completed on 2026-03-18

Purpose:

Move analytics refresh/status orchestration behind a dedicated seam and remove the largest read-side render blocks from the route.

Target files:

- `frontend/src/app/live/page.tsx`
- `frontend/src/app/live/hooks/useLiveAnalytics.ts`
- `frontend/src/app/live/components/LiveChartPanel.tsx`
- `frontend/src/app/live/components/LiveAnalyticsPanel.tsx`

Tasks:

1. Move analytics bootstrap, refresh, status polling, and empty-data retry behavior into `useLiveAnalytics`.
2. Extract the intraday chart display into `LiveChartPanel`.
3. Extract analytics/radar rendering into `LiveAnalyticsPanel`.
4. Add direct tests for analytics refresh/status behavior and selected panel rendering interactions.

Deliverables:

- dedicated analytics hook seam
- extracted chart and analytics panels
- direct analytics regression coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/live/page.test.tsx src/app/live/hooks/useLiveAnalytics.test.tsx`

Acceptance criteria:

- analytics orchestration is no longer primarily route-local
- chart and radar rendering no longer dominate the route file
- route-level live behavior remains unchanged

### F6-P3. Controls and Sovereign Alerts Extraction

Status: Completed on 2026-03-18

Purpose:

Isolate the live control-plane actions and websocket lifecycle from the broader runtime path so the route stops mixing polling and push behavior in one implementation.

Target files:

- `frontend/src/app/live/page.tsx`
- `frontend/src/app/live/hooks/useLiveControls.ts`
- `frontend/src/app/live/hooks/useSovereignAlerts.ts`
- `frontend/src/app/live/components/LiveStatusPanel.tsx`
- `frontend/src/app/live/components/SovereignAlertsPanel.tsx`

Tasks:

1. Move live feed start/stop and live-status refresh behavior into `useLiveControls`.
2. Move websocket setup, message parsing, alert buffering, and cleanup into `useSovereignAlerts`.
3. Extract status display into `LiveStatusPanel`.
4. Extract sovereign alert rendering into `SovereignAlertsPanel`.
5. Add direct tests for control success/failure paths and websocket lifecycle behavior.

Deliverables:

- dedicated controls seam
- dedicated websocket/alerts seam
- extracted status and alerts panels
- direct control and websocket regression coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/live/page.test.tsx src/app/live/hooks/useLiveControls.test.tsx src/app/live/hooks/useSovereignAlerts.test.tsx`

Acceptance criteria:

- live start/stop behavior is no longer primarily route-local
- websocket lifecycle is no longer primarily route-local
- route-level live behavior remains stable

### F6-P4. Route Slimdown and Closeout

Status: Completed on 2026-03-18

Purpose:

Remove the remaining route-local business blocks, isolate any last helper residue, and define the frontend checkpoint for this Phase 6 slice.

Target files:

- `frontend/src/app/live/page.tsx`
- all new hook/component test files
- Phase 6 checkpoint docs

Tasks:

1. Remove dead or duplicated helper bodies from the route once extracted seams are live.
2. Keep `page.tsx` focused on composition and light route wiring only.
3. Run the full frontend baseline and browser checks.
4. Write the Phase 6 checkpoint summary and update the roadmap status.

Deliverables:

- materially thinner live route page
- expanded direct seam coverage
- Phase 6 checkpoint artifacts

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- `frontend/src/app/live/page.tsx` is primarily a route shell and composition layer
- runtime, analytics, controls, and websocket behavior are isolated behind explicit seams
- frontend baseline remains green
- the live page has direct hook/component seam tests alongside route anchors

Closeout note:

- Completed with the checkpoint recorded in `docs/superpowers/reference/2026-03-18-phase-6-live-checkpoint-summary.md`.

## 7. Verification Matrix

Each package must declare:

1. protected behavior
2. direct seam tests added or updated
3. route-level tests kept green
4. release gates impacted
5. rollback path

Minimum required verification for this Phase 6 slice:

- route-level live Jest tests
- direct hook tests for runtime, analytics, controls, and websocket seams
- frontend lint and strict production build
- Playwright browser baseline

## 8. Risks and Controls

### Risk: websocket behavior becomes flaky under test

Control:

- keep the websocket seam narrow and directly test message parsing/buffer/cleanup independently from the page

### Risk: analytics retry semantics drift during extraction

Control:

- preserve the current route-level tests and add direct analytics tests before removing route-local logic

### Risk: prop drilling across too many live panels

Control:

- extract around workflow boundaries and keep panel components display-oriented rather than pushing orchestration down into them

## 9. Suggested Execution Cadence

For a single owner, the expected order is:

1. `F6-P1`
2. `F6-P2`
3. `F6-P3`
4. `F6-P4`

Do not start the next package until the current package's targeted tests are green.

## 10. Exit Checklist for the Phase 6 Live Slice

This slice is complete when all of the following are true:

- `frontend/src/app/live/page.tsx` is no longer the primary home for fetch/poll/websocket/control orchestration
- runtime, analytics, controls, and websocket seams exist and are directly tested
- chart/panel rendering lives behind focused presentational components
- the full frontend baseline and browser baseline are green
- a Phase 6 checkpoint summary is written and linked from the top-level roadmap

## 11. Recommended Next Move After This Plan

Phase 6 is complete. The next recommended move is the next frontend runtime decomposition target from the roadmap.
