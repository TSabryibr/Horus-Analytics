# App-Wide Horus Chamber Shell Rollout Implementation Plan

Date: 2026-04-22
Status: Planned
Spec: `docs/superpowers/specs/2026-04-22-app-wide-horus-chamber-shell-rollout-design.md`

## Objective

Roll out the approved Horus chamber design system across the application by upgrading shared shell primitives first, fixing the navbar command layer, and then aligning the remaining routes into chamber families without disturbing the working signal, lifecycle, or Telegram business flows.

## Delivery Strategy

This rollout should be executed as a shell-first design refactor:

1. upgrade shared design tokens and shell primitives
2. repair the navbar and dropdown command layer
3. spread the new chamber system across route families
4. lock responsiveness, browser behavior, and regression coverage

This is intentionally not a route-by-route bespoke redesign pass. Shared inheritance is the primary mechanism.

## Phase Plan

### HCSR-P1: Shared Chamber Token System

Goal:
- establish the app-wide chamber visual system in reusable tokens and base shell utilities

Scope:
- `frontend/src/app/globals.css`
- any shared utility classes needed for:
  - chamber surfaces
  - chamber crowns/headers
  - orbit/support panels
  - state chips
  - empty/degraded states
  - chrome spacing and standard zoom layout stability

Implementation targets:
- refine global palette balance around obsidian, sandstone haze, solar gold, and restrained cyan
- normalize shell spacing so the app works correctly at `100%` zoom
- tune shared surface depth, borders, radius rhythm, and shadows
- add reusable classes/tokens for flagship vs subordinate chamber rank

Verification:
- targeted tests for shared shell consumers where needed
- `npm run build --prefix frontend`

### HCSR-P2: Navbar Command Layer Repair

Goal:
- replace the fragile hover-only grouped navigation with a real chamber navigator

Scope:
- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- related navbar tests and Playwright expectations

Implementation targets:
- convert grouped domains into anchored menus with explicit open/closed state
- support click, hover enhancement, keyboard focus, escape close, and outside click dismissal
- ensure hidden flyout items are not treated like visibly available primary actions
- improve visual affordance for expandable domains
- ensure dropdown placement is viewport-stable and visually aligned with the chamber system

Verification:
- navbar Jest coverage
- route-shell Playwright checks for command ribbon readiness and navigation behavior

### HCSR-P3: Shared Primitive Upgrade

Goal:
- upgrade the shared shell components so non-flagship pages inherit the new chamber quality automatically

Scope:
- `CommandHeader`
- `IndustrialCard`
- `CommandToolbar`
- other shared shell/notice primitives as needed

Implementation targets:
- make `CommandHeader` the default chamber crown for subordinate pages
- improve card hierarchy and panel rhythm
- align warning, error, stale, and empty states with the authored Horus language
- keep `Home` and `Telegram` visibly above the subordinate chamber tier

Verification:
- targeted component tests
- build validation

### HCSR-P4: Chamber Family Rollout Across Routes

Goal:
- apply the upgraded system across the remaining route families

Route families:
- Intelligence Chambers
  - `Scanner`, `Oracle`, `Whales`, `Traps`, `Analytics`, `Live`
- Oversight Chambers
  - `Audit`, `Strategy`, `Optimization`, `Simulation`, `Reports`
- System Chambers
  - `Portfolio`, `Settings`, `Status`
- Admin Intel Chambers
  - `News`, `Sectors`, `Seasonality`, `Arbitrage`

Implementation targets:
- align page shell composition
- align header/crown treatment
- align panel density and accent usage by family
- reduce visual orphaning and inconsistent legacy layouts
- keep workflows unchanged while upgrading presentation

Verification:
- targeted route/component tests per touched family
- manual browser sanity during rollout

### HCSR-P5: Responsiveness and Zoom Hardening

Goal:
- ensure the shell and chamber pages work correctly at normal desktop zoom and remain stable across viewport sizes

Scope:
- shared chrome
- flagship pages
- at least one representative route from each chamber family

Implementation targets:
- remove remaining oversized shell patterns
- ensure dropdowns and anchored overlays do not clip or overflow unpredictably
- keep mobile and tablet behavior coherent with the new chamber system
- preserve accessible interaction targets and readable hierarchy

Verification:
- targeted responsive/component tests where applicable
- Playwright route crawl
- visual audit pass

### HCSR-P6: Regression Lock and Final Audit

Goal:
- confirm the app-wide chamber rollout is stable and shippable

Verification sweep:
- `npm test -- --runInBand`
- `npm run build --prefix frontend`
- `npm run test:e2e -- home.spec.ts interactive_controls.spec.ts e2e_crawl.spec.ts`
- `npm run test:e2e:audit`

Completion criteria:
- shared shell is coherent at `100%` zoom
- navbar command layer is reliable and testable
- `Home` and `Telegram` remain flagship-ranked
- subordinate routes visibly inherit the chamber family
- browser verification is green

## Execution Notes

- use shared primitives and tokens as the main lever, not one-off page repainting
- keep existing business workflows intact
- do not regress the signal desk, lifecycle, Telegram release rail, or autopilot flows
- preserve the admin-only boundary for `News` and `Sectors`
- do not revert unrelated in-flight workspace changes

## Recommended First Slice

Start with:

1. `HCSR-P1` Shared Chamber Token System
2. `HCSR-P2` Navbar Command Layer Repair
3. the beginning of `HCSR-P3` Shared Primitive Upgrade

That combination gives the biggest app-wide visual improvement earliest and fixes the current navbar weakness before family rollout begins.
