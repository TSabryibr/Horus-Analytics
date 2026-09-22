# Home Signal Temple Polish Implementation Plan

Date: 2026-04-22
Based on:

- `docs/superpowers/specs/2026-04-22-home-signal-temple-polish-design.md`
- `frontend/src/app/HomeClientPage.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- `frontend/src/app/components/HomeMetricsBar.tsx`
- `frontend/src/app/components/config/navigation.ts`
- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/sidebar/SidebarNavMenu.tsx`
- `frontend/src/app/components/sidebar/SidebarHeader.tsx`
- `frontend/src/app/page.test.tsx`
- `frontend/src/app/components/HomeShell.test.tsx`
- `frontend/src/app/components/HomeSignalsPanel.test.tsx`
- `frontend/src/app/components/custom/IndustrialNavbar.test.tsx`
- `frontend/e2e/home.spec.ts`
- `frontend/e2e/interactive_controls.spec.ts`
- `frontend/e2e/e2e_crawl.spec.ts`

Track: Home Signal Temple Polish
Status: Executed
Owner model: Single owner

## Execution Outcome

Execution status: Completed across one continuous `Home` polish rollout.

Completed rollout coverage:

- `HSTP-P1` Temple Core composition for `Home`, including posture-driven hero language, stronger primary action hierarchy, and first-viewport flagship framing
- `HSTP-P2` orbit-panel refinement across signal lanes, stewardship state, warnings, and intentional empty-state copy
- `HSTP-P3` mythic-but-disciplined visual system application, including halo atmosphere, lower-orbit telemetry treatment, and aligned shell language
- `HSTP-P4` top-navbar and sidebar hierarchy refresh so `Home` and `Telegram` act as anchors while the rest of the app is grouped into `Intelligence`, `Oversight`, and `System`
- `HSTP-P5` responsive/frontend regression lock across targeted unit coverage, build verification, and route-level Playwright checks

Final verification evidence:

- targeted component coverage passed via:
  - `src/app/page.test.tsx`
  - `src/app/components/HomeShell.test.tsx`
  - `src/app/components/HomeSignalsPanel.test.tsx`
  - `src/app/components/HomeMetricsPanel.test.tsx`
  - `src/app/components/custom/IndustrialNavbar.test.tsx`
  - `src/app/components/sidebar/SidebarNavMenu.test.tsx`
- frontend build: `npm run build` passed
- route E2E: `npm run test:e2e -- home.spec.ts` passed
- broader shell E2E:
  - `npm run test:e2e -- interactive_controls.spec.ts` passed
  - `npm run test:e2e -- e2e_crawl.spec.ts` passed

Residual notes:

- this phase intentionally stops at `Home` and shell hierarchy polish; it does not redesign `Telegram`, `Status`, or `Audit` as flagship surfaces
- workflow behavior, backend contracts, lifecycle logic, and signal-desk authority remain unchanged by this rollout
- `News` and `Sectors` remain informal admin-intelligence surfaces rather than formal signal feeders

## 1. Planning Goal

Transform `Home` into the flagship Horus surface without changing signal-desk behavior:

`signal desk -> Signal Temple hierarchy -> faster operator judgment`

The rollout should:

1. recompose `Home` around a dominant `Temple Core`
2. demote equal-card treatment and create clear orbit hierarchy
3. apply the approved mythic-but-disciplined Horus visual system
4. refresh the upper navbar so `Home` and `Telegram` read as anchors instead of peer tabs
5. preserve responsiveness, operator usefulness, and existing workflow integrity

## 2. In Scope

Primary implementation targets:

- `Home` shell layout and hierarchy
- `Home` signal desk panel presentation
- `Home` hero copy, action emphasis, and empty/warning states
- visual tokens, atmospheric treatments, and selective motion for the flagship surface
- upper-navbar hierarchy refresh for anchor vs grouped destinations
- targeted unit and E2E verification for the polished shell

Primary files expected to move:

- `frontend/src/app/HomeClientPage.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- `frontend/src/app/components/HomeMetricsBar.tsx`
- shared styling seams used by those components
- `frontend/src/app/components/config/navigation.ts`
- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/sidebar/SidebarNavMenu.tsx`
- `frontend/src/app/components/sidebar/SidebarHeader.tsx`
- related tests under `frontend/src/app/**/*.test.tsx`
- route checks under `frontend/e2e/`

Out of scope for this slice:

- backend contract or lifecycle rule changes
- redesigning `Telegram`, `Status`, or `Audit` as flagship pages
- moving `News` or `Sectors` into the formal signal pipeline
- changing route ownership or feature scope
- full-app shell rewrite beyond the targeted navbar hierarchy refresh

## 3. Execution Rules

These rules apply across the rollout:

1. Keep the existing signal-desk workflow intact; this is a polish and hierarchy phase, not a behavior rewrite.
2. `Home` must read as the flagship surface within the first viewport.
3. `Temple Core` remains the dominant focal block; orbit panels support it rather than compete with it.
4. Use mythic Horus atmosphere with restraint; avoid sci-fi HUD styling and generic gold-on-black dashboard treatment.
5. The navbar must reinforce `Home` and `Telegram` as anchors while preserving fast access to the rest of the app.
6. Empty, warning, and blocked states should become more intentional and legible, not noisier.
7. Preserve desktop and mobile usability; premium presentation cannot break scan speed or responsiveness.
8. Land composition and hierarchy changes before decorative refinements.
9. Finish each package with verification so polish does not destabilize the working operator flow.

## 4. Work Package Sequence

Execute in this order:

1. `HSTP-P1` Home composition and Temple Core scaffolding
2. `HSTP-P2` Orbit panels and operator-state polish
3. `HSTP-P3` Visual system, atmosphere, and motion refinement
4. `HSTP-P4` Navbar hierarchy refresh
5. `HSTP-P5` Responsive hardening and regression lock

This order is intentional:

- the flagship page hierarchy must exist before the premium finish can be judged
- orbit content should be reorganized before styling details are tuned
- navbar hierarchy should be adjusted after the new `Home` center of gravity is visible
- verification should lock the integrated shell behavior, not isolated cosmetic fragments

## 5. Work Packages

### HSTP-P1. Home Composition And Temple Core Scaffolding

Purpose:

Recompose `Home` so the first viewport clearly communicates Horus judgment and next action.

Target files:

- `frontend/src/app/HomeClientPage.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/page.test.tsx`
- `frontend/src/app/components/HomeShell.test.tsx`

Tasks:

1. Replace the current header/readiness split with a dominant `Temple Core` composition.
2. Promote market posture, release readiness, operating mode, and primary action into the central hero block.
3. Reduce the visual equality of adjacent metric cards so they read as supporting intelligence rather than peer heroes.
4. Rework the top-of-page content order so the page answers:
   - what Horus sees
   - what should happen next
5. Preserve existing live state wiring and actions such as `Initialize Run` and system check.

Deliverables:

- flagship `Home` hero composition
- stable Temple Core scaffold
- preserved runtime behavior with upgraded visual hierarchy

Verification:

- `npm test -- --runInBand --runTestsByPath src/app/components/HomeShell.test.tsx src/app/page.test.tsx`

Acceptance criteria:

- `Home` no longer reads like a set of equal cards
- the dominant hero explains posture and next action within the first viewport

### HSTP-P2. Orbit Panels And Operator-State Polish

Purpose:

Turn the supporting `Home` content into purposeful left/right/bottom orbits with clearer intervention cues.

Target files:

- `frontend/src/app/components/HomeSignalsPanel.tsx`
- `frontend/src/app/components/HomeMetricsBar.tsx`
- `frontend/src/app/hooks/useHomeRuntime.ts`
- `frontend/src/app/components/HomeSignalsPanel.test.tsx`
- related `Home` runtime tests if needed

Tasks:

1. Reorganize lane, lifecycle, and follow-up content into clearer supporting orbits.
2. Make lane cards show top-candidate context and urgency without needing a click.
3. Elevate warnings such as failed follow-ups, blocked autopilot, stale queues, and ambiguity with cleaner prioritization.
4. Improve empty-state copy so the desk feels watchful and intentional rather than blank.
5. Tighten primary vs secondary actions around the desk panel and release-rail entry point.

Deliverables:

- orbit-based desk presentation
- more decisive operator-state messaging
- clearer signal-lane and follow-up stewardship surfaces

Verification:

- `npm test -- --runInBand --runTestsByPath src/app/components/HomeSignalsPanel.test.tsx src/app/hooks/useHomeRuntime.test.tsx`

Acceptance criteria:

- supporting panels reinforce the Temple Core instead of competing with it
- operator warnings and empty states feel intentional and easier to scan

### HSTP-P3. Visual System, Atmosphere, And Motion Refinement

Purpose:

Apply the approved Horus visual language so the flagship page feels premium and branded instead of merely reorganized.

Target files:

- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- shared styling/token seams used by `Home`
- `frontend/src/app/components/HomeShell.test.tsx`
- visual/behavior checks in `frontend/e2e/home.spec.ts`

Tasks:

1. Introduce the `Signal Temple` visual system:
   - obsidian and charcoal base
   - sandstone haze
   - solar gold and amber emphasis
   - restrained cyan precision accents
2. Add atmospheric treatments such as halo lighting, dimensional surfaces, and subtle celestial linework where appropriate.
3. Refine typography hierarchy for monumental core statements and calmer support copy.
4. Add purposeful, low-noise motion for initial reveal and state changes.
5. Ensure decorative treatments do not obscure data readability or reduce responsiveness.

Deliverables:

- mythic Horus flagship styling
- restrained motion and atmospheric polish
- stronger brand authority on `Home`

Verification:

- `npm test -- --runInBand --runTestsByPath src/app/components/HomeShell.test.tsx src/app/components/HomeSignalsPanel.test.tsx`
- `npm run build --prefix frontend`

Acceptance criteria:

- the page feels premium and authored rather than generic
- styling strengthens clarity instead of distracting from it

### HSTP-P4. Navbar Hierarchy Refresh

Purpose:

Make the upper navbar reinforce `Home` as center of gravity and `Telegram` as the release rail, while grouping the rest into domains.

Target files:

- `frontend/src/app/components/config/navigation.ts`
- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/sidebar/SidebarNavMenu.tsx`
- `frontend/src/app/components/sidebar/SidebarHeader.tsx`
- `frontend/src/app/components/custom/IndustrialNavbar.test.tsx`

Tasks:

1. Refactor route metadata so `Home` and `Telegram` remain anchors and the rest can be presented as grouped domains.
2. Introduce grouped hierarchy for:
   - `Intelligence`
   - `Oversight`
   - `System`
3. Reduce the equal-tab feel in the upper bar through composition, labeling, and emphasis.
4. Make `Home` feel like the crest/throne of the navbar and `Telegram` the outbound rail.
5. Preserve accessibility and fast route access on desktop and mobile/sidebar navigation.

Deliverables:

- hierarchy-aware route model
- polished top navbar emphasizing anchors over tab sprawl
- aligned sidebar/menu presentation if needed

Verification:

- `npm test -- --runInBand --runTestsByPath src/app/components/custom/IndustrialNavbar.test.tsx`

Acceptance criteria:

- the navbar stops presenting every route as an equal flagship destination
- `Home` and `Telegram` read as anchors while grouped routes remain easy to reach

### HSTP-P5. Responsive Hardening And Regression Lock

Purpose:

Verify that the flagship polish survives real use across desktop, mobile, and shell navigation.

Target files:

- `frontend/src/app/page.test.tsx`
- `frontend/src/app/components/HomeShell.test.tsx`
- `frontend/src/app/components/HomeSignalsPanel.test.tsx`
- `frontend/src/app/components/custom/IndustrialNavbar.test.tsx`
- `frontend/e2e/home.spec.ts`
- `frontend/e2e/interactive_controls.spec.ts`
- `frontend/e2e/e2e_crawl.spec.ts`

Tasks:

1. Update component tests for the new hierarchy, copy, and actions.
2. Refresh route-level checks so the new `Home` and navbar behavior are locked.
3. Run frontend build and route E2E validation.
4. Fix any responsive regressions introduced by the new hero and grouped navbar layout.
5. Capture any residual warnings worth deferring explicitly.

Deliverables:

- green component and route checks for the polished shell
- mobile-safe and desktop-safe flagship `Home`

Verification:

- `npm test -- --runInBand --runTestsByPath src/app/page.test.tsx src/app/components/HomeShell.test.tsx src/app/components/HomeSignalsPanel.test.tsx src/app/components/custom/IndustrialNavbar.test.tsx`
- `npm run build --prefix frontend`
- `npm run test:e2e -- home.spec.ts interactive_controls.spec.ts e2e_crawl.spec.ts`

Acceptance criteria:

- the polished `Home` and navbar pass targeted tests and route checks
- the flagship presentation remains usable on both desktop and mobile

## 6. Recommended First Slice

Start with:

- `HSTP-P1` Home composition and Temple Core scaffolding
- `HSTP-P4` navbar hierarchy modeling only where it unblocks the new Home header composition

Why:

- the biggest value comes from changing first impression and center of gravity immediately
- navbar hierarchy can begin in parallel at the route-metadata level without waiting for all visual polish
- once the new flagship composition exists, the later visual pass has a stable structure to refine

## 7. Final Verification Target

Before closing the track, the rollout should have:

- targeted component coverage for `Home` and the navbar
- successful frontend production build
- route E2E coverage for `Home` and navigation flow
- a final manual smoke check that `Home` feels like the unquestioned flagship surface and the navbar no longer reads as isolated tabs
