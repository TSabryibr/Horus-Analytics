# Telegram Lifecycle Follow-Up Automation Implementation Plan

Date: 2026-04-22
Based on:

- `docs/superpowers/specs/2026-04-22-telegram-lifecycle-follow-up-automation-design.md`
- `docs/superpowers/specs/2026-04-22-published-signal-lifecycle-and-outcome-tracking-design.md`
- `database.py`
- `routes/signals.py`
- `routes/system.py`
- `core/signals/lifecycle.py`
- `core/signals/outcomes.py`
- `core/signals/publishing.py`
- `core/horus/telegram.py`
- `core/TelegramBot_Alerts.py`
- `core/scheduling.py`
- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`
- `frontend/src/app/telegram/components/TelegramStatusCard.tsx`
- `frontend/src/app/context/SignalDeskContext.tsx`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- `frontend/src/app/status/**`
- `frontend/src/app/audit/**`
- `frontend/src/app/reports/weekly/**`
- `tests/test_published_signal_lifecycle.py`
- `tests/test_horus_monitor_service.py`
- `tests/test_analysis_reports.py`

Track: Telegram Lifecycle Follow-Up Automation
Status: Executed
Owner model: Single owner

## Execution Outcome

Execution status: Completed across one continuous follow-up automation rollout.

Completed rollout coverage:

- `TLFA-P1` dedicated follow-up queue persistence, queue APIs, and system-status queue health
- `TLFA-P2` lifecycle-driven follow-up rule creation with milestone eligibility and duplicate suppression
- `TLFA-P3` Horus-branded Telegram follow-up template delivery, retry, suppression, resend, and scheduler processing
- `TLFA-P4` operator-facing queue visibility and controls across `Telegram`, `Home`, `Status`, and `Audit`
- `TLFA-P5` delivery KPI separation in reporting and weekly-report operator surfaces
- `TLFA-P6` full-loop backend, frontend, route, and audit regression lock

Final verification evidence:

- backend queue/lifecycle/delivery/reporting sweep: `62 passed` via `tests/test_signals_publish_service.py`, `tests/test_signal_followup_queue.py`, `tests/test_telegram_followups.py`, `tests/test_published_signal_lifecycle.py`, `tests/test_horus_monitor_service.py`, `tests/test_signals_outcomes_service.py`, and `tests/test_strategy_and_system.py`
- backend reporting follow-up sweep: `13 passed` via `tests/test_analysis_reports.py`
- frontend targeted follow-up/report UI tests passed across `SignalDeskContext`, `HomeSignalsPanel`, `TelegramFollowUpsPanel`, `TelegramStatusCard`, `StatusLifecyclePanel`, `AuditFollowUpsPanel`, `AuditLifecyclePanel`, `WeeklyReportSummaryPanel`, and related runtime/page tests
- frontend build: `npm run build --prefix frontend` passed
- route E2E: `home.spec.ts`, `interactive_controls.spec.ts`, and `e2e_crawl.spec.ts` passed
- audit E2E: `npm run test:e2e:audit` passed

Operational note:

- local default ports were normalized to avoid collisions with other running apps: frontend now defaults to `127.0.0.1:3100` and backend defaults to `127.0.0.1:8100`

Residual notes:

- client-facing Telegram follow-ups remain `Horus`-branded and do not expose lifecycle provenance, admin override details, or operating-mode internals
- delivery metrics are intentionally separated from trading metrics; delivery issues do not alter lifecycle-derived signal performance
- this phase stops at Telegram lifecycle follow-up automation and operator visibility; it does not introduce client-facing public track-record pages or new outbound channels

## 1. Planning Goal

Implement the next post-lifecycle Horus loop:

`publish -> monitor -> detect milestone -> queue follow-up -> send Horus update -> score`

The rollout should:

1. create a dedicated follow-up queue for client-facing Telegram lifecycle updates
2. keep lifecycle truth independent from follow-up delivery success
3. support `Manual`, `AI Assist`, and `Autopilot` follow-up release behavior
4. expose follow-up queue health and actions inside `Telegram`, `Home`, `Status`, and `Audit`
5. add delivery KPIs without contaminating trading KPIs

## 2. In Scope

Primary implementation targets:

- backend persistence for lifecycle follow-up jobs and delivery state
- lifecycle rule evaluation for follow-up-eligible milestones
- Telegram follow-up message template generation
- delivery worker, retry logic, suppression, and resend flow
- operator-facing follow-up queue visibility and controls
- delivery metrics separated from lifecycle trading metrics
- focused backend, frontend, and E2E verification for the full follow-up loop

Primary files expected to move:

- `database.py`
- `routes/signals.py`
- `routes/system.py`
- `routes/analysis_reports.py`
- `core/signals/lifecycle.py`
- new helper modules under `core/signals/` for follow-up queue logic if needed
- `core/horus/telegram.py`
- `core/TelegramBot_Alerts.py` only if existing send seams require small extensions
- `core/scheduling.py`
- `frontend/src/app/context/SignalDeskContext.tsx`
- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`
- new Telegram follow-up components under `frontend/src/app/telegram/components/`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- `frontend/src/app/status/**`
- `frontend/src/app/audit/**`
- `frontend/src/app/reports/weekly/**`
- related tests under `tests/`, `frontend/src/app/**/*.test.tsx`, and `frontend/e2e/`

Out of scope for this slice:

- redesigning the initial signal publish card
- client-facing public performance pages
- new outbound channels beyond Telegram
- changing lifecycle resolution rules already approved
- exposing provenance, override history, or operating-mode internals to clients

## 3. Execution Rules

These rules apply across the rollout:

1. Lifecycle truth remains the source of trading truth; Telegram follow-up delivery is an operational layer on top.
2. Do not send follow-up messages directly from the lifecycle monitor loop; always route through a queue and delivery worker.
3. Only commercially meaningful lifecycle states can create client-facing follow-up jobs.
4. `AMBIGUOUS` never creates a client-facing follow-up automatically.
5. Each lifecycle milestone can create at most one client follow-up unless an operator explicitly resends it.
6. Keep all client-facing Telegram copy branded as `Horus` and free of provenance, override, or mode metadata.
7. Delivery failures must not roll back lifecycle state.
8. Land queue persistence and rule creation before operator UI work.
9. Finish each work package with verification so follow-up automation does not erode signal trust.

## 4. Work Package Sequence

Execute in this order:

1. `TLFA-P1` Follow-up persistence and backend contract
2. `TLFA-P2` Lifecycle rule engine and queue creation
3. `TLFA-P3` Telegram follow-up template builder and delivery worker
4. `TLFA-P4` Operator queue surfaces and controls
5. `TLFA-P5` Delivery metrics and reporting boundary
6. `TLFA-P6` Full-loop verification and regression lock

This order is intentional:

- queue persistence must exist before lifecycle milestones can enqueue work
- rule creation must be stable before message sending is automated
- delivery should be reliable before operator surfaces depend on it
- delivery KPIs should be layered in after queue truth exists
- verification should validate the integrated follow-up loop, not just isolated helpers

## 5. Work Packages

### TLFA-P1. Follow-Up Persistence And Backend Contract

Purpose:

Create a dedicated queue authority for Telegram lifecycle follow-ups without overloading the lifecycle table itself.

Target files:

- `database.py`
- `routes/signals.py`
- `routes/system.py`
- `tests/conftest.py`
- new backend tests such as `tests/test_signal_followup_queue.py`

Tasks:

1. Add persistence for lifecycle follow-up jobs and follow-up events or delivery attempts.
2. Support fields for:
   - linked lifecycle, recommendation, run, delivery, and portfolio
   - trigger state such as `TP1_HIT`, `TP2_HIT`, `STOP_LOSS_HIT`, `EXPIRED`, `CANCELLED`
   - message type: `UPDATE` or `CLOSE`
   - queue state: `PENDING`, `READY`, `SENT`, `FAILED`, `SUPPRESSED`
   - draft message payload
   - send timestamps, retry counts, suppression metadata, and Telegram message ids
3. Add backend serialization helpers and read endpoints for:
   - follow-up queue summary
   - queue list filters
   - follow-up detail view
4. Extend system status payloads to expose follow-up queue health, failed count, and stale pending count.

Deliverables:

- stable follow-up queue contract
- dedicated persistence layer for client follow-up operations
- operator-facing read APIs

Verification:

- `pytest tests/test_signal_followup_queue.py tests/test_strategy_and_system.py`

Acceptance criteria:

- the backend can represent pending, sent, failed, and suppressed follow-up jobs independently of lifecycle truth
- follow-up queue state is queryable through stable operator-facing APIs

### TLFA-P2. Lifecycle Rule Engine And Queue Creation

Purpose:

Turn eligible lifecycle milestones into follow-up jobs using explicit rules and duplicate suppression.

Target files:

- `core/signals/lifecycle.py`
- new helper module(s) under `core/signals/` for follow-up rule evaluation
- `routes/signals.py`
- `tests/test_published_signal_lifecycle.py`
- `tests/test_horus_monitor_service.py`
- new lifecycle-follow-up tests

Tasks:

1. Add follow-up rule evaluation for:
   - `TP1_HIT`
   - `TP2_HIT`
   - `STOP_LOSS_HIT`
   - `EXPIRED`
   - optional `CANCELLED`
2. Enforce duplicate suppression by lifecycle milestone.
3. Block automatic queue creation for:
   - `PUBLISHED`
   - `OPEN`
   - `AMBIGUOUS`
4. Respect operating mode and follow-up policy when deciding whether a job becomes `PENDING`, `READY`, or auto-send eligible.
5. Record queue-creation and suppression events without mutating lifecycle truth.

Deliverables:

- lifecycle-to-follow-up rule engine
- duplicate-safe queue creation
- operating-mode-aware follow-up job generation

Verification:

- `pytest tests/test_signal_followup_queue.py tests/test_published_signal_lifecycle.py tests/test_horus_monitor_service.py`

Acceptance criteria:

- eligible lifecycle milestones create follow-up jobs exactly once
- ambiguous or ineligible states do not create client-facing queue jobs
- lifecycle truth remains unchanged by delivery policy decisions

### TLFA-P3. Telegram Follow-Up Template Builder And Delivery Worker

Purpose:

Generate clean Horus follow-up copy and deliver queued updates reliably through Telegram with retry semantics.

Target files:

- `core/horus/telegram.py`
- `core/TelegramBot_Alerts.py`
- `core/scheduling.py`
- new queue-delivery helper module(s) under `core/signals/`
- `routes/signals.py`
- `tests/test_telegram_followups.py`
- `tests/test_horus_monitor_service.py`

Tasks:

1. Add follow-up templates for:
   - `TP1_HIT` -> `HORUS UPDATE`
   - `TP2_HIT` -> `HORUS CLOSE`
   - `STOP_LOSS_HIT` -> `HORUS CLOSE`
   - `EXPIRED` -> `HORUS UPDATE` or `HORUS CLOSE`
2. Preserve current Horus Telegram voice while keeping copy provenance-free.
3. Implement a delivery worker that:
   - sends ready or pending follow-up jobs
   - records Telegram response ids
   - retries failed jobs
   - marks jobs as failed without rolling back lifecycle state
4. Integrate the worker into the scheduler or an equivalent safe execution seam.
5. Support manual resend and retry paths through the same queue contract.

Deliverables:

- follow-up template builder
- automated delivery worker
- retry-safe Telegram delivery path for follow-up jobs

Verification:

- `pytest tests/test_telegram_followups.py tests/test_signal_followup_queue.py tests/test_horus_monitor_service.py`

Acceptance criteria:

- queued follow-up jobs can be delivered and retried reliably
- client messages remain clean Horus lifecycle updates with no internal leakage
- delivery failures remain operational failures, not lifecycle failures

### TLFA-P4. Operator Queue Surfaces And Controls

Purpose:

Expose follow-up operations inside the existing Telegram-centered control plane and supporting operator surfaces.

Target files:

- `frontend/src/app/context/SignalDeskContext.tsx`
- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`
- new follow-up queue components under `frontend/src/app/telegram/components/`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- `frontend/src/app/status/**`
- `frontend/src/app/audit/**`
- related frontend tests

Tasks:

1. Extend shared desk state to include follow-up queue summary, rows, and queue actions.
2. Add a `Lifecycle Follow-Ups` panel on `Telegram` showing:
   - pending
   - sent
   - failed
   - suppressed
3. Add operator actions for:
   - send now
   - retry
   - suppress
   - resend
4. Add lightweight follow-up queue counts to `Home`.
5. Add queue-health, suppression, and resend visibility to `Status` and `Audit`.

Deliverables:

- follow-up queue visibility on `Telegram`
- lightweight queue awareness on `Home`
- operational review surfaces in `Status` and `Audit`

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/telegram src/app/status src/app/audit src/app/components/HomeSignalsPanel.test.tsx`

Acceptance criteria:

- operators can see and act on follow-up queue items from the main control surfaces
- Telegram now behaves like a release-and-follow-up rail rather than only a broadcaster

### TLFA-P5. Delivery Metrics And Reporting Boundary

Purpose:

Add delivery KPIs without mixing delivery reliability into trading-performance scoring.

Target files:

- `routes/analysis_reports.py`
- `routes/system.py`
- `frontend/src/app/reports/weekly/**`
- `frontend/src/app/status/**`
- `tests/test_analysis_reports.py`
- `tests/test_horus_reporting_integration.py`

Tasks:

1. Add delivery metrics such as:
   - follow-up send rate
   - follow-up failure rate
   - average retry count
   - pending queue age
   - suppressed update count
2. Keep trading metrics and delivery metrics separated in reporting payloads.
3. Extend operator-facing report surfaces to display delivery KPIs without changing the lifecycle-based trading boundary.
4. Ensure delivery failures do not alter lifecycle-derived win/loss/expiry reporting.

Deliverables:

- operational delivery metrics
- clean separation between trading and delivery reporting
- report surfaces that reflect follow-up automation quality

Verification:

- `pytest tests/test_analysis_reports.py tests/test_horus_reporting_integration.py tests/test_signal_followup_queue.py`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/reports/weekly`

Acceptance criteria:

- delivery KPIs are visible without contaminating lifecycle-derived trading KPIs
- reports remain honest about both signal performance and communication performance

### TLFA-P6. Full-Loop Verification And Regression Lock

Purpose:

Validate the follow-up automation loop end to end and lock the phase with regression coverage.

Target files:

- touched files from `TLFA-P1` through `TLFA-P5`
- `tests/test_signal_followup_queue.py`
- `tests/test_published_signal_lifecycle.py`
- `tests/test_horus_monitor_service.py`
- `tests/test_telegram_followups.py`
- `tests/test_analysis_reports.py`
- `frontend/e2e/home.spec.ts`
- `frontend/e2e/interactive_controls.spec.ts`
- `frontend/e2e/e2e_crawl.spec.ts`
- `frontend/e2e/_phase3_audit.spec.ts`

Tasks:

1. Verify the full follow-up loop:
   - Horus publishes a signal
   - lifecycle milestone is reached
   - follow-up job is created exactly once
   - message is sent, retried, suppressed, or resent correctly
   - delivery metrics appear without altering trading truth
2. Run frontend build verification.
3. Run focused backend suites for queue, lifecycle, delivery, reporting, and system status.
4. Run route and audit checks to ensure the new follow-up UI does not destabilize the shell.
5. Record any residual out-of-scope issues separately from the phase.

Deliverables:

- verified follow-up automation loop
- regression evidence for backend, frontend, and route-level behavior
- explicit residual-issues list if anything remains outside scope

Verification:

- `pytest tests/test_signal_followup_queue.py tests/test_published_signal_lifecycle.py tests/test_horus_monitor_service.py tests/test_telegram_followups.py tests/test_analysis_reports.py`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e -- home.spec.ts interactive_controls.spec.ts e2e_crawl.spec.ts`
- `npm --prefix frontend run test:e2e:audit`

Acceptance criteria:

- follow-up automation works from lifecycle milestone through delivery and reporting
- operator surfaces expose follow-up truth without leaking internals to clients
- no critical follow-up, queue, or route regressions remain in the verified phase

## 6. Risks And Controls

### Risk 1. Follow-up jobs are sent multiple times because lifecycle polling re-observes the same state

Control:

- create explicit queue records per lifecycle milestone
- enforce duplicate suppression by lifecycle id plus trigger state

### Risk 2. Telegram delivery failures corrupt lifecycle truth

Control:

- keep lifecycle state authoritative and immutable with respect to delivery failures
- treat delivery failure as queue state only

### Risk 3. Client messages leak internal operations language

Control:

- centralize copy generation in follow-up templates
- block provenance, override, and operating-mode fields from client message builders

### Risk 4. Operator surfaces overwhelm the desk with delivery detail

Control:

- keep `Home` lightweight
- reserve detailed queue control for `Telegram`, `Status`, and `Audit`

### Risk 5. Delivery KPIs get mixed into trade-performance KPIs

Control:

- keep delivery metrics in a separate reporting family
- verify analysis report payloads and UI keep the two boundaries distinct

## 7. Recommended Execution Notes

- Start with `TLFA-P1` and `TLFA-P2` back-to-back so queue truth exists before delivery automation begins.
- Reuse lifecycle and Telegram sending seams where they already exist, but do not let the monitor send client follow-ups directly.
- Keep Telegram follow-up template work close to the existing Horus messaging helpers so brand voice stays consistent.
- Treat `Telegram` as the primary operator surface for the queue, with `Home` only showing lightweight awareness.
- Keep the commercial boundary hard: trading truth comes from lifecycle state, not from follow-up delivery success.

## 8. Recommended Next Move After This Plan

Execute `TLFA-P1` and `TLFA-P2` as the first active implementation slice. They create the dedicated queue authority and lifecycle follow-up rule engine that every delivery worker, UI surface, and reporting KPI depends on.
