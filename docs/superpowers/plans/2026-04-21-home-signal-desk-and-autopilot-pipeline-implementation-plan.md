# Home Signal Desk And Autopilot Pipeline Implementation Plan

Date: 2026-04-21
Based on:

- `docs/superpowers/specs/2026-04-21-home-signal-desk-and-autopilot-pipeline-design.md`
- `database.py`
- `routes/signals.py`
- `routes/scanner.py`
- `routes/settings.py`
- `routes/system.py`
- `core/signals/boundary.py`
- `core/signals/publishing.py`
- `core/signals/workspace.py`
- `frontend/src/app/HomeClientPage.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- `frontend/src/app/hooks/useHomeRuntime.ts`
- `frontend/src/app/hooks/useHomeActions.ts`
- `frontend/src/app/context/GlobalDataContext.tsx`
- `frontend/src/app/components/config/navigation.ts`
- `frontend/src/app/scanner/page.tsx`
- `frontend/src/app/scanner/components/ScannerResultsTable.tsx`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/components/OracleAiReportPanel.tsx`
- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/components/TelegramShell.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`
- `frontend/src/app/telegram/hooks/useTelegramBroadcasts.ts`
- `frontend/src/app/telegram/hooks/useTelegramRuntime.ts`
- `tests/test_signals_run_service.py`
- `tests/test_signals_publish_service.py`
- `tests/test_telegram_broadcast.py`
- `frontend/e2e/home.spec.ts`
- `frontend/e2e/interactive_controls.spec.ts`

Track: Home Signal Desk And Autopilot Rollout
Status: Executed
Owner model: Single owner

## Execution Outcome

Execution status: Completed in one continuous implementation track.

Completed rollout coverage:

- `HSDA-P1` signal pipeline persistence and API foundation
- `HSDA-P2` shared desk state and `Home` data-loading rollout
- `HSDA-P3` `Home` daily signal desk UI and navigation hierarchy
- `HSDA-P4` feeder route promotion integration across Scanner, Oracle, Whales, Traps, and Analytics
- `HSDA-P5` Telegram release rail and operator policy surface
- `HSDA-P6` Autopilot direct publishing and system-status integration
- `HSDA-P7` full-loop verification and regression lock

Final verification evidence:

- backend: `73 passed` via `tests/test_signals_run_service.py`, `tests/test_signals_publish_service.py`, `tests/test_telegram_broadcast.py`, `tests/test_scanner_and_data.py`, `tests/test_strategy_and_system.py`, and `tests/test_signals_desk.py`
- frontend build: `npm run build` passed
- route E2E: `home.spec.ts`, `e2e_crawl.spec.ts`, and `interactive_controls.spec.ts` passed
- audit E2E: `npm run test:e2e:audit` passed

Residual notes:

- `News` and `Sectors` were intentionally not promoted into the desk contract in this rollout because their current surfaces do not expose reliable entry, stop, and target fields.
- internal provenance remains available only on operator-facing and audit-facing surfaces; outgoing Telegram client messages stay `Horus`-branded and provenance-free.

## 1. Planning Goal

Implement the approved `Home`-centered signal pipeline as one ordered rollout that can be executed in a single uninterrupted implementation session.

The rollout should:

1. establish one shared backend contract for signal lanes, publish batches, operating mode, and policy
2. turn `Home` into the daily `Intraday`, `Swing`, and `Position` signal desk
3. make feeder routes promote candidates into the desk instead of ending in isolation
4. turn `Telegram` into the release rail for finalized or autopilot-authorized batches
5. enable `Autopilot` to use `AI Assist` to publish directly under internal policy and audit controls
6. preserve one client-facing voice: `Horus`

## 2. In Scope

Primary implementation targets:

- backend persistence and API support for lane-aware candidates, batch composition, publish policy, and operating mode
- extension of the existing `core.signals` subsystem instead of building a separate parallel pipeline
- `Home` data and UI transformation into a three-lane signal desk
- feeder promotion seams from the major analysis routes
- Telegram refactor into a dispatch-first release surface
- visible `Manual`, `AI Assist`, and `Autopilot` operator state
- internal failure, retry, and audit visibility for publish operations
- focused backend, frontend, and E2E verification for the full loop

Primary files expected to move:

- `database.py`
- `routes/signals.py`
- `routes/scanner.py`
- `routes/settings.py`
- `routes/system.py`
- `core/signals/boundary.py`
- `core/signals/publishing.py`
- `core/signals/workspace.py`
- new helper modules under `core/signals/` if the current files become too dense
- `frontend/src/app/context/GlobalDataContext.tsx`
- new `frontend/src/app/context/SignalDeskContext.tsx`
- `frontend/src/app/HomeClientPage.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- new desk components under `frontend/src/app/components/signal-desk/`
- `frontend/src/app/hooks/useHomeRuntime.ts`
- `frontend/src/app/hooks/useHomeActions.ts`
- `frontend/src/app/components/config/navigation.ts`
- `frontend/src/app/scanner/**`
- `frontend/src/app/oracle/**`
- `frontend/src/app/whales/**`
- `frontend/src/app/traps/**`
- `frontend/src/app/news/**`
- `frontend/src/app/analytics/**`
- `frontend/src/app/sectors/**`
- `frontend/src/app/telegram/**`
- related tests under `tests/`, `frontend/src/app/**/*.test.tsx`, and `frontend/e2e/`

Out of scope for this slice:

- rebuilding the underlying analysis engines themselves
- new outbound channels beyond Telegram
- exposing internal publish provenance to clients
- portfolio auto-trading redesign
- broad monetization, subscription, or client entitlement work
- cosmetic route redesign outside the new signal pipeline and hierarchy work

## 3. Execution Rules

These rules apply across the rollout:

1. Extend the existing `routes/signals.py` and `core/signals/*` path first; do not create a second competing signal-pipeline authority.
2. Treat `Home` as the single editorial center once the rollout starts; avoid leaving batch composition split between `Home` and `Telegram`.
3. Keep `Intraday`, `Swing`, and `Position` as explicit first-class lanes across persistence, API, UI, and publish policy.
4. Preserve one client-facing brand voice. Internal mode and provenance must never leak into outgoing Telegram content.
5. Replace scattered Telegram `auto_*` toggles with one visible operating-mode and policy model, even if legacy fields are preserved temporarily for migration.
6. Prefer additive compatibility shims over disruptive rewrites where they keep the rollout moving in one session.
7. Land backend contracts before frontend desk UI, and land the desk before release-rail refactors.
8. Full `Autopilot` authority must always pass through a policy gate, failure handling path, and retryable delivery record.
9. Keep the rollout vertically integrated. Each major package should finish with verification, not deferred uncertainty.

## 4. Work Package Sequence

Execute in this order:

1. `HSDA-P1` Signal pipeline persistence and API foundation
2. `HSDA-P2` Shared desk state and Home data-loading rollout
3. `HSDA-P3` Home Daily Signal Desk UI and navigation hierarchy
4. `HSDA-P4` Feeder route promotion integration
5. `HSDA-P5` Telegram release rail and operator policy surface
6. `HSDA-P6` Autopilot direct publishing and system-status integration
7. `HSDA-P7` Full-loop verification and regression lock

This order is intentional:

- the desk and release rail cannot be stable without one shared backend contract
- `Home` must gain real state authority before feeder routes can hand off into it
- feeder integration should exist before Telegram is re-centered around finalized batches
- `Autopilot` should be enabled only after lanes, policy, and dispatch surfaces are already explicit
- verification should validate the integrated system, not partial intermediate scaffolding

## 5. Work Packages

### HSDA-P1. Signal Pipeline Persistence And API Foundation

Purpose:

Create the backend contract for lane-aware candidates, batch composition, operating mode, and publish policy using the existing signal subsystem as the base.

Target files:

- `database.py`
- `routes/signals.py`
- `routes/settings.py`
- `routes/system.py`
- `core/signals/boundary.py`
- `core/signals/publishing.py`
- `core/signals/workspace.py`
- `tests/test_signals_boundary_service.py`
- `tests/test_signals_run_service.py`
- `tests/test_signals_publish_service.py`
- `tests/test_signals_coverage.py`

Tasks:

1. Extend the persistence model to support:
   - lane identity: `INTRADAY`, `SWING`, `POSITION`
   - internal batch composition state
   - operating mode state: `MANUAL`, `AI_ASSIST`, `AUTOPILOT`
   - publish policy state
   - internal dispatch metadata that remains invisible to clients
2. Decide the smallest additive schema that keeps the rollout honest:
   - extend `SignalRecommendation` and `SignalDelivery` where practical
   - add dedicated desk batch tables only where current tables cannot express the workflow cleanly
3. Add or extend API endpoints for:
   - lane summaries
   - queue candidates
   - batch composition
   - operating mode read/write
   - publish policy read/write
   - failed outbound and retryable batch state
4. Keep backward-compatible response behavior where existing consumers still rely on legacy signal payloads during the transition.
5. Extend `routes/system.py` and `routes/settings.py` so operating mode and policy can appear in operator-facing system/config surfaces.

Deliverables:

- stable backend contract for the desk pipeline
- lane-aware signal model
- operating mode and policy API surfaces
- migration-safe persistence changes

Verification:

- `pytest tests/test_signals_boundary_service.py tests/test_signals_run_service.py tests/test_signals_publish_service.py tests/test_signals_coverage.py`

Acceptance criteria:

- the backend can represent lane-specific candidates and internal publish state
- operating mode and policy are queryable without depending on ad hoc legacy toggles
- the new contract extends the existing signals subsystem instead of bypassing it

### HSDA-P2. Shared Desk State And Home Data-Loading Rollout

Purpose:

Introduce a frontend desk-state seam so `Home` can load lane summaries, candidate queues, publish readiness, mode, and failed outbound state as first-class desk data.

Target files:

- `frontend/src/app/context/GlobalDataContext.tsx`
- `frontend/src/app/context/GlobalDataContext.test.tsx`
- new `frontend/src/app/context/SignalDeskContext.tsx`
- new `frontend/src/app/context/SignalDeskContext.test.tsx`
- `frontend/src/app/hooks/useHomeRuntime.ts`
- `frontend/src/app/hooks/useHomeRuntime.test.tsx`
- `frontend/src/app/hooks/useHomeActions.ts`
- `frontend/src/app/hooks/useHomeActions.test.tsx`
- `frontend/src/app/lib/` new desk-transform helpers if needed

Tasks:

1. Add a dedicated desk-state context or equivalent shared hook path rather than forcing the workflow into the current dashboard-only payload.
2. Teach `Home` to request:
   - lane summaries
   - ranked intake per lane
   - batch composition state
   - publish readiness
   - active operating mode
   - failed outbound state
3. Keep existing dashboard telemetry only where it still supports the desk, but demote it from primary authority.
4. Add mutation actions for:
   - changing operating mode
   - moving candidates into or out of a batch
   - triggering AI Assist draft composition
   - arming or disarming Autopilot
5. Preserve compatibility with the broader `GlobalDataContext` routing model so other routes do not regress while `Home` gains a new state shape.

Deliverables:

- desk-focused frontend data seam
- lane-ready `Home` runtime state
- action hooks for the desk workflow

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/context/GlobalDataContext.test.tsx src/app/context/SignalDeskContext.test.tsx src/app/hooks/useHomeRuntime.test.tsx src/app/hooks/useHomeActions.test.tsx`

Acceptance criteria:

- `Home` can load desk-specific state without pretending it is only dashboard data
- lane state, mode state, and failed outbound state are available in one coherent frontend seam

### HSDA-P3. Home Daily Signal Desk UI And Navigation Hierarchy

Purpose:

Turn `Home` into the primary three-lane editorial signal desk and make the shell hierarchy visibly favor `Home` and `Telegram`.

Target files:

- `frontend/src/app/HomeClientPage.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/components/HomeSignalsPanel.tsx`
- `frontend/src/app/components/HomeMetricsBar.tsx`
- new desk components under `frontend/src/app/components/signal-desk/`
- `frontend/src/app/components/config/navigation.ts`
- `frontend/src/app/components/HomeShell.test.tsx`
- `frontend/src/app/components/HomeSignalsPanel.test.tsx`
- `frontend/src/app/page.test.tsx` if present or new route-level tests
- `frontend/e2e/home.spec.ts`

Tasks:

1. Replace the current dashboard-first `Home` composition with a real desk layout that exposes:
   - `Intraday Lane`
   - `Swing Lane`
   - `Position Lane`
2. Give each lane its own:
   - ranked intake
   - batch composer
   - release readiness section
3. Surface operating mode, Autopilot armed state, queue health, and failed outbound warnings directly in `Home`.
4. Retain only the telemetry that supports operator context, not the old dashboard-first hierarchy.
5. Update the route ribbon hierarchy so `Home` and `Telegram` read as the two anchor destinations and the remaining routes read as grouped lanes or support surfaces instead of equal peers.

Deliverables:

- `Home` as the daily editorial center
- three explicit signal lanes
- visible hierarchy correction in the shell

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/components/HomeShell.test.tsx src/app/components/HomeSignalsPanel.test.tsx`
- `npm --prefix frontend run test:e2e -- home.spec.ts`

Acceptance criteria:

- `Home` reads as the product center of gravity
- the three lanes are explicit and operational
- navigation no longer presents every route as an equal peer

### HSDA-P4. Feeder Route Promotion Integration

Purpose:

Make the major analysis routes feed the desk directly instead of leaving the operator to bridge analysis into action mentally.

Target files:

- `frontend/src/app/scanner/page.tsx`
- `frontend/src/app/scanner/components/ScannerResultsTable.tsx`
- `frontend/src/app/scanner/components/ScannerShell.tsx`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/components/OracleAiReportPanel.tsx`
- `frontend/src/app/oracle/components/OracleShell.tsx`
- `frontend/src/app/whales/**`
- `frontend/src/app/traps/**`
- `frontend/src/app/news/**`
- `frontend/src/app/analytics/**`
- `frontend/src/app/sectors/**`
- new shared feeder action component(s) under `frontend/src/app/components/`
- `frontend/src/app/scanner/page.test.tsx`
- `frontend/src/app/oracle/page.test.tsx`
- `frontend/e2e/interactive_controls.spec.ts`

Tasks:

1. Add a shared promotion action seam that can send a candidate into:
   - `Intraday Lane`
   - `Swing Lane`
   - `Position Lane`
2. Implement the shared promotion seam first in Scanner and Oracle, then mirror the same interaction pattern into the other feeder routes.
3. Ensure promotion actions carry enough data for the desk contract:
   - lane type
   - ticker
   - risk levels
   - confidence
   - rationale or enrichment metadata
4. Keep feeder pages specialized. Do not re-home editorial batch composition into them.
5. Preserve route-specific depth while making the next step obvious.

Deliverables:

- shared feeder promotion interaction
- desk handoff from the major signal-producing routes
- consistent route-to-desk vocabulary

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner/page.test.tsx src/app/oracle/page.test.tsx`
- `npm --prefix frontend run test:e2e -- interactive_controls.spec.ts`

Acceptance criteria:

- Scanner and Oracle can promote candidates directly into the correct lane
- secondary feeder routes follow the same handoff contract
- the operator no longer has to guess where analysis should go next

### HSDA-P5. Telegram Release Rail And Operator Policy Surface

Purpose:

Refactor `Telegram` into a dispatch-first release rail that consumes finalized batches and exposes the operator-facing policy and release controls.

Target files:

- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/components/TelegramShell.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`
- `frontend/src/app/telegram/components/TelegramBroadcastPanel.tsx`
- `frontend/src/app/telegram/components/TelegramActivityLog.tsx`
- `frontend/src/app/telegram/components/TelegramStatusCard.tsx`
- new Telegram desk-dispatch components if needed
- `frontend/src/app/telegram/hooks/useTelegramBroadcasts.ts`
- `frontend/src/app/telegram/hooks/useTelegramRuntime.ts`
- `frontend/src/app/telegram/hooks/useTelegramConfig.ts`
- `frontend/src/app/telegram/page.test.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.test.tsx`
- `frontend/src/app/telegram/hooks/useTelegramBroadcasts.test.tsx`

Tasks:

1. Re-center `Telegram` around:
   - finalized batch preview
   - channel target
   - send or schedule controls
   - failed outbound retry
   - internal release history
2. Demote or remove local signal invention controls that now belong to `Home` or feeder routes.
3. Surface operating mode and policy state in Telegram as operator context, not as client-facing content.
4. Keep the public message output branded only as `Horus`.
5. Preserve Telegram config and connectivity workflows while shifting the main route purpose from authoring-first to dispatch-first.

Deliverables:

- Telegram as the release rail
- internal operator-facing policy and release controls
- removal of the old "Telegram as another isolated module" feel

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/telegram/page.test.tsx src/app/telegram/components/TelegramSignalPanel.test.tsx src/app/telegram/hooks/useTelegramBroadcasts.test.tsx src/app/telegram/hooks/useTelegramRuntime.test.tsx`

Acceptance criteria:

- Telegram receives and dispatches desk-composed batches
- Telegram still supports operator control, but no longer acts as the primary place where signals are invented
- client-facing messages remain provenance-free and Horus-branded

### HSDA-P6. Autopilot Direct Publishing And System-Status Integration

Purpose:

Enable direct Autopilot publishing through AI Assist and wire that state into operator-facing system and settings surfaces.

Target files:

- `routes/signals.py`
- `routes/settings.py`
- `routes/system.py`
- `core/signals/publishing.py`
- `core/signals/workspace.py`
- `core/signals/boundary.py`
- `frontend/src/app/telegram/hooks/useTelegramRuntime.ts`
- `frontend/src/app/telegram/components/TelegramStatusCard.tsx`
- `frontend/src/app/components/systemBootModel.ts`
- `frontend/src/app/components/systemBootModel.test.ts`
- `tests/test_signals_publish_service.py`
- `tests/test_telegram_broadcast.py`
- `tests/test_strategy_and_system.py`

Tasks:

1. Implement the `Autopilot` execution path so AI Assist can:
   - assemble batches
   - generate release copy
   - publish directly
   - record internal audit and delivery state
2. Enforce hard policy gates for:
   - lane-specific thresholds
   - missing fields
   - weak rationale
   - duplicate suppression
   - publish windows
   - retry handling
3. Ensure `routes/system.py` and related status payloads can expose:
   - current mode
   - Autopilot armed state
   - queue health or publish-blocked state
4. Keep all internal provenance restricted to operator or audit surfaces only.
5. Preserve manual override, kill switch, and instant downgrade behavior.

Deliverables:

- direct Autopilot publish capability
- policy-gated AI Assist execution path
- operator-visible system status for the new mode model

Verification:

- `pytest tests/test_signals_publish_service.py tests/test_telegram_broadcast.py tests/test_strategy_and_system.py`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/components/systemBootModel.test.ts src/app/telegram/hooks/useTelegramRuntime.test.tsx`

Acceptance criteria:

- Autopilot can publish without admin approval when armed and policy allows
- failures remain retryable and visible internally
- system and Telegram status surfaces reflect the new operating mode truthfully

### HSDA-P7. Full-Loop Verification And Regression Lock

Purpose:

Validate the full product loop end to end and lock the rollout with targeted regression coverage.

Target files:

- touched files from `HSDA-P1` through `HSDA-P6`
- `tests/test_signals_run_service.py`
- `tests/test_signals_publish_service.py`
- `tests/test_telegram_broadcast.py`
- `tests/test_scanner_and_data.py`
- `frontend/e2e/home.spec.ts`
- `frontend/e2e/interactive_controls.spec.ts`
- `frontend/e2e/e2e_crawl.spec.ts`
- `frontend/e2e/_phase3_audit.spec.ts`

Tasks:

1. Verify the end-to-end loop:
   - feeder creates candidate
   - candidate lands in the correct lane
   - batch composes on Home
   - Telegram dispatch receives finalized output
   - Autopilot publishes directly when armed
2. Run build verification for the frontend.
3. Run focused backend suites for signals, publish, Telegram delivery, and system status.
4. Run the route crawl and layout audit to ensure the hierarchy and desk UI did not destabilize the broader app.
5. Record any residual out-of-scope gaps separately from the rollout itself.

Deliverables:

- verified end-to-end signal desk pipeline
- regression evidence for backend, frontend, and route-level behavior
- explicit residual-issues list if anything remains outside scope

Verification:

- `pytest tests/test_signals_run_service.py tests/test_signals_publish_service.py tests/test_telegram_broadcast.py tests/test_scanner_and_data.py`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e -- home.spec.ts interactive_controls.spec.ts e2e_crawl.spec.ts`
- `npm --prefix frontend run test:e2e:audit`

Acceptance criteria:

- the full signal lifecycle works from feeder to desk to release rail
- Autopilot and AI Assist behavior is policy-safe and internally traceable
- no critical route, layout, or dispatch regressions remain in the verified rollout

## 6. Risks And Controls

### Risk 1. The rollout leaves legacy direct-broadcast behavior alive beside the new desk pipeline

Control:

- centralize new publish authority in `routes/signals.py` and `core/signals/*`
- treat old route-local broadcast helpers as compatibility shims to be demoted or removed during the rollout

### Risk 2. Home is visually redesigned without gaining real editorial authority

Control:

- land desk-state and batch APIs before UI transformation
- require lane, mode, and failed-outbound state to exist before the Home redesign is considered complete

### Risk 3. Signal horizons blur back into one undifferentiated queue

Control:

- enforce `INTRADAY`, `SWING`, and `POSITION` in persistence, API, desk state, and UI
- block ambiguous candidate promotion paths

### Risk 4. Autopilot publishes unsafe or incomplete content

Control:

- require policy gates, blocking states, retry logic, and internal audit before enabling full publish authority
- keep kill switch and instant downgrade paths available throughout the rollout

### Risk 5. Frontend route integration balloons into a broad redesign that breaks one-session execution

Control:

- prefer shared promotion actions and shared desk state over route-specific rewrites
- keep feeder-route edits narrowly focused on the handoff contract

### Risk 6. Internal provenance leaks into Telegram client messages

Control:

- keep provenance fields in delivery records and internal operator surfaces only
- verify outgoing message builders continue to emit only `Horus`-branded client content

## 7. Recommended Execution Notes

- Start with `HSDA-P1` and `HSDA-P2` back-to-back. They establish the contract and state seams that every UI and Autopilot package depends on.
- Do not wait to "perfect" the schema before moving to `Home`; prefer the smallest additive persistence that fully supports lanes, mode, and policy.
- Reuse the existing `core.signals` publishing and delivery logic wherever possible so retry and audit semantics stay in one subsystem.
- Keep `Home` and `Telegram` tightly coordinated during the rollout, because they are the two anchor routes whose responsibilities are being redefined together.
- Make Scanner and Oracle the first feeder integrations, then spread the same promotion seam across the remaining feeder routes.
- Treat the public-client copy boundary as a hard invariant throughout implementation.

## 8. Recommended Next Move After This Plan

Execute `HSDA-P1` and `HSDA-P2` as the first active implementation slice. They create the backend and shared-state foundation required to finish the rest of the rollout in one uninterrupted build session without stopping for architectural rework.
