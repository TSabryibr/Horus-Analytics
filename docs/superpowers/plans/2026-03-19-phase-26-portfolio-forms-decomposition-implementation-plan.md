# Phase 26: Portfolio Form Logic Decomposition Implementation Plan

**Date:** 2026-03-19
**Target:** `frontend/src/app/portfolio/page.tsx`
**Status:** Ready for Execution

## 1. Goal

Reduce the 403-line `PortfolioPage` component into a concise composition layer (under 150 lines) by extracting local controller state for Modals and Forms into two custom hooks: `usePortfolioForms` and `usePortfolioDialogs`.

## 2. Work Packages

### Package 26.1: Dialogs Logic Extraction
- **`hooks/usePortfolioDialogs.ts`**: Extract:
  - `isGenesisModalOpen`, `isAnalysisModalOpen`, `isManagementModalOpen`.
  - `closeConfirmOpen`, `pendingClosePosition`, `pendingCloseShares`, `pendingClosePrice`.
  - `genesisData`, and the array handlers (`addGenesisHoldingRow`, `removeGenesisHoldingRow`, `updateGenesisHoldingRow`, `handleGenesisFieldChange`).
  - Close position logic (`getMaxSellableShares`, `requestClosePosition`, `setQuickCloseShares`, `resetCloseDialog`).
- **Verification**: Write unit tests for `usePortfolioDialogs.test.tsx` checking percentage logic for selling shares and array immutability during genesis row updates.

### Package 26.2: Forms Action Extraction
- **`hooks/usePortfolioForms.ts`**: Extract:
  - `isAddModalOpen`, `isUpdateModalOpen`.
  - `selectedPosition`.
  - `formData` (`ticker`, `shares`, `price`, `sl`, `tp`, `tp2`, `date`).
  - Handlers (`handleFormFieldChange`, form resets).
- **Verification**: Write unit tests for `usePortfolioForms.test.tsx` verifying state initialization.

### Package 26.3: Rewriting PortfolioPage
- **`page.tsx`**: Replace the inline state declarations with the new hooks. Pass the external actions (`submitAddPosition`, `submitClosePosition`, etc.) from `usePortfolioActions` down into the new UI composition blocks.
- **Verification**: 
  - Ensure the form props align correctly across `PortfolioPositionModal` and `PortfolioGenesisModal`.
  - Run the existing `page.test.tsx` (which is a massive 12KB integration suite) to verify no side effects or modal behaviors are regressions. (`npm test -- src/app/portfolio`).

### Package 26.4: Final Global Verification and Checkpointing
- Execute `npm --prefix frontend run test -- --runInBand`. The total passing count must remain 167 suites and 515 tests.
- Produce the final Phase 26 Checkpoint Summary.
