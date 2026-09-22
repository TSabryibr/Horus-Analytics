# Horus Analytics II Phase 16 Scanner Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/scanner/page.tsx`
- `frontend/src/app/scanner/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 16
Status: Proposed design
Owner model: Single owner

## 1. Goal

Phase 16 should turn `frontend/src/app/scanner/page.tsx` into a thin route shell without changing:

- the route path
- `/scanner/start` query semantics for `index` and `intraday`
- `/scanner/status` polling behavior and completion handling
- stale-mode error-title and message behavior
- restored-status hydration behavior on mount
- the current idle-state, pulse-card, and result-table rendering semantics

The route currently mixes two distinct responsibilities in one file:

1. scanner execution and polling lifecycle
2. result-state rendering, filter-state wiring, and table presentation

The decomposition should leave those responsibilities behind explicit seams that are directly testable.

## 2. Scope

Primary source file:

- `frontend/src/app/scanner/page.tsx`

Primary extraction target areas:

- `frontend/src/app/scanner/hooks/`
- `frontend/src/app/scanner/lib/`
- `frontend/src/app/scanner/components/`

Primary route responsibilities to preserve:

- restored status hydration on mount
- index-selector and intraday-toggle behavior
- start-scan request behavior
- polling progress, completion, and error transitions
- stale-mode and fallback error behavior
- pulse-card rendering for regime, breadth, and signal count
- idle empty-state rendering
- signal result-table rendering

Out of scope for this Phase 16 slice:

- visual redesign of the scanner route
- backend endpoint changes
- changes to scanner result payload structure
- unrelated frontend route decomposition

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/scanner/page.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/scanner/hooks/useScannerRuntime.test.tsx`
- `frontend/src/app/scanner/hooks/useScannerExecution.test.tsx`
- selected component tests for shell, controls, pulse panel, and results table

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/scanner/hooks/useScannerRuntime.ts`

Owns:

- restored scanner status hydration on mount
- route-local result state
- `index` and `isIntraday` filter state
- loading, error, error-title, and progress state
- derived visibility flags for pulse cards and idle state

### `frontend/src/app/scanner/hooks/useScannerExecution.ts`

Owns:

- scan trigger behavior
- `/scanner/status` polling transitions
- completion state application
- progress updates while running
- stale-mode and fallback error mapping

### `frontend/src/app/scanner/lib/scannerTransforms.ts`

Owns:

- truncated price formatting
- regime and breadth styling helpers
- small signal-row display helpers that remain pure

### `frontend/src/app/scanner/components/`

Target components:

- `ScannerShell.tsx`
- `ScannerControls.tsx`
- `ScannerPulsePanel.tsx`
- `ScannerResultsTable.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Design Rules

The decomposition should follow four rules:

1. Hooks own async orchestration and state transitions.
2. Pure formatting and style helpers live in transforms.
3. Components stay display-oriented and receive explicit props.
4. `page.tsx` should not keep polling logic, start-scan logic, or large render blocks once seams are live.

This keeps the scanner route consistent with the decomposition pattern already used in the frontend track.

## 6. Recommended Extraction Sequence

Execute the Scanner decomposition in this order:

1. `F16-P1` Pure transforms and runtime extraction
2. `F16-P2` Execution seam and shell extraction
3. `F16-P3` Controls, pulse panel, and results table extraction
4. `F16-P4` Closeout and checkpoint

This order is intentional:

- runtime state moves first because it stabilizes restored-status and route-owned state
- execution and polling move second because they are the highest-risk behavior seam
- display surfaces move after the runtime and execution contracts are explicit
- closeout happens only after the route is structurally reduced to composition plus wiring

## 7. Testing And Safety

Minimum new anchors:

- `frontend/src/app/scanner/hooks/useScannerRuntime.test.tsx`
- `frontend/src/app/scanner/hooks/useScannerExecution.test.tsx`
- selected component tests for:
  - `ScannerShell`
  - `ScannerControls`
  - `ScannerPulsePanel`
  - `ScannerResultsTable`

Existing route protection to keep green:

- `frontend/src/app/scanner/page.test.tsx`

Release gate for the Phase 16 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Safety rules:

- no backend API contract changes
- no semantic changes to `/scanner/start` query behavior
- no semantic changes to `/scanner/status` transition handling
- preserve the current visible loading, stale-mode, idle-state, and result-table behavior while extracting

## 8. Phase 16 Completion Definition

Phase 16 should be considered complete when:

- `frontend/src/app/scanner/page.tsx` is primarily composition and lightweight wiring
- restored status, local result state, and derived visibility live behind `useScannerRuntime`
- start-scan and polling lifecycle behavior live behind `useScannerExecution`
- shell, controls, pulse cards, and results table live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and primary components
- the frontend verification gate passes

## 9. Recommended Next Move After This Spec

Write the Phase 16 implementation plan next, then start `F16-P1` by extracting `scannerTransforms.ts` and `useScannerRuntime.ts` before touching the polling seam or the larger UI blocks.
