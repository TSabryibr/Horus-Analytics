# Horus Analytics II Phase 7 Simulation Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/simulation/page.tsx`
- `frontend/src/app/simulation/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 7 candidate
Status: Approved design
Owner model: Single owner

## 1. Goal

This design defines the next frontend runtime decomposition wave for `frontend/src/app/simulation/page.tsx`.

The objective is to turn the route into a thin composition shell while preserving:

- the current route path
- the current three-tab simulation surface
- backend request contracts
- current success, warning, and failure semantics
- current chart and metric presentation semantics

The route currently mixes three separate simulator workflows in one file:

1. crash simulation
2. Ragnarok portfolio ruin simulation
3. strategy Monte Carlo simulation

Phase 7 should separate those workflows into explicit seams without changing what the page does.

## 2. Why This Route Is Next

`frontend/src/app/simulation/page.tsx` is the next logical frontend runtime target after the completed portfolio, settings, and live decompositions.

It is a good candidate because:

- it is still a large mixed-responsibility route
- it owns three independent async workflows in one component
- it already contains repeated UI patterns that should become reusable seams
- it has existing route-level test anchors that make structural extraction safer

The file currently combines:

- tab state
- simulator-specific request state
- direct fetch calls for three endpoints
- repeated chart shaping
- repeated metric-card and result-panel rendering
- reusable-looking UI primitives defined inline at the bottom of the file

That makes the file harder to reason about, harder to test by capability, and harder to extend safely.

## 3. Scope

Primary source file:

- `frontend/src/app/simulation/page.tsx`

Primary extraction target areas:

- `frontend/src/app/simulation/hooks/`
- `frontend/src/app/simulation/components/`
- `frontend/src/app/simulation/lib/`

In scope:

- all three simulation tabs in one decomposition wave
- per-tab async state and request orchestration
- shared page shell and tab navigation
- shared presentational primitives already implied by the route
- chart-path shaping helpers that are currently duplicated in concept

Out of scope:

- visual redesign of the simulation route
- backend endpoint changes
- changes to the payload schema of `/api/v1/stress-test`
- changes to the payload schema of `/api/v1/ragnarok`
- changes to the payload schema of `/api/v1/montecarlo`
- changes to the business interpretation of returned simulation results

## 4. Target Boundary

After decomposition, `frontend/src/app/simulation/page.tsx` should keep only:

- active tab selection
- top-level composition
- lightweight wiring between extracted hooks and presentational panels

Everything else should move behind explicit seams.

### Route responsibilities that should leave the page

- crash simulation input and request state
- Ragnarok input parsing and request state
- strategy Monte Carlo input and request state
- shared chart-path formatting
- large tab-specific result layouts
- inline reusable display primitives

### Route responsibilities that may remain

- the selected tab
- final panel ordering
- small amounts of glue code if needed for composition

## 5. Recommended Approach

Three approaches were considered:

### Option 1. Full three-tab capability split in one phase

Move all three workflows behind separate hooks and extract tab-specific panels plus shared UI primitives.

Pros:

- strongest structural result
- matches the successful portfolio, settings, and live decomposition pattern
- avoids leaving one or two tabs tangled in the route after the first slice

Cons:

- larger initial diff
- requires more careful sequencing

### Option 2. Shared primitives first, workflow extraction later

Extract cards, controls, and chart wrappers first, then move async behavior later.

Pros:

- lower short-term risk
- visually shrinks the route quickly

Cons:

- keeps the hardest runtime logic tangled
- gives weaker architectural value

### Option 3. One big page hook

Move all state and effects into one `useSimulationPage` hook.

Pros:

- fast apparent shrink

Cons:

- simply relocates the tangle
- weak boundaries
- poor long-term testability

### Recommended option

Option 1.

The simulation page already contains three distinct workflow domains. The correct boundary is one hook per workflow plus one shared shell and shared presentational primitives.

## 6. Target Module Map

### `frontend/src/app/simulation/page.tsx`

Owns:

- active tab state
- top-level composition
- wiring extracted hooks to extracted panels

### `frontend/src/app/simulation/hooks/useCrashSimulation.ts`

Owns:

- selected index
- reference date
- initial capital
- loading state
- result state
- request execution for `/api/v1/stress-test`
- crash-simulation error handling

### `frontend/src/app/simulation/hooks/useRagnarokSimulation.ts`

Owns:

- iterations and days
- ticker-input parsing
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
- warning and error handling
- request execution for `/api/v1/montecarlo`
- chart-path shaping for Monte Carlo paths

### `frontend/src/app/simulation/lib/simulationTransforms.ts`

Owns:

- shared path-to-chart formatting
- small numeric or display transforms that are pure and reusable

### `frontend/src/app/simulation/components/SimulationShell.tsx`

Owns:

- page frame
- route header
- tab navigation

### `frontend/src/app/simulation/components/SimulationControls.tsx`

Owns:

- shared control-bar layout and action button chrome

### `frontend/src/app/simulation/components/SimulationMetricBox.tsx`

Owns:

- shared metric-card presentation

### `frontend/src/app/simulation/components/SimulationGlassCard.tsx`

Owns:

- shared result-card framing

### `frontend/src/app/simulation/components/SimulationErrorDisplay.tsx`

Owns:

- error display for tab-specific failures

### `frontend/src/app/simulation/components/SimulationDistributionRow.tsx`

Owns:

- reusable probability row rendering

### `frontend/src/app/simulation/components/CrashSimulationPanel.tsx`

Owns:

- crash tab rendering only

### `frontend/src/app/simulation/components/RagnarokSimulationPanel.tsx`

Owns:

- Ragnarok tab rendering only

### `frontend/src/app/simulation/components/StrategyMonteCarloPanel.tsx`

Owns:

- strategy Monte Carlo tab rendering only

## 7. Data and Control Flow

The target runtime shape is:

1. `page.tsx` owns tab selection.
2. Each simulator hook owns its own request state and result state.
3. The route passes hook state into the matching tab panel.
4. Shared presentation primitives are composed inside tab panels, not in the route.
5. Shared chart formatting lives in `simulationTransforms.ts`, not duplicated across hooks.

That makes each simulator independently understandable and directly testable.

## 8. Error Handling and Contract Preservation

The decomposition must preserve the current behavior:

- crash simulator silently logs fetch failure today; that behavior can remain unless explicitly tightened in a later phase
- Ragnarok keeps explicit backend-error and network-failure banner behavior
- strategy Monte Carlo keeps warning/error mapping behavior
- no endpoint payload changes

This phase is structural, not behavioral.

If any behavior is tightened while extracting, it must be justified, directly tested, and called out as a separate change. The default is preservation.

## 9. Testing Strategy

Existing route protection that must remain green:

- `frontend/src/app/simulation/page.test.tsx`

Minimum direct seam coverage to add:

- `frontend/src/app/simulation/hooks/useCrashSimulation.test.tsx`
- `frontend/src/app/simulation/hooks/useRagnarokSimulation.test.tsx`
- `frontend/src/app/simulation/hooks/useStrategyMonteCarlo.test.tsx`
- selected component tests for:
  - `SimulationShell`
  - `CrashSimulationPanel`
  - `RagnarokSimulationPanel`
  - `StrategyMonteCarloPanel`

Recommended direct test focus:

- request payload correctness
- success mapping
- backend failure mapping
- network failure mapping
- ticker parsing for Ragnarok
- chart-data shaping for Ragnarok and Monte Carlo

## 10. Safety Rules

Phase 7 should follow these guardrails:

1. No backend API contract changes.
2. No tab/route path changes.
3. No changes to simulation semantics unless separately justified.
4. No broad visual redesign.
5. Existing route tests stay green throughout extraction.
6. Shared primitives should be presentational only and must not absorb async business logic.

## 11. Verification Gate

The checkpoint gate for this phase should be:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Focused package work can use narrower test slices during extraction, but the phase closeout should return to the full frontend and browser baseline.

## 12. Exit Criteria

Phase 7 is complete when:

- `frontend/src/app/simulation/page.tsx` is primarily a route shell and composition layer
- crash, Ragnarok, and strategy workflows each have dedicated hooks
- shared chart and display helpers are extracted
- tab-specific result layouts no longer dominate the route
- route tests remain green
- direct hook and component seams exist for the extracted units
- the frontend baseline and browser baseline pass

## 13. Recommended Next Move

Write the Phase 7 implementation plan next.

The first implementation slice should establish the shared shell and the first workflow hook, but the overall plan should still cover all three tabs in one decomposition wave.
