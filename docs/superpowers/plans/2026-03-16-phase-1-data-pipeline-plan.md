# Horus Analytics II Phase 1 Data Pipeline Plan

Date: 2026-03-16
Based on: `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
Track: Data Pipeline Reliability
Phase: Phase 1 - Safety Rails and Failure Visibility
Status: Completed in code and verification on 2026-03-17
Owner model: Single owner
Reference docs:

- `docs/superpowers/reference/2026-03-16-data-sync-runs-api-reference.md`
- `docs/superpowers/reference/2026-03-17-phase-1-operator-checklist.md`
- `docs/superpowers/reference/2026-03-17-phase-1-final-checkpoint-summary.md`

## 1. Goal

This plan turns the Phase 1 data-pipeline work into an execution sequence for Month 1. The purpose is to make pipeline state explicit, expose degraded and retry behavior through one understandable contract, and improve provider and ingest diagnostics before structural decomposition begins in Phase 2.

Phase 1 pipeline work should leave four things true:

1. Pipeline state vocabulary is canonical across worker, freshness, and status surfaces.
2. Sync, retry, and degraded behavior are visible in tests and status output.
3. Provider fallback and ingest-path failures are diagnosable.
4. The system can explain stale mode with evidence rather than inference.

## 2. In Scope

Primary files:

- `core/pipeline.py`
- `data_engine/freshness.py`
- `data_engine/pipeline_worker.py`
- `data_engine/sync.py`
- `data_engine/local_feed_selector.py`
- `data_engine/ingest_intraday.py`
- `data_engine/data_quality.py`
- `routes/system.py`

Primary function seams:

- `core/pipeline.py`: `_derive_pipeline_state_from_freshness`, `_sync_worker_payload`, `refresh_pipeline_state`, `pipeline_allows_active_ops`
- `data_engine/freshness.py`: `evaluate_freshness`
- `data_engine/pipeline_worker.py`: `read_worker_state`, `_classify_pipeline_state`, `AdaptiveSyncWorker`
- `data_engine/sync.py`: `_sync_intraday`, `_sync_history`, `_sync_ticks`, `sync_all`
- `data_engine/local_feed_selector.py`: `compare_local_sources`, `resolve_local_feed_provider`, `resolve_timeframe_provider`
- `data_engine/ingest_intraday.py`: `_ingest_intraday_from_csv`, `_ingest_intraday_from_mubasher_db`, `_ingest_intraday_from_directfn`, `ingest_intraday`
- `data_engine/data_quality.py`: `validate_ohlcv_and_quarantine`

Out of scope for Phase 1:

- Major provider architecture redesign
- Full split of ingest and provider-selection modules
- New data sources
- Performance tuning not tied to visibility or correctness

## 3. Existing Test Anchors

Use the current pipeline tests as the starting harness:

- `tests/test_data_freshness_canonical.py`
- `tests/test_pipeline_stale_mode.py`
- `tests/test_strategy_and_system.py`
- `tests/test_sync_parallelism.py`
- `tests/test_observability_and_metadata.py`
- `tests/test_local_feed_selector.py`
- `tests/test_ingest_intraday_incremental.py`
- `tests/test_data_quality_dlq.py`
- `tests/test_ingest_history_incremental.py`
- `tests/test_scanner_and_data.py`
- `tests/test_v1_coverage_gap.py`

## 4. Package Sequence

Execute the pipeline track in this order:

1. `DP1` Canonical pipeline-state contract
2. `DP2` Sync and worker-state visibility
3. `DP3` Provider fallback visibility
4. `DP4` Intraday ingest and data-quality guardrails

This order matters because the system-status and stale-mode contract should be stable before provider and ingest details are tightened.

## 5. Work Packages

### DP1. Canonical Pipeline-State Contract

Status: Completed on 2026-03-17

Purpose:

Make pipeline state consistent across freshness evaluation, worker state, and system-status output.

Target files:

- `core/pipeline.py`
- `data_engine/freshness.py`
- `data_engine/pipeline_worker.py`
- `routes/system.py`

Tasks:

1. Define the canonical states used in Phase 1: fresh, syncing, stale, degraded, retrying, and failed if that state already exists implicitly.
2. Compare the classifications produced by `_derive_pipeline_state_from_freshness`, `_classify_pipeline_state`, and the system-status routes.
3. Identify mismatches between worker state and API-visible state.
4. Add or tighten tests that prove the same underlying freshness condition produces a consistent public state.

Deliverables:

- Canonical state vocabulary note
- State-mapping table from worker state to API state
- Regression coverage for stale, degraded, and syncing cases

Verification:

- `tests/test_data_freshness_canonical.py`
- `tests/test_pipeline_stale_mode.py`
- `tests/test_strategy_and_system.py`

Acceptance criteria:

- The same underlying freshness scenario yields the same state classification across worker, pipeline, and system-status surfaces.
- Stale mode is explained by explicit status fields rather than only by message text.

### DP2. Sync and Worker-State Visibility

Status: Completed on 2026-03-17

Purpose:

Make sync attempts, retries, and worker progression visible enough to diagnose whether the pipeline is actively recovering or silently stuck.

Target files:

- `data_engine/sync.py`
- `data_engine/pipeline_worker.py`
- `core/pipeline.py`

Priority seams:

- `sync_all`
- `_sync_all_with_timeout`
- `AdaptiveSyncWorker`
- `_sync_worker_payload`

Tasks:

1. Inventory current sync metadata, timeout, retry, and partial-failure handling.
2. Confirm which worker fields need to be surfaced as operator-visible status.
3. Add tests around sync partial failure, timeout, and worker-state propagation where gaps remain.
4. Improve logs and status payloads for retry scheduling, last-success timestamps, and partial-failure outcomes.

Deliverables:

- Sync and worker visibility note
- Expanded tests for sync partial failure or worker propagation
- Diagnostics improvement for retry and timeout behavior

Verification:

- `tests/test_sync_parallelism.py`
- `tests/test_observability_and_metadata.py`

Acceptance criteria:

- A sync failure can be distinguished from an in-progress sync and a stale idle pipeline.
- Worker state exposes enough information to explain whether recovery is happening.

### DP3. Provider Fallback Visibility

Status: Completed on 2026-03-17

Purpose:

Make local provider selection and fallback decisions observable and test-protected before changing the architecture in Phase 2.

Target files:

- `data_engine/local_feed_selector.py`
- `data_engine/sync.py`

Priority seams:

- `compare_local_sources`
- `resolve_local_feed_provider`
- `recommend_provider_for_timeframe`
- `resolve_timeframe_provider`

Tasks:

1. Inventory the provider recommendation and fallback decision points.
2. Identify the evidence currently available for why a provider was chosen or rejected.
3. Add or tighten tests for stale-source fallback, recommendation changes, and timeframe-specific provider selection.
4. Improve diagnostics so provider decisions are visible in logs or status output.

Deliverables:

- Provider-decision matrix
- Tests covering stale-source fallback and recommendation behavior
- Better provider selection diagnostics

Verification:

- `tests/test_local_feed_selector.py`
- `tests/test_sync_parallelism.py`

Acceptance criteria:

- When intraday or history sources are stale, the selected provider is explainable from logs or returned metadata.
- Provider fallback behavior is covered by direct tests rather than implied by broad integration flow.

### DP4. Intraday Ingest and Data-Quality Guardrails

Status: Completed on 2026-03-17

Purpose:

Tighten the visibility of intraday ingest and quarantine behavior so stale or corrupt data does not silently blend into normal operation.

Target files:

- `data_engine/ingest_intraday.py`
- `data_engine/data_quality.py`

Priority seams:

- `_get_last_ingested_minute`
- `_ingest_intraday_from_csv`
- `_ingest_intraday_from_mubasher_db`
- `ingest_intraday`
- `validate_ohlcv_and_quarantine`

Tasks:

1. Inventory the main ingest-path failure and correction behaviors.
2. Confirm how duplicate, stale-minute, and invalid OHLCV data are surfaced.
3. Add or tighten tests for same-minute correction, stale-source handling, and DLQ quarantine behavior.
4. Improve diagnostics around rejected rows, provider-specific ingest failure, and correction paths.

Deliverables:

- Intraday ingest failure note
- Better tests for correction and quarantine paths
- Diagnostics improvement for data-quality rejection or ingest-source failure
- Sync-runs API reference for frontend and operator consumers

Verification:

- `tests/test_ingest_intraday_incremental.py`
- `tests/test_data_quality_dlq.py`
- `tests/test_ingest_history_incremental.py`

Acceptance criteria:

- Intraday ingest failure and correction paths are visible in logs or metadata.
- DLQ or quarantine behavior is explicit enough to diagnose without stepping through code.

## 6. Week-by-Week Execution

### Week 1

1. Complete `DP1` state-vocabulary inventory.
2. Compare system-status output with worker-state and freshness-derived state.
3. Capture the current stale-mode evidence exposed to the API layer.

### Week 2

1. Add or tighten `DP1` and `DP2` tests.
2. Apply the first diagnostics improvements for sync and worker visibility.
3. Confirm that stale, syncing, and degraded cases remain visible through `routes/system.py`.

### Week 3

1. Execute `DP3` and document provider-selection evidence.
2. Tighten provider fallback tests where direct coverage is missing.
3. Improve provider-decision diagnostics.

### Week 4

1. Execute `DP4`.
2. Re-run the focused pipeline suites.
3. Finalize the Month 1 pipeline checkpoint summary.

## 7. Focused Command Set

Use these commands during package work:

### State and stale-mode contract

```powershell
$env:HORUS_DB_FILE=':memory:'
$env:HORUS_DISABLE_READINESS_GATE='true'
$env:DEBUG='false'
python -m pytest tests/test_data_freshness_canonical.py tests/test_pipeline_stale_mode.py tests/test_strategy_and_system.py
```

### Sync and observability

```powershell
$env:HORUS_DB_FILE=':memory:'
$env:HORUS_DISABLE_READINESS_GATE='true'
$env:DEBUG='false'
python -m pytest tests/test_sync_parallelism.py tests/test_observability_and_metadata.py tests/test_scanner_and_data.py tests/test_v1_coverage_gap.py
```

### Provider fallback and ingest

```powershell
$env:HORUS_DB_FILE=':memory:'
$env:HORUS_DISABLE_READINESS_GATE='true'
$env:DEBUG='false'
python -m pytest tests/test_local_feed_selector.py tests/test_ingest_intraday_incremental.py tests/test_data_quality_dlq.py tests/test_ingest_history_incremental.py
```

The end-of-month checkpoint still uses the full baseline from the main implementation plan.

## 8. Phase 1 Exit Checklist

Pipeline Phase 1 is complete when all of the following are true:

1. Canonical pipeline states are documented and reflected consistently in code and tests.
2. Retry, sync, stale, and degraded behavior are visible in logs or status output.
3. Provider fallback decisions are test-protected and diagnosable.
4. Intraday ingest and DLQ behavior have direct regression coverage for the main failure paths.
5. Focused pipeline suites are green.
6. The full backend baseline from the main implementation plan is green.

Phase 1 pipeline closeout result:

- All four data-pipeline packages are complete.
- Sync, retry, provider-fallback, and ingest diagnostics are now operator-visible through status or sync-run metadata.
- The full backend baseline passed on 2026-03-17.

## 9. Next Planning Boundary

Do not start module decomposition from this document. Once this Phase 1 plan is complete, the next pipeline artifact should be a Phase 2 decomposition plan for `data_engine/ingest_intraday.py`, then `data_engine/local_feed_selector.py`.
