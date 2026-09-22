# Navbar Portfolio Command And Shell Consistency Design

Date: 2026-04-17
Status: Approved design for planning
Authoring mode: Brainstorming-approved design

Based on:

- `frontend/src/app/layout.tsx`
- `frontend/src/app/components/MainLayoutWrapper.tsx`
- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/custom/CommandHeader.tsx`
- `frontend/src/app/components/Sidebar.tsx`
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`
- `.impeccable.md`

## 1. Purpose

This design moves portfolio switching and global default authority into the actual live frontend shell and defines a broader consistency sweep to eliminate remaining old-design seams across the app.

The goal is not only to relocate the portfolio organizer from the legacy sidebar seam into the top navbar, but also to make the full application read as one coherent command environment.

## 2. Problem Summary

The app's current live shell is no longer driven by the older sidebar path.

The verified ownership path is:

`layout.tsx -> MainLayoutWrapper -> IndustrialNavbar -> page content`

This creates a mismatch:

- the earlier portfolio organizer work landed in the legacy sidebar seam
- the live product experience is anchored by `IndustrialNavbar`
- parts of the app already follow the newer shared command-system patterns
- other areas may still carry older shell assumptions, visual framing, or duplicated authority controls

As a result, the app risks presenting two generations of navigation and workspace control at once.

## 3. Goal

Introduce one authoritative global workspace surface in the live navbar and bring the rest of the app into alignment with the new design system.

This design is successful when:

1. the top `IndustrialNavbar` is the primary portfolio organizer and default-selection surface
2. the old sidebar portfolio seam is removed, neutralized, or demoted so it no longer competes for authority
3. the app's major routes follow one shared shell language
4. leftover old-design markers are either removed or intentionally normalized

## 4. Non-Goals

This design does not include:

- redesigning the entire product from scratch
- changing backend portfolio rules already approved in the portfolio command deck design
- introducing multiple portfolio-control surfaces with equal authority
- rewriting each page into the same layout regardless of domain needs
- broad visual experimentation outside the established design direction in `.impeccable.md`

## 5. Recommended Approach

Three approaches were considered.

### Option A. Navbar command cluster plus app-wide consistency pass

Move portfolio authority into the top `IndustrialNavbar` and perform a route-by-route consistency sweep across the live shell and major pages.

Pros:

- matches the actual live application entrypoint
- keeps global workspace authority in the global chrome
- removes competing surfaces
- addresses both the portfolio migration and broader design drift in one pass

Cons:

- wider touch surface across shared UI and multiple routes

Recommended.

### Option B. Navbar summary plus full drawer

Keep the navbar as a trigger and summary surface, but place the full organizer in a secondary drawer or panel.

Pros:

- lighter persistent chrome
- more room for dense controls

Cons:

- introduces another interaction layer
- weakens the directness of the command surface

Reject for this project.

### Option C. Minimal navbar migration only

Move only the current portfolio switcher into the navbar and defer the broader shell cleanup.

Pros:

- fastest to ship
- smallest immediate change set

Cons:

- leaves visible old-design leftovers elsewhere
- does not meet the user's request for a broader consistency sweep

Reject for this project.

## 6. Design Principles

The migration and cleanup should follow these rules:

- Live shell first. The app should evolve around the actual runtime entrypoints, not legacy seams that still happen to exist in the codebase.
- Single workspace authority. One primary portfolio organizer should exist in the global chrome.
- Command-system coherence. Shared shell primitives should feel related across routes without flattening page-specific function.
- Mechanical clarity. Labels, groupings, and status tags should carry operational meaning.
- Industrial restraint. The UI should stay aligned with the cold, institutional, operator-first design direction in `.impeccable.md`.
- No ghost chrome. Old controls that suggest deprecated interaction models should be removed or reduced to non-authoritative mirrors.

## 7. Live Shell Ownership

The migration should explicitly respect the current live ownership path:

1. `frontend/src/app/layout.tsx`
2. `frontend/src/app/components/MainLayoutWrapper.tsx`
3. `frontend/src/app/components/custom/IndustrialNavbar.tsx`
4. route page shells and `CommandHeader` surfaces

This means the legacy `Sidebar` path is no longer the correct primary insertion point for workspace authority.

If the sidebar still exists in the codebase for local or transitional use, it must not remain the authoritative portfolio workflow after this migration.

## 8. UX Architecture

The live command model should be:

`persisted backend default -> portfolio context -> IndustrialNavbar command cluster -> route-level consumption`

### 8.1 Navbar command cluster

`IndustrialNavbar` gains a dedicated `Portfolio Command Cluster` near the operational controls.

In compact form it should show:

- active portfolio name
- active portfolio class
- current global default system portfolio
- a clear trigger for opening the command surface

### 8.2 Expanded command deck

Opening the cluster reveals a structured deck that includes:

- search or quick filter input
- grouped sections for `SYSTEM MATRICES` and `USER MATRICES`
- `Activate` on any portfolio row
- `Set Default` only for `SYSTEM` rows
- visible locked treatment for `USER` rows
- a summary rail for the current global default

This should use the navbar's industrial chrome language, not the older sidebar card language.

### 8.3 Route relationship

Route pages may reflect the current active portfolio state, but they should not own the primary workflow for:

- switching the global workspace
- assigning the global default system portfolio

Those actions belong to the global navbar surface.

## 9. Sidebar Migration Rules

The old sidebar portfolio control must stop acting as primary authority.

Acceptable end states:

- remove the old sidebar portfolio control entirely
- keep it only as a passive display
- keep it only in contexts where the live navbar is not present, provided it does not compete with navbar authority

Not acceptable:

- two independently actionable global portfolio organizers in the same live experience
- one surface switching active portfolios while another assigns default authority without clear ownership

## 10. Full-App Consistency Sweep

The cleanup pass should audit and normalize the shared frontend surfaces that define the new product language.

Primary sweep targets:

- `MainLayoutWrapper`
- `IndustrialNavbar`
- `CommandHeader`
- routes using `page-shell`, `page-shell-wide`, and related shell classes
- any top-level page or shared component still carrying older sidebar-era or pre-command-system styling

The sweep should look for:

- duplicated or competing control surfaces
- shell framing that does not match the new command environment
- inconsistent spacing rhythm
- hardcoded legacy styling that bypasses newer shared tokens or shell classes
- route-local chrome that conflicts with the newer navbar-plus-command-header architecture
- leftover old navigation affordances or styling metaphors

The objective is consistency, not uniformity. Different pages can keep distinct density and content structure as long as they still belong to the same system.

## 11. Visual Direction

The migrated navbar control and cleanup work must remain aligned with `.impeccable.md`.

The system should feel:

- institutional
- predatory
- mechanically calm
- high contrast and telemetry-driven
- dense but readable

The portfolio control should read as a matrix authority instrument inside the navbar:

- concise status labels
- disciplined grouping
- restrained cyan or amber signal accents
- no consumer-product dropdown softness
- no leftover generic dashboard chrome

## 12. Behavior

### 12.1 Workspace authority

The active portfolio may still be any portfolio allowed by the approved backend rules.

The global default remains restricted to the approved designated class:

- `SYSTEM`

The navbar cluster is now the primary place where operators:

- inspect the active workspace
- switch workspaces
- inspect the current default
- reassign the default

### 12.2 Boot and persistence

Boot resolution should continue to respect the previously approved portfolio command deck rules:

1. use the persisted backend default when valid
2. otherwise fall back safely according to the approved resolver chain

Moving the control to the navbar does not change backend authority; it changes where that authority is surfaced in the live product.

### 12.3 Old-seam deactivation

Any old portfolio surface that remains in code after migration must either:

- mirror the navbar state without owning it, or
- be retired from the live shell

No hidden secondary authority paths should remain.

## 13. Audit And Verification

The implementation should include a full verification pass against the live design system.

This should cover:

- shared shell ownership correctness
- responsive behavior of the navbar control
- absence of competing old portfolio controls
- route-by-route visual consistency across major pages
- token and spacing drift in shared layout surfaces

Recommended verification modes:

- focused frontend tests for navbar portfolio behavior
- route-level smoke tests for major pages
- app-wide visual or DOM audit for old design markers where practical
- build verification for the frontend

## 14. Acceptance Criteria

This design is complete when:

1. `IndustrialNavbar` is the live primary portfolio organizer/default surface
2. the old sidebar portfolio seam is no longer acting as global authority
3. the portfolio workflow feels native to the current navbar-driven shell
4. major routes share one coherent command-system language
5. obvious old-design leftovers have been removed or normalized across the app
6. focused tests and a full-app verification pass support the migration

## 15. Risks And Guardrails

### 15.1 Main risks

The primary risks are:

- moving portfolio controls visually but leaving hidden legacy authority paths alive
- creating partial shell consistency where the navbar is modernized but page-level chrome remains fragmented
- over-normalizing pages until they lose needed domain-specific hierarchy

### 15.2 Guardrails

To control those risks:

- treat `IndustrialNavbar` as the single global workspace authority
- audit shared shell primitives before polishing route details
- remove or demote old controls rather than letting them silently coexist
- normalize to shared tokens and shell patterns instead of one-off restyling
- verify both desktop and mobile behavior during the sweep

## 16. Implementation Boundary

This document defines the approved design only.

The next step is an implementation plan that:

- identifies the files needed to migrate portfolio authority into `IndustrialNavbar`
- defines how the old sidebar seam will be removed or neutralized
- scopes the route-by-route consistency sweep
- specifies the verification pass for app-wide design alignment
