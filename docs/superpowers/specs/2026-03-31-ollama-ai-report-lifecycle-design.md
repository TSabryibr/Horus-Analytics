# Horus Analytics II Ollama AI Report Lifecycle Design

Date: 2026-03-31
Status: Proposed
Authoring mode: Brainstorming-approved design

Based on:

- `utils/ollama_manager.py`
- `routes/ai_report.py`
- `core/ai_report/generation.py`
- `core/scheduling.py`
- `frontend/src/app/context/lib/marketTransforms.ts`
- `frontend/src/app/context/hooks/useMarketRuntime.ts`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/hooks/useOracleActions.ts`

## 1. Purpose

This design makes Ollama an internal, report-scoped worker used only for Horus AI report generation.

The intended behavior is:

- start Ollama only when Horus needs an AI report
- use Ollama only for that report job
- fall back to the existing local rule-based report if Ollama startup or generation fails
- shut Ollama down immediately after the report is generated or delivered

This applies to both:

- manual AI report requests from the Oracle workflow
- scheduled AI report broadcasts

## 2. Product Outcome

After this change, the operator experience should be:

1. Request an AI report from the app, or let the scheduled AI report dispatch run.
2. Horus starts Ollama on demand if needed.
3. Horus generates the report with Ollama when available.
4. If Ollama cannot be started or used successfully, Horus still returns or broadcasts the rule-based report.
5. Horus shuts Ollama down after the report completes.

The user should never have to manage Ollama manually for normal AI report use.

## 3. Design Goals

This package should leave five things true:

1. Ollama is no longer treated as a permanently running dependency for AI reports.
2. Horus owns the Ollama lifecycle for AI report generation end-to-end.
3. Manual and scheduled AI report flows behave the same way.
4. Failures in Ollama startup or inference degrade gracefully to the current rule-based report.
5. Ollama shutdown happens reliably after each report attempt to save local resources.

## 4. Non-Goals

This change does not attempt to:

- redesign Oracle page UI beyond exposing clearer report metadata later
- change non-report Ollama consumers elsewhere in the codebase
- introduce a general-purpose process supervisor for all local AI services
- keep Ollama warm across multiple requests
- support user-managed shared Ollama sessions

## 5. Current State

The existing AI report flow already converges in a small number of places:

- manual report generation:
  - `frontend/src/app/context/lib/marketTransforms.ts`
  - `frontend/src/app/context/hooks/useMarketRuntime.ts`
  - `routes/ai_report.py`
- scheduled report broadcast:
  - `core/scheduling.py`
  - `routes/ai_report.py`

The current local Ollama lifecycle helper already exists in:

- `utils/ollama_manager.py`

It can:

- detect whether the Ollama HTTP service is reachable
- start `ollama serve`
- verify whether a model exists and pull it asynchronously if needed

It does not currently:

- stop the Ollama service
- wrap one report request in a start/generate/stop lifecycle
- expose lifecycle metadata to the report payload

The current AI report generator in `routes/ai_report.py` and `core/ai_report/generation.py` assumes Ollama is already reachable when `use_llm=true`.

## 6. User-Approved Runtime Policy

The approved behavior for this package is:

- Horus starts and stops Ollama for:
  - manual AI report requests
  - scheduled AI report broadcasts
- if Ollama fails to start or becomes unavailable:
  - Horus falls back to the existing local rule-based report
- Horus shuts Ollama down immediately after each report
- Ollama is treated as an internal Horus report worker only, not as a user-shared service

This means Horus is allowed to stop Ollama whenever a report session ends.

## 7. Recommended Approach

Three approaches were considered:

### Option 1. Central report-scoped Ollama lifecycle manager

Use one shared lifecycle wrapper around AI report generation.

Pros:

- one implementation path for manual and scheduled report flows
- easiest place to enforce start, fallback, and shutdown policy
- easier to test than route-level duplication

Cons:

- requires extending the existing manager and threading lifecycle metadata through the AI report path

### Option 2. Route-level lifecycle wiring

Put start and stop logic directly in report routes and scheduler code.

Pros:

- smaller initial edits in each call site

Cons:

- duplicated behavior
- higher chance that manual and scheduled flows drift over time

### Option 3. Background worker queue

Move AI reports to a dedicated worker that manages Ollama for each job.

Pros:

- strongest centralization for a future multi-job AI system

Cons:

- too much infrastructure for the current problem

### Recommendation

Use Option 1: a central report-scoped lifecycle wrapper shared by both manual and scheduled AI report generation.

## 8. Architecture

Add one report-lifecycle orchestration layer around the existing AI report generation path.

### 8.1 Core units

#### A. Ollama lifecycle manager

Extend `utils/ollama_manager.py` with:

- `wait_until_ready(timeout_sec)`
- `stop_service()`
- a small session-scoped helper such as `run_managed_report_session(...)` or equivalent orchestration primitives

Responsibilities:

- detect running service
- start service if needed
- wait for readiness
- stop service after report completion
- emit structured lifecycle outcomes

#### B. AI report lifecycle wrapper

Add a shared wrapper near the AI report implementation, preferably under `core/ai_report/` rather than embedding orchestration into routes.

Responsibilities:

- decide whether a request needs Ollama
- invoke lifecycle manager
- call the existing LLM report generator
- catch startup/readiness/generation failures
- fall back to the rule-based report
- return lifecycle metadata alongside the report payload

#### C. Report callers

Keep the existing callers thin:

- `routes/ai_report.py`
- `core/scheduling.py`

Responsibilities:

- request report generation
- deliver or return the resulting payload
- avoid managing Ollama directly

## 9. Lifecycle Flow

For an Ollama-backed AI report request:

1. Caller requests report generation with `use_llm=true` or `provider=OLLAMA`.
2. Lifecycle wrapper checks whether the report mode requires Ollama.
3. Horus ensures Ollama is running.
4. Horus waits until the Ollama HTTP endpoint is responsive or timeout expires.
5. Horus runs the existing LLM report generation path.
6. If startup/readiness/inference fails, Horus falls back to the current local rule-based report.
7. In a `finally` block, Horus stops Ollama.
8. The report payload includes lifecycle metadata describing what happened.

For local-only AI report requests:

- Horus skips Ollama entirely
- the existing local rule-based path runs unchanged

## 10. API and Payload Behavior

The AI report API should remain backward-compatible in shape, but add metadata that makes the lifecycle visible.

### 10.1 Existing endpoints affected

- `GET /api/v1/ai/daily-report`
- `POST /api/v1/ai/daily-report/broadcast`
- scheduled AI report dispatch in `core/scheduling.py`

### 10.2 Proposed response metadata additions

Add fields like:

- `report_mode: "LOCAL" | "OLLAMA" | "OLLAMA_FALLBACK"`
- `ollama_start_attempted: bool`
- `ollama_ready: bool`
- `ollama_shutdown_attempted: bool`
- `ollama_shutdown_ok: bool`
- `ollama_lifecycle_reason: str | null`

Example values:

- successful LLM report:
  - `report_mode = "OLLAMA"`
  - `source_module = "OLLAMA"`
  - `degraded = false`
- startup timeout:
  - `report_mode = "OLLAMA_FALLBACK"`
  - `source_module = "LOCAL"`
  - `degraded = true`
  - `fallback_reason = "ollama_start_timeout"`
- inference failure:
  - `report_mode = "OLLAMA_FALLBACK"`
  - `source_module = "LOCAL"`
  - `degraded = true`
  - `fallback_reason = "ollama_generation_failed"`

The current `degraded`, `fallback_reason`, and `source_module` semantics should remain intact.

## 11. Scheduler Behavior

The scheduled daily AI report dispatch should use exactly the same lifecycle wrapper as manual requests.

Requirements:

- scheduled dispatch attempts Ollama only when using the LLM path
- if Ollama fails, the local rule-based report is still broadcast
- the scheduler only fails the job when:
  - final payload generation is invalid
  - Telegram delivery itself fails

This keeps the scheduling behavior operationally safe even when Ollama is unavailable.

## 12. Shutdown Mechanics

The shutdown path is mandatory and must run in a `finally` block.

Primary behavior:

- use a graceful local shutdown strategy when possible
- if that is not available, use a controlled fallback process termination strategy

Because Ollama is treated as an internal Horus-only report worker in this design, shutting it down after every report is expected behavior rather than a coexistence compromise.

Every shutdown attempt should be logged with:

- whether shutdown was attempted
- whether shutdown succeeded
- if shutdown failed, the reason

## 13. Error Handling

### 13.1 Startup failure

If Ollama cannot be started:

- log the startup failure
- generate the local rule-based report
- return success with degraded metadata
- attempt shutdown cleanup only if a partial startup occurred

### 13.2 Readiness timeout

If Ollama starts but does not become reachable in time:

- log readiness timeout
- generate the local rule-based report
- return success with degraded metadata
- stop Ollama

### 13.3 LLM generation failure

If Ollama is reachable but report generation fails:

- log inference failure
- generate the local rule-based report
- return success with degraded metadata
- stop Ollama

### 13.4 Shutdown failure

If Ollama report generation succeeds but shutdown fails:

- keep the report result as success
- include shutdown failure in logs and lifecycle metadata
- do not convert the report itself into a failed request

## 14. Frontend Impact

The frontend does not need a structural redesign for phase 1.

Manual Oracle report flow can keep the same user actions:

- refresh current AI report
- regenerate with Ollama
- broadcast AI report

The main useful enhancement later is to surface lifecycle-aware status text such as:

- `Generated with Ollama`
- `Fell back to local report because Ollama was unavailable`

That UI change is optional for the first implementation slice and should not block the backend lifecycle work.

## 15. Testing Strategy

Add focused backend lifecycle coverage rather than rewriting the whole AI report test stack.

### 15.1 Required unit/integration tests

- startup succeeds, LLM report succeeds, shutdown runs
- startup fails, local fallback report is returned, shutdown logic remains safe
- readiness timeout returns local fallback report
- LLM inference failure returns local fallback report
- scheduled broadcast still sends fallback report when Ollama fails
- shutdown failure is logged and surfaced in metadata without losing the report result

### 15.2 Mocking strategy

Do not require a live Ollama process in automated tests.

Mock:

- lifecycle manager start/readiness/shutdown methods
- LLM generation call path
- Telegram delivery where needed

Keep the tests centered on behavior and final payloads, not process implementation details.

## 16. Rollout Plan

Implement in this order:

1. Extend `utils/ollama_manager.py` with stop and readiness control.
2. Add a shared AI report lifecycle wrapper under `core/ai_report/`.
3. Route manual AI report generation through the wrapper.
4. Route scheduled AI report dispatch through the same wrapper.
5. Add lifecycle metadata to response payloads.
6. Add tests for startup, fallback, shutdown, and scheduler behavior.
7. Optionally surface lifecycle status in the Oracle UI.

## 17. Success Criteria

This package is successful when:

1. Manual AI reports can trigger Ollama on demand.
2. Scheduled AI reports can trigger Ollama on demand.
3. Rule-based fallback still delivers usable reports when Ollama is unavailable.
4. Ollama is shut down after each AI report job.
5. The behavior is covered by tests and does not rely on a permanently running local Ollama service.
