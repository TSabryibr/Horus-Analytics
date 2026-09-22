# Horus Analytics II Closed-Session Freshness Implementation Plan

Date: 2026-03-28
Based on:

- `docs/superpowers/specs/2026-03-28-closed-session-freshness-design.md`
- `docs/Log.md`
- `data_engine/pipeline_worker.py`
- `data_engine/sync.py`
- `data_engine/freshness.py`
- `core/pipeline.py`
- `core/settings.py`
- `api.py`
- `frontend/src/app/scanner/hooks/useScannerExecution.ts`
- `frontend/src/app/scanner/components/ScannerShell.tsx`
- `frontend/src/app/status/*`

Track: Closed-Session Freshness, Weekend Calm-State, and Trading-Hours-Only Tick Sync
Status: Planned
Owner model: Single owner

## 1. Goal

Implement closed-session freshness behavior so Horus:

1. runs one verification pass after-hours or on weekends
2. marks the pipeline `FRESH` when daily history matches the expected last trading day
3. treats intraday as informational outside trading hours
4. ignores tick freshness outside trading hours
5. syncs ticks only during trading hours
6. avoids repeated closed-session `SYNCING` loops when data is already complete
7. keeps real history gaps visible and retryable

## 2. In Scope

Primary backend targets:

- `data_engine/pipeline_worker.py`
- `data_engine/sync.py`
- `data_engine/freshness.py`
- `core/pipeline.py`
- `api.py`
- targeted tests for stale-mode responses, worker behavior, and session-aware sync gating

Primary frontend targets:

- `frontend/src/app/scanner/components/ScannerShell.tsx`
- `frontend/src/app/scanner/hooks/useScannerExecution.ts`
- `frontend/src/app/status/*`
- targeted scanner/status tests

Out of scope:

- trading-hours freshness redesign
- historical provisioning changes
- market-calendar redesign
- new sync providers
- tick freshness modeling during live trading

## 3. Execution Rules

These rules apply across the slice:

1. Closed-session `FRESH` must depend on history matching the expected last working day.
2. Intraday must not block `FRESH` when the market is closed.
3. Tick sync must not run outside trading hours.
4. Tick freshness must not block closed-session `FRESH`.
5. Real history gaps must still keep stale/degraded behavior and retry eligibility.
6. Public status/scanner surfaces must reflect the same backend truth.

## 4. Work Package Sequence

Execute in this order:

1. `CSF-P1` Backend contract and stale-response metadata
2. `CSF-P2` Session-aware tick sync gating
3. `CSF-P3` Closed-session worker normalization
4. `CSF-P4` Public pipeline-state and scanner/status alignment
5. `CSF-P5` Full verification and EXE/runtime smoke check

This order is intentional:

- response contracts should stabilize before worker logic changes
- tick policy should be explicit before closed-session normalization depends on it
- worker truth should settle before frontend/status surfaces are aligned

## 5. Work Packages

### CSF-P1. Backend Contract and Stale-Response Metadata

Purpose:

Ensure stale-mode/public responses carry the closed-session context needed by scanner and status surfaces.

Target files:

- `api.py`
- `core/pipeline.py`
- targeted backend tests

Tasks:

1. Ensure stale-mode responses always expose:
   - `last_updated`
   - `expected_date`
2. Preserve compatibility with existing stale-mode consumers.
3. Add tests locking the metadata for closed-session cases.

Deliverables:

- stable stale-mode response contract
- test-backed expected-trading-day metadata

Verification:

- `python -m pytest tests/test_pipeline_stale_mode.py -q`

Acceptance criteria:

- closed-session responses expose enough context to distinguish real gaps from normal weekends

### CSF-P2. Session-Aware Tick Sync Gating

Purpose:

Make ticks a trading-hours-only sync concern.

Target files:

- `data_engine/sync.py`
- targeted sync tests

Tasks:

1. Skip tick sync entirely when the market is closed.
2. Preserve current tick sync behavior during trading hours.
3. Add tests for:
   - weekend skip
   - after-hours skip
   - trading-hours tick sync still allowed

Deliverables:

- closed-session tick skip policy
- trading-hours-only tick sync

Verification:

- `python -m pytest tests/test_strategy_and_system.py -q -k tick`

Acceptance criteria:

- ticks do not run or influence closed-session recovery work

### CSF-P3. Closed-Session Worker Normalization

Purpose:

Teach the adaptive worker to perform one verification pass and then settle to `FRESH` when closed-session history is complete.

Target files:

- `data_engine/pipeline_worker.py`
- optionally small helper additions in `data_engine/freshness.py`
- targeted worker tests

Tasks:

1. Detect closed-session mode:
   - after-hours
   - weekend
   - DB-confirmed holiday
2. Run one verification pass when entering closed-session recovery.
3. After verification:
   - if history matches expected trading day, write worker state as `FRESH`
   - clear retry/backoff
   - idle instead of looping
4. Keep retry behavior when history is still behind expected day.

Deliverables:

- closed-session `FRESH` normalization
- no repeated sync loop for complete weekend/after-hours data

Verification:

- `python -m pytest tests/test_strategy_and_system.py tests/test_pipeline_stale_mode.py -q`

Acceptance criteria:

- normal weekend/after-hours completeness settles to `FRESH`
- real history gaps still retry

### CSF-P4. Public Pipeline-State and Scanner/Status Alignment

Purpose:

Align scanner and status surfaces to the backend closed-session truth.

Target files:

- `core/pipeline.py`
- `frontend/src/app/scanner/components/ScannerShell.tsx`
- `frontend/src/app/scanner/hooks/useScannerExecution.ts`
- `frontend/src/app/status/*`
- targeted frontend tests

Tasks:

1. Ensure public pipeline state resolves to `FRESH` when worker closed-session normalization succeeds.
2. Ensure scanner no longer shows stale-mode affordances for a normal weekend-complete state.
3. Ensure status surfaces do not keep saying `SYNCING` when the market is closed and history is complete.
4. Add tests for scanner and status calm-state behavior.

Deliverables:

- scanner/status aligned with closed-session `FRESH`
- no misleading weekend stale-mode UX

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner src/app/status`

Acceptance criteria:

- weekend-complete data looks calm and healthy to operators

### CSF-P5. Full Verification and EXE/Runtime Smoke Check

Purpose:

Confirm the new behavior holds in the integrated app and packaged runtime.

Target files:

- no major new production seams expected
- verification scripts and runtime logs

Tasks:

1. Run backend verification sweep.
2. Run scanner/status frontend tests.
3. Rebuild packaged app if needed.
4. Verify packaged runtime behavior on:
   - weekend or after-hours complete data
   - stale-mode no longer appears for normal closed-session completeness

Deliverables:

- release-quality verification
- EXE/runtime confidence for the new calm-state behavior

Verification:

- `python -m pytest tests/test_pipeline_stale_mode.py tests/test_strategy_and_system.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner src/app/status`
- `npm --prefix frontend run build`
- packaged EXE smoke check

Acceptance criteria:

- backend, frontend, and packaged runtime all reflect the same closed-session truth

## 6. Verification Matrix

Each package should declare:

1. protected behavior
2. tests added or updated
3. backend/public contract changes
4. scanner/status surfaces affected
5. session behavior impact:
   - trading hours
   - after-hours
   - weekend

Minimum release-quality verification:

### Backend

```powershell
python -m pytest tests/test_pipeline_stale_mode.py tests/test_strategy_and_system.py -q
```

### Frontend

```powershell
npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner src/app/status
npm --prefix frontend run build
```

### Runtime / Manual assertions

- Thursday after market close settles to `FRESH` once Thursday history is present
- Friday/Saturday weekend does not keep retrying in `SYNCING`
- scanner does not ask to mark a normal weekend as holiday
- status surfaces do not claim syncing once closed-session verification succeeds
- tick sync does not run when the market is closed

## 7. Risks and Controls

### Risk: closed-session normalization hides real data incompleteness

Control:

- require exact match between `last_updated` and `expected_last_working_day`

### Risk: worker state and public pipeline state drift

Control:

- keep normalization in shared backend state flow, not frontend-only logic

### Risk: tick gating suppresses useful live behavior

Control:

- restrict tick skip policy strictly to closed sessions

### Risk: after-hours verification never retries when it should

Control:

- only stop retries after a successful closed-session verification
- preserve retry path for history-behind cases

## 8. Suggested Execution Cadence

For a single owner:

1. land `CSF-P1` first so metadata and tests are stable
2. land `CSF-P2` next so tick policy is explicit
3. implement `CSF-P3` once worker closed-session success criteria are locked
4. align scanner/status in `CSF-P4`
5. finish with `CSF-P5` runtime and EXE verification

## 9. First Recommended Slice

Start with `CSF-P1`.

The highest-value first edit is:

- lock stale-mode response metadata for `expected_date`
- keep scanner/runtime distinction between normal weekend completeness and real freshness gaps
- add tests before worker policy changes land

That gives the cleanest path into the remaining closed-session worker work with minimal regression risk.
