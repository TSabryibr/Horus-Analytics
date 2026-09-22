# Telegram Lifecycle Follow-Up Automation Design

Date: 2026-04-22
Status: Approved

## 1. Goal

Extend the published-signal lifecycle into a post-release communication loop so Horus can automatically send clean client-facing Telegram updates after meaningful lifecycle milestones.

This phase adds the missing commercial layer after lifecycle truth:

`publish -> monitor -> detect milestone -> send Horus update -> close -> score`

The system should:

1. convert eligible lifecycle milestones into Telegram follow-up jobs
2. keep lifecycle truth separate from delivery success
3. preserve one client-facing Horus voice without exposing internal provenance
4. support `Manual`, `AI Assist`, and `Autopilot` follow-up behavior
5. expose follow-up queue health and actions inside the existing operator surfaces

## 2. Scope

In scope:

- lifecycle-to-follow-up rule evaluation
- dedicated Telegram follow-up queue and delivery records
- Telegram follow-up message templates
- operator controls for send, retry, suppress, and resend
- `Telegram`, `Home`, `Status`, and `Audit` visibility for follow-up operations
- delivery metrics separated from trading metrics

Out of scope:

- redesigning the primary publish message format
- client-facing public track-record pages
- non-Telegram outbound channels
- changing the lifecycle scoring rules already approved
- exposing internal provenance or override details to clients

## 3. Client Update Boundary

Only commercially meaningful lifecycle milestones should create client-facing follow-up opportunities.

Recommended lifecycle-to-follow-up mapping:

- `TP1_HIT` -> yes
- `TP2_HIT` -> yes
- `STOP_LOSS_HIT` -> yes
- `EXPIRED` -> yes, optional by policy
- `CANCELLED` -> yes, optional by policy
- `AMBIGUOUS` -> no
- `PUBLISHED` -> no
- `OPEN` -> no

Rules:

- follow-ups must never expose `AUTO`, `ADMIN_OVERRIDE`, `AI Assist`, `Autopilot`, or lifecycle internals
- each milestone can create at most one client-facing follow-up unless the admin explicitly resends
- follow-up messages must remain branded as `Horus`

This keeps the client experience focused on the signal journey, not the internal machinery that produced it.

## 4. Architecture

The follow-up system should not send Telegram messages directly from the lifecycle monitor.

Recommended components:

- `Lifecycle Follow-Up Rule Engine`
  - decides whether a lifecycle event should create a follow-up job
  - applies policy rules for eligible states, duplicate suppression, and cooldowns

- `Telegram Follow-Up Queue`
  - stores pending follow-up jobs
  - supports retry, suppression, resend, and sent-state tracking
  - links to lifecycle and delivery records

- `Message Template Builder`
  - converts lifecycle state into client-facing Horus copy
  - generates the update or close message without leaking internal metadata

- `Delivery Worker`
  - sends pending follow-up jobs to Telegram
  - records message ids, send results, retry counts, and errors

- `Operator Controls`
  - allow `send now`, `retry`, `suppress`, and `resend`
  - allow draft review in `Manual` and `AI Assist` modes

Responsibility split:

- lifecycle monitor decides `what happened`
- rule engine decides `what should be sent`
- queue owns `what is pending`
- Telegram delivery owns `sending and retries`

This keeps the system reliable, retryable, and auditable without polluting lifecycle truth.

## 5. Client Message Set

The client-facing Telegram copy should feel like a continuous Horus signal journey.

Recommended messages:

- `TP1_HIT`
  - `HORUS UPDATE`
  - first target reached
  - stop moved to breakeven
  - second target remains active

- `TP2_HIT`
  - `HORUS CLOSE`
  - final target reached
  - signal closed in profit

- `STOP_LOSS_HIT`
  - `HORUS CLOSE`
  - stop loss hit
  - signal closed

- `EXPIRED`
  - `HORUS UPDATE` or `HORUS CLOSE`
  - entry was not triggered in time
  - signal expired with no trade

Copy rules:

- keep ticker, direction, and outcome clear
- preserve the current Horus Telegram tone
- mention breakeven promotion after `TP1`
- never mention `lifecycle`, `monitor`, `override`, `autopilot`, `admin`, or provenance details

## 6. Operating Modes

Follow-up release behavior should respect the same operating mode model already used elsewhere.

Mode behavior:

- `Manual`
  - Horus creates the follow-up draft
  - admin decides whether to send it

- `AI Assist`
  - Horus creates the draft and queues it as ready
  - admin can review, lightly edit, or approve

- `Autopilot`
  - Horus creates and sends the follow-up automatically when the lifecycle rule allows it
  - delivery failures remain retryable but do not roll back lifecycle truth

Required policy controls:

- eligible lifecycle-state allowlist
- duplicate suppression by lifecycle milestone
- optional cooldown windows between updates
- suppression for `AMBIGUOUS`
- per-signal admin suppression override

Critical rule:

- lifecycle state remains the trading truth even if Telegram delivery fails
- follow-up delivery is operational state layered on top of lifecycle truth

## 7. Operator Surfaces

The follow-up system should appear inside the existing Telegram-centered operating model.

Recommended surfaces:

- `Telegram`
  - add `Lifecycle Follow-Ups` panel
  - show:
    - pending updates
    - sent updates
    - failed updates
    - suppressed updates
  - actions:
    - send now
    - retry
    - suppress
    - resend

- `Home`
  - show lightweight counts for:
    - pending follow-ups
    - failed follow-ups

- `Status` or `Audit`
  - show queue health
  - duplicate suppression events
  - delivery failures
  - manual suppressions and resends

Recommended row fields:

- ticker
- triggering lifecycle state
- message type: `UPDATE` or `CLOSE`
- queue state: `PENDING`, `SENT`, `FAILED`, `SUPPRESSED`
- created time
- sent time
- retry count

This makes Telegram the full release-and-follow-up rail rather than a one-time broadcaster.

## 8. Reporting Boundary

Follow-up delivery should improve operational visibility without affecting trade scoring.

Trading performance remains lifecycle-driven:

- fill rate
- `TP1` hit rate
- full win rate
- stop-loss rate
- expiry rate
- expectancy
- time to resolution

Delivery performance is separate:

- follow-up send rate
- follow-up failure rate
- average retry count
- pending queue age
- suppressed update count

Rules:

- scoring does not depend on whether a follow-up Telegram message was sent
- delivery failures are ops issues, not trade-performance issues
- lifecycle remains the authority for commercial track record

This keeps both the signal product and the infrastructure reporting honest.

## 9. Recommended Next Step

Create an implementation plan for:

`Telegram Lifecycle Follow-Up Automation`

Recommended execution order:

1. persistence and queue contract
2. lifecycle rule engine and queue creation
3. Telegram follow-up template builder and delivery worker
4. operator controls and queue surfaces
5. delivery metrics and regression lock
