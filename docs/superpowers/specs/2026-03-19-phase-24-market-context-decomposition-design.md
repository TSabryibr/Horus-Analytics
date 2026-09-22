# Phase 24: Market Context Decomposition Design

**Date:** 2026-03-19
**Target:** `frontend/src/app/context/MarketContext.tsx`
**Status:** Design Approved

## 1. Problem Statement

The `MarketProvider` (~154 lines) is the high-bandwidth data hub for the scanner, arbitrage, and oracle modules. It currently mixes:
1. Complex data normalization per endpoint (e.g., `normalizeTrapsPayload`).
2. Multi-step async orchestration for the "Oracle Bundle" (4 POSTs + 1 GET).
3. 6 parallel SWR polling hooks.
4. Memoization logic for the entire context value.

As a critical dependency tree node, this component needs to be decomposed into testable, pure transforms and a focused implementation hook.

## 2. Target Architecture

The provider will be refactored into:

1. **Pure Transforms:** `lib/marketTransforms.ts`
   - `normalizeTrapsPayload`: Standalone pure function.
   - `fetchOracleBundle`: Extracted async coordinator using `apiFetch`.
   - `extractSyncTimestamp`: (Already exists in `syncTimestamps.ts`, but we'll audit its usage).

2. **Runtime Implementation (Hook):** `hooks/useMarketRuntime.ts`
   - Encapsulates the 6 `useSWR` calls.
   - Calculates the `value` object (with `useMemo`).
   - Exposes `refreshMarket`, `refreshOracleNoCache`, etc.

3. **Provider Shell:** `MarketContext.tsx`
   - Thin wrapper providing the context using `useMarketRuntime`.
   - Consumer hooks (`useMarketData`).

## 3. Structural Boundaries

### A. Context Definition & Consumption
- `MarketContext.tsx` defines the `MarketContextValue` type and the `useMarketData` hook.
- It acts as the "Glue" component.

### B. Logic & Network (useMarketRuntime)
- **Input:** None (internal calls to `useSWR`).
- **Output:** The complete `MarketContextValue` object.
- **Responsibility:** Managing polling intervals, deduplication, and dependency mapping.

### C. Pure Formatting (marketTransforms)
- **Input:** Raw JSON payloads.
- **Output:** Typed domain models (`SectorStat[]`, `Trap[]`, etc.).
- **Responsibility:** Resilient data normalization and status validation.

## 4. Testing Strategy

1. **Hook Unit Tests:** Create `useMarketRuntime.test.tsx` using `swr`'s suggested testing patterns (mocking the `fetcher`).
2. **Transform Unit Tests:** Create `marketTransforms.test.ts` to test trap payload normalization with edge case JSON inputs.
3. **Integration Verification:** Ensure all pages consuming `useMarketData` (Sectors, Whales, Arbitrage, Traps, Oracle) still function correctly using existing regression suites.

## 5. Rollback Plan
Since `MarketContext` is a foundational dependency, we will first verify the refactored code passes all 163 current suites before committing. Rollback involves restoring the single-file provider implementation.
