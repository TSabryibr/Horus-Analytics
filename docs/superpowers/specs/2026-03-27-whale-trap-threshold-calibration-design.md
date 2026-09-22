# Horus Analytics II Whale And Trap Threshold Calibration Design

Date: 2026-03-27
Status: Implemented
Authoring mode: Brainstorming-approved design

Based on:

- `docs/superpowers/specs/2026-03-27-whale-trap-shadow-metadata-design.md`
- `docs/superpowers/specs/2026-03-27-whale-trap-enforcement-gates-design.md`
- `docs/superpowers/plans/2026-03-27-whale-trap-enforcement-gates-implementation-plan.md`
- implemented enforcement consumers:
  - `core/enforcement_gates.py`
  - `core/DailyScanner.py`
  - `core/signals/publishing.py`
  - `core/ai_report/snapshot.py`
  - `core/ai_report/generation.py`
  - scanner and Oracle/operator-facing diagnostics

## 1. Purpose

This design defines the next package after first-release whale/trap enforcement: threshold calibration and post-rollout tuning.

The purpose of this package is not to add stronger enforcement. It is to make the current enforcement package measurable, comparable, and adjustable without guesswork.

The core job is to answer:

- are current thresholds too loose or too strict
- where do EGX30 and EGX70 differ in practice
- which reasons dominate watch-only and blocked states
- which threshold changes would improve selectivity without destroying operator trust

This package should create a disciplined path for tuning the enforcement rules before any simulator or live execution package is considered.

## 2. Current Context

The system now has three layers already in place:

1. shadow whale/trap metadata
2. visible-but-blocked enforcement
3. scanner, publishing, and AI report consumption of the same enforcement truth

That means the next package does not need to invent new whale/trap logic. It needs to calibrate the thresholds that already drive:

- `ALLOW`
- `WATCH_ONLY`
- `BLOCK_EXECUTION`

The current rule set is intentionally conservative and explainable, but it is still an initial release. It should now be evaluated against real scanner distributions and operator review patterns before the thresholds are tightened, loosened, or expanded.

## 3. Design Goals

The threshold-calibration package should leave seven things true:

1. Threshold changes are driven by shared observability rather than ad hoc intuition.
2. Calibration compares candidate threshold profiles against the current baseline without silently changing live behavior first.
3. EGX30 and EGX70 can be tuned independently through explicit profile configuration.
4. Operators can see what changed, why it changed, and how the candidate profile differs from the current one.
5. Calibration remains deterministic and rule-based; no opaque optimization loop is introduced.
6. The package stays reversible so the current baseline can remain active while alternatives are evaluated.
7. Simulator and live execution enforcement still remain out of scope.

## 4. Non-Goals

This package does not attempt to:

- auto-tune thresholds intraday
- add machine-learning-based threshold search
- redesign scanner or Oracle UI surfaces
- move enforcement into simulator or live broker paths
- change position sizing rules
- replace the shared enforcement seam

Those may become future packages, but they should not be mixed into the first calibration slice.

## 5. Architectural Recommendation

The recommended approach is to add one new shared calibration seam and one clear threshold configuration source.

Recommended additions:

1. `core/enforcement_calibration.py`
2. threshold-profile configuration kept near the enforcement seam, such as:
   - `core/enforcement_profiles.py`
   - or a closely related configuration module under `core/`

Responsibilities should split like this:

- `core/enforcement_gates.py`
  - applies the currently selected active threshold profile

- `core/enforcement_calibration.py`
  - evaluates one or more candidate profiles against the same candidate set in compare-only mode
  - reports how candidate profiles differ from the active baseline

- threshold profile configuration
  - stores the explicit rule settings for:
    - baseline profile
    - candidate calibration profiles

This keeps enforcement execution and calibration analysis separate while preserving one shared vocabulary.

## 6. Calibration Contract

The calibration package should introduce a compare-only contract that can be attached to diagnostics, audit summaries, and optional operator-facing review surfaces.

Suggested fields:

- `active_enforcement_profile`
  - the currently enforced profile name

- `candidate_calibration_profiles`
  - list of compare-only profile names evaluated against the same candidates

- `calibration_summary`
  - aggregate comparison object containing:
    - baseline counts
    - candidate counts
    - deltas

- `calibration_deltas`
  - structured output such as:
    - `allow_delta`
    - `watch_only_delta`
    - `block_delta`
    - `reason_deltas`

- `top_delta_reasons`
  - reasons whose counts changed most under the candidate profile

- `top_reclassified_names`
  - optional list of symbols whose state changed between baseline and candidate profile

The calibration contract should remain additive. It should not overwrite the actual enforced state in the first release.

## 7. Threshold Profile Model

The calibration package should make threshold tuning explicit instead of embedding it in scattered conditionals.

Each profile should be able to express rules such as:

- trap band that causes automatic block
- trap band plus whale conflict combinations that cause block
- conflict-only cases that produce watch-only
- profile-specific escalation rules for:
  - `EGX30`
  - `EGX70`

The first calibration package should support:

- one active baseline profile
- one or two candidate profiles in compare-only mode

That keeps the comparison understandable and avoids creating a large profile matrix too early.

## 8. Calibration Workflow

The recommended workflow is staged:

### Stage 1: Baseline Measurement

Collect stable baseline distributions from the current enforced profile:

- allow/watch/block counts
- counts by reason
- counts by market segment
- counts by profile

### Stage 2: Candidate Compare-Only Runs

Evaluate one or more candidate profiles against the same scanner candidates without changing actual enforcement behavior.

This should answer:

- how many additional names would move from allow to watch-only
- how many watch-only names would become blocked
- whether EGX70 remains materially stricter than EGX30
- which reasons dominate the reclassifications

### Stage 3: Operator Review

Surface compact calibration summaries so operators can review whether the candidate profile looks healthier or too aggressive.

### Stage 4: Controlled Profile Revision

Only after compare-only evidence looks sound should a later package promote a candidate profile to the new baseline.

## 9. Consumer Behavior

### 9.1 Scanner and Runtime Diagnostics

Scanner-facing diagnostics should be able to show:

- current enforced baseline counts
- candidate compare-only counts
- delta summaries

The scanner should not replace the current row state with candidate row states in this package. Candidate results should remain diagnostic only.

### 9.2 Publishing and Audit

Publishing should continue to follow the active baseline profile only.

Audit summaries should be able to record:

- baseline profile used
- candidate profile compared
- state deltas
- dominant reason deltas

### 9.3 AI Report and Oracle

AI/report surfaces should summarize calibration drift at a compact level, but they should not become the primary calibration workspace.

If surfaced, the message should stay descriptive, for example:

- current profile blocked 3 names
- candidate profile would block 5 names
- most additional blocks came from `distribution_conflict`

## 10. Observability Requirements

This package should not ship without compare-only observability.

Required counters:

- baseline allow/watch/block counts
- candidate allow/watch/block counts
- allow/watch/block deltas
- counts by reason delta
- counts by market segment delta
- counts by profile delta

Required review outputs:

- top reclassified names
- top reasons driving reclassification
- baseline versus candidate summaries per EGX30 and EGX70

## 11. Testing Strategy

### 11.1 Seam-Level Tests

- `core/enforcement_calibration.py`
  - baseline versus candidate comparison
  - delta computation
  - top reclassified names
  - top reason deltas

- threshold profile configuration
  - profile parsing and normalization
  - EGX30 and EGX70 profile resolution

### 11.2 Integration Tests

- scanner/runtime diagnostics include calibration compare-only summaries
- publishing audit can expose baseline versus candidate metadata without changing live output
- AI report consumes calibration summaries without recomputing enforcement logic
- absent candidate profiles degrade cleanly to baseline-only behavior

### 11.3 Safety Assertions

The first calibration release must verify that:

- candidate profiles do not change the actual enforced state
- publishing still follows the active baseline profile only
- scanner visibility remains stable even when compare-only results differ

## 12. Risks And Controls

### Risk: calibration gets confused with enforcement

Control:

- keep candidate results compare-only and additive in the first release

### Risk: too many candidate profiles create noise

Control:

- limit the first release to one baseline plus one or two candidate profiles

### Risk: operators misread compare-only deltas as active behavior

Control:

- label candidate outputs explicitly as compare-only

### Risk: threshold tuning drifts into manual guesswork

Control:

- require delta summaries and reason-level evidence before baseline changes

### Risk: calibration starts changing simulator or live behavior indirectly

Control:

- keep simulator and live execution out of scope in this package

## 13. Success Criteria

This package is successful if:

- the team can compare current and candidate threshold profiles using shared backend truth
- EGX30 and EGX70 threshold behavior can be reviewed independently
- top reclassifications and top reason deltas are visible
- candidate profiles do not silently change live enforcement behavior
- a later baseline-revision decision can be made with evidence instead of guesswork

## 14. Recommended Next Step

The calibration implementation plan for this design has been completed and the first compare-only calibration slice is now landed.

The recommended next step after this implemented slice is:

1. review live compare-only calibration evidence from scanner, publishing/audit, and AI/Oracle surfaces
2. decide whether a candidate profile is strong enough to promote to the next baseline
3. if promotion is justified, write a narrow baseline-revision package rather than folding that decision into the calibration slice itself

That preserves the original goal of keeping threshold tuning observable, reversible, and operationally safe before any active threshold promotion.
