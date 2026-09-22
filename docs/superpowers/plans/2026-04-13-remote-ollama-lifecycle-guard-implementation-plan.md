# Remote Ollama Lifecycle Guard Implementation Plan

Date: 2026-04-13
Based on:

- `docs/superpowers/specs/2026-04-13-remote-ollama-lifecycle-guard-design.md`
- `routes/ai_report.py`
- `core/ai_report/lifecycle.py`
- `utils/ollama_manager.py`
- `tests/test_ai_daily_report.py`

Track: AI Report Ollama Lifecycle Safety
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Implement the approved Ollama lifecycle guard so Horus:

1. continues to auto-manage Ollama for local loopback endpoints
2. never starts or stops a local Ollama process when `OLLAMA_BASE_URL` targets a remote host
3. preserves the existing AI report call surface and error reporting
4. verifies the local-vs-remote contract with focused automated tests

## 2. In Scope

Primary implementation targets:

- Ollama endpoint locality detection
- AI report lifecycle gating for local vs remote Ollama endpoints
- targeted test coverage for local and remote lifecycle behavior

Primary files expected to move:

- `utils/ollama_manager.py`
- `core/ai_report/lifecycle.py`
- `routes/ai_report.py`
- `tests/test_ai_daily_report.py`

Out of scope for this slice:

- changing non-AI-report Ollama consumers
- redesigning Ollama settings UI or configuration storage
- broad Ollama process-management refactors beyond the guard required here
- unrelated AI report generation logic changes

## 3. Execution Rules

These rules apply across the slice:

1. Treat host classification as the root contract; do not scatter ad hoc localhost checks across multiple call sites.
2. Preserve the current route and lifecycle return shapes so callers do not need unrelated rewrites.
3. Keep local developer convenience intact for loopback hosts.
4. Make remote behavior explicit in lifecycle metadata rather than relying on implied skipped calls.
5. Verify both local and remote paths with focused tests before considering the slice complete.

## 4. Work Package Sequence

Execute in this order:

1. `ROLG-P1` Endpoint locality contract
2. `ROLG-P2` Lifecycle management guard
3. `ROLG-P3` Regression lock and verification

This order is intentional:

- the locality decision needs one canonical implementation before lifecycle code can depend on it
- lifecycle gating should land before route-level cleanup or metadata expectations are adjusted
- tests should lock the contract after the runtime behavior is in place

## 5. Work Packages

### ROLG-P1. Endpoint Locality Contract

Purpose:

Introduce one reusable, explicit way to decide whether an Ollama base URL is local or remote.

Target files:

- `utils/ollama_manager.py`

Tasks:

1. Add a safe base-URL host parser that normalizes casing and trailing slash behavior.
2. Introduce a locality helper that treats `127.0.0.1`, `localhost`, `::1`, and empty/default loopback hosts as local.
3. Treat all non-loopback hosts as remote.
4. Expose the result in a way the AI report lifecycle can consume without duplicating parsing logic.

Deliverables:

- canonical local-vs-remote Ollama classification helper
- stable host normalization behavior for Ollama base URLs

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_ai_daily_report.py -k "ollama" -q`

Acceptance criteria:

- one shared helper determines locality
- loopback host variants classify as local
- non-loopback hosts classify as remote

### ROLG-P2. Lifecycle Management Guard

Purpose:

Apply the locality contract so only local Ollama endpoints are process-managed.

Target files:

- `core/ai_report/lifecycle.py`
- `routes/ai_report.py`
- `utils/ollama_manager.py`

Tasks:

1. Update the lifecycle flow to gate `ensure_service_running()` behind the local-endpoint contract.
2. Update cleanup so `stop_service()` is skipped for remote endpoints.
3. Preserve readiness checks and generation behavior for remote endpoints by probing the configured endpoint directly.
4. Keep metadata shape stable while making remote lifecycle skips explicit in the recorded flags and reason fields.
5. Confirm the route-level manager construction passes the required endpoint context into the lifecycle cleanly.

Deliverables:

- guarded AI report Ollama lifecycle for remote endpoints
- stable route integration with unchanged request/response surface
- metadata that accurately reflects skipped local lifecycle operations

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_ai_daily_report.py -k "provider_key_test_endpoint or ollama" -q`

Acceptance criteria:

- remote `OLLAMA_BASE_URL` does not attempt local startup
- remote `OLLAMA_BASE_URL` does not attempt local shutdown
- local `OLLAMA_BASE_URL` retains current startup and shutdown behavior
- AI report route behavior stays intact

### ROLG-P3. Regression Lock and Verification

Purpose:

Lock the new safety behavior with focused tests so future AI report refactors do not reintroduce local process management for remote endpoints.

Target files:

- `tests/test_ai_daily_report.py`

Tasks:

1. Add a local-endpoint test proving startup and shutdown are still attempted for loopback hosts.
2. Add a remote-endpoint test proving startup is skipped.
3. Add a remote-endpoint test proving shutdown is skipped.
4. Add or update a failure-path test showing remote readiness or generation errors still surface normally.

Deliverables:

- focused regression tests for the remote lifecycle guard

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_ai_daily_report.py -q`

Acceptance criteria:

- the targeted AI report suite passes
- the remote lifecycle contract is covered by explicit tests, not inference

## 6. Risks and Controls

Risk: URL parsing misclassifies uncommon loopback forms.
Control: keep the helper small, explicit, and covered by direct tests for supported local variants.

Risk: remote lifecycle skips accidentally bypass readiness validation entirely.
Control: preserve the readiness probe against the configured endpoint even when local process management is skipped.

Risk: metadata consumers assume startup and shutdown are always attempted.
Control: keep the metadata shape unchanged and only vary the boolean values and reason semantics.

## 7. Recommended Execution Notes

- Keep the locality decision close to `OllamaManager` so other Ollama consumers can reuse it later without duplicated parsing.
- Avoid broad manager refactors; the approved slice only needs enough structure to support local-vs-remote lifecycle gating.
- Treat the route import and manager construction as integration seams, not redesign targets.

## 8. Recommended Next Move After This Plan

Start with `ROLG-P1` plus `ROLG-P2`: add the locality helper in `utils/ollama_manager.py`, thread that contract into `core/ai_report/lifecycle.py`, and keep the route integration in `routes/ai_report.py` minimal. Then finish with `ROLG-P3` by locking the behavior in `tests/test_ai_daily_report.py`.
