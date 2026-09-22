# Horus Analytics II Phase 19 Whales Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-19-whales-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 19
Status: Complete
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 19 Whales decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/whales/page.tsx` into a thin route shell without changing the route path, the current filter behavior, the current sector-summary aggregation, the current price truncation semantics, the current selected-ticker modal behavior, the ticker-history query behavior, the chart and OBV display semantics, or the current loading and empty-state behavior.

Phase 19 Whales work should leave six things true:

1. The route page is no longer the primary home of filter state and candidate filtering.
2. The route page is no longer the primary home of selected-ticker modal behavior and chart-history wiring.
3. The route page is no longer the primary home of price truncation and sector aggregation helpers.
4. The shell, sector summary, status card, candidate grid, and modal surfaces are extracted into focused components.
5. The extracted seams are directly testable without full route execution.
6. The extraction pattern remains consistent with the Phase 4 through Phase 18 frontend decomposition track.

## 2. In Scope

Primary source file:

- `frontend/src/app/whales/page.tsx`

Primary extraction target areas:

- `frontend/src/app/whales/hooks/`
- `frontend/src/app/whales/lib/`
- `frontend/src/app/whales/components/`

Primary route responsibilities to preserve:

- filter input behavior
- candidate filtering by ticker and sector
- sector-summary aggregation
- selected-ticker modal behavior
- ticker-history chart wiring
- status-card rendering
- candidate-card rendering
- loading and empty-state behavior

Out of scope for this Phase 19 slice:

- visual redesign of the whales route
- backend endpoint changes
- whale payload contract changes
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/whales/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/whales/hooks/useWhalesRuntime.test.tsx`
- `frontend/src/app/whales/hooks/useWhaleChartModal.test.tsx`
- selected component tests for shell, sector summary, status card, candidates grid, and chart modal

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/whales/hooks/useWhalesRuntime.ts`

Owns:

- filter state
- filtered candidates
- sector-summary aggregation
- loading and display derivation
- truncated price formatting access

### `frontend/src/app/whales/hooks/useWhaleChartModal.ts`

Owns:

- selected ticker state
- open and close behavior
- SWR key derivation
- chart-data and OBV shaping

### `frontend/src/app/whales/lib/whaleTransforms.ts`

Owns:

- price truncation
- sector-summary aggregation
- candidate filtering helpers
- chart-series shaping helpers

### `frontend/src/app/whales/components/`

Target components:

- `WhalesShell.tsx`
- `WhaleSectorSummary.tsx`
- `WhaleStatusCard.tsx`
- `WhaleCandidatesGrid.tsx`
- `WhaleChartModal.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Whales decomposition in this order:

1. `F19-P1` Pure transforms and runtime extraction
2. `F19-P2` Modal seam and shell extraction
3. `F19-P3` Sector summary, status card, and candidates grid extraction
4. `F19-P4` Closeout and checkpoint

This order is intentional:

- pure transforms and runtime state move first because they stabilize filtering and aggregation semantics
- the modal seam moves next because selected-ticker and history-fetch behavior are the main interaction seam
- display surfaces move after runtime and modal seams are explicit
- final slimdown happens only after the route is fully covered by seams

## 6. Work Packages

### F19-P1. Pure Transforms and Runtime Extraction

Status: Complete

Purpose:

Establish the pure shaping helpers and isolate filter, candidates, sector-summary, and price-formatting behavior before moving the modal seam or large render blocks.

Target files:

- `frontend/src/app/whales/page.tsx`
- `frontend/src/app/whales/lib/whaleTransforms.ts`
- `frontend/src/app/whales/hooks/useWhalesRuntime.ts`

Tasks:

1. Move price truncation, candidate filtering, and sector aggregation into `whaleTransforms.ts`.
2. Move filter state, filtered candidates, and sector-summary derivation into `useWhalesRuntime`.
3. Keep the route consuming runtime state through the hook instead of inline derivation.
4. Add direct tests for filter-by-ticker, filter-by-sector, sector aggregation, and price truncation.

Deliverables:

- shared whale transforms
- runtime seam for whales route state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/whales/page.test.tsx src/app/whales/hooks/useWhalesRuntime.test.tsx`

Acceptance criteria:

- filter and aggregation behavior are no longer primarily route-local
- pure helpers are no longer defined inline in the route
- current route-level whales tests stay green

### F19-P2. Modal Seam and Shell Extraction

Status: Complete

Purpose:

Separate selected-ticker modal behavior and pull the top-level shell and controls out of the route once runtime state is stable.

Target files:

- `frontend/src/app/whales/page.tsx`
- `frontend/src/app/whales/hooks/useWhaleChartModal.ts`
- `frontend/src/app/whales/components/WhalesShell.tsx`
- `frontend/src/app/whales/components/WhaleChartModal.tsx`

Tasks:

1. Extract selected-ticker state and modal open/close behavior into `useWhaleChartModal`.
2. Extract SWR key derivation, chart-data shaping, and OBV shaping into `useWhaleChartModal`.
3. Extract the page frame, header, filter input, and refresh button into `WhalesShell`.
4. Extract the chart modal structure into `WhaleChartModal`.
5. Add direct tests for modal open/close, SWR key derivation, chart fallback, and shell rendering.

Deliverables:

- dedicated whales modal seam
- extracted shell
- extracted chart modal
- direct modal and shell tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/whales/page.test.tsx src/app/whales/hooks/useWhaleChartModal.test.tsx src/app/whales/components/WhalesShell.test.tsx src/app/whales/components/WhaleChartModal.test.tsx`

Acceptance criteria:

- modal and chart-history behavior are no longer primarily route-local
- top-level shell structure is no longer defined inline in the route
- current route-level whales behavior remains stable

### F19-P3. Sector Summary, Status Card, and Candidates Grid Extraction

Status: Complete

Purpose:

Finish the primary structural decomposition by extracting the visible whales surfaces into focused components.

Target files:

- `frontend/src/app/whales/page.tsx`
- `frontend/src/app/whales/components/WhaleSectorSummary.tsx`
- `frontend/src/app/whales/components/WhaleStatusCard.tsx`
- `frontend/src/app/whales/components/WhaleCandidatesGrid.tsx`

Tasks:

1. Extract sector-summary rendering into `WhaleSectorSummary`.
2. Extract sonar/status rendering into `WhaleStatusCard`.
3. Extract whale-card grid rendering into `WhaleCandidatesGrid`.
4. Add direct tests for the extracted display surfaces.

Deliverables:

- extracted sector summary
- extracted status card
- extracted candidates grid
- direct component coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/whales/page.test.tsx src/app/whales/components/WhaleSectorSummary.test.tsx src/app/whales/components/WhaleStatusCard.test.tsx src/app/whales/components/WhaleCandidatesGrid.test.tsx`

Acceptance criteria:

- the main whales display surfaces are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level whales behavior remains stable

### F19-P4. Closeout and Checkpoint

Status: Complete

Purpose:

Finish seam coverage, run the broader frontend gate, and define the frontend checkpoint for this Phase 19 slice.

Target files:

- `frontend/src/app/whales/page.tsx`
- all new hook/component test files
- Phase 19 checkpoint docs

Tasks:

1. Run the broader frontend verification gate.
2. Write the Phase 19 checkpoint summary.
3. Update the top-level roadmap.
4. Confirm the route remains primarily composition plus lightweight wiring.

Deliverables:

- complete seam-focused test surface
- Phase 19 checkpoint summary
- updated top-level roadmap

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- all whales seam and route tests are green
- frontend baseline and browser baseline are green
- the route is materially thinner and acts as a composition shell

## 7. Verification Matrix

Each package must declare:

1. The smallest fast test slice that proves the extraction did not break the active contract
2. The broader route-level test anchor that remains green
3. The final checkpoint commands required before Phase 19 is closed

### Fast slices by package

`F19-P1`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/whales/page.test.tsx src/app/whales/hooks/useWhalesRuntime.test.tsx`

`F19-P2`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/whales/page.test.tsx src/app/whales/hooks/useWhaleChartModal.test.tsx src/app/whales/components/WhalesShell.test.tsx src/app/whales/components/WhaleChartModal.test.tsx`

`F19-P3`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/whales/page.test.tsx src/app/whales/components/WhaleSectorSummary.test.tsx src/app/whales/components/WhaleStatusCard.test.tsx src/app/whales/components/WhaleCandidatesGrid.test.tsx`

`F19-P4`

- full frontend checkpoint commands

## 8. Risk Notes

### Risk: filter and aggregation behavior drift during extraction

Mitigation:

- keep the route test green
- add direct runtime tests for ticker filtering, sector filtering, sector aggregation, and price truncation

### Risk: modal and chart-history behavior changes subtly

Mitigation:

- isolate selected-ticker and chart-history logic in `useWhaleChartModal`
- test SWR key derivation, modal open/close, and history fallback directly

### Risk: over-engineering a medium whales route

Mitigation:

- keep only the minimum seam set
- retain the current card and modal patterns
- do not introduce extra abstraction beyond runtime, modal, transforms, shell, sector summary, status card, candidates grid, and chart modal

## 9. Checkpoint Definition

Phase 19 should be considered complete when:

- `frontend/src/app/whales/page.tsx` is primarily composition and lightweight wiring
- filter, aggregation, and price formatting live in `useWhalesRuntime` and `whaleTransforms`
- selected-ticker and chart-history behavior live in `useWhaleChartModal`
- shell, sector summary, status card, candidate grid, and modal live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and core components
- the frontend verification gate passes

## 10. Notes For Execution

Keep behavior changes out of this slice. If a bug is found during extraction, fix it only if:

1. it is required to preserve the current visible contract, or
2. it is small enough to lock with a direct regression test in the same package

If broader whales UX or card/modal changes are desired, defer them to a later phase after the structural seam work is complete.

## 11. Recommended Next Move After This Plan

Start `F19-P1` first. The highest-value first edit is to extract `whaleTransforms.ts` and `useWhalesRuntime.ts`, then move filter state, aggregation, and price shaping out of `frontend/src/app/whales/page.tsx` before touching the modal seam or the larger UI blocks.
