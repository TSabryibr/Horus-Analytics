# Horus Analytics II Whale And Trap Shadow Metadata Design

Date: 2026-03-27
Status: Proposed
Authoring mode: Brainstorming-approved design

## 1. Purpose

This design introduces a shared whale-flow and trap-risk metadata layer for Horus Analytics II.

The first release is intentionally shadow-only. It does not block scanner candidates, reject trades, or override live behavior. Its job is to compute one reusable interpretation of:

- smart-money accumulation or distribution
- trap-risk context around breakout candidates
- supportive versus conflicted market-structure conditions

That shared interpretation should then feed three surfaces in the same slice:

1. scanner candidate metadata
2. AI report snapshot and narrative generation
3. dashboard summary surfaces

The core goal is to stop treating whales, traps, scanner decisions, and AI commentary as loosely-related parallel concepts. They should share one backend truth path.

## 2. Current Context

The codebase already contains useful whale and trap inputs, but they are not yet integrated into the new EGX microstructure layer:

- scanner candidates now carry placeholder fields such as `Trap_Risk`, `Expected_Slippage_Pct`, and execution metadata
- AI report snapshot generation already collects whale and trap data from the existing engines
- AI report generation already scores market direction using broad whale and trap counts
- dashboard and market contexts already consume whale and trap payloads independently
- frontend routes for whales and traps already exist as separate product surfaces

The missing piece is a shared seam that computes whale/trap meaning once and reuses that output across scanner, report, and dashboard consumers.

## 3. Design Goals

The first whale/trap metadata slice should leave five things true:

1. Whale alignment and trap-risk are computed in shared backend seams rather than duplicated in scanner, AI report, and dashboard logic.
2. The first release is metadata-only and does not hard-veto or re-rank candidates.
3. Scanner payloads, AI snapshots, and dashboard summaries can all explain supportive versus conflicted smart-money context using the same field vocabulary.
4. Missing whale or trap data degrades gracefully without breaking scanner or report generation.
5. The slice creates observability that can support a later enforcement package.

## 4. Non-Goals

This slice does not attempt to:

- add hard blocking to scanner candidates
- change portfolio sizing or order execution rules
- redesign the existing whales or traps frontend pages
- add machine-learning-based classification
- build a new order-flow engine or intraday tape reader

Those are valid future packages, but they should not be mixed into the first shadow-only integration.

## 5. Architectural Recommendation

The recommended approach is to add two new shared seams:

1. `core/whale_flow.py`
2. `core/trap_risk.py`

These seams should be consumed by:

- `core/DailyScanner.py`
- `core/ai_report/snapshot.py`
- `core/ai_report/generation.py`
- dashboard-facing data shaping paths where scanner or summary payloads are surfaced

This is preferred over patching each consumer separately because:

- it avoids semantic drift between scanner and AI report commentary
- it makes the new fields testable in isolation
- it aligns with the new EGX microstructure seam pattern already introduced
- it creates a clean foundation for a future enforcement package

## 6. Core Seams

### 6.1 `core/whale_flow.py`

This module should normalize whale inputs into scanner-ready metadata.

Responsibilities:

- determine the whale state for a candidate
- normalize whale strength into a compact score
- classify whether whale flow supports or conflicts with the candidate
- emit concise explanation labels

Outputs should include:

- `whale_signal`
- `whale_strength`
- `whale_alignment`
- `whale_reason`

It should tolerate absent whale data and return neutral defaults rather than failing consumers.

### 6.2 `core/trap_risk.py`

This module should compute a shadow-only trap-risk interpretation for a candidate.

Responsibilities:

- combine breakout-quality weakness, sector weakness, liquidity weakness, trap context, and whale conflict
- generate a numeric trap-risk score
- assign a simple severity band
- emit a primary reason label plus optional component detail

Outputs should include:

- `trap_risk_score`
- `trap_risk_band`
- `trap_risk_reason`
- optional `trap_risk_components`

This module should remain deterministic and explainable. The first version should use simple weighted rules, not opaque heuristics.

## 7. Shared Metadata Contract

### 7.1 Whale Metadata

Every candidate or summarized recommendation should be able to carry:

- `whale_signal`
  - `ACCUMULATION`
  - `DISTRIBUTION`
  - `NEUTRAL`
  - `UNKNOWN`

- `whale_strength`
  - normalized numeric score in a compact range such as `0.0` to `1.0`

- `whale_alignment`
  - `SUPPORTIVE`
  - `CONFLICT`
  - `NEUTRAL`

- `whale_reason`
  - short backend reason label such as:
    - `accumulation_support`
    - `distribution_conflict`
    - `no_whale_signal`

### 7.2 Trap-Risk Metadata

Every candidate or summarized recommendation should be able to carry:

- `trap_risk_score`
  - shadow-only numeric score, recommended range `0` to `100`

- `trap_risk_band`
  - `LOW`
  - `MEDIUM`
  - `HIGH`
  - `SEVERE`

- `trap_risk_reason`
  - short primary reason label such as:
    - `bull_trap_pressure`
    - `weak_sector_breakout`
    - `distribution_against_breakout`
    - `illiquid_breakout`
    - `low_risk_alignment`

- `trap_risk_components`
  - optional structured component detail for debugging and AI explanation

## 8. First-Release Scoring Contract

### 8.1 Whale Alignment

The first release should keep whale alignment simple:

- long candidate + `ACCUMULATION` -> `SUPPORTIVE`
- long candidate + `DISTRIBUTION` -> `CONFLICT`
- missing or mixed signal -> `NEUTRAL`

If the current whale engine already emits strength, intent, or confidence-like fields, this module should normalize those rather than inventing frontend-only heuristics.

### 8.2 Trap-Risk Composition

The first release should increase trap risk when any of the following are present:

- weak liquidity tier
- marginal sector RS
- weak breakout-quality context
- whale distribution conflict
- elevated bull-trap context

The first release should decrease trap risk when:

- whale accumulation supports the setup
- sector RS is clearly positive
- validation quality is strong
- liquidity is healthy

The first release should remain additive and interpretable. A small number of weighted rules is preferred over a broad feature soup.

## 9. Consumer Integration

### 9.1 Scanner

`core/DailyScanner.py` should attach the new fields directly to candidate payloads.

The scanner should:

- compute whale/trap metadata after the raw signal exists
- expose the new fields without blocking the candidate
- preserve existing metadata from the EGX microstructure slice
- make the new fields visible to later scanner UI consumers

### 9.2 AI Report Snapshot

`core/ai_report/snapshot.py` should aggregate the new scanner-level metadata into reusable summary structures.

The snapshot should include:

- counts of supportive whale alignments
- counts of whale conflicts
- counts of high and severe trap-risk candidates
- top supportive names
- top conflicted or high-risk names

This creates one clean source for narrative generation without duplicating calculation logic inside the report layer.

### 9.3 AI Report Generation

`core/ai_report/generation.py` should use the new fields in three places:

1. market-direction reasoning
2. candidate-specific commentary
3. risk-warning sections

The report should explicitly call out cases such as:

- technical breakout with whale accumulation support
- technical breakout with whale distribution conflict
- technically valid scanner candidate carrying high trap-risk

### 9.4 Dashboard Summary

Dashboard-facing data shaping should expose compact summaries such as:

- supportive whale-aligned candidates count
- high or severe trap-risk candidates count
- strongest supportive names
- strongest conflict names

The dashboard should summarize the state; it should not recalculate whale/trap logic on its own.

## 10. Rollout Strategy

The rollout should be staged:

### Stage 1: Compute Only

Add whale/trap metadata to scanner, AI snapshot, and dashboard-facing summaries without enforcement.

### Stage 2: Observability

Add counters for:

- supportive whale alignments
- whale conflicts
- high and severe trap-risk counts
- top trap-risk reasons

This is required before any future enforcement package.

### Stage 3: Narrative Adoption

Use the new fields inside AI report and dashboard summaries so operators can see whether the metadata is actually informative.

### Stage 4: Later Enforcement Package

Only after the shadow distribution is understood should a later package consider:

- hard vetoes
- ranking penalties
- position-size throttles

## 11. Testing Strategy

Testing should follow the seam boundaries.

### 11.1 Seam-Level Tests

- `core/whale_flow.py`
  - signal normalization
  - alignment mapping
  - missing-data fallback

- `core/trap_risk.py`
  - score calculation
  - severity banding
  - component-driven increases and decreases

### 11.2 Integration Tests

- scanner payload contains whale/trap metadata
- AI snapshot includes aggregate whale/trap summaries
- AI report generation consumes those fields without crashing
- dashboard-facing consumers render or shape the new fields cleanly
- absent whale or trap data degrades to safe defaults

### 11.3 Shadow-Mode Assertions

The first release must verify that:

- no candidate disappears solely because of the new metadata
- report generation still succeeds when whale/trap data is absent
- dashboard summary generation remains stable under partial payloads

## 12. Success Criteria

The slice is successful if:

- scanner candidates can explain supportive versus conflicted smart-money context
- AI report can cite whale/trap metadata using shared backend truth
- dashboard can summarize whale/trap state compactly
- no enforcement occurs in this slice
- observability exists for a later enforcement package

## 13. Recommended Implementation Sequence

The safest order is:

1. `core/whale_flow.py`
2. `core/trap_risk.py`
3. scanner metadata integration
4. AI snapshot integration
5. AI report narrative integration
6. dashboard summary integration
7. testing and diagnostics closeout

This keeps the shared logic first and the consumers second.

## 14. Follow-On Package

After this slice proves useful in shadow mode, the next package should decide whether and where to enforce the metadata through:

- hard vetoes for severe conflict conditions
- score/ranking penalties
- position-size throttles
- portfolio-level conflict or crowding rules

Those enforcement decisions should remain a separate package rather than being folded into the first shadow-only release.
