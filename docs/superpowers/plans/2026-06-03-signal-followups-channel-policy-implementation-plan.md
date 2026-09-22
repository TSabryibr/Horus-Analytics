# Signal Follow-Ups and Channel Broadcast Policy Implementation Plan

Date: 2026-06-03
Based on:

- `docs/superpowers/specs/2026-06-03-signal-followups-channel-policy-design.md`
- `docs/superpowers/plans/2026-04-22-telegram-lifecycle-follow-up-automation-implementation-plan.md`
- `database.py`
- `core/signals/publishing.py`
- `core/signals/lifecycle.py`
- `core/signals/followups.py`
- `core/subscriptions.py`
- `core/TelegramBot_Alerts.py`
- `routes/signals.py`
- `routes/settings.py`
- `core/scheduling.py`
- `frontend/src/app/telegram/components/TelegramFollowUpsPanel.tsx`
- `frontend/src/app/subscribers/page.tsx`
- existing signal/follow-up/subscriber tests under `tests/` and `frontend/src/app/**`

Track: Signal Follow-Ups and Channel Policy
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Implement the approved subscriber follow-up and main-channel routing design in one tightly related rollout.

The rollout should:

1. freeze signal destination eligibility at original publish time
2. send Type 1 follow-up cards to every eligible Type 1 subscriber destination
3. support automatic and manual lifecycle transitions through the same follow-up path
4. add a cumulative automated main-channel broadcast level across Type 1, Type 2, and Type 3
5. preserve retries, suppression, auditability, and duplicate prevention per destination

## 2. In Scope

Primary implementation targets:

- persistence additions for service tier, destination identity, and frozen eligibility
- routing helpers for subscriber entitlement and main-channel broadcast level
- publishing fan-out for active subscribers and optional main channel delivery
- destination-aware lifecycle follow-up creation and delivery
- admin APIs and UI controls for broadcast level and follow-up destination visibility
- focused backend and frontend tests for routing, lifecycle transitions, and duplicate prevention

Out of scope:

- opening or managing real positions for Type 1 subscribers
- changing the initial signal strategy generation logic
- changing manual admin channel post behavior
- adding channels beyond Telegram
- rebuilding subscriber onboarding or billing

## 3. Execution Rules

1. Treat the approved spec as the source of truth for behavior.
2. Keep lifecycle state as trading truth; delivery success must not mutate lifecycle truth.
3. Freeze destination eligibility when the original signal is published.
4. Use the same follow-up creation path for monitor transitions and admin overrides.
5. Deduplicate by lifecycle, trigger state, and destination.
6. Keep Type 1 copy actionable but clear that Horus is following up on a signal, not managing an opened subscriber position.
7. Keep manual channel posts independent from automated broadcast policy.
8. Prefer extending existing lifecycle/follow-up/publishing code over creating a parallel notification system.

## 4. Work Package Sequence

Execute in this order:

1. `SFCP-P1` Destination and policy persistence
2. `SFCP-P2` Entitlement and channel routing helpers
3. `SFCP-P3` Original signal publish fan-out
4. `SFCP-P4` Destination-aware lifecycle follow-ups
5. `SFCP-P5` Admin surfaces, scheduling, and reporting visibility
6. `SFCP-P6` Verification and regression lock

This order keeps storage and policy stable before expanding publish behavior, then layers follow-up fan-out and UI on top.

## 5. Work Packages

### SFCP-P1. Destination And Policy Persistence

Purpose:

Extend existing delivery records so original signals and follow-ups can identify service tier, destination type, destination id, and frozen channel eligibility.

Target files:

- `database.py`
- `database_async.py` if async model parity is still maintained for these tables
- `tests/conftest.py`
- new or existing backend tests such as `tests/test_signal_followup_queue.py` and `tests/test_signals_publish_service.py`

Tasks:

1. Add fields needed to represent destination-aware signal delivery and follow-ups.
2. Add a stable destination type model, expected values:
   - `SUBSCRIBER`
   - `MAIN_CHANNEL`
   - existing portfolio/user delivery where still needed
3. Add or encode destination identifiers:
   - subscriber/client id for subscriber sends
   - main channel marker for channel sends
   - Telegram chat id snapshot where relevant
4. Add service tier metadata, expected values:
   - `SIGNALS_ONLY`
   - `SIGNALS_PLUS_PORTFOLIO_RECS`
   - `MANAGED_ADVISORY`
5. Add migration/backfill handling for existing tables without breaking old lifecycle records.
6. Update uniqueness constraints or duplicate checks so records are unique by run/recommendation/destination/channel where needed.

Deliverables:

- persistent destination identity for original signal deliveries
- persistent destination identity for follow-up jobs
- migration-safe defaults for existing records

Verification:

- `pytest tests/test_signal_followup_queue.py tests/test_signals_publish_service.py`

Acceptance criteria:

- existing lifecycle/follow-up rows still serialize correctly
- new delivery rows can distinguish subscriber destinations from the main channel
- duplicate prevention can be enforced per destination instead of only per lifecycle

### SFCP-P2. Entitlement And Channel Routing Helpers

Purpose:

Create explicit helpers for subscriber entitlement and cumulative main-channel broadcast policy.

Target files:

- `core/subscriptions.py`
- `core/signals/publishing.py`
- `core/settings.py`
- `GlobalSettings.py` only if runtime compatibility requires it
- `routes/settings.py`
- backend tests such as `tests/test_subscriptions.py`, `tests/test_signals_publish_service.py`, or a new `tests/test_signal_channel_policy.py`

Tasks:

1. Add a normalized service-tier order:
   - Type 1: `SIGNALS_ONLY`
   - Type 2: `SIGNALS_PLUS_PORTFOLIO_RECS`
   - Type 3: `MANAGED_ADVISORY`
2. Implement subscriber entitlement checks for automated service content.
3. Add global automated main-channel broadcast level:
   - `none`
   - `type_1`
   - `type_2`
   - `type_3`
4. Implement cumulative channel policy:
   - `type_2` includes Type 1 and Type 2
   - `type_3` includes Type 1, Type 2, and Type 3
5. Expose the setting through existing settings APIs.
6. Keep manual channel send paths outside this policy.

Deliverables:

- reusable routing helpers
- persisted/admin-visible main-channel broadcast level
- policy tests for cumulative routing

Verification:

- `pytest tests/test_signal_channel_policy.py tests/test_signals_publish_service.py`

Acceptance criteria:

- `none` blocks automated main-channel sends
- `type_1`, `type_2`, and `type_3` include the correct service tiers
- subscriber entitlement and channel policy can be evaluated independently

### SFCP-P3. Original Signal Publish Fan-Out

Purpose:

Expand automated signal publishing so it can deliver signal cards to entitled subscribers and optionally to the main Telegram channel.

Target files:

- `core/signals/publishing.py`
- `routes/signals.py`
- `core/subscriptions.py`
- `core/TelegramBot_Alerts.py` if chat override handling needs small adjustments
- `tests/test_signals_publish_service.py`
- `tests/test_subscriptions.py`

Tasks:

1. Determine the service tier for each automated publish operation.
2. Build destination snapshots for active entitled subscribers.
3. Include subscriber Telegram chat id and delivery token override where applicable.
4. Include the main channel destination only when the global channel policy allows the service tier.
5. Create signal delivery records per destination.
6. Send original signal cards to each destination through the existing Telegram send function with `chat_id` override support.
7. Create published lifecycle records after successful original sends.
8. Record audit details explaining selected and skipped destinations.

Deliverables:

- subscriber fan-out for original Type 1 signal cards
- optional automated main-channel fan-out
- lifecycle records tied to destination snapshots

Verification:

- `pytest tests/test_signals_publish_service.py tests/test_published_signal_lifecycle.py`

Acceptance criteria:

- every active entitled Type 1 subscriber with a valid Telegram chat id receives Type 1 original signal cards
- main channel receives automated cards only under the cumulative policy
- lifecycle creation remains tied to successful original sends
- failed sends are tracked per destination without blocking other destinations

### SFCP-P4. Destination-Aware Lifecycle Follow-Ups

Purpose:

Create and deliver Type 1 follow-up cards per eligible destination for lifecycle states approved in the spec.

Target files:

- `core/signals/followups.py`
- `core/signals/lifecycle.py`
- `routes/signals.py`
- `core/scheduling.py`
- `tests/test_signal_followup_queue.py`
- `tests/test_published_signal_lifecycle.py`
- `tests/test_telegram_followups.py`

Tasks:

1. Change follow-up creation from one job per lifecycle/state to one job per lifecycle/state/destination.
2. Preserve compatibility for existing lifecycle-level rows where possible.
3. Generate Type 1 copy:
   - `TP1_HIT`: instruct move stop loss to breakeven and keep TP2 active
   - `TP2_HIT`: signal fully closed, no further action
   - `STOP_LOSS_HIT`: signal fully closed, no further action
   - `EXPIRED`: signal expired/closed, no further action
4. Send follow-ups to subscriber chat ids and main-channel chat id based on frozen original eligibility.
5. Ensure admin overrides and monitor transitions call the same follow-up creation service.
6. Keep retry, requeue, suppress, and send-now actions destination-aware.
7. Include destination metadata in follow-up serialization and audit events.

Deliverables:

- destination-aware follow-up queue
- copy aligned with approved Type 1 behavior
- retry/suppress/resend support per destination

Verification:

- `pytest tests/test_signal_followup_queue.py tests/test_published_signal_lifecycle.py tests/test_telegram_followups.py`

Acceptance criteria:

- `TP1_HIT`, `TP2_HIT`, `STOP_LOSS_HIT`, and `EXPIRED` create follow-ups for every frozen eligible Type 1 destination
- duplicate transitions do not create duplicate follow-up cards per destination
- manual admin overrides create missing follow-ups through the same path as automatic monitoring
- delivery failure for one destination does not affect lifecycle state or other destinations

### SFCP-P5. Admin Surfaces, Scheduling, And Reporting Visibility

Purpose:

Expose the new policy and destination-aware follow-ups to admins without changing manual broadcast behavior.

Target files:

- `routes/settings.py`
- `routes/signals.py`
- `routes/system.py`
- `routes/analysis_reports.py` if delivery KPIs need destination separation
- `frontend/src/app/telegram/components/TelegramFollowUpsPanel.tsx`
- `frontend/src/app/context/SignalDeskContext.tsx`
- likely settings UI files under `frontend/src/app/settings/**`
- related frontend tests under `frontend/src/app/**`

Tasks:

1. Add settings UI/API support for automated main-channel broadcast level.
2. Show destination type/name/chat status in the follow-up queue.
3. Preserve existing follow-up actions:
   - send now
   - retry
   - suppress
   - resend/requeue
4. Confirm scheduled follow-up processing handles destination-aware sends.
5. Separate subscriber and main-channel delivery counts where useful in summaries.
6. Keep manual admin channel sends available when automated policy is `none`.

Deliverables:

- admin-controlled broadcast level
- destination-aware follow-up queue visibility
- system/status/reporting summaries that remain understandable after fan-out

Verification:

- `pytest tests/test_strategy_and_system.py tests/test_analysis_reports.py`
- `npm test --prefix frontend -- TelegramFollowUpsPanel`
- `npm test --prefix frontend -- settings`

Acceptance criteria:

- admins can set `none`, `type_1`, `type_2`, or `type_3`
- admins can identify which follow-up is going to a subscriber versus the main channel
- existing follow-up controls continue to work per destination
- manual admin channel posts are not blocked by the automated broadcast setting

### SFCP-P6. Verification And Regression Lock

Purpose:

Validate the integrated subscriber/channel/follow-up loop across backend and frontend.

Target files:

- backend tests touched or added in earlier packages
- frontend tests touched or added in earlier packages
- optional E2E tests if local app test coverage already covers Telegram/settings workflows

Tasks:

1. Run focused backend tests for publishing, lifecycle, follow-up queue, subscriptions, and settings.
2. Run focused frontend tests for settings and follow-up queue visibility.
3. Run broader smoke tests that are likely to catch route or serialization regressions.
4. Record any residual risks or skipped tests in the implementation close-out.

Deliverables:

- passing focused backend tests
- passing focused frontend tests
- documented verification result

Verification:

- `pytest tests/test_signals_publish_service.py tests/test_signal_followup_queue.py tests/test_published_signal_lifecycle.py tests/test_telegram_followups.py`
- `pytest tests/test_strategy_and_system.py tests/test_analysis_reports.py`
- `npm test --prefix frontend -- TelegramFollowUpsPanel`
- `npm test --prefix frontend -- settings`
- `npm run build --prefix frontend`

Acceptance criteria:

- the automated publish path routes to the correct subscriber and channel destinations
- follow-ups are destination-aware, deduplicated, retryable, and suppressible
- Type 1 copy matches the approved action/closure behavior
- the frontend builds after admin settings and queue changes

## 6. Risks And Controls

Risk: existing `SignalDelivery` uniqueness is portfolio-centered and may not fit subscriber/channel fan-out.
Control: introduce destination fields and migrate uniqueness carefully, with compatibility handling for old rows.

Risk: existing `PublishedSignalFollowUp` uniqueness is lifecycle/state only.
Control: move duplicate logic to lifecycle/state/destination and test duplicate suppression before enabling sends.

Risk: broadcasting to many subscribers can increase Telegram rate-limit exposure.
Control: preserve queue processing, keep retry state per destination, and avoid sending directly from lifecycle transitions.

Risk: subscription changes after publish could create confusing follow-up eligibility.
Control: freeze eligibility at original publish time as required by the spec.

Risk: main-channel policy could accidentally affect manual admin messages.
Control: keep the automated policy helper scoped to automated signal/follow-up paths only.

## 7. Recommended Execution Notes

Start with backend persistence and tests. The existing follow-up automation already has a queue and lifecycle transition path, so the highest-risk change is destination identity, not message formatting.

Do not start with UI. The admin panels should consume stable backend fields after fan-out and duplicate rules are locked.

Where storage options are ambiguous, prefer explicit columns over burying critical routing decisions only in JSON. JSON can still carry extra audit context, but destination identity and service tier should be queryable.

## 8. Recommended Next Move After This Plan

Begin with `SFCP-P1`: add destination and service-tier persistence for original signal deliveries and published follow-ups, then lock it with backend tests before changing publish fan-out.
