# App-Wide Horus Chamber Shell Rollout Design

Date: 2026-04-22
Status: Proposed

## Objective

Extend the approved `Signal Temple` and `Release Chamber` visual language across the entire application so Horus reads as one premium product family instead of a few polished flagship pages surrounded by legacy surfaces.

This phase is not a workflow rewrite. The signal-desk, lifecycle, Telegram release rail, and existing route logic remain intact. The focus is shell-level design unification, chamber-grade page presentation, and a reliable top-navbar command layer.

## Design Context

The approved design context for Horus remains:

- users: high-intensity EGX quantitative operators
- brand personality: cold, predatory omniscience
- aesthetic direction: institutional futuristic industrial terminal
- product hierarchy:
  - `Home` is the sanctum
  - `Telegram` is the release throne
  - all remaining routes are subordinate chambers in the same civilization

This rollout should preserve the sharper ceremonial mood already established in `Home` and `Telegram` while making the rest of the app feel authored rather than inherited.

## Section 1: Horus Chamber System

The whole app should become one shared `Horus chamber system`, with `Home` and `Telegram` retained as the two ceremonial flagships and every other route upgraded into a matching subordinate chamber.

Recommended structure:

- `Home`
  - remains the `Signal Temple`
  - highest drama, strongest hero composition
- `Telegram`
  - remains the `Release Chamber`
  - second flagship, focused on outbound authority
- all other routes
  - become consistent chamber variants, not generic dashboards
  - each gets:
    - a strong chamber header
    - a disciplined chamber body
    - shared surfaces, tags, and action styling
    - domain-specific emphasis through copy and accent balance rather than a separate visual language

The app should stop feeling like `one beautiful page plus many leftovers` and start feeling like `one design civilization with ranked rooms`.

## Section 2: Shared Primitive Rollout

Consistency should come from shared shell primitives first, not from repainting pages manually.

Recommended upgrade targets:

- `frontend/src/app/globals.css`
  - promote the new chamber palette, spacing rhythm, surface depth, and chrome sizing into reusable tokens
- `CommandHeader`
  - becomes the default crown/header for non-flagship routes
  - stronger hierarchy, clearer status chips, more authored framing
- `IndustrialCard`
  - upgraded so common panels inherit the richer chamber surface language
- `CommandToolbar`
  - made more ceremonial and more clearly subordinate to the chamber header
- `section-surface` and `section-surface-muted`
  - tuned closer to the new `Home` and `Telegram` atmosphere
- empty, degraded, warning, and system-notice states
  - aligned so fallback and failure states still feel intentional

Implementation principle:

`change the system, then let pages inherit the civilization`

## Section 3: Navbar Command Layer

The top navbar dropdown must stop behaving like a fragile hover reveal and become a real chamber navigator.

Current issues:

- grouped routes appear as hidden flyouts
- they are easy to miss
- hidden links in the DOM create testing and discoverability friction
- the interaction quality is below the flagship surfaces

Recommended behavior:

- grouped domains open as anchored menus with real open/closed state
- support:
  - click
  - hover enhancement
  - keyboard focus
  - escape to close
  - outside click dismissal
- clear distinction between:
  - direct anchors
  - expandable domains
- visible active-route emphasis inside the open menu
- stable menu sizing and viewport-aware placement

Recommended visual direction:

- the menu should feel like a `sub-chamber`
- richer than a plain dropdown
- calmer and smaller than a flagship page
- fully aligned with the Horus family

The navbar should become `a real navigation command layer`, not `a hover card with hidden links`.

## Section 4: Chamber Families By Route Role

Non-flagship routes should adopt chamber variants by role, not all receive the exact same treatment.

Recommended chamber families:

- `Intelligence Chambers`
  - `Scanner`, `Oracle`, `Whales`, `Traps`, `Analytics`, `Live`
  - sharper data emphasis
  - cooler precision accents
  - stronger telemetry language

- `Oversight Chambers`
  - `Audit`, `Strategy`, `Optimization`, `Simulation`, `Reports`
  - calmer analytical posture
  - stronger review and verdict hierarchy
  - more archival composure

- `System Chambers`
  - `Portfolio`, `Settings`, `Status`
  - clearest operational hierarchy
  - tighter status framing
  - less spectacle, more authority

- `Admin Intel Chambers`
  - `News`, `Sectors`, `Seasonality`, `Arbitrage`
  - same family
  - slightly lighter and more contextual
  - clearly useful but visually below the two flagships

This keeps the product unified without making it monotonous.

## Section 5: Practical Outcomes

This rollout must solve real usability problems while improving design quality.

Required outcomes:

- the app feels correct at normal desktop zoom
- the top shell no longer consumes excessive vertical space
- headers establish hierarchy quickly
- cards and panels feel authored instead of mass-produced
- dropdown navigation is reliable and testable
- degraded, empty, and warning states still feel deliberate

Success is not only visual. It is operational:

- `Home` feels like the sanctum
- `Telegram` feels like the release throne
- every other page feels like a true Horus chamber
- the navbar feels like a command layer
- the shell works at `100%` zoom without manual rescue

## Non-Goals

This phase does not:

- change signal-desk workflows
- change lifecycle or Telegram business logic
- move `News` or `Sectors` into the formal signal pipeline
- replace `Home` or `Telegram` with new flagship concepts
- require bespoke redesigns for every route before system-level improvements land

## Recommended Implementation Focus

The rollout should prioritize:

1. shared shell tokens and surface system
2. navbar command-layer repair and dropdown redesign
3. shared chamber primitives (`CommandHeader`, `IndustrialCard`, `CommandToolbar`, empty/error states)
4. route-family rollout across the remaining pages
5. final responsiveness, browser regression, and audit lock

## Success Criteria

The phase is successful when:

- the app reads as one coherent Horus product family
- `Home` and `Telegram` remain visibly highest-rank surfaces
- non-flagship pages inherit chamber quality without feeling copied
- the navbar dropdown behaves like a real navigator instead of a hidden hover trick
- the shell remains usable, responsive, and testable at standard zoom levels
