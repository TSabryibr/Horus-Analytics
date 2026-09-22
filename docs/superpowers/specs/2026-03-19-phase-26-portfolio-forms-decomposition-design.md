# Phase 26: Portfolio Form Logic Decomposition Design

**Date:** 2026-03-19
**Target:** `frontend/src/app/portfolio/page.tsx`
**Status:** Design Drafted

## 1. Problem Statement

The `PortfolioPage` component is currently 403 lines long. While it successfully delegates data fetching and management side-effects to custom hooks (`usePortfolioRuntime`, `usePortfolioActions`, `usePortfolioManagement`), it acts as a massive controller holding all local form-state and GUI-bridging logic for:
1.  Add/Update Position Modals (`formData`, `selectedPosition`).
2.  Genesis Modal (`genesisData`, dynamic holding row alterations).
3.  Close Dialog (`closeConfirmOpen`, share percentage calculations, `pendingClosePosition`).
4.  Miscellaneous modal toggles (`isAnalysisModalOpen`, `isManagementModalOpen`).

By extracting this monolithic local controller logic into distinct hook(s), we standardize the composition shell pattern across the entire application and vastly improve unit testability of the form validations and logic.

## 2. Target Architecture

The controller logic in `page.tsx` will be refactored into two logical domains.

### A. Add/Update & Form Logic
- **`hooks/usePortfolioForms.ts`**:
  - Handles the `formData` object (ticker, shares, price, sl, tp, etc.).
  - Handles `selectedPosition` context for updates.
  - Implements `handleAddPosition` and `handleUpdatePosition` bridging functions.

### B. Dialog & Genesis Logic
- **`hooks/usePortfolioDialogs.ts`**:
  - Handles Genesis state (`genesisData`, row alterations).
  - Handles Dialog visibility states (`isGenesisModalOpen`, `isAnalysisModalOpen`, `isManagementModalOpen`).
  - Handles the complex Close Position dialog math (`getMaxSellableShares`, percentage quick-links, `confirmClosePosition`).

### C. Composition Shell (`page.tsx`)
- The page will invoke `usePortfolioForms` and `usePortfolioDialogs` alongside the existing data-hooks, dropping the file size from ~400 lines down to ~120 lines of pure UI composition binding.

## 3. Testing Strategy

1. **`usePortfolioForms.test.tsx`**: Mock `submitAddPosition` and assert that the hook clears the form and triggers modal closure upon success.
2. **`usePortfolioDialogs.test.tsx`**: Unit test the `setQuickCloseShares` percentage function and the Genesis row addition/alteration algorithms.
3. **`page.test.tsx`**: Given `PortfolioPage` is heavily integration-tested (at least 12600 bytes), ensure no existing routing or mock logic breaks down during testing.

## 4. Rollback Plan
If `npm test` fails post-extraction and the complexity of mocking the form interactions exceeds the value of the extraction, Phase 26 can be reverted, leaving the `page.tsx` intact since it handles purely local component memory.
