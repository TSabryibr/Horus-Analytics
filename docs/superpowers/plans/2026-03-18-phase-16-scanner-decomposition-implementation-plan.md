# Horus Analytics II Phase 16 Scanner Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-16-scanner-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 16
Status: Complete
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 16 Scanner decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/scanner/page.tsx` into a thin route shell without changing the route path, the current `/scanner/start` query semantics for `index` and `intraday`, the current `/scanner/status` polling lifecycle, the stale-mode error-title and message behavior, the restored-status hydration behavior, the pulse-card rendering semantics, the idle empty-state behavior, or the current signal table rendering semantics.

Phase 16 Scanner work should leave six things true:

1. The route page is no longer the primary home of restored-status hydration and route-owned result state.
2. The route page is no longer the primary home of scan-trigger and polling behavior.
3. The route page is no longer the primary home of price formatting and display-oriented scanner helpers.
4. The shell, controls, pulse cards, and results table are extracted into focused components.
5. The extracted seams are directly testable without full route execution.
6. The extraction pattern remains consistent with the Phase 4 through Phase 15 frontend decomposition track.

## 2. In Scope

Primary source file:

- `frontend/src/app/scanner/page.tsx`

Primary extraction target areas:

- `frontend/src/app/scanner/hooks/`
- `frontend/src/app/scanner/lib/`
- `frontend/src/app/scanner/components/`

Primary route responsibilities to preserve:

- restored status hydration on mount
- `index` and `isIntraday` state behavior
- start-scan request behavior
- progress, completion, and error transitions during polling
- stale-mode and fallback error behavior
- pulse-card rendering for regime, breadth, and signal count
- idle empty-state behavior
- results-table rendering

Out of scope for this Phase 16 slice:

- visual redesign of the scanner route
- backend endpoint changes
- scanner payload contract changes
- decomposing unrelated frontend routes in the same slice

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
- local `data` state
- `index` and `isIntraday` filter state
- loading, error, error-title, and progress state
- derived visibility flags for pulse cards and idle state

### `frontend/src/app/scanner/hooks/useScannerExecution.ts`

Owns:

- scan trigger behavior
- `/scanner/status` polling transitions
- progress updates while running
- completion state application
- stale-mode and fallback error mapping

### `frontend/src/app/scanner/lib/scannerTransforms.ts`

Owns:

- truncated price formatting
- regime and breadth styling helpers
- small pure signal-row helpers

### `frontend/src/app/scanner/components/`

Target components:

- `ScannerShell.tsx`
- `ScannerControls.tsx`
- `ScannerPulsePanel.tsx`
- `ScannerResultsTable.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Scanner decomposition in this order:

1. `F16-P1` Pure transforms and runtime extraction
2. `F16-P2` Execution seam and shell extraction
3. `F16-P3` Controls, pulse panel, and results table extraction
4. `F16-P4` Closeout and checkpoint

This order is intentional:

- pure transforms and runtime state move first because they stabilize restored-status and route-owned state
- the execution seam moves next because polling and scan start are the main command-side behavior
- the display surfaces move after runtime and execution seams are explicit
- final slimdown happens only after the route is fully covered by seams

## 6. Work Packages

### F16-P1. Pure Transforms and Runtime Extraction

Status: Complete

Purpose:

Establish the pure shaping helpers and isolate restored-status hydration, route-owned result state, and basic UI state before moving the polling seam or large render blocks.

Target files:

- `frontend/src/app/scanner/page.tsx`
- `frontend/src/app/scanner/lib/scannerTransforms.ts`
- `frontend/src/app/scanner/hooks/useScannerRuntime.ts`

Tasks:

1. Move truncated price formatting and other pure scanner helpers into `scannerTransforms.ts`.
2. Move restored-status hydration, `data`, `index`, `isIntraday`, loading, error-title, error, and progress state into `useScannerRuntime`.
3. Keep the route consuming runtime state through the hook instead of inline derivation.
4. Add direct tests for `IDLE`, `RUNNING`, and `COMPLETED` hydration plus filter-state wiring.

Deliverables:

- shared scanner transforms
- runtime seam for scanner route state
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner/page.test.tsx src/app/scanner/hooks/useScannerRuntime.test.tsx`

Acceptance criteria:

- restored-status and route-owned scanner state are no longer primarily route-local
- formatting helpers are no longer defined inline in the route
- current route-level scanner tests stay green

### F16-P2. Execution Seam and Shell Extraction

Status: Complete

Purpose:

Separate scan-trigger and polling behavior and pull the top-level shell and error banner out of the route once runtime state is stable.

Target files:

- `frontend/src/app/scanner/page.tsx`
- `frontend/src/app/scanner/hooks/useScannerExecution.ts`
- `frontend/src/app/scanner/components/ScannerShell.tsx`

Tasks:

1. Extract `/scanner/start` behavior into `useScannerExecution`.
2. Extract `/scanner/status` polling transitions and completion/error handling into `useScannerExecution`.
3. Extract the page frame, header shell, and top-level error-banner slot into `ScannerShell`.
4. Add direct tests for start success/failure, stale-mode mapping, polling completion/error transitions, and shell rendering.

Deliverables:

- dedicated scanner execution seam
- extracted shell
- direct execution and shell tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner/page.test.tsx src/app/scanner/hooks/useScannerExecution.test.tsx src/app/scanner/components/ScannerShell.test.tsx`

Acceptance criteria:

- scan-trigger and polling behavior are no longer primarily route-local
- top-level shell structure is no longer defined inline in the route
- current route-level scanner behavior remains stable

### F16-P3. Controls, Pulse Panel, and Results Table Extraction

Status: Complete

Purpose:

Finish the primary structural decomposition by extracting the visible scanner surfaces into focused components.

Target files:

- `frontend/src/app/scanner/page.tsx`
- `frontend/src/app/scanner/components/ScannerControls.tsx`
- `frontend/src/app/scanner/components/ScannerPulsePanel.tsx`
- `frontend/src/app/scanner/components/ScannerResultsTable.tsx`

Tasks:

1. Extract the index selector, intraday toggle, and initialize button into `ScannerControls`.
2. Extract the market pulse cards into `ScannerPulsePanel`.
3. Extract the idle empty-state branch and results table into `ScannerResultsTable`.
4. Add direct tests for the extracted display surfaces.

Deliverables:

- extracted controls component
- extracted pulse panel
- extracted results table
- direct component coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner/page.test.tsx src/app/scanner/components/ScannerControls.test.tsx src/app/scanner/components/ScannerPulsePanel.test.tsx src/app/scanner/components/ScannerResultsTable.test.tsx`

Acceptance criteria:

- the main scanner display surfaces are no longer primarily route-local
- current visible rendering semantics remain stable
- route-level scanner behavior remains stable

### F16-P4. Closeout and Checkpoint

Status: Complete

Purpose:

Finish seam coverage, run the broader frontend gate, and define the frontend checkpoint for this Phase 16 slice.

Target files:

- `frontend/src/app/scanner/page.tsx`
- all new hook/component test files
- Phase 16 checkpoint docs

Tasks:

1. Run the broader frontend verification gate.
2. Write the Phase 16 checkpoint summary.
3. Update the top-level roadmap.
4. Confirm the route remains primarily composition plus lightweight wiring.

Deliverables:

- complete seam-focused test surface
- Phase 16 checkpoint summary
- updated top-level roadmap

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- all scanner seam and route tests are green
- frontend baseline and browser baseline are green
- the route is materially thinner and acts as a composition shell

## 7. Verification Matrix

Each package must declare:

1. The smallest fast test slice that proves the extraction did not break the active contract
2. The broader route-level test anchor that remains green
3. The final checkpoint commands required before Phase 16 is closed

### Fast slices by package

`F16-P1`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner/page.test.tsx src/app/scanner/hooks/useScannerRuntime.test.tsx`

`F16-P2`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner/page.test.tsx src/app/scanner/hooks/useScannerExecution.test.tsx src/app/scanner/components/ScannerShell.test.tsx`

`F16-P3`

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner/page.test.tsx src/app/scanner/components/ScannerControls.test.tsx src/app/scanner/components/ScannerPulsePanel.test.tsx src/app/scanner/components/ScannerResultsTable.test.tsx`

`F16-P4`

- full frontend checkpoint commands

## 8. Risk Notes

### Risk: restored-status behavior drifts during extraction

Mitigation:

- keep the route test green
- add direct runtime tests for `IDLE`, `RUNNING`, and `COMPLETED` hydration

### Risk: polling and error transitions change subtly

Mitigation:

- isolate polling transitions in `useScannerExecution`
- test stale-mode mapping, completion, and polling failure behavior directly

### Risk: over-engineering a medium scanner route

Mitigation:

- keep only the minimum seam set
- retain the current table and card implementations
- do not introduce extra abstraction beyond runtime, execution, transforms, shell, controls, pulse panel, and results table

## 9. Checkpoint Definition

Phase 16 should be considered complete when:

- `frontend/src/app/scanner/page.tsx` is primarily composition and lightweight wiring
- restored status and route-owned scanner state live in `useScannerRuntime`
- start-scan and polling lifecycle behavior live in `useScannerExecution`
- shell, controls, pulse cards, and results table live in extracted components
- existing route tests remain green
- direct seam tests cover the extracted hooks and core components
- the frontend verification gate passes

## 10. Notes For Execution

Keep behavior changes out of this slice. If a bug is found during extraction, fix it only if:

1. it is required to preserve the current visible contract, or
2. it is small enough to lock with a direct regression test in the same package

If broader scanner UX or table/card changes are desired, defer them to a later phase after the structural seam work is complete.

## 11. Recommended Next Move After This Plan

Phase 16 is closed. The recommended next move is to start the next frontend decomposition design pass for `frontend/src/app/strategy/page.tsx`, which is now the largest untreated route in the frontend surface.
