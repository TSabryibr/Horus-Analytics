# Horus Analytics II Phase 4 Frontend Portfolio Decomposition Implementation Plan

Date: 2026-03-17
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-17-phase-4-frontend-portfolio-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 4 candidate
Status: Completed checkpoint
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 4 frontend portfolio decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/portfolio/page.tsx` into a thin route shell without changing the route path, backend API contracts, modal availability, import/export behavior, or active-portfolio semantics.

Phase 4 frontend portfolio work should leave five things true:

1. The route page is no longer the primary home of fetch orchestration and modal business logic.
2. Portfolio fetch/runtime behavior is directly testable through a dedicated hook seam.
3. Portfolio mutation behavior is directly testable through an action hook seam.
4. Management/reporting behavior is directly testable through a dedicated management hook seam.
5. The extraction pattern is reusable later for other large frontend route surfaces such as `settings`, `live`, and `simulation`.

## 2. In Scope

Primary source file:

- `frontend/src/app/portfolio/page.tsx`

Primary extraction target areas:

- `frontend/src/app/portfolio/hooks/`
- `frontend/src/app/portfolio/lib/`
- `frontend/src/app/portfolio/components/`

Primary route responsibilities to preserve:

- page bootstrap and refresh
- active portfolio binding
- add/update/close position flows
- treasury genesis flow
- CSV import/export
- portfolio analysis modal
- management report build/send flow
- report-section composition

Out of scope for this Phase 4 slice:

- visual redesign of the portfolio page
- backend endpoint changes
- portfolio domain-rule rewrites
- moving the page to server components
- decomposing unrelated large frontend pages in the same package

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/portfolio/page.test.tsx`
- `frontend/src/components/PortfolioTable.test.tsx`
- `frontend/src/app/context/GlobalDataContext.test.tsx`
- `frontend/src/app/components/Sidebar.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/portfolio/hooks/usePortfolioRuntime.test.tsx`
- `frontend/src/app/portfolio/hooks/usePortfolioActions.test.tsx`
- `frontend/src/app/portfolio/hooks/usePortfolioManagement.test.tsx`
- selected component tests for extracted modals and shell blocks

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/portfolio/hooks/usePortfolioRuntime.ts`

Owns:

- hoard, health, and analysis bootstrap fetches
- page refresh orchestration
- route-level loading state
- shared UI message state for fetch/degraded conditions

### `frontend/src/app/portfolio/hooks/usePortfolioActions.ts`

Owns:

- add position
- update position
- close position
- treasury genesis
- CSV import/export trigger helpers
- mutation loading state and error/success mapping

### `frontend/src/app/portfolio/hooks/usePortfolioManagement.ts`

Owns:

- managed-holding row state
- report control state
- management report build/send flow
- send-result state and message mapping

### `frontend/src/app/portfolio/lib/forms.ts`

Owns:

- numeric normalization helpers
- close-dialog value coercion
- row mapping helpers shared across hooks and components

### `frontend/src/app/portfolio/components/`

Target components:

- `PortfolioShell.tsx`
- `PortfolioActionBar.tsx`
- `PortfolioGenesisModal.tsx`
- `PortfolioPositionModal.tsx`
- `PortfolioCloseDialog.tsx`
- `PortfolioAnalysisModal.tsx`
- `PortfolioManagementModal.tsx`

The route page should remain the route owner and composition point. These extracted units should not import the route file.

## 5. Package Sequence

Execute the frontend decomposition in this order:

1. `F4-P1` Runtime hook and page-shell extraction
2. `F4-P2` Action hook and mutation modal extraction
3. `F4-P3` Management/reporting hook extraction
4. `F4-P4` Final route slimdown, test expansion, and checkpoint closeout

This order is intentional:

- the runtime seam removes the broadest state coupling first
- the mutation seam is high-churn and already has strong behavior anchors
- management/reporting is the most cross-cutting and should move after the shared fetch and action seams are stable
- the final route slimdown should happen only after the hooks and UI sections are proven

## 6. Work Packages

### F4-P1. Runtime Hook and Page-Shell Extraction

Purpose:

Establish one reusable frontend seam for page bootstrap, refresh, and core runtime state before moving mutation logic.

Target files:

- `frontend/src/app/portfolio/page.tsx`
- `frontend/src/app/portfolio/hooks/usePortfolioRuntime.ts`
- `frontend/src/app/portfolio/components/PortfolioShell.tsx`

Tasks:

1. Move hoard, health, and analysis bootstrap fetches into `usePortfolioRuntime`.
2. Move page-level refresh orchestration and shared UI message state into the same hook.
3. Extract the non-modal shell and toolbar composition into `PortfolioShell`.
4. Keep the route page as the owner of active-portfolio binding and hook wiring.
5. Add direct tests for successful bootstrap and degraded/non-active portfolio behavior.

Deliverables:

- first reusable portfolio runtime hook
- thinner route shell
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/portfolio/page.test.tsx src/app/portfolio/hooks/usePortfolioRuntime.test.tsx`

Acceptance criteria:

- bootstrap fetch logic no longer lives inline in the route page
- current page-level route tests stay green
- runtime seam is directly testable without rendering the full page

### F4-P2. Action Hook and Mutation Modal Extraction

Purpose:

Move mutation orchestration behind a command-style frontend seam while preserving the current modal and API behavior.

Target files:

- `frontend/src/app/portfolio/page.tsx`
- `frontend/src/app/portfolio/hooks/usePortfolioActions.ts`
- `frontend/src/app/portfolio/components/PortfolioPositionModal.tsx`
- `frontend/src/app/portfolio/components/PortfolioCloseDialog.tsx`
- `frontend/src/app/portfolio/components/PortfolioGenesisModal.tsx`
- `frontend/src/app/portfolio/lib/forms.ts`

Tasks:

1. Move add/update/close/genesis/import/export behavior into `usePortfolioActions`.
2. Extract modal-local rendering and input state into dedicated components where practical.
3. Keep the current WFA-block, partial-close, and import/export behavior unchanged.
4. Add direct action-hook tests for success, block, and error mapping cases.

Deliverables:

- mutation-oriented hook seam
- extracted modal components
- direct action-hook regression coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/portfolio/page.test.tsx src/app/portfolio/hooks/usePortfolioActions.test.tsx`

Acceptance criteria:

- mutation submission logic is no longer primarily route-local
- route-level add/close/import behavior remains unchanged
- new hook tests cover the main user-facing failure paths

### F4-P3. Management and Reporting Hook Extraction

Purpose:

Isolate the portfolio-management workflow from the rest of the page so report-building and Telegram sending do not remain entangled with position mutation and bootstrap state.

Target files:

- `frontend/src/app/portfolio/page.tsx`
- `frontend/src/app/portfolio/hooks/usePortfolioManagement.ts`
- `frontend/src/app/portfolio/components/PortfolioManagementModal.tsx`
- `frontend/src/app/portfolio/components/PortfolioAnalysisModal.tsx`

Tasks:

1. Move managed-holding row state and report-control state into `usePortfolioManagement`.
2. Move report build/send orchestration into the same hook.
3. Extract management and analysis modal rendering into focused components.
4. Add direct tests for report build/send flows and error mapping.

Deliverables:

- dedicated management/reporting seam
- extracted reporting modals
- direct management hook coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/portfolio/page.test.tsx src/app/portfolio/hooks/usePortfolioManagement.test.tsx`

Acceptance criteria:

- management/reporting flow is no longer primarily route-local
- current reporting behavior remains stable
- the reporting seam has direct tests

### F4-P4. Route Slimdown and Closeout

Purpose:

Remove the remaining route-local business blocks, finish seam coverage, and define the frontend checkpoint for this Phase 4 slice.

Target files:

- `frontend/src/app/portfolio/page.tsx`
- all new hook/component test files
- Phase 4 checkpoint docs

Tasks:

1. Remove dead or duplicated helper bodies from the route once the extracted seams are live.
2. Keep only route ownership, composition wiring, and compatibility wrappers where tests still depend on named seams.
3. Run the full frontend baseline and affected backend/browser checks.
4. Write the Phase 4 checkpoint summary and update the roadmap status.

Deliverables:

- materially thinner portfolio route page
- expanded direct seam coverage
- Phase 4 checkpoint artifacts

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- `frontend/src/app/portfolio/page.tsx` is primarily a route shell and composition layer
- frontend baseline remains green
- the portfolio page has direct hook/component seam tests alongside route anchors

## 7. Verification Matrix

Each package must declare:

1. protected behavior
2. direct seam tests added or updated
3. route-level tests kept green
4. release gates impacted
5. rollback path

Minimum required verification for this Phase 4 slice:

- route-level portfolio Jest tests
- direct hook tests for runtime, actions, and management
- frontend lint and strict production build
- Playwright browser baseline

## 8. Risks and Controls

### Risk: state fragmentation across too many hooks

Control:

- keep each hook capability-bounded and return one coherent contract object instead of many independent values

### Risk: prop drilling from page shell into every modal

Control:

- extract UI sections around workflow boundaries, not around arbitrary small pieces of markup

### Risk: behavior drift in modal actions during extraction

Control:

- preserve the existing route-level tests and add direct hook tests before removing route-local logic

## 9. Suggested Execution Cadence

For a single owner, the expected order is:

1. `F4-P1`
2. `F4-P2`
3. `F4-P3`
4. `F4-P4`

Do not start the next package until the current package’s targeted tests are green.

## 10. Exit Checklist for the Phase 4 Portfolio Slice

This slice is complete when all of the following are true:

- `frontend/src/app/portfolio/page.tsx` is no longer the primary home for bootstrap and mutation orchestration
- runtime, action, and management seams exist and are directly tested
- the route shell still preserves the current active-portfolio UX and API behavior
- full frontend baseline and browser baseline are green
- a Phase 4 checkpoint summary is written and linked from the top-level roadmap

## 11. Checkpoint Result

This plan is now executed through the Phase 4 frontend portfolio checkpoint.

Checkpoint artifact:

- `docs/superpowers/reference/2026-03-18-phase-4-frontend-portfolio-checkpoint-summary.md`

Completed outcomes:

- `F4-P1` runtime hook and shell extraction
- `F4-P2` action hook and mutation modal extraction
- `F4-P3` management/reporting hook and modal extraction
- `F4-P4` route slimdown, utility extraction, and frontend verification closeout

The next move is no longer another Phase 4 execution package. The program can advance to the next planning target after a short review of the remaining large frontend route surfaces.
