# Phase 27: Live Dashboard Logic Decomposition - Design Document

## 1. Problem Statement
The `frontend/src/app/live/page.tsx` file is one of the last remaining monolithic components in the NextJS presentation layer. While it correctly delegates to sub-providers (`useLiveRuntime`, `useLiveAnalytics`, `useLiveControls`), it acts as a massive 250-line God-Component tying them together.

It contains:
- Inline mathematical formatting functions (`toNumber`, `truncatePrice`, `formatPrice`).
- Complex `useMemo` blocks extracting cross-hook intersections (e.g., merging `analyticsData` with `highConvictionItems` into a `radarItems` array).
- Mathematical derivatives (e.g., dynamically calculating the `yDomain` of charts and generating real-time `metrics` on candlestick closures).
- Inline sub-renderers (`renderCandleTooltip`).

## 2. Proposed Architecture

### 2.1 Pure Transformation Layer (`lib/liveTransforms.ts`)
Extract all stateless calculation logic:
- `toNumber(value: unknown): number`
- `truncatePrice(value: unknown, decimals?: number): string`
- `formatPrice(value: unknown): string`
- function `calculateRadarTargets(analyticsData, highConvictionItems)`
- function `calculateYDomain(data)`
- function `calculateLiveMetrics(data)`

### 2.2 Orchestration Hook (`hooks/useLiveDashboard.ts`)
Extract the inline bindings managing the cross-talk between the 4 independent data hooks:
- Manages `autoRefreshMs`, `autoRefreshEnabled`, `isMounted`, `showRadar`.
- Injects the `lib/liveTransforms.ts` functions over the raw hook data to yield pre-computed metrics bindings for the UI layer.

### 2.3 UI Sub-Component Extraction
- Extract `renderCandleTooltip` into `components/LiveChartTooltip.tsx` to keep the chart panel clean.

### 2.4 Composition Shell
Update `src/app/live/page.tsx` to strictly consume `useLiveDashboard()`:
```tsx
const dashboard = useLiveDashboard();
return (
    <LiveShell {...dashboard.shellProps}>
       <LiveAnalyticsPanel {...dashboard.analyticsProps} />
       <LiveStatusPanel {...dashboard.statusProps} />
       <LiveChartPanel {...dashboard.chartProps} />
    </LiveShell>
);
```

## 3. Success Criteria
1. `src/app/live/page.tsx` length reduced by at least 50% (< 120 lines).
2. Existing integration tests in `live/page.test.tsx` continue to pass without modification.
3. No inline logic or formatting left in the JSX closure.
