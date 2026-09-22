# Horus Analytics II Phase 19 Whales Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/whales/page.tsx`
- `frontend/src/app/whales/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 19
Status: Proposed design
Owner model: Single owner

## 1. Goal

Phase 19 should turn `frontend/src/app/whales/page.tsx` into a thin route shell without changing:

- the route path
- whale filter behavior
- sector-summary aggregation behavior
- current price truncation semantics
- ticker modal open and close behavior
- ticker-history query behavior
- chart and OBV display semantics
- current loading and empty-state behavior

The route currently mixes two distinct responsibilities in one file:

1. read-side candidate filtering, sector aggregation, and display shaping
2. interaction-side modal lifecycle and ticker-history/chart wiring

The decomposition should leave those responsibilities behind explicit seams that are directly testable.

## 2. Scope

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
- price truncation behavior
- selected-ticker modal behavior
- ticker-history chart wiring
- status-card rendering
- candidate-card rendering

Out of scope for this Phase 19 slice:

- visual redesign of the whales route
- backend endpoint changes
- whale payload contract changes
- decomposing unrelated frontend routes

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

## 5. Design Rules

The decomposition should follow four rules:

1. Hooks own async orchestration and mutable route state.
2. Pure filtering, aggregation, and formatting helpers live in transforms.
3. Components stay display-oriented and receive explicit props.
4. `page.tsx` should not keep filter, modal, chart, or large render blocks inline once seams are live.

## 6. Recommended Extraction Sequence

Execute the Whales decomposition in this order:

1. `F19-P1` Pure transforms and runtime extraction
2. `F19-P2` Modal seam and shell extraction
3. `F19-P3` Sector summary, status card, and candidates grid extraction
4. `F19-P4` Closeout and checkpoint

This order is intentional:

- runtime and pure shaping move first because they stabilize filter and aggregation semantics
- the modal seam moves next because selected-ticker and history-fetch behavior are the primary interaction seam
- display surfaces move after runtime and modal seams are explicit
- closeout happens only after the route is structurally reduced to composition plus wiring

## 7. Testing And Safety

Minimum new anchors:

- `frontend/src/app/whales/hooks/useWhalesRuntime.test.tsx`
- `frontend/src/app/whales/hooks/useWhaleChartModal.test.tsx`
- selected component tests for:
  - `WhalesShell`
  - `WhaleSectorSummary`
  - `WhaleStatusCard`
  - `WhaleCandidatesGrid`
  - `WhaleChartModal`

Existing route protection to keep green:

- `frontend/src/app/whales/page.test.tsx`

Release gate for the Phase 19 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Safety rules:

- no backend API contract changes
- no semantic changes to whale filtering or price truncation behavior
- no semantic changes to ticker-history query behavior
- preserve current visible loading, modal, sector-summary, and candidate-card behavior while extracting

## 8. Phase 19 Completion Definition

Phase 19 should be considered complete when:

- `frontend/src/app/whales/page.tsx` is primarily composition and lightweight wiring
- filter, aggregation, and price formatting live behind `useWhalesRuntime` and `whaleTransforms`
- selected-ticker and chart-history behavior live behind `useWhaleChartModal`
- shell, sector summary, status card, candidate grid, and modal live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and primary components
- the frontend verification gate passes

## 9. Recommended Next Move After This Spec

Write the Phase 19 implementation plan next, then start `F19-P1` by extracting `whaleTransforms.ts` and `useWhalesRuntime.ts` before touching the modal seam or the larger UI blocks.
