# Phase 2 Operating Surface Checklist

Date: 2026-03-17
Phase: Phase 2 closeout
Status: Active release checklist

## Purpose

This checklist is the operator-facing validation sequence for the Phase 2 system shape. It assumes the Phase 1 runtime contracts are already in place and adds the new Phase 2 seams that must be checked before trusting a release.

## Backend and Pipeline Gate

Run:

- `python -m pytest tests/ --doctest-modules`

Validate:

- The full backend baseline passes.
- New seam suites are present and green:
  - `tests/test_portfolio_identity_service.py`
  - `tests/test_portfolio_command_service.py`
  - `tests/test_portfolio_query_service.py`
  - `tests/test_signals_boundary_service.py`
  - `tests/test_signals_run_service.py`
  - `tests/test_signals_publish_service.py`
  - `tests/test_signals_outcomes_service.py`
  - `tests/test_provider_selection_service.py`

## Frontend Gate

Run:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`
- `npm --prefix frontend run test:e2e:audit`

Validate:

- The shared-data contexts build cleanly.
- Browser smoke routes still load after the shared-data timestamp normalization.
- The manual visual audit still passes after the context changes.

## Runtime Surface Checks

Check these API surfaces after deployment:

- `GET /api/v1/system/status`
- `GET /api/v1/system/full-status`
- `GET /api/v1/data/status`
- `GET /api/v1/data/sync/runs?problems_only=true`
- `GET /api/v1/signals/ops/sla?days=30`
- `GET /api/v1/signals/audit/summary?days=30`

Validate:

- System status exposes canonical pipeline and sync-worker state.
- Data status exposes provider-decision evidence for history and intraday.
- Sync runs expose `problem_type`, fallback classification, and filtered facets.
- Signals SLA and audit surfaces return structured operator-readable summaries.

## Release Decision

Ship only if all of the following are true:

- Backend baseline is green.
- Frontend lint, tests, build, Playwright, and audit are green.
- No new seam-level regressions appear in portfolio, signals, or provider-selection services.
- Status and sync-history endpoints are sufficient to classify stale, degraded, retrying, and fallback states without opening the code.
