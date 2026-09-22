# Horus Analytics II Phase 14 Sectors Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-14-sectors-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 14
Status: Complete
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 14 Sectors decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/sectors/page.tsx` into a thin route shell without changing the route path, the `view=sectors|stocks` query behavior, the `trail=10` fetch behavior, the optional `sector=` filtering behavior, the current loading and empty states, the fullscreen modal behavior, or the current SVG RRG chart rendering semantics.

Phase 14 Sectors work should leave six things true:

1. The route page is no longer the primary home of sectors fetch, view-mode, and sector-filter behavior.
2. The route page is no longer the primary home of fullscreen open/close and ESC lifecycle behavior.
3. The route page is no longer the primary home of rankings sorting, count shaping, and status-color shaping.
4. The shell, embedded chart surface, fullscreen modal, and rankings table are extracted into focused components.
5. The SVG chart is extracted as a presentational unit instead of living inside the route file.
6. The extraction pattern remains consistent with the Phase 4 through Phase 13 frontend decomposition track.

## 2. In Scope

Primary source file:

- `frontend/src/app/sectors/page.tsx`

Primary extraction target areas:

- `frontend/src/app/sectors/hooks/`
- `frontend/src/app/sectors/lib/`
- `frontend/src/app/sectors/components/`

Primary route responsibilities to preserve:

- sectors and stocks fetch behavior
- `trail=10` query behavior
- optional sector-filter query behavior
- loading and empty states
- rankings counts and rankings-table behavior
- embedded chart rendering
- fullscreen expand and close behavior
- ESC-to-close behavior
- current visible status badge behavior

Out of scope for this Phase 14 slice:

- visual redesign of the sectors page
- backend endpoint changes
- `/api/v1/rrg` API contract changes
- replacing the current SVG chart with a charting library
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/sectors/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/sectors/hooks/useSectorRuntime.test.tsx`
- `frontend/src/app/sectors/hooks/useSectorFullscreen.test.tsx`
- selected component tests for shell, chart panel, fullscreen modal, and rankings table

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/sectors/hooks/useSectorRuntime.ts`

Owns:

- fetch orchestration
- `viewMode`
- `selectedSector`
- loading and error state
- `fetchData`
- sorted ranking rows
- quadrant counts

### `frontend/src/app/sectors/hooks/useSectorFullscreen.ts`

Owns:

- fullscreen state
- open and close handlers
- ESC-key listener lifecycle

### `frontend/src/app/sectors/lib/sectorTransforms.ts`

Owns:

- rankings sorting
- quadrant counts
- status color class shaping
- safe label and numeric display shaping

### `frontend/src/app/sectors/components/`

Target components:

- `RRGChart.tsx`
- `SectorShell.tsx`
- `SectorRrgPanel.tsx`
- `SectorFullscreenModal.tsx`
- `SectorRankingsTable.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Sectors decomposition in this order:

1. `F14-P1` Pure transforms and runtime extraction
2. `F14-P2` Fullscreen seam and chart extraction
3. `F14-P3` Shell, chart panel, and rankings table extraction
4. `F14-P4` Route slimdown and checkpoint closeout

This order is intentional:

- pure transforms and runtime state move first because they stabilize fetch and ranking contracts
- fullscreen lifecycle moves next because it is the second runtime seam
- visual surfaces move after the hooks are explicit
- final slimdown happens only after the route is fully covered by seams

## 6. Work Packages

### F14-P1. Pure Transforms and Runtime Extraction

Status: Complete

Purpose:

Establish the pure shaping helpers and isolate sectors fetch/view/filter behavior before moving fullscreen or large render blocks.

Target files:

- `frontend/src/app/sectors/page.tsx`
- `frontend/src/app/sectors/lib/sectorTransforms.ts`
- `frontend/src/app/sectors/hooks/useSectorRuntime.ts`

Tasks:

1. Move rankings sorting, quadrant-count shaping, and status-color helpers into `sectorTransforms.ts`.
2. Move fetch orchestration, loading state, `viewMode`, `selectedSector`, and `fetchData` into `useSectorRuntime`.
3. Move sorted ranking rows and quadrant counts into `useSectorRuntime`.
4. Add direct tests for sectors fetch, stocks fetch, sector-filter query behavior, empty data, and error handling.

Deliverables:

- shared sectors transforms
- runtime seam for display-ready sectors state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/sectors/page.test.tsx src/app/sectors/hooks/useSectorRuntime.test.tsx`

Acceptance criteria:

- fetch/view/filter behavior is no longer primarily route-local
- pure helper logic is no longer defined inline in the route
- current route-level sectors tests stay green

### F14-P2. Fullscreen Seam and Chart Extraction

Status: Complete

Purpose:

Separate fullscreen lifecycle behavior and pull the SVG chart out of the route once runtime state is stable.

Target files:

- `frontend/src/app/sectors/page.tsx`
- `frontend/src/app/sectors/hooks/useSectorFullscreen.ts`
- `frontend/src/app/sectors/components/RRGChart.tsx`
- `frontend/src/app/sectors/components/SectorFullscreenModal.tsx`

Tasks:

1. Extract fullscreen state, open/close handlers, and ESC-key lifecycle into `useSectorFullscreen`.
2. Extract the current SVG chart implementation into `RRGChart.tsx` without changing its display semantics.
3. Extract the fullscreen modal wrapper and close affordance into `SectorFullscreenModal`.
4. Add direct tests for fullscreen open/close, ESC cleanup, and modal rendering.

Deliverables:

- dedicated fullscreen seam
- extracted presentational SVG chart
- extracted fullscreen modal
- direct fullscreen seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/sectors/page.test.tsx src/app/sectors/hooks/useSectorFullscreen.test.tsx src/app/sectors/components/SectorFullscreenModal.test.tsx`

Acceptance criteria:

- fullscreen behavior is no longer primarily route-local
- chart rendering is no longer defined inline in the route
- current route-level sectors behavior remains stable

### F14-P3. Shell, Chart Panel, and Rankings Table Extraction

Status: Complete

Purpose:

Finish the structural decomposition by extracting the shell controls, embedded chart surface, and rankings surface into focused components.

Target files:

- `frontend/src/app/sectors/page.tsx`
- `frontend/src/app/sectors/components/SectorShell.tsx`
- `frontend/src/app/sectors/components/SectorRrgPanel.tsx`
- `frontend/src/app/sectors/components/SectorRankingsTable.tsx`

Tasks:

1. Extract the page frame, title, mode controls, sector picker, and refresh button into `SectorShell`.
2. Extract the embedded chart card and expand affordance into `SectorRrgPanel`.
3. Extract the rankings summary strip and rankings table into `SectorRankingsTable`.
4. Add direct tests for shell rendering, chart-panel affordance, and rankings-table branches.

Deliverables:

- extracted sectors shell
- extracted chart panel
- extracted rankings table
- direct component coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/sectors/page.test.tsx src/app/sectors/components/SectorShell.test.tsx src/app/sectors/components/SectorRrgPanel.test.tsx src/app/sectors/components/SectorRankingsTable.test.tsx`

Acceptance criteria:

- shell, chart, and rankings surfaces are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level sectors behavior remains stable

### F14-P4. Route Slimdown and Closeout

Status: Complete

Purpose:

Remove remaining route-local residue, finish seam coverage, and define the frontend checkpoint for this Phase 14 slice.

Target files:

- `frontend/src/app/sectors/page.tsx`
- all new hook/component test files
- Phase 14 checkpoint docs

Tasks:

1. Remove remaining route-local helper or state residue once the seams are live.
2. Ensure `page.tsx` is primarily composition plus lightweight wiring.
3. Run the broader frontend verification gate.
4. Write the Phase 14 checkpoint summary and update the top-level roadmap.

Deliverables:

- slimmed sectors route shell
- complete seam-focused test surface
- Phase 14 checkpoint summary
- updated top-level roadmap

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- the route is materially thinner and acts as a composition shell
- all sectors seam and route tests are green
- frontend baseline and browser baseline are green

## 7. Verification Matrix

Each package must declare:

1. The smallest fast test slice that proves the extraction did not break the active contract
2. The broader route-level test anchor that remains green
3. The final checkpoint commands required before Phase 14 is closed

### Fast slices by package

`F14-P1`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/sectors/page.test.tsx src/app/sectors/hooks/useSectorRuntime.test.tsx`

`F14-P2`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/sectors/page.test.tsx src/app/sectors/hooks/useSectorFullscreen.test.tsx src/app/sectors/components/SectorFullscreenModal.test.tsx`

`F14-P3`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/sectors/page.test.tsx src/app/sectors/components/SectorShell.test.tsx src/app/sectors/components/SectorRrgPanel.test.tsx src/app/sectors/components/SectorRankingsTable.test.tsx`

`F14-P4`

- full frontend checkpoint commands

## 8. Risk Notes

### Risk: view-specific query behavior drifts during extraction

Mitigation:

- keep the route test green
- add direct runtime tests for sectors view, stocks view, and sector-filter fetch behavior

### Risk: fullscreen ESC semantics change subtly

Mitigation:

- isolate fullscreen lifecycle in `useSectorFullscreen`
- test open, close, and cleanup behavior directly

### Risk: over-engineering a medium route

Mitigation:

- keep only the minimum seam set
- retain the current SVG chart implementation
- do not introduce extra abstraction beyond runtime, fullscreen, transforms, shell, chart panel, modal, and rankings table

## 9. Checkpoint Definition

Phase 14 should be considered complete when:

- `frontend/src/app/sectors/page.tsx` is primarily composition and lightweight wiring
- fetch, view-switching, and rankings behavior live in `useSectorRuntime`
- fullscreen behavior and ESC handling live in `useSectorFullscreen`
- the SVG chart, shell, fullscreen modal, and rankings table live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and core components
- the frontend verification gate passes

## 10. Notes For Execution

Keep behavior changes out of this slice. If a bug is found during extraction, fix it only if:

1. it is required to preserve the current visible contract, or
2. it is small enough to lock with a direct regression test in the same package

If broader sectors UX or charting changes are desired, defer them to a later phase after the structural seam work is complete.

## 11. Recommended Next Move After This Plan

Phase 14 is complete. The next recommended move is to start the next frontend decomposition target from the roadmap: `frontend/src/app/page.tsx`.
