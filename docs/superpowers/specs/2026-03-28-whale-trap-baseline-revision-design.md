# Horus Analytics II Whale And Trap Baseline Revision Design

Date: 2026-03-28
Status: Implemented
Authoring mode: Brainstorming-approved design

Based on:

- `docs/superpowers/specs/2026-03-27-whale-trap-enforcement-gates-design.md`
- `docs/superpowers/specs/2026-03-27-whale-trap-threshold-calibration-design.md`
- `docs/superpowers/plans/2026-03-27-whale-trap-threshold-calibration-implementation-plan.md`
- implemented compare-only calibration consumers:
  - `core/enforcement_profiles.py`
  - `core/enforcement_calibration.py`
  - `core/enforcement_gates.py`
  - `core/DailyScanner.py`
  - `core/signals/publishing.py`
  - `core/ai_report/snapshot.py`
  - `core/ai_report/generation.py`
  - scanner and Oracle/operator-facing calibration diagnostics

## 1. Purpose

This design defines the package that followed the compare-only calibration slice: controlled promotion of segment-specific candidate calibration profiles into the new active enforcement baseline.

The purpose of this package is not to add new whale/trap logic. It is to make one explicit decision:

- should specific segment-scoped candidate profiles replace the current active baselines

The package should only exist once compare-only calibration evidence is already visible and reviewable across scanner, publishing/audit, and AI/Oracle surfaces.

Implemented outcome:

- `EGX30_GUARDED` became the active `EGX30` baseline
- `EGX70_HARDENED` became the active `EGX70` baseline
- rollback remained explicit to:
  - `EGX30_BALANCED`
  - `EGX70_STRICT`

## 2. Current Context

The system now has four layers in place:

1. shared whale/trap metadata
2. visible-but-blocked enforcement
3. compare-only calibration profiles
4. scanner, publishing, audit, and AI/Oracle calibration summaries

That means the package did not need to invent a new comparison mechanism. It only needed to decide whether the already-observed segment candidates were strong enough to become active.

The key boundary is:

- calibration remains compare-only until this package explicitly promotes one candidate
- promotion should be narrow, reversible, and easy to audit

## 3. Design Goals

The baseline-revision package should leave seven things true:

1. Candidate profiles are promoted through explicit backend configuration decisions.
2. Promotion is justified by documented evidence, not an ad hoc toggle.
3. Operators can still understand which profile is active and why it was promoted.
4. Scanner, publishing, and AI/Oracle continue consuming one shared enforcement truth after promotion.
5. Rollback to the previous baseline remains simple and fast.
6. EGX30 and EGX70 can be revised independently if evidence supports asymmetric promotion.
7. Simulator and live broker execution still remain out of scope.

## 4. Non-Goals

This package does not attempt to:

- introduce additional candidate profiles
- redesign calibration diagnostics
- auto-promote profiles based on thresholds
- add simulator-side enforcement
- add live broker execution controls
- mix baseline promotion with new threshold-search logic

Those should remain separate from the first baseline-revision slice.

## 5. Promotion Preconditions

No baseline revision should start unless four things are already true:

1. compare-only calibration has run long enough to produce stable evidence
2. operator-facing diagnostics show the same candidate drift consistently
3. publishing/audit summaries confirm the candidate profile would change behavior for understandable reasons
4. there is a named rollback target for the current baseline

If those conditions are not met, the system should remain in compare-only mode.

## 6. Promotion Decision Contract

The package should treat promotion as an explicit decision artifact, not an implicit config edit.

Suggested promotion metadata:

- `previous_active_profile`
- `new_active_profile`
- `promotion_scope`
  - `GLOBAL`
  - or segment-scoped such as:
    - `EGX30`
    - `EGX70`
- `promotion_rationale`
  - short decision label such as:
    - `reduced_false_actionables`
    - `improved_conflict_handling`
    - `operator_review_confirmed`
- `promotion_evidence`
  - compact counts/deltas that justified the switch
- `rollback_profile`
  - previous active profile name

This metadata should be visible in audit/review surfaces so later operators can understand why the baseline changed.

## 7. Recommended Rollout Shape

The recommended rollout is staged:

### Stage 1: Evidence Freeze

Freeze the candidates under consideration:

- named candidate profiles per segment
- one documented evidence snapshot
- one rollback target per promoted segment

No additional candidate churn should be mixed into the same promotion package.

### Stage 2: Config Promotion

Promote the selected candidate by changing the active baseline profile resolution path in shared configuration.

This should happen in one place only:

- `core/enforcement_profiles.py`

### Stage 3: Post-Promotion Verification

Verify that:

- scanner row states now match the promoted baseline
- publishing behavior follows the promoted baseline
- AI/Oracle enforcement and calibration narratives remain internally consistent

### Stage 4: Rollback Readiness

Keep the previous baseline available as the immediate rollback profile until enough live evidence confirms the new baseline is stable.

## 8. Architectural Recommendation

The promotion package should stay small and config-centered.

Primary seams:

- `core/enforcement_profiles.py`
  - source of truth for active baseline resolution
- `core/enforcement_gates.py`
  - unchanged consumer of whichever profile is active
- `core/enforcement_calibration.py`
  - still used for compare-only diagnostics after promotion, but against the new baseline

This package should prefer changing the active profile mapping rather than rewriting rule logic in `core/enforcement_gates.py`.

## 9. Consumer Behavior After Promotion

### 9.1 Scanner

Scanner should:

- show row states from the newly active baseline
- continue exposing compare-only diagnostics for any remaining candidate profile
- surface the active profile name clearly in diagnostics if needed

### 9.2 Publishing and Audit

Publishing should:

- follow the promoted active baseline immediately
- emit audit summaries that show the new active profile
- retain enough metadata to reconstruct the before/after promotion change

### 9.3 AI Report and Oracle

AI/Oracle should:

- describe enforcement using the promoted baseline
- keep compare-only language for any remaining non-active candidate profile
- avoid implying that multiple profiles are active at once

## 10. Observability Requirements

No promotion package should ship without explicit before/after tracking.

Required outputs:

- previous active profile
- new active profile
- before/after allow/watch/block counts
- before/after top reasons
- counts by segment after promotion
- rollback profile metadata

Required audit review:

- which profile was promoted
- why it was promoted
- what changed operationally
- how to roll back if needed

## 11. Testing Strategy

### 11.1 Config and Seam Tests

- active profile resolution reflects the promoted baseline
- previous rollback profile remains resolvable
- EGX30 and EGX70 promotion scope behaves as configured

### 11.2 Integration Tests

- scanner reflects the promoted active profile
- publishing output changes only because the active profile changed
- AI report reads the promoted profile without additional logic drift
- compare-only summaries still work after baseline promotion

### 11.3 Rollout Assertions

The package must verify that:

- exactly one promotion target became active
- rollback can restore the prior baseline cleanly
- operator-facing diagnostics do not present mixed active-profile meanings

## 12. Risks And Controls

### Risk: a candidate is promoted too early

Control:

- require a documented evidence snapshot before promotion

### Risk: promotion and calibration narratives drift apart

Control:

- keep active-profile resolution centralized in shared configuration

### Risk: rollback is unclear during a bad promotion

Control:

- store `previous_active_profile` and `rollback_profile` explicitly

### Risk: segment-specific promotion causes confusion

Control:

- declare promotion scope explicitly as `GLOBAL`, `EGX30`, or `EGX70`

### Risk: the package expands into simulator/live execution changes

Control:

- keep simulator and live execution explicitly out of scope

## 13. Success Criteria

This package is successful if:

- the selected segment candidates are promoted through a clear shared-config change
- scanner, publishing, and AI/Oracle all reflect the new baseline consistently
- audit metadata explains the promotion and rollback path
- compare-only calibration can continue against the promoted baseline
- the system remains reversible if the new baseline underperforms

## 14. Recommended Next Step

This design is now implemented. The next artifact after this baseline-revision slice should focus on post-promotion review, such as:

1. post-promotion evidence review
2. rollback readiness validation
3. follow-on threshold tuning only if the promoted baselines underperform

That keeps baseline promotion explicit, reversible, and operationally understandable.
