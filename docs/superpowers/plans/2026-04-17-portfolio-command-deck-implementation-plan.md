# Portfolio Command Deck Implementation Plan

Date: 2026-04-17
Based on:

- `docs/superpowers/specs/2026-04-17-portfolio-command-deck-design.md`
- `routes/portfolio.py`
- `database.py`
- `frontend/src/app/context/PortfolioContext.tsx`
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`
- `frontend/src/app/components/hooks/useSidebarRuntime.ts`
- `frontend/src/app/portfolio/components/PortfolioShell.tsx`
- `frontend/src/app/context/PortfolioContext.test.tsx`
- `tests/test_portfolio_operations.py`
- `tests/test_portfolio_query_service.py`

Track: Portfolio Command Deck
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Implement the approved portfolio command deck as an ordered rollout that:

1. introduces one persisted backend authority for the global default `SYSTEM` portfolio
2. exposes that authority through a stable portfolio API contract
3. updates frontend boot resolution to honor the backend default before legacy name-based fallbacks
4. upgrades the sidebar switcher into a grouped command deck for all portfolio classes
5. verifies startup, reassignment, and fallback behavior with backend and frontend regression coverage

## 2. In Scope

Primary implementation targets:

- persisted backend storage for the global default `SYSTEM` portfolio
- read and write API support for default-portfolio state
- startup resolution changes in `PortfolioContext`
- command-deck UI and interaction changes in the sidebar
- targeted frontend and backend tests for default resolution and constraint enforcement

Primary files expected to move:

- `database.py`
- `routes/portfolio.py`
- `core/portfolio/identity.py`
- `core/portfolio/queries.py`
- `tests/test_portfolio_operations.py`
- `tests/test_portfolio_query_service.py`
- `frontend/src/app/context/PortfolioContext.tsx`
- `frontend/src/app/context/PortfolioContext.test.tsx`
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`
- `frontend/src/app/components/hooks/useSidebarRuntime.ts`
- `frontend/src/app/components/hooks/useSidebarRuntime.test.tsx`
- `frontend/src/app/components/Sidebar.tsx`
- `frontend/src/app/components/sidebar/Sidebar.test.tsx`

Out of scope for this slice:

- portfolio-page-only organizer expansions outside the sidebar flow
- broad redesign of portfolio analytics content on `/portfolio`
- import/export changes
- per-user remembered recent portfolio state
- support for multiple defaults or `USER` default eligibility
- unrelated cleanup in existing portfolio management services

## 3. Execution Rules

These rules apply across the rollout:

1. Land backend authority first; the frontend must not invent default behavior locally.
2. Keep active portfolio and global default as separate concepts in API shape, state management, and UI labels.
3. Enforce the `SYSTEM`-only default rule in both backend validation and frontend disabled states.
4. Preserve current portfolio switching behavior for all dependent pages while changing startup resolution.
5. Prefer extending existing portfolio payloads and context providers over creating parallel portfolio state paths.
6. Keep the command deck readable and industrial; do not regress to a generic consumer dropdown.
7. Cover deletion and missing-default fallback paths explicitly in tests before closing the slice.

## 4. Work Package Sequence

Execute in this order:

1. `PCD-P1` Backend default-authority foundation
2. `PCD-P2` Portfolio API contract and fallback-query updates
3. `PCD-P3` Frontend portfolio-context boot resolution
4. `PCD-P4` Sidebar command deck rollout
5. `PCD-P5` Regression lock and execution checkpoint

This order is intentional:

- the persisted default must exist before the API can expose it
- the API contract must stabilize before the frontend context consumes it
- context boot logic should be correct before the richer sidebar UI is layered on top
- the sidebar command deck depends on both default metadata and active-state separation
- regression coverage should lock the fully integrated result, not partial assumptions

## 5. Work Packages

### PCD-P1. Backend Default-Authority Foundation

Purpose:

Create one persisted backend source of truth for the global default `SYSTEM` portfolio.

Target files:

- `database.py`
- `core/portfolio/identity.py`
- `tests/test_portfolio_operations.py`
- `tests/test_portfolio_query_service.py`

Tasks:

1. Add a lightweight persisted settings seam for `default_system_portfolio_id` using the repository's existing settings/storage patterns.
2. Add helpers that:
   - read the persisted default
   - validate that the referenced portfolio exists
   - validate that the referenced portfolio is `SYSTEM`
   - clear invalid references when the default portfolio is deleted or missing
3. Add a resolver helper for default startup fallback:
   - persisted default `SYSTEM`
   - first available `SYSTEM`
   - existing portfolio resolver as final safety net
4. Update deletion handling so removing the current default clears the persisted setting safely.
5. Add backend tests covering:
   - assigning a valid `SYSTEM` default
   - rejecting a `USER` default
   - clearing a deleted default
   - fallback when no persisted default is valid

Deliverables:

- persisted backend authority for the global default `SYSTEM` portfolio
- helper functions for validation and fallback resolution
- backend regression coverage for default authority rules

Verification:

- `pytest tests/test_portfolio_operations.py -q`
- `pytest tests/test_portfolio_query_service.py -q`

Acceptance criteria:

- one persisted global default can be stored and resolved
- `USER` portfolios cannot become the backend default
- deleting the current default does not leave a stale authoritative reference behind

### PCD-P2. Portfolio API Contract and Fallback-Query Updates

Purpose:

Expose default-portfolio state through stable API contracts that the frontend can consume without name-based guessing.

Target files:

- `routes/portfolio.py`
- `core/portfolio/queries.py`
- `core/portfolio/identity.py`
- `tests/test_portfolio_operations.py`
- `tests/test_portfolio_query_service.py`

Tasks:

1. Extend the portfolio API contract to expose:
   - the persisted default-system portfolio id, or equivalent resolved metadata
   - enough catalog metadata for grouped rendering and active/default separation
2. Add a write path for assigning a new default `SYSTEM` portfolio.
3. Keep the API shape explicit so the frontend does not infer default authority from names like `Horus` or `My Portfolio`.
4. Ensure query helpers that currently resolve a preferred portfolio use the new default-first fallback model where appropriate.
5. Add tests for:
   - reading the new default metadata from the catalog or dedicated endpoint
   - successful reassignment of the default
   - API rejection for non-`SYSTEM` default requests

Deliverables:

- stable read contract for default-system portfolio state
- stable write contract for default assignment
- query-layer alignment with backend default-first behavior

Verification:

- `pytest tests/test_portfolio_operations.py -q`
- `pytest tests/test_portfolio_query_service.py -q`

Acceptance criteria:

- the frontend can fetch authoritative default metadata without portfolio-name heuristics
- setting a new default updates one backend source of truth
- API validation rejects invalid default assignments cleanly

### PCD-P3. Frontend Portfolio-Context Boot Resolution

Purpose:

Update frontend startup behavior so the active portfolio resolves from backend default authority before legacy fallbacks.

Target files:

- `frontend/src/app/context/PortfolioContext.tsx`
- `frontend/src/app/context/PortfolioContext.test.tsx`
- `frontend/src/app/components/hooks/useSidebarRuntime.ts`
- `frontend/src/app/components/hooks/useSidebarRuntime.test.tsx`

Tasks:

1. Update `PortfolioContext` to fetch or receive the persisted default-system portfolio id alongside the portfolio catalog.
2. Replace the current primary startup logic based on preferred names with:
   - persisted default `SYSTEM`
   - first available `SYSTEM`
   - existing fallback resolver only as the last safety net
3. Expose default-system metadata in context so the sidebar can show both active and default state.
4. Preserve manual active switching behavior so downstream pages continue to react to the chosen active portfolio id.
5. Add tests covering:
   - boot into persisted default
   - fallback when persisted default is missing
   - fallback when no `SYSTEM` portfolio exists
   - separation between active id and default id

Deliverables:

- backend-driven startup resolution in portfolio context
- shared frontend state for active and default portfolio metadata
- frontend tests for default-first boot logic

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/context/PortfolioContext.test.tsx src/app/components/hooks/useSidebarRuntime.test.tsx`

Acceptance criteria:

- frontend boot uses backend default authority first
- active portfolio and default portfolio are distinct and both observable
- legacy name preferences no longer act as the primary startup rule

### PCD-P4. Sidebar Command Deck Rollout

Purpose:

Replace the minimal sidebar selector with the approved grouped command deck for switching and default assignment.

Target files:

- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`
- `frontend/src/app/components/Sidebar.tsx`
- `frontend/src/app/components/sidebar/Sidebar.test.tsx`
- `frontend/src/app/components/hooks/useSidebarRuntime.ts`
- `frontend/src/app/components/hooks/useSidebarRuntime.test.tsx`
- `frontend/src/app/globals.css`

Tasks:

1. Redesign `SidebarPortfolioSwitcher` into the unified command deck entry and expanded panel.
2. Render grouped sections for:
   - `SYSTEM MATRICES`
   - `USER MATRICES`
3. Support row actions for:
   - `Activate` on all rows
   - `Set Default` on `SYSTEM` rows only
4. Render explicit locked states on `USER` rows so the restriction is visible rather than hidden.
5. Add a compact summary rail for the current global default and badges such as `ACTIVE` and `DEFAULT`.
6. Keep the styling aligned with the existing industrial command language and preserve collapsed-sidebar behavior.
7. Add tests covering:
   - grouped rendering
   - active badge movement
   - default badge movement after reassignment
   - locked `USER` default action behavior

Deliverables:

- sidebar-based portfolio command deck
- grouped portfolio organizer surface
- default assignment controls and visible lock states

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/components/sidebar/Sidebar.test.tsx src/app/components/hooks/useSidebarRuntime.test.tsx`
- `npm --prefix frontend run build`

Acceptance criteria:

- operators can switch to any portfolio from the sidebar command deck
- only `SYSTEM` rows can trigger default assignment
- default and active states are visually distinct and update correctly

### PCD-P5. Regression Lock and Execution Checkpoint

Purpose:

Lock the rollout with focused backend and frontend verification around startup authority, sidebar behavior, and fallback safety.

Target files:

- touched files from `PCD-P1` through `PCD-P4`

Tasks:

1. Re-run the focused backend portfolio suites.
2. Re-run the focused frontend context and sidebar suites.
3. Run a frontend build to catch contract drift across routes consuming `PortfolioContext`.
4. Manually sanity-check the portfolio flow in the app if a local verification path is available:
   - boot with a persisted default `SYSTEM`
   - reassign the default
   - delete or simulate removal of the current default
   - confirm fallback behavior
5. Record any remaining out-of-scope regressions separately from this slice.

Deliverables:

- integrated regression evidence for backend and frontend
- explicit closeout checkpoint for the portfolio command deck slice

Verification:

- `pytest tests/test_portfolio_operations.py tests/test_portfolio_query_service.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/context/PortfolioContext.test.tsx src/app/components/hooks/useSidebarRuntime.test.tsx src/app/components/sidebar/Sidebar.test.tsx`
- `npm --prefix frontend run build`

Acceptance criteria:

- backend and frontend verification pass for default-authority behavior
- startup and reassignment behavior are stable across the integrated slice
- any remaining issues are clearly outside the approved scope

## 6. Risks and Controls

### Risk 1. Legacy name-based fallback still overrides the real default

Control:

- move boot resolution into a backend-driven default-first contract
- add explicit tests for persisted default precedence

### Risk 2. Active and default portfolio state become conflated

Control:

- keep separate ids in API payloads, context, and UI labels
- test reassignment without forcing active-state mutation unless intended

### Risk 3. Default assignment works in UI but is not enforced server-side

Control:

- validate `SYSTEM`-only eligibility in the backend
- keep `USER` controls visibly locked in the frontend
- add API rejection tests for invalid assignments

### Risk 4. Portfolio deletion leaves the app in a broken startup state

Control:

- clear invalid default references on delete
- resolve through explicit fallback order
- add deletion and missing-default regression tests

### Risk 5. Sidebar redesign regresses scanability or collapsed behavior

Control:

- keep the command deck grouped and label-driven
- preserve collapsed-sidebar behavior as a specific acceptance criterion
- run focused sidebar tests and a frontend build before closeout

## 7. Recommended Execution Notes

- Start with `PCD-P1` and `PCD-P2` together if batching is necessary, because the frontend cannot safely change startup behavior until backend authority and API shape are stable.
- Keep naming honest in code and API payloads: `active` and `default` should never be overloaded.
- Reuse the existing portfolio context and sidebar runtime seams instead of creating a separate portfolio-deck provider.
- Treat the fallback order as a contract that should be shared by helper functions and tests, not duplicated ad hoc.

## 8. Recommended Next Move After This Plan

Execute `PCD-P1` and `PCD-P2` as the first active implementation slice. They establish the persisted backend default authority and API contract that the frontend boot and sidebar command deck depend on.
