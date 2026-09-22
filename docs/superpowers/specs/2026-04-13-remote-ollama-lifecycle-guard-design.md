# Remote Ollama Lifecycle Guard Design

## Goal

When `OLLAMA_BASE_URL` points to a non-local address, Horus must not start or stop a local `ollama serve` process on the current machine.

## Problem

The AI report lifecycle currently assumes every Ollama endpoint is local. It always:

- attempts `ensure_service_running()`
- waits for readiness
- calls `stop_service()` in the cleanup path

That behavior is safe for `localhost` workflows, but wrong for remote Ollama deployments because a remote HTTP endpoint should be treated as an external dependency, not as a process Horus manages locally.

## Scope

This change is limited to the AI report Ollama lifecycle path:

- `routes/ai_report.py`
- `core/ai_report/lifecycle.py`
- `utils/ollama_manager.py`
- focused tests for local vs remote behavior

No unrelated Ollama refactors are included.

## Proposed Behavior

### Local endpoints

If `OLLAMA_BASE_URL` resolves to a local host, Horus keeps the current behavior:

- auto-start local Ollama when needed
- wait for readiness
- run report generation
- stop the managed local Ollama service afterward

Local hosts are:

- `127.0.0.1`
- `localhost`
- `::1`
- empty host values that resolve to the local default

### Remote endpoints

If `OLLAMA_BASE_URL` resolves to any non-local host, Horus must:

- skip `ensure_service_running()`
- skip `stop_service()`
- only call the configured remote Ollama endpoint
- report readiness/generation failures based on the remote endpoint response only

This makes Horus a client of the remote Ollama instance rather than a lifecycle manager for a local one.

## Design

### 1. Add locality detection

Introduce a small host check that classifies the configured Ollama base URL as local or remote.

Requirements:

- parse the URL safely
- normalize host casing
- treat loopback names/addresses as local
- treat all other hosts as remote

### 2. Gate lifecycle management

Update the report-session lifecycle so that lifecycle management is conditional:

- local host: current start/wait/stop flow
- remote host: no start or stop attempts

The metadata should continue to be populated, but for remote hosts it should reflect that no local lifecycle action was attempted.

### 3. Preserve current call surface

Callers should not need broad rewrites. The lifecycle should continue to expose the same result shape so the surrounding route logic remains stable.

## Testing

Add focused tests that cover:

1. local base URL still attempts startup and shutdown
2. remote base URL does not attempt startup
3. remote base URL does not attempt shutdown
4. remote readiness/generation failures surface normally without local process management

## Risks

- misclassifying a host as local could still trigger unwanted process management
- misclassifying a local alias as remote could disable expected local convenience behavior

The tests should explicitly lock the main supported local host variants.

## Acceptance Criteria

- non-local `OLLAMA_BASE_URL` never starts `ollama serve` locally
- non-local `OLLAMA_BASE_URL` never stops local `ollama.exe`
- local `OLLAMA_BASE_URL` keeps current lifecycle behavior
- targeted AI report tests pass
