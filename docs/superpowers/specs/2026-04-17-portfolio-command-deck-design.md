# Portfolio Command Deck Design

Date: 2026-04-17
Status: Approved design for planning
Authoring mode: Brainstorming-approved design

Based on:

- `frontend/src/app/context/PortfolioContext.tsx`
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`
- `frontend/src/app/portfolio/components/PortfolioShell.tsx`
- `frontend/src/app/portfolio/page.tsx`
- `routes/portfolio.py`
- `.impeccable.md`

## 1. Purpose

This design defines the missing portfolio organizer, workspace switcher, and global default selection behavior for the Horus Analytics II frontend and portfolio API.

The goal is to turn portfolio selection into a deliberate operator workflow:

- switch into any portfolio context quickly
- organize the available matrices in one command surface
- persist one global startup default
- enforce that only `SYSTEM` portfolios may hold startup authority

The approved direction is a unified `Portfolio Command Deck`.

## 2. Problem Summary

The current product already exposes the underlying idea of multiple portfolios, but the workflow is incomplete.

Today:

- the sidebar switcher only offers a minimal select control
- the switcher filters down to `USER` portfolios only
- the initial active portfolio is chosen with hardcoded fallback rules such as `Horus` or `My Portfolio`
- there is no user-visible organizer for portfolio classes
- there is no persisted server-side global default
- the frontend and backend do not express the `default system matrix` concept explicitly

This leaves a clear operational gap.

The app behaves as though portfolios are workspace contexts, but it does not yet provide the command surface needed to manage them with confidence.

## 3. Goal

Introduce one coherent portfolio control system that:

1. allows switching into all portfolio types
2. groups portfolios clearly by operational class
3. persists one global default portfolio on the server
4. restricts that global default to `SYSTEM` portfolios only
5. resolves application startup from the persisted global default before any hardcoded fallback path

## 4. Non-Goals

This design does not include:

- redesigning the broader portfolio analytics page beyond the command deck workflow
- changing the meaning of `USER` versus `SYSTEM` portfolios
- introducing per-user or per-browser remembered portfolio state
- supporting multiple defaults
- allowing `USER` portfolios to become the startup default
- reworking portfolio import, export, or management-report flows

## 5. Recommended Approach

Three approaches were considered.

### Option A. Unified portfolio command deck

Create one command surface accessible from the sidebar or header that handles:

- active portfolio switching
- grouped portfolio organization
- startup default assignment

Pros:

- one mental model for operators
- strongest discoverability
- fits the command-environment design language of the product
- keeps switching and default assignment in the same place

Cons:

- denser than a plain dropdown
- requires disciplined hierarchy in the UI

Recommended.

### Option B. Split quick switcher plus settings organizer

Keep the sidebar switcher lightweight and move default assignment and organization into a settings or portfolio-management area.

Pros:

- simpler sidebar
- less control density in the always-visible chrome

Cons:

- weaker discoverability
- two places to complete one workflow
- higher chance of operator confusion

Reject for this project.

### Option C. Portfolio page only

Make the portfolio page the only place to switch, organize, and assign defaults while leaving the sidebar as a passive indicator.

Pros:

- simplest single-page implementation
- avoids adding sidebar complexity

Cons:

- slow for operators
- weakens the workspace-switching model
- less aligned with the rest of the app's command-driven behavior

Reject for this project.

## 6. Design Principles

The command deck should follow these rules:

- Workspace clarity first. Portfolios are operational contexts, not just records.
- One source of authority. Only one persisted global default may exist.
- Explicit constraints. `USER` portfolios must visibly show that default assignment is locked.
- Mechanical hierarchy. Grouping, labels, and badges must carry meaning without depending only on color.
- Fast switching. Activation of another portfolio should be low-friction and immediate.
- Safe startup. App boot should resolve from persisted backend state before local fallback heuristics.

## 7. UX Architecture

The portfolio control system should be structured as:

`persisted backend default -> portfolio catalog -> portfolio command deck -> active workspace context`

### 7.1 Command deck entry point

The existing sidebar portfolio switcher becomes the launch point for the richer command deck.

In its compact state, it should show:

- the currently active portfolio
- the portfolio class
- a `DEFAULT` marker when the active portfolio is also the persisted global default

### 7.2 Command deck body

Opening the command deck reveals:

- a compact search or filter field
- a global default summary rail
- grouped portfolio sections
- inline actions per row

The grouped sections are:

- `SYSTEM MATRICES`
- `USER MATRICES`

### 7.3 Row actions

Every portfolio row supports `Activate`.

Only `SYSTEM` rows support `Set Default`.

`USER` rows must still render the default constraint explicitly, for example through a locked badge or disabled action state, rather than hiding the control completely.

## 8. Core Behavior

### 8.1 Active portfolio switching

The active portfolio may be any portfolio in the system, including `SYSTEM` and `USER`.

Switching the active portfolio should update frontend context immediately and refresh dependent portfolio views using the selected portfolio id.

### 8.2 Global default assignment

The global default is a separate persisted server-side setting.

Rules:

- exactly one global default may exist at a time
- only a `SYSTEM` portfolio may be assigned as global default
- assigning a new default replaces the previous one immediately
- the command deck must update its indicators as soon as reassignment succeeds

### 8.3 Startup resolution

On app boot, the frontend should request both:

- the portfolio catalog
- the persisted default system portfolio id, or equivalent resolved default metadata

If the persisted default exists and is valid, it becomes the initial active portfolio.

If the persisted default is missing or invalid, the fallback order is:

1. first available `SYSTEM` portfolio
2. existing portfolio resolver fallback logic as the final safety net

This means the current hardcoded `Horus` / `My Portfolio` preference logic should stop being the primary startup rule.

## 9. Backend Design

The backend should add a lightweight persisted setting for the global default system portfolio.

Conceptually this value is:

- `default_system_portfolio_id`

The backend must support:

- reading the current default
- assigning a new default
- validating that the assigned portfolio exists and is `SYSTEM`
- clearing or replacing the default when necessary

The API surface may be implemented either as:

- an extension of the existing portfolio list payload
- or a small dedicated endpoint for reading and setting the default

The key requirement is that the frontend must not need to guess or reconstruct this state from portfolio names.

## 10. Frontend Design

### 10.1 Portfolio context

`PortfolioContext` becomes responsible for resolving active startup state from backend-provided default data.

It should:

- fetch the portfolio catalog
- fetch or receive the persisted default system portfolio id
- initialize the active portfolio from that value when valid
- expose both `activePortfolioId` and the current default-system id to downstream UI

### 10.2 Sidebar command deck

The current sidebar select control should be upgraded into a richer command surface that matches the product's industrial terminal identity.

The approved deck shape includes:

- grouped sections for `SYSTEM` and `USER`
- inline tags such as `ACTIVE`, `DEFAULT`, and locked-default states
- a compact status rail identifying the current global default
- a search or filter affordance for fast scanning

This deck should feel like a workspace authority panel, not a generic consumer dropdown.

### 10.3 Portfolio page relationship

The dedicated portfolio page may later mirror the same state and controls for deeper management, but it should not become the primary owner of default-selection logic.

The source workflow remains the command deck.

## 11. Edge Cases and Safeguards

### 11.1 Active portfolio deleted

If the current active portfolio is deleted, the frontend should automatically move to:

1. the persisted global default, if still valid
2. the next valid fallback described in startup resolution

### 11.2 Global default deleted

If the current global default `SYSTEM` portfolio is deleted:

- the backend should clear that setting
- the frontend should fall back to the next available `SYSTEM` portfolio until a new default is chosen

### 11.3 No system portfolios available

If no `SYSTEM` portfolios exist:

- the deck should show a clear warning state
- the UI must not imply that a startup default is configured
- the backend should reject attempts to point the default to a non-system portfolio

### 11.4 UI/API rule alignment

The `SYSTEM`-only default rule must be enforced in both places:

- disabled or locked in the UI
- validated and rejected in the API

## 12. Visual Direction

The command deck should follow the existing design context in `.impeccable.md`:

- cold, industrial, and operator-first
- semantically colored but not flashy
- high contrast against slate backgrounds
- clear status tagging that does not rely only on color

The deck should read like a matrix authority panel:

- sharp labels
- grouped ledger-style rows
- restrained cyan telemetry accents for active/default system states
- visible lock treatment for rows that cannot hold startup authority

Avoid:

- consumer-style menu patterns
- playful workspace metaphors
- soft retail-product dropdown treatments

## 13. Testing Strategy

### 13.1 Backend

Add tests for:

- reading the persisted global default
- assigning a valid `SYSTEM` portfolio as default
- replacing an existing default
- clearing or recovering from a deleted default
- rejecting attempts to assign a `USER` portfolio as default

### 13.2 Frontend

Add tests for:

- booting into the persisted default system portfolio
- fallback when the persisted default is missing
- grouped deck rendering for `SYSTEM` and `USER`
- locked default action on `USER` rows
- badge and summary updates after default reassignment

### 13.3 Acceptance behavior

This design is successful when:

1. operators can activate any portfolio from one command surface
2. exactly one `SYSTEM` portfolio can be marked as the startup default
3. the frontend boots into the persisted default when valid
4. the UI visibly communicates that `USER` portfolios cannot become the default
5. fallback behavior remains safe when defaults or active portfolios disappear

## 14. Risks and Guardrails

### 14.1 Main risk

The largest risk is splitting authority between frontend heuristics and backend persistence.

If the frontend still prefers hardcoded names while the backend exposes a true default, the product will behave unpredictably.

### 14.2 Guardrails

To control that risk:

- move startup authority to one backend-resolved source
- keep the active portfolio and global default conceptually separate
- enforce the `SYSTEM`-only rule in both API and UI
- add regression tests around boot resolution and deletion scenarios

## 15. Implementation Boundary

This document defines the approved design only.

The next step is to produce an implementation plan that:

- identifies the backend storage and endpoint changes
- updates portfolio context boot resolution
- upgrades the sidebar switcher into the command deck
- defines the test sequence for backend and frontend coverage
