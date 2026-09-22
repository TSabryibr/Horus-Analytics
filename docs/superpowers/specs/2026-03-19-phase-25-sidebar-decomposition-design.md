# Phase 25: Sidebar Decomposition Design

**Date:** 2026-03-19
**Target:** `frontend/src/app/components/Sidebar.tsx`
**Status:** Design Drafted

## 1. Problem Statement

The `Sidebar` component is approximately 468 lines of dense implementation. It serves as the primary navigation and global status indicator for the application. As it stands, it mixes:
1. Static configuration data (e.g., `routes`, `providerLabels`).
2. Inline pure date/time formatting functions (`formatClockHHMM`, `formatStatusTimestamp`).
3. Complex runtime state management (Language, Portfolios, Polling for data sync status, hydration tracking, localStorage caching).
4. Verbose structural JSX for five distinct interactive zones (Header, Portfolio Switcher, Nav List, Data Status Card, Footer Controls).

To improve maintainability and adherence to the Reliability-First Program, this component must be decomposed into a modular composition shell.

## 2. Target Architecture

The sidebar will be refactored into a standardized pattern (Config + Lib + Hooks + UI):

### A. Configuration & Transforms
- `config/navigation.ts`: Exports the static `routes` array (icons and paths).
- `lib/sidebarTransforms.ts`: Extracts the pure `formatStatusTimestamp` and `formatClockHHMM` helper functions.

### B. Runtime Hook (hooks/useSidebarRuntime.ts)
- **Input:** None (reads from global contexts and browser storage).
- **Behavior:** 
  - Tracks `isCollapsed` state with `localStorage` persistence.
  - Hydration management.
  - Calculates `systemStatus` (using existing `resolveRuntimeSurfaceState`) and `lastSyncDisplay` strings based on `useDataSyncStatus` and active polling.
- **Output:** Returns a consolidated state object (e.g., `isCollapsed`, `toggleSidebar`, `pathname`, `systemStatusData`, `portfolioData`, and `footerActions`).

### C. Presentational Components (components/sidebar/)
- `SidebarShell.tsx`: The animated backdrop container (`w-64` vs `w-20`).
- `SidebarHeader.tsx`: Renders the Horus logo and the collapse toggle button.
- `SidebarPortfolioSwitcher.tsx`: Renders the "ACTIVE_MATRIX" portfolio dropdown.
- `SidebarNavMenu.tsx`: Iterates over the `routes` config and highlights the active route.
- `SidebarDataStatus.tsx`: Renders the blinking indicator and data feed timestamp telemetry.
- `SidebarFooterActions.tsx`: Contains the Translation (Language) and Matrix Travel (Simulation) buttons.

### D. Composition Shell (Sidebar.tsx)
- Thin wrapper orchestrating `useSidebarRuntime` with the sub-components. Expected size < 50 lines.

## 3. Testing Strategy

1. **Retain Sidebar.test.tsx:** Ensure any existing integration tests covering navigation and layout mounting continue to pass under the new structure.
2. **Transform Unit Tests:** Create `sidebarTransforms.test.ts` to test edge cases of `formatStatusTimestamp` (dates, raw strings, NaNs).
3. **Hook Unit Tests:** Mock `localStorage`, `usePathname`, and the global data contexts to verify state toggling in `useSidebarRuntime.test.tsx`.
4. **UI Component Unit Tests:** Create basic `.test.tsx` files for `SidebarDataStatus` (status colors mapping) and `SidebarPortfolioSwitcher` (dropdown renders based on user-owned portfolios).

## 4. Rollback Plan
Given its global reach, an issue in the Sidebar could break navigation across the entire app. `npm test` provides the primary defense. In case of production anomaly, the branch can be cleanly reverted.
