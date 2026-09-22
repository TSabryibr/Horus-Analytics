# Horus Analytics II Phase 6 Live Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-5-settings-checkpoint-summary.md`

Track: Frontend Runtime Stability
Phase: Phase 6 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Why this is the next Phase 6 target

After the Phase 5 settings split, the clearest remaining oversized frontend runtime route is `frontend/src/app/live/page.tsx`.

Current shape:

- `frontend/src/app/live/page.tsx` is about 774 lines
- it owns ticker bootstrap, intraday fetch lifecycle, analytics refresh/status polling, websocket sovereign alerts, live feed start/stop controls, poll cadence state, formatting helpers, and large route-local render blocks
- the current route test file `frontend/src/app/live/page.test.tsx` protects meaningful behavior, but the implementation still concentrates multiple independent runtime domains in one route

This is the next high-value structural target because it mixes read-side runtime orchestration, websocket subscription logic, control-plane actions, and chart/panel rendering in one component.

## 2. Phase 6 goal

Turn the live monitor page into a thin route shell that composes smaller hooks and panel components, without changing:

- route path
- backend live-status, analytics, intraday, or ticker API contracts
- websocket payload contract for sovereign alerts
- live feed start/stop semantics
- current polling behavior unless explicitly documented in the implementation plan

At the end of this slice, the live surface should follow the same capability-oriented structure already used in the Phase 4 portfolio and Phase 5 settings frontend splits.

## 3. In scope

Primary source:

- `frontend/src/app/live/page.tsx`

Primary supporting files:

- `frontend/src/app/live/page.test.tsx`
- live-route helpers/tests touched by current route behavior

In-scope workflows:

- ticker bootstrap and current ticker selection
- intraday data fetch lifecycle and refresh sequencing
- analytics fetch, refresh, and status polling
- live feed start/stop actions and live-status display
- websocket sovereign alert subscription and buffer management
- chart/panel display for intraday and analytics data

## 4. Out of scope

This design does not include:

- redesigning the live monitor UI
- backend endpoint changes
- websocket server or payload-schema changes
- changing chart semantics or analytics calculations
- decomposing unrelated frontend routes in the same implementation slice

## 5. Current responsibility map

The current live page mixes five responsibility classes:

1. Runtime bootstrap for ticker universe, current ticker, loading state, and last-update state
2. Analytics refresh and status orchestration, including empty-data retry behavior
3. Live control-plane actions for start, stop, and live-status refresh
4. Websocket subscription, sovereign-alert parsing, and bounded alert buffering
5. Large route-local render blocks and transformation helpers for charts and panels

This makes the file expensive to change safely because one edit can affect network sequencing, websocket lifecycle, control behavior, and visual rendering at once.

## 6. Recommended decomposition approach

Recommended approach: capability split in one slice.

This means extracting the live route by workflow boundary instead of doing a helper-only or component-only split.

### 6.1 Route shell

Keep `frontend/src/app/live/page.tsx` as the route owner, but reduce it to:

- route-level composition
- wiring of extracted hooks
- lightweight local view state only if still needed after extraction

### 6.2 Runtime hook

Create a focused runtime hook, for example:

- `frontend/src/app/live/hooks/useLiveRuntime.ts`

Responsibilities:

- ticker bootstrap
- current ticker state
- intraday fetch lifecycle
- refresh cadence state
- loading, error, and last-update state

This hook should not own analytics polling, websocket behavior, or live start/stop actions.

### 6.3 Analytics hook

Create a dedicated analytics seam, for example:

- `frontend/src/app/live/hooks/useLiveAnalytics.ts`

Responsibilities:

- analytics bootstrap and refresh
- analytics status polling
- empty-data retry behavior
- radar and analytics data shaping for presentation

This keeps analytics orchestration separate from intraday fetch and control-plane actions.

### 6.4 Controls hook

Create a command-style controls seam, for example:

- `frontend/src/app/live/hooks/useLiveControls.ts`

Responsibilities:

- start live feed
- stop live feed
- refresh live status
- action loading and status mapping

This hook should centralize the control-plane contract and remove start/stop business logic from the route page.

### 6.5 Sovereign alerts hook

Create a websocket-focused seam, for example:

- `frontend/src/app/live/hooks/useSovereignAlerts.ts`

Responsibilities:

- websocket subscription setup
- payload parsing and sovereign-alert filtering
- bounded in-memory alert buffer
- cleanup and socket close behavior

This keeps realtime lifecycle logic independent from the rest of the page runtime.

### 6.6 Presentational components

Extract the largest render blocks into focused components under:

- `frontend/src/app/live/components/`

Target groups:

- live page shell and toolbar
- intraday chart panel
- analytics/radar panel
- live-status panel
- sovereign-alerts panel

These components should stay mostly presentational, with handlers and data passed in from hooks and the route shell.

### 6.7 Shared transforms

Move route-local transformation helpers into:

- `frontend/src/app/live/lib/liveTransforms.ts`

Expected responsibilities:

- number formatting
- candle parsing and normalization
- candle compression
- small analytics display helpers

This prevents helper drift between hooks and panels while keeping the route clean.

## 7. Alternatives considered

### Option A. Read-side first, controls/websocket later

Pros:

- lower short-term diff
- simpler first extraction

Cons:

- leaves the highest-risk runtime behavior tangled in the route
- weakens the structural value of the checkpoint

Reject for this phase.

### Option B. Full capability split in one slice

Pros:

- matches the route's actual responsibility boundaries
- isolates websocket and control-plane behavior behind direct seams
- produces real testable units
- follows the successful Phases 4 and 5 frontend pattern

Cons:

- moderate multi-file diff
- requires careful test anchors for polling and websocket cleanup

Recommendation:

- choose Option B

### Option C. Component-first split with state left local

Pros:

- makes the file look smaller quickly

Cons:

- keeps async, polling, and websocket tangles alive
- likely creates prop-drilling without real structural repair

Reject for this phase.

## 8. Target file map

Proposed target shape:

- `frontend/src/app/live/page.tsx`
- `frontend/src/app/live/hooks/useLiveRuntime.ts`
- `frontend/src/app/live/hooks/useLiveAnalytics.ts`
- `frontend/src/app/live/hooks/useLiveControls.ts`
- `frontend/src/app/live/hooks/useSovereignAlerts.ts`
- `frontend/src/app/live/lib/liveTransforms.ts`
- `frontend/src/app/live/components/LiveShell.tsx`
- `frontend/src/app/live/components/LiveChartPanel.tsx`
- `frontend/src/app/live/components/LiveAnalyticsPanel.tsx`
- `frontend/src/app/live/components/LiveStatusPanel.tsx`
- `frontend/src/app/live/components/SovereignAlertsPanel.tsx`

The final filenames may adjust during implementation, but the boundary split should remain capability-based.

## 9. Testing strategy

Keep the current route coverage in `frontend/src/app/live/page.test.tsx` and add direct seam tests instead of replacing route tests early.

Minimum new test anchors:

- `useLiveRuntime.test.tsx`
  ticker bootstrap, fetch success/failure, abort cleanup, refresh sequencing
- `useLiveAnalytics.test.tsx`
  analytics refresh/status polling, empty-data fallback, radar shaping
- `useLiveControls.test.tsx`
  start/stop success/failure, live-status refresh, action loading state
- `useSovereignAlerts.test.tsx`
  websocket message parsing, buffer limit, cleanup/close behavior
- selected component tests for:
  - `LiveShell`
  - `LiveStatusPanel`
  - `SovereignAlertsPanel`

Verification gate for the checkpoint should be:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

## 10. Safety rules

Phase 6 should preserve these behaviors throughout extraction:

- no backend API contract changes
- no websocket payload contract changes
- no unjustified change to ticker or analytics polling semantics
- no change to live feed start/stop user-facing semantics
- existing route-level live tests stay green during all extraction slices

## 11. Exit condition

This design is successful when all of the following are true:

- `frontend/src/app/live/page.tsx` is no longer the primary home for fetch/poll/websocket/control orchestration
- runtime, analytics, controls, and websocket seams exist and are directly tested
- chart/panel rendering is moved behind focused presentational components
- the full frontend baseline and browser baseline remain green
- a Phase 6 checkpoint summary can point to a materially thinner live route and explicit runtime seams

## 12. Recommended next step

Write the Phase 6 implementation plan next. The highest-value first implementation slice should create `frontend/src/app/live/hooks/useLiveRuntime.ts`, move ticker bootstrap and intraday fetch sequencing out of `frontend/src/app/live/page.tsx`, and add the first direct runtime seam tests before touching analytics polling or websocket behavior.
