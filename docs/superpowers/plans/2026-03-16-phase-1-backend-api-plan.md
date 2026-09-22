# Horus Analytics II Phase 1 Backend/API Plan

Date: 2026-03-16
Based on: `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
Track: Backend/API Stability
Phase: Phase 1 - Safety Rails and Failure Visibility
Status: Completed in code and verification on 2026-03-17
Owner model: Single owner

## 1. Goal

This plan turns the Phase 1 backend and API work into an executable sequence. The purpose is to make failure behavior explicit at the HTTP boundary, tighten the most dangerous error paths, and improve diagnostics without starting broad route decomposition yet.

Phase 1 backend work should leave three things true:

1. High-risk routes have documented failure contracts.
2. At least one critical route family has stronger regression coverage around its failure paths.
3. Operator-facing backend status and exception behavior are easier to diagnose from logs and responses.

Closeout references:

- `docs/superpowers/reference/2026-03-17-phase-1-operator-checklist.md`
- `docs/superpowers/reference/2026-03-17-phase-1-final-checkpoint-summary.md`

## 2. In Scope

Primary files:

- `api.py`
- `routes/system.py`
- `routes/signals.py`
- `routes/portfolio.py`
- `routes/ai_report.py`
- `routes/analytics.py`

Primary function seams:

- `api.py`: `readiness_gate`, `global_exception_handler`, `health_check`
- `routes/system.py`: `get_system_status`, `get_full_system_status`, `get_backfill_status`
- `routes/signals.py`: `run_daily_signals_logic`, `publish_signal_run_logic`, `_retry_failed_deliveries_logic`
- `routes/portfolio.py`: `get_positions`, `add_trade`, `close_trade`, `check_trade_risk`, `get_portfolio_management_report`
- `routes/ai_report.py`: `_compute_data_freshness`, `_maybe_generate_llm_report`, `get_ai_daily_report`, `broadcast_ai_daily_report`
- `routes/analytics.py`: `get_analytics_data`, `refresh_analytics`, `get_health`

Out of scope for Phase 1:

- Full route decomposition into service layers
- New feature work
- Behavior changes unrelated to error handling, diagnostics, or safety rails
- Broad schema redesign

## 3. Existing Test Anchors

Use the current tests as the initial protection layer before adding new ones:

- `tests/test_api_endpoints.py`
- `tests/test_error_paths.py`
- `tests/test_strategy_and_system.py`
- `tests/test_pipeline_stale_mode.py`
- `tests/test_signals_p0.py`
- `tests/test_signals_coverage.py`
- `tests/test_portfolio_operations.py`
- `tests/test_portfolio_remaining.py`
- `tests/test_portfolio_management_service.py`
- `tests/test_portfolio_audit.py`
- `tests/test_portfolio_csv_backup.py`
- `tests/test_ai_daily_report.py`
- `tests/test_analytics_coverage.py`

## 4. Package Sequence

Execute the backend track in this order:

1. `BA1` Global boundary and system-status contract
2. `BA2` Signals failure contract
3. `BA3` Portfolio failure contract
4. `BA4` AI report fallback and error contract
5. `BA5` Analytics endpoint sanity pass

This order matters because `api.py` and `routes/system.py` define the operator-facing behavior that the other route families depend on when the system is degraded.

## 5. Work Packages

### BA1. Global Boundary and System-Status Contract

Status: Completed on 2026-03-17

Purpose:

Make app-level failure handling and system-status behavior explicit before changing route-family behavior.

Target files:

- `api.py`
- `routes/system.py`
- `core/pipeline.py`

Tasks:

1. Inventory app-wide exception handling and middleware behavior in `global_exception_handler` and `readiness_gate`.
2. Confirm which exceptions should remain raw `HTTPException` responses versus being normalized into a structured 500 path.
3. Document and test the expected contract for `/api/v1/system/status`, `/api/v1/system/full-status`, `/health`, and stale-gate behavior.
4. Improve logging around readiness-gate rejection, stale-mode rejection, and unexpected unhandled exceptions.

Deliverables:

- App-level failure-contract matrix
- System-status response contract note
- First diagnostics upgrade in `api.py` or `routes/system.py`
- Regression tests for the highest-risk app boundary paths

Verification:

- `tests/test_api_endpoints.py`
- `tests/test_strategy_and_system.py`
- `tests/test_pipeline_stale_mode.py`

Acceptance criteria:

- System-status endpoints return predictable structure under normal and degraded conditions.
- App-level logging can distinguish stale gate, readiness gate, and unexpected exception paths.

### BA2. Signals Failure Contract

Status: Completed on 2026-03-17

Purpose:

Clarify how signal generation, publish, retry, and guard-state failures should behave at the route boundary.

Target files:

- `routes/signals.py`

Priority seams:

- `run_daily_signals_logic`
- `publish_signal_run_logic`
- `_retry_failed_deliveries_logic`
- `get_signal_guard_state`
- `set_signal_guard_state`

Tasks:

1. Inventory broad exception handling and fallback behavior in the run, publish, retry, and guard flows.
2. Separate user-error responses from infrastructure and unexpected failure responses at the route contract level.
3. Add regression coverage for publish and retry failure cases that currently depend on implicit behavior.
4. Improve audit or logger output when signal execution is blocked by freshness, guard state, or downstream delivery failure.

Deliverables:

- Signals failure-mode matrix
- Prioritized list of catch-all handlers to replace or narrow later
- Additional tests around publish, retry, and guard-state failure paths
- Better diagnostics for blocked and failed signal flows

Verification:

- `tests/test_signals_p0.py`
- `tests/test_signals_coverage.py`

Acceptance criteria:

- Signal routes return consistent status and error payloads for freshness-blocked, guard-blocked, invalid-input, and retry-failure cases.
- Logs and audit events identify the failure class without reading code.

### BA3. Portfolio Failure Contract

Status: Completed on 2026-03-17

Purpose:

Reduce ambiguity in portfolio mutation and reporting endpoints before decomposition work starts in Phase 2.

Target files:

- `routes/portfolio.py`

Priority seams:

- `get_positions`
- `add_trade`
- `close_trade`
- `check_trade_risk`
- `get_portfolio_management_report`
- `intake_portfolio_holdings`

Tasks:

1. Inventory exception handling across read, mutate, import, and reporting flows.
2. Identify endpoints where validation or user-input errors are incorrectly converted into generic server failures.
3. Add regression coverage around the most brittle mutation and import paths.
4. Improve failure messages and logs for portfolio reporting and holdings-intake flows.

Deliverables:

- Portfolio endpoint failure matrix
- Candidate list of user-error versus server-error mismatches
- Regression tests for mutation and reporting failure paths
- Diagnostics improvement for one portfolio reporting or intake flow

Verification:

- `tests/test_portfolio_operations.py`
- `tests/test_portfolio_remaining.py`
- `tests/test_portfolio_management_service.py`
- `tests/test_portfolio_audit.py`
- `tests/test_portfolio_csv_backup.py`

Acceptance criteria:

- Portfolio mutation and report endpoints expose clearer client-error versus server-error behavior.
- One operator-relevant portfolio failure can be diagnosed from logs or response structure alone.

### BA4. AI Report Fallback and Error Contract

Status: Completed on 2026-03-17

Purpose:

Make LLM fallback, provider failure, and report-generation degradation explicit without redesigning the report system yet.

Target files:

- `routes/ai_report.py`

Priority seams:

- `_compute_data_freshness`
- `_collect_portfolio_snapshot`
- `_maybe_generate_llm_report`
- `get_ai_daily_report`
- `broadcast_ai_daily_report`

Tasks:

1. Inventory provider-failure, snapshot-failure, and fallback-to-rule-engine behavior.
2. Document which failures should degrade the report content and which should fail the request.
3. Add regression coverage for provider failure and fallback paths that are critical to production use.
4. Improve logging around provider selection, fallback activation, and broadcast failure.

Deliverables:

- AI report fallback contract note
- Tests for critical rule-engine fallback paths
- Diagnostics improvement for provider failure or broadcast failure

Verification:

- `tests/test_ai_daily_report.py`

Acceptance criteria:

- AI report endpoints have a documented distinction between degraded report output and hard request failure.
- Provider failure is operator-visible in logs without tracing code manually.

### BA5. Analytics Endpoint Sanity Pass

Status: Completed on 2026-03-17

Purpose:

Do a narrow Phase 1 pass on analytics endpoints so the Month 1 release checkpoint does not ignore this route family entirely.

Target files:

- `routes/analytics.py`

Priority seams:

- `get_analytics_data`
- `refresh_analytics`
- `get_health`

Tasks:

1. Inventory the main failure and cache-state paths in the analytics endpoints.
2. Confirm that background-scan start and status behavior remain test-protected.
3. Add or tighten only the tests needed to keep analytics behavior visible during Phase 1.

Deliverables:

- Minimal analytics failure note
- Any needed regression additions for refresh and status behavior

Verification:

- `tests/test_analytics_coverage.py`
- `tests/test_analytics_new_features.py`

Acceptance criteria:

- Analytics routes are not a blind spot in the Phase 1 release checkpoint.

## 6. Week-by-Week Execution

### Week 1

1. Complete `BA1` inventory and draft the app-level failure matrix.
2. Start `BA2` signals inventory because that route family already has the strongest test anchors.
3. Capture current response and logging behavior for stale gate, readiness gate, and system status.

### Week 2

1. Add or tighten regression tests for `BA1` and `BA2`.
2. Apply the first diagnostics improvements to `api.py` and `routes/system.py`.
3. Finish the signals failure-contract note.

### Week 3

1. Execute `BA3` portfolio inventory and first regression additions.
2. Apply one portfolio diagnostics improvement.
3. Run the focused backend package suite and fix contract mismatches found by tests.

### Week 4

1. Execute `BA4` and `BA5`.
2. Re-run the full backend baseline.
3. Finalize the Phase 1 backend checkpoint summary for Month 1.

## 7. Focused Command Set

Use these commands during package work:

### App boundary and system status

```powershell
$env:HORUS_DB_FILE=':memory:'
$env:HORUS_DISABLE_READINESS_GATE='true'
$env:DEBUG='false'
python -m pytest tests/test_api_endpoints.py tests/test_error_paths.py tests/test_strategy_and_system.py tests/test_pipeline_stale_mode.py
```

### Signals

```powershell
$env:HORUS_DB_FILE=':memory:'
$env:HORUS_DISABLE_READINESS_GATE='true'
$env:DEBUG='false'
python -m pytest tests/test_signals_p0.py tests/test_signals_coverage.py
```

### Portfolio

```powershell
$env:HORUS_DB_FILE=':memory:'
$env:HORUS_DISABLE_READINESS_GATE='true'
$env:DEBUG='false'
python -m pytest tests/test_portfolio_operations.py tests/test_portfolio_remaining.py tests/test_portfolio_management_service.py tests/test_portfolio_audit.py tests/test_portfolio_csv_backup.py
```

### AI report and analytics

```powershell
$env:HORUS_DB_FILE=':memory:'
$env:HORUS_DISABLE_READINESS_GATE='true'
$env:DEBUG='false'
python -m pytest tests/test_ai_daily_report.py tests/test_analytics_coverage.py tests/test_analytics_new_features.py
```

The end-of-month checkpoint still uses the full baseline from the main implementation plan.

## 8. Phase 1 Exit Checklist

Backend Phase 1 is complete when all of the following are true:

1. The app-level and route-family failure matrices exist for system, signals, portfolio, and AI report paths.
2. At least one route family has materially better regression coverage around failure cases.
3. Diagnostics have improved in `api.py` and at least one route family.
4. Focused backend suites are green.
5. The full backend baseline from the main implementation plan is green.

Phase 1 backend closeout result:

- All five backend packages are complete.
- The full backend baseline passed on 2026-03-17.
- Remaining warnings are non-blocking and recorded in the Phase 1 checkpoint summary.

## 9. Next Planning Boundary

Do not start route decomposition from this document. Once this Phase 1 plan is complete, the next backend artifact should be a Phase 2 decomposition plan for `routes/portfolio.py`, followed by `routes/signals.py`.
