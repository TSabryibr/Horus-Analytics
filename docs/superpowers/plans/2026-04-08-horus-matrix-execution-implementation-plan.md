# Horus Matrix Execution Implementation Plan

Date: 2026-04-08
Based on:

- `docs/superpowers/specs/2026-04-08-horus-matrix-execution-design.md`
- `database.py`
- `core/signals/runs.py`
- `core/scheduling.py`
- `core/AutoTrader.py`
- `core/portfolio/identity.py`
- `frontend/src/app/context/PortfolioContext.tsx`
- `tests/test_signals_run_service.py`
- `tests/test_portfolio_identity_service.py`
- `tests/test_autotrader.py`

Track: Premium Signal Operations
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Implement `Horus` as the app's default premium execution matrix without breaking the existing simulation lanes.

This plan is organized to preserve four constraints:

1. `Daily Simulation` and `Intraday Simulation` stay functionally intact while `Horus` is introduced as an additive path.
2. `Horus` execution is ledger-first and idempotent, with no Telegram lifecycle message sent before the database state is durable.
3. After-hours daily signals never pretend to trade on the prior close; they must execute at the next working-session open or be skipped.
4. Matrix isolation must remain real in the data layer, not just visible in the UI.

## 2. In Scope

Primary backend scope:

- `Horus` portfolio seeding and default selection behavior
- dedicated execution-state schema for `Horus`
- signal-run intake changes required for repeated intraday and pre-close execution
- `Horus` open, update, pending-next-open, skip, monitor, and close behavior
- Telegram lifecycle messaging for `Horus`
- workspace/reporting integration needed to make `Horus` the default premium matrix

Primary frontend scope:

- default `active_matrix` preference for `Horus`
- no-regression matrix switching behavior for `USER` portfolios

Verification scope:

- backend tests for identity, signal intake, execution, scheduler behavior, monitoring, Telegram idempotency, and reporting
- focused frontend tests for portfolio-selection behavior

Out of scope:

- live broker execution
- subscriber billing or entitlement packaging
- broad UI redesign
- strategy re-optimization beyond the approved stop/target/trailing behavior changes for `Horus`

## 3. Execution Rules

These rules apply to every work package in this plan:

1. Keep the legacy simulation path operational until the new `Horus` path is verified.
2. Do not route `Horus` through `AutoTrader.process_scanner_signals()` as a shortcut if that would blur simulation and premium execution ownership.
3. Use the new execution-state table as the idempotency anchor for scheduler retries and Telegram lifecycle events.
4. Extend signal-run persistence before adding Horus execution consumers; repeated intraday scans need a stable run identity that is not limited to `run_date + scan_type`.
5. Daily after-hours signals must create pending-next-open intent, never same-session fills.
6. Automatic trailing logic may only ratchet risk tighter; any loosened stop or widened target must come from an explicit stronger-signal update event.
7. Keep public reporting and portfolio APIs backward compatible unless the package explicitly changes their contract.

## 4. Work Package Sequence

Execute in this order:

1. `HMX-P1` Portfolio identity and schema foundation
2. `HMX-P2` Signal-run intake normalization for intraday and pre-close
3. `HMX-P3` Horus immediate execution and single-position updates
4. `HMX-P4` Daily next-open execution and gap invalidation
5. `HMX-P5` Monitoring, close logic, and Telegram lifecycle idempotency
6. `HMX-P6` Workspace reporting integration and full regression pass

This order is intentional:

- package `HMX-P1` creates the storage and default-resolution contract every later package depends on
- package `HMX-P2` fixes the signal source-of-truth issue before `Horus` starts consuming runs
- packages `HMX-P3` through `HMX-P5` layer execution behavior in the same order the trade lifecycle unfolds
- package `HMX-P6` closes the loop on reporting, isolation, and end-to-end verification once lifecycle data is real

## 5. Work Packages

### HMX-P1. Portfolio Identity And Schema Foundation

Purpose:

Seed `Horus`, make it the default workspace, and introduce the dedicated execution-state schema and indexes required for reliable lifecycle management.

Target files:

- `database.py`
- `core/portfolio/identity.py`
- `core/horus/identity.py`
- `frontend/src/app/context/PortfolioContext.tsx`
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`
- `tests/test_portfolio_identity_service.py`
- `tests/test_horus_identity_service.py`
- `frontend/src/app/context/PortfolioContext.test.tsx`
- `frontend/src/app/components/hooks/useSidebarRuntime.test.tsx`

Tasks:

1. Add startup seeding for `Horus` as a `USER` portfolio while preserving `My Portfolio`, `Daily Simulation`, and `Intraday Simulation`.
2. Add the dedicated execution-state model, additive migration logic, and indexes for:
   - `portfolio + ticker + open-status`
   - `portfolio + recommendation`
   - `pending-next-open lookup`
   - lifecycle-message idempotency markers
3. Create `core/horus/identity.py` for `Horus` portfolio lookup and helper resolution.
4. Change backend default portfolio resolution to prefer `Horus`, then `My Portfolio`, then the first `USER` portfolio.
5. Change frontend auto-selection to prefer `Horus` with the same fallback order.
6. Keep `active_matrix` behavior limited to `USER` portfolios and verify no regression in manual switching.

Deliverables:

- seeded `Horus` portfolio and default workspace behavior
- dedicated execution-state schema scaffold
- backend and frontend regression coverage for default selection

Verification:

```powershell
python -m pytest tests/test_portfolio_identity_service.py tests/test_horus_identity_service.py -q
npm --prefix frontend test -- --runInBand src/app/context/PortfolioContext.test.tsx src/app/components/hooks/useSidebarRuntime.test.tsx
```

Acceptance criteria:

- a fresh app startup creates `Horus` if missing
- backend default portfolio resolution returns `Horus` when no portfolio is specified
- frontend first-load workspace selection prefers `Horus`
- `active_matrix` still lists `USER` portfolios cleanly
- the new execution table exists with additive migration behavior and no destructive changes

### HMX-P2. Signal-Run Intake Normalization For Intraday And Pre-Close

Purpose:

Give `Horus` one consistent signal source by extending the signal-run pipeline to support repeated intraday runs and explicit pre-close runs without colliding on the current `run_date + scan_type` uniqueness.

Target files:

- `database.py`
- `core/signals/runs.py`
- `routes/signals.py`
- `core/scheduling.py`
- `tests/test_signals_run_service.py`
- `tests/test_signals_p0.py`
- `tests/test_broadcast_simulation.py`
- `tests/test_horus_signal_intake_service.py`

Tasks:

1. Extend `SignalRun` identity so repeated same-day intraday runs can persist safely.
2. Add explicit pre-close run support instead of forcing pre-close behavior into the current daily-only or intraday-only contract.
3. Refactor scheduler paths so intraday, pre-close, and daily recommendation generation can all create durable runs and recommendations before `Horus` execution is attempted.
4. Preserve current Telegram summary broadcasting and simulation-routing behavior while the run model expands.
5. Keep scheduler reruns idempotent by using the new run identity rather than the current one-run-per-day intraday limitation.
6. Add tests for:
   - multiple intraday runs on the same date
   - a distinct pre-close run on the same date
   - no duplicate run creation under retry or rerun conditions

Deliverables:

- run persistence that supports repeated intraday execution windows
- explicit pre-close recommendation runs
- scheduler-backed recommendation records that `Horus` can consume consistently

Verification:

```powershell
python -m pytest tests/test_signals_run_service.py tests/test_signals_p0.py tests/test_broadcast_simulation.py tests/test_horus_signal_intake_service.py -q
```

Acceptance criteria:

- intraday runs no longer collide when the scheduler runs multiple times in one day
- pre-close runs persist distinctly and predictably
- daily, intraday, and pre-close recommendations all have a consistent durable source record
- existing broadcast simulation behavior remains intact

### HMX-P3. Horus Immediate Execution And Single-Position Updates

Purpose:

Implement the `Horus` executor for intraday and pre-close recommendations, including one-position-per-ticker enforcement and stronger-signal update behavior.

Target files:

- `core/horus/executor.py`
- `core/horus/identity.py`
- `core/horus/telegram.py`
- `core/scheduling.py`
- `core/PositionTracker.py`
- `core/portfolio/commands.py`
- `tests/test_horus_execution_service.py`
- `tests/test_autotrader.py`
- `tests/test_portfolio_command_service.py`

Tasks:

1. Build an execution service that consumes completed intraday and pre-close recommendations for the `Horus` portfolio.
2. Reuse the current simulation sizing rules for share calculation and entry sizing.
3. Open a new internal ledger position when no open `Horus` ticker position exists.
4. Detect an existing open `Horus` ticker position and convert the new recommendation into an update event rather than a duplicate entry.
5. Record prior and new stop/target/trailing values in execution history whenever a stronger-signal update is accepted.
6. Keep `Daily Simulation` and `Intraday Simulation` on their current path without inheriting `Horus` update logic accidentally.
7. Send `OPEN` and `UPDATE` lifecycle messages only after durable execution-state and ledger writes succeed.

Deliverables:

- `Horus` execution service for market-hours immediate entries
- one-position-per-ticker behavior with explicit update history
- ledger-first `OPEN` and `UPDATE` lifecycle messaging

Verification:

```powershell
python -m pytest tests/test_horus_execution_service.py tests/test_autotrader.py tests/test_portfolio_command_service.py -q
```

Acceptance criteria:

- an eligible intraday or pre-close recommendation opens one `Horus` position when no position exists
- a later stronger recommendation on the same open ticker updates the existing `Horus` trade instead of opening another
- the executor reuses existing sizing rules rather than inventing a new sizing path
- `OPEN` and `UPDATE` Telegram lifecycle events are not emitted before durable writes

### HMX-P4. Daily Next-Open Execution And Gap Invalidation

Purpose:

Turn after-hours daily signals into next-session execution intents with correct gap handling and invalidation behavior.

Target files:

- `core/horus/executor.py`
- `core/scheduling.py`
- `core/DataManager.py`
- `core/horus/telegram.py`
- `tests/test_horus_daily_open_service.py`
- `tests/test_horus_scheduler.py`

Tasks:

1. Add a pending-next-open execution path for daily recommendations that were not already activated earlier by intraday or pre-close.
2. Store the signaled entry and next eligible market session on the execution record.
3. At the next working-session open, resolve the tradable opening price from available intraday or opening-bar data.
4. Execute the pending trade when the gap from signal entry is within `1.5%`.
5. Mark the execution as gap-adjusted and send a Telegram note when actual entry differs from the original signal entry.
6. Skip the trade and record a deterministic invalidation reason when the opening gap exceeds `1.5%`.
7. Keep this path fail-closed when opening price data is stale or missing.

Deliverables:

- pending-next-open daily execution flow
- bounded `1.5%` gap adjustment behavior
- skip/invalidation path for oversized gaps

Verification:

```powershell
python -m pytest tests/test_horus_daily_open_service.py tests/test_horus_scheduler.py -q
```

Acceptance criteria:

- after-hours daily signals do not open same-session trades
- next-session open execution occurs only when the opening gap is within `1.5%`
- oversized gaps create `SKIPPED` lifecycle state and an invalidation message
- missing opening-price data fails closed without creating a false fill

### HMX-P5. Monitoring, Close Logic, And Telegram Lifecycle Idempotency

Purpose:

Add the dedicated `Horus` monitoring loop for stop-loss, target, and trailing exits, and make open/update/close/skip Telegram delivery idempotent under scheduler retries.

Target files:

- `core/horus/monitor.py`
- `core/horus/telegram.py`
- `core/scheduling.py`
- `core/PositionTracker.py`
- `database.py`
- `tests/test_horus_monitor_service.py`
- `tests/test_telegram_broadcast.py`
- `tests/verify_telegram_backoff.py`

Tasks:

1. Add a Horus-specific monitor entry point, separate from the current `SYSTEM` portfolio monitor path.
2. Evaluate close conditions in the approved order:
   - stop-loss
   - target
   - trailing-stop after trailing is armed
3. Keep automatic trailing ratchets one-way tighter once armed.
4. Allow stop/target loosening only through explicit stronger-signal update events recorded by the executor.
5. Persist close reason, linked trade row, realized PnL, and final execution-state status.
6. Add idempotent lifecycle-delivery tracking for `OPEN`, `UPDATE`, `CLOSE`, and `SKIP`.
7. Verify retries or scheduler overlaps do not duplicate lifecycle messages or close rows.

Deliverables:

- dedicated `Horus` trade monitor
- deterministic close reason handling
- idempotent Telegram lifecycle delivery

Verification:

```powershell
python -m pytest tests/test_horus_monitor_service.py tests/test_telegram_broadcast.py tests/verify_telegram_backoff.py -q
```

Acceptance criteria:

- stop-loss, target, and trailing conditions close `Horus` positions correctly
- automatic trailing never loosens risk by itself
- duplicate `Trade` rows are not created under overlapping monitor ticks
- lifecycle messages remain single-send under retry conditions

### HMX-P6. Workspace Reporting Integration And Full Regression Pass

Purpose:

Make `Horus` show up as the default premium workspace in reporting and verify matrix isolation end to end.

Target files:

- `routes/signals.py`
- `core/signals/workspace.py`
- `routes/ai_report.py`
- `routes/analysis_reports.py`
- `frontend/src/app/portfolio/page.tsx`
- `frontend/src/app/portfolio/page.test.tsx`
- `tests/test_signals_outcomes_service.py`
- `tests/test_analysis_reports.py`
- `tests/test_ai_report_boundary_service.py`
- `tests/test_horus_reporting_integration.py`

Tasks:

1. Route default workspace reporting to `Horus` via the updated identity helpers.
2. Make sure `Horus` execution and delivery state feeds workspace-level reporting and premium reporting summaries.
3. Keep portfolio-scoped caches and report snapshots isolated per portfolio.
4. Keep backward compatibility for existing report endpoints while ensuring `Horus` is the default context when no explicit portfolio is provided.
5. Verify `Horus`, `My Portfolio`, `Daily Simulation`, and `Intraday Simulation` remain behaviorally distinct in reporting and workspace metrics.
6. Run a broader backend and frontend regression pass across identity, signal intake, execution, monitoring, and reporting.

Deliverables:

- `Horus` as the default reporting workspace
- matrix-isolated reporting behavior
- end-to-end regression confidence for the full slice

Verification:

```powershell
python -m pytest tests/test_signals_outcomes_service.py tests/test_analysis_reports.py tests/test_ai_report_boundary_service.py tests/test_horus_reporting_integration.py -q
npm --prefix frontend test -- --runInBand src/app/portfolio/page.test.tsx src/app/components/hooks/useSidebarRuntime.test.tsx
```

Acceptance criteria:

- AI report and analysis-report defaults resolve to `Horus` when no explicit portfolio is provided
- report caching remains portfolio-scoped
- workspace metrics for `Horus` do not collapse into other matrices
- the regression suite proves the new execution lifecycle does not break existing simulation or reporting behavior

## 6. Risks and Controls

### Risk 1. Double execution between legacy simulations and Horus

Control:

- keep `Horus` execution in its own service path
- do not repurpose `AutoTrader.process_scanner_signals()` as the premium executor
- add explicit tests proving simulation portfolios still use the old route while `Horus` uses the new one

### Risk 2. Intraday run identity collisions

Control:

- address `SignalRun` uniqueness before adding `Horus` consumption
- add explicit same-day repeated intraday persistence tests in `HMX-P2`

### Risk 3. False premium fills from after-hours signals

Control:

- use pending-next-open intent rather than same-bar daily fills
- fail closed on missing or stale opening-price data
- keep the `1.5%` gap rule covered by direct tests

### Risk 4. Telegram duplication under retries

Control:

- use execution-state delivery markers as the message idempotency source
- keep delivery downstream from durable ledger changes
- test retry and overlapping scheduler scenarios directly

### Risk 5. Matrix isolation leaking through reporting

Control:

- rely on portfolio-scoped execution data for `Horus` workspace behavior
- keep caches partitioned by portfolio
- verify `Horus` and non-Horus portfolios against the same run set in reporting tests

### Risk 6. Overfitting the first release into a full matrix framework

Control:

- keep the new services `Horus`-oriented and additive
- defer generalized matrix-policy abstraction until `Horus` is proven in production-like use

## 7. Recommended Execution Notes

1. Treat `HMX-P1` and `HMX-P2` as the non-negotiable foundation. Do not start lifecycle execution code until schema, identity, and signal-run persistence are stable.
2. Prefer additive schema changes over mutating existing table meaning. The codebase already has broad route coverage; compatibility matters more than elegance here.
3. When reporting needs portfolio-specific lifecycle truth, prefer the new `Horus` execution state over trying to force the current single-row-per-recommendation `SignalOutcome` model to represent every matrix at once.
4. Keep package diffs focused. `HMX-P3` through `HMX-P5` should change behavior in small vertical slices, not one large blended rewrite.
5. After each package, verify targeted tests before moving forward. Do not wait for `HMX-P6` to discover scheduler or Telegram regressions.

## 8. Recommended Next Move After This Plan

Start with `HMX-P1` only.

That first execution boundary is:

- seed `Horus`
- add the execution-state schema and migration
- switch backend and frontend default workspace preference to `Horus`
- land the identity tests and focused frontend selection tests

Do not begin scheduler or execution lifecycle work until `HMX-P1` is passing cleanly, because every later package assumes that identity and schema contract.
