# Shared Frontend Command System Design

Date: 2026-04-12
Status: Approved design for planning
Authoring mode: Brainstorming-approved design

Based on:

- `frontend/src/app/globals.css`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/components/MainLayoutWrapper.tsx`
- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/custom/IndustrialCard.tsx`
- `frontend/src/app/oracle/components/OracleShell.tsx`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/scanner/components/ScannerShell.tsx`
- `frontend/src/app/live/components/LiveShell.tsx`
- `frontend/src/app/status/components/StatusShell.tsx`
- `frontend/e2e/e2e_crawl.spec.ts`
- `frontend/e2e/_phase3_audit.spec.ts`

## 1. Purpose

This design defines a broader shared-system frontend refresh for Horus Analytics II.

The goal is not to restyle one page in isolation. The goal is to turn the app into one coherent command environment across:

- the navbar
- page shells and headers
- core card surfaces
- right-rail chrome
- page background and framing
- loading, empty, and error states

The approved visual direction is `B`, interpreted as a cinematic intelligence-wall style with scanability prioritized over theatrical ornament.

That means the app should feel atmospheric and premium, while still reading quickly during trading workflows.

## 2. Problem Summary

The current frontend already has strong visual ingredients:

- a dark tactical palette
- industrial corner treatments
- mono labels and telemetry language
- atmospheric gradients and scan-line motifs

But those ingredients are applied inconsistently.

Today, the app presents several competing shell patterns:

- the navbar uses one rhythm and density model
- Oracle uses a different hero and panel system
- Scanner uses a separate header and alert language
- Live uses softer rounded surfaces and a different control rail style
- Status uses a cleaner observability treatment that does not fully match the other pages

This creates visual drift:

- page headers do not share one contract
- controls change shape from route to route
- cards do not communicate hierarchy consistently
- rails and sticky panels use different offsets and framing rules
- responsive behavior varies enough to risk new layout regressions

The result is that the product feels assembled from strong pieces rather than operating as one deliberate interface system.

## 3. Goal

Introduce a shared command-system layer that standardizes the app chrome without flattening each page's personality.

The target outcome is:

1. Every top-level route feels like part of the same operating environment.
2. The navbar, page shell, and card system communicate one hierarchy.
3. Cinematic styling is carried by the chrome and atmosphere, not by excessive noise or ornament.
4. Dense workflows remain fast to scan on desktop and stable on mobile.
5. Browser-first frontend tests can verify the shared system and catch layout regressions early.

## 4. Non-Goals

This design does not include:

- a product rebrand
- changing the information architecture of the primary routes
- rewriting feature logic for Oracle, Scanner, Live, or Status beyond UI shell alignment
- creating a brand-new component library unrelated to the existing industrial design language
- replacing browser-first verification with a large unit-test-only frontend strategy

## 5. Recommended Approach

Three approaches were considered.

### Option A. Light normalization only

Standardize spacing, borders, and typography while keeping each page shell mostly as-is.

Pros:

- lowest implementation risk
- smallest diff
- fast visual cleanup

Cons:

- does not fix the deeper shell and chrome drift
- keeps page headers and cards feeling unrelated
- still leaves Oracle as a visual island

Reject for this project.

### Option B. Shared-system cinematic refresh

Create a small set of shared chrome primitives for navbar, page headers, action rails, cards, and page framing. Apply them across the major top-level routes while keeping each page's data density and content structure intact.

Pros:

- solves the real consistency problem
- preserves the current tactical identity instead of replacing it
- supports both dense trading workflows and a more premium visual presentation
- gives frontend testing a clear shared contract to verify

Cons:

- larger than a pure polish pass
- may require touching several shells together to avoid partial drift

Recommended.

### Option C. Full dramatic overhaul

Push much harder on animation, glow, layered overlays, and stylized surfaces across the whole app.

Pros:

- highest immediate visual impact
- strongest differentiation

Cons:

- increases regression risk
- risks making dense analytical pages harder to scan
- more likely to age poorly than a disciplined shared system

Reject for this phase.

## 6. Design Principles

The approved system should follow these rules:

- Scanability first. The interface must serve operational reading speed before spectacle.
- Atmosphere through depth. Cinematic quality should come from layered surfaces, lighting, and hierarchy rather than clutter.
- One chrome language. Headers, rails, cards, and control strips should feel related across routes.
- Visual hierarchy over repetition. Not every box should look the same; card tone should communicate importance.
- Responsive simplification. Mobile should simplify and stack cleanly instead of shrinking desktop layouts.
- Browser-first confidence. Shared chrome changes must be verified in the rendered app, not only in isolated unit tests.

## 7. Shared System Architecture

The shared command-system layer should be introduced as a small reusable structure above route-specific content:

`design tokens -> shared chrome primitives -> page shells -> page-specific analytical panels`

### 7.1 Token layer

The token layer remains anchored in `frontend/src/app/globals.css`, but it should be extended to describe command-chrome concerns more clearly:

- page atmosphere and background depth
- shell spacing and section rhythm
- surface elevation tiers
- chrome border intensity
- active, muted, alert, and success telemetry accents
- sticky offsets beneath the navbar and banners

The key design change is conceptual: shared tokens should describe system surfaces and chrome roles, not just raw color and spacing values.

### 7.2 Shared chrome primitive layer

The system should standardize a small set of primitives:

- `command-navbar`
- `page-frame`
- `command-header`
- `command-toolbar`
- `surface-card`
- `rail-card`

These primitives should replace the current pattern where each page improvises its own shell language.

### 7.3 Page shell layer

Top-level pages such as Oracle, Scanner, Live, Status, Home, and the other route shells should compose the shared primitives instead of declaring new page-specific chrome rules wherever possible.

Page identity should come from:

- icon choice
- status chips
- mission text
- action set
- card composition

Page identity should not come from inventing a new shell contract each time.

## 8. Shared Primitive Contracts

### 8.1 `command-navbar`

The navbar should become a calm tactical ribbon with clearer grouping:

- a compact brand block on the left
- a horizontally scrollable primary route strip in the center
- a right-side ops cluster for sync/runtime/language

The active route should use one shared illuminated frame treatment across all pages.

The navbar should support:

- stable desktop density
- touch-friendly mobile tap targets
- clean horizontal scrolling without clipping
- stronger separation between navigation and system status

### 8.2 `page-frame`

The page frame should define the shared environmental chrome:

- restrained atmospheric gradient
- subtle grid texture
- edge lighting and section separators
- consistent page padding
- safe overflow behavior
- shared sticky spacing below navbar and global banners

This is the layer that carries most of the cinematic quality.

### 8.3 `command-header`

Every major page shell should use the same hero structure:

- eyebrow label
- page title
- one-sentence mission description
- compact status chips
- action rail

This gives Oracle, Scanner, Live, and Status a common language while preserving their individual content.

### 8.4 `command-toolbar`

Controls such as toggles, selects, search inputs, refresh buttons, and mode switches should share one command-strip language:

- consistent heights
- shared border and fill behavior
- predictable wrapping on small screens
- one active-state treatment
- one disabled-state treatment

This removes the current drift where control clusters vary sharply between pages.

### 8.5 `surface-card`

Cards should become tiered instead of visually uniform.

Use three shared tones:

- `primary`: the main analytical focus surface for content such as Oracle briefing output or live intelligence panels
- `secondary`: support surfaces for charts, diagnostics, or side analyses
- `rail`: sticky or stacked support modules such as archives, tactical status, or operator notes

The system should communicate importance through tone, spacing, and framing rather than by repeating the same card shell everywhere.

## 9. Route Application Model

### 9.1 Oracle as the reference page

Oracle should become the reference implementation for the shared system:

- a strong command header at top
- a primary left-side briefing surface
- secondary analytical cards underneath
- a right rail built from rail-card surfaces

Oracle should stop feeling like a separate product inside the app and instead become the clearest example of the shared command system at work.

### 9.2 Scanner, Live, and Status

These routes should inherit the same page skeleton:

- command header
- command toolbar or control rail
- primary data surface
- secondary support modules
- normalized alert and state panels

Their density can remain distinct, but their shell language should no longer diverge.

### 9.3 Navbar, footer, and page chrome

The top and bottom application chrome should reinforce the same system identity:

- the navbar should feel more deliberate and less cramped
- the footer should remain restrained and technical
- the background effects should support the pages without overpowering them

## 10. Responsiveness and Layout Rules

Desktop, tablet, and mobile must share one responsive intent.

### 10.1 Desktop

On desktop:

- the navbar remains stable and low-friction
- command headers carry route identity
- sticky right rails remain available where useful
- spacing emphasizes panel hierarchy rather than filling all available width

### 10.2 Tablet and mobile

On smaller viewports:

- nav strips become horizontally scrollable without collapsing labels into unusable targets
- action rails wrap into compact stacked groups
- right rails drop beneath the main analysis column
- page headers simplify instead of shrinking awkwardly
- cards preserve readable internal spacing

The system must avoid reintroducing the horizontal overflow and collapsed-main errors already caught by the current Playwright audit.

## 11. State Handling

Loading, empty, degraded, and error states should all use the same surface language as the rest of the app.

That means:

- no abrupt fallback boxes with unrelated styling
- empty states inherit the card tone they belong to
- loading states use restrained motion and telemetry cues
- error and stale-data warnings use one alert contract shared across pages

The app should feel composed and intentional even when content is missing or a backend dependency is unavailable.

## 12. Testing Strategy

This design should be verified with a browser-first frontend testing approach.

### 12.1 Primary verification

The main confidence layer should remain Playwright-based:

- full-route crawl across the top-level app
- desktop and mobile layout audit
- visible `main` landmark verification
- horizontal overflow detection
- sticky-shell and rail sanity checks on key routes
- console and runtime error observation during route traversal

Key acceptance routes for the refresh are:

- `/oracle`
- `/scanner`
- `/live`
- `/status`
- `/`

Together they cover the shared navbar, large command headers, dense controls, right rails, and mixed card hierarchies.

### 12.2 Secondary verification

Add a narrower set of component tests only for shared primitives that gain or enforce new contracts, such as:

- navbar rendering and active state
- shared shell or command-header presence
- shared toolbar wrapping and landmark behavior

The test strategy should not try to prove visual consistency mainly through page-specific unit tests.

### 12.3 Regression targets

The refresh is successful only if it preserves or improves:

- no critical layout errors in the audit run
- no horizontal overflow on supported viewports
- stable route navigation through the primary crawl
- readable mobile stacking for shells and rails

## 13. Risks and Guardrails

### 13.1 Main risk

The largest risk is partial adoption.

If the new shared system is applied to only one or two pages while the other shells keep their older contracts, the app will look more inconsistent instead of less.

### 13.2 Guardrails

To control that risk:

- centralize shared chrome tokens and primitives first
- refresh the navbar and top-level page frame before polishing route-specific details
- treat Oracle, Scanner, Live, and Status as the first shared rollout set
- keep motion restrained and readable
- verify desktop and mobile behavior after each major chrome change

## 14. Acceptance Criteria

This design is satisfied when all of the following are true:

1. The navbar, footer, page frame, page headers, and cards present one coherent command-system language.
2. Oracle, Scanner, Live, and Status all read as part of the same product family while keeping distinct content roles.
3. Primary, secondary, and rail surfaces are visually differentiated without becoming noisy.
4. Mobile and desktop layouts remain readable and free of critical overflow issues.
5. Browser-first tests confirm the refreshed shared chrome across the app's key routes.

## 15. Implementation Boundary

This document defines the approved design only.

The next step is to produce an implementation plan that:

- stages the shared chrome rollout
- identifies the files and primitives to update first
- defines the verification sequence for browser-first testing
- isolates any route-specific follow-up needed after the shared-system layer lands
