# Phase 3 Operating Surface Checklist

Date: 2026-03-17
Phase: Phase 3 closeout
Status: Active release checklist

## Purpose

This checklist closes the remaining Phase 3 follow-on packages after the AI report structural repair. It is the operator-facing validation path for throughput fixes, browser/runtime stability, and stale-or-degraded runtime behavior.

## Backend and Performance Gate

Run:

- `.\.venv313\Scripts\python.exe -m pytest tests/ --doctest-modules`

Validate:

- The full backend baseline passes.
- The AI report seam suites remain green:
  - `tests/test_ai_daily_report.py`
  - `tests/test_ai_report_boundary_service.py`
  - `tests/test_ai_report_snapshot_service.py`
  - `tests/test_ai_report_generation_service.py`
  - `tests/test_ai_report_transport_service.py`
- The simulation/time-travel performance gate remains green:
  - `tests/test_simulation_performance.py`
  - `tests/test_datamanager.py`

## Frontend and Browser Gate

Run:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Validate:

- Shared runtime-state semantics build cleanly.
- Browser crawl/specs pass without fixed boot sleeps or manual retries.
- Critical operator-facing views still pass after runtime-state wording changes:
  - scanner
  - status
  - sidebar shell

## Runtime Surface Checks

Check these surfaces after deployment:

- `GET /api/v1/system/status`
- `GET /api/v1/system/full-status`
- `GET /api/v1/data/status`
- `POST /api/v1/scanner/start`
- `GET /api/v1/ai/daily-report`
- `POST /api/v1/ai/daily-report/broadcast`

Validate:

- Stale or syncing runtime state is readable from status surfaces without opening the code.
- Scanner stale-mode blocks are presented as a stale/degraded operator state, not a generic connection failure.
- Sidebar, status, and scanner surfaces use the same runtime-state vocabulary for healthy, syncing, and stale conditions.
- AI report degraded and fallback responses still expose structured degradation metadata.

## Common Failure-Class Runbook

### Pipeline stale

Check:

- `GET /api/v1/system/full-status`
- `GET /api/v1/data/status`

Respond:

- If the sync worker is `SYNCING` or `recovering=true`, wait for the next retry window before restarting anything.
- If history or intraday are stale and not recovering, start a data sync and re-check `data/status`.
- If stale mode persists after sync completion, inspect the latest `data/sync/runs?problems_only=true`.

### Provider unavailable or fallback-driven ingest

Check:

- `GET /api/v1/data/status`
- `GET /api/v1/data/sync/runs?problems_only=true&fallback_type=runtime`

Respond:

- If provider fallback is visible and runs are still succeeding, degrade and continue.
- If fallback is absent and a provider repeatedly fails, stop trusting fresh intraday assumptions until the provider path is restored.

### Startup degraded or backend route failure

Check:

- `GET /api/v1/system/status`
- affected route response body

Respond:

- Distinguish `bootstrap` or stale/readiness failures from unexpected `500` responses using the structured error fields.
- Retry only after the bootstrap or stale gate clears.
- Escalate immediately if the same route returns structured `500` failures after readiness is green.

### Frontend runtime or build breakage

Run:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Respond:

- If lint or Jest fails, fix the runtime contract mismatch before shipping.
- If build fails, do not ship; treat it as a release stop.
- If Playwright fails on boot or route crawl, treat it as a runtime-surface regression and re-check the shared boot/readiness helpers before re-running.

## Release Decision

Ship only if all of the following are true:

- Full backend baseline is green.
- Frontend lint, Jest, build, and Playwright are green.
- Simulation-performance and AI report seam packages remain green.
- Runtime-state semantics are readable and consistent across sidebar, status, and scanner surfaces.
