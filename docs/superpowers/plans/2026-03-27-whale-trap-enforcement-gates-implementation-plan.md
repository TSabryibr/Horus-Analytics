# Horus Analytics II Whale And Trap Enforcement Gates Implementation Plan

Date: 2026-03-27
Based on:

- `docs/superpowers/specs/2026-03-27-whale-trap-enforcement-gates-design.md`
- `docs/superpowers/specs/2026-03-27-whale-trap-shadow-metadata-design.md`
- `core/whale_flow.py`
- `core/trap_risk.py`
- `core/DailyScanner.py`
- `routes/signals.py`
- `core/signals/publishing.py`
- `core/ai_report/generation.py`
- scanner and Oracle/operator-facing shadow diagnostics already implemented

Track: Whale/Trap Enforcement, Recommendation Gating, and Operator Visibility
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved whale/trap enforcement-gates design into an execution-ready sequence for one owner.

The implementation must leave seven things true:

1. Whale/trap enforcement is computed in one shared backend seam instead of being duplicated across scanner, publishing, and AI report layers.
2. The first enforced release keeps candidates visible and explainable rather than silently hiding them.
3. Scanner rows can distinguish `ALLOW`, `WATCH_ONLY`, and `BLOCK_EXECUTION`.
4. Recommendation publishing stops promoting blocked names as normal actionable recommendations.
5. AI report reads and explains enforcement state using backend truth instead of recomputing its own rules.
6. EGX30 and EGX70 thresholds remain profile-aware and configurable.
7. Simulator and live execution remain untouched in this first enforcement package.

## 2. In Scope

Primary backend targets:

- new shared seam under `core/`:
  - `core/enforcement_gates.py`
- `core/DailyScanner.py`
- `routes/signals.py`
- `core/signals/publishing.py`
- `core/ai_report/generation.py`
- targeted tests for enforcement seam, scanner payloads, publishing behavior, and AI report consumption

Potential frontend/runtime touchpoints:

- scanner-facing frontend consumers if enforcement state becomes visible in result rows or summary cards
- operator-facing report/dashboard surfaces only if additive enforced-state explanation is needed

Out of scope:

- simulator trade allow/block logic
- live broker execution changes
- position-size throttles
- hidden-row behavior that removes blocked names from operator view
- machine-learning-based threshold selection

## 3. Execution Rules

These rules apply to every package in this slice:

1. No enforcement logic may live only in UI or route code; gate decisions must come from the shared seam.
2. No blocked candidate may disappear silently in the first release.
3. No publishing change without audit metadata explaining what was downgraded or blocked.
4. No AI report logic may invent enforcement state independently of scanner or publishing.
5. No simulator or live execution enforcement in this package.
6. Prefer reason-labeled rule gates over opaque composite heuristics.

## 4. Work Package Sequence

Execute this slice in the following order:

1. `EF-P1` Enforcement contract and diagnostics scaffolding
2. `EF-P2` Shared enforcement seam
3. `EF-P3` Scanner visible-but-blocked integration
4. `EF-P4` Recommendation publishing enforcement
5. `EF-P5` AI report and audit closeout

This order is intentional:

- the contract should exist before any consumer depends on it
- the shared seam should stabilize before scanner or publishing wiring
- scanner should surface enforced state before publishing starts excluding names
- AI report should consume already-stable enforcement payloads, not invent a parallel story

## 5. Work Packages

### EF-P1. Enforcement Contract and Diagnostics Scaffolding

Purpose:

Define the shared enforcement vocabulary and observability counters before rules begin changing behavior.

Target files:

- `core/enforcement_gates.py`
- `core/whale_flow.py` or a closely-related helper if shared diagnostics composition needs extension
- targeted tests

Tasks:

1. Define shared enforcement fields:
   - `enforcement_state`
   - `enforcement_visibility`
   - `enforcement_reason`
   - `enforcement_notes`
   - `enforcement_profile`
2. Define neutral enforcement defaults that degrade safely when whale/trap metadata is absent.
3. Add initial observability counters for:
   - allow count
   - watch-only count
   - block count
   - counts by reason
   - counts by profile
   - EGX30 vs EGX70 enforcement counts
4. Add tests that lock the contract shape before seam logic lands.

Deliverables:

- shared enforcement vocabulary
- enforcement-safe defaults
- diagnostics contract

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_whale_trap_metadata_contract.py tests/test_scanner_and_data.py -q`

Acceptance criteria:

- all later packages can emit and consume one enforcement contract
- missing metadata resolves to explicit safe defaults instead of ad hoc per-consumer fallbacks

### EF-P2. Shared Enforcement Seam

Purpose:

Compute `ALLOW`, `WATCH_ONLY`, and `BLOCK_EXECUTION` from whale/trap metadata and profile-aware thresholds.

Target files:

- `core/enforcement_gates.py`
- targeted seam tests

Tasks:

1. Implement first-release gate logic:
   - `SEVERE` trap risk -> `BLOCK_EXECUTION`
   - `HIGH` trap risk + `CONFLICT` -> `BLOCK_EXECUTION`
   - `HIGH` trap risk -> `WATCH_ONLY`
   - `CONFLICT` -> `WATCH_ONLY`
   - otherwise `ALLOW`
2. Make the seam accept profile context so EGX30 and EGX70 can diverge without scattered branching.
3. Emit:
   - enforcement state
   - reason
   - notes
   - profile used
4. Add direct tests for:
   - severe trap risk block
   - high risk conflict block
   - high risk watch-only
   - low-risk supportive allow
   - EGX30 vs EGX70 threshold difference

Deliverables:

- reusable enforcement seam
- profile-aware gate logic

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_signals_coverage.py tests/test_strategy_and_system.py -q`

Acceptance criteria:

- enforcement state is produced through one shared seam
- rule labels and notes are deterministic and test-backed

### EF-P3. Scanner Visible-But-Blocked Integration

Purpose:

Apply enforcement state to scanner payloads while keeping blocked names visible and explainable.

Target files:

- `core/DailyScanner.py`
- `routes/scanner.py` if diagnostics/state exposure needs extension
- scanner-facing frontend consumers if enforced-state badges or labels are surfaced
- targeted scanner tests

Tasks:

1. Compute enforcement state after whale/trap metadata and route profile exist.
2. Attach enforcement fields to scanner candidates.
3. Extend scanner diagnostics with allow/watch/block rollups.
4. Surface blocked/watch-only state in scanner UI with explicit reason text or badges.
5. Ensure blocked rows remain visible.
6. Add tests for:
   - payload presence
   - blocked rows remain in scanner data
   - watch-only and blocked counts
   - frontend rendering of enforced state

Deliverables:

- scanner payloads enriched with enforcement metadata
- operator-visible blocked/watch-only state

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner`

Acceptance criteria:

- blocked names are visible with explicit reasons
- scanner no longer presents blocked names as plain actionable rows

### EF-P4. Recommendation Publishing Enforcement

Purpose:

Make publishing respect enforcement state so blocked names stop flowing into normal actionable outputs.

Target files:

- `routes/signals.py`
- `core/signals/publishing.py`
- targeted publishing tests

Tasks:

1. Persist or rebuild enforcement state on recommendations from scanner-derived metadata.
2. Exclude `BLOCK_EXECUTION` recommendations from normal publishable sets.
3. Downgrade `WATCH_ONLY` recommendations to non-actionable commentary or watchlist treatment rather than full publish.
4. Emit audit events for:
   - blocked recommendations
   - watch-only downgrades
   - publish summaries after enforcement filtering
5. Add tests for:
   - blocked recommendations not published
   - watch-only recommendations downgraded
   - publish summaries and audit metadata reflect enforcement

Deliverables:

- recommendation publishing aligned with scanner enforcement state
- audit trail for blocked and downgraded recommendations

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_signals_coverage.py tests/test_signals_publish_service.py tests/test_signals_p0.py -q`

Acceptance criteria:

- blocked names are not promoted as normal publishable recommendations
- publish summaries clearly explain enforcement impact

### EF-P5. AI Report and Audit Closeout

Purpose:

Teach AI/report surfaces to read and explain enforced state while closing out observability and audit coverage.

Target files:

- `core/ai_report/generation.py`
- `core/ai_report/snapshot.py` only if enforcement aggregates need additive shaping
- operator-facing report/dashboard consumers if additive enforced-state summary appears there
- targeted report and audit tests

Tasks:

1. Make AI report distinguish:
   - actionable names
   - watch-only names
   - blocked names
2. Add narrative support for:
   - technically valid but blocked candidates
   - watch-only downgrades
   - enforcement counts and top reasons
3. Ensure audit endpoints and summaries can surface the new enforcement events cleanly.
4. Add tests for:
   - blocked-state report wording
   - watch-only report wording
   - audit metadata availability
   - graceful degradation if enforcement metadata is absent

Deliverables:

- AI report aligned with enforced state
- audit closeout for enforcement package

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_ai_daily_report.py tests/test_ai_report_generation_service.py tests/test_api_endpoints.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/oracle`

Acceptance criteria:

- AI report explains enforcement decisions using shared backend truth
- operator-facing audit/review surfaces can trace why names were downgraded or blocked

## 6. Verification Matrix

Each work package must declare:

1. protected behavior
2. tests added or updated
3. scanner, publishing, or AI/report surfaces affected
4. observability counters added
5. rollout mode: visible-but-blocked first release

Minimum release-quality verification for the full slice:

### Backend

```powershell
$env:HORUS_DB_FILE=':memory:'
.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py tests/test_signals_coverage.py tests/test_signals_publish_service.py tests/test_signals_p0.py tests/test_ai_daily_report.py tests/test_ai_report_generation_service.py tests/test_api_endpoints.py -q
```

### Frontend

```powershell
npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner
npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/oracle
npm --prefix frontend run build
```

### Manual assertions

- blocked candidates remain visible in scanner with explicit reason text
- watch-only candidates are distinguishable from actionable names
- blocked recommendations are not published through the normal actionable channel
- AI report can call out blocked and watch-only names using shared backend truth
- audit summaries can explain what was allowed, downgraded, or blocked

## 7. Risks and Controls

### Risk: blocked names still leak into recommendation publishing

Control:

- make publishing consume the shared enforcement seam and add audit-backed tests

### Risk: scanner and AI report show different enforcement meanings

Control:

- centralize decisioning in `core/enforcement_gates.py` and keep AI/report as a reader only

### Risk: EGX70 thresholds are too aggressive in the first release

Control:

- keep thresholds profile-based, observable, and easy to loosen without changing consumer contracts

### Risk: visible-but-blocked state is confusing to operators

Control:

- show explicit state vocabulary, reasons, and notes in scanner/report surfaces

### Risk: the package grows into simulator/live enforcement too early

Control:

- keep simulator and live execution explicitly out of scope for this plan

## 8. Suggested Execution Cadence

For a single owner, the recommended order is:

1. finish `EF-P1` and `EF-P2` first so contract and seam logic stabilize before behavior changes
2. land `EF-P3` before touching publishing so operators can see the enforced state first
3. land `EF-P4` once scanner-visible states are trustworthy
4. close with `EF-P5` after publishing behavior is stable and auditable

## 9. First Recommended Slice

Start with `EF-P1` first.

The highest-value first edit is:

- create `core/enforcement_gates.py`
- define visible-but-blocked contract defaults and diagnostics
- add seam tests for `ALLOW`, `WATCH_ONLY`, and `BLOCK_EXECUTION`

That sequence gives the cleanest shared gate contract with the lowest regression risk.
