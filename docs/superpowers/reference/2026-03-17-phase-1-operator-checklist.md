# Horus Analytics II Phase 1 Operator Note and Checklist

Date: 2026-03-17
Audience: Single-owner operator and maintainer
Scope: Phase 1 production safety rails, diagnostics, and release verification

## 1. Purpose

This note is the Phase 1 operator-facing companion to the reliability-first program. It documents the minimum checks to run when the system is unhealthy, when a sync or signal workflow looks blocked, and when preparing a release-quality checkpoint.

Phase 1 changed the app in three operator-relevant ways:

1. Pipeline state, retry state, and degraded mode are now exposed more consistently.
2. Sync-run diagnostics now surface provider fallback, problem type, stage, and provider facets directly from the API.
3. Backend, frontend, browser, and manual visual checks now form one practical release gate.

## 2. Quick Triage Order

When the app looks unhealthy, check surfaces in this order:

1. `GET /api/v1/system/status`
2. `GET /api/v1/system/full-status`
3. `GET /api/v1/data/status`
4. `GET /api/v1/data/sync/status`
5. `GET /api/v1/data/sync/runs?problems_only=true`

If the issue is signal publication or blocked execution, also check:

1. the relevant signals route response payload
2. audit-event output for the same run
3. the current guard-state and freshness context included in the returned payload

## 3. What the Main States Mean

### Pipeline status

- `FRESH`: Data is healthy enough for active operations.
- `SYNCING`: The worker is actively recovering or ingesting.
- `STALE`: Data is behind freshness thresholds and active operations may be blocked.
- `DEGRADED`: The pipeline is up, but fallback, partial failure, or mixed-source freshness is present.

### Sync worker runtime fields

- `recovering=true`: The worker is actively syncing or retrying from a stale/degraded state.
- `retry_reason=sync_in_progress`: A sync is underway now.
- `retry_reason=freshness_below_threshold`: The worker is retrying because freshness is still not acceptable.
- `retry_reason=sync_failed`: The last sync attempt failed and the worker is retrying.

### Sync-run problem classification

Each run row in `/api/v1/data/sync/runs` now exposes:

- `problem_type`
- `has_selection_fallback`
- `has_runtime_fallback`
- `runtime_used_provider`
- `runtime_fallback_from`
- `runtime_failure_mode`
- `runtime_status`

Use `problem_type` first for triage:

- `error`: Stage failed.
- `warning`: Stage completed with warning state.
- `runtime_fallback`: Stage only completed after an ingest-time provider fallback.
- `selection_fallback`: Provider policy selected a fallback source before execution started.

## 4. Sync-Runs Checklist

Use these filters first when diagnosing ingestion behavior:

### Problem-focused scan

`GET /api/v1/data/sync/runs?problems_only=true`

### Runtime fallback only

`GET /api/v1/data/sync/runs?fallback_type=runtime`

### Exact problem class

`GET /api/v1/data/sync/runs?problem_type=error`

### Stage/provider narrowing

- `GET /api/v1/data/sync/runs?stage=ingest_history`
- `GET /api/v1/data/sync/runs?provider=MUBASHER_DB`

Read these parts of the response in order:

1. `summary`
2. `facets.problem_type_counts`
3. `facets.fallback_type_counts`
4. `facets.stage_counts`
5. `facets.provider_counts`
6. `runs[*].provider_context`

## 5. Signals Checklist

When signal generation or publishing is blocked:

1. Confirm whether the response is a block contract or a failure contract.
2. Read `block_type` and `block_reason` first.
3. If it is a guard block, inspect:
   - `guard`
   - `guard_reason`
   - `guard_source`
   - `guard_details`
4. If it is a freshness block, inspect the freshness payload rather than the message text alone.
5. If publish or retry did not proceed, inspect:
   - `error_type`
   - `error_reason`
   - `noop_type`
   - `noop_reason`
   - `summary.skip_reasons`
   - `summary.failure_reasons`

## 6. AI Daily Report Checklist

When the AI report does not look healthy:

1. Check whether the response is degraded or failed.
2. Read:
   - `degraded`
   - `degradation_stage`
   - `degradation_reason`
   - `provider_fallback_used`
   - `snapshot_degraded`
   - `snapshot_degradation`
3. Treat degraded `200` responses as usable but reduced-confidence outputs.
4. Treat structured `500` responses as hard failures that require provider or collection-path follow-up.

## 7. Portfolio and Data Boundary Checklist

Phase 1 tightened many request boundaries. If an endpoint now fails faster than before:

1. Confirm whether the input is now rejected at schema/query validation.
2. Expect non-positive `portfolio_id`, blank tickers, and invalid filter values to fail at the boundary.
3. For report, data, and scanner flows, check exclusions before assuming route failure.

## 8. Release Checkpoint Checklist

Run from repo root.

### Backend baseline

```powershell
$env:HORUS_DB_FILE=':memory:'
$env:HORUS_DISABLE_READINESS_GATE='true'
$env:DEBUG='false'
python -m pytest tests/ --doctest-modules
```

### Frontend baseline

```powershell
npm --prefix frontend run lint
npm --prefix frontend run test -- --runInBand
npm --prefix frontend run build
```

### Browser baseline

```powershell
npm --prefix frontend run test:e2e
```

### Manual visual audit

```powershell
npm --prefix frontend run test:e2e:audit
```

## 9. Escalation Guidance

Escalate beyond routine operator handling when any of the following is true:

1. `system/status` and `data/status` disagree on the health story.
2. `recovering=true` persists without meaningful sync-run movement.
3. `runtime_fallback` becomes the dominant completion mode for a provider or stage.
4. Signal publishing is repeatedly blocked for the same structured reason without a deliberate guard/freshness policy.
5. The release checkpoint is green only because a package-specific subset was used instead of the full baseline.

## 10. Phase 1 Closeout Result

As of 2026-03-17, the full Phase 1 checkpoint is green:

- backend baseline passed
- frontend baseline passed
- browser baseline passed
- manual visual audit passed

Residual warnings still exist in the full suite, but they are not blocking the Phase 1 checkpoint.
