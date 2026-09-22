# Phase 24: Market Context Decomposition Implementation Plan

**Date:** 2026-03-19
**Target:** `frontend/src/app/context/MarketContext.tsx`
**Status:** Ready for Execution

## 1. Goal

Refactor the monolithic `MarketProvider` (~154 lines) into a lean provider shell by extracting its data normalization logic and SWR orchestration into a library and custom hook. Standardize the data path for the 6 core market modules.

## 2. Work Packages

### Package 24.1: Logic Extraction (Library)
- **`lib/marketTransforms.ts`**: Extract `normalizeTrapsPayload` (pure) and `fetchOracleBundle` (async coordinator).
- **Tests**: Create `marketTransforms.test.ts` to verify trap payload normalization (nested vs flat payloads) and Oracle bundle assembly.

### Package 24.2: Runtime Hook Extraction
- **`hooks/useMarketRuntime.ts`**: Implement the data-fetching layer (6 `useSWR` calls) with their respective intervals and mutate callbacks. Consolidate into a single `useMemo` context value.
- **Tests**: Create `useMarketRuntime.test.tsx` mocking `apiFetch` (via global fetch) to verify state updates and refreshing.

### Package 24.3: Refactoring the Provider Shell
- **`MarketContext.tsx`**: Replace the inline implementation with `useMarketRuntime()`.
- **Verification**: Run internal tests for the context provider.

### Package 24.4: Suite-wide Regression Verification
- Run all 163 current frontend suites (`npm test`) to ensure no regressions in Sectors, Whales, Arbitrage, Traps, or Oracle.

## 3. Pre-flight Checklist
- `MarketContext.tsx` uses standard `useSWR` with 30s/300s polling. The new hook will maintain these standard intervals.
- The `normalizeTrapsPayload` function has logic to handle both `{ data: { bull_traps: [] } }` and `{ bull_traps: [] }`. This resilience must be preserved in the lib and tested.
