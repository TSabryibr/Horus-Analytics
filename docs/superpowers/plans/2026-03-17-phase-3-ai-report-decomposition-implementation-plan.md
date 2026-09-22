# Horus Analytics II Phase 3 AI Report Decomposition Implementation Plan

Date: 2026-03-17
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-17-phase-3-ai-report-decomposition-design.md`

Track: Backend/API Stability
Phase: Phase 3 - Throughput, Operational Confidence, and Runtime Polish
Status: Completed on 2026-03-17
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 3 AI report decomposition design into an executable extraction sequence. The purpose is to turn `routes/ai_report.py` into a thin transport layer without changing endpoint paths, response shapes, degradation semantics, or broadcast behavior.

Phase 3 AI report work should leave five things true:

1. Route handlers are no longer the primary home of snapshot, generation, or transport logic.
2. Snapshot collection is directly testable without HTTP setup.
3. Provider/model fallback is directly testable without route setup.
4. Broadcast formatting and delivery diagnostics are directly testable without route setup.
5. The extraction pattern is reusable later for Phase 3 runtime-quality follow-on work.

## 2. Source Analysis and Completion Snapshot

Original source shape before extraction:

`routes/ai_report.py` contained **52 functions/classes across 2,657 lines**. The five largest functions accounted for 1,229 lines (46% of the file):

| Function | Lines | Target Module |
|---|---|---|
| `_collect_cross_tab_snapshot` | 385 | `snapshot.py` |
| `_build_rule_based_recommendations` | 282 | `generation.py` |
| `_generate_rule_based_report` | 268 | `generation.py` |
| `_score_market_direction` | 161 | `generation.py` |
| `_build_llm_prompts` | 133 | `generation.py` |

Completed extraction snapshot:

- `routes/ai_report.py` is now **553 lines**
- the route now delegates through `core/ai_report/boundary.py`, `core/ai_report/snapshot.py`, `core/ai_report/generation.py`, and `core/ai_report/transport.py`
- the route remains the HTTP contract owner and preserves the monkeypatch seams the existing suite depends on
- focused AI report verification now passes with `39 passed`

## 3. In Scope

Primary source file:

- `routes/ai_report.py` (2,657 lines -> 553 lines after completion)

Primary extraction target package:

- `core/ai_report/__init__.py`
- `core/ai_report/boundary.py`
- `core/ai_report/snapshot.py`
- `core/ai_report/generation.py`
- `core/ai_report/transport.py`

Primary route families:

- `POST /api/v1/ai/provider/test`
- `GET /api/v1/ai/daily-report`
- `POST /api/v1/ai/daily-report/broadcast`

Out of scope for this Phase 3 slice:

- redesigning the AI report schema
- changing recommendation policy except where required to preserve correctness
- replacing the current provider stack
- fixing the Playwright crawl flake in the same package
- fixing the simulation performance threshold in the same package

## 4. Existing Test Anchors and Monkeypatch Inventory

### 4.1 Route-level test anchors to keep green

- `tests/test_ai_daily_report.py` (22 tests)
- `frontend/src/app/oracle/page.test.tsx`
- `frontend/src/app/news/page.test.tsx`
- `frontend/src/app/news/page.route.test.tsx`
- `frontend/src/app/context/GlobalDataContext.test.tsx`
- `frontend/src/app/components/Sidebar.test.tsx`

### 4.2 Critical monkeypatch seams in existing tests

These are the exact `monkeypatch.setattr` targets used by the existing 22 route tests. Every extraction must preserve or explicitly re-export these seams so the existing test suite does not break:

| Monkeypatch Target | Used By Tests | Migration Strategy |
|---|---|---|
| `routes.ai_report._collect_cross_tab_snapshot` | 8 tests | Keep thin wrapper in route that delegates to `core.ai_report.snapshot` |
| `routes.ai_report._maybe_generate_llm_report` | 7 tests | Keep thin wrapper in route that delegates to `core.ai_report.generation` |
| `routes.ai_report._collect_signal_snapshot` | 1 test | Re-export from route or update test import |
| `routes.ai_report._collect_portfolio_snapshot` | 1 test | Re-export from route or update test import |
| `routes.ai_report._test_ollama_endpoint` | 1 test | Re-export from route or update test import |
| `routes.ai_report._call_ollama_report` | 3 tests | Re-export from route or update test import |
| `routes.ai_report._call_openai_report` | 2 tests | Re-export from route or update test import |
| `routes.ai_report._call_openrouter_report` | 2 tests | Re-export from route or update test import |
| `routes.ai_report._call_gemini_report` | 2 tests | Re-export from route or update test import |
| `routes.ai_report.requests.get` | 1 test | Import passthrough stays |
| `routes.ai_report.TelegramBot_Alerts.send_message` | 2 tests | Import passthrough stays |
| `routes.ai_report.Ratatoskr.*` | 2 tests | Import passthrough stays |
| `routes.ai_report.SectorRotation.*` | 1 test | Import passthrough stays |
| `routes.ai_report.Vanaheim.*` | 1 test | Import passthrough stays |
| `routes.ai_report.Svartalfheim.*` | 1 test | Import passthrough stays |
| `routes.ai_report.Jotunheim.*` | 1 test | Import passthrough stays |
| `routes.ai_report.Fenrir.*` | 1 test | Import passthrough stays |
| `routes.ai_report.MarketPredictor.*` | 2 tests | Import passthrough stays |
| `ai_report.NEWS_CACHE` (5 caches) | 2 tests | Keep cache objects in route; pass to snapshot as arguments |

> [!IMPORTANT]
> **Migration rule**: For the 8 tests that monkeypatch `_collect_cross_tab_snapshot` and the 7 that monkeypatch `_maybe_generate_llm_report`, the safest approach is to keep thin delegation wrappers in `routes/ai_report.py` so the existing monkeypatch paths continue to resolve. Only update test imports in A3-5 after all extractions are stable.

### 4.3 New seam tests to add

- `tests/test_ai_report_boundary_service.py`
- `tests/test_ai_report_snapshot_service.py`
- `tests/test_ai_report_generation_service.py`
- `tests/test_ai_report_transport_service.py`

## 5. Target Module Map

### `core/ai_report/__init__.py`

Public re-exports for the package. Selective imports from the sub-modules below.

### `core/ai_report/boundary.py`

Owns (10 functions, ~94 lines):

| Function | Current Lines | Notes |
|---|---|---|
| `_normalize_source_module` | L71-86 (16 lines) | Provider normalization |
| `_int_env` | L87-96 (10 lines) | Env parsing |
| `_float_env` | L97-106 (10 lines) | Env parsing |
| `_bool_env` | L107-113 (7 lines) | Env parsing |
| `_parse_csv_models` | L114-117 (4 lines) | Model list parsing |
| `_ollama_model_candidates` | L118-130 (13 lines) | Fallback model list |
| `_cache_is_fresh` | L223-233 (11 lines) | Cache TTL check |
| `_ai_report_cache_ttl_sec` | L234-237 (4 lines) | Cache TTL helper |
| `_error_context` | L238-246 (9 lines) | Structured error builder |
| `_module_issue` | L247-255 (9 lines) | Structured issue builder |

Also moves:

| Function | Current Lines | Notes |
|---|---|---|
| `_safe_call` | L216-222 (7 lines) | Generic safe-call wrapper |
| `_safe_call_with_error` | L256-262 (7 lines) | Safe-call with error capture |
| `_seconds_age_from_time` | L263-274 (12 lines) | Time age computation |
| `_canonical_text` | L131-134 (4 lines) | Text normalization |
| `_dedupe_strings` | L135-151 (17 lines) | String deduplication |
| `_remove_overlaps` | L152-165 (14 lines) | Overlap removal |
| `_dedupe_recommendations` | L166-183 (18 lines) | Recommendation deduplication |
| `_dedupe_report_sections` | L184-215 (32 lines) | Report section deduplication |
| `_rule_engine_instruction_text` | L67-70 (4 lines) | Instruction text builder |

**Total: ~19 functions, ~172 lines**

### `core/ai_report/snapshot.py`

Owns (6 functions, ~635 lines):

| Function | Current Lines | Notes |
|---|---|---|
| `_compute_data_freshness` | L275-351 (77 lines) | Freshness scoring |
| `_extract_sector_leaders` | L352-364 (13 lines) | Sector helper |
| `_resolve_portfolio_id` | L365-374 (10 lines) | Portfolio resolution |
| `_collect_portfolio_snapshot` | L375-464 (90 lines) | Portfolio data |
| `_collect_signal_snapshot` | L465-524 (60 lines) | Signal data |
| `_collect_cross_tab_snapshot` | L525-909 (385 lines) | Cross-tab assembly |

**Total: ~6 functions, ~635 lines** — this is the highest-value extraction.

### `core/ai_report/generation.py`

Owns (18 functions, ~1,144 lines):

| Function | Current Lines | Notes |
|---|---|---|
| `_score_market_direction` | L910-1070 (161 lines) | Market scoring |
| `_derive_local_execution_profile` | L1071-1141 (71 lines) | Execution profile |
| `_compute_rr_ratio` | L1142-1152 (11 lines) | Risk/reward |
| `_build_rule_based_recommendations` | L1153-1434 (282 lines) | Rule-based recs |
| `_generate_rule_based_report` | L1435-1702 (268 lines) | Rule report |
| `_strip_code_fences` | L1703-1711 (9 lines) | LLM output cleanup |
| `_safe_string_list` | L1712-1717 (6 lines) | Safe list helper |
| `_safe_recommendations` | L1718-1747 (30 lines) | Safe recs helper |
| `_normalize_llm_report` | L1748-1795 (48 lines) | LLM output normalize |
| `_build_llm_prompts` | L1796-1928 (133 lines) | Prompt construction |
| `_extract_gemini_text` | L1929-1946 (18 lines) | Gemini response parse |
| `_call_openai_report` | L1947-1993 (47 lines) | OpenAI provider |
| `_call_gemini_report` | L1994-2039 (46 lines) | Gemini provider |
| `_call_openrouter_report` | L2040-2086 (47 lines) | OpenRouter provider |
| `_call_ollama_report` | L2087-2149 (63 lines) | Ollama provider |
| `_test_openai_api_key` | L2150-2163 (14 lines) | Provider test |
| `_test_gemini_api_key` | L2164-2177 (14 lines) | Provider test |
| `_test_openrouter_api_key` | L2178-2191 (14 lines) | Provider test |
| `_test_ollama_endpoint` | L2192-2229 (38 lines) | Provider test |
| `_maybe_generate_llm_report` | L2230-2296 (67 lines) | LLM orchestrator |

**Total: ~20 functions, ~1,144 lines** — the largest extraction.

### `core/ai_report/transport.py`

Owns (2 functions, ~69 lines):

| Function | Current Lines | Notes |
|---|---|---|
| `_sanitize_telegram_text` | L2519-2525 (7 lines) | Text cleanup |
| `build_ai_report_telegram_message` | L2526-2587 (62 lines) | Message builder |

**Total: ~2 functions, ~69 lines**

### Route file after extraction (`routes/ai_report.py`)

Current completed shape (~553 lines):

| Item | Lines | Notes |
|---|---|---|
| Imports and constants | ~50 | Updated to import from `core.ai_report.*` |
| `AiDailyBroadcastRequest` model | ~10 | Route-facing model |
| `_AI_REPORT_CACHE` and cache constants | ~20 | Cache stays in route |
| Delegation wrappers (monkeypatch compatibility) | ~50 | Thin wrappers for test seams |
| `test_ai_provider_key` endpoint | ~52 | L2297-2348 |
| `get_ai_daily_report` endpoint | ~58 | L2349-2406 |
| `_get_ai_daily_report_inner` | ~112 | L2407-2518 |
| `broadcast_ai_daily_report` endpoint | ~70 | L2588-2657 |
| Remaining route glue | ~215 | Orchestration and response mapping |

**This represents a ~79% reduction** from 2,657 to 553 lines.

## 6. Package Sequence

Execute the AI report decomposition in this order:

1. `A3-1` Boundary and cache helpers
2. `A3-2` Snapshot assembly
3. `A3-3` Generation and fallback
4. `A3-4` Broadcast and message transport
5. `A3-5` Route slimdown and checkpoint

This order is intentional:

- lower-risk helpers move first and establish a stable vocabulary
- snapshot assembly is the highest-value dependency seam
- generation should move only after the snapshot contract is stable
- transport should move after generation to avoid re-coupling delivery behavior to provider logic
- the route should be simplified last

## 7. Work Packages

### A3-1. Boundary and Cache Helpers

Purpose:

Establish one reusable AI report boundary seam before larger extractions begin.

Target files:

- `routes/ai_report.py`
- `core/ai_report/__init__.py` [NEW]
- `core/ai_report/boundary.py` [NEW]

Tasks:

1. Create the `core/ai_report` package.
2. Move the 19 functions listed in §5 `boundary.py` section (~172 lines).
3. Update `routes/ai_report.py` to import from `core.ai_report.boundary`.
4. Preserve existing monkeypatch seams by keeping re-exports or wrappers in the route file where tests use `routes.ai_report.*` paths.
5. Add direct tests for:
   - `_normalize_source_module` (all provider variants including coercion)
   - `_int_env`, `_float_env`, `_bool_env` (valid, invalid, missing)
   - `_cache_is_fresh` (fresh, stale, missing entry)
   - `_error_context` and `_module_issue` (structured payload shape)
   - `_dedupe_report_sections` (already tested at route level, add direct seam test)

Verification:

- `python -m pytest tests/test_ai_report_boundary_service.py -q`
- `python -m pytest tests/test_ai_daily_report.py -q`

Acceptance criteria:

- shared route helpers are imported from `core/ai_report/boundary.py`
- route-level validation and cache/degradation behavior remains unchanged
- all 22 existing route tests pass
- direct seam tests cover the extracted helper layer

### A3-2. Snapshot Assembly

Purpose:

Separate snapshot collection from route transport and make later performance work measurable.

Target files:

- `routes/ai_report.py`
- `core/ai_report/snapshot.py` [NEW]

Functions to extract (6 functions, ~635 lines):

- `_compute_data_freshness`
- `_extract_sector_leaders`
- `_resolve_portfolio_id`
- `_collect_portfolio_snapshot`
- `_collect_signal_snapshot`
- `_collect_cross_tab_snapshot`

> [!WARNING]
> `_collect_cross_tab_snapshot` (385 lines) uses 8 external domain module imports (`Ratatoskr`, `SectorRotation`, `Vanaheim`, `Svartalfheim`, `Jotunheim`, `Fenrir`, `MarketPredictor`, `ConfluenceEngine`) and accesses 7 shared cache objects. These imports must move to `snapshot.py`, but the route must keep its own top-level imports so that monkeypatch paths like `routes.ai_report.Ratatoskr.gather_gossip` continue to resolve. Consider passing external deps as arguments or accepting them from the route's namespace.

Tasks:

1. Extract the 6 functions into `core/ai_report/snapshot.py`.
2. Keep snapshot degradation, module-status, and issue-record behavior identical to Phase 1 contract.
3. Keep thin delegation wrappers in `routes/ai_report.py` for `_collect_cross_tab_snapshot` and `_collect_portfolio_snapshot` so the 9 existing monkeypatch paths resolve.
4. Add direct seam tests for:
   - `_compute_data_freshness` with missing/stale/fresh sources
   - `_collect_portfolio_snapshot` with missing portfolio degradation
   - `_collect_cross_tab_snapshot` with module failure injection
   - `_extract_sector_leaders` with edge cases

Verification:

- `python -m pytest tests/test_ai_report_snapshot_service.py -q`
- `python -m pytest tests/test_ai_daily_report.py -q`

Acceptance criteria:

- snapshot collection no longer lives primarily in the route file
- snapshot degradation semantics remain unchanged
- all 22 existing route tests pass
- direct snapshot tests cover the extracted layer

### A3-3. Generation and Fallback

Purpose:

Move the highest-churn generation and provider-fallback logic behind a dedicated seam while keeping the HTTP surface stable.

Target files:

- `routes/ai_report.py`
- `core/ai_report/generation.py` [NEW]

Functions to extract (20 functions, ~1,144 lines):

- `_score_market_direction` (161 lines)
- `_derive_local_execution_profile` (71 lines)
- `_compute_rr_ratio` (11 lines)
- `_build_rule_based_recommendations` (282 lines)
- `_generate_rule_based_report` (268 lines)
- `_strip_code_fences`, `_safe_string_list`, `_safe_recommendations` (45 lines combined)
- `_normalize_llm_report` (48 lines)
- `_build_llm_prompts` (133 lines)
- `_extract_gemini_text` (18 lines)
- `_call_openai_report`, `_call_gemini_report`, `_call_openrouter_report`, `_call_ollama_report` (203 lines combined)
- `_test_openai_api_key`, `_test_gemini_api_key`, `_test_openrouter_api_key`, `_test_ollama_endpoint` (80 lines combined)
- `_maybe_generate_llm_report` (67 lines)

> [!IMPORTANT]
> **Monkeypatch note**: 7 tests monkeypatch `routes.ai_report._maybe_generate_llm_report` and 3 tests monkeypatch `routes.ai_report._call_ollama_report`. Thin delegation wrappers were intentionally preserved in the route module at completion so those seams continue to resolve.

Tasks:

1. Extract the 20 functions into `core/ai_report/generation.py`.
2. Keep current provider fallback semantics and reason fields unchanged.
3. Move `_RULE_ENGINE_REASONING_PROFILE` and `_RULE_ENGINE_THINKING_CONTRACT` constants to `generation.py`.
4. Keep thin wrappers in route for monkeypatch-targeted functions.
5. Add direct generation tests for:
   - `_score_market_direction` with various snapshot states
   - `_generate_rule_based_report` output schema compliance
   - `_build_llm_prompts` content structure and required keys
   - `_maybe_generate_llm_report` fallback chain behavior
   - Provider-specific call helpers with mocked HTTP

Verification:

- `python -m pytest tests/test_ai_report_generation_service.py -q`
- `python -m pytest tests/test_ai_daily_report.py -q`

Acceptance criteria:

- provider and report-generation orchestration delegates to `core/ai_report/generation.py`
- route tests stay green without contract drift
- direct generation tests exercise fallback behavior without full route execution

### A3-4. Broadcast and Message Transport

Purpose:

Isolate Telegram formatting and delivery handling so transport issues stop touching snapshot and generation logic.

Target files:

- `routes/ai_report.py`
- `core/ai_report/transport.py` [NEW]

Functions to extract (2 functions, ~69 lines):

- `_sanitize_telegram_text` (7 lines)
- `build_ai_report_telegram_message` (62 lines)

Tasks:

1. Extract the 2 functions into `core/ai_report/transport.py`.
2. Keep broadcast success and delivery-failure response shapes unchanged.
3. Keep delivery diagnostics and degradation metadata visible to the transport layer.
4. Add direct transport tests for:
   - `_sanitize_telegram_text` with special characters
   - `build_ai_report_telegram_message` output structure and truncation behavior
   - Message formatting with empty/degraded report payloads

Verification:

- `python -m pytest tests/test_ai_report_transport_service.py -q`
- `python -m pytest tests/test_ai_daily_report.py -q`

Acceptance criteria:

- broadcast logic no longer embeds most Telegram transport behavior
- route tests stay green without contract drift
- direct transport tests cover formatting and failure handling

### A3-5. Route Slimdown and Checkpoint

Purpose:

Turn `routes/ai_report.py` into a thin transport layer and prove the package still holds under backend and frontend verification.

Target files:

- `routes/ai_report.py`
- all new `core/ai_report/*` modules
- relevant test files

Tasks:

1. Remove dead inline helpers once the extracted seams are in place.
2. Optionally update test imports from `routes.ai_report._collect_cross_tab_snapshot` to `core.ai_report.snapshot.collect_cross_tab_snapshot` where safe.
3. Remove delegation wrappers that are no longer needed after test migration.
4. Run the package checkpoint across backend route tests, frontend Oracle/news/context tests, frontend build, and browser checks.
5. Write the Phase 3 AI report checkpoint summary after verification passes.

Deliverables:

- materially smaller `routes/ai_report.py` (553 lines, ~79% reduction)
- AI report checkpoint summary
- explicit seam-level regression coverage

Verification:

- `python -m pytest tests/test_ai_daily_report.py tests/test_ai_report_boundary_service.py tests/test_ai_report_snapshot_service.py tests/test_ai_report_generation_service.py tests/test_ai_report_transport_service.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/oracle/page.test.tsx src/app/news/page.test.tsx src/app/news/page.route.test.tsx src/app/context/GlobalDataContext.test.tsx src/app/components/Sidebar.test.tsx`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- `routes/ai_report.py` is materially smaller and primarily transport-focused
- existing AI report route contracts are preserved
- relevant frontend Oracle/news/shared-data checks remain green

## 8. Working Rules

These rules apply throughout the package:

1. No endpoint path or response-shape changes during the decomposition wave.
2. No prompt-policy or report-schema changes mixed with structural extraction unless required to preserve correctness.
3. Keep the route module as the HTTP contract owner.
4. Keep imports one-way: `routes/ai_report.py` imports `core/ai_report/*`, not the reverse.
5. Do not mix the Playwright crawl flake or simulation performance work into these extraction packages.
6. **Monkeypatch preservation**: keep thin delegation wrappers in the route module until A3-5 so existing `routes.ai_report.*` monkeypatch paths resolve.

## 9. Suggested Execution Sequence

Recommended order by slice:

### Slice 1

- `A3-1` boundary helpers (~172 lines to extract)
- add `tests/test_ai_report_boundary_service.py`
- estimated effort: small

### Slice 2

- `A3-2` snapshot assembly (~635 lines to extract)
- add `tests/test_ai_report_snapshot_service.py`
- estimated effort: medium (cross-tab snapshot has many external deps)

### Slice 3

- `A3-3` generation and fallback (~1,144 lines to extract)
- add `tests/test_ai_report_generation_service.py`
- estimated effort: large (most functions, most monkeypatch seams)

### Slice 4

- `A3-4` transport extraction (~69 lines to extract)
- add `tests/test_ai_report_transport_service.py`
- estimated effort: small

### Slice 5

- `A3-5` route slimdown and test migration
- package checkpoint
- checkpoint summary
- estimated effort: medium (test import migration, wrapper cleanup)

## 10. Risk Annotations

| Risk | Impact | Mitigation |
|---|---|---|
| Monkeypatch paths break after extraction | 22 route tests fail | Keep delegation wrappers until A3-5 |
| `_collect_cross_tab_snapshot` external imports | Snapshot tests need many mocks | Pass deps as arguments or accept module-level imports |
| `_maybe_generate_llm_report` uses `setattr` on itself for state | Stateful side-effect coupling | Preserve `last_source_module` / `last_fallback_reason` pattern in new module |
| Cache object (`_AI_REPORT_CACHE`) shared between route and snapshot | Ownership ambiguity | Keep cache in route; snapshot returns data, route manages cache |
| `asyncio.run` inside `_collect_cross_tab_snapshot` for confluence | Sync/async boundary risk | Keep as-is during extraction; refactor in Phase 3 follow-on |
| `GlobalSettings.settings` mutation in `get_ai_daily_report` | Side-effect in route handler | Keep mutation in route; extraction does not change this pattern |

## 11. Phase 3 AI Report Exit Checklist

- [x] `routes/ai_report.py` is materially smaller and primarily transport-focused
- [x] shared boundary helpers live in `core/ai_report/boundary.py`
- [x] snapshot assembly lives in `core/ai_report/snapshot.py`
- [x] generation and fallback live in `core/ai_report/generation.py`
- [x] broadcast transport lives in `core/ai_report/transport.py`
- [x] route-level AI report tests remain green (22 tests)
- [x] new seam-level tests exist for each extracted capability unit
- [x] relevant frontend Oracle/news/context tests remain green
- [x] frontend build still passes
- [x] browser baseline still passes for the affected surface
- [x] route file reduced by >=70% (553 lines from 2,657)

Checkpoint artifact to write after completion:

- `docs/superpowers/reference/2026-03-17-phase-3-ai-report-checkpoint-summary.md`

## 12. Next Planning Boundary

After the AI report structural repair is complete, the next Phase 3 planning boundary should be split into two smaller follow-on packages rather than bundled into the same work:

1. Playwright crawl/runtime boot flake reduction
2. simulation/time-travel performance profiling and threshold correction
