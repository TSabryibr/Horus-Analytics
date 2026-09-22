# Horus Analytics II Phase 2 Signals Decomposition Implementation Plan

Date: 2026-03-17
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-17-phase-2-signals-decomposition-design.md`

Track: Backend/API Stability
Phase: Phase 2 - Structural Repair in High-Risk Areas
Status: Completed on 2026-03-17
Owner model: Single owner

## 1. Goal

This plan turns the approved signals decomposition design into an execution sequence. The purpose is to turn `routes/signals.py` into a thinner transport layer without changing endpoint paths, HTTP contracts, publish semantics, or Phase 1 structured failure behavior.

## 2. In Scope

Primary source file:

- `routes/signals.py`

Primary extraction target package:

- `core/signals/__init__.py`
- `core/signals/boundary.py`
- `core/signals/runs.py`
- `core/signals/publishing.py`
- `core/signals/outcomes.py`
- `core/signals/workspace.py`

Primary route families:

- daily run execution
- publish and retry flows
- guard and walkforward flows
- outcomes and calibration flows
- workspace and SLA reads
- audit-event reads

## 3. Existing Test Anchors

Keep these route-level suites green through every extraction package:

- `tests/test_signals_coverage.py`
- `tests/test_signals_p0.py`

Add direct seam tests gradually:

- `tests/test_signals_boundary_service.py`
- `tests/test_signals_run_service.py`
- `tests/test_signals_publish_service.py`
- `tests/test_signals_outcomes_service.py`

## 4. Package Sequence

1. `S2-S1` Boundary and contract helpers
2. `S2-S2` Run and guard orchestration
3. `S2-S3` Publish and retry orchestration
4. `S2-S4` Outcomes, audit, and workspace reads

## 5. Work Packages

### S2-S1. Boundary and Contract Helpers

Status: Completed on 2026-03-17

Purpose:

Move the lowest-risk shared helpers first so later extractions reuse one contract surface.

Target files:

- `routes/signals.py`
- `core/signals/__init__.py`
- `core/signals/boundary.py`

Tasks:

1. Extract run-date parsing, env parsing, publish-window logic, structured error/noop helpers, and validated channel checks.
2. Keep route helper names as thin wrappers where the existing test suite monkeypatches or imports them directly.
3. Add direct seam tests for window states, invalid run-date behavior, channel validation, and structured payload helpers.

Verification:

- `python -m pytest tests/test_signals_boundary_service.py -q`
- `python -m pytest tests/test_signals_coverage.py tests/test_signals_p0.py -k "invalid_run_date or unsupported_channel or window or retry_latest" -q`

Closeout note:

- Boundary helpers now live in `core/signals/boundary.py`, with `routes/signals.py` preserving import and monkeypatch compatibility through thin wrappers.

### S2-S2. Run and Guard Orchestration

Status: Completed on 2026-03-17

Purpose:

Move run execution and guard-state behavior behind focused services before publish logic moves.

Target files:

- `routes/signals.py`
- `core/signals/runs.py`

Tasks:

1. Extract `run_daily_signals_logic` and walkforward-validation orchestration.
2. Move guard-state read/write helpers that belong with run policy into the run layer.
3. Keep Phase 1 blocked/freshness/guard payloads unchanged.

Verification:

- `python -m pytest tests/test_signals_run_service.py -q`
- `python -m pytest tests/test_signals_coverage.py tests/test_signals_p0.py -k "guard or freshness or walkforward or runs/daily" -q`

Closeout note:

- Run execution, freshness blocking, guard state, and walkforward orchestration now live in `core/signals/runs.py`.

### S2-S3. Publish and Retry Orchestration

Status: Completed on 2026-03-17

Purpose:

Isolate the highest-risk signals mutation path after the shared contract seam exists.

Target files:

- `routes/signals.py`
- `core/signals/publishing.py`

Tasks:

1. Extract publish and retry orchestration.
2. Move delivery-message building and publish audit writes into the publish layer.
3. Keep dry-run, blocked, retry-noop, and delivery-failure summaries unchanged.

Verification:

- `python -m pytest tests/test_signals_publish_service.py -q`
- `python -m pytest tests/test_signals_coverage.py tests/test_signals_p0.py -k "publish or retry or deliveries" -q`

Closeout note:

- Publish/retry orchestration, delivery serialization, retry-noop handling, and delivery message building now live in `core/signals/publishing.py`.

### S2-S4. Outcomes, Audit, and Workspace Reads

Status: Completed on 2026-03-17

Purpose:

Finish the route by separating read/reporting paths from transport concerns.

Target files:

- `routes/signals.py`
- `core/signals/outcomes.py`
- `core/signals/workspace.py`

Tasks:

1. Extract outcomes rebuild/query and calibration logic.
2. Extract audit-event summary/list shaping.
3. Extract workspace performance and SLA read paths.

Verification:

- `python -m pytest tests/test_signals_outcomes_service.py -q`
- `python -m pytest tests/test_signals_coverage.py tests/test_signals_p0.py -k "outcomes or calibration or workspace or sla or audit" -q`

Closeout note:

- Outcomes/audit/validation reads now live in `core/signals/outcomes.py`, and workspace/SLA reads now live in `core/signals/workspace.py`.

## 6. Phase 2 Exit Checklist for Signals Decomposition

- `routes/signals.py` is materially smaller and more transport-focused
- shared signals contract logic lives in `core/signals/boundary.py`
- run and guard orchestration lives in `core/signals/runs.py`
- publish and retry orchestration lives in `core/signals/publishing.py`
- outcomes and workspace reads live in dedicated modules
- route-level signals tests remain green
- new seam-level tests exist for each extracted capability
- full backend baseline still passes

Checkpoint reference:

- `docs/superpowers/reference/2026-03-17-phase-2-signals-checkpoint-summary.md`
