# Horus Analytics II Phase 8 Optimization Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-8-optimization-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 8
Status: Complete on 2026-03-18
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 8 optimization decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/optimization/page.tsx` into a thin route shell without changing the route path, backend API contracts, mode availability, optimizer semantics, simulator semantics, or current apply/audit behavior.

Phase 8 optimization work should leave six things true:

1. The route page is no longer the primary home of optimizer polling and start orchestration.
2. The route page is no longer the primary home of simulator parameter editing, validation, and backtest execution.
3. Apply-settings confirmation and commit behavior are isolated behind an explicit seam.
4. AI audit execution and proposal-commit behavior are isolated behind an explicit seam.
5. Shared optimization shell, control blocks, and results panels are extracted into focused components.
6. The extraction pattern is reusable for the remaining large frontend runtime routes after `optimization`.

## 2. In Scope

Primary source file:

- `frontend/src/app/optimization/page.tsx`

Primary extraction target areas:

- `frontend/src/app/optimization/hooks/`
- `frontend/src/app/optimization/lib/`
- `frontend/src/app/optimization/components/`

Primary route responsibilities to preserve:

- `SIMULATOR` and `OPTIMIZER` mode switching
- optimizer polling/status presentation and execute flow
- simulator validation, backtest execution, and result rendering
- apply-settings confirmation and commit semantics
- AI audit run/open/commit behavior
- current KPI, chart, and assumptions presentation semantics

Out of scope for this Phase 8 slice:

- visual redesign of the optimization page
- backend endpoint changes
- payload-schema changes for `/api/v1/strategy/status`
- payload-schema changes for `/api/v1/strategy/start`
- payload-schema changes for `/api/v1/strategy/backtest`
- payload-schema changes for `/api/v1/strategy/apply`
- payload-schema changes for `/api/v1/ai/audit`
- payload-schema changes for `/api/v1/strategy/propose-from-lab`
- changes to optimizer or backtest business interpretation
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/optimization/page.test.tsx`
- `frontend/src/app/components/Sidebar.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/optimization/hooks/useOptimizationRuntime.test.tsx`
- `frontend/src/app/optimization/hooks/useOptimizerControl.test.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.test.tsx`
- `frontend/src/app/optimization/hooks/useOptimizationAudit.test.tsx`
- selected component tests for shell, control, lab, and results panels

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/optimization/hooks/useOptimizationRuntime.ts`

Owns:

- route-wide UI message state
- mode-independent shared helpers
- route-level computed flags that are not specific to one capability

### `frontend/src/app/optimization/hooks/useOptimizerControl.ts`

Owns:

- optimizer status
- optimizer index selection
- optimizer loading/status mapping
- polling enable logic
- start action for `/api/v1/strategy/start`

### `frontend/src/app/optimization/hooks/useBacktestLab.ts`

Owns:

- simulator parameter state
- validation rules
- backtest execution for `/api/v1/strategy/backtest`
- result state
- apply-settings prompt and confirm state
- apply-settings request for `/api/v1/strategy/apply`

### `frontend/src/app/optimization/hooks/useOptimizationAudit.ts`

Owns:

- audit loading
- audit result state
- audit drawer open state
- audit execution for `/api/v1/ai/audit`
- commit flow for `/api/v1/strategy/propose-from-lab`

### `frontend/src/app/optimization/lib/optimizationTransforms.ts`

Owns:

- pure display helpers for optimization/backtest metrics
- chart-data formatting helpers
- small parameter/display metadata that reduce duplication cleanly

### `frontend/src/app/optimization/components/`

Target components:

- `OptimizationShell.tsx`
- `OptimizerControlPanel.tsx`
- `BacktestLabPanel.tsx`
- `OptimizationResultsPanel.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the optimization decomposition in this order:

1. `F8-P1` Shared shell and optimizer-control extraction
2. `F8-P2` Backtest lab extraction
3. `F8-P3` Audit/apply extraction and result-panel cleanup
4. `F8-P4` Route slimdown and checkpoint closeout

This order is intentional:

- optimizer control moves first because it contains polling-heavy logic and establishes the shell pattern
- the simulator/backtest lab moves second because it is the largest interactive form surface
- audit/apply moves third because it depends on extracted simulator and results seams
- final slimdown happens only after all major workflows are extracted and directly tested

## 6. Work Packages

### F8-P1. Shared Shell and Optimizer-Control Extraction

Status: Completed on 2026-03-18

Purpose:

Establish the shared route shell and isolate the polling-heavy optimizer workflow before moving the simulator and audit flows.

Target files:

- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/hooks/useOptimizationRuntime.ts`
- `frontend/src/app/optimization/hooks/useOptimizerControl.ts`
- `frontend/src/app/optimization/components/OptimizationShell.tsx`
- `frontend/src/app/optimization/components/OptimizerControlPanel.tsx`

Tasks:

1. Extract the page frame, header, mode switcher, and route-level message banner into `OptimizationShell`.
2. Move route-wide UI message state and shared helpers into `useOptimizationRuntime`.
3. Move optimizer status, index selection, start action, and polling enable logic into `useOptimizerControl`.
4. Extract the optimizer mode UI into `OptimizerControlPanel`.
5. Add direct tests for optimizer polling enable rules, start success/failure, and shell rendering.

Deliverables:

- shared optimization shell
- route-wide runtime seam
- optimizer-control seam
- extracted optimizer mode panel
- direct optimizer seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/optimization/page.test.tsx src/app/optimization/hooks/useOptimizerControl.test.tsx src/app/optimization/components/OptimizationShell.test.tsx`

Acceptance criteria:

- optimizer workflow is no longer primarily route-local
- shared shell is no longer defined inline in the route
- current route-level optimization tests stay green

### F8-P2. Backtest Lab Extraction

Status: Completed on 2026-03-18

Purpose:

Move the simulator parameter/edit/run flow into its own seam once the route shell and optimizer seam are stable.

Target files:

- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/hooks/useBacktestLab.ts`
- `frontend/src/app/optimization/components/BacktestLabPanel.tsx`
- `frontend/src/app/optimization/lib/optimizationTransforms.ts`

Tasks:

1. Move simulator parameter state and validation into `useBacktestLab`.
2. Move backtest execution and result state into `useBacktestLab`.
3. Extract the simulator controls surface into `BacktestLabPanel`.
4. Move pure result/chart helpers into `optimizationTransforms.ts`.
5. Add direct tests for validation, payload mapping, success mapping, and apply-prompt wiring.

Deliverables:

- dedicated backtest-lab seam
- extracted simulator panel
- shared optimization transforms
- direct backtest seam coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/optimization/page.test.tsx src/app/optimization/hooks/useBacktestLab.test.tsx`

Acceptance criteria:

- simulator workflow is no longer primarily route-local
- validation behavior remains unchanged
- route-level optimization behavior remains stable

### F8-P3. Audit, Apply, and Results-Panel Extraction

Status: Completed on 2026-03-18

Purpose:

Separate the audit/apply command flows and finish the major results-side render extraction.

Target files:

- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/hooks/useOptimizationAudit.ts`
- `frontend/src/app/optimization/components/OptimizationResultsPanel.tsx`

Tasks:

1. Move AI audit loading, result, open-state, and commit flow into `useOptimizationAudit`.
2. Move apply-settings confirmation/commit wiring fully behind the extracted seams where appropriate.
3. Extract KPI cards, chart area, assumptions display, and audit/apply triggers into `OptimizationResultsPanel`.
4. Add direct tests for audit success/failure, commit mapping, and selected results-panel rendering.

Deliverables:

- dedicated audit/apply seam
- extracted results panel
- direct audit seam coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/optimization/page.test.tsx src/app/optimization/hooks/useOptimizationAudit.test.tsx`

Acceptance criteria:

- audit/apply flows are no longer primarily route-local
- `ConfirmDialog` and `StrategyAuditDrawer` behavior remain unchanged from the user perspective
- route-level optimization behavior remains stable

### F8-P4. Route Slimdown and Closeout

Status: Completed on 2026-03-18

Purpose:

Remove the remaining route-local helper residue, finish seam coverage, and define the frontend checkpoint for this Phase 8 slice.

Target files:

- `frontend/src/app/optimization/page.tsx`
- all new hook/component test files
- Phase 8 checkpoint docs

Tasks:

1. Remove dead or duplicated helper bodies from the route once extracted seams are live.
2. Keep `page.tsx` focused on mode selection and composition only.
3. Run the full frontend baseline and browser checks.
4. Write the Phase 8 checkpoint summary and update the roadmap status.

Deliverables:

- materially thinner optimization route page
- expanded direct seam coverage
- Phase 8 checkpoint artifacts

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- `frontend/src/app/optimization/page.tsx` is primarily a route shell and composition layer
- optimizer, simulator, and audit/apply workflows are isolated behind explicit seams
- frontend baseline remains green
- the optimization page has direct hook/component seam tests alongside route anchors

## 7. Verification Matrix

Each package must declare:

1. protected behavior
2. direct seam tests added or updated
3. route-level tests kept green
4. release gates impacted
5. rollback path

Minimum required verification for this Phase 8 slice:

- route-level optimization Jest tests
- direct hook tests for runtime, optimizer, backtest, and audit seams
- focused component tests for shell and major panels
- frontend lint and strict production build
- Playwright browser baseline

## 8. Risks and Controls

### Risk: polling and command flows become coupled again through shared helpers

Control:

- keep optimizer control separate from simulator and audit hooks even if they share message state

### Risk: apply-settings and audit flows drift from current modal/drawer behavior

Control:

- preserve current `ConfirmDialog` and `StrategyAuditDrawer` contracts and cover the integration points with route-level tests

### Risk: simulator parameter metadata becomes duplicated across route and panel

Control:

- move stable parameter display metadata into `optimizationTransforms.ts` or the panel file once, not both

## 9. Suggested Execution Cadence

For a single owner, the expected order is:

1. `F8-P1`
2. `F8-P2`
3. `F8-P3`
4. `F8-P4`

Do not start the next package until the current package's targeted tests are green.

## 10. Exit Checklist for the Phase 8 Optimization Slice

This slice is complete when all of the following are true:

- `frontend/src/app/optimization/page.tsx` is no longer the primary home for optimizer, simulator, and audit/apply workflows
- runtime, optimizer, backtest, and audit seams exist and are directly tested
- shared optimization shell and major panels are extracted
- the full frontend baseline and browser baseline are green
- a Phase 8 checkpoint summary is written and linked from the top-level roadmap

Checkpoint artifact:

- `docs/superpowers/reference/2026-03-18-phase-8-optimization-checkpoint-summary.md`

## 11. Recommended Next Move After This Plan

Phase 8 is complete. Choose the next frontend decomposition target from the roadmap and begin with a design/spec pass before implementation.
