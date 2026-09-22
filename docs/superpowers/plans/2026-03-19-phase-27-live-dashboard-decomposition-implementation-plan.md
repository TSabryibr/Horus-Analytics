# Phase 27: Live Dashboard Logic Decomposition - Implementation Plan

## Work Packages

### Package 27.1: UI Sub-Component Extraction
1. **Target**: `frontend/src/app/live/components/LiveChartTooltip.tsx`
2. **Action**: Create a new component file for the chart tooltip. Extract the inline `renderCandleTooltip` function from `live/page.tsx` into an exported functional React component.
3. **Verification**: Write unit tests comparing the rendered tooltip values (`Open`, `High`, `Low`, `Close`, `Volume`) with standard formatting.

### Package 27.2: Logic Transformation Binding (`liveTransforms.ts`)
1. **Target**: `frontend/src/app/live/lib/liveTransforms.ts`
2. **Action**: Extract the pure functional math derivations from the page header spanning variables like `radarItems`, `metrics` objects, and `yDomain` constraints.
3. **Verification**: Write `liveTransforms.test.ts` verifying parsing fallbacks, correct rounding parameters for price decimals, percentage change math for candlesticks, and max-min Y-domain padding logic.

### Package 27.3: Runtime Dashboard Extraction (`useLiveDashboard.ts`)
1. **Target**: `frontend/src/app/live/hooks/useLiveDashboard.ts`
2. **Action**: Combine the 4 primary live subsystem hooks (`useLiveRuntime`, `useLiveAnalytics`, `useLiveControls`, `useSovereignAlerts`) alongside the local React auto-refresh polling state into a unified Context Orchestrator. The orchestrator must return strongly-typed structural props ready to map 1:1 on the `LiveShell` sub-trees.
3. **Verification**: Inject standard mock arrays and verify state bindings output the correct radar structures natively.

### Package 27.4: Page Refactoring (Composition Shell)
1. **Target**: `frontend/src/app/live/page.tsx`
2. **Action**: Delete 100% of the inline hook orchestration, functional state, and mapping logic. Use a single instantiation of `useLiveDashboard()` to pass configuration directly to Sub-Components.
3. **Verification**: Re-run the existing `page.test.tsx` integration tests against the composed boundary.
