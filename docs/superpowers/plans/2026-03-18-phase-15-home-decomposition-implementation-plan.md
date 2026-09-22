# Horus Analytics II Phase 15 Home Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-15-home-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 15
Status: Complete
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 15 Home decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/page.tsx` into a thin route shell without changing the route path, the current dashboard refresh-on-portfolio behavior, the source badge and loading/empty-state behavior, the signal-feed and equity-panel behavior, the `Initialize Run` action semantics, the current 30-day archive grouping window, the archive modal behavior, the visible error-banner behavior, or the simulation-clock and market-status behavior.

Phase 15 Home work should leave six things true:

1. The route page is no longer the primary home of dashboard refresh and runtime shaping behavior.
2. The route page is no longer the primary home of archive fetch enablement and 30-day grouping behavior.
3. The route page is no longer the primary home of `Initialize Run` action behavior.
4. The simulation clock, KPI cluster, equity panel, signal feed, and archive modal are extracted into focused components.
5. Pure archive and badge shaping logic is extracted into shared transforms.
6. The extraction pattern remains consistent with the Phase 4 through Phase 14 frontend decomposition track.

## 2. In Scope

Primary source file:

- `frontend/src/app/page.tsx`

Primary extraction target areas:

- `frontend/src/app/hooks/`
- `frontend/src/app/lib/`
- `frontend/src/app/components/`

Primary route responsibilities to preserve:

- dashboard refresh-on-portfolio behavior
- loading, source, and error-state behavior
- KPI and empty-state behavior
- equity chart and empty-state behavior
- signal-feed and empty-state behavior
- archive-open behavior
- 30-day archive grouping and modal rendering
- `Initialize Run` request semantics
- simulation clock and market-status behavior

Out of scope for this Phase 15 slice:

- visual redesign of the home page
- backend endpoint changes
- dashboard API contract changes
- control API contract changes
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/hooks/useHomeRuntime.test.tsx`
- `frontend/src/app/hooks/useHomeActions.test.tsx`
- selected component tests for shell, market-status, metrics, equity, signals, and archives modal

## 4. Target Module Map

The decomposition should converge on this internal shape:

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

### `frontend/src/app/components/`

Target components:

- `HomeShell.tsx`
- `HomeMarketStatus.tsx`
- `HomeMetricsPanel.tsx`
- `HomeEquityPanel.tsx`
- `HomeSignalsPanel.tsx`
- `HomeArchivesModal.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Home decomposition in this order:

1. `F15-P1` Pure transforms and runtime extraction
2. `F15-P2` Action seam and shell extraction
3. `F15-P3` Market-status, metrics, equity, and signals extraction
4. `F15-P4` Archives modal extraction and route slimdown
5. `F15-P5` Closeout and checkpoint

This order is intentional:

- pure transforms and runtime state move first because they stabilize refresh, source, and archive contracts
- the action seam moves next because it is the main command-side behavior
- the high-traffic display surfaces move after runtime and actions are explicit
- the archive modal moves after the signal-feed seam is isolated
- final slimdown happens only after the route is fully covered by seams

## 6. Work Packages

### F15-P1. Pure Transforms and Runtime Extraction

Status: Complete

Purpose:

Establish the pure shaping helpers and isolate dashboard refresh, source-state shaping, and archive grouping behavior before moving action or large render blocks.

Target files:

- `frontend/src/app/page.tsx`
- `frontend/src/app/lib/homeTransforms.ts`
- `frontend/src/app/hooks/useHomeRuntime.ts`

Tasks:

1. Move archive grouping, 30-day filtering, and source badge helper logic into `homeTransforms.ts`.
2. Move dashboard refresh-on-portfolio, source/loading/error shaping, archive fetch enablement, and display-ready booleans into `useHomeRuntime`.
3. Keep the route consuming runtime state through the hook instead of inline derivation.
4. Add direct tests for refresh-on-portfolio, source/loading shaping, archive grouping, and empty archive behavior.

Deliverables:

- shared home transforms
- runtime seam for display-ready home state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/page.test.tsx src/app/hooks/useHomeRuntime.test.tsx`

Acceptance criteria:

- dashboard runtime behavior is no longer primarily route-local
- archive grouping logic is no longer defined inline in the route
- current route-level home tests stay green

### F15-P2. Action Seam and Shell Extraction

Status: Complete

Purpose:

Separate `Initialize Run` behavior and pull the top-level shell/header and error banner out of the route once runtime state is stable.

Target files:

- `frontend/src/app/page.tsx`
- `frontend/src/app/hooks/useHomeActions.ts`
- `frontend/src/app/components/HomeShell.tsx`

Tasks:

1. Extract `Initialize Run` request behavior into `useHomeActions`.
2. Extract the page frame, header shell, and top-level error banner slot into `HomeShell`.
3. Keep current action semantics and current header ordering intact.
4. Add direct tests for initialize-run success/failure mapping and shell rendering.

Deliverables:

- dedicated home action seam
- extracted shell
- direct action and shell tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/page.test.tsx src/app/hooks/useHomeActions.test.tsx src/app/components/HomeShell.test.tsx`

Acceptance criteria:

- action behavior is no longer primarily route-local
- top-level shell structure is no longer defined inline in the route
- current route-level home behavior remains stable

### F15-P3. Market-Status, Metrics, Equity, and Signals Extraction

Status: Complete

Purpose:

Finish the primary structural decomposition by extracting the visible dashboard surfaces into focused components.

Target files:

- `frontend/src/app/page.tsx`
- `frontend/src/app/components/HomeMarketStatus.tsx`
- `frontend/src/app/components/HomeMetricsPanel.tsx`
- `frontend/src/app/components/HomeEquityPanel.tsx`
- `frontend/src/app/components/HomeSignalsPanel.tsx`

Tasks:

1. Extract simulation clock and market-status behavior into `HomeMarketStatus`.
2. Extract KPI cluster and empty-state branch into `HomeMetricsPanel`.
3. Extract equity chart card and empty-state branch into `HomeEquityPanel`.
4. Extract signal-feed surface, empty-state branch, and archive-open affordance into `HomeSignalsPanel`.
5. Add direct tests for the extracted display surfaces.

Deliverables:

- extracted market-status component
- extracted metrics panel
- extracted equity panel
- extracted signals panel
- direct component coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/page.test.tsx src/app/components/HomeMarketStatus.test.tsx src/app/components/HomeMetricsPanel.test.tsx src/app/components/HomeEquityPanel.test.tsx src/app/components/HomeSignalsPanel.test.tsx`

Acceptance criteria:

- the main dashboard surfaces are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level home behavior remains stable

### F15-P4. Archives Modal Extraction and Route Slimdown

Status: Complete

Purpose:

Finish the structural extraction by moving the archive modal out of the route and reducing `page.tsx` to composition plus lightweight wiring.

Target files:

- `frontend/src/app/page.tsx`
- `frontend/src/app/components/HomeArchivesModal.tsx`

Tasks:

1. Extract the archive modal wrapper, grouped rendering, close affordance, and empty-archive branch into `HomeArchivesModal`.
2. Remove remaining route-local helper or modal residue once the seams are live.
3. Ensure `page.tsx` is primarily composition plus lightweight wiring.
4. Add direct tests for archive modal rendering and empty state.

Deliverables:

- extracted archives modal
- slimmed route shell
- direct modal coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/page.test.tsx src/app/components/HomeArchivesModal.test.tsx`

Acceptance criteria:

- archive modal behavior is no longer primarily route-local
- the route is materially thinner and acts as a composition shell
- route-level home behavior remains stable

### F15-P5. Closeout and Checkpoint

Status: Complete

Purpose:

Finish seam coverage, run the broader frontend gate, and define the frontend checkpoint for this Phase 15 slice.

Target files:

- `frontend/src/app/page.tsx`
- all new hook/component test files
- Phase 15 checkpoint docs

Tasks:

1. Run the broader frontend verification gate.
2. Write the Phase 15 checkpoint summary.
3. Update the top-level roadmap.
4. Confirm the route remains primarily composition plus lightweight wiring.

Deliverables:

- complete seam-focused test surface
- Phase 15 checkpoint summary
- updated top-level roadmap

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- all home seam and route tests are green
- frontend baseline and browser baseline are green
- the route is materially thinner and acts as a composition shell

## 7. Verification Matrix

Each package must declare:

1. The smallest fast test slice that proves the extraction did not break the active contract
2. The broader route-level test anchor that remains green
3. The final checkpoint commands required before Phase 15 is closed

### Fast slices by package

`F15-P1`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/page.test.tsx src/app/hooks/useHomeRuntime.test.tsx`

`F15-P2`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/page.test.tsx src/app/hooks/useHomeActions.test.tsx src/app/components/HomeShell.test.tsx`

`F15-P3`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/page.test.tsx src/app/components/HomeMarketStatus.test.tsx src/app/components/HomeMetricsPanel.test.tsx src/app/components/HomeEquityPanel.test.tsx src/app/components/HomeSignalsPanel.test.tsx`

`F15-P4`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/page.test.tsx src/app/components/HomeArchivesModal.test.tsx`

`F15-P5`

- full frontend checkpoint commands

## 8. Risk Notes

### Risk: refresh-on-portfolio behavior drifts during extraction

Mitigation:

- keep the route test green
- add direct runtime tests for refresh wiring and source/loading behavior

### Risk: archive grouping semantics change subtly

Mitigation:

- isolate grouping in `homeTransforms`
- test 30-day grouping and empty-archive behavior directly

### Risk: over-engineering a large dashboard route

Mitigation:

- keep only the minimum seam set
- retain the current chart and card implementations
- do not introduce extra abstraction beyond runtime, actions, transforms, shell, panels, and modal

## 9. Checkpoint Definition

Phase 15 should be considered complete when:

- `frontend/src/app/page.tsx` is primarily composition and lightweight wiring
- dashboard runtime behavior and archive grouping live in `useHomeRuntime`
- `Initialize Run` behavior lives in `useHomeActions`
- the shell, market-status block, KPI panel, equity panel, signal-feed panel, and archive modal live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and core components
- the frontend verification gate passes

## 10. Notes For Execution

Keep behavior changes out of this slice. If a bug is found during extraction, fix it only if:

1. it is required to preserve the current visible contract, or
2. it is small enough to lock with a direct regression test in the same package

If broader dashboard UX or card/chart changes are desired, defer them to a later phase after the structural seam work is complete.

## 11. Recommended Next Move After This Plan

Phase 15 is closed. The recommended next move is to start the next frontend decomposition design pass for `frontend/src/app/scanner/page.tsx`, which is now the largest untreated route in the frontend surface.
