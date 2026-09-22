# Horus Analytics II Whale And Trap Shadow Metadata Implementation Plan

Date: 2026-03-27
Based on:

- `docs/superpowers/specs/2026-03-27-whale-trap-shadow-metadata-design.md`
- `core/DailyScanner.py`
- `core/ai_report/snapshot.py`
- `core/ai_report/generation.py`
- existing whale and trap collection paths already consumed by report and dashboard surfaces

Track: Whale Flow, Trap-Risk, and Shared Narrative Metadata
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved whale/trap shadow-metadata design into an execution-ready sequence for one owner.

The implementation must leave six things true:

1. Whale-flow and trap-risk meaning are computed in shared backend seams rather than duplicated across scanner, AI report, and dashboard paths.
2. The first slice is metadata-only and does not block, veto, or re-rank candidates.
3. Scanner payloads can explain supportive versus conflicted whale context and trap-risk severity.
4. AI snapshot and report generation consume the same shared metadata rather than re-inventing their own heuristics.
5. Dashboard-facing summaries can expose whale/trap state compactly without recalculating backend logic in the frontend.
6. Missing whale or trap data degrades safely without breaking scanner, reports, or dashboard summaries.

## 2. In Scope

Primary backend targets:

- new shared seams under `core/`:
  - `core/whale_flow.py`
  - `core/trap_risk.py`
- `core/DailyScanner.py`
- `core/ai_report/snapshot.py`
- `core/ai_report/generation.py`
- targeted tests for scanner metadata, AI snapshot aggregation, and report generation

Potential frontend/runtime touchpoints:

- dashboard-facing data shaping or summary surfaces if the new metadata needs to be shown directly
- scanner-facing frontend consumers if additive fields are surfaced in existing result tables or summary cards

Out of scope:

- hard blocking or score penalties in scanner
- execution-model changes
- portfolio sizing changes
- redesign of the standalone whales or traps pages
- intraday order-flow modeling

## 3. Execution Rules

These rules apply to every package in this slice:

1. No enforcement logic in this package; whale/trap outputs remain shadow-only metadata.
2. No whale/trap interpretation may live only inside the AI report or dashboard consumer; shared logic must live in reusable seams.
3. No frontend-only heuristic recreation of whale/trap meaning; the frontend may format but not reinterpret.
4. No scanner candidate may disappear solely because of the new metadata in this slice.
5. Prefer deterministic, explainable weighted rules over opaque composite heuristics.
6. Prefer vectorized or batch-friendly data shaping where the scanner path touches universe-scale data.

## 4. Work Package Sequence

Execute this slice in the following order:

1. `WT-P1` Shared metadata contract and diagnostics scaffolding
2. `WT-P2` Whale-flow seam
3. `WT-P3` Trap-risk seam
4. `WT-P4` Scanner metadata integration
5. `WT-P5` AI snapshot integration
6. `WT-P6` AI report narrative integration
7. `WT-P7` Dashboard summary integration and closeout

This order is intentional:

- shared vocabulary should exist before consumers depend on it
- whale and trap seams should stabilize before scanner wiring
- scanner integration should land before AI layers aggregate or narrate the metadata
- dashboard summary should consume already-stable payloads rather than inventing a parallel path

## 5. Work Packages

### WT-P1. Shared Metadata Contract and Diagnostics Scaffolding

Purpose:

Define the shared whale/trap vocabulary and observability counters before deeper logic lands.

Target files:

- `core/whale_flow.py`
- `core/trap_risk.py`
- targeted tests

Tasks:

1. Define shared whale metadata fields:
   - `whale_signal`
   - `whale_strength`
   - `whale_alignment`
   - `whale_reason`
2. Define shared trap metadata fields:
   - `trap_risk_score`
   - `trap_risk_band`
   - `trap_risk_reason`
   - optional `trap_risk_components`
3. Define zeroed or neutral shadow defaults that scanner, AI snapshot, and dashboard summaries can reuse.
4. Add basic observability counters for:
   - supportive whale alignments
   - whale conflicts
   - high trap-risk count
   - severe trap-risk count
   - top trap-risk reasons
5. Add tests that lock the payload shape before scoring logic is added.

Deliverables:

- shared whale/trap metadata vocabulary
- shadow-safe defaults
- diagnostics contract

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py tests/test_api_endpoints.py -q`

Acceptance criteria:

- all later packages can emit and consume one whale/trap vocabulary
- missing data has explicit neutral defaults rather than ad hoc per-consumer fallbacks

### WT-P2. Whale-Flow Seam

Purpose:

Normalize existing whale data into scanner-ready candidate metadata.

Target files:

- `core/whale_flow.py`
- targeted seam tests

Tasks:

1. Add a helper that maps existing whale engine output into:
   - signal state
   - normalized strength
   - candidate alignment
   - explanation reason
2. Keep the first release long-only and shadow-only.
3. Make absent whale data resolve to neutral output rather than failure.
4. Add direct tests for:
   - accumulation support
   - distribution conflict
   - neutral fallback
   - missing-data fallback

Deliverables:

- reusable whale-flow seam
- test-backed alignment mapping

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_strategy_and_system.py tests/test_api_endpoints.py -q`

Acceptance criteria:

- whale meaning is computed once in a reusable seam
- consumers do not need to reverse-engineer whale interpretation

### WT-P3. Trap-Risk Seam

Purpose:

Compute a shadow-only trap-risk score and severity band using scanner and market-structure context.

Target files:

- `core/trap_risk.py`
- targeted seam tests

Tasks:

1. Define the first-release weighted inputs:
   - liquidity weakness
   - sector weakness
   - breakout-quality weakness
   - whale conflict
   - bull-trap context
2. Implement:
   - numeric score
   - band mapping
   - primary reason label
   - optional component breakdown
3. Keep the scoring deterministic and explainable.
4. Add direct tests for:
   - low-risk aligned case
   - whale-conflict increase
   - illiquid breakout increase
   - severe band thresholding

Deliverables:

- reusable trap-risk seam
- clear score/band contract

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_strategy_and_system.py tests/test_signals_coverage.py -q`

Acceptance criteria:

- trap risk is scored through one shared seam
- score, band, and reason are all produced consistently

### WT-P4. Scanner Metadata Integration

Purpose:

Attach whale/trap metadata to scanner candidates without changing candidate eligibility.

Target files:

- `core/DailyScanner.py`
- scanner metadata tests

Tasks:

1. Compute whale-flow metadata for candidate tickers.
2. Compute trap-risk metadata after scanner and EGX microstructure context exist.
3. Attach the new metadata to candidate payloads.
4. Preserve all existing EGX microstructure metadata fields.
5. Ensure no candidate is filtered solely because of this new metadata.
6. Add tests for:
   - metadata presence
   - neutral fallback with missing whale/trap data
   - conflict and high-risk payload shaping

Deliverables:

- scanner payloads enriched with whale/trap metadata
- no behavior change in candidate blocking

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py tests/test_signals_coverage.py -q`

Acceptance criteria:

- scanner payloads can explain supportive vs conflicted whale context
- trap-risk metadata is visible without enforcement

### WT-P5. AI Snapshot Integration

Purpose:

Aggregate scanner-level whale/trap metadata into reusable AI snapshot structures.

Target files:

- `core/ai_report/snapshot.py`
- targeted snapshot tests

Tasks:

1. Add snapshot aggregates for:
   - supportive whale-aligned count
   - whale conflict count
   - high trap-risk count
   - severe trap-risk count
2. Add top supportive and top conflicted / high-risk names.
3. Keep snapshot generation resilient when whale/trap or scanner data is missing.
4. Add tests for:
   - aggregate counts
   - top-name selection
   - missing-data fallback

Deliverables:

- AI snapshot support for whale/trap metadata
- aggregate summary structures usable by generation and dashboard layers

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_api_endpoints.py tests/test_strategy_and_system.py -q`

Acceptance criteria:

- AI snapshot can summarize whale/trap state without recalculating the logic internally

### WT-P6. AI Report Narrative Integration

Purpose:

Teach the AI report layer to cite and narrate the new whale/trap metadata using shared backend truth.

Target files:

- `core/ai_report/generation.py`
- targeted narrative tests

Tasks:

1. Use whale/trap metadata inside:
   - market-direction reasoning
   - candidate commentary
   - risk-warning sections
2. Add explicit narrative support for:
   - accumulation-supported technical setups
   - distribution-conflicted technical setups
   - technically valid but high trap-risk candidates
3. Preserve current report behavior when whale/trap metadata is absent.
4. Add tests for:
   - supportive narrative
   - conflict warning narrative
   - graceful degradation when metadata is absent

Deliverables:

- AI report narrative aware of whale/trap metadata
- shared reasoning with scanner and snapshot layers

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_strategy_and_system.py tests/test_api_endpoints.py -q`

Acceptance criteria:

- report language reflects shared whale/trap truth instead of independent ad hoc heuristics

### WT-P7. Dashboard Summary Integration and Closeout

Purpose:

Expose compact whale/trap summary signals to dashboard-facing consumers.

Target files:

- dashboard-facing backend or shaping paths
- frontend/dashboard consumers only if additive fields are surfaced
- targeted tests

Tasks:

1. Surface summary fields such as:
   - supportive whale-aligned count
   - high or severe trap-risk count
   - strongest supportive names
   - strongest conflict names
2. Keep the dashboard summary thin; it should consume backend truth rather than recompute it.
3. Add tests for:
   - summary presence
   - partial-payload stability
   - no-regression handling when no whale/trap data exists

Deliverables:

- dashboard-facing whale/trap summary metadata
- closeout verification for scanner, AI, and dashboard consumers

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_api_endpoints.py tests/test_strategy_and_system.py tests/test_scanner_and_data.py -q`
- `npm --prefix frontend run test -- --runInBand`

Acceptance criteria:

- dashboard can summarize whale/trap state compactly
- frontend consumers stay aligned with backend truth

## 6. Verification Matrix

Each work package must declare:

1. protected behavior
2. tests added or updated
3. scanner, AI report, or dashboard surfaces affected
4. observability counters added
5. rollout mode: shadow-only

Minimum release-quality verification for the full slice:

### Backend

```powershell
$env:HORUS_DB_FILE=':memory:'
.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py tests/test_signals_coverage.py tests/test_strategy_and_system.py tests/test_api_endpoints.py -q
```

### Frontend

```powershell
npm --prefix frontend run test -- --runInBand
npm --prefix frontend run build
```

### Manual assertions

- scanner candidates expose whale and trap fields without reducing candidate count solely because of the new metadata
- AI snapshot includes supportive/conflict and trap-risk aggregates
- AI report cites whale/trap metadata when present
- dashboard summary surfaces the new counts and top-name groupings safely

## 7. Risks and Controls

### Risk: whale/trap logic drifts between scanner and AI report

Control:

- keep all first-release interpretation inside shared seams

### Risk: the first score is too clever to explain

Control:

- keep weighted rules small, deterministic, and reason-labeled

### Risk: missing whale or trap data breaks downstream consumers

Control:

- define neutral defaults and test missing-data fallbacks explicitly

### Risk: frontend consumers silently reinterpret backend metadata

Control:

- let frontend layers format and display only; do not recreate score logic there

### Risk: operators assume the new metadata already blocks risky names

Control:

- keep rollout mode explicitly shadow-only and expose supporting diagnostics

## 8. Suggested Execution Cadence

For a single owner, the recommended order is:

1. finish `WT-P1`, `WT-P2`, and `WT-P3` first so shared logic stabilizes before consumer wiring
2. land `WT-P4` before touching AI layers so scanner payload truth exists first
3. land `WT-P5` and `WT-P6` together so snapshot and narrative share the same structure
4. close with `WT-P7` after backend summary shapes are stable

## 9. First Recommended Slice

Start with `WT-P1` first.

The highest-value first edit is:

- create `core/whale_flow.py`
- create `core/trap_risk.py`
- define shadow-safe metadata defaults and counters before consumer wiring

That sequence gives the cleanest shared contract with the lowest regression risk.
