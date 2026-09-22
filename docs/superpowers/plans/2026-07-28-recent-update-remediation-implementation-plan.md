# Recent Update Remediation Implementation Plan

Date: 2026-07-28
Based on:

- review of the uncommitted delta from commit `e291c2f1`
- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/plans/2026-06-05-pre-close-daily-preview-implementation-plan.md`
- `frontend/src/app/portfolio/page.tsx`
- `data_engine/mubasher_realtime_source.py`
- `core/DataManager.py`
- `core/scheduling.py`
- `core/session_mode.py`
- `utils/logger.py`
- `scripts/horus_keepalive.ps1`
- `scripts/install_keepalive_task.ps1`
- current frontend and backend validation results from 2026-07-28

Track: Recent Update Stabilization
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Bring the July 23-28 update set to release quality without discarding its product improvements.

The remediation must:

1. restore a passing frontend type/build boundary
2. make Mubasher live OHLCV behavior match its data contract and tests
3. make scheduler catch-up use one explicit market date end to end
4. prevent operator UI from displaying invented connectivity or freshness
5. make one-click portfolio replication safe, truthful, and testable
6. restore reliable lint, unit-test, and build gates
7. harden logging and Windows keepalive behavior
8. document and validate material trading-configuration changes
9. separate source changes from generated and runtime artifacts

### 1A. Binding Implementation Decisions

These decisions are part of the plan and are not left for the implementing agent to reinterpret.

1. Fleet replication means:
   - create source tickers that do not exist in the destination
   - replace shares, entry price, stops, targets, currency, sector, and notes for matching open destination tickers
   - leave unrelated destination positions unchanged
   - never add source shares to existing destination shares
2. Fleet replication requires a confirmation dialog. The dialog must name the source and destination portfolios and state that matching positions will be replaced.
3. An intake result with any errors is `partial`, not success. The UI must show exact created, updated, and failed counts.
4. The canonical Mubasher intraday-store row remains an incremental current-minute bar:
   - `open = high = low = close = last`
   - `volume = last_quantity`
   - `timestamp = source timestamp floored to one minute`
5. `session_open`, `session_high`, `session_low`, and `session_volume` remain snapshot metadata and range-validation inputs. They must not be written into the incremental intraday bar without a separate cumulative-session schema.
6. The conflicting new test that expects session OHLCV from `to_intraday_frame()` must be corrected to the incremental-minute contract. Existing `tests/test_mubasher_realtime_source.py` is the source of truth.
7. Daily live volume continues to sum incremental minute volume. Its new projection logic must be extracted and tested through DataManager; no cumulative-volume heuristic is allowed.
8. Scheduler run identity is based on the market session date and phase:
   - `<market_date>:PRE_CLOSE`
   - `<market_date>:DAILY:PREVIEW`
   - `<market_date>:DAILY:CONFIRMED`
9. A post-close preview belongs to that same market session date. The next-morning confirmation also uses the previous completed market session date, even though delivery/execution occurs on the current morning.
10. `catchup_missed_post_market_jobs()` must return `status=skipped, reason=before_market_close` when called before market close. Morning startup runs only morning confirmation catch-up; it must not recreate pre-close or post-close preview jobs.
11. Scheduler idempotency is database-backed through `SignalRun.run_key`. In-memory sets may remain only as process-local optimizations.
12. Operational UI must never invent a connection state or timestamp. Missing evidence renders `Unknown`, `Disconnected`, `Polling`, `Stale`, or `Pending`.
13. Keep `horus.log` for compatibility and keep the new market/analysis split, but share singleton handler instances so one process opens each file only once.
14. Keep active logs. Automatic retention deletes only rotated backups older than 30 days and runs from explicit startup/maintenance code, not module import.
15. Keepalive prevents system sleep by default, not display sleep. Display wakefulness is opt-in.
16. Keepalive Telegram notification is opt-in and disabled for the scheduled task by default.
17. Preserve the current intended trading defaults:
   - `COMMISSION_PCT = 0.15` percent units
   - `SL_PCT = 2.5` percent units
   - `SLIPPAGE_PCT = 0.10` percent units
   - `REPLAY_ENTRY_CUTOFF_HHMM = 12:30`
   - `REPLAY_MAX_CONCURRENT_POSITIONS = 5`
18. The implementation must document and validate these values; it must not silently restore the older values.
19. `settings.json` becomes local persistent state. Committed defaults move to `config/settings.defaults.json`; local `settings.json` is ignored after migration support is added.
20. New council reports and transcripts move under `docs/council/2026-07/`. Do not relocate the older 110 tracked root artifacts in this remediation.

## 2. In Scope

Primary implementation targets:

- portfolio replication types, API-result handling, merge semantics, and confirmation UX
- Mubasher session OHLCV mapping and live daily-volume aggregation/projection
- post-market and morning signal scheduling, durable idempotency, and market-date propagation
- real telemetry for stream status, synchronization age, cache state, and verification badges
- frontend lint/type/build failures and slow or hanging test suites
- session-aware logging, retention policy, and handler duplication
- Windows keepalive schedule and late-start behavior
- commission, slippage, stop-loss, and replay-risk configuration governance
- repository ignore rules, generated artifacts, whitespace, and commit boundaries
- focused and full regression verification

Out of scope:

- adding new trading strategies
- redesigning the application shell
- changing Telegram subscriber tiers
- broad architectural refactoring unrelated to the reviewed update
- deleting user-generated reports, transcripts, snapshots, or logs without an explicit retention decision
- changing risk defaults again before the intended values are confirmed

## 3. Execution Rules

1. Fix release blockers before feature polish.
2. Add or correct regression tests before changing market-data and scheduler behavior.
3. Use an explicit `market_date` value for catch-up operations; do not infer it independently in nested functions.
4. UI status labels must derive from runtime state or say `Unknown`, `Unavailable`, or `Not connected`.
5. Portfolio mutation must require a clear user action and must report partial success accurately.
6. Preserve all existing uncommitted work; use narrow patches and do not reset the working tree.
7. Do not remove generated artifacts until they are classified as source, retained evidence, or disposable runtime output.
8. Treat commission, slippage, stop-loss, position-cap, and cutoff changes as product-risk changes requiring explicit acceptance.
9. End every package with its focused verification before proceeding.
10. Do not declare release readiness until type checking, lint, production build, focused backend tests, and the agreed full test baseline pass.

## 4. Work Package Sequence

Execute in this order:

1. `RUR-P1` Frontend build restoration and safe portfolio replication
2. `RUR-P2` Mubasher OHLCV and live-volume correctness
3. `RUR-P3` Scheduler market-date consistency and durable idempotency
4. `RUR-P4` Truthful frontend telemetry and verification states
5. `RUR-P5` Test and static-analysis gate repair
6. `RUR-P6` Logging and Windows keepalive hardening
7. `RUR-P7` Trading configuration governance
8. `RUR-P8` Workspace and artifact hygiene
9. `RUR-P9` Full release verification and closeout

The first three packages contain release or trading-correctness risks and should not be combined with cosmetic cleanup.

## 5. Work Packages

### RUR-P1. Frontend Build Restoration And Safe Portfolio Replication

Purpose:

Restore TypeScript correctness and make fleet replication an explicit, accurately reported portfolio mutation.

Target files:

- `frontend/src/app/portfolio/page.tsx`
- `frontend/src/app/portfolio/components/SystemComparisonSection.tsx`
- `frontend/src/app/portfolio/components/PortfolioShell.tsx`
- `frontend/src/app/portfolio/hooks/usePortfolioRuntime.ts`
- `frontend/src/types/index.ts`
- `routes/portfolio.py`
- `core/portfolio/management.py`
- relevant portfolio frontend and backend tests

Tasks:

1. Change the three new `showUiMessage` calls to the established two-argument contract.
2. Resolve the `Position.sector` type mismatch by using the canonical API position type or explicitly extending the contract.
3. Require a valid non-null active target portfolio before enabling replication.
4. Implement the binding replacement semantics from section 1A: replace matching open positions, create missing positions, and leave unrelated positions unchanged.
5. Add a confirmation dialog showing source portfolio, destination portfolio, source position count, and the exact replacement semantics.
6. Parse the intake response body even when HTTP status is 200.
7. Display created, updated, blocked, and failed counts separately.
8. Do not show `Replicated` when the result is partial or zero positions were changed.
9. Add a pending-state guard to prevent double clicks and concurrent duplicate requests.
10. Add tests for no active portfolio, empty source, partial WFA rejection, total failure, success, and cancellation.
11. Add a typed `PortfolioIntakeResult` interface with `status`, `portfolio_id`, `created`, `updated`, `errors`, and `report_summary`.
12. Treat `status !== "completed"` or `errors.length > 0` as partial, even when `Response.ok` is true.
13. Use the canonical API helper `readJsonSafe` rather than calling `response.json()` directly.

Deliverables:

- zero portfolio-related TypeScript errors
- explicit replication semantics and confirmation
- accurate partial-result reporting
- regression tests around mutation safety

Verification:

- `npx --prefix frontend tsc --noEmit -p frontend/tsconfig.json`
- `npm test --prefix frontend -- --runInBand frontend/src/app/portfolio`
- `.venv313\Scripts\python.exe -m pytest tests/test_portfolio_management_service.py tests/test_portfolio.py -q`

Acceptance criteria:

- TypeScript validation passes
- replication cannot target a null or unknown portfolio
- users know whether matching positions are replaced, merged, or skipped
- a partial backend result is never presented as full success
- repeated clicks cannot create duplicate mutations
- matching holdings are replaced, not quantity-merged

### RUR-P2. Mubasher OHLCV And Live-Volume Correctness

Purpose:

Align realtime snapshot output, intraday persistence, daily live-bar merging, and volume projection with one documented data contract.

Target files:

- `data_engine/mubasher_realtime_source.py`
- `data_engine/harvester_service.py`
- `data_engine/ingest_intraday.py`
- `core/DataManager.py`
- `tests/test_live_scan_alignment.py`
- existing realtime and scanner data tests

Tasks:

1. Document that each `to_intraday_frame()` result is an incremental current-minute contribution, not a cumulative session snapshot.
2. Preserve the current last-price OHLC and last-quantity volume mapping.
3. Correct `tests/test_live_scan_alignment.py::test_mubasher_quote_snapshot_preserves_session_ohlcv` to assert the canonical incremental-minute contract and rename it accordingly.
4. Keep session fields on `MubasherQuoteSnapshot` for validation and future separate session-snapshot use; do not mix them into `intraday_store`.
5. Preserve source timestamps and enforce timezone normalization.
6. Validate low/high range guards against malformed source values.
7. Extract volume projection into a testable helper.
8. Test before 10:30, at 10:30, midday, market close, replay mode, stale prior-day data, and zero/negative source volume.
9. Replace the current time-comparison-only volume test with an integration-level DataManager assertion using a fixed intraday frame and mocked `TimeUtils.now()`.
10. Confirm that projected volume cannot inflate replay or complete-session data.

Deliverables:

- one explicit realtime-volume contract
- passing session OHLCV regression test
- correct live daily volume without cumulative double counting
- focused projection tests

Verification:

- `.venv313\Scripts\python.exe -m pytest tests/test_live_scan_alignment.py -q`
- `.venv313\Scripts\python.exe -m pytest tests/test_scanner_and_data.py -q`
- `.venv313\Scripts\python.exe -m pytest tests -k "mubasher or intraday or volume" -q`

Acceptance criteria:

- incremental OHLC and volume match the existing documented intraday contract
- snapshot session fields remain available without contaminating incremental bar aggregation
- daily live volume is not projected during replay
- volume projection begins only at the configured threshold
- malformed source snapshots fail safely

### RUR-P3. Scheduler Market-Date Consistency And Durable Idempotency

Purpose:

Ensure catch-up, preview, morning confirmation, persistence, execution, reconciliation, and publishing all refer to the same intended trading date.

Target files:

- `core/scheduling.py`
- `config/startup.py`
- `config/app_factory.py`
- `core/session_mode.py`
- `core/signals/runs.py`
- `core/signals/executor.py`
- scheduler and signal-run tests
- `tests/test_morning_daily_signal.py`

Tasks:

1. Add a required keyword-only `market_date: datetime.date` parameter to the internal scheduled scan/persistence/freshness path. Public APScheduler callbacks compute it once before calling the internal path.
2. Pass that date into freshness checks, signal-run persistence, preview reconciliation, completion checks, execution, and report dispatch.
3. Remove nested uses of `TimeUtils.today()` when an explicit catch-up date exists.
4. Implement the binding morning behavior: previous completed trading session as `market_date`, current trading morning only as the delivery/execution time.
5. Replace in-memory-only morning completion tracking with durable signal-run or job-completion state.
6. Ensure restart before market open cannot duplicate a completed scan, no-signal notice, Telegram publication, or auto-execution.
7. Ensure watchdog and ANALYSIS transition catch-up calls share the same durable guard.
8. Add tests for:
   - Monday morning catching up Sunday
   - Sunday morning catching up Thursday
   - DB holiday gaps
   - restart before market open
   - repeated watchdog invocation
   - catch-up after market close
   - replay/simulation date behavior
9. Assert persisted run keys and reconciliation dates, not only the in-memory executed-job list.
10. Generate distinct preview and confirmed run keys so a completed preview can never suppress morning confirmation.
11. Query `SignalRun` to determine completion before consulting in-memory sets.
12. Make `catchup_missed_post_market_jobs()` refuse pre-close execution and post-close preview execution before `MARKET_END_TIME`.
13. Keep weekly/monthly report catch-up separate from signal catch-up so it cannot bypass the time guard.

Deliverables:

- explicit end-to-end market-date propagation
- durable scheduler idempotency
- restart-safe morning confirmation
- regression coverage for weekend and holiday boundaries

Verification:

- `.venv313\Scripts\python.exe -m pytest tests/test_morning_daily_signal.py -q`
- `.venv313\Scripts\python.exe -m pytest tests/test_session_mode.py tests/test_broadcast_reliability.py tests/test_horus_signal_intake_service.py -q`
- `.venv313\Scripts\python.exe -m pytest tests -k "scheduler or daily_signal or pre_close" -q`

Acceptance criteria:

- a previous-session catch-up is persisted under the previous session date
- reconciliation and reporting use the same date
- repeated or restarted jobs do not duplicate delivery or execution
- weekend and holiday boundaries are covered by tests
- post-close preview and morning confirmation coexist as two durable phases

### RUR-P4. Truthful Frontend Telemetry And Verification States

Purpose:

Replace hard-coded operational claims with real runtime state and prevent decorative badges from implying verified system health.

Target files:

- `frontend/src/app/execution-quality/page.tsx`
- `frontend/src/app/audit-logs/page.tsx`
- `frontend/src/app/audit/components/AuditShell.tsx`
- `frontend/src/app/optimization/components/OptimizationShell.tsx`
- `frontend/src/app/simulation/components/SimulationShell.tsx`
- `frontend/src/app/strategy/components/StrategyShell.tsx`
- `frontend/src/app/components/custom/CommandHeader.tsx`
- relevant hooks, contexts, and tests

Tasks:

1. Inventory every new `WS LIVE`, `12s ago`, `VERIFIED`, `CONVERGED`, `FRESH`, and similar operational label.
2. Classify each value as live connectivity, last successful fetch, cache age, calculated quality state, or decorative copy.
3. Source live connectivity and timestamps from existing hooks or shared contexts.
4. Render `Unknown`, `Disconnected`, `Polling`, `Stale`, or `Pending` when runtime evidence is missing.
5. Use a shared formatter for last-updated age and stale thresholds.
6. Reserve `VERIFIED` for a defined validation result, not merely positive profit or low displayed slippage.
7. Add tests for connected, disconnected, stale, never-loaded, polling fallback, and recovery states.
8. Remove tests that assert fixed fake timestamps.

Deliverables:

- truthful status headers across affected pages
- shared freshness formatting
- state-transition tests

Verification:

- `npm test --prefix frontend -- --runInBand AnalyticsShell AuditShell OptimizationShell SimulationShell StrategyShell`
- `npx --prefix frontend tsc --noEmit -p frontend/tsconfig.json`

Acceptance criteria:

- no page displays `WS LIVE` without a real connected-state signal
- no fixed `12s ago` values remain in production components
- `VERIFIED` and similar labels have documented, testable criteria
- stale and disconnected states are visible to operators

### RUR-P5. Test And Static-Analysis Gate Repair

Purpose:

Make the repository's declared validation commands complete reliably and return actionable results.

Target files:

- `frontend/jest.setup.ts`
- frontend Jest configuration and slow test files
- `package.json`
- `frontend/package.json`
- `pytest.ini`
- `scripts/run_backend_tests.py`
- CI workflow files if local fixes expose CI drift

Tasks:

1. Replace forbidden CommonJS imports in `frontend/jest.setup.ts` with lint-compliant imports.
2. Run Jest with open-handle diagnostics and identify the source of the current timeout.
3. Check for unclosed timers, SWR polling, websocket mocks, unresolved promises, and open server handles.
4. Ensure new component timers use fake timers or are cleaned up on unmount.
5. Establish a fast changed-area suite and a full release suite with separate time budgets.
6. Ensure a failed parallel check does not hide the output of other checks.
7. Add an explicit frontend typecheck script.
8. Add or restore production build as a required release gate.
9. Review backend test runtime and split integration tests from fast unit tests if necessary.
10. Document known unrelated failures only temporarily; do not normalize a permanently red baseline.

Deliverables:

- passing frontend lint
- explicit typecheck script
- Jest suites that terminate normally
- reliable backend/frontend validation commands

Verification:

- `npm run lint --prefix frontend`
- `npx --prefix frontend tsc --noEmit -p frontend/tsconfig.json`
- `npm test --prefix frontend -- --runInBand --detectOpenHandles`
- `npm run build --prefix frontend`
- `.venv313\Scripts\python.exe scripts/run_backend_tests.py`

Acceptance criteria:

- lint, typecheck, unit tests, and build all return normally
- no test worker remains after command completion
- failures from one gate do not suppress other gate reports
- changed-area checks complete within an agreed developer time budget

### RUR-P6. Logging And Windows Keepalive Hardening

Purpose:

Retain useful session separation without unsafe retention, duplicate handlers, misleading schedule behavior, or corrupted notifications.

Target files:

- `utils/logger.py`
- `scripts/horus_keepalive.ps1`
- `scripts/install_keepalive_task.ps1`
- logger tests
- operations documentation

Tasks:

1. Keep `horus.log` plus session-specific logs for compatibility and document the intentional duplicate destination.
2. Set the explicit maximum disk budget to approximately 180 MB: three active 10 MB files plus five 10 MB backups per file.
3. Create module-level singleton handler instances and ensure one process opens each destination only once.
4. Move cleanup from import-time side effects to an explicit startup/maintenance operation invoked before handler creation.
5. Restrict cleanup to rotated backups matching `*.log.<number>`; never delete active `*.log` files.
6. Log cleanup failures instead of silently swallowing every exception.
7. Parse and honor `TargetEndTime` in the keepalive script.
8. If a scheduled task starts after the target market time, exit immediately instead of running another default duration.
9. Use `ES_SYSTEM_REQUIRED | ES_CONTINUOUS` by default and add an opt-in `-KeepDisplayAwake` switch.
10. Resolve `.venv313\Scripts\python.exe` from the project root; skip optional notification cleanly when it is absent.
11. Correct PowerShell/Telegram Unicode encoding and save scripts as UTF-8.
12. Document that the task runs every Sun-Thu and the app-level market/holiday guards remain authoritative.
13. Add `-NotifyTelegram`, default false; do not enable it in the scheduled task installer.
14. Provide install, inspect, and uninstall instructions for the scheduled task.

Deliverables:

- bounded and observable log retention
- no duplicate rotating handlers for the same destination
- keepalive that never runs beyond the intended market window
- readable notifications and operator instructions

Verification:

- `.venv313\Scripts\python.exe -m pytest tests -k "logger or logging" -q`
- PowerShell parser validation for both scripts
- manual dry run with target times before and after the current time
- scheduled-task inspection after installation in a controlled environment

Acceptance criteria:

- importing the logger module does not delete files
- log retention has a documented maximum
- late task startup exits safely
- target end time is honored
- scripts contain no corrupted text

### RUR-P7. Trading Configuration Governance

Purpose:

Confirm, document, and regression-test material changes to commission, stop-loss, replay cutoff, and position limits.

Target files:

- `core/settings.py`
- `settings.json`
- `saved_settings.json` if it participates in runtime defaults
- settings UI and API contracts if these values are user-configurable
- replay, sizing, and settings tests
- operator/release notes

Tasks:

1. Preserve and document the binding intended values from section 1A.
2. Standardize these settings as percent units: `0.15` means `0.15%`, and calculation boundaries divide by 100 exactly once.
3. Remove duplicate settings blocks or document why multiple profiles exist.
4. Validate cutoff format and position-limit bounds during settings load/update.
5. Add migration behavior for existing persisted settings.
6. Add tests proving costs are applied once and consistently in replay, portfolio, and execution calculations.
7. Compare representative backtest results before and after the intended configuration.
8. Record the expected behavioral impact in release notes.

Deliverables:

- approved and documented risk defaults
- validation and migration coverage
- before/after impact evidence

Verification:

- `.venv313\Scripts\python.exe -m pytest tests/test_settings.py tests/test_replay_engine.py tests/test_autotrader.py -q`
- representative replay/backtest comparison using fixed fixtures

Acceptance criteria:

- every material risk-default change is intentional and documented
- invalid cutoff or position-limit values fail safely
- costs are not double-applied
- persisted settings upgrade without silent behavior drift

### RUR-P8. Workspace And Artifact Hygiene

Purpose:

Separate implementation code, user evidence, runtime state, and generated output into reviewable commit boundaries.

Target files:

- `.gitignore`
- `.gitattributes` if line-ending policy is absent
- `logs/audit.jsonl`
- `.parallel_rate_cache.json`
- `settings.json`
- `config_snapshots/`
- council reports and transcripts
- generated build and test-output directories

Tasks:

1. Classify each modified or untracked artifact as:
   - source
   - test fixture
   - documentation/evidence
   - local runtime state
   - generated disposable output
2. Move only the new July 25-27 untracked council reports and transcripts to `docs/council/2026-07/`; leave older tracked root artifacts unchanged.
3. Add ignore rules for `.parallel_rate_cache.json`, `logs/*.jsonl`, `config_snapshots/*.json`, local `settings.json`, and future root-level `council-report-*` / `council-transcript-*` output after the generator is pointed at `docs/council/<year-month>/`.
4. Remove the live `logs/audit.jsonl` from source tracking while preserving the local file; create a small deterministic audit fixture only if tests require it.
5. Move committed defaults to `config/settings.defaults.json`. Load defaults first and overlay local persistent `settings.json`; writes go only to local state.
6. Normalize line-ending policy to prevent repeated LF/CRLF churn.
7. Fix all `git diff --check` whitespace findings.
8. Split future commits by concern:
   - build and replication
   - market data
   - scheduling
   - telemetry
   - test infrastructure
   - operations
   - configuration
   - artifact hygiene
9. Re-run status and ensure no unrelated runtime file is accidentally staged.
10. Restore `package-lock.json` to the committed version when package manifests are unchanged; otherwise document the exact dependency reason for retaining the lockfile delta.
11. Keep `config_snapshots/settings_20260726_171835.json` as local recovery evidence but do not add it to source control.

Deliverables:

- clean artifact classification
- updated ignore/line-ending policy
- zero whitespace errors
- reviewable commit boundaries

Verification:

- `git status --short`
- `git diff --check`
- `git ls-files logs config_snapshots`
- clean-checkout validation after the planned commit series

Acceptance criteria:

- runtime logs and caches do not appear in normal source diffs
- retained reports/evidence live in an intentional location
- settings ownership is unambiguous
- `git diff --check` passes
- no user artifact is deleted without a retention decision

### RUR-P9. Full Release Verification And Closeout

Purpose:

Prove that the remediation is complete and the recent update can be released safely.

Target files:

- all files touched by `RUR-P1` through `RUR-P8`
- release notes or checkpoint summary

Tasks:

1. Run focused tests after each package.
2. Run the complete Python compile check.
3. Run the agreed full backend baseline with controlled test environment variables.
4. Run frontend lint, typecheck, unit tests, and production build.
5. Run critical browser smoke checks for portfolio replication, scanner/live status, simulation, and Telegram status.
6. Re-run `git diff --check`.
7. Inspect repository status for generated pollution.
8. Verify no test, Node, or Python worker remains after test completion.
9. Record pass counts, durations, and any explicitly deferred non-release issue.
10. Produce a final release checkpoint summary.

Deliverables:

- green release gates
- browser-level confirmation of operator-critical flows
- clean repository status
- final checkpoint report

Verification:

- `.venv313\Scripts\python.exe -m compileall -q config core data_engine database.py scripts utils`
- `.venv313\Scripts\python.exe scripts/run_backend_tests.py`
- `npm run lint --prefix frontend`
- `npx --prefix frontend tsc --noEmit -p frontend/tsconfig.json`
- `npm test --prefix frontend -- --runInBand`
- `npm run build --prefix frontend`
- `npm run test:e2e --prefix frontend`
- `git diff --check`
- `git status --short`

Acceptance criteria:

- no blocker or major review finding remains
- frontend lint, typecheck, tests, and build pass
- backend focused and full baselines pass
- critical browser paths pass
- test processes terminate normally
- generated/runtime artifacts are absent from the source change set

## 6. Risks And Controls

Risk: Fixing session OHLCV changes live volume behavior and scanner outcomes.

Control: Lock the data contract with source-level and DataManager integration tests before modifying aggregation.

Risk: Catch-up date propagation changes run keys and may conflict with existing database records.

Control: Add migration-aware lookup behavior and test existing completed, pending, and duplicate run records.

Risk: Portfolio replication unintentionally replaces live holdings.

Control: Define semantics explicitly, add preview/confirmation, and report every skipped or failed holding.

Risk: Replacing hard-coded telemetry exposes missing runtime state.

Control: Prefer honest unknown/disconnected states first; add new transport plumbing only where an existing source does not exist.

Risk: Test timeout investigation expands into unrelated legacy cleanup.

Control: First isolate handles introduced or exercised by the changed pages, then separately record older suite debt.

Risk: Artifact cleanup removes user evidence.

Control: Classify and relocate before ignoring or deleting; keep destructive cleanup outside implementation until approved.

Risk: Trading defaults were intentional and remediation accidentally restores old values.

Control: Require an explicit value decision and compare fixed-fixture results before changing configuration.

Risk: Log-handler consolidation reduces diagnostics.

Control: Verify both LIVE and ANALYSIS routing with tests and keep a documented fallback log destination.

## 7. Recommended Execution Notes

Start with `RUR-P1` because the current TypeScript errors block production builds and are localized enough to fix and verify independently.

Implement `RUR-P2` and `RUR-P3` as separate commits. Both affect trading correctness and should have narrow regression evidence that can be reviewed independently.

Do not begin repository artifact removal while product-code fixes are active. Artifact classification can be documented early, but actual moves and ignore-rule changes belong in `RUR-P8`.

Use package-level tests during development, then run the full release baseline only in `RUR-P9`.

## 8. Recommended Next Move After This Plan

Begin `RUR-P1` with a narrow frontend patch:

1. correct `showUiMessage` calls
2. fix the `Position` contract
3. parse partial intake responses
4. add confirmation and duplicate-submit protection
5. run typecheck and portfolio tests before touching market-data or scheduler code

## 9. AI Agent Execution Protocol

This section is mandatory for any agent implementing the plan.

### 9.1 Preflight

Before editing:

1. Read `CLAUDE.md`.
2. Read this plan completely.
3. Run:

   - `git status --short`
   - `git diff --stat`
   - `git diff --check`
   - `git branch --show-current`

4. Record the existing dirty files. Treat all existing changes as user-owned.
5. Do not use `git reset --hard`, `git checkout --`, or broad file restoration.
6. Read every target file and its closest tests before patching it.
7. Work on one `RUR-P*` package at a time.

### 9.2 Implementation Method

For each package:

1. Reproduce the current failure or add a failing regression test.
2. Make the smallest implementation change that satisfies the binding decisions.
3. Run the package's focused verification.
4. Run TypeScript or Python static validation for touched languages.
5. Run `git diff --check`.
6. Review the package diff for unrelated changes.
7. Record:
   - files changed
   - tests added or updated
   - commands run
   - pass/fail counts
   - remaining risks
8. Do not begin the next package while a new package-specific failure remains.

### 9.3 Test Process Safety

The current full backend and frontend suites exceeded their two-minute review timeout. Therefore:

1. Do not launch duplicate full suites in parallel.
2. Run focused suites first.
3. Use a generous, explicit timeout for the single full release suite.
4. If a test command times out, inspect and terminate only the child processes created by that command.
5. Re-run the smallest affected test with verbose output or open-handle diagnostics.
6. Never report a timed-out suite as passed.

### 9.4 Change Boundaries

1. Do not refactor unrelated modules while fixing a package.
2. Do not change trading strategy thresholds outside `RUR-P7`.
3. Do not send Telegram messages, install scheduled tasks, or mutate live portfolios during automated verification.
4. Mock external delivery and portfolio mutations in tests.
5. Do not delete or overwrite the untracked council artifacts or settings snapshot.
6. Do not stage or commit unless the user separately requests it.
7. Suggested commit boundaries are organizational guidance only:
   - `fix(frontend): make portfolio replication safe and typed`
   - `test(data): lock mubasher incremental bar contract`
   - `fix(scheduler): use durable market-date phase keys`
   - `fix(ui): derive operational telemetry from runtime state`
   - `test: restore lint typecheck build and terminating suites`
   - `fix(ops): harden logging and keepalive lifecycle`
   - `chore(config): formalize trading defaults and local overrides`
   - `chore(repo): separate runtime artifacts from source`

### 9.5 Stop Conditions

Stop and request user direction only when:

1. implementing a package requires changing one of the binding decisions
2. source data proves `COMMISSION_PCT`, `SL_PCT`, or other declared defaults were accidental
3. a database migration would destroy or rewrite existing signal/portfolio records
4. artifact cleanup would delete evidence instead of relocating or ignoring it
5. a required external service or credential is needed for validation

Ordinary test failures, difficult implementation, or slow suites are not stop conditions; diagnose them within the package.

### 9.6 Required Closeout Artifact

After `RUR-P9`, create:

`docs/superpowers/reference/2026-07-28-recent-update-remediation-checkpoint-summary.md`

It must contain:

- implemented package list
- final file list by package
- final validation commands and results
- backend/frontend test counts and durations
- production build result
- browser smoke result
- configuration defaults confirmed
- artifacts relocated or ignored
- remaining non-release issues
- explicit release recommendation: `READY`, `READY WITH DOCUMENTED DEBT`, or `NOT READY`

## 10. Required Regression Matrix

The implementing agent must cover at least the following cases.

| Area | Case | Expected result |
|---|---|---|
| Portfolio replication | No active destination portfolio | Replicate control disabled; no request sent |
| Portfolio replication | User cancels confirmation | No request sent |
| Portfolio replication | Source ticker absent in destination | Position created |
| Portfolio replication | Source ticker already open in destination | Matching fields replaced; unrelated positions unchanged |
| Portfolio replication | Backend returns one WFA error | UI reports partial result with exact counts |
| Portfolio replication | Double click during request | One mutation request only |
| Mubasher | Valid last trade | Incremental minute bar uses last price and last quantity |
| Mubasher | Price outside session range | Empty frame; no write |
| Mubasher | Repeated update in same minute | Existing minute row replaced, not duplicated |
| DataManager | 10:15 live session | No volume projection |
| DataManager | 10:30 live session | Projection starts using elapsed-session fraction |
| DataManager | Replay/simulation | No volume projection |
| DataManager | Market closed | No volume projection |
| Scheduler | Post-close preview | Run key is `<market_date>:DAILY:PREVIEW` |
| Scheduler | Next-morning confirmation | Run key is `<previous_market_date>:DAILY:CONFIRMED` |
| Scheduler | Restart before open after confirmation | No duplicate scan, publish, or execution |
| Scheduler | Catch-up invoked before close | Skipped with explicit reason |
| Scheduler | Friday/Saturday weekend gap | Previous completed EGX session selected |
| Scheduler | Registered holiday gap | Previous non-holiday session selected |
| Telemetry | Websocket connected with timestamp | Live state and real age rendered |
| Telemetry | Websocket disconnected | Disconnected rendered; no green live badge |
| Telemetry | No timestamp available | Pending or Unknown rendered |
| Telemetry | Timestamp exceeds stale threshold | Stale rendered |
| Logging | Multiple named loggers | Each file opened by one shared handler per process |
| Logging | Cleanup run | Only old rotated backups removed |
| Keepalive | Started before target end | Runs until target end |
| Keepalive | Started after target end | Exits immediately |
| Keepalive | Default flags | System awake; display may sleep |
| Settings | Valid current defaults | Values load in percent units |
| Settings | Invalid cutoff | Validation rejects or safely restores default |
| Settings | Existing local settings | Defaults load first; local values override |
| Repository | Clean source edit | Runtime logs, cache, snapshots, and local settings absent from source diff |

## 11. Definition Of Done

This remediation is complete only when all boxes are satisfied:

- [ ] `RUR-P1` portfolio replication is typed, confirmed, idempotent, and accurately reports partial results.
- [ ] `RUR-P2` Mubasher incremental-minute contract is consistent across implementation and tests.
- [ ] DataManager volume projection has real behavioral tests.
- [ ] `RUR-P3` preview and confirmed scheduler phases use durable, date-correct run keys.
- [ ] Restart and repeated catch-up tests prove no duplicate publish or execution.
- [ ] `RUR-P4` contains no hard-coded production `WS LIVE` or fixed synchronization ages.
- [ ] `RUR-P5` lint passes.
- [ ] Frontend TypeScript validation passes.
- [ ] Frontend unit tests terminate and pass.
- [ ] Frontend production build passes.
- [ ] Focused backend tests pass.
- [ ] Full backend release baseline passes.
- [ ] Critical browser smoke tests pass.
- [ ] `RUR-P6` logger cleanup has no import-time deletion.
- [ ] Logging handlers are shared and disk budget is documented.
- [ ] Keepalive late-start, display, interpreter, and encoding behavior is corrected.
- [ ] `RUR-P7` current trading defaults are documented, validated, and tested.
- [ ] `RUR-P8` runtime state and new council evidence are separated from source changes.
- [ ] `git diff --check` passes.
- [ ] No orphaned test workers remain.
- [ ] The closeout checkpoint summary exists and gives an explicit release recommendation.
