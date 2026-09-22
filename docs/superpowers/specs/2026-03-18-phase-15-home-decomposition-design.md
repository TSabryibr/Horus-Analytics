# Horus Analytics II Phase 15 Home Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/page.tsx`
- `frontend/src/app/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 15 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Goal

This design defines the next frontend runtime decomposition wave for `frontend/src/app/page.tsx`.

The objective is to turn the home route into a thin composition shell while preserving:

- the current route path
- the current dashboard refresh-on-portfolio behavior
- the current source badge and loading/empty-state behavior
- the current signal-feed and equity-panel behavior
- the current `Initialize Run` action semantics
- the current 30-day archive grouping and modal behavior
- the current visible error-banner behavior
- the current simulation-clock and market-status behavior

The route currently mixes six separate concerns in one file:

1. dashboard refresh wiring and runtime shaping
2. simulation clock and market-hours derivation
3. action behavior for `Initialize Run`
4. archive fetch enablement and 30-day grouping
5. large header, KPI, chart, and feed render blocks
6. archive modal rendering and close behavior

Phase 15 should separate those concerns into explicit seams without changing what the page does.

## 2. Why This Route Is Next

`frontend/src/app/page.tsx` is now the highest-value untreated frontend runtime route after the completed portfolio, settings, live, simulation, optimization, Telegram, Oracle, Audit, Status, Analytics, and Sectors decompositions.

It is the right next boundary because:

- it is still a large route at about 390 lines
- it mixes shared dashboard runtime behavior with route-specific display shaping
- it contains two meaningful interaction seams: `Initialize Run` and the archive modal workflow
- it embeds a large amount of layout and modal rendering inline
- it already has route-level test anchors that make extraction safer

The file currently combines:

- portfolio-aware dashboard refresh behavior
- loading and source-state shaping
- archive fetch enablement and grouping
- `Initialize Run` request dispatch
- simulation clock and market-hours derivation
- KPI cluster rendering
- equity chart panel rendering
- signal feed rendering
- archive modal rendering

That makes the route harder to change safely because one edit can affect dashboard runtime semantics, action behavior, and modal rendering at once.

## 3. Scope

Primary source file:

- `frontend/src/app/page.tsx`

Primary extraction target areas:

- `frontend/src/app/hooks/`
- `frontend/src/app/components/`
- `frontend/src/app/lib/`

In scope:

- dashboard refresh-on-portfolio behavior
- loading, source, and error shaping
- archive fetch enablement
- 30-day archive grouping
- `Initialize Run` request behavior
- simulation clock and market-status block
- shell extraction
- KPI panel extraction
- equity panel extraction
- signal feed extraction
- archive modal extraction

Out of scope:

- visual redesign of the home route
- backend endpoint changes
- API contract changes for dashboard or control routes
- changing visible wording except where required for structural extraction

## 4. Target Boundary

After decomposition, `frontend/src/app/page.tsx` should keep only:

- top-level composition
- lightweight wiring between extracted hooks and components

Everything else should move behind explicit seams.

### Route responsibilities that should leave the page

- dashboard refresh and runtime shaping
- archive fetch enablement and grouping
- source/loading/error visibility shaping
- `Initialize Run` action behavior
- simulation clock and market-hours derivation
- KPI render block
- equity panel render block
- signal-feed render block
- archive modal render block

### Route responsibilities that may remain

- top-level section ordering
- composition of extracted components
- small glue code if needed for composition

## 5. Recommended Approach

Three approaches were considered:

### Option 1. Full capability split in one phase

Move dashboard runtime and action behavior behind separate hooks and extract the shell, market-status block, KPI panel, equity panel, signal-feed panel, and archive modal into focused components.

Pros:

- strongest structural result
- handles both interaction seams in one checkpoint
- matches the successful Phase 4 through Phase 14 frontend decomposition pattern

Cons:

- larger first diff than a read-only extraction

### Option 2. Read-side split first, actions and modal later

Extract dashboard runtime, simulation clock, and large render blocks first and leave `Initialize Run` and archive-modal behavior in the route.

Pros:

- lower first diff

Cons:

- leaves both meaningful interaction seams in the page
- weakens the checkpoint value

### Option 3. Header and panel component extraction only

Extract JSX into components but leave refresh, archive grouping, and action behavior in the route.

Pros:

- makes the file look smaller quickly

Cons:

- weak boundary
- poor long-term testability
- keeps the route responsible for the real behavior

### Recommended option

Option 1.

This route is not just a dashboard view. It is a runtime and interaction surface with shared dashboard data semantics, a control action, and an archive modal workflow. The route should only be considered decomposed if those behaviors leave the page with the large render blocks.

## 6. Target Module Map

### `frontend/src/app/page.tsx`

Owns:

- top-level composition
- wiring extracted hooks to extracted components

### `frontend/src/app/hooks/useHomeRuntime.ts`

Owns:

- dashboard refresh-on-portfolio behavior
- source/loading/error shaping
- archive fetch enablement
- 30-day archive grouping
- display-ready booleans for metrics, curve, signals, and health

### `frontend/src/app/hooks/useHomeActions.ts`

Owns:

- `Initialize Run` request behavior
- action loading and error mapping
- notify payload shaping

### `frontend/src/app/lib/homeTransforms.ts`

Owns:

- archive grouping
- 30-day date filtering
- source badge styling helpers
- confidence badge shaping helpers

### `frontend/src/app/components/HomeShell.tsx`

Owns:

- page frame
- header shell
- top-level error banner slot

### `frontend/src/app/components/HomeMarketStatus.tsx`

Owns:

- simulation clock
- market-active and standby indicator

### `frontend/src/app/components/HomeMetricsPanel.tsx`

Owns:

- KPI cluster
- metric empty-state branch

### `frontend/src/app/components/HomeEquityPanel.tsx`

Owns:

- equity chart card
- equity empty-state branch

### `frontend/src/app/components/HomeSignalsPanel.tsx`

Owns:

- signal-feed surface
- signal empty-state branch
- archive-open affordance

### `frontend/src/app/components/HomeArchivesModal.tsx`

Owns:

- grouped archive rendering
- modal close affordance
- empty-archive branch

The chart implementation should stay presentational. It should not own refresh or archive behavior.

## 7. Data Flow

The intended runtime flow is:

1. `page.tsx` reads dashboard runtime state through `useHomeRuntime`
2. `useHomeRuntime` exposes display-ready metrics, curve, signals, health flags, and grouped archives
3. `page.tsx` reads action behavior through `useHomeActions`
4. `page.tsx` passes display-ready props into `HomeShell`, `HomeMarketStatus`, `HomeMetricsPanel`, `HomeEquityPanel`, `HomeSignalsPanel`, and `HomeArchivesModal`
5. `HomeSignalsPanel` triggers archive open and `HomeArchivesModal` renders grouped archive data without owning fetch or grouping logic

This keeps behavior in hooks, pure shaping in `homeTransforms`, and rendering in components.

## 8. Error Handling And Contract Preservation

The decomposition must preserve the current visible behavior for:

- initial dashboard refresh
- loading source state
- empty metrics and empty curve behavior
- signal-feed empty state
- archive empty state
- `Initialize Run` request semantics
- visible error-banner rendering
- simulation clock and market-status behavior

Key rule:

- no backend API contract changes
- no changes to dashboard refresh semantics
- no changes to `Initialize Run` payload semantics
- no changes to archive grouping window or visible modal outcomes

## 9. Testing Strategy

Existing route protection to keep green:

- `frontend/src/app/page.test.tsx`

New direct seam tests:

- `frontend/src/app/hooks/useHomeRuntime.test.tsx`
  - refresh-on-portfolio behavior
  - source/loading shaping
  - archive 30-day grouping
  - empty archive fallback
- `frontend/src/app/hooks/useHomeActions.test.tsx`
  - initialize-run success
  - initialize-run failure mapping
- `frontend/src/app/components/HomeShell.test.tsx`
- `frontend/src/app/components/HomeMarketStatus.test.tsx`
- `frontend/src/app/components/HomeMetricsPanel.test.tsx`
- `frontend/src/app/components/HomeEquityPanel.test.tsx`
- `frontend/src/app/components/HomeSignalsPanel.test.tsx`
- `frontend/src/app/components/HomeArchivesModal.test.tsx`

Release gate for the Phase 15 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

## 10. Execution Sequencing

Recommended implementation order:

1. extract `homeTransforms.ts`
2. extract `useHomeRuntime.ts`
3. extract `useHomeActions.ts`
4. extract `HomeShell.tsx`
5. extract `HomeMarketStatus.tsx`
6. extract `HomeMetricsPanel.tsx`
7. extract `HomeEquityPanel.tsx`
8. extract `HomeSignalsPanel.tsx`
9. extract `HomeArchivesModal.tsx`
10. slim `page.tsx` to composition only
11. run broader frontend verification and write checkpoint docs

This ordering stabilizes pure helpers and runtime/action contracts before moving the large header, panel, and modal UI blocks.

## 11. Exit Criteria

Phase 15 should be considered complete when:

- `frontend/src/app/page.tsx` is primarily composition and lightweight wiring
- dashboard runtime behavior and archive grouping live in `useHomeRuntime`
- `Initialize Run` behavior lives in `useHomeActions`
- the shell, market-status block, KPI panel, equity panel, signal-feed panel, and archive modal live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and core components
- the frontend verification gate passes

## 12. Risks And Mitigations

### Risk: refresh-on-portfolio behavior drifts during extraction

Mitigation:

- lock refresh wiring with direct runtime tests
- keep the existing route tests green while extraction proceeds

### Risk: archive grouping semantics change subtly

Mitigation:

- isolate grouping in `homeTransforms`
- test 30-day grouping and empty-state behavior directly

### Risk: over-engineering a large dashboard route

Mitigation:

- keep only the minimum seam set
- retain the existing chart and card implementations
- do not introduce another oversized catch-all dashboard hook beyond runtime, actions, transforms, shell, panels, and modal
