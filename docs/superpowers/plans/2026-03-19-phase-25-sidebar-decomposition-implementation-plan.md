# Phase 25: Sidebar Decomposition Implementation Plan

**Date:** 2026-03-19
**Target:** `frontend/src/app/components/Sidebar.tsx`
**Status:** Ready for Execution

## 1. Goal

Reduce the 468-line `Sidebar` component into a concise composition shell (under 50 lines) by extracting configuration constants, pure date/time formatting functions, a custom runtime hook, and dedicated sub-components.

## 2. Work Packages

### Package 25.1: Configuration and Pure Logic
- **`config/navigation.ts`**: Extract the `routes` array and `providerLabels` mapping out of the component.
- **`lib/sidebarTransforms.ts`**: Extract and export the `formatClockHHMM` and `formatStatusTimestamp` helper functions.
- **Verification**: Write unit tests for `sidebarTransforms.test.ts` to ensure robust timestamp parsing.

### Package 25.2: Runtime Hook Extraction
- **`hooks/useSidebarRuntime.ts`**: Encapsulate the complex state:
  - Language, dashboard, and portfolio contexts.
  - Data Sync polling (`fetchDataStatus` function mapping to `usePolling`).
  - `isCollapsed` state with `localStorage` binding and manual window events.
  - Hydration flag handling (`useEffect`).
  - The derived `systemStatus` and `lastSyncDisplay` strings.
  - Matrix Simulation start command (`POST /api/v1/simulate/start`).
- **Verification**: Create `useSidebarRuntime.test.tsx` to handle localStorage interaction, default routing, and context mocking.

### Package 25.3: UI Sub-Component Extraction
Extract the visual components from the inline JSX into the following structured views:
- **`SidebarHeader.tsx`**: Renders the toggle button and Horus Logo header.
- **`SidebarPortfolioSwitcher.tsx`**: The active matrix `<select>` logic.
- **`SidebarNavMenu.tsx`**: Maps over `routes` and highlights the active route based on pathname.
- **`SidebarDataStatus.tsx`**: Renders the data telemetry block, timestamps, and pulse dot.
- **`SidebarFooterActions.tsx`**: Renders the Language and Simulator controls.

### Package 25.4: Composition and Final Verification
- **`Sidebar.tsx`**: Rewrite as a thin wrapper that invokes `useSidebarRuntime()` and arranges the sub-components within the main shell.
- **Verification**: 
  - Ensure the layout remains visually identical.
  - Run the existing frontend suites (`npm test`). Given the Sidebar's global reach, 100% regression stability is paramount. The suite count (at least 166 suites, 503+ tests) should pass.
  - Create the Phase 25 checkpoint summary.

## 3. Pre-flight Checklist
- `formatStatusTimestamp` contains edge case logic for `T` versus space separation and NaN checks. The transform logic must remain identical.
- The `onClick` handler for Matrix Simulation performs a `window.location.reload()`. This side-effect must remain intact when extracting to `SidebarFooterActions` or the runtime hook.
