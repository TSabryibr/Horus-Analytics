# Horus Analytics II Phase 4 Frontend Portfolio Decomposition Design

Date: 2026-03-17
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-17-phase-2-portfolio-decomposition-design.md`
- `docs/superpowers/plans/2026-03-17-phase-2-portfolio-decomposition-implementation-plan.md`

Track: Frontend Runtime Stability
Phase: Phase 4 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Why this is the next Phase 4 target

After the Phase 2 backend portfolio split and the Phase 3 runtime-polish closeout, the largest remaining high-risk interactive surface is `frontend/src/app/portfolio/page.tsx`.

Current shape:

- `frontend/src/app/portfolio/page.tsx` is 1,700+ lines
- it owns initial data loading, modal orchestration, mutation flows, reporting controls, CSV import/export, risk-analysis state, portfolio-management state, and numerous form-normalization helpers
- the existing test file `frontend/src/app/portfolio/page.test.tsx` protects only a thin slice of that behavior

This is now the clearest remaining case where frontend complexity is concentrated in one route despite the backend already being decomposed by capability.

## 2. Phase 4 goal

Turn the portfolio page into a thin route shell that composes smaller hooks and UI sections, without changing:

- route path
- backend API contracts
- modal availability
- CSV import/export behavior
- management-report behavior
- active-portfolio context semantics

At the end of this slice, the frontend portfolio surface should follow the same capability boundaries already introduced in `core/portfolio/`.

## 3. In scope

Primary source:

- `frontend/src/app/portfolio/page.tsx`

Primary supporting files:

- `frontend/src/app/portfolio/page.test.tsx`
- `frontend/src/app/portfolio/components/PortfolioReportSection.tsx`
- `frontend/src/app/context/GlobalDataContext.tsx`
- `frontend/src/components/PortfolioTable.tsx`

## 4. Out of scope

This design does not include:

- redesigning the portfolio UI
- changing portfolio backend endpoints
- changing portfolio calculations or risk rules
- replacing the active-portfolio context contract
- moving the whole page to server components

## 5. Current responsibility map

The current page mixes six different responsibility classes:

1. Page-shell rendering and layout composition
2. Portfolio bootstrap fetching and refresh
3. Mutation orchestration for add, update, close, genesis, import, and export
4. Portfolio-management service orchestration and report sending
5. Local modal/form state normalization helpers
6. Presentation blocks for diagnostics, action bars, and modal bodies

This makes the file expensive to change safely because almost any edit crosses data, UI, and mutation concerns at once.

## 6. Recommended decomposition approach

Recommended approach: decompose by capability seam, not by arbitrary line-count split.

### 6.1 Route shell

Keep `frontend/src/app/portfolio/page.tsx` as the route owner, but reduce it to:

- active portfolio resolution through context
- top-level shell composition
- wiring of extracted hooks and section components

### 6.2 Data and runtime hook

Create a focused hook for portfolio runtime state, for example:

- `frontend/src/app/portfolio/hooks/usePortfolioRuntime.ts`

Responsibilities:

- bootstrap fetch for hoard, health, and analysis
- refresh orchestration
- loading state
- shared UI message surface

This hook should not own modal-specific forms or mutation submission details.

### 6.3 Mutation hook

Create a command-style hook, for example:

- `frontend/src/app/portfolio/hooks/usePortfolioActions.ts`

Responsibilities:

- add position
- update position
- close position
- genesis
- import/export triggers

It should expose small action functions and action-loading state, while leaving modal visibility and form rendering to UI components.

### 6.4 Management hook

Create a dedicated management/report seam, for example:

- `frontend/src/app/portfolio/hooks/usePortfolioManagement.ts`

Responsibilities:

- intake row normalization
- management report build/send flow
- report-control state
- send-result state

This separates the management service workflow from the core position-mutation workflow.

### 6.5 UI sections and modal components

Split large render blocks into focused components under:

- `frontend/src/app/portfolio/components/`

Target groups:

- shell/header/actions
- treasury summary and health cards
- add/update/close modals
- genesis modal
- management modal
- diagnostics/analysis modal

The components should be mostly presentational, with handlers passed in from the page shell and hooks.

## 7. Alternatives considered

### Option A. Keep one page file and only extract helpers

Pros:

- smallest diff
- low routing risk

Cons:

- does not materially change the cost of editing the page
- keeps modal, fetch, and mutation coupling in one file

### Option B. Capability-based hook and component split

Pros:

- matches the backend portfolio decomposition
- keeps behavior stable while producing real seams
- easiest to cover with focused frontend tests

Cons:

- moderate number of new files
- requires careful prop and state-shape design

Recommendation:

- choose Option B

### Option C. Full state-machine rewrite

Pros:

- could produce a very explicit UI contract

Cons:

- too much behavior change for the next structural phase
- higher regression risk than the current need justifies

Reject for this phase.

## 8. Target file map

Proposed target shape:

- `frontend/src/app/portfolio/page.tsx`
- `frontend/src/app/portfolio/hooks/usePortfolioRuntime.ts`
- `frontend/src/app/portfolio/hooks/usePortfolioActions.ts`
- `frontend/src/app/portfolio/hooks/usePortfolioManagement.ts`
- `frontend/src/app/portfolio/lib/forms.ts`
- `frontend/src/app/portfolio/components/PortfolioShell.tsx`
- `frontend/src/app/portfolio/components/PortfolioActionBar.tsx`
- `frontend/src/app/portfolio/components/PortfolioGenesisModal.tsx`
- `frontend/src/app/portfolio/components/PortfolioPositionModal.tsx`
- `frontend/src/app/portfolio/components/PortfolioCloseDialog.tsx`
- `frontend/src/app/portfolio/components/PortfolioAnalysisModal.tsx`
- `frontend/src/app/portfolio/components/PortfolioManagementModal.tsx`

The exact filenames can shift during implementation, but the boundary split should remain capability-based.

## 9. Testing strategy

Required test direction:

- keep the current route-level tests in `frontend/src/app/portfolio/page.test.tsx`
- add direct hook and component tests for the new seams
- prefer behavior tests over implementation-detail assertions

Minimum new test anchors:

- runtime hook fetch success and degraded fetch behavior
- action hook error mapping for add/update/close/import
- management hook report/send flows
- modal section behavior for the most important user actions

## 10. Risks and controls

### Risk: prop drilling explosion

Control:

- prefer a small number of coherent hook return objects over dozens of primitive props

### Risk: behavior drift between frontend and already-decomposed backend seams

Control:

- name frontend capabilities to mirror the backend portfolio domains where practical

### Risk: modal regressions under partial state changes

Control:

- extract modal-local state deliberately instead of keeping cross-modal shared form state by accident

## 11. Success criteria

This Phase 4 slice is successful if:

- `frontend/src/app/portfolio/page.tsx` is no longer the primary home for fetch orchestration and modal business logic
- the route remains behavior-compatible with the current API and context surface
- the new hooks/components have direct tests
- the frontend baseline still passes
- Playwright/browser checks remain green

## 12. Recommended next artifact

If this design looks right, the next artifact should be:

- `docs/superpowers/plans/2026-03-17-phase-4-frontend-portfolio-decomposition-implementation-plan.md`

That plan should turn this design into execution packages, verification gates, and a checkpoint definition for the first Phase 4 slice.
