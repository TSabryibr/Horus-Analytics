# Navbar Portfolio Command And Shell Consistency Implementation Plan

Date: 2026-04-17
Based on:

- `docs/superpowers/specs/2026-04-17-navbar-portfolio-command-and-shell-consistency-design.md`
- `docs/superpowers/specs/2026-04-17-portfolio-command-deck-design.md`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/components/MainLayoutWrapper.tsx`
- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/custom/CommandHeader.tsx`
- `frontend/src/app/components/Sidebar.tsx`
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`
- `frontend/src/app/context/PortfolioContext.tsx`
- `frontend/src/app/globals.css`

Track: Navbar Portfolio Migration And Shell Consistency
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Implement the approved live-shell migration as an ordered rollout that:

1. moves portfolio organizer and default-selection authority into `IndustrialNavbar`
2. removes or neutralizes the old sidebar portfolio seam so it no longer competes with the live shell
3. aligns shared shell primitives and major routes with the newer command-system design
4. verifies that the app no longer exposes leftover old-design authority or obvious old-shell drift

## 2. In Scope

Primary implementation targets:

- `IndustrialNavbar` as the authoritative global portfolio command surface
- migration of existing portfolio command behavior out of the old sidebar seam
- cleanup of shared layout surfaces and route-level shell drift
- focused tests and app-wide verification for the new design system

Primary files expected to move:

- `frontend/src/app/layout.tsx`
- `frontend/src/app/components/MainLayoutWrapper.tsx`
- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/custom/CommandHeader.tsx`
- `frontend/src/app/components/Sidebar.tsx`
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`
- `frontend/src/app/components/hooks/useSidebarRuntime.ts`
- `frontend/src/app/context/PortfolioContext.tsx`
- `frontend/src/app/globals.css`
- major route shells under `frontend/src/app/**/`
- related frontend tests and E2E or smoke checks under `frontend/src/app/**/*.test.tsx` and `frontend/e2e/`

Out of scope for this slice:

- backend portfolio default rules already implemented unless the live migration reveals a blocking contract issue
- redesigning page content domains that already fit the new shell system
- introducing a second portfolio workflow surface on the portfolio page
- unrelated feature work outside the shared shell and design-consistency pass

## 3. Execution Rules

These rules apply across the rollout:

1. Treat `layout.tsx -> MainLayoutWrapper -> IndustrialNavbar` as the live shell authority path.
2. Do not leave two actionable global portfolio organizers in the same user experience.
3. Keep global workspace authority in the navbar; route pages may consume state but should not own it.
4. Normalize shared shell patterns before polishing isolated page details.
5. Reuse existing command-system primitives and tokens instead of introducing one-off styling islands.
6. Preserve the established industrial identity from `.impeccable.md`.
7. Verify desktop and mobile behavior during the sweep, not only desktop.

## 4. Work Package Sequence

Execute in this order:

1. `NPC-P1` Live shell trace and shared authority stabilization
2. `NPC-P2` Navbar portfolio command cluster migration
3. `NPC-P3` Sidebar seam retirement or demotion
4. `NPC-P4` Shared shell normalization pass
5. `NPC-P5` Route-by-route consistency sweep
6. `NPC-P6` Full-app verification and regression lock

This order is intentional:

- the shell ownership path must be stabilized before moving global controls into it
- navbar authority must exist before the sidebar seam can be removed or demoted
- shared shell primitives should be normalized before route-specific cleanup so pages inherit a coherent base
- the broad consistency sweep should happen after the primary shell and portfolio authority path are correct
- full-app verification should validate the integrated result rather than partial states

## 5. Work Packages

### NPC-P1. Live Shell Trace And Shared Authority Stabilization

Purpose:

Confirm and harden the real live frontend shell so later migration work lands in the correct seam.

Target files:

- `frontend/src/app/layout.tsx`
- `frontend/src/app/components/MainLayoutWrapper.tsx`
- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/MainLayoutWrapper.test.tsx`

Tasks:

1. Trace how global layout, navbar, banner, and page content compose in the live app.
2. Identify any places where old shell assumptions still leak into `MainLayoutWrapper` or related shared chrome.
3. Ensure `IndustrialNavbar` has the correct data and callback seams needed to host the portfolio control without creating parallel state paths.
4. Add or update shared layout tests where needed so the navbar shell contract is explicit.

Deliverables:

- stable live shell authority path
- clear shared seams for navbar-hosted portfolio controls
- regression coverage around the live shell wrapper if needed

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/components/MainLayoutWrapper.test.tsx`

Acceptance criteria:

- the real global shell ownership path is explicit in code
- navbar-hosted global controls can be wired without depending on legacy sidebar authority

### NPC-P2. Navbar Portfolio Command Cluster Migration

Purpose:

Move the portfolio organizer/default workflow into `IndustrialNavbar` so it becomes the authoritative global workspace surface.

Target files:

- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/context/PortfolioContext.tsx`
- `frontend/src/app/components/hooks/useSidebarRuntime.ts`
- related tests for navbar and portfolio context
- `frontend/src/app/globals.css`

Tasks:

1. Design and implement the `Portfolio Command Cluster` within the navbar chrome.
2. Surface:
   - current active portfolio
   - current global default system portfolio
   - grouped `SYSTEM` and `USER` portfolio lists
   - `Activate` for all rows
   - `Set Default` for `SYSTEM` rows only
   - visible locked state for `USER` rows
3. Keep state wiring grounded in the existing portfolio context rather than creating a new authority path.
4. Ensure the navbar cluster works in both desktop and mobile layouts.
5. Add or update tests covering active/default rendering and command behavior in the navbar seam.

Deliverables:

- portfolio organizer and default-selection workflow inside `IndustrialNavbar`
- responsive global workspace control in the live shell
- focused test coverage for navbar-hosted portfolio authority

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/context/PortfolioContext.test.tsx`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/components/custom`

Acceptance criteria:

- the live navbar is the primary portfolio authority surface
- active and default portfolio states are visible and distinct in the navbar
- mobile and desktop layouts both preserve usable access to the portfolio cluster

### NPC-P3. Sidebar Seam Retirement Or Demotion

Purpose:

Remove the old sidebar portfolio seam as a competing source of authority in the live app.

Target files:

- `frontend/src/app/components/Sidebar.tsx`
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`
- `frontend/src/app/components/Sidebar.test.tsx`
- any consumers that still expect sidebar-driven portfolio authority

Tasks:

1. Determine whether the old sidebar control should be removed entirely or kept as a passive mirror in non-live contexts.
2. Eliminate duplicate actionable portfolio authority from the old sidebar path.
3. Update tests so they reflect the new ownership model rather than the retired sidebar workflow.
4. Remove stale visual or logic artifacts that still imply the sidebar owns workspace switching.

Deliverables:

- no competing old portfolio authority in the legacy sidebar seam
- updated tests reflecting navbar ownership
- cleaned-up leftover sidebar-specific portfolio logic

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/components/Sidebar.test.tsx`

Acceptance criteria:

- the old sidebar seam no longer acts as a live global portfolio organizer
- no duplicate actionable portfolio control remains in the same experience

### NPC-P4. Shared Shell Normalization Pass

Purpose:

Bring shared shell primitives into alignment with the new command-system design so route cleanup builds on a coherent base.

Target files:

- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/custom/CommandHeader.tsx`
- `frontend/src/app/components/MainLayoutWrapper.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/app/components/config/navigation.ts`

Tasks:

1. Normalize spacing rhythm, framing, and token usage across the shared shell.
2. Remove hardcoded legacy styling that conflicts with the command-system look.
3. Align navbar, command headers, and page-shell classes so they feel like one environment.
4. Preserve route-specific hierarchy while eliminating outdated chrome metaphors.

Deliverables:

- shared shell primitives that match the current design language
- reduced token drift and fewer one-off legacy styles
- consistent shell framing across the global app chrome

Verification:

- `npm --prefix frontend run build`

Acceptance criteria:

- shared shell components feel visually related and intentional
- old-sidebar-era framing or styling leftovers are removed from the shared base

### NPC-P5. Route-By-Route Consistency Sweep

Purpose:

Audit and normalize major routes so the app reads as one cohesive command system instead of a mix of old and new shells.

Target files:

- top-level route shells and pages under:
  - `frontend/src/app/page.tsx`
  - `frontend/src/app/portfolio/**`
  - `frontend/src/app/oracle/**`
  - `frontend/src/app/scanner/**`
  - `frontend/src/app/live/**`
  - `frontend/src/app/status/**`
  - `frontend/src/app/settings/**`
  - `frontend/src/app/seasonality/**`
  - `frontend/src/app/arbitrage/**`
  - `frontend/src/app/whales/**`
  - other major top-level routes still using older shell patterns

Tasks:

1. Review each major route for shell drift against the shared design system.
2. Normalize:
   - page-shell usage
   - command header framing
   - spacing rhythm
   - old control styling
   - outdated layout wrappers that clash with the new shell
3. Leave page-specific domain content intact where it already fits the system.
4. Add or update focused tests only where shell behavior or top-level rendering contracts change materially.

Deliverables:

- major routes aligned to the new shared shell language
- removal or normalization of obvious old-design leftovers
- targeted test updates for changed shells where needed

Verification:

- `npm --prefix frontend run test -- --runInBand`

Acceptance criteria:

- major routes feel like one app, not parallel generations
- obvious old-design markers have been removed or normalized

### NPC-P6. Full-App Verification And Regression Lock

Purpose:

Validate the integrated migration technically and visually across the app.

Target files:

- touched files from `NPC-P1` through `NPC-P5`
- relevant test and E2E files under `frontend/src/app/**/*.test.tsx` and `frontend/e2e/`

Tasks:

1. Run focused frontend tests for shared shell and portfolio behavior.
2. Run a production build of the frontend.
3. Run an app-wide route smoke or E2E pass where practical.
4. Perform a visual audit for:
   - old portfolio authority leftovers
   - mismatched shell framing
   - inconsistent command-header patterns
   - responsive regressions
5. Record any remaining out-of-scope inconsistencies separately from this rollout.

Deliverables:

- integrated verification evidence for the migration
- explicit list of residual issues if any remain outside scope

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/components/MainLayoutWrapper.test.tsx src/app/context/PortfolioContext.test.tsx`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test -- --runInBand`

Acceptance criteria:

- the navbar migration is stable in the live shell
- the app no longer exposes obvious old-design authority conflicts
- full-app verification supports the consistency sweep

## 6. Risks And Controls

### Risk 1. Navbar migration leaves hidden legacy authority alive

Control:

- explicitly retire or demote the old sidebar seam
- verify there is only one actionable global portfolio organizer in the live experience

### Risk 2. Shell cleanup becomes a collection of one-off restyles

Control:

- normalize shared primitives first
- reuse command-system tokens and page-shell patterns
- avoid route-specific styling patches unless they are necessary

### Risk 3. Mobile navbar behavior regresses under the denser portfolio control

Control:

- treat responsive behavior as a first-class acceptance criterion
- verify both compact and expanded navbar states during implementation

### Risk 4. Route cleanup over-normalizes pages and erodes domain hierarchy

Control:

- normalize shell framing and control language, not content personality
- keep route-specific density and information structure where already effective

### Risk 5. Full-app test scope becomes too noisy to interpret

Control:

- keep focused checks around shared shell and portfolio authority
- use the broader app run as a final regression pass, not the first signal

## 7. Recommended Execution Notes

- Start with `NPC-P1` and `NPC-P2` together if the shared shell trace is already clear in code, because the navbar cluster is the critical-path migration.
- Treat sidebar cleanup as a hard follow-on to navbar migration, not an optional polish pass.
- During the route sweep, prioritize the top-level operator paths first: home, portfolio, oracle, scanner, live, status, and settings.
- Where a route already conforms to the shared command system, leave it alone and avoid gratuitous churn.

## 8. Recommended Next Move After This Plan

Execute `NPC-P1` and `NPC-P2` as the first active implementation slice. They establish the live-shell authority seam and move the portfolio organizer into the actual `IndustrialNavbar`, which the rest of the consistency sweep depends on.
