# Horus Analytics II Ollama AI Report Lifecycle Implementation Plan

Date: 2026-03-31
Based on:

- `docs/superpowers/specs/2026-03-31-ollama-ai-report-lifecycle-design.md`
- `utils/ollama_manager.py`
- `routes/ai_report.py`
- `core/ai_report/generation.py`
- `core/scheduling.py`
- `frontend/src/app/context/lib/marketTransforms.ts`
- `frontend/src/app/context/hooks/useMarketRuntime.ts`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/hooks/useOracleActions.ts`

Track: On-Demand Ollama Lifecycle for AI Reports
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved Ollama AI report lifecycle design into an implementation sequence that fits the current Horus architecture.

The implementation must leave six things true:

1. Ollama is started only for AI report work, not as a permanent dependency.
2. Manual Oracle AI reports and scheduled AI report broadcasts use the same lifecycle behavior.
3. LLM-backed AI report requests fall back to the existing local rule-based report when Ollama startup, readiness, or inference fails.
4. Ollama shutdown runs after every AI report attempt in a `finally` path.
5. Existing AI report endpoint contracts remain backward compatible while gaining lifecycle metadata.
6. The behavior is covered by focused tests without requiring a live Ollama process in CI.

## 2. In Scope

Primary backend targets:

- `utils/ollama_manager.py`
- new lifecycle seam under `core/ai_report/`
- `routes/ai_report.py`
- `core/scheduling.py`
- targeted backend tests under `tests/`

Primary frontend touchpoints:

- `frontend/src/app/context/lib/marketTransforms.ts`
- `frontend/src/app/context/hooks/useMarketRuntime.ts`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/hooks/useOracleActions.ts`

Primary workflow capabilities to add:

- on-demand Ollama startup for manual AI reports
- on-demand Ollama startup for scheduled AI report broadcasts
- centralized fallback to local rule-based reports
- immediate Ollama shutdown after each report session
- response metadata describing lifecycle and fallback behavior

Out of scope for this phase:

- redesigning the Oracle page UI
- changing non-report Ollama consumers
- implementing a persistent warm Ollama pool
- reworking unrelated AI provider logic outside the report path
- changing report scoring or rule-based recommendation policy

## 3. Current Constraints

These existing facts shape the rollout:

1. `utils/ollama_manager.py` can start Ollama and check readiness, but cannot stop the service.
2. `routes/ai_report.py` currently assumes Ollama is already available when `use_llm=true`.
3. `core/scheduling.py` already calls `ai_report.get_ai_daily_report(...)`, so scheduler integration should reuse the same lifecycle seam rather than duplicate it.
4. `frontend/src/app/context/lib/marketTransforms.ts` already routes Oracle report requests through `GET /api/v1/ai/daily-report`.
5. Existing tests in `tests/test_ai_daily_report.py` monkeypatch route-level seams, so backend changes should preserve those seams or wrap them carefully.
6. The app already treats AI reports as `success` even when the report degrades to the local rule engine after an LLM failure.

The plan must address each of those constraints directly.

## 4. Execution Rules

These rules apply across all work packages:

1. No direct start/stop logic should be duplicated across route handlers and scheduler code.
2. No change should make `LOCAL` rule-based reports depend on Ollama.
3. No Ollama-backed report path may fail completely when a local fallback report can still be produced.
4. No shutdown path may be best-effort only; it must run from a `finally` block after the report session.
5. No test may depend on a real running Ollama service.
6. No frontend Oracle refresh flow should need a new route shape to benefit from the backend lifecycle work.
7. No unrelated Ollama consumers should be silently broken by AI report lifecycle changes.

## 5. Target Module Map

The implementation should converge on this shape.

### Backend lifecycle seams

- `utils/ollama_manager.py`
- new `core/ai_report/lifecycle.py`

### Backend report seams

- `routes/ai_report.py`
- `core/ai_report/generation.py`
- `core/scheduling.py`

### Frontend consumption seams

- `frontend/src/app/context/lib/marketTransforms.ts`
- `frontend/src/app/context/hooks/useMarketRuntime.ts`
- optional Oracle UI metadata seams later if needed

### Test seams

- `tests/test_ai_daily_report.py`
- new `tests/test_ai_report_lifecycle.py`
- optional focused scheduler coverage if existing scheduling tests are insufficient

The route layer should remain the HTTP contract owner. Lifecycle control should move into a reusable backend seam.

## 6. Work Package Sequence

Execute this slice in the following order:

1. `OAR-P1` Ollama manager lifecycle controls
2. `OAR-P2` Shared AI report lifecycle wrapper
3. `OAR-P3` Route integration and payload metadata
4. `OAR-P4` Scheduler integration and fallback delivery behavior
5. `OAR-P5` Frontend consumption polish and closeout

This order is intentional:

- the manager must support stop and readiness control before report orchestration can be built cleanly
- the shared wrapper must exist before routes and scheduler can converge on one behavior
- route integration should stabilize payload semantics before scheduler wiring relies on them
- scheduler work should consume the same wrapper, not invent a second runtime path
- frontend changes should remain thin and consume already-stable payload metadata

## 7. Work Packages

### OAR-P1. Ollama Manager Lifecycle Controls

Purpose:

Extend the existing local Ollama helper so it can support start, readiness wait, and shutdown semantics needed for report-scoped execution.

Target files:

- `utils/ollama_manager.py`
- targeted tests

Tasks:

1. Add `wait_until_ready(timeout_sec)` that polls the existing Ollama HTTP endpoint.
2. Add `stop_service()` with:
   - preferred graceful local shutdown path if feasible
   - controlled fallback termination path if graceful shutdown is unavailable
3. Make startup behavior explicitly synchronous for report-scoped work, even if startup-at-app-boot remains asynchronous elsewhere.
4. Add structured result data or clear boolean/error returns so higher layers can distinguish:
   - already running
   - started successfully
   - startup failed
   - readiness timeout
   - shutdown failed
5. Preserve compatibility for any existing startup-time uses of `ensure_service_running(...)`.

Deliverables:

- lifecycle-capable Ollama manager
- explicit readiness and shutdown behavior

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_ai_report_lifecycle.py -q`

Acceptance criteria:

- manager can detect readiness synchronously
- manager can attempt shutdown deterministically
- existing app startup behavior is not broken

### OAR-P2. Shared AI Report Lifecycle Wrapper

Purpose:

Create one reusable orchestration seam for report-scoped Ollama sessions.

Target files:

- new `core/ai_report/lifecycle.py`
- optional small imports in `core/ai_report/__init__.py`
- targeted tests

Tasks:

1. Add a wrapper that:
   - decides whether a report mode requires Ollama
   - starts Ollama if needed
   - waits for readiness
   - runs the existing LLM report generator callback
   - catches startup/readiness/inference failures
   - falls back to the rule-based report
   - shuts down Ollama in `finally`
2. Keep the wrapper generic enough to be called by:
   - manual AI report generation
   - scheduled report broadcast
3. Return structured lifecycle metadata such as:
   - `report_mode`
   - `ollama_start_attempted`
   - `ollama_ready`
   - `ollama_shutdown_attempted`
   - `ollama_shutdown_ok`
   - `ollama_lifecycle_reason`
4. Ensure fallback remains a `success` payload when a rule-based report is available.

Deliverables:

- one shared lifecycle orchestration seam
- structured lifecycle metadata contract

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_ai_report_lifecycle.py -q`

Acceptance criteria:

- manual and scheduled callers can share one lifecycle implementation
- fallback behavior is centralized and testable

### OAR-P3. Route Integration and Payload Metadata

Purpose:

Wire the shared lifecycle wrapper into the existing AI report route flow while preserving current route contracts.

Target files:

- `routes/ai_report.py`
- `core/ai_report/generation.py` if small callback shaping changes are required
- `tests/test_ai_daily_report.py`

Tasks:

1. Route LLM-backed AI report requests through the shared lifecycle wrapper.
2. Keep local-only requests on the existing rule-based path without starting Ollama.
3. Preserve current response fields like:
   - `status`
   - `source`
   - `source_module`
   - `degraded`
   - `fallback_reason`
4. Add lifecycle metadata fields to successful payloads.
5. Preserve existing route-level monkeypatch seams where tests depend on them.
6. Ensure `broadcast_ai_daily_report(...)` continues to accept the same request shape.

Deliverables:

- route-level lifecycle integration
- backward-compatible AI report response shape with richer metadata

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_ai_daily_report.py -q`

Acceptance criteria:

- existing AI report routes remain stable for consumers
- Ollama is only touched for LLM-backed requests
- fallback-to-local remains a successful report response

### OAR-P4. Scheduler Integration and Fallback Delivery Behavior

Purpose:

Make scheduled AI report dispatch use the same Ollama lifecycle and fallback behavior as manual requests.

Target files:

- `core/scheduling.py`
- `routes/ai_report.py` if small helper reuse is needed
- targeted tests

Tasks:

1. Ensure `scheduled_daily_ai_report_dispatch()` uses the same lifecycle-backed AI report generation flow.
2. Keep Telegram delivery semantics unchanged:
   - if a final valid report exists, send it
   - only fail the job on invalid final payload or Telegram delivery failure
3. Preserve useful logging on:
   - startup attempted
   - startup failed
   - fallback used
   - shutdown attempted
   - shutdown failed
4. Verify scheduler behavior when Ollama:
   - starts and succeeds
   - fails to start
   - times out
   - generates and then shutdown fails

Deliverables:

- scheduler path using shared lifecycle behavior
- safe fallback delivery for scheduled AI reports

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_ai_report_lifecycle.py tests/test_ai_daily_report.py -q`

Acceptance criteria:

- scheduled broadcasts do not need a separate Ollama management path
- fallback report still broadcasts when Ollama is unavailable

### OAR-P5. Frontend Consumption Polish and Closeout

Purpose:

Consume the new lifecycle metadata cleanly and finish the package with targeted tests and documentation updates if needed.

Target files:

- `frontend/src/app/context/lib/marketTransforms.ts`
- `frontend/src/app/context/hooks/useMarketRuntime.ts`
- optional Oracle UI files only if metadata display is added
- frontend tests only if any payload shape assumptions need updates

Tasks:

1. Ensure frontend report fetching tolerates the new metadata without regressions.
2. Optionally expose simple lifecycle-aware language later, such as:
   - `Generated with Ollama`
   - `Fell back to local report`
3. Keep Oracle user actions unchanged:
   - refresh
   - regenerate
   - broadcast
4. Run the relevant frontend tests if any payload consumption changed.

Deliverables:

- frontend compatibility with enriched AI report payloads
- stable Oracle refresh and broadcast flows

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns "src/app/oracle|src/app/context"`

Acceptance criteria:

- no Oracle frontend regression from the backend lifecycle change
- lifecycle metadata can be consumed without UI breakage

## 8. Test Strategy

The implementation should add a focused lifecycle test layer instead of scattering process-control assertions everywhere.

### Backend lifecycle coverage

Required scenarios:

1. startup succeeds, LLM report succeeds, shutdown runs
2. startup fails, rule-based fallback succeeds, shutdown remains safe
3. readiness timeout, rule-based fallback succeeds
4. LLM generation failure, rule-based fallback succeeds
5. scheduler broadcast succeeds with a fallback report when Ollama fails
6. shutdown failure is logged and surfaced in metadata but does not erase a valid report result

### Route contract coverage

Keep current route-level AI report tests green while extending them to cover:

- lifecycle metadata fields on success
- lifecycle metadata fields on fallback

### Frontend coverage

Only add frontend tests if payload shape handling changes in the Oracle/client runtime.

## 9. Rollout Notes

Important implementation notes:

1. Preserve the current route-level monkeypatch seams in `tests/test_ai_daily_report.py`.
2. Keep the new lifecycle wrapper behind small backend seams so future non-report Ollama consumers can choose whether to adopt it.
3. Do not let scheduler code become a second orchestration owner.
4. Keep `LOCAL` mode fast and free of any Ollama startup overhead.
5. Prefer deterministic logging and structured metadata over silent process behavior.

## 10. Success Criteria

This package is successful when:

1. manual AI reports can trigger Ollama on demand
2. scheduled AI reports can trigger Ollama on demand
3. rule-based fallback still delivers usable reports when Ollama is unavailable
4. Ollama is shut down after each AI report job
5. the route and scheduler paths use one shared lifecycle implementation
6. the behavior is covered by focused backend tests and does not require a permanently running local Ollama service
