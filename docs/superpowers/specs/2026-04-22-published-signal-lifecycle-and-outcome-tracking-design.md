# Published Signal Lifecycle And Outcome Tracking Design

Date: 2026-04-22
Status: Approved design for planning
Authoring mode: Brainstorming-approved design

Based on:

- `database.py`
- `routes/signals.py`
- `routes/analysis_reports.py`
- `core/signals/outcomes.py`
- `core/signals/runs.py`
- `core/horus/executor.py`
- `core/horus/monitor.py`
- `core/horus/telegram.py`
- `frontend/src/app/HomeClientPage.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`
- `frontend/src/app/telegram/components/TelegramStatusCard.tsx`
- `frontend/src/app/audit/**`
- `frontend/src/app/status/**`

## 1. Purpose

This design adds the missing layer after signal publication:

`publish -> monitor -> resolve -> score`

Horus already has a stronger unified flow for:

`analysis -> desk -> release`

What it still lacks is a formal, trustworthy answer to:

- what happened after Horus published the signal
- whether the signal actually filled
- whether it hit `TP1`, `TP2`, stop loss, or expired
- how published Horus signals performed over time

The goal of this design is to introduce a dedicated lifecycle authority for published Horus signals only, then derive trusted internal outcome and scoring data from that lifecycle.

## 2. Problem Summary

The current codebase already contains useful pieces, but not one clean lifecycle authority.

Today:

- `SignalRecommendation` stores the analysis recommendation
- `SignalDelivery` stores whether a signal run was delivered
- `SignalOutcome` stores historical outcome summaries
- `HorusExecution` stores portfolio or execution-oriented state such as `OPEN`, `UPDATED`, and `CLOSED`
- Horus execution monitoring already checks stop and target behavior for internal portfolio operations

But the product now needs a different truth boundary:

- only signals actually published by `Horus` should count toward the formal lifecycle and track record
- published client signals are not the same thing as internal research outcomes
- published client signals are also not the same thing as internal execution objects tied to portfolio behavior

Without a dedicated lifecycle layer, the system risks:

- overstating fills by treating publication as entry
- mixing unpublished research ideas into the commercial score base
- coupling client signal truth too tightly to portfolio execution internals
- making Telegram follow-up automation and performance reporting harder to trust

## 3. Goal

This design is successful when:

1. only published Horus signals enter the formal lifecycle
2. a signal becomes `OPEN` only after market price actually reaches entry
3. Horus automatically tracks `TP1`, `TP2`, stop loss, and expiry with admin override support
4. `TP1` automatically moves the active stop to breakeven
5. all lifecycle transitions are internally auditable
6. `SignalOutcome` and reporting are derived from lifecycle closure rather than acting as the live authority
7. client-facing Telegram content stays branded as `Horus` and remains free of internal provenance

## 4. Non-Goals

This phase does not include:

- Telegram follow-up template redesign as its own feature slice
- public client exposure of lifecycle internals or automation provenance
- track-record marketing pages for clients
- reworking unpublished analysis routes into lifecycle participants
- making `News` or `Sectors` part of the formal signal lifecycle
- redesigning Horus portfolio auto-trading around the new lifecycle model

## 5. Recommended Approach

Three approaches were considered.

### Option A. Extend `SignalOutcome` into the live lifecycle authority

Pros:

- smallest additive schema change
- reuses current outcomes and analytics surfaces

Cons:

- mixes live state tracking with historical summary
- becomes awkward once `PUBLISHED`, `TP1_HIT`, expiry, ambiguity, and overrides are added
- weak separation between lifecycle truth and reporting projection

Reject.

### Option B. Extend `HorusExecution` into the lifecycle authority

Pros:

- already has open and close behavior
- already tracks stop and target fields plus message ids

Cons:

- too tied to internal execution and portfolio behavior
- not a clean source of truth for published client signal lifecycle
- risks conflating "client signal state" with "internal execution state"

Reject.

### Option C. Add a dedicated published-signal lifecycle authority

Pros:

- cleanly models the commercial product boundary
- isolates published client signal truth from internal research and internal execution
- supports follow-up automation, admin overrides, and reporting without twisting existing models

Cons:

- requires a new persistence seam and supporting APIs
- needs careful integration with existing publish and outcome paths

Recommended.

## 6. Design Principles

The lifecycle system should follow these rules:

- Published-only truth. Only signals actually published by `Horus` enter the formal lifecycle.
- Honest fill boundary. Publication is not the same as entry.
- State machine first. Lifecycle should be expressed as an explicit transition model, not scattered status flags.
- Auto first, admin corrects. Horus should auto-detect lifecycle transitions, while the admin retains override authority.
- Outcome is derived. Reporting and scoring should be derived from lifecycle closure, not treated as the live authority.
- Public simplicity, private traceability. Telegram clients see Horus signals and updates; operators see the internal mechanics.
- Lane-aware expiry. `Intraday`, `Swing`, and `Position` use different expiry windows.
- Conservative ambiguity handling. When bar sequencing is unknowable, Horus should not overstate results.

## 7. Product Boundary

The formal lifecycle applies only to:

- signals actually published to Telegram by `Horus`

It does not apply to:

- unpublished desk candidates
- research-only scanner or oracle outputs
- admin-only intelligence from `News` or `Sectors`
- rejected or blocked candidates that never reached Telegram

This creates a clean business rule:

the formal track record answers

`How did Horus signals perform after clients actually received them?`

not

`How did all internal ideas perform in research?`

## 8. Canonical Domain Model

The lifecycle layer should introduce two dedicated objects.

### 8.1 Published Signal Lifecycle

Recommended canonical name:

- `PublishedSignalLifecycle`

This is the live authority for a published Horus signal.

Recommended fields:

- `recommendation_id`
- `run_id`
- `delivery_id`
- `ticker`
- `side`
- `lane`
- `source_module`
- `operating_mode`
- `channel`
- `published_message_id`
- `state`
- `resolution_source`
- `published_at`
- `expires_at`
- `opened_at`
- `tp1_hit_at`
- `closed_at`
- `entry_price_planned`
- `entry_price_filled`
- `stop_loss_initial`
- `stop_loss_active`
- `target_price_1`
- `target_price_2`
- `close_price`
- `close_reason`
- `override_notes`
- `last_market_event_at`
- `details_json`

### 8.2 Published Signal Lifecycle Event

Recommended canonical name:

- `PublishedSignalLifecycleEvent`

This is the append-only internal event log for transitions and overrides.

Recommended fields:

- `lifecycle_id`
- `event_type`
- `from_state`
- `to_state`
- `event_source`
- `event_time`
- `price_context_json`
- `notes`
- `actor`

Examples:

- `published`
- `opened`
- `tp1_hit`
- `stop_moved_to_breakeven`
- `tp2_hit`
- `stop_loss_hit`
- `expired`
- `cancelled`
- `admin_override`
- `ambiguous_bar_detected`

## 9. Lifecycle State Machine

The lifecycle should be modeled as a published-signal state machine.

Recommended flow:

- `PUBLISHED`
  - Horus sent the signal to Telegram
  - the signal is now formally tracked
  - it is not yet considered filled
- `OPEN`
  - market price actually reached the planned entry level or entry zone
  - this is the first live-trade state
- `TP1_HIT`
  - first target was reached
  - stop automatically moves to breakeven
  - the signal remains active while Horus tracks the path to `TP2`

Recommended terminal states:

- `TP2_HIT`
- `STOP_LOSS_HIT`
- `EXPIRED`
- `CANCELLED`

Supporting internal resolution state:

- `AMBIGUOUS`

`AMBIGUOUS` should be internal-only and used when the system cannot defensibly determine intrabar sequencing. It should not be treated as a client-facing lifecycle state, but as an operator review state.

## 10. Lifecycle Components

The lifecycle engine should run as a small coordinated pipeline.

### 10.1 Lifecycle Publisher Hook

Runs immediately after a successful Telegram publish and:

- creates the `PublishedSignalLifecycle` record
- connects it to the published delivery and recommendation
- sets lane, expiry, entry, stop, `TP1`, `TP2`, and initial state `PUBLISHED`

### 10.2 Lifecycle Monitor Job

Runs on a schedule and:

- checks latest market data against active lifecycle records
- advances records through `PUBLISHED -> OPEN -> TP1_HIT -> terminal state`
- applies the `TP1 -> breakeven stop` rule
- raises `AMBIGUOUS` when bar sequencing cannot be trusted

### 10.3 Lifecycle Event Log

Records every transition and override as an internal event stream.

This becomes the audit trail for:

- trust
- debugging
- policy review
- later follow-up message automation

### 10.4 Admin Override Surface

Allows the admin to:

- force open
- correct fill price
- mark `TP1`
- mark `TP2`
- mark stop hit
- cancel signal
- reopen if Horus misclassified it

Every override writes an event. It must not silently mutate state.

### 10.5 Outcome Projector

Converts terminal lifecycle states into the summarized outcome layer used by reporting and calibration.

This keeps:

- lifecycle as the live truth
- `SignalOutcome` as the reporting projection

## 11. Monitoring Rules

The lifecycle rules need to be explicit because this is where trust is won or lost.

### 11.1 `PUBLISHED -> OPEN`

Move to `OPEN` only when market price trades through the planned entry level or entry zone.

Rules:

- use bar high and low containment, not close-only logic
- record actual open time
- record filled entry price

### 11.2 `OPEN -> TP1_HIT`

Trigger when price reaches `TP1`.

Rules:

- keep the lifecycle active
- automatically move active stop to breakeven
- write a lifecycle event for both `tp1_hit` and `stop_moved_to_breakeven`

### 11.3 `OPEN` or `TP1_HIT -> STOP_LOSS_HIT`

Trigger when price reaches the active stop.

Rules:

- before `TP1_HIT`, the active stop is the original stop
- after `TP1_HIT`, the active stop is breakeven unless later stop logic raises it further

### 11.4 `TP1_HIT -> TP2_HIT`

Trigger when price reaches `TP2`.

Rules:

- close the lifecycle as a full win
- project a closed winning outcome for reporting

### 11.5 `PUBLISHED -> EXPIRED`

If entry is never reached before the lane expiry window ends, the lifecycle moves to `EXPIRED`.

Recommended defaults:

- `Intraday`: expires at session end
- `Swing`: expires after a short multi-day window
- `Position`: expires after a longer multi-day or multi-week window

These windows should be policy-configurable even if the implementation starts with sensible defaults.

## 12. Ambiguity Policy

If both stop and target conditions are touched in the same bar and sequencing cannot be proven:

- mark the lifecycle as internally `AMBIGUOUS`
- require admin review or a conservative house rule

Recommended default:

- use the conservative house rule
- assume the less favorable outcome unless lower-granularity data resolves it

This avoids overstating performance.

## 13. Integration With Existing Models

The design should evolve from the current code rather than replace it blindly.

### 13.1 `SignalRecommendation`

Remains the analysis recommendation object.

### 13.2 `SignalDelivery`

Remains proof that Horus actually published the signal.

Lifecycle creation should hang off successful delivery.

### 13.3 `SignalOutcome`

Should remain the summarized reporting and calibration layer.

It should no longer be treated as the live lifecycle authority for published signals.

### 13.4 `HorusExecution`

Should remain the internal execution and portfolio companion where needed.

It may inform lifecycle behavior, but it should not define the client signal lifecycle truth.

## 14. Operator Surfaces

The operator surfaces should expose lifecycle state without leaking internal mechanics into client-facing posts.

### 14.1 Home

`Home` should gain a published lifecycle summary strip or panel showing counts by state:

- `Published`
- `Open`
- `TP1`
- `Closed Win`
- `Closed Loss`
- `Expired`

### 14.2 Telegram

`Telegram` should show lifecycle status of recently published signals so it becomes the operational view of:

- what was sent
- what is still waiting for fill
- what hit `TP1`
- what closed

### 14.3 Status or Audit

These routes should surface:

- monitor-job health
- ambiguous cases waiting for review
- override activity
- stale unresolved records

### 14.4 Admin Lifecycle Detail View

Recommended fields:

- lane
- ticker
- publish time
- expiry time
- current state
- active stop
- `TP1`
- `TP2`
- last detected market event
- override controls

## 15. Public Message Boundary

Client-facing Telegram output should stay simple and Horus-branded.

Clients should receive:

- signal publication
- later signal updates

Clients should not receive:

- automation provenance
- admin override provenance
- ambiguity diagnostics
- internal lifecycle mechanics

Internal lifecycle metadata belongs in operator and audit surfaces only.

## 16. Reporting And Scoring Boundary

Lifecycle closure should feed a trusted internal track record without mixing unpublished research into sold signals.

Recommended scoring rules:

- only lifecycle records created from actual published Telegram signals count toward the formal track record
- unpublished candidates and admin-only intelligence never enter the formal score base
- `TP2_HIT`, `STOP_LOSS_HIT`, `EXPIRED`, and `CANCELLED` are terminal states
- `TP1_HIT` is an intermediate milestone, not a final outcome

Recommended reporting cuts:

- by lane: `Intraday`, `Swing`, `Position`
- by source module: `Scanner`, `Oracle`, `Whales`, `Traps`, `Analytics`
- by operating mode: `Manual`, `AI Assist`, `Autopilot`
- by time window: daily, weekly, rolling 30-day

Recommended metrics:

- publish count
- fill rate
- expiry rate
- `TP1` hit rate
- full win rate
- stop-loss rate
- average realized return
- expectancy per published signal
- average time to open
- average time to terminal resolution

## 17. Testing Strategy

Implementation should be verified across persistence, monitor logic, override behavior, and reporting projection.

### 17.1 Backend

Add tests for:

- lifecycle record creation after successful publish
- `PUBLISHED -> OPEN` transition when entry is actually touched
- `OPEN -> TP1_HIT` transition plus automatic breakeven stop move
- `TP1_HIT -> TP2_HIT`
- `OPEN` or `TP1_HIT -> STOP_LOSS_HIT`
- lane-aware expiry behavior
- ambiguous same-bar resolution
- admin override event logging
- projection from lifecycle closure into reporting and outcome summaries

### 17.2 Frontend

Add tests for:

- `Home` lifecycle summary rendering
- `Telegram` recent lifecycle status rendering
- operator visibility of ambiguous or override-required records
- admin lifecycle detail and override controls

### 17.3 End-to-end

Add workflow tests such as:

- Horus publishes a signal
- lifecycle record is created
- monitor job opens the signal only when price reaches entry
- signal hits `TP1`, stop moves to breakeven
- signal resolves to `TP2` or stop
- reporting surfaces show the derived result

## 18. Risks And Guardrails

### 18.1 Main risks

- treating publication as fill and inflating the track record
- mixing unpublished research performance with sold-signal performance
- coupling client lifecycle too tightly to Horus portfolio execution internals
- overstating performance in ambiguous same-bar conditions

### 18.2 Guardrails

- lifecycle starts only after confirmed Horus publication
- `OPEN` requires real price interaction with entry
- outcome reporting is derived from lifecycle closure
- ambiguity defaults to conservative handling
- every override becomes an event, not a silent mutation

## 19. Implementation Boundary

This document defines phase `A` only:

- internal lifecycle engine first
- published-signal state authority
- monitor and override rules
- derived outcome and score boundary

The next design phases can build on this:

- Telegram follow-up automation
- published-signal performance board
- Autopilot feedback tuning from real lifecycle results
