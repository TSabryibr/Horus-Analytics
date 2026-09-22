# Horus Analytics II Closed-Session Freshness Design

Date: 2026-03-28
Status: Proposed
Authoring mode: Brainstorming-approved design

Based on:

- `docs/Log.md`
- `docs/Backfill_log.md`
- `data_engine/pipeline_worker.py`
- `data_engine/sync.py`
- `data_engine/freshness.py`
- `core/pipeline.py`
- `core/settings.py`
- `api.py`
- `frontend/src/app/scanner/hooks/useScannerExecution.ts`
- `frontend/src/app/scanner/components/ScannerShell.tsx`

## 1. Purpose

This design defines how Horus should classify and manage pipeline freshness when the EGX market is closed.

The goal is to stop noisy and misleading closed-session syncing behavior while preserving one safe verification pass after startup or session change.

The intended operator-facing outcome is simple:

- during trading hours, the current live freshness model remains active
- after market close or during the weekly Friday/Saturday closure, the system should become `FRESH` once daily history is complete for the last expected trading day
- the system should not keep looping in `SYNCING` just because intraday or tick layers are naturally quiet while the market is closed

## 2. Current Problem

The current system already knows the EGX weekend and already computes the last completed market day correctly.

That logic exists in:

- `core/settings.py`
- `data_engine/freshness.py`

However, the adaptive worker currently keeps pursuing a generic non-`FRESH` state:

- it runs `sync_all()` whenever the worker classifies the pipeline as not `FRESH`
- `sync_all()` only skips intraday on weekends
- history and tick stages can still run
- the worker can remain in `SYNCING` or retry mode even when the last completed trading day is already present

This creates a poor closed-session experience:

- scanner can show read-only stale mode while data is actually correct for the last market day
- operators may see weekend/after-hours syncing that looks suspicious
- tick activity can continue influencing the perception of freshness even when ticks are irrelevant outside trading hours

## 3. Design Goals

This package should leave five things true:

1. Closed-session freshness is decided primarily by daily history completeness.
2. The system performs one verification pass after startup or session transition, not endless closed-session retries.
3. Intraday data does not block `FRESH` outside trading hours.
4. Tick sync is ignored for after-hours/weekend freshness and only runs during trading hours.
5. Operator-facing surfaces show `FRESH` when the market is closed and the expected trading day is already present.

## 4. Non-Goals

This package does not attempt to:

- redesign trading-hours freshness classification
- change historical provisioning rules
- change market calendar configuration beyond existing weekend and holiday behavior
- introduce exchange-specific tick freshness policies during live trading
- change scan logic itself

## 5. Session Model

The design divides runtime into two session classes:

### 5.1 Trading Session

A trading session means:

- market is open

In this mode:

- current adaptive sync behavior remains active
- history, intraday, and tick sync can all run
- intraday and live-feed freshness can still affect the overall pipeline state

### 5.2 Closed Session

A closed session means either:

- after market close on a working day
- or weekly weekend closure
- or a database-confirmed holiday

In this mode:

- the system may run one verification pass
- the system must not remain in aggressive retry/sync loops once daily history is confirmed complete

## 6. Closed-Session Freshness Rule

Closed-session freshness should be determined by the following rule:

- if `history.last_updated == history.expected_last_working_day`
- then the overall closed-session pipeline state is `FRESH`

That rule explicitly means:

- intraday freshness becomes informational only outside trading hours
- tick freshness does not participate in closed-session readiness

This is the central policy decision in the design.

## 7. Tick Policy

Tick policy should become session-aware.

### Trading Hours

- tick sync behaves as it does now
- tick activity may continue for normal data maintenance

### Closed Session

- tick sync should not run
- tick data should not block or degrade closed-session freshness
- tick data should not keep the worker in `SYNCING`

This matches the operator requirement that tick sync is only relevant during trading hours.

## 8. Worker Behavior

The adaptive worker should gain explicit closed-session behavior.

### 8.1 Closed-Session Entry

When the worker starts in a closed session, or when a trading session transitions into a closed session:

1. evaluate current freshness
2. perform one verification sync pass
3. re-evaluate freshness using closed-session rules

### 8.2 Closed-Session Success

If the verification pass confirms:

- `last_updated == expected_last_working_day`

then the worker should:

- write pipeline state as `FRESH`
- clear retry reason
- clear backoff
- stop repeated retry looping
- enter an idle closed-session heartbeat state

### 8.3 Closed-Session Failure

If the verification pass still shows history behind the expected trading day:

- worker may keep the current degraded/stale behavior
- retries remain allowed because there is a real history gap

This preserves resilience without masking actual data incompleteness.

## 9. Freshness Classification Recommendation

The implementation should preserve the existing trading-hours classification model and add a closed-session override path rather than rewriting the entire freshness engine.

Recommended behavior:

- trading hours:
  - current classification remains authoritative
- closed session:
  - if expected history day is present, normalize the worker-facing pipeline state to `FRESH`

This keeps the blast radius smaller than rewriting the whole data-freshness model.

## 10. UI and API Effects

Once the closed-session rule is active:

### 10.1 Scanner

- scanner should not enter stale-mode blocking for a normal weekend or after-hours state when daily history is already complete
- the holiday-confirmation path should remain reserved for true calendar ambiguity, not normal weekly closure

### 10.2 Status

- runtime and system-status surfaces should show `FRESH` when the market is closed and history is complete
- they should not keep saying `SYNCING` purely because intraday or tick layers are inactive

### 10.3 API Contracts

Existing stale-mode APIs should remain compatible.

However, the pipeline state they emit after closed-session verification should now settle to:

- `FRESH` when expected history is present

## 11. Implementation Shape

Primary implementation seams:

- `data_engine/pipeline_worker.py`
  - closed-session verification and idle behavior
- `data_engine/sync.py`
  - tick sync gating by session
- `core/pipeline.py`
  - worker-state normalization into public pipeline state
- `data_engine/freshness.py`
  - only if additive metadata or helper functions are needed

Supporting seams:

- `api.py`
- `frontend/src/app/scanner/*`
- `frontend/src/app/status/*`

The recommended strategy is to keep the main policy in backend worker/runtime code so all consumers inherit the same truth.

## 12. Testing Strategy

### 12.1 Backend

Add tests that prove:

- closed-session verification marks the system `FRESH` when history matches expected trading day
- worker does not keep retrying in a normal weekend-complete state
- tick sync is skipped during closed session
- a real history gap still keeps stale/degraded behavior

Suggested targets:

- `tests/test_pipeline_stale_mode.py`
- `tests/test_strategy_and_system.py`
- targeted worker/sync seam tests

### 12.2 Frontend

Add tests that prove:

- scanner does not show stale-mode controls for normal weekend completeness
- status surfaces show `FRESH` instead of `SYNCING` after closed-session verification success

Suggested targets:

- `frontend/src/app/scanner/*`
- `frontend/src/app/status/*`

## 13. Risks and Controls

### Risk: closed-session logic hides a real data gap

Control:

- only normalize to `FRESH` when history exactly matches the expected last working day

### Risk: worker becomes inconsistent with public pipeline state

Control:

- keep normalization in shared backend state, not in individual frontend consumers

### Risk: tick data becomes stale silently

Control:

- make this explicit policy: ticks are trading-hours-only freshness inputs

### Risk: after-hours live workflow loses useful reconciliation

Control:

- keep one verification pass before idling
- preserve retries when history remains behind expected trading day

## 14. Recommended Rollout

Recommended order:

1. add failing backend tests for closed-session `FRESH` normalization
2. make tick sync session-aware
3. update worker closed-session behavior
4. verify public pipeline state resolves to `FRESH`
5. add frontend tests for scanner/status calm-state behavior

## 15. Expected Outcome

After this package:

- Thursday after close can settle to `FRESH` once Thursday history is present
- Friday/Saturday weekend can remain `FRESH` without repeated sync noise
- intraday inactivity no longer makes closed sessions look unhealthy
- tick sync no longer runs or blocks readiness outside trading hours
- operators see a calmer, more truthful closed-session system
