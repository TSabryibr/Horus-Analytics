# Phase 23: Traps Decomposition Design

**Date:** 2026-03-19
**Target:** `frontend/src/app/traps/page.tsx`
**Status:** Design Approved

## 1. Problem Statement

The `TrapsPage` component (~109 lines) currently acts as a monolithic file that handles:
1. Fetching trap data from the Global Data Context.
2. Handling null defaults and empty state evaluations ("The Market is Honest Today" banner).
3. Rendering the page shell and header.
4. Rendering distinct lists for Bull Traps (fake breakouts) and Bear Traps (fake breakdowns).

To adhere to the Reliability-First Program's directives, this component must be decomposed. Even though the file is small, standardizing its structure alongside `News`, `Arbitrage`, and `Seasonality` ensures a uniform boundary for testing, maintainability, and future expansion.

## 2. Target Architecture

The page will be refactored into the standard 4-part pattern:

1. **Composition Layer:** `page.tsx` stays as the single routing entry, but becomes a thin shell that only orchestrates sub-components and reads from a custom hook.
2. **Runtime Hooks:** `hooks/useTrapsRuntime.ts` handles context consumption, null safety extraction, and exposes computed "hasTraps" booleans.
3. **Pure Transforms:** `lib/trapsTransforms.ts` isolates any text formatting (e.g., adding positive/negative signs to fakeout depths).
4. **Presentational Components:**
   - `TrapsShell.tsx` for layout, headers, and refresh actions.
   - `TrapsEmptyBanner.tsx` for the "Honest Market" alert.
   - `TrapCategoryList.tsx` for rendering the typed list (Bull vs Bear) of individual trap cards.
   - `TrapCard.tsx` for an individual trap item.

## 3. Structural Boundaries

### A. Context & State (useTrapsRuntime)
- **Input:** Reads from `useTrapsData()` (via `GlobalDataContext`).
- **Output:** `isLoading`, `bullTraps`, `bearTraps`, `hasAnyTraps`, `onRefresh`.
- **Responsibility:** Null coalescing and exposing derived state conditions. Preserves the `useTrapsData` mock path for existing tests.

### B. View Components
- **`TrapsShell`**: Accepts `loading` state, `onRefresh` callback, and children. Renders the top-level page header and background layout.
- **`TrapsEmptyBanner`**: A stateless component displaying the "no traps" graphic.
- **`TrapCategoryList`**: Renders the section header (Bull or Bear) and maps over trap items. Accepts title, icon, color theme, and items.
- **`TrapCard`**: Displays a single trap's ticker, price, fakeout depth, date, and detail text.

## 4. Testing Strategy

1. **Retain Existing Suite:** The current `page.test.tsx` (6 tests spanning rendering, empty states, null safety, and refresh) will act as the macro regression suite.
2. **Hook Unit Tests:** Create `useTrapsRuntime.test.tsx` to verify null handling and derived boolean flags.
3. **Component Unit Tests:** Create `.test.tsx` files for `TrapsShell`, `TrapsEmptyBanner`, `TrapCategoryList`, and `TrapCard`.

## 5. Rollback Plan
Since the component is small and self-contained, rollback is a simple `git revert`. The `page.test.tsx` file acts as our confidence gauge. If the CI loop or verification baseline fails, we reverse the commit.
