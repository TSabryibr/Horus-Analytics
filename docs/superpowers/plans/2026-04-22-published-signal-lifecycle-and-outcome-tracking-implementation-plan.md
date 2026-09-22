# Published Signal Lifecycle And Outcome Tracking Implementation Plan

Date: 2026-04-22
Based on:

- `docs/superpowers/specs/2026-04-22-published-signal-lifecycle-and-outcome-tracking-design.md`
- `database.py`
- `routes/signals.py`
- `routes/analysis_reports.py`
- `routes/system.py`
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
- `tests/test_signals_publish_service.py`
- `tests/test_signals_outcomes_service.py`
- `tests/test_horus_execution_service.py`
- `tests/test_horus_monitor_service.py`

Track: Published Signal Lifecycle And Outcome Tracking
Status: Executed
Owner model: Single owner

## Execution Outcome

Execution status: Completed across one continuous lifecycle rollout.

Completed rollout coverage:

- `PSLA-P1` dedicated lifecycle persistence, lifecycle APIs, and system-status summary
- `PSLA-P2` publish-hook creation, lifecycle monitor engine, ambiguity handling, and scheduler integration
- `PSLA-P3` admin override actions, lifecycle event log, ambiguity review, and operator control surfaces
- `PSLA-P4` lifecycle-to-outcome projection plus lifecycle-first portfolio reporting and score boundary
- `PSLA-P5` lifecycle visibility across `Home`, `Telegram`, `Status`, `Audit`, and the weekly analysis report summary
- `PSLA-P6` full-loop backend, frontend, route, and audit regression lock

Final verification evidence:

- backend: `67 passed` via `tests/test_signals_publish_service.py`, `tests/test_published_signal_lifecycle.py`, `tests/test_horus_monitor_service.py`, `tests/test_signals_outcomes_service.py`, `tests/test_analysis_reports.py`, and `tests/test_strategy_and_system.py`
- additional backend reporting sweep: `29 passed` via `tests/test_published_signal_lifecycle.py`, `tests/test_signals_outcomes_service.py`, `tests/test_analysis_reports.py`, and `tests/test_horus_reporting_integration.py`
- frontend targeted lifecycle/report UI tests: `src/app/reports/weekly/components/WeeklyReportSummaryPanel.test.tsx` and `src/app/reports/weekly/hooks/useWeeklyReportRuntime.test.tsx` passed
- frontend build: `npm run build` passed
- route E2E: `home.spec.ts`, `interactive_controls.spec.ts`, and `e2e_crawl.spec.ts` passed
- audit E2E: `npm run test:e2e:audit` passed

Residual notes:

- client-facing Telegram posts remain `Horus`-branded and do not expose internal lifecycle provenance, override history, or operating-mode details
- the phase intentionally stops short of client-facing track-record pages and Telegram follow-up template redesign; lifecycle truth and scoring are internal/operator-facing in this rollout
- unpublished research ideas, admin-only intel surfaces, `News`, and `Sectors` remain outside the formal sold-signal lifecycle boundary

## 1. Planning Goal

Implement phase `A` of the next Horus product loop:

`publish -> monitor -> resolve -> score`

The rollout should:

1. create a dedicated lifecycle authority for signals actually published by `Horus`
2. move a signal from `PUBLISHED` to `OPEN` only when market price actually reaches entry
3. track `TP1`, `TP2`, stop loss, expiry, ambiguity, and admin overrides
4. automatically move stop to breakeven after `TP1`
5. project terminal lifecycle states into reporting and scoring without mixing unpublished research into the commercial track record
6. surface lifecycle truth to operator-facing `Home`, `Telegram`, and ops views without leaking internals to Telegram clients

## 2. In Scope

Primary implementation targets:

- backend persistence and API support for published signal lifecycle state
- lifecycle creation immediately after successful Telegram publication
- automated lifecycle monitoring based on market data
- admin override and ambiguity handling
- outcome projection from lifecycle closure into internal reporting and score surfaces
- operator-facing lifecycle visibility in `Home`, `Telegram`, and ops surfaces
- focused backend, frontend, and E2E verification for the full lifecycle loop

Primary files expected to move:

- `database.py`
- `routes/signals.py`
- `routes/system.py`
- `routes/analysis_reports.py`
- `core/signals/outcomes.py`
- `core/signals/runs.py`
- new helper modules under `core/signals/` for lifecycle logic if needed
- `core/horus/monitor.py`
- `core/horus/telegram.py`
- `frontend/src/app/HomeClientPage.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`
- `frontend/src/app/telegram/components/TelegramStatusCard.tsx`
- `frontend/src/app/status/**`
- `frontend/src/app/audit/**`
- related tests under `tests/`, `frontend/src/app/**/*.test.tsx`, and `frontend/e2e/`

Out of scope for this slice:

- Telegram follow-up template redesign as its own phase
- client-facing track-record pages
- bringing unpublished desk candidates into the formal lifecycle
- formal lifecycle participation for `News` or `Sectors`
- portfolio auto-trading redesign
- Autopilot feedback tuning based on lifecycle results

## 3. Execution Rules

These rules apply across the rollout:

1. Treat published Horus signals as the only formal lifecycle participants.
2. Do not treat publication as fill; `OPEN` requires real price interaction with entry.
3. Keep the lifecycle authority separate from `SignalOutcome` and `HorusExecution` even where they integrate.
4. Project lifecycle closure into reporting; do not let reporting become the live authority.
5. Keep public Telegram content provenance-free and Horus-branded.
6. Use conservative handling for ambiguous same-bar sequencing unless lower-granularity data resolves it.
7. Make every admin override append an event instead of silently mutating lifecycle truth.
8. Land persistence and lifecycle APIs before frontend visibility work.
9. Finish each work package with verification so the state machine stays trustworthy.

## 4. Work Package Sequence

Execute in this order:

1. `PSLA-P1` Lifecycle persistence and backend contract
2. `PSLA-P2` Publish hook and lifecycle monitor engine
3. `PSLA-P3` Override, ambiguity, and admin-control surfaces
4. `PSLA-P4` Outcome projection and scoring integration
5. `PSLA-P5` Frontend lifecycle visibility rollout
6. `PSLA-P6` Full-loop verification and regression lock

This order is intentional:

- lifecycle persistence must exist before publish hooks can create records
- publish and monitor logic must exist before overrides make sense
- reporting and scoring should depend on terminal lifecycle truth, not placeholders
- frontend visibility should follow stable backend state and APIs
- verification should validate the integrated lifecycle loop, not partial scaffolding

## 5. Work Packages

### PSLA-P1. Lifecycle Persistence And Backend Contract

Purpose:

Create a dedicated published-signal lifecycle authority and event stream without twisting `SignalOutcome` or `HorusExecution` into roles they do not own.

Target files:

- `database.py`
- `routes/signals.py`
- `routes/system.py`
- `core/signals/outcomes.py`
- new helper module(s) under `core/signals/`
- `tests/conftest.py`
- new backend tests such as `tests/test_published_signal_lifecycle.py`

Tasks:

1. Add dedicated persistence for:
   - `PublishedSignalLifecycle`
   - `PublishedSignalLifecycleEvent`
2. Support fields for:
   - recommendation, run, and delivery linkage
   - lane, source module, and operating mode
   - `PUBLISHED`, `OPEN`, `TP1_HIT`, `TP2_HIT`, `STOP_LOSS_HIT`, `EXPIRED`, `CANCELLED`, and internal `AMBIGUOUS`
   - planned and filled entry prices
   - active stop state
   - `TP1` and `TP2`
   - close price and close reason
   - expiry timing
   - override notes and details payload
3. Add backend serialization helpers and read endpoints for:
   - lifecycle summary counts
   - active lifecycle queue
   - lifecycle detail view
   - lifecycle event history
4. Extend system status payloads to expose:
   - lifecycle monitor health
   - ambiguous count
   - stale active lifecycle count if relevant

Deliverables:

- stable backend lifecycle contract
- dedicated persistence layer for published-signal truth
- lifecycle read surfaces for operator UIs

Verification:

- `pytest tests/test_published_signal_lifecycle.py tests/test_strategy_and_system.py`

Acceptance criteria:

- the backend can represent live published-signal state independently of outcomes and internal execution
- lifecycle state and events are queryable through stable operator-facing APIs

### PSLA-P2. Publish Hook And Lifecycle Monitor Engine

Purpose:

Create lifecycle records immediately after publish, then advance them automatically through the state machine using market data.

Target files:

- `routes/signals.py`
- `core/signals/publishing.py`
- `core/horus/monitor.py`
- `core/horus/telegram.py`
- new lifecycle monitor helper module(s) under `core/signals/`
- `tests/test_signals_publish_service.py`
- `tests/test_horus_monitor_service.py`
- new lifecycle monitor tests

Tasks:

1. Hook lifecycle creation into successful Telegram publish flow so:
   - only actual published signals create lifecycle records
   - `PUBLISHED` records carry lane, expiry, entry, stop, `TP1`, and `TP2`
2. Implement lifecycle monitor logic for:
   - `PUBLISHED -> OPEN`
   - `OPEN -> TP1_HIT`
   - `TP1_HIT -> TP2_HIT`
   - `OPEN` or `TP1_HIT -> STOP_LOSS_HIT`
   - `PUBLISHED -> EXPIRED`
3. Apply the approved rule:
   - after `TP1_HIT`, automatically move active stop to breakeven
4. Detect ambiguous same-bar conditions and route them to internal `AMBIGUOUS`
5. Record every automatic transition as a lifecycle event

Deliverables:

- lifecycle record creation on publish
- scheduled lifecycle transition engine
- evented transition history for all automatic state changes

Verification:

- `pytest tests/test_signals_publish_service.py tests/test_horus_monitor_service.py tests/test_published_signal_lifecycle.py`

Acceptance criteria:

- published signals enter lifecycle automatically
- lifecycle transitions follow the approved state machine
- `TP1` triggers breakeven stop logic automatically

### PSLA-P3. Override, Ambiguity, And Admin-Control Surfaces

Purpose:

Give the admin safe override power while keeping lifecycle truth auditable and explicit.

Target files:

- `routes/signals.py`
- new lifecycle override helper module(s) under `core/signals/`
- `frontend/src/app/status/**`
- `frontend/src/app/audit/**`
- new backend and frontend tests for override behavior

Tasks:

1. Add mutation endpoints for:
   - force open
   - correct fill price
   - mark `TP1`
   - mark `TP2`
   - mark stop hit
   - cancel signal
   - reopen or reclassify ambiguous records
2. Ensure every override:
   - writes a lifecycle event
   - records actor, time, and notes
   - updates lifecycle state through a controlled transition path
3. Add ambiguity-review surfaces for operators:
   - ambiguous lifecycle list
   - stale unresolved items
   - override activity log
4. Prevent silent mutation of terminal lifecycle states without explicit override semantics

Deliverables:

- admin override API surface
- ambiguity review path
- audit-safe override event stream

Verification:

- `pytest tests/test_published_signal_lifecycle.py tests/test_strategy_and_system.py`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/status src/app/audit`

Acceptance criteria:

- admins can correct lifecycle truth without bypassing the audit trail
- ambiguous cases are visible and resolvable

### PSLA-P4. Outcome Projection And Scoring Integration

Purpose:

Project terminal lifecycle truth into the internal reporting layer and keep the formal track record limited to published Horus signals.

Target files:

- `core/signals/outcomes.py`
- `core/signals/runs.py`
- `routes/analysis_reports.py`
- `routes/signals.py`
- `tests/test_signals_outcomes_service.py`
- `tests/test_analysis_reports.py`
- `tests/test_signals_run_service.py`

Tasks:

1. Add lifecycle-to-outcome projection so terminal lifecycle states create or update the derived outcome layer.
2. Ensure unpublished research ideas do not enter the formal commercial score base.
3. Add scoring and reporting cuts for:
   - lane
   - source module
   - operating mode
   - rolling time windows
4. Add metrics for:
   - publish count
   - fill rate
   - expiry rate
   - `TP1` hit rate
   - win rate
   - stop-loss rate
   - average realized return
   - expectancy per published signal
   - average time to open
   - average time to terminal resolution
5. Keep `SignalOutcome` as the reporting projection, not the live lifecycle authority.

Deliverables:

- trustworthy published-signal scoring boundary
- derived outcome integration
- reporting-ready lifecycle metrics

Verification:

- `pytest tests/test_signals_outcomes_service.py tests/test_analysis_reports.py tests/test_signals_run_service.py`

Acceptance criteria:

- the formal track record reflects only published Horus signals
- lifecycle closure feeds reporting without replacing lifecycle truth

### PSLA-P5. Frontend Lifecycle Visibility Rollout

Purpose:

Expose lifecycle state to operators in the right places without leaking internals into client messaging.

Target files:

- `frontend/src/app/HomeClientPage.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`
- `frontend/src/app/telegram/components/TelegramStatusCard.tsx`
- `frontend/src/app/status/**`
- `frontend/src/app/audit/**`
- new lifecycle frontend helper(s) if needed
- related frontend tests

Tasks:

1. Add a published lifecycle summary strip or panel on `Home` for:
   - `Published`
   - `Open`
   - `TP1`
   - `Closed Win`
   - `Closed Loss`
   - `Expired`
2. Make `Telegram` show recent published lifecycle state so operators can see:
   - what was sent
   - what is waiting for fill
   - what hit `TP1`
   - what closed
3. Add status and audit visibility for:
   - monitor health
   - ambiguous items
   - override activity
4. Keep Telegram client content unchanged and Horus-branded; all lifecycle metadata remains internal

Deliverables:

- lifecycle visibility on anchor operator routes
- ops surfaces for ambiguity and override review
- no client-facing provenance leakage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/components/HomeShell.test.tsx src/app/components/HomeSignalsPanel.test.tsx src/app/telegram/page.test.tsx src/app/telegram/components/TelegramSignalPanel.test.tsx src/app/telegram/components/TelegramStatusCard.test.tsx`

Acceptance criteria:

- operators can see lifecycle state at a glance on `Home` and `Telegram`
- lifecycle internals stay confined to operator surfaces

### PSLA-P6. Full-Loop Verification And Regression Lock

Purpose:

Validate the published signal lifecycle end to end and lock the phase with targeted regression coverage.

Target files:

- touched files from `PSLA-P1` through `PSLA-P5`
- `tests/test_signals_publish_service.py`
- `tests/test_published_signal_lifecycle.py`
- `tests/test_horus_monitor_service.py`
- `tests/test_signals_outcomes_service.py`
- `tests/test_analysis_reports.py`
- `frontend/e2e/home.spec.ts`
- `frontend/e2e/interactive_controls.spec.ts`
- `frontend/e2e/e2e_crawl.spec.ts`
- `frontend/e2e/_phase3_audit.spec.ts`

Tasks:

1. Verify the full lifecycle loop:
   - Horus publishes a signal
   - lifecycle record is created
   - signal becomes `OPEN` only when entry is touched
   - `TP1` moves stop to breakeven
   - signal resolves to `TP2`, stop, expiry, or ambiguity review
   - derived reporting surfaces show the result
2. Run frontend build verification.
3. Run focused backend suites for lifecycle, publish, monitor, outcomes, reporting, and status.
4. Run route and audit checks to ensure the new lifecycle visibility does not destabilize the shell.
5. Record any residual out-of-scope gaps separately from the lifecycle phase.

Deliverables:

- verified published-signal lifecycle loop
- regression evidence for backend, frontend, and route-level behavior
- explicit residual-issues list if anything remains outside scope

Verification:

- `pytest tests/test_signals_publish_service.py tests/test_published_signal_lifecycle.py tests/test_horus_monitor_service.py tests/test_signals_outcomes_service.py tests/test_analysis_reports.py`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e -- home.spec.ts interactive_controls.spec.ts e2e_crawl.spec.ts`
- `npm --prefix frontend run test:e2e:audit`

Acceptance criteria:

- the full published signal lifecycle works from release through resolution and scoring
- operator surfaces show lifecycle truth without leaking internals to clients
- no critical monitoring, reporting, or route regressions remain in the verified phase

## 6. Risks And Controls

### Risk 1. The lifecycle overstates fills by treating publication as entry

Control:

- require real price interaction with entry before `OPEN`
- test `PUBLISHED -> OPEN` explicitly against market data behavior

### Risk 2. Published-signal truth gets mixed with research outcomes or internal execution objects

Control:

- keep lifecycle persistence dedicated and separate
- treat `SignalOutcome` as derived reporting and `HorusExecution` as internal execution companion only

### Risk 3. Ambiguous same-bar conditions inflate performance

Control:

- add explicit ambiguity handling
- default to conservative house-rule resolution unless better data is available

### Risk 4. Admin overrides silently corrupt track-record credibility

Control:

- require every override to emit an event
- surface override activity in audit-facing views

### Risk 5. Frontend visibility grows faster than backend truth

Control:

- land persistence, lifecycle APIs, and monitor logic before UI visibility
- keep frontend state read-oriented until backend transition rules are stable

## 7. Recommended Execution Notes

- Start with `PSLA-P1` and `PSLA-P2` back-to-back so lifecycle records and transitions exist before reporting or UI work.
- Keep the first lifecycle engine focused on deterministic state transitions; follow-up Telegram automation can remain a later phase.
- Reuse current publish and outcome code where it helps, but do not force the new lifecycle model into old model boundaries.
- Keep `Home` and `Telegram` aligned as the two main operator surfaces for lifecycle visibility.
- Treat the commercial boundary as hard: only published Horus signals count.

## 8. Recommended Next Move After This Plan

Execute `PSLA-P1` and `PSLA-P2` as the first active implementation slice. They create the dedicated lifecycle authority and automatic transition engine that every later scoring, override, and visibility surface depends on.
