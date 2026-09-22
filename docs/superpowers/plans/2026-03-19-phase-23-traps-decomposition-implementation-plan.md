# Phase 23: Traps Decomposition Implementation Plan

**Date:** 2026-03-19
**Target:** `frontend/src/app/traps/page.tsx`
**Status:** Ready for Execution

## 1. Goal

Reduce the ~109-line `TrapsPage` component into a ~40-line composition shell by extracting its logic into a custom hook, pure text transforms, and three focused presentational components (`TrapsShell`, `TrapsEmptyBanner`, and `TrapCategoryList`).

## 2. Work Packages

### Package 23.1: Logic Extraction (Runtime & Transforms)
- **`lib/trapsTransforms.ts`**: Pure functions for formatting fakeout depth percentages and determining the color classes for a given trap type.
- **`hooks/useTrapsRuntime.ts`**: Wrap `useTrapsData` from the global context to ensure `bull_traps` and `bear_traps` fall back to empty arrays safely. Calculate boolean flags (`hasTraps`, `isLoading`).
- **Tests**: Write `trapsTransforms.test.ts` and `useTrapsRuntime.test.tsx` to ensure proper fallback values and formatted output.

### Package 23.2: Component Extraction (Presentational)
- **`components/TrapsShell.tsx`**: The main layout wrapper with background, title block, and the refresh button.
- **`components/TrapsEmptyBanner.tsx`**: The "Honest Market" banner shown when no traps are present.
- **`components/TrapCategoryList.tsx`**: Renders the section header (Bull or Bear with its specific Lucide icon) and maps over the array of traps.
- **Tests**: Create `.test.tsx` files for each component, verifying icon color classes, rendering data, and invoking the refresh callback.

### Package 23.3: Wiring and Composition
- **`page.tsx`**: Convert the monolithic file into a composition shell importing the `useTrapsRuntime` and the UI components. 
- Ensure `page.test.tsx` (the existing integration suite) successfully mounts the refactored tree using the mock `GlobalDataContext` provider.

### Package 23.4: Final Verification and Closeout
- Execute `npm test` to verify all 479+ frontend tests pass.
- Generate checkpoint summary.

## 3. Pre-flight Checklist
- `frontend/src/app/traps/page.test.tsx` has been reviewed and contains 6 critical rendering/state tests that rely on `useTrapsData`. The extraction plan preserves this mock boundary intact.
