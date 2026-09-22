# Horus Analytics II Whale And Trap Enforcement Gates Design

Date: 2026-03-27
Status: Proposed
Authoring mode: Brainstorming-approved design

Based on:

- `docs/superpowers/specs/2026-03-27-whale-trap-shadow-metadata-design.md`
- `docs/superpowers/plans/2026-03-27-whale-trap-shadow-metadata-implementation-plan.md`
- implemented shadow seams and consumers:
  - `core/whale_flow.py`
  - `core/trap_risk.py`
  - `core/DailyScanner.py`
  - `core/ai_report/snapshot.py`
  - `core/ai_report/generation.py`
  - scanner and Oracle/operator-facing shadow diagnostics

## 1. Purpose

This design defines the first enforcement package that will sit on top of the whale-flow and trap-risk shadow layer.

The recommended first enforcement package is intentionally conservative:

- it starts with scanner and recommendation-publishing surfaces
- it does not begin with simulator or live execution gates
- it keeps blocked names visible to operators
- it marks them as blocked-for-execution or downgraded-to-watch instead of silently hiding them

The goal is to turn the existing shadow diagnostics into explicit operator decisions without destroying observability or trust.

## 2. Current Context

The shadow package already gives the system six important things:

1. shared whale/trap metadata seams
2. scanner payload metadata
3. scanner observability counters
4. scanner UI legend and badge explanations
5. AI report and Oracle narrative usage
6. shadow threshold analysis showing how many candidates would be reviewed or blocked

That means the next package does not need to invent new interpretation logic first. It needs to decide where enforcement applies and how it is surfaced.

The recommended answer is:

- enforce first in scanner candidate decisioning and recommendation publishing
- keep rows visible with explicit blocked state
- defer simulator and live execution enforcement to a later package after rollout evidence is reviewed

## 3. Design Goals

The first enforcement package should leave seven things true:

1. Enforcement uses the same whale/trap backend truth already visible in scanner, AI report, and Oracle.
2. The first enforced action is visible-but-blocked, not silent disappearance.
3. Scanner operators can see why a candidate is blocked or downgraded.
4. Recommendation publishing respects the same gates so actionable outputs do not drift from scanner meaning.
5. EGX30 and EGX70 can use different enforcement thresholds through profile-aware rules.
6. Enforcement outcomes are observable and reversible.
7. Simulator and live execution remain out of scope for the first enforcement pass.

## 4. Non-Goals

This package does not attempt to:

- hide blocked names entirely from the scanner
- add live broker execution changes
- add simulator-side position sizing or fill changes
- redesign the whales or traps standalone pages
- add machine-learning-based gate selection

Those can follow later, but the first enforcement release should stay narrow and explainable.

## 5. Recommended Rollout Shape

The recommended rollout is staged:

### Stage 1: Visible-But-Blocked Scanner Enforcement

Scanner candidates remain visible, but blocked names are explicitly labeled as:

- not executable
- downgraded to watch-only
- or blocked from recommendation publishing

### Stage 2: Recommendation Publishing Enforcement

Recommendation outputs, AI daily recommendations, and other downstream “actionable” surfaces should respect the same gate state so they stop promoting blocked names as normal buys.

### Stage 3: Review-Only Threshold Calibration

Thresholds are reviewed against observed scanner distributions and operator outcomes before any simulator or execution-layer enforcement is designed.

### Stage 4: Later Simulator / Live Enforcement Design

Only after the first enforced package proves stable should the next package decide whether the same gates belong in:

- simulator trade allow/block paths
- ranking penalties
- position-size throttles
- live execution protections

## 6. Architectural Recommendation

The recommended architecture is to keep enforcement logic as an additive shared seam rather than embedding it in UI or route code.

Recommended new seam:

- `core/enforcement_gates.py`

This seam should consume existing shadow outputs from:

- `core/whale_flow.py`
- `core/trap_risk.py`
- route or profile context already produced by scanner logic

Primary consumers:

- `core/DailyScanner.py`
- recommendation publishing paths
- `core/ai_report/generation.py` only as a reader of the enforced state, not as an enforcer

This keeps the gate decision centralized and prevents scanner, publishing, and report surfaces from inventing different meanings for the same candidate.

## 7. Enforcement Contract

Every enforced candidate should be able to carry:

- `enforcement_state`
  - `ALLOW`
  - `WATCH_ONLY`
  - `BLOCK_EXECUTION`

- `enforcement_visibility`
  - `VISIBLE`
  - always `VISIBLE` in the first package

- `enforcement_reason`
  - short backend label such as:
    - `severe_trap_risk`
    - `severe_distribution_conflict`
    - `stacked_shadow_threshold`
    - `profile_threshold_breach`

- `enforcement_notes`
  - optional human-readable explanation for scanner and report surfaces

- `enforcement_profile`
  - threshold profile name used to make the decision

The first enforcement package should not introduce a hidden state. If a candidate is blocked, the operator should still be able to see it and understand why.

## 8. First-Release Gate Logic

The first release should stay rule-based and small.

### 8.1 Base Gate Triggers

The recommended first triggers are:

- `BLOCK_EXECUTION` when:
  - `trap_risk_band == SEVERE`
  - or `trap_risk_band == HIGH` and `whale_alignment == CONFLICT`

- `WATCH_ONLY` when:
  - `trap_risk_band == HIGH`
  - or `whale_alignment == CONFLICT`
  - or a profile-specific warning threshold is breached without a full block

- `ALLOW` otherwise

### 8.2 Profile-Aware Thresholds

The first design should support profile-aware thresholds:

- `EGX30`
  - more tolerant of medium trap pressure when liquidity and sector context are healthy

- `EGX70`
  - stricter conflict handling because meme-like or tactical names are more vulnerable to distribution and false breakouts

The thresholds should live in profile configuration, not in scattered call-site conditionals.

### 8.3 Publishing Behavior

The first enforcement package should translate states like this:

- `ALLOW`
  - publish normally as actionable

- `WATCH_ONLY`
  - visible in scanner
  - may appear in report commentary
  - should not be promoted as a normal high-conviction buy

- `BLOCK_EXECUTION`
  - visible in scanner with explicit blocked reason
  - excluded from executable/publishable recommendation sets
  - may still appear in AI report under blocked or cautionary context

## 9. Consumer Behavior

### 9.1 Scanner

Scanner should:

- keep blocked names visible
- display enforcement state and reason
- visually distinguish:
  - actionable
  - watch-only
  - blocked-for-execution

Scanner should not silently drop rows that used to exist.

### 9.2 Recommendation Publishing

Recommendation publishing should:

- exclude `BLOCK_EXECUTION` names from normal actionable outputs
- downgrade `WATCH_ONLY` names to non-actionable commentary or watchlists
- emit audit events for blocked recommendations

This is where enforcement becomes operationally meaningful without yet touching simulator or live execution code.

### 9.3 AI Report

AI report should:

- read enforcement state from backend truth
- distinguish:
  - actionable candidates
  - watch-only candidates
  - blocked candidates
- explain when a technically interesting name is blocked by whale/trap enforcement

AI report should not compute enforcement logic by itself.

## 10. Observability Requirements

No enforcement package should ship without counters.

The first enforced package should add:

- allow count
- watch-only count
- block count
- counts by enforcement reason
- counts by profile
- counts by EGX30 vs EGX70

It should also emit audit metadata so operators can review:

- what was blocked
- why it was blocked
- which threshold profile triggered the decision

## 11. Testing Strategy

### 11.1 Seam-Level Tests

- `core/enforcement_gates.py`
  - severe trap risk -> block
  - high risk + conflict -> block
  - high risk only -> watch-only
  - supportive / low-risk -> allow
  - EGX30 vs EGX70 threshold differences

### 11.2 Integration Tests

- scanner payload includes enforcement state and reason
- blocked candidates remain visible
- publishing excludes blocked candidates
- AI report consumes enforcement state without recomputing logic
- absent whale/trap metadata degrades to safe allow-or-watch defaults, not crashes

### 11.3 Rollout Assertions

The first enforced package must verify that:

- blocked names are still visible to operators
- blocked names are not published as normal actionable recommendations
- recommendation counts change for explainable reasons
- observability counters match emitted scanner/publishing states

## 12. Risks And Controls

### Risk: enforcement hides useful context from operators

Control:

- visible-but-blocked first, not silent removal

### Risk: publishing and scanner drift

Control:

- one shared enforcement seam

### Risk: EGX70 thresholds over-block too aggressively

Control:

- profile-based thresholds plus reason counters before later tightening

### Risk: operators misread watch-only as actionable

Control:

- explicit state vocabulary and scanner/report explanation text

### Risk: enforcement moves too quickly into simulator or live execution

Control:

- keep the first package limited to scanner and recommendation-publishing surfaces

## 13. Success Criteria

The package is successful if:

- blocked names remain visible and explainable in scanner
- actionable recommendation outputs stop promoting blocked names
- AI report reflects enforcement state using shared backend truth
- observability shows exactly how many names were allowed, downgraded, or blocked
- simulator and live execution remain untouched in this first package

## 14. Recommended Next Step

The next artifact after this design should be an implementation plan for the first enforcement package with a staged order such as:

1. `EF-P1` enforcement contract and diagnostics scaffolding
2. `EF-P2` enforcement seam implementation
3. `EF-P3` scanner visibility + blocked-state UI
4. `EF-P4` recommendation publishing integration
5. `EF-P5` AI report and audit closeout

That keeps the first enforcement release narrow, reversible, and operator-visible.
