# Horus Analytics II Phase 7 Simulation Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-7-simulation-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 7
Status: Complete on 2026-03-18
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 7 simulation decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/simulation/page.tsx` into a thin route shell without changing the route path, backend API contracts, tab availability, chart semantics, or current success and error behavior for the three simulator families.

Phase 7 simulation work should leave six things true:

1. The route page is no longer the primary home of crash, Ragnarok, and Monte Carlo request orchestration.
2. Crash simulation behavior is directly testable through a dedicated hook seam.
3. Ragnarok simulation behavior is directly testable through a dedicated hook seam.
4. Strategy Monte Carlo behavior is directly testable through a dedicated hook seam.
5. Shared simulation controls, cards, and chart helpers are isolated behind focused presentational units.
6. The extraction pattern is reusable for the remaining large frontend runtime routes after `simulation`.

## 2. In Scope

Primary source file:

- `frontend/src/app/simulation/page.tsx`

Primary extraction target areas:

- `frontend/src/app/simulation/hooks/`
- `frontend/src/app/simulation/lib/`
- `frontend/src/app/simulation/components/`

Primary route responsibilities to preserve:

- tab selection across `CRASH`, `RAGNAROK`, and `STRATEGY`
- crash simulation request behavior and result rendering
- Ragnarok request behavior, error handling, and chart rendering
- strategy Monte Carlo request behavior, warning handling, and chart rendering
- current shared metric-card, error-display, and glass-card presentation semantics

Out of scope for this Phase 7 slice:

- visual redesign of the simulation page
- backend endpoint changes
- payload-schema changes for `/api/v1/stress-test`
- payload-schema changes for `/api/v1/ragnarok`
- payload-schema changes for `/api/v1/montecarlo`
- changes to business interpretation of simulation results
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/simulation/page.test.tsx`
- `frontend/src/app/components/Sidebar.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/simulation/hooks/useCrashSimulation.test.tsx`
- `frontend/src/app/simulation/hooks/useRagnarokSimulation.test.tsx`
- `frontend/src/app/simulation/hooks/useStrategyMonteCarlo.test.tsx`
- selected component tests for shell, controls, and the three simulation panels

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/simulation/hooks/useCrashSimulation.ts`

Owns:

- selected crash index
- reference date
- initial capital
- loading state
- result state
- request execution for `/api/v1/stress-test`

### `frontend/src/app/simulation/hooks/useRagnarokSimulation.ts`

Owns:

- ticker input and parsed ticker list
- iterations and days
- loading state
- result state
- error state
- request execution for `/api/v1/ragnarok`
- chart-path shaping for returned paths

### `frontend/src/app/simulation/hooks/useStrategyMonteCarlo.ts`

Owns:

- strategy capital
- simulations count
- loading state
- result state
- warning and error state
- request execution for `/api/v1/montecarlo`
- chart-path shaping for returned paths

### `frontend/src/app/simulation/lib/simulationTransforms.ts`

Owns:

- shared path-to-chart formatting
- small numeric or display transforms reused across simulation hooks and panels

### `frontend/src/app/simulation/components/`

Target components:

- `SimulationShell.tsx`
- `SimulationControls.tsx`
- `SimulationMetricBox.tsx`
- `SimulationGlassCard.tsx`
- `SimulationErrorDisplay.tsx`
- `SimulationDistributionRow.tsx`
- `CrashSimulationPanel.tsx`
- `RagnarokSimulationPanel.tsx`
- `StrategyMonteCarloPanel.tsx`

The route page should remain the route owner and composition point. These extracted units should not import the route file.

## 5. Package Sequence

Execute the simulation decomposition in this order:

1. `F7-P1` Shared shell and crash workflow extraction
2. `F7-P2` Ragnarok workflow extraction
3. `F7-P3` Strategy Monte Carlo workflow extraction
4. `F7-P4` Shared primitive cleanup, route slimdown, and checkpoint closeout

This order is intentional:

- the crash workflow is the simplest first seam and proves the pattern while establishing the shared shell and controls
- Ragnarok moves next because it adds the first explicit error flow and chart-path shaping seam
- strategy Monte Carlo moves after the shared chart and metric primitives are already stable
- the final slimdown should happen only after all three simulator workflows are extracted and directly tested

## 6. Work Packages

### F7-P1. Shared Shell and Crash Workflow Extraction

Status: Completed on 2026-03-18

Purpose:

Establish the shared route shell and the first simulator seam before moving the more complex result/error flows.

Target files:

- `frontend/src/app/simulation/page.tsx`
- `frontend/src/app/simulation/hooks/useCrashSimulation.ts`
- `frontend/src/app/simulation/components/SimulationShell.tsx`
- `frontend/src/app/simulation/components/SimulationControls.tsx`
- `frontend/src/app/simulation/components/CrashSimulationPanel.tsx`

Tasks:

1. Extract the page frame and tab navigation into `SimulationShell`.
2. Extract the shared execute bar into `SimulationControls`.
3. Move crash index/date/capital state and `/api/v1/stress-test` execution into `useCrashSimulation`.
4. Extract the crash-tab rendering into `CrashSimulationPanel`.
5. Add direct tests for crash request payloads and crash-panel rendering.

Deliverables:

- shared simulation shell
- first workflow hook seam
- extracted crash panel
- direct crash seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/simulation/page.test.tsx src/app/simulation/hooks/useCrashSimulation.test.tsx`

Acceptance criteria:

- crash workflow is no longer primarily route-local
- shared shell and controls are no longer defined inline in the route
- current route-level simulation tests stay green

### F7-P2. Ragnarok Workflow Extraction

Status: Completed on 2026-03-18

Purpose:

Move the most complex error-driven workflow behind its own seam once the shell and first tab pattern are established.

Target files:

- `frontend/src/app/simulation/page.tsx`
- `frontend/src/app/simulation/hooks/useRagnarokSimulation.ts`
- `frontend/src/app/simulation/components/RagnarokSimulationPanel.tsx`
- `frontend/src/app/simulation/lib/simulationTransforms.ts`

Tasks:

1. Move ticker parsing, iterations/days state, request execution, and error handling into `useRagnarokSimulation`.
2. Move chart-data shaping into `simulationTransforms.ts`.
3. Extract the Ragnarok tab rendering into `RagnarokSimulationPanel`.
4. Add direct tests for ticker parsing, success mapping, backend-failure mapping, and network-failure mapping.

Deliverables:

- dedicated Ragnarok seam
- extracted Ragnarok panel
- shared chart formatting helpers
- direct Ragnarok seam coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/simulation/page.test.tsx src/app/simulation/hooks/useRagnarokSimulation.test.tsx`

Acceptance criteria:

- Ragnarok workflow is no longer primarily route-local
- current error-banner behavior remains unchanged
- route-level simulation behavior remains stable

### F7-P3. Strategy Monte Carlo Workflow Extraction

Status: Completed on 2026-03-18

Purpose:

Move the remaining simulator workflow behind a dedicated seam and finish the per-tab runtime split.

Target files:

- `frontend/src/app/simulation/page.tsx`
- `frontend/src/app/simulation/hooks/useStrategyMonteCarlo.ts`
- `frontend/src/app/simulation/components/StrategyMonteCarloPanel.tsx`
- `frontend/src/app/simulation/components/SimulationMetricBox.tsx`
- `frontend/src/app/simulation/components/SimulationGlassCard.tsx`
- `frontend/src/app/simulation/components/SimulationErrorDisplay.tsx`
- `frontend/src/app/simulation/components/SimulationDistributionRow.tsx`

Tasks:

1. Move capital/sim-count state, request execution, and warning/error handling into `useStrategyMonteCarlo`.
2. Extract the strategy tab rendering into `StrategyMonteCarloPanel`.
3. Move the shared inline helper components into dedicated presentational files.
4. Add direct tests for warning mapping, failure mapping, and selected panel rendering.

Deliverables:

- dedicated Monte Carlo seam
- extracted strategy panel
- extracted shared simulation primitives
- direct Monte Carlo seam coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/simulation/page.test.tsx src/app/simulation/hooks/useStrategyMonteCarlo.test.tsx`

Acceptance criteria:

- Monte Carlo workflow is no longer primarily route-local
- shared simulation primitives no longer live inline in the route
- route-level simulation behavior remains unchanged

### F7-P4. Route Slimdown and Closeout

Status: Completed on 2026-03-18

Purpose:

Remove the remaining route-local helper residue, finish seam coverage, and define the frontend checkpoint for this Phase 7 slice.

Target files:

- `frontend/src/app/simulation/page.tsx`
- all new hook/component test files
- Phase 7 checkpoint docs

Tasks:

1. Remove dead or duplicated helper bodies from the route once extracted seams are live.
2. Keep `page.tsx` focused on tab selection and composition only.
3. Run the full frontend baseline and browser checks.
4. Write the Phase 7 checkpoint summary and update the roadmap status.

Deliverables:

- materially thinner simulation route page
- expanded direct seam coverage
- Phase 7 checkpoint artifacts

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- `frontend/src/app/simulation/page.tsx` is primarily a route shell and composition layer
- crash, Ragnarok, and strategy workflows are isolated behind explicit seams
- frontend baseline remains green
- the simulation page has direct hook/component seam tests alongside route anchors

## 7. Verification Matrix

Each package must declare:

1. protected behavior
2. direct seam tests added or updated
3. route-level tests kept green
4. release gates impacted
5. rollback path

Minimum required verification for this Phase 7 slice:

- route-level simulation Jest tests
- direct hook tests for crash, Ragnarok, and Monte Carlo seams
- focused component tests for shell and tab panels
- frontend lint and strict production build
- Playwright browser baseline

## 8. Risks and Controls

### Risk: shared primitives absorb business logic

Control:

- keep shared simulation components presentational only and leave async behavior in hooks

### Risk: three tabs make the route props noisy

Control:

- extract by workflow boundary and keep each panel contract local to its simulator family

### Risk: chart shaping drifts across Ragnarok and Monte Carlo

Control:

- move chart-path formatting into one shared transform seam before the final slimdown

## 9. Suggested Execution Cadence

For a single owner, the expected order is:

1. `F7-P1`
2. `F7-P2`
3. `F7-P3`
4. `F7-P4`

Do not start the next package until the current package's targeted tests are green.

## 10. Exit Checklist for the Phase 7 Simulation Slice

This slice is complete when all of the following are true:

- `frontend/src/app/simulation/page.tsx` is no longer the primary home for three separate simulation workflows
- crash, Ragnarok, and Monte Carlo seams exist and are directly tested
- shared simulation controls and display primitives are extracted
- the full frontend baseline and browser baseline are green
- a Phase 7 checkpoint summary is written and linked from the top-level roadmap

Checkpoint artifact:

- `docs/superpowers/reference/2026-03-18-phase-7-simulation-checkpoint-summary.md`

## 11. Recommended Next Move After This Plan

Phase 7 is complete. Choose the next frontend decomposition target from the roadmap and begin with a design/spec pass before implementation.
