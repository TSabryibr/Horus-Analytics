# Home Signal Temple Polish Design

Date: 2026-04-22
Status: Proposed

## Objective

Elevate `Home` from a competent operations dashboard into the flagship Horus surface: a premium, mythic, clarity-first mission-control page that immediately communicates what Horus sees and what should happen next.

This is a polish phase, not a workflow rewrite. The underlying signal-desk architecture stays intact:

- `Home` remains the central signal desk
- `Telegram` remains the release and follow-up rail
- lifecycle, autopilot, and lane logic stay as implemented

The goal is to improve visual hierarchy, brand authority, and operator comprehension so the page feels like the true center of the product.

## Design Direction

The approved direction is:

- flagship surface: `Home`
- premium priority: showcase-first
- primary concept: `Signal Temple`
- tone: mythic `Horus`
- emotional priority: `clarity`
- density: `balanced tableau`

This means the page should feel iconic and ceremonial without becoming theatrical noise, and operational without looking like a generic finance dashboard.

## Section 1: Signal Temple Concept

`Home` should become a `Signal Temple`: a mythic mission-control surface where Horus appears to see the market clearly, rank what matters, and present the next release decision with authority.

Core composition:

- the page centers around one dominant `Temple Core` panel
- that core panel is the "truth block" for the day:
  - market posture
  - release readiness
  - top conviction batch
  - current operating mode
- surrounding it are supporting panels, not equal competitors:
  - left side: signal lanes
  - right side: lifecycle and follow-up posture
  - lower band: recent movement, batch health, and operator actions

Visual character:

- the tone is mythic and ceremonial, not military
- the atmosphere should feel like `Horus sees the field`, not `ops center under attack`
- use radiant gold, solar amber, obsidian, sandstone haze, and disciplined cyan only as a precision accent
- typography should feel monumental and branded, not generic SaaS

Hierarchy rule:

- one panel must clearly feel like the sacred center
- the rest of the page should look like orbiting intelligence around that center
- no more "all cards are equal"

Instead of reading like `dashboard widgets`, `Home` should feel like the sanctum where Horus interprets the market and prepares release.

## Section 2: Temple Core

The `Temple Core` should answer one question immediately:

`What does Horus see, and what should happen next?`

Recommended contents:

- a large market posture statement
  - examples:
    - `Bullish Expansion`
    - `Selective Risk`
    - `Defensive Rotation`
- a conviction summary
  - how many signals are ready
  - how they are distributed across `Intraday`, `Swing`, and `Position`
- the primary release call
  - `Release Batch`
  - `Review Queue`
  - `Autopilot Watching`
  - `Follow-Ups Pending`
- current operating mode
  - `Manual`
  - `AI Assist`
  - `Autopilot`

Layout behavior:

- the posture statement is the biggest text on the screen
- the primary release action is visually anchored near the core, not buried in a lower panel
- the mode badge feels important but secondary to market clarity
- confidence and readiness indicators are visible at a glance

The intended emotional effect is that the admin feels Horus has already interpreted the noise. The page presents judgment, not just metrics.

## Section 3: Orbit Panels

The supporting panels should behave like `orbits` around the Temple Core, each with one clear purpose.

Recommended orbit structure:

- `Left Orbit: Signal Lanes`
  - `Intraday`
  - `Swing`
  - `Position`
  - each shows ready count, top ticker, and urgency
  - answers: `where is today's opportunity concentrated?`

- `Right Orbit: Lifecycle + Follow-Ups`
  - active published signals
  - `TP1` / `TP2` / `SL` / `Expired`
  - pending follow-ups
  - failed follow-ups
  - answers: `what still needs stewardship after release?`

- `Lower Orbit: Release and Flow Health`
  - batch health
  - autopilot readiness
  - delivery failures
  - stale or blocked items
  - answers: `is the machine flowing cleanly?`

Important rule:

- orbit panels should not visually overpower the center
- they should feel like trusted satellites feeding and protecting the core judgment
- each orbit should use a different emphasis:
  - lanes = opportunity
  - lifecycle = stewardship
  - flow health = system confidence

The page story becomes:

- center: `what Horus sees`
- left: `where opportunity lives`
- right: `what published signals are doing`
- bottom: `whether the release machine is healthy`

## Section 4: Visual Language

The visual language should feel premium and branded without collapsing into fantasy UI.

Palette:

- base:
  - obsidian black
  - deep charcoal
  - warm sandstone smoke
- primary highlights:
  - solar gold
  - muted amber
- precision accent:
  - restrained cyan for data emphasis, not mood
- danger and warning:
  - ember red, used sparingly

Textures and atmosphere:

- subtle radial light behind the Temple Core, like a solar halo
- layered shadow and haze, not glossy neon
- faint geometric linework or etched grid motifs inspired by celestial mapping
- very little flat empty black; surfaces should feel authored and dimensional

Typography:

- expressive headline treatment for core titles and posture statements
- restrained but elegant supporting typography for panel content
- avoid a generic `Inter-only` feel if the current stack can support a more distinctive pairing

Motion:

- slow reveal of the halo and orbit panels on load
- gentle stagger as signals appear
- meaningful state transitions for mode and readiness changes
- avoid noisy glow pulses and sci-fi gimmicks

Target feeling:

- `premium intelligence sanctum`

Avoid:

- `sci-fi game HUD`
- `ordinary enterprise dashboard with gold paint`

## Section 5: Operator Usefulness

This polish pass should improve operator usefulness while making `Home` feel premium, not trade usefulness for style.

Recommended behavioral upgrades:

- primary actions become fewer and clearer
  - one dominant call near the Temple Core
  - a small number of secondary actions beside or beneath it
- empty states should feel intentional
  - not "nothing here"
  - more like `Horus is watching, no qualified release yet`
- warnings should be elevated elegantly:
  - failed follow-ups
  - blocked autopilot
  - ambiguous lifecycle states
  - stale signal inputs
- lane cards should show top candidate information without forcing a click
- the lifecycle side should surface what actually needs intervention now

Desired operator outcome:

- within a few seconds, admin should know:
  - current market posture
  - whether a release is justified
  - where the strongest opportunities are
  - whether published signals need follow-up attention
  - whether Autopilot is safe, blocked, or irrelevant right now

This pass should be measured by:

- stronger first impression
- clearer next action
- faster operator comprehension
- more brand authority

## Section 6: Home-Led Navbar Hierarchy

The upper navbar should stop acting like a row of equal product tabs.

If `Home` becomes the `Signal Temple`, the top bar needs to support that hierarchy instead of flattening it.

Recommended direction:

- keep `Home` as the visual anchor
- keep `Telegram` as the second anchor because it is the release rail
- demote the rest out of equal-tab treatment

Recommended structure:

- `Home`
- `Telegram`
- `Intelligence`
  - `Scanner`
  - `Oracle`
  - `Whales`
  - `Traps`
  - `Analytics`
- `Oversight`
  - `Status`
  - `Audit`
  - `Reports`
- `System`
  - `Portfolio`
  - `Settings`

Navbar behavior goals:

- `Home` should read like the throne or crest in the navbar
- `Telegram` should feel like the active outbound rail
- grouped destinations should feel like domains, not peer flagship pages
- the upper bar should become more ceremonial and branded, with fewer loud labels

This is a `Home-led navbar hierarchy refresh`, not a full shell rewrite.

## Non-Goals

This phase does not:

- redesign the full app shell beyond the targeted navbar hierarchy refresh
- rewrite `Telegram`, `Status`, or `Audit` as flagship surfaces
- change signal desk workflows or backend behavior
- move `News` or `Sectors` into the formal signal pipeline

Those surfaces may get future polish passes, but this spec is specifically about making `Home` the unmistakable center of gravity.

## Recommended Implementation Focus

The implementation should prioritize:

1. recompose `Home` around the `Temple Core`
2. reduce card equality and strengthen hierarchy
3. apply the new mythic-but-disciplined visual system
4. refresh the upper navbar so `Home` and `Telegram` read as anchors instead of equal peers
5. tighten action emphasis and empty/warning states
6. preserve responsiveness and operator speed on desktop and mobile

## Success Criteria

The polish phase is successful when:

- `Home` immediately reads as the flagship Horus page
- the page feels premium and branded rather than generic
- the admin can identify the current market posture and next action within seconds
- lane, lifecycle, and flow-health information support the center instead of competing with it
- the upper navbar reinforces `Home` as the center of gravity instead of a peer tab in a crowded ribbon
- the design remains operationally useful, not just visually impressive
