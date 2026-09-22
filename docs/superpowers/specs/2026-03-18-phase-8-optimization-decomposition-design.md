# Horus Analytics II Phase 8 Optimization Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/optimization/page.tsx`
- `frontend/src/app/optimization/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 8 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Goal

This design defines the next frontend runtime decomposition wave for `frontend/src/app/optimization/page.tsx`.

The objective is to turn the route into a thin composition shell while preserving:

- the current route path
- the current `SIMULATOR` and `OPTIMIZER` mode switch
- backend request contracts
- optimizer polling/start behavior
- simulator validation and apply-settings behavior
- AI audit drawer and commit semantics
- current chart and KPI presentation semantics

The route currently mixes four separate workflow domains in one file:

1. optimizer status polling and start control
2. simulator parameter editing, validation, and backtest execution
3. apply-settings confirmation flow
4. AI audit execution and commit flow

Phase 8 should separate those workflows into explicit seams without changing what the page does.

## 2. Why This Route Is Next

`frontend/src/app/optimization/page.tsx` is the strongest remaining frontend runtime target after the completed portfolio, settings, live, and simulation decompositions.

It is the right next boundary because:

- it is currently the largest untreated frontend route at about 676 lines
- it owns both read-side polling and command-side action flows
- it mixes two primary modes (`SIMULATOR` and `OPTIMIZER`) in one component
- it coordinates modal/drawer flows in addition to normal route rendering
- it already has route-level test anchors that make structural extraction safer

The file currently combines:

- mode state
- UI message state
- optimizer status and polling enable logic
- simulator parameter state and validation
- optimizer start request
- backtest request
- apply-config confirmation and commit flow
- AI audit request and audit-commit flow
- large mode-specific render blocks

That makes the route harder to change safely because one edit can affect polling, destructive confirmation, audit flows, and major UI rendering at once.

## 3. Scope

Primary source file:

- `frontend/src/app/optimization/page.tsx`

Primary extraction target areas:

- `frontend/src/app/optimization/hooks/`
- `frontend/src/app/optimization/components/`
- `frontend/src/app/optimization/lib/`

In scope:

- both optimization modes in one decomposition wave
- optimizer polling/start orchestration
- simulator parameter editing and validation
- backtest execution and result state
- apply-settings confirmation wiring
- AI audit open/run/commit flow
- shared route shell and section/panel extraction

Out of scope:

- visual redesign of the optimization route
- backend endpoint changes
- changing `/api/v1/strategy/status`, `/api/v1/strategy/start`, `/api/v1/strategy/backtest`, `/api/v1/strategy/apply`, `/api/v1/ai/audit`, or `/api/v1/strategy/propose-from-lab`
- changing optimizer or backtest business rules
- changing `ConfirmDialog` or `StrategyAuditDrawer` contracts unless strictly required for seam extraction

## 4. Target Boundary

After decomposition, `frontend/src/app/optimization/page.tsx` should keep only:

- active mode selection
- top-level composition
- lightweight wiring between extracted hooks and presentational panels

Everything else should move behind explicit seams.

### Route responsibilities that should leave the page

- optimizer polling enable/state logic
- optimizer start action and status mapping
- simulator parameter updates and validation
- simulator run/apply flows
- AI audit run/open/commit flow
- large mode-specific layout blocks

### Route responsibilities that may remain

- active mode
- final panel ordering
- small amounts of glue code if needed for composition

## 5. Recommended Approach

Three approaches were considered:

### Option 1. Full capability split in one phase

Move optimizer, simulator, and audit/apply behavior behind separate hooks and extract major render sections into focused components.

Pros:

- strongest structural result
- matches the successful portfolio, settings, live, and simulation decomposition pattern
- avoids leaving polling or destructive flows tangled in the route

Cons:

- larger initial diff
- requires careful sequencing around shared messages and modal/drawer state

### Option 2. Simulator-first only, optimizer later

Extract the simulator/backtest side first and leave optimizer polling and AI audit in the route.

Pros:

- lower short-term diff
- simpler first extraction

Cons:

- leaves the highest-risk command/polling flow in the route
- weakens the value of the checkpoint

### Option 3. One big page hook

Move all state and effects into one `useOptimizationPage` hook.

Pros:

- fast apparent shrink

Cons:

- simply relocates the tangle
- weak boundaries
- poor long-term testability

### Recommended option

Option 1.

The optimization page already contains multiple independent workflow domains. The correct boundary is one hook per capability plus a shared shell and focused panels.

## 6. Target Module Map

### `frontend/src/app/optimization/page.tsx`

Owns:

- active mode state
- top-level composition
- wiring extracted hooks to extracted panels and existing modal/drawer components

### `frontend/src/app/optimization/hooks/useOptimizationRuntime.ts`

Owns:

- top-level UI message state
- mode-independent shared helpers
- any route-wide computed flags that are not specific to one workflow

### `frontend/src/app/optimization/hooks/useOptimizerControl.ts`

Owns:

- optimizer status
- optimizer index selection
- polling enable logic
- start action for `/api/v1/strategy/start`
- loading/status mapping for optimizer mode

### `frontend/src/app/optimization/hooks/useBacktestLab.ts`

Owns:

- simulator parameter state
- validation rules
- backtest execution for `/api/v1/strategy/backtest`
- result state
- apply-settings prompt/confirm state
- apply-settings request for `/api/v1/strategy/apply`

### `frontend/src/app/optimization/hooks/useOptimizationAudit.ts`

Owns:

- AI audit loading
- audit result state
- drawer open state
- audit execution for `/api/v1/ai/audit`
- proposal commit flow for `/api/v1/strategy/propose-from-lab`

### `frontend/src/app/optimization/lib/optimizationTransforms.ts`

Owns:

- pure display helpers for optimization/backtest metrics
- chart-data formatting helpers if the route currently shapes chart props inline
- small parameter-group metadata if it reduces duplication cleanly

### `frontend/src/app/optimization/components/OptimizationShell.tsx`

Owns:

- page frame
- header
- mode switcher
- route-level message banner

### `frontend/src/app/optimization/components/BacktestLabPanel.tsx`

Owns:

- simulator controls layout
- parameter editor rendering
- run-backtest trigger

### `frontend/src/app/optimization/components/OptimizationResultsPanel.tsx`

Owns:

- KPI cards
- chart area
- assumptions display
- apply-config trigger
- audit trigger placement

### `frontend/src/app/optimization/components/OptimizerControlPanel.tsx`

Owns:

- optimizer mode controls
- index selector
- status presentation
- execute-optimization trigger
- optimizer result list rendering

The final filenames may adjust during implementation, but the boundary split should remain capability-based.

## 7. Testing Strategy

Keep the current route coverage in `frontend/src/app/optimization/page.test.tsx` and add direct seam tests instead of replacing route tests early.

Minimum new test anchors:

- `useOptimizationRuntime.test.tsx`
  shared message behavior and route-wide state helpers
- `useOptimizerControl.test.tsx`
  polling enable rules, start success/failure, status mapping
- `useBacktestLab.test.tsx`
  validation, backtest request payload, apply-settings confirmation/commit flow
- `useOptimizationAudit.test.tsx`
  audit run success/failure, drawer state, proposal commit mapping
- selected component tests for:
  - `OptimizationShell`
  - `BacktestLabPanel`
  - `OptimizationResultsPanel`
  - `OptimizerControlPanel`

Existing route protection to keep green:

- `frontend/src/app/optimization/page.test.tsx`

## 8. Safety Rules

Phase 8 should preserve these behavioral rules:

1. No backend contract changes.
2. No change to optimizer polling cadence or enable semantics unless explicitly justified in the implementation plan.
3. No change to simulator validation semantics unless the change is a bugfix and explicitly documented.
4. No change to apply-settings confirmation semantics.
5. No change to AI audit drawer or commit semantics from the user’s perspective.

## 9. Release Gate for the Phase 8 Checkpoint

The Phase 8 checkpoint should require:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

## 10. Recommended Next Move

Write the Phase 8 implementation plan next.

The first implementation slice should extract the shared shell and the optimizer-control seam before touching the simulator or audit flows. That gives a safe first cut around the route’s polling-heavy logic and establishes the composition pattern for the rest of the page.
