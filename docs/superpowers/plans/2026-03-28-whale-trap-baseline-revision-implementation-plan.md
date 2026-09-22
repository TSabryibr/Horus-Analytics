# Horus Analytics II Whale And Trap Baseline Revision Implementation Plan

Date: 2026-03-28
Based on:

- `docs/superpowers/specs/2026-03-28-whale-trap-baseline-revision-design.md`
- `docs/superpowers/specs/2026-03-27-whale-trap-threshold-calibration-design.md`
- `docs/superpowers/plans/2026-03-27-whale-trap-threshold-calibration-implementation-plan.md`
- `core/enforcement_profiles.py`
- `core/enforcement_gates.py`
- `core/enforcement_calibration.py`
- `core/DailyScanner.py`
- `routes/scanner.py`
- `routes/signals.py`
- `core/signals/publishing.py`
- `core/ai_report/snapshot.py`
- `core/ai_report/generation.py`
- scanner and Oracle/operator-facing calibration diagnostics already implemented

Track: Whale/Trap Baseline Revision, Candidate Promotion, and Rollback Safety
Status: Completed
Owner model: Single owner

## 1. Goal

This plan turns the approved baseline-revision design into an execution-ready sequence for one owner.

The implementation must leave seven things true:

1. Segment-scoped promoted profiles are resolved through explicit shared configuration rather than scattered consumer edits.
2. Promotion is backed by named evidence and audit metadata.
3. Scanner, publishing, and AI/report surfaces all reflect the same newly active baseline.
4. Compare-only calibration can continue after promotion against the new baseline.
5. Rollback to the prior baseline remains simple and explicit.
6. EGX30 and EGX70 promotion scope can stay global or segment-specific without hidden branching.
7. Simulator and live execution remain untouched in this package.

## 2. In Scope

Primary backend targets:

- `core/enforcement_profiles.py`
- `core/enforcement_gates.py`
- `core/enforcement_calibration.py`
- `core/DailyScanner.py`
- `routes/scanner.py`
- `routes/signals.py`
- `core/signals/publishing.py`
- `core/ai_report/snapshot.py`
- `core/ai_report/generation.py`
- targeted tests for profile promotion, rollback resolution, scanner/runtime verification, publishing/audit verification, and AI/report promotion narrative

Potential frontend/runtime touchpoints:

- scanner-facing diagnostics if active-profile labels need additive clarification
- Oracle/operator-facing surfaces if promotion metadata is surfaced there

Out of scope:

- introducing new candidate profiles
- automatic promotion logic
- simulator trade allow/block logic
- live broker execution changes
- machine-learning-based threshold selection

## 3. Execution Rules

These rules apply to every package in this slice:

1. Promotion must occur through the shared active-profile configuration path only.
2. Promotion targets must become active only through shared configuration, with rollback metadata preserved per affected segment.
3. Rollback profile metadata must exist before the active baseline changes.
4. No consumer may invent its own notion of which profile is active.
5. Compare-only diagnostics must remain available after promotion.
6. No simulator or live execution behavior may be touched in this package.

## 4. Work Package Sequence

Execute this slice in the following order:

1. `BR-P1` Promotion decision contract and audit scaffolding
2. `BR-P2` Active profile configuration revision
3. `BR-P3` Scanner/runtime promotion verification
4. `BR-P4` Publishing and audit promotion verification
5. `BR-P5` AI/Oracle promotion narrative closeout

This order is intentional:

- promotion metadata should exist before the active profile changes
- the shared configuration switch should stabilize before consumer verification wiring
- scanner/runtime should verify the new baseline first
- publishing and AI/report should remain readers of the promoted baseline rather than parallel decision-makers

## 5. Work Packages

### BR-P1. Promotion Decision Contract and Audit Scaffolding

Purpose:

Define the explicit promotion decision metadata before the baseline is changed.

Target files:

- `core/enforcement_profiles.py`
- `routes/signals.py` or closely related audit summary helpers if promotion metadata needs additive exposure
- targeted tests

Tasks:

1. Define promotion decision fields such as:
   - `previous_active_profile`
   - `new_active_profile`
   - `promotion_scope`
   - `promotion_rationale`
   - `promotion_evidence`
   - `rollback_profile`
2. Define safe defaults for baseline-only environments where no promotion has happened yet.
3. Add tests that lock the promotion/rollback contract before config revision lands.

Deliverables:

- explicit promotion decision vocabulary
- rollback-ready metadata contract

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_enforcement_gates.py tests/test_whale_trap_metadata_contract.py -q`

Acceptance criteria:

- promotion metadata is readable, named, and test-backed
- rollback target is explicit before active-profile changes are introduced

### BR-P2. Active Profile Configuration Revision

Purpose:

Promote the selected candidate profiles into the active baseline resolution path.

Target files:

- `core/enforcement_profiles.py`
- `core/enforcement_gates.py`
- targeted seam tests

Tasks:

1. Update active profile resolution to point to the promoted baselines.
2. Preserve the previous active profile as the named rollback profile.
3. Support either:
   - global promotion
   - or segment-specific promotion for `EGX30` / `EGX70`
4. Add tests for:
   - promoted profile becomes active
   - previous profile remains resolvable for rollback
   - segment-specific scope behaves correctly

Deliverables:

- promoted active baselines
- rollback-resolvable configuration

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_enforcement_gates.py tests/test_strategy_and_system.py -q`

Acceptance criteria:

- promoted segment profiles become active through shared configuration
- no consumer-specific branching is required to recognize the new baseline

### BR-P3. Scanner/Runtime Promotion Verification

Purpose:

Verify that scanner/runtime surfaces now reflect the promoted baseline cleanly.

Target files:

- `core/DailyScanner.py`
- `routes/scanner.py`
- scanner-facing frontend/runtime consumers only if active-profile labels need additive clarification
- targeted scanner/runtime tests

Tasks:

1. Verify scanner rows now reflect the promoted baseline state.
2. Keep compare-only calibration diagnostics available against the new baseline.
3. If useful, add additive runtime visibility for:
   - active profile name
   - rollback profile name
4. Add tests for:
   - promoted baseline row states
   - rollback profile metadata presence
   - compare-only diagnostics still present after promotion

Deliverables:

- scanner/runtime aligned to the promoted baseline
- continued compare-only visibility after promotion

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner`

Acceptance criteria:

- scanner reflects the promoted active profile consistently
- calibration summaries still remain additive and compare-only

### BR-P4. Publishing and Audit Promotion Verification

Purpose:

Ensure publishing behavior and audit summaries reflect the promoted baseline without ambiguity.

Target files:

- `routes/signals.py`
- `core/signals/publishing.py`
- targeted publishing and audit tests

Tasks:

1. Verify publish filtering now follows the promoted baseline.
2. Add or expose audit metadata for:
   - previous active profile
   - new active profile
   - rollback profile
   - promotion rationale/evidence
3. Add tests for:
   - publish outcomes change only because the active baseline changed
   - audit summaries explain the promotion
   - rollback metadata remains visible

Deliverables:

- publishing aligned to the promoted baseline
- auditable before/after promotion trail

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_signals_coverage.py tests/test_signals_publish_service.py tests/test_signals_p0.py -q`

Acceptance criteria:

- publishing uses the promoted baseline consistently
- audit summaries can reconstruct the promotion decision and rollback path

### BR-P5. AI/Oracle Promotion Narrative Closeout

Purpose:

Teach AI/report and Oracle surfaces to describe the promoted baseline cleanly without blurring it with compare-only diagnostics.

Target files:

- `core/ai_report/snapshot.py`
- `core/ai_report/generation.py`
- operator-facing Oracle/report consumers if additive promotion wording is surfaced
- targeted tests

Tasks:

1. Thread active-profile promotion metadata into AI snapshot/report payloads if needed.
2. Ensure AI/report wording distinguishes:
   - active promoted baseline
   - remaining compare-only candidate profiles
   - rollback availability
3. Add tests for:
   - promoted active-profile wording
   - compare-only wording remains separate
   - graceful degradation when promotion metadata is absent

Deliverables:

- AI/report promotion narrative aligned with the new baseline
- operator-facing wording that remains explicit and reversible

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_ai_daily_report.py tests/test_ai_report_generation_service.py tests/test_api_endpoints.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/oracle`

Acceptance criteria:

- AI/report surfaces describe the promoted baseline without inventing new logic
- compare-only and active-profile meanings remain distinct

## 6. Verification Matrix

Each work package must declare:

1. protected behavior
2. tests added or updated
3. scanner, publishing, or AI/report surfaces affected
4. promotion/rollback metadata added
5. rollout mode: promoted baseline active, rollback ready, compare-only diagnostics still additive

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

- scanner row states reflect the promoted baseline
- compare-only diagnostics still appear against the new baseline
- publishing behavior matches the promoted baseline only
- audit summaries explain previous profile, new profile, and rollback target
- AI/report wording does not confuse active promotion with compare-only calibration

## 7. Implementation Outcome

The completed slice landed in five packages:

1. `BR-P1` promotion decision contract and rollback defaults
2. `BR-P2` active baseline promotion for:
   - `EGX30_GUARDED`
   - `EGX70_HARDENED`
3. `BR-P3` scanner/runtime promotion verification and rollback visibility
4. `BR-P4` publishing/audit promotion metadata and verification
5. `BR-P5` AI/Oracle promotion narrative and rollback-aware wording

Named rollback targets remain:

- `EGX30_BALANCED`
- `EGX70_STRICT`

Full release-quality verification passed:

- backend:
  - `203 passed, 27 skipped`
- frontend scanner:
  - `7 suites passed, 20 tests passed`
- frontend oracle:
  - `7 suites passed, 24 tests passed`
- frontend build:
  - passed

## 8. Risks and Controls

### Risk: promotion changes more than one active profile target at once

Control:

- keep the first promotion slice limited to one named target and one rollback profile

### Risk: rollback path is incomplete during a bad promotion

Control:

- require rollback metadata and profile resolution tests before promotion lands

### Risk: scanner, publishing, and AI/report drift after promotion

Control:

- keep active-profile resolution centralized in shared configuration and verify all three surfaces explicitly

### Risk: remaining compare-only diagnostics become misleading after promotion

Control:

- continue running calibration against the new baseline and keep labels explicit

### Risk: the package drifts into simulator/live execution changes

Control:

- keep simulator and live execution explicitly out of scope for this plan

## 9. Suggested Execution Cadence

For a single owner, the recommended order is:

1. finish `BR-P1` and `BR-P2` first so the promotion contract and config switch stabilize before consumer verification
2. land `BR-P3` before publishing and AI/report follow-through so runtime truth is visible first
3. land `BR-P4` once publishing and audit can verify the baseline switch cleanly
4. close with `BR-P5` so operator-facing narrative stays aligned with the promoted baseline and remaining compare-only diagnostics

## 10. First Recommended Slice

Start with `BR-P1` first.

The highest-value first edit is:

- define the promotion decision and rollback metadata
- name the specific candidate profile to be promoted
- add tests that lock previous/new active profile resolution before the baseline is switched

That sequence gives the cleanest path to a reversible baseline promotion with the lowest regression risk.
