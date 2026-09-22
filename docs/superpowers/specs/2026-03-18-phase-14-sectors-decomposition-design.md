# Horus Analytics II Phase 14 Sectors Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/sectors/page.tsx`
- `frontend/src/app/sectors/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 14 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Goal

This design defines the next frontend runtime decomposition wave for `frontend/src/app/sectors/page.tsx`.

The objective is to turn the route into a thin composition shell while preserving:

- the current route path
- the existing `view=sectors|stocks` fetch behavior
- the current `trail=10` query behavior
- the current optional `sector=` filtering behavior in stocks view
- the current loading and empty-state behavior
- the current ranking summary and table semantics
- the current fullscreen expand and ESC-close behavior
- the current SVG RRG chart rendering semantics

The route currently mixes five separate concerns in one file:

1. fetch orchestration and query building
2. view-mode and sector-filter state
3. fullscreen modal lifecycle and ESC handling
4. pure ranking and quadrant display shaping
5. large SVG chart, modal, and rankings-table render blocks

Phase 14 should separate those concerns into explicit seams without changing what the page does.

## 2. Why This Route Is Next

`frontend/src/app/sectors/page.tsx` is now the highest-value untreated frontend runtime route after the completed portfolio, settings, live, simulation, optimization, Telegram, Oracle, Audit, Status, and Analytics decompositions.

It is the right next boundary because:

- it is still a medium-large route at about 367 lines
- it mixes runtime fetch/query behavior with fullscreen interaction behavior
- it embeds a large custom SVG chart implementation in the route file
- it contains both rankings derivation and a large rankings-table render block
- it already has route-level test anchors that make extraction safer

The file currently combines:

- fetch URL construction
- loading and error behavior
- `viewMode` and `selectedSector` state
- fullscreen open/close state
- ESC-key listener lifecycle
- status color shaping
- rankings sorting
- large RRG SVG chart rendering
- fullscreen modal rendering
- rankings summary and table rendering

That makes the route harder to change safely because one edit can affect data semantics, keyboard behavior, and display logic at once.

## 3. Scope

Primary source file:

- `frontend/src/app/sectors/page.tsx`

Primary extraction target areas:

- `frontend/src/app/sectors/hooks/`
- `frontend/src/app/sectors/components/`
- `frontend/src/app/sectors/lib/`

In scope:

- fetch orchestration and query construction
- `viewMode` state
- sector-filter state
- loading and error handling
- sorted rankings and quadrant counts
- fullscreen state and ESC handling
- shell extraction
- RRG chart extraction
- fullscreen modal extraction
- rankings-table extraction

Out of scope:

- visual redesign of the sectors route
- backend endpoint changes
- API contract changes for `/api/v1/rrg`
- replacing the existing SVG chart with a charting library
- changing visible wording except where required for structural extraction

## 4. Target Boundary

After decomposition, `frontend/src/app/sectors/page.tsx` should keep only:

- top-level composition
- lightweight wiring between extracted hooks and components

Everything else should move behind explicit seams.

### Route responsibilities that should leave the page

- fetch URL and query construction
- loading and error behavior
- view-mode and sector-filter state
- sorted rankings and quadrant counts
- fullscreen open/close state
- ESC-key listener lifecycle
- status color shaping
- large SVG chart render block
- fullscreen modal render block
- rankings summary and table render block

### Route responsibilities that may remain

- top-level section ordering
- composition of extracted components
- small glue code if needed for composition

## 5. Recommended Approach

Three approaches were considered:

### Option 1. Full capability split in one phase

Move runtime and fullscreen behavior behind separate hooks and extract the shell, chart panel, fullscreen modal, rankings table, and SVG chart into focused components.

Pros:

- strongest structural result
- handles both runtime behaviors in one checkpoint
- matches the successful Phase 4 through Phase 13 frontend decomposition pattern

Cons:

- larger first diff than a read-only extraction

### Option 2. Data/runtime split first, fullscreen later

Extract fetch, view switching, and rankings behavior first and leave fullscreen interaction behavior in the route.

Pros:

- lower first diff

Cons:

- leaves one of the route’s main interaction seams in the page
- weakens the checkpoint value

### Option 3. Chart and table component extraction only

Extract JSX and the SVG chart into components but leave all fetch, filter, and fullscreen behavior in the route.

Pros:

- makes the file look smaller quickly

Cons:

- weak boundary
- poor long-term testability
- keeps the route responsible for the real behavior

### Recommended option

Option 1.

This route is not just a chart page. It is a runtime and interaction surface with fullscreen lifecycle behavior plus view-specific fetch behavior. The route should only be considered decomposed if both of those behaviors leave the page with the large render blocks.

## 6. Target Module Map

### `frontend/src/app/sectors/page.tsx`

Owns:

- top-level composition
- wiring extracted hooks to extracted components

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
- safe label/value helpers if kept independent from React state

### `frontend/src/app/sectors/components/SectorShell.tsx`

Owns:

- page frame
- title
- mode toggle
- sector picker
- refresh button

### `frontend/src/app/sectors/components/SectorRrgPanel.tsx`

Owns:

- embedded chart card
- expand affordance

### `frontend/src/app/sectors/components/SectorFullscreenModal.tsx`

Owns:

- fullscreen wrapper
- fullscreen header chrome
- close affordance

### `frontend/src/app/sectors/components/SectorRankingsTable.tsx`

Owns:

- ranking summary strip
- rankings table rendering

### `frontend/src/app/sectors/components/RRGChart.tsx`

Owns:

- current SVG chart rendering

The chart implementation should stay presentational. It should not own fetch, fullscreen, or route state.

## 7. Data Flow

The intended runtime flow is:

1. `page.tsx` reads sectors runtime state through `useSectorRuntime`
2. `useSectorRuntime` exposes loaded rows, counts, and display-ready sorted ranking rows
3. `page.tsx` reads fullscreen behavior through `useSectorFullscreen`
4. `page.tsx` passes display-ready props into `SectorShell`, `SectorRrgPanel`, `SectorFullscreenModal`, and `SectorRankingsTable`
5. `SectorRrgPanel` and `SectorFullscreenModal` render `RRGChart` without owning async behavior

This keeps behavior in hooks, pure shaping in `sectorTransforms`, and rendering in components.

## 8. Error Handling And Contract Preservation

The decomposition must preserve the current visible behavior for:

- initial loading state
- fetch failures that currently log without crashing the route
- sectors and stocks view switching
- sector-filter fetch behavior
- rankings count updates
- fullscreen open/close behavior
- ESC-to-close behavior
- empty-result rendering

Key rule:

- no backend API contract changes
- no changes to `/api/v1/rrg` query semantics
- no changes to visible route outcomes beyond structural extraction

## 9. Testing Strategy

Existing route protection to keep green:

- `frontend/src/app/sectors/page.test.tsx`

New direct seam tests:

- `frontend/src/app/sectors/hooks/useSectorRuntime.test.tsx`
  - sectors fetch success
  - stocks-view fetch
  - sector-filter fetch
  - empty data
  - error path
- `frontend/src/app/sectors/hooks/useSectorFullscreen.test.tsx`
  - open and close behavior
  - ESC-key cleanup
- `frontend/src/app/sectors/components/SectorShell.test.tsx`
- `frontend/src/app/sectors/components/SectorRrgPanel.test.tsx`
- `frontend/src/app/sectors/components/SectorFullscreenModal.test.tsx`
- `frontend/src/app/sectors/components/SectorRankingsTable.test.tsx`

Release gate for the Phase 14 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

## 10. Execution Sequencing

Recommended implementation order:

1. extract `sectorTransforms.ts`
2. extract `useSectorRuntime.ts`
3. extract `useSectorFullscreen.ts`
4. extract `RRGChart.tsx`
5. extract `SectorShell.tsx`
6. extract `SectorRrgPanel.tsx`
7. extract `SectorFullscreenModal.tsx`
8. extract `SectorRankingsTable.tsx`
9. slim `page.tsx` to composition only
10. run broader frontend verification and write checkpoint docs

This ordering stabilizes pure helpers and runtime/fullscreen contracts before moving the chart and table UI blocks.

## 11. Exit Criteria

Phase 14 should be considered complete when:

- `frontend/src/app/sectors/page.tsx` is primarily composition and lightweight wiring
- fetch, view-switching, and rankings behavior live in `useSectorRuntime`
- fullscreen behavior and ESC handling live in `useSectorFullscreen`
- the SVG chart, shell, fullscreen modal, and rankings table live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and core components
- the frontend verification gate passes

## 12. Risks And Mitigations

### Risk: view-specific query semantics drift during extraction

Mitigation:

- lock sectors and stocks fetch behavior with direct runtime tests
- keep the existing route tests green while extraction proceeds

### Risk: fullscreen ESC handling breaks subtly

Mitigation:

- isolate fullscreen lifecycle in `useSectorFullscreen`
- test open, close, and cleanup behavior directly

### Risk: over-engineering a medium route

Mitigation:

- keep only the minimum seam set
- retain the existing SVG chart implementation
- do not introduce extra abstraction beyond runtime, fullscreen, transforms, shell, chart panel, modal, and rankings table
