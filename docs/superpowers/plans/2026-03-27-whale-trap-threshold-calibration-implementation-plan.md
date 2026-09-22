# Horus Analytics II Whale And Trap Threshold Calibration Implementation Plan

Date: 2026-03-27
Based on:

- `docs/superpowers/specs/2026-03-27-whale-trap-threshold-calibration-design.md`
- `docs/superpowers/specs/2026-03-27-whale-trap-enforcement-gates-design.md`
- `docs/superpowers/plans/2026-03-27-whale-trap-enforcement-gates-implementation-plan.md`
- `core/enforcement_gates.py`
- `core/DailyScanner.py`
- `routes/scanner.py`
- `routes/signals.py`
- `core/signals/publishing.py`
- `core/ai_report/snapshot.py`
- `core/ai_report/generation.py`
- scanner and Oracle/operator-facing enforcement diagnostics already implemented

Track: Whale/Trap Threshold Calibration, Compare-Only Diagnostics, and Threshold Tuning
Status: Completed
Owner model: Single owner

Implementation outcome:

- `TC-P1` completed
- `TC-P2` completed
- `TC-P3` completed
- `TC-P4` completed
- `TC-P5` completed

The first-release calibration slice is now implemented in compare-only mode across shared seams, scanner/runtime diagnostics, publishing/audit summaries, and AI/Oracle operator-facing narratives.

## 1. Goal

This plan turns the approved threshold-calibration design into an execution-ready sequence for one owner.

The implementation must leave seven things true:

1. Threshold calibration is computed in shared backend seams instead of being improvised inside scanner, publishing, or AI report code.
2. Candidate threshold profiles remain compare-only in the first release and do not change actual enforced behavior.
3. Baseline and candidate profiles can be compared using the same candidate set and the same enforcement vocabulary.
4. EGX30 and EGX70 calibration behavior remains profile-aware and explicit.
5. Operators can inspect reclassification deltas, dominant reason shifts, and top changed names.
6. Publishing and AI/report surfaces can consume calibration summaries without changing live enforcement outputs.
7. Simulator and live execution remain untouched in this calibration package.

## 2. In Scope

Primary backend targets:

- new shared seams under `core/`:
  - `core/enforcement_profiles.py`
  - `core/enforcement_calibration.py`
- `core/enforcement_gates.py`
- `core/DailyScanner.py`
- `routes/scanner.py`
- `routes/signals.py`
- `core/signals/publishing.py`
- `core/ai_report/snapshot.py`
- `core/ai_report/generation.py`
- targeted tests for profile configuration, calibration seam, scanner/runtime diagnostics, publishing summaries, and AI/report consumption

Potential frontend/runtime touchpoints:

- scanner-facing diagnostics panels if compare-only calibration summaries become visible there
- operator-facing Oracle/report surfaces only if additive calibration language is included

Out of scope:

- changing the active enforced profile automatically
- simulator trade allow/block logic
- live broker execution changes
- machine-learning-based profile optimization
- hidden-row or hidden-recommendation behavior
- automatic intraday threshold tuning

## 3. Execution Rules

These rules apply to every package in this slice:

1. Candidate calibration profiles must remain compare-only in the first release.
2. No scanner row or publishable recommendation may change state solely because a candidate calibration profile is evaluated.
3. No calibration logic may live only in UI or route code.
4. Baseline enforcement and calibration comparison must use the same shared candidate metadata inputs.
5. Prefer explicit profile configuration and reason-labeled deltas over implicit heuristics.
6. No simulator or live execution behavior may be touched in this package.

## 4. Work Package Sequence

Execute this slice in the following order:

1. `TC-P1` Threshold profile configuration extraction
2. `TC-P2` Shared calibration seam
3. `TC-P3` Scanner/runtime compare-only diagnostics
4. `TC-P4` Publishing and audit calibration summaries
5. `TC-P5` AI/Oracle calibration narrative closeout

This order is intentional:

- profile configuration should exist before calibration comparison depends on it
- the calibration seam should stabilize before consumer wiring begins
- scanner/runtime diagnostics should expose compare-only outputs before publishing or AI/report summarize them
- publishing and AI/report should remain readers of already-stable calibration summaries

## 5. Work Packages

### TC-P1. Threshold Profile Configuration Extraction

Purpose:

Move active and candidate threshold settings into explicit configuration so calibration comparisons use named profiles rather than scattered conditionals.

Target files:

- `core/enforcement_profiles.py`
- `core/enforcement_gates.py`
- targeted tests

Tasks:

1. Extract threshold-profile definitions into a shared configuration module.
2. Represent:
   - active baseline profile
   - one or two candidate compare-only profiles
   - segment-aware behavior for `EGX30` and `EGX70`
3. Refactor `core/enforcement_gates.py` to read thresholds from named profile configuration rather than embedded branching where practical.
4. Add tests that lock:
   - profile normalization
   - active profile lookup
   - candidate profile lookup
   - EGX30 vs EGX70 profile resolution

Deliverables:

- explicit threshold profile definitions
- shared profile lookup path
- stable baseline for compare-only evaluation

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_enforcement_gates.py tests/test_whale_trap_metadata_contract.py -q`

Acceptance criteria:

- profile settings are readable, named, and test-backed
- enforcement seam can resolve profile settings without consumer-specific branching

### TC-P2. Shared Calibration Seam

Purpose:

Evaluate candidate profiles against the same candidate set as the active baseline and compute compare-only deltas.

Target files:

- `core/enforcement_calibration.py`
- `core/enforcement_gates.py`
- targeted seam tests

Tasks:

1. Add shared compare-only helpers that:
   - evaluate baseline profile outcomes
   - evaluate candidate profile outcomes
   - compute allow/watch/block deltas
   - compute reason deltas
   - identify top reclassified names
2. Keep output additive so baseline enforced state remains authoritative.
3. Ensure compare-only summaries can carry:
   - active profile name
   - candidate profile names
   - baseline counts
   - candidate counts
   - deltas
4. Add direct tests for:
   - unchanged candidate set yields zero deltas
   - stricter candidate profile increases watch-only/block counts
   - top delta reasons are sorted deterministically
   - top reclassified names are stable and explainable

Deliverables:

- reusable calibration seam
- deterministic compare-only delta contract

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_enforcement_gates.py tests/test_strategy_and_system.py -q`

Acceptance criteria:

- calibration comparison is produced through one shared seam
- candidate profiles never overwrite actual baseline enforcement state

### TC-P3. Scanner/Runtime Compare-Only Diagnostics

Purpose:

Expose baseline-versus-candidate calibration summaries in runtime diagnostics without changing the visible enforced state of scanner rows.

Target files:

- `core/DailyScanner.py`
- `routes/scanner.py`
- scanner-facing frontend/runtime consumers if compare-only diagnostics are surfaced
- targeted scanner/runtime tests

Tasks:

1. Evaluate candidate calibration profiles after baseline enforcement state is already attached.
2. Extend runtime diagnostics with:
   - baseline counts
   - candidate counts
   - deltas
   - top reclassified names
   - top delta reasons
3. Keep row-level enforcement state tied to baseline only.
4. Add tests for:
   - calibration summary presence
   - baseline row state unchanged
   - compare-only labels clearly marked
   - segment-specific deltas for EGX30 and EGX70

Deliverables:

- scanner/runtime calibration diagnostics
- compare-only delta visibility for operators

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner`

Acceptance criteria:

- scanner shows calibration diagnostics without altering enforced row states
- operators can inspect candidate-threshold drift without confusion about active behavior

### TC-P4. Publishing and Audit Calibration Summaries

Purpose:

Make publishing and audit surfaces able to summarize compare-only threshold deltas while still following the active baseline profile only.

Target files:

- `routes/signals.py`
- `core/signals/publishing.py`
- targeted publishing and audit tests

Tasks:

1. Thread calibration summaries into publish-side diagnostics and audit payloads.
2. Keep actual publishing decisions bound to the active baseline profile only.
3. Add audit metadata for:
   - active baseline profile
   - candidate compared profile
   - allow/watch/block deltas
   - top delta reasons
4. Add tests for:
   - publishable output unchanged under compare-only evaluation
   - audit payload includes calibration metadata
   - blocked/watch-only operational outputs still follow baseline only

Deliverables:

- publish/audit calibration summaries
- evidence trail for threshold tuning review

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_signals_coverage.py tests/test_signals_publish_service.py tests/test_signals_p0.py -q`

Acceptance criteria:

- calibration metadata is available to audit review
- compare-only profiles do not leak into live publishing decisions

### TC-P5. AI/Oracle Calibration Narrative Closeout

Purpose:

Teach AI/report and Oracle surfaces to summarize calibration drift as a required part of the first slice without turning them into primary decision engines.

Target files:

- `core/ai_report/snapshot.py`
- `core/ai_report/generation.py`
- operator-facing Oracle/report consumers if additive summaries are surfaced
- targeted tests

Tasks:

1. Thread calibration summaries into AI snapshot payloads.
2. Add compact report/oracle language for:
   - baseline blocked count
   - candidate blocked count
   - top reclassification reasons
3. Keep language descriptive and compare-only.
4. Add tests for:
   - calibration summary exposure
   - compare-only wording
   - graceful degradation when candidate calibration data is absent

Deliverables:

- required AI/report calibration summaries
- consistent compare-only wording across operator-facing surfaces

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_ai_daily_report.py tests/test_ai_report_generation_service.py tests/test_api_endpoints.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/oracle`

Acceptance criteria:

- AI/report surfaces can describe calibration drift without recomputing enforcement logic
- compare-only summaries are clearly separate from actual enforced outputs

## 6. Verification Matrix

Each work package must declare:

1. protected behavior
2. tests added or updated
3. scanner, publishing, or AI/report surfaces affected
4. compare-only diagnostics added
5. rollout mode: baseline enforcement unchanged, candidate calibration compare-only

Minimum release-quality verification for the full slice:

### Backend

```powershell
$env:HORUS_DB_FILE=':memory:'
.\.venv313\Scripts\python -m pytest tests/test_enforcement_gates.py tests/test_scanner_and_data.py tests/test_signals_coverage.py tests/test_signals_publish_service.py tests/test_signals_p0.py tests/test_ai_daily_report.py tests/test_ai_report_generation_service.py tests/test_api_endpoints.py -q
```

### Frontend

```powershell
npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner
npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/oracle
npm --prefix frontend run build
```

### Manual assertions

- scanner row states remain tied to the active baseline profile
- candidate profiles appear only in compare-only diagnostics
- publishing remains unchanged by candidate calibration profiles
- audit summaries can explain baseline-versus-candidate deltas
- AI/report language does not imply candidate profiles are already active

## 7. Risks and Controls

### Risk: compare-only summaries accidentally affect live enforcement

Control:

- keep baseline enforcement and calibration comparison on separate paths with tests asserting no state mutation

### Risk: calibration profiles become hard to reason about

Control:

- keep profile definitions explicit, named, and small in the first release

### Risk: operators misread candidate deltas as active rules

Control:

- use explicit compare-only labeling and preserve baseline state vocabulary

### Risk: reason deltas are noisy or unstable

Control:

- sort and cap top delta reasons and reclassified names deterministically

### Risk: the package drifts into simulator/live threshold tuning

Control:

- keep simulator and live execution explicitly out of scope for this plan

## 8. Suggested Execution Cadence

For a single owner, the recommended order is:

1. finish `TC-P1` and `TC-P2` first so profile configuration and comparison logic stabilize before consumer wiring
2. land `TC-P3` before publishing or AI/report summary work so operators can inspect runtime deltas first
3. land `TC-P4` once compare-only summaries are stable and auditable
4. close with `TC-P5` so operator-facing AI/report surfaces remain aligned with runtime diagnostics before the slice is considered complete

Completion note:

- the recommended cadence was followed in order
- compare-only calibration remained additive throughout the slice
- baseline enforcement behavior remained unchanged while diagnostics and narratives were expanded

## 9. First Recommended Slice

Start with `TC-P1` first.

The highest-value first edit is:

- extract threshold profile configuration from the enforcement seam
- define one active baseline profile plus one or two candidate compare-only profiles
- add tests for profile resolution and segment-aware lookup

That sequence gives the cleanest foundation for compare-only calibration with the lowest regression risk.

Completed result:

- the slice now ends with shared compare-only calibration visible in scanner, publishing/audit, AI report, and Oracle
- the next package can focus on evidence review and baseline-revision decisioning rather than missing plumbing
