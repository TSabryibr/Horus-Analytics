# Horus Analytics II Phase 2 Signals Decomposition Design

Date: 2026-03-17
Status: Draft for implementation planning
Document type: Design / explanation for Phase 2 execution
Target audience: Single-owner maintainer of the Horus Analytics II backend
Primary goal: Decompose `routes/signals.py` into smaller, testable units without changing behavior

## 1. Purpose

This design defines the next Phase 2 backend decomposition after the completed portfolio slice. Phase 1 hardened the signals failure contract and expanded regression coverage. The next step is to turn `routes/signals.py` into a thinner transport surface so future changes to publishing, guard logic, outcomes, and workspace analytics stop colliding in one oversized route file.

This is an internal architecture design. It is not a feature redesign.

## 2. Current Problem

`routes/signals.py` currently mixes multiple concerns in one module:

- request models and query validation helpers
- publish-window and runtime contract helpers
- guard-state read/write behavior
- daily run orchestration
- outcomes rebuild and calibration logic
- publish and retry delivery orchestration
- audit-event persistence and serialization
- workspace performance and SLA reporting

Even after Phase 1 contract hardening, three risks remain:

1. signals behavior is correct but still expensive to modify safely
2. route handlers still know too much about persistence and orchestration details
3. direct testing is skewed toward route execution instead of narrower internal seams

## 3. Phase 2 Objective

Phase 2 should keep the existing HTTP contract while moving signals behavior behind capability seams. Success means:

1. route handlers are mostly transport and request translation
2. publishing, run execution, outcomes, and workspace logic have explicit ownership
3. Phase 1 structured error contracts remain intact
4. extraction happens in slices without a big-bang rewrite

## 4. Recommended Approach

Recommended approach: capability-based extraction behind the existing route surface.

Why this approach:

- the portfolio slice already proved the extraction pattern
- the signals module already clusters naturally into helper, run, publish, outcomes, and workspace sections
- the existing tests are broad enough to protect a slice-by-slice move

Rejected alternatives:

### A. Split only by route path groups

Why rejected:

- it leaves shared publish/guard/audit helpers tangled
- it does not produce reusable internal interfaces

### B. Rewrite the entire signals domain in one pass

Why rejected:

- too much churn for one owner
- too much risk to the existing publish and audit contracts

## 5. Proposed Target Shape

Keep `routes/signals.py` as the HTTP surface, but move internals toward this shape:

1. `core/signals/boundary.py`
   - run-date parsing
   - publish-window evaluation
   - structured error/noop/block payload helpers
   - lightweight serialization helpers shared across the route

2. `core/signals/runs.py`
   - daily run orchestration
   - recommendation construction
   - walkforward validation and guard-update side effects

3. `core/signals/publishing.py`
   - publish orchestration
   - retry orchestration
   - delivery message building
   - audit-event writes tied to publish lifecycle

4. `core/signals/outcomes.py`
   - outcomes rebuild
   - calibration assembly
   - outcome query shaping

5. `core/signals/workspace.py`
   - workspace performance analytics
   - SLA reporting
   - portfolio-window metrics and related read shaping

The new package must not import `routes/signals.py`.

## 6. Extraction Order

### S2-S1: Boundary and contract helpers

Extract first:

- `_parse_run_date`
- env parsing helpers
- publish-window logic
- structured error/noop/block helpers
- validated publish-channel helper
- lightweight shared serializers where they do not pull in orchestration

Reason:

- this is the lowest-risk shared seam
- later slices depend on these helpers
- it lets the route keep the current response shapes while shrinking local contract logic

### S2-S2: Run and guard orchestration

Extract next:

- `run_daily_signals_logic`
- walkforward validation logic
- guard-state read/write helpers that belong with run policy

Reason:

- Phase 1 already stabilized blocked/freshness/guard contracts
- this isolates the execution path before publish/retry is moved

### S2-S3: Publish and retry orchestration

Extract:

- `publish_signal_run_logic`
- `_retry_failed_deliveries_logic`
- delivery message construction
- publish-side audit emission

Reason:

- this is the highest-risk mutation path
- it should move only after boundary helpers and run policy are stable

### S2-S4: Outcomes, audit, and workspace reads

Extract last:

- outcomes rebuild/query
- calibration
- audit-event list/summary shaping
- workspace performance
- SLA read path

Reason:

- these are read-heavy and can follow the established pattern once mutation paths are extracted

## 7. Test Strategy

Keep the existing route suites green throughout:

- `tests/test_signals_coverage.py`
- `tests/test_signals_p0.py`

Add direct seam tests gradually:

- `tests/test_signals_boundary_service.py`
- `tests/test_signals_run_service.py`
- `tests/test_signals_publish_service.py`
- `tests/test_signals_outcomes_service.py`

## 8. Success Criteria

The Phase 2 signals decomposition is successful when:

1. the route file is materially smaller and more transport-focused
2. Phase 1 error and block contracts remain unchanged
3. new direct seam tests exist for each extracted capability
4. backend baseline still passes after the extraction sequence
