# Horus Analytics II Packaged Startup Idle Sync Implementation Plan

Date: 2026-04-07
Based on:

- `docs/superpowers/specs/2026-04-07-packaged-startup-idle-sync-design.md`
- `docs/Log.md`
- `api.py`
- `core/settings.py`
- `core/session_mode.py`
- `core/pipeline.py`
- `data_engine/pipeline_worker.py`
- `tests/test_pipeline_worker.py`
- `tests/test_session_mode.py`
- `tests/test_startup_browser_autolaunch.py`
- `tests/test_api_runner_config.py`

Track: Packaged Startup Mode Resolution and Closed-Session Idle Sync
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Implement packaged startup behavior so Horus:

1. runs one startup sync after market close
2. stays idle until the next market open
3. keeps browser-launch choice independent from backend sync behavior
4. resolves packaged runtime mode from market time by default
5. preserves explicit force behavior for source/dev and intentional override cases
6. persists compatible worker-state metadata explaining configured mode, effective mode, and closed-session idle status

## 2. In Scope

Primary backend targets:

- `api.py`
- `core/settings.py`
- `core/session_mode.py`
- `core/pipeline.py`
- `data_engine/pipeline_worker.py`
- targeted backend tests for startup mode resolution, worker behavior, and packaged semantics

Verification and runtime confidence targets:

- packaged startup smoke check
- worker-state compatibility validation
- browser prompt regression coverage

Out of scope:

- frontend UI redesign
- scheduler redesign beyond removing duplicate ownership for closed-session wake behavior
- market-calendar feature expansion
- new sync providers
- broad `.env`/settings system redesign

## 3. Execution Rules

These rules apply across the slice:

1. Packaged runs must derive `effective_session_mode` from market status unless an explicit force flag is present.
2. A plain configured `SESSION_MODE=LIVE` must not keep packaged after-hours launches in live behavior by default.
3. After-hours packaged startup gets one sync attempt, not a retry loop.
4. If that sync completes but still ends degraded, the worker must idle anyway and report the degraded state honestly.
5. Worker-state changes must be additive and backward compatible.
6. Browser-launch prompt behavior must remain functionally unchanged.
7. Wake ownership for closed-session idle must stay in the adaptive sync worker, not be split between scheduler and worker.

## 4. Work Package Sequence

Execute in this order:

1. `PSI-P1` Session-mode resolution contract
2. `PSI-P2` Worker closed-session idle contract
3. `PSI-P3` Startup integration and logging alignment
4. `PSI-P4` Worker-state compatibility and regression coverage
5. `PSI-P5` Full verification and packaged smoke check

This order is intentional:

- packaged mode resolution must stabilize before worker behavior consumes it
- worker semantics should settle before startup wiring and state-payload changes are finalized
- tests and runtime verification should lock the integrated behavior, not partial assumptions

## 5. Work Packages

### PSI-P1. Session-Mode Resolution Contract

Purpose:

Create one startup-time resolver for configured mode, effective mode, and force behavior.

Target files:

- `core/settings.py`
- `core/session_mode.py`
- `api.py`
- targeted tests in `tests/test_session_mode.py` and `tests/test_api_runner_config.py`

Tasks:

1. Add a dedicated packaged startup mode-resolution helper or equivalent seam.
2. Preserve the existing config chain for resolving configured mode.
3. Apply the approved precedence:
   - explicit force flag wins
   - otherwise packaged startup uses market-time auto-detection
   - configured mode remains visible for logging and persistence
4. Normalize invalid configured values safely before runtime resolution.
5. Keep source/dev forcing behavior compatible.

Deliverables:

- one authoritative packaged mode-resolution contract
- explicit packaged-vs-source precedence in code and tests

Verification:

- `python -m pytest tests/test_session_mode.py tests/test_api_runner_config.py -q`

Acceptance criteria:

- packaged after-hours launches resolve to `effective_session_mode=ANALYSIS` unless force is explicitly enabled
- source/dev mode forcing remains available

### PSI-P2. Worker Closed-Session Idle Contract

Purpose:

Make the adaptive sync worker own the one-sync-then-idle behavior after close.

Target files:

- `data_engine/pipeline_worker.py`
- optionally small helper additions in `core/session_mode.py` or `core/pipeline.py`
- targeted tests in `tests/test_pipeline_worker.py`

Tasks:

1. Teach the worker to distinguish:
   - bootstrap
   - startup sync
   - closed-session idle
   - live monitoring
2. Ensure after-hours packaged boot performs exactly one sync attempt.
3. After that sync:
   - transition to live monitoring if the market opened during the sync
   - otherwise idle until the next market-open boundary
4. If the sync completes with degraded freshness, persist degraded state but do not retry after hours.
5. If the sync throws, persist error/degraded state and still idle after hours.
6. Keep wake ownership inside the worker.

Deliverables:

- one-sync closed-session worker behavior
- no repeated packaged after-hours retry loop

Verification:

- `python -m pytest tests/test_pipeline_worker.py -q`

Acceptance criteria:

- packaged after-hours runs do one sync and then stop retrying
- market-open boundary crossing during startup sync is handled deterministically

### PSI-P3. Startup Integration and Logging Alignment

Purpose:

Wire the packaged startup path so logs, startup flow, and worker behavior all reflect the same runtime truth.

Target files:

- `api.py`
- `core/pipeline.py`
- targeted tests in `tests/test_startup_browser_autolaunch.py`

Tasks:

1. Use the packaged mode-resolution result before post-ready services begin.
2. Log:
   - configured mode
   - force state
   - effective mode
   - resolution reason
3. Keep browser-launch prompt semantics unchanged.
4. Ensure browser decline does not alter backend startup behavior.
5. Avoid duplicate wake or idle ownership between startup wiring and the worker.

Deliverables:

- aligned startup logs
- startup wiring that reflects effective runtime mode

Verification:

- `python -m pytest tests/test_startup_browser_autolaunch.py -q`

Acceptance criteria:

- logs clearly explain packaged after-hours mode resolution
- browser prompt stays decoupled from sync behavior

### PSI-P4. Worker-State Compatibility and Regression Coverage

Purpose:

Extend worker-state persistence safely and lock down the new behavior with regression tests.

Target files:

- `data_engine/pipeline_worker.py`
- `core/pipeline.py`
- targeted tests in `tests/test_pipeline_worker.py` and any worker-state snapshot tests already present

Tasks:

1. Add additive worker-state fields for:
   - `configured_session_mode`
   - `effective_session_mode`
   - `forced_mode`
   - `closed_session_idle`
   - `next_wake_reason`
   - `last_startup_sync_result`
2. Keep existing fields stable for older readers.
3. Lock allowed values for the new bounded fields in tests.
4. Add regressions for:
   - packaged after-hours with `SESSION_MODE=LIVE`
   - forced-mode override
   - calendar fallback coarse re-check behavior
   - restart-safe closed-session idle behavior

Deliverables:

- backward-compatible worker-state schema extension
- test-backed regression safety for packaged startup semantics

Verification:

- `python -m pytest tests/test_pipeline_worker.py tests/test_pipeline_state_snapshot.py -q`

Acceptance criteria:

- old worker-state consumers remain functional
- new packaged startup semantics are covered by automated tests

### PSI-P5. Full Verification and Packaged Smoke Check

Purpose:

Confirm the approved behavior works end-to-end in source tests and packaged runtime.

Target files:

- no large new production seams expected
- packaging/runtime verification artifacts only

Tasks:

1. Run the focused backend test sweep.
2. Rebuild the packaged app if needed.
3. Run a packaged after-hours startup smoke test.
4. Confirm the packaged logs show:
   - one startup sync
   - closed-session idle transition
   - no repeated sync retry loop
5. Confirm market-hours behavior remains normal.

Deliverables:

- release-quality verification for the new packaged startup behavior
- packaged runtime evidence in logs

Verification:

- `python -m pytest tests/test_session_mode.py tests/test_api_runner_config.py tests/test_startup_browser_autolaunch.py tests/test_pipeline_worker.py tests/test_pipeline_state_snapshot.py -q`
- packaged EXE smoke check after rebuild

Acceptance criteria:

- packaged after-hours run performs one sync and then stays idle
- no regression in browser prompt behavior
- no regression in live-session worker behavior

## 6. Risks and Controls

### Risk 1. Mode Resolution Drifts Across Startup Layers

Control:

- centralize packaged mode resolution behind one helper
- test both direct resolution and startup integration

### Risk 2. Duplicate Wake Ownership Reappears

Control:

- keep closed-session wake responsibility in the worker
- treat scheduler as market-hours orchestration only

### Risk 3. Worker-State Extensions Break Existing Readers

Control:

- add fields only
- keep existing fields unchanged
- validate snapshot compatibility with focused tests

### Risk 4. Calendar Failure Paths Become Noisy Retry Loops

Control:

- fail closed
- use coarse re-checks only
- explicitly test unresolved market-status boot behavior

## 7. Recommended Execution Notes

- Start with tests for packaged precedence and after-hours worker behavior before broad startup rewiring.
- Keep the change backend-only unless a test proves a public status surface also needs adjustment.
- Treat the packaged EXE smoke check as mandatory, because this issue is runtime-shape specific.

## 8. Recommended Next Move After This Plan

Execute `PSI-P1` and `PSI-P2` together as the first active implementation slice, because packaged mode resolution and closed-session worker semantics are the two contracts the rest of the work depends on.
