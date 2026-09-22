# Home Signal Desk And Autopilot Pipeline Design

Date: 2026-04-21
Status: Approved design for planning
Authoring mode: Brainstorming-approved design

Based on:

- `frontend/src/app/HomeClientPage.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/hooks/useHomeRuntime.ts`
- `frontend/src/app/hooks/useHomeActions.ts`
- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/components/TelegramShell.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`
- `frontend/src/app/telegram/hooks/useTelegramBroadcasts.ts`
- `frontend/src/app/components/config/navigation.ts`
- `frontend/src/app/scanner/page.tsx`
- `frontend/src/app/scanner/components/ScannerShell.tsx`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/components/OracleShell.tsx`
- `frontend/src/app/context/GlobalDataContext.tsx`
- `routes/scanner.py`
- `routes/settings.py`
- `routes/system.py`

## 1. Purpose

This design re-centers Horus around its actual product purpose: generating and selling Telegram trading signals rather than behaving like a collection of unrelated analysis tabs.

The goal is to turn the app into one coherent editorial publishing machine:

- analysis modules discover and validate signal ideas
- `Home` becomes the daily signal desk
- `AI Assist` and `Autopilot` help compose release-ready batches
- `Telegram` becomes the outbound release rail

The approved direction is a `Home-centered signal pipeline` with full `Autopilot` authority under policy guardrails.

## 2. Problem Summary

The current frontend already has a shared shell, but the product still feels fragmented.

Today:

- major routes read as peer destinations instead of one operating loop
- `Home` is still dashboard-heavy rather than queue-heavy
- analysis tabs such as Scanner and Oracle generate insight but do not clearly hand off into the next action
- `Telegram` behaves like a separate command center instead of the outbound end of a shared pipeline
- the app does not visibly communicate one central object such as a publish queue or signal batch
- automation is expressed through scattered `auto_*` toggles rather than one explicit operating model
- signal horizons are not elevated into first-class product lanes

This creates the exact product feeling the user described:

- every tab appears top-level
- analysis does not naturally convert into action
- the app feels like isolated islands instead of one business system

## 3. Goal

Introduce one coherent operating workflow where Horus behaves like a signal newsroom and release engine.

This design is successful when:

1. `Home` is the primary daily mission-control surface
2. specialist routes feed one shared signal pipeline instead of acting as isolated endpoints
3. `Telegram` is the outbound release rail rather than the place where signals are invented
4. Horus supports three official signal products: `Intraday`, `Swing`, and `Position`
5. `Manual`, `AI Assist`, and `Autopilot` are visible operating modes inside the same pipeline
6. `Autopilot` can publish directly through `AI Assist` when the admin is busy
7. client-facing Telegram messages remain branded only as `Horus`, while internal provenance stays private to operators

## 4. Non-Goals

This design does not include:

- rewriting all analysis engines from scratch
- removing specialist pages such as Scanner, Oracle, Whales, or Traps
- exposing internal provenance or automation labels to Telegram clients
- replacing every existing backend broadcast path in one immediate rewrite
- flattening every page into the same layout regardless of function
- changing the business identity of Horus into a portfolio-first or auto-trading-first product

## 5. Recommended Approach

Three approaches were considered.

### Option A. Home-centered editorial signal desk

Turn `Home` into the daily signal desk, keep analysis modules as feeder lanes, and make `Telegram` the release rail.

Pros:

- creates one clear center of gravity
- solves the "everything feels top-level" problem
- lets specialist tabs stay specialized
- matches the user's approved direction for `Home`
- supports `AI Assist` and `Autopilot` naturally

Cons:

- requires a meaningful shift in `Home` from dashboard metrics to queue operations
- requires stronger shared pipeline objects across frontend and backend

Recommended.

### Option B. Telegram-centered publish hub

Make `Telegram` the main queue and batch-composition surface while other routes feed into it directly.

Pros:

- very explicit about the business destination
- simple mental model for outbound publishing

Cons:

- overloads the Telegram route
- weakens `Home`
- risks making the product feel like "Telegram tools plus other tabs"

Reject for this project.

### Option C. Lightweight handoff improvements only

Keep the existing route hierarchy but add more cross-route buttons and "add to batch" affordances.

Pros:

- smallest immediate change set
- least disruptive

Cons:

- does not truly solve the missing center of gravity
- leaves the equal-tab problem mostly intact
- likely preserves the "isolated islands" feeling

Reject for this project.

## 6. Design Principles

The new signal system should follow these rules:

- One operating loop. The app should read as `discover -> validate -> compose -> publish -> track`, not as disconnected modules.
- Home owns editorial gravity. The primary daily workflow belongs to `Home`.
- Specialist lanes stay specialized. Scanner, Oracle, Whales, Traps, News, and similar routes should feed the desk rather than become mini-products.
- Horizon-first organization. `Intraday`, `Swing`, and `Position` are separate product lanes, not cosmetic labels.
- Explicit operating modes. `Manual`, `AI Assist`, and `Autopilot` must be visible system states.
- Publish-safe autonomy. `Autopilot` may publish directly, but only through policy-gated workflow.
- Single public voice. Client-facing messages come from `Horus` only, regardless of internal mode.
- Internal traceability only. Mode, provenance, and policy decisions remain visible to operators and audits, never to clients.

## 7. Product Backbone

The approved product loop is:

`feeder analysis -> signal candidate -> Daily Signal Desk -> AI-assisted batch composition -> Telegram dispatch -> outcome tracking`

This is a shift from the current implied loop of:

`open page -> analyze something -> maybe manually decide what to do next`

The central product object is no longer a page-specific view or standalone scanner result.

The central product object becomes:

- a `Signal Candidate`
- promoted into a lane-specific `Publish Batch`
- released through a policy-governed `Telegram` pipeline

## 8. Route Responsibility Model

The route hierarchy should visibly communicate one product system.

### 8.1 Primary anchor routes

- `Home`: the `Daily Signal Desk`
- `Telegram`: the `Release Rail`

These are the two anchor destinations in the shell.

### 8.2 Feeder lanes

These routes generate or strengthen signal candidates:

- `Scanner`
- `Oracle`
- `Whales`
- `Traps`
- `News`
- `Sectors`
- `Analytics`

Each feeder lane should expose an obvious handoff into the desk rather than leaving the operator to mentally bridge the next step.

### 8.3 Support lanes

These routes support validation, refinement, or post-hoc reasoning:

- `Strategy`
- `Optimization`
- `Simulation`
- `Reports`
- `Audit`

### 8.4 Utility lanes

These routes support platform operation rather than editorial composition:

- `Portfolio`
- `Settings`
- `Status`

### 8.5 Navigation hierarchy

The shell should stop presenting the route ribbon as a list of equal peers.

The navigation should visibly privilege:

- `Home` as the editorial center
- `Telegram` as the outbound destination

The remaining routes should read as grouped lane types rather than top-level products competing for attention.

At a minimum, the command ribbon should communicate:

- anchor destinations
- feeder lanes
- support lanes
- utility lanes

The goal is not to hide routes. The goal is to stop the product from reading like eighteen unrelated tools.

## 9. Canonical Domain Model

The app needs one shared editorial vocabulary.

### 9.1 Signal Candidate

A `Signal Candidate` is the internal object produced or promoted by feeder modules.

It should include:

- ticker or asset
- direction or action bias
- `signal_type`: `INTRADAY`, `SWING`, or `POSITION`
- entry zone
- stop loss
- targets
- confidence
- rationale
- source module
- ranking score
- readiness state

### 9.2 Publish Batch

A `Publish Batch` is the curated release unit assembled on `Home`.

It should include:

- lane type
- ordered candidates
- channel target
- draft release copy
- publish mode
- release status
- scheduled or immediate dispatch metadata

### 9.3 Publish Policy

A `Publish Policy` is the rule set used by `AI Assist` and `Autopilot`.

It should include:

- minimum confidence threshold
- source-module allowlist
- duplicate suppression rules
- batch size limits
- quiet hours
- send windows
- blocking rules for missing fields or weak rationale

### 9.4 Operating Mode

The system should expose one shared `Operating Mode` state:

- `MANUAL`
- `AI_ASSIST`
- `AUTOPILOT`

This state should be visible from `Home` and `Telegram`, and available to backend status surfaces where appropriate.

## 10. Home As The Daily Signal Desk

`Home` should stop acting mainly as a dashboard and become the main editorial workspace.

The approved desk structure is:

- `Intraday Lane`
- `Swing Lane`
- `Position Lane`

Each lane is a separate working stream with its own:

- candidate intake
- ranking logic
- batch composition
- readiness checks
- publish controls

### 10.1 Lane structure

Each lane should expose three working zones:

- `Ranked Intake`: what Horus proposed from feeder routes
- `Batch Composer`: what is being curated for release
- `Release Readiness`: policy, completeness, and duplication checks

### 10.2 Lane behavior

`Intraday` lane:

- prioritizes freshness and session timing
- uses the fastest ranking and release cadence
- should be the most time-sensitive lane

`Swing` lane:

- prioritizes stronger confirmation and multi-session structure
- likely becomes the most frequent curated lane
- balances speed with selectivity

`Position` lane:

- uses the strictest selectivity
- carries the richest rationale expectations
- releases less frequently and with higher conviction thresholds

### 10.3 Home responsibilities

`Home` should visibly show:

- active operating mode
- lane health
- queue depth
- publish readiness
- Autopilot armed state
- failed outbound or blocked candidates needing attention

## 11. AI Assist And Autopilot

Horus should support three explicit operating modes inside the same pipeline.

### 11.1 Manual

The admin:

- reviews candidates
- edits batches
- publishes directly

### 11.2 AI Assist

Horus:

- ranks candidates
- drafts batches
- drafts Telegram copy
- supports editorial choice

But it does not publish on its own.

### 11.3 Autopilot

When the admin is busy, Horus uses `AI Assist` as the publishing engine:

- assembles the batch
- generates the release copy
- sends it directly without waiting for admin approval

This means `Autopilot` is not a separate intelligence stack.

It is `AI Assist` with delegated publish authority under policy.

### 11.4 Visibility and control

Autopilot must not feel like a hidden background trick.

The app should visibly communicate:

- current mode
- whether Autopilot is armed
- queue or lane health
- whether publish authority is delegated

The system must also support:

- emergency kill switch
- instant downgrade from `AUTOPILOT` to `AI_ASSIST` or `MANUAL`

## 12. Telegram As The Release Rail

`Telegram` should stop acting like an independent signal authoring island.

Its primary role should become:

- receive finalized or autopilot-authorized batches
- format dispatch output
- choose target channel
- send or schedule release
- display internal delivery history and failure states

### 12.1 Route role

`Telegram` remains important, but it is downstream of `Home`.

It should no longer be the place where the main signal idea is manually invented from scratch.

### 12.2 Client-facing output

Outgoing Telegram messages should present one consistent public identity:

- `Horus`

Client-facing messages should not expose:

- whether the admin sent it
- whether AI Assist drafted it
- whether Autopilot published it

### 12.3 Internal logs

Internal operator surfaces should still retain:

- mode used
- policy decision
- dispatch result
- retry status
- failure reason

This information belongs in internal logs and audit views only.

## 13. Feeder Integration Rules

Specialist routes should contribute into the desk rather than terminate in isolation.

### 13.1 Required handoff behavior

Each feeder route should support a clear action such as:

- `Add to Intraday Lane`
- `Add to Swing Lane`
- `Add to Position Lane`
- `Promote to Daily Signal Desk`

The operator should never have to guess where an insight goes next.

### 13.2 Feeder examples

`Scanner`:

- strong source of ranked tactical candidates
- current direct broadcast behavior should be demoted behind the new shared policy path

`Oracle`:

- strong source of deeper validation, rationale, and price-structure support
- should be able to strengthen or promote candidates into the appropriate lane

`Whales`, `Traps`, `News`, and similar routes:

- should act as candidate enrichers or filters
- should be able to support lane-specific confidence and rationale

## 14. Policy, Failures, And Safety

Because `Autopilot` has full publish authority, the system must fail safely.

### 14.1 Required policy controls

Autopilot and AI Assist should operate behind policy such as:

- minimum confidence threshold
- source allowlist
- duplicate and overlap suppression
- lane-specific batch size limits
- quiet hours and release windows
- channel targeting rules
- blockers for missing fields
- blockers for weak rationale

### 14.2 Publish failure handling

If Telegram delivery fails:

- the batch moves to `failed outbound`
- the batch remains visible on `Home`
- the operator can retry from `Telegram` without rebuilding the batch

If AI Assist cannot produce acceptable release copy:

- the system either blocks publish or falls back to a safe structured template according to policy

If a candidate is incomplete:

- it stays in a blocked or needs-review state
- it never silently enters the outgoing batch

### 14.3 Deduplication boundary

Deduplication should occur at the batch and candidate pipeline level, not only inside route-local broadcast helpers.

This prevents multiple direct paths from republishing the same idea.

## 15. Current-System Alignment

This design should evolve from the current code rather than ignore it.

### 15.1 Home

Current state:

- `HomeClientPage.tsx` is dashboard-heavy
- `useHomeRuntime.ts` is dashboard-data oriented
- `useHomeActions.ts` currently triggers scan-oriented commands

Required shift:

- make `Home` queue-oriented
- make actions lane and batch oriented
- retain useful telemetry, but subordinate it to editorial workflow

### 15.2 Telegram

Current state:

- `telegram/page.tsx` contains direct broadcast tools
- `useTelegramBroadcasts.ts` is action-first
- `TelegramSignalPanel.tsx` emphasizes local broadcast triggers

Required shift:

- make Telegram dispatch-first
- accept finalized batches from the desk
- preserve config, channel, and log surfaces

### 15.3 Existing auto-broadcast settings

Current state:

- `routes/settings.py` and Telegram config currently expose scattered toggles such as:
  - `auto_intraday`
  - `auto_daily`
  - `auto_horus_eye`
  - `auto_ai_daily_report`
  - `auto_weekly_report`
  - `auto_monthly_report`

Required shift:

- consolidate these into one explicit `Publish Policy` and `Operating Mode` model
- preserve backward-compatible migration where needed

### 15.4 Existing scanner auto-broadcast flow

Current state:

- `routes/scanner.py` can directly auto-broadcast detected signals

Required shift:

- route signals through the shared candidate and batch pipeline
- keep lane-aware publish policy above route-local broadcast behavior

### 15.5 System status integration

`routes/system.py` already serializes system and Telegram status.

This design should extend the system surface so operator status can eventually expose:

- current operating mode
- Autopilot armed state
- queue health summary
- publish-blocked state when relevant

### 15.6 Shared data-loading model

`GlobalDataContext.tsx` currently resolves route-specific stream policy mainly around dashboard, news, market, and live data.

This design implies a new desk-oriented loading model where `Home` can request:

- lane summaries
- candidate queue state
- publish readiness
- operating-mode state
- failed outbound state

without pretending those are just dashboard metrics.

That means planning should treat desk state as its own shared domain rather than forcing it into the current dashboard-only path.

## 16. Testing Strategy

The implementation should be verified across frontend workflow, backend policy, and end-to-end publish behavior.

### 16.1 Frontend

Add tests for:

- `Home` rendering three separate lanes
- lane-specific candidate and batch behavior
- visible operating mode state
- explicit feeder handoff actions from key routes
- `Telegram` consuming batch-driven dispatch state rather than only local manual form state

### 16.2 Backend

Add tests for:

- candidate classification into `INTRADAY`, `SWING`, and `POSITION`
- policy gating for `AI Assist` and `Autopilot`
- direct Autopilot publish flow
- failure-to-retry behavior for outbound dispatch
- deduplication across candidate and batch stages
- safe blocking for incomplete or weak candidates

### 16.3 End-to-end acceptance

The system should be validated with workflow tests such as:

- feeder module creates candidate
- candidate appears in correct lane on `Home`
- AI Assist drafts release copy
- Autopilot publishes directly when armed and policy allows
- Telegram history records the internal dispatch outcome
- client-facing output contains only `Horus` branding

## 17. Acceptance Criteria

This design is complete when:

1. `Home` is the primary `Daily Signal Desk`
2. the app visibly revolves around one publish pipeline rather than equal top-level tabs
3. feeder routes hand off into the desk instead of ending in isolation
4. `Intraday`, `Swing`, and `Position` exist as separate first-class lanes
5. `Manual`, `AI Assist`, and `Autopilot` are explicit system modes
6. `Autopilot` can use `AI Assist` to publish directly without waiting for admin approval
7. `Telegram` acts as the release rail for finalized batches
8. client-facing messages expose only the `Horus` brand, not internal provenance
9. internal logs and audits still retain mode and dispatch traceability

## 18. Risks And Guardrails

### 18.1 Main risks

The primary risks are:

- leaving old direct broadcast paths alive alongside the new batch pipeline
- redesigning `Home` visually without truly giving it editorial authority
- mixing signal horizons into one pool and losing the lane distinction
- giving `Autopilot` authority without strong enough blocking policy

### 18.2 Guardrails

To control those risks:

- treat `Home` as the single editorial center
- keep `Telegram` downstream of batch composition
- require every candidate to declare `INTRADAY`, `SWING`, or `POSITION`
- enforce policy before direct publish
- keep internal traceability while hiding provenance from clients
- verify lane, policy, and dispatch behavior together instead of only per route

## 19. Implementation Boundary

This document defines the approved design only.

The next step is an implementation plan that:

- stages the `Home` transformation into the Daily Signal Desk
- defines the shared candidate, batch, mode, and policy model
- maps feeder-route integration points
- restructures Telegram around dispatch-first flow
- consolidates scattered automation toggles into one operating model
- defines verification for lane behavior, AI Assist, and Autopilot publishing
