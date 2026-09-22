# Horus Analytics II Phase 3 AI Report Decomposition Design

Date: 2026-03-17
Status: Draft for implementation planning
Document type: Design / explanation for Phase 3 execution
Target audience: Single-owner maintainer of the Horus Analytics II backend
Primary goal: Decompose `routes/ai_report.py` into smaller, testable units without changing behavior

## 1. Purpose

This design defines the Phase 3 decomposition strategy for `routes/ai_report.py`. Phase 1 stabilized the AI report failure contract and made degradation explicit. Phase 2 decomposed the first oversized backend route families and the first shared pipeline/frontend seams. Phase 3 should use that stability to split the AI report route behind explicit capability seams so future work on report generation, snapshot assembly, and broadcast delivery does not require broad incidental edits to one oversized module.

This is not a feature design. It is an internal architecture design for safer maintenance, clearer test boundaries, and lower regression risk in one of the remaining high-density route modules.

## 2. Current Problem

`routes/ai_report.py` currently mixes multiple unrelated responsibilities in one module:

- environment parsing and provider normalization
- cache and TTL logic
- structured error and degradation payload construction
- data freshness computation
- portfolio, signal, and cross-tab snapshot collection
- rule-based report generation
- prompt construction
- LLM provider routing and fallback
- Telegram message formatting
- broadcast delivery behavior
- endpoint registration for provider testing, daily report generation, and broadcast

Even with the Phase 1 contract hardening, this creates four ongoing risks:

1. snapshot changes, LLM changes, and broadcast changes are coupled in one file
2. route handlers still know too much about data collection and transport details
3. lower-level logic is harder to test directly than it should be
4. performance and runtime-consistency work in Phase 3 would otherwise land in the same oversized module, increasing regression risk

## 3. Phase 3 Objective

Phase 3 should turn `routes/ai_report.py` into a thin HTTP transport module backed by focused backend units. The result should preserve all current API behavior while making each major AI-report capability understandable and testable on its own.

Success means:

1. route handlers are mostly request translation and response mapping
2. snapshot assembly is directly testable without HTTP setup
3. LLM/provider fallback logic is directly testable without route setup
4. broadcast formatting and delivery diagnostics are directly testable without route setup
5. existing AI-report route behavior and Phase 1 error/degradation contracts remain intact

## 4. Recommended Approach

Recommended approach: capability-based service extraction behind a stable route surface.

Why this approach:

- it matches the decomposition pattern that worked cleanly in Phase 2 for `routes/portfolio.py` and `routes/signals.py`
- `ai_report.py` already divides naturally into a few responsibility clusters
- it keeps migration incremental and preserves the existing HTTP contract while internals move behind seams

Rejected alternatives:

### A. Split by endpoint only

Example: one file for `/ai/provider/test`, one for `/ai/daily-report`, one for `/ai/daily-report/broadcast`.

Why rejected:

- shared snapshot and provider-fallback logic would still be duplicated or awkwardly shared
- it produces weaker boundaries than splitting by capability
- it makes later performance work harder because the expensive internals remain entangled

### B. Stability-only wrapper pass

Why rejected:

- too little structural payoff for a Phase 3 decomposition wave
- leaves the main maintenance problem in place
- does not create strong new seam-level test targets

## 5. Proposed Target Shape

The target is not to redesign the public API. The target is to keep the existing endpoints and move the internals toward this structure:

### 5.1 Route surface

Keep `routes/ai_report.py`, but shrink it to:

- request models that are truly route-facing
- endpoint registration
- minimal route-boundary validation
- mapping from route calls to capability functions

### 5.2 Capability units

Create focused internal backend units for these concerns:

1. `ai_report_boundary`
   - provider normalization
   - env parsing
   - cache helpers and TTL evaluation
   - structured error/degradation payload builders

2. `ai_report_snapshot`
   - freshness computation
   - portfolio snapshot collection
   - signal snapshot collection
   - cross-tab snapshot assembly
   - snapshot degradation and module-status reporting

3. `ai_report_generation`
   - rule-based report generation
   - prompt building
   - provider/model selection
   - LLM routing and fallback
   - report-section de-duplication

4. `ai_report_transport`
   - Telegram message formatting
   - broadcast send flow
   - delivery diagnostics

These do not need to become four public modules on day one. They are the target boundaries. The implementation can start with a `core/ai_report/` package containing a few files and grow only where that improves clarity.

## 6. Extraction Order

The extraction order should minimize behavior risk and maximize seam value.

### Package A3-1: Boundary and cache helpers

Extract first:

- `_normalize_source_module`
- `_int_env`
- `_float_env`
- `_bool_env`
- `_parse_csv_models`
- `_ollama_model_candidates`
- `_cache_is_fresh`
- `_ai_report_cache_ttl_sec`
- `_error_context`
- `_module_issue`

Reason:

- these helpers are lower risk and give the rest of the work a stable shared vocabulary
- they reduce noise in the route file immediately without changing endpoint logic

Target outcome:

- one shared boundary module used by the existing route and later extracted capability units

### Package A3-2: Snapshot assembly

Extract next:

- `_compute_data_freshness`
- `_collect_portfolio_snapshot`
- `_collect_signal_snapshot`
- `_collect_cross_tab_snapshot`
- any small snapshot-only helper functions that exist only to support those flows

Reason:

- this is the main dependency hub inside `ai_report.py`
- it is the highest-value seam for both correctness and future performance work

Target outcome:

- snapshot collection is directly testable without route setup

### Package A3-3: Generation and fallback

Extract:

- `_generate_rule_based_report`
- `_build_llm_prompts`
- `_maybe_generate_llm_report`
- provider-specific call helpers
- report de-duplication helpers

Reason:

- generation and provider fallback are cohesive
- this area already has strong Phase 1 route coverage and can now gain direct seam tests

Target outcome:

- provider/model fallback becomes directly testable and easier to profile

### Package A3-4: Broadcast and message transport

Extract:

- `build_ai_report_telegram_message`
- `broadcast_ai_daily_report`
- message chunking or transport-specific diagnostics that belong to the broadcast flow

Reason:

- broadcast behavior is distinct from snapshot generation
- transport concerns should not live alongside data collection and prompt logic

Target outcome:

- Telegram send behavior and delivery diagnostics are directly testable

### Package A3-5: Route slimdown and checkpoint

Finish by:

- leaving `routes/ai_report.py` as a thin HTTP shell
- preserving route-level monkeypatch seams where the current test suite depends on them
- running the package checkpoint across backend and frontend/browser surfaces that touch Oracle/news behavior

Reason:

- the route should be the last thing simplified after the internals are stable

## 7. Rules for the Decomposition

These rules keep the refactor safe:

1. No endpoint path or response-shape changes during the decomposition wave.
2. No business-behavior changes mixed with structural extraction unless required to preserve correctness.
3. Every extraction slice starts with the existing `ai_report` route tests already passing.
4. New lower-level tests should be added only after the seam exists.
5. The route module should remain the HTTP contract owner.
6. Shared helpers should move to capability units, not to a new generic `utils` dumping ground.

## 8. Testing Strategy

The decomposition should preserve the current route-level protection while adding seam-level tests gradually.

### Existing route anchors to preserve

- `tests/test_ai_daily_report.py`
- Oracle/news frontend tests that depend on the AI report surface

### New test strategy by slice

For each extracted unit:

1. keep the existing route-level tests green
2. add direct tests for the new service/helper layer
3. only narrow route mocks after the new seam exists

Examples:

- `ai_report_boundary` should get direct tests for provider normalization, env parsing, and cache TTL decisions
- `ai_report_snapshot` should get direct tests for degradation assembly and module-status shaping
- `ai_report_generation` should get direct tests for provider fallback and prompt/report shaping
- `ai_report_transport` should get direct tests for Telegram message formatting and delivery-failure handling

## 9. Error-Contract Preservation

Phase 1 already established important `ai_report` behavior that must not regress:

1. degraded output versus hard failure must stay explicit
2. snapshot degradation must remain visible and structured
3. invalid provider input must remain a structured validation failure
4. broadcast delivery failures must retain the current structured diagnostics

This means the decomposition is not allowed to simplify away existing reason fields just because they are now produced lower in the stack.

## 10. Operational and Maintenance Benefits

If implemented correctly, this design should produce these practical gains:

1. AI-report logic becomes easier to profile and optimize in Phase 3 performance work
2. snapshot failures become easier to reason about separately from provider failures
3. transport issues stop polluting generation logic
4. the route file becomes safer to change because it owns less business logic
5. future model/provider additions become more localized

## 11. Non-Goals

This Phase 3 design does not attempt to:

1. redesign the report schema
2. change the prompt strategy or recommendation policy beyond what is needed to preserve correctness
3. replace the current provider stack
4. bundle Playwright-flake or simulation-performance fixes into the same extraction packages

Those runtime-quality items are valid Phase 3 work, but they should be tracked as separate follow-on packages after the `ai_report` structural repair.

## 12. Acceptance Criteria

This design is successful if:

- `routes/ai_report.py` is materially smaller and primarily transport-focused
- snapshot, generation, and transport seams exist and are directly testable
- existing `ai_report` route tests still pass
- the relevant frontend Oracle/news tests and build checks still pass
- the decomposition reduces file-level coupling without changing route behavior

## 13. Recommended Next Artifact

The next artifact should be a Phase 3 implementation plan for `ai_report` decomposition. That plan should:

1. define the exact `core/ai_report/` module map
2. sequence packages `A3-1` through `A3-5`
3. name the concrete route anchors and seam tests for each slice
4. define the Phase 3 `ai_report` checkpoint commands
