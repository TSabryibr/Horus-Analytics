# Packaged Startup Idle Sync Design

Date: 2026-04-07
Status: Approved for planning

## Goal

Make the packaged Horus application behave predictably after market close:

- run one startup sync
- serve the API normally
- stay idle until the next market open

This behavior must not depend on whether the frontend browser is opened, and it must remain stable even when `.env` contains `SESSION_MODE=LIVE`.

## Problem Summary

The current packaged startup path can produce conflicting runtime signals:

- the browser prompt only controls whether `http://localhost:8000` is opened
- backend services still start even when the user answers `N`
- `.env` can force `SESSION_MODE=LIVE`
- the adaptive sync worker may continue retry behavior after market close

This leads to confusing logs and unnecessary after-hours sync activity.

## Desired Behavior

For packaged runs started after market close:

1. Start the API and scheduler normally.
2. Resolve the effective runtime mode from current market time.
3. Run one startup sync pass.
4. Persist the resulting worker state honestly, even if still degraded.
5. Enter a closed-session idle state.
6. Resume live worker behavior only when the next market-open window begins.

For packaged runs started during market hours:

- use normal live monitoring behavior

For source and development runs:

- preserve the existing ability to force session behavior for testing

## Design Principles

- One source of truth: startup computes one effective mode and the rest of the system uses it.
- Calm after-hours behavior: one sync attempt, then rest.
- Honest state reporting: degraded after-hours is acceptable if the sync completed.
- Clear overrides: forcing a mode should require an intentional stronger signal than a plain default.
- Browser independence: browser launch choice must never control backend sync behavior.

## Proposed Runtime Model

### Configured Mode vs Effective Mode

Introduce a clear separation:

- `configured_session_mode`: what config or environment says
- `effective_session_mode`: what this runtime should actually use

Rules:

- packaged runs default to market-time auto-detection
- source/dev runs may continue honoring `SESSION_MODE`
- packaged runs ignore a plain `SESSION_MODE=LIVE` default unless an explicit force flag is present
- an explicit force flag such as `SESSION_MODE_FORCE=1` can override auto-detection when needed

Packaged launch precedence:

| Priority | Input | Rule |
|---|---|---|
| 1 | explicit force flag | if `SESSION_MODE_FORCE=1`, honor the resolved configured mode exactly |
| 2 | packaged auto-detection | if no force flag is present, derive `effective_session_mode` from current market status |
| 3 | configured session value | used for logging and persistence as `configured_session_mode`, but not as the effective mode for packaged runs unless forced |

Configured mode resolution:

- resolve the configured mode from the same existing config chain the app already uses
- if multiple config sources exist, the existing app precedence remains in force
- the new design does not introduce a second competing config precedence model; it only defines how packaged startup converts the resolved configured value into an effective runtime mode
- invalid configured values should be normalized to the current safe default before the packaged precedence rules are applied

### Mode Contract

`ANALYSIS` remains a real session mode value used by the runtime, not just a descriptive label.

The distinction is:

- `configured_session_mode`: raw configured preference
- `effective_session_mode`: resolved runtime session mode for this launch
- worker lifecycle state: the worker's current operating phase

Mode-to-state mapping:

| Effective session mode | Worker lifecycle state at boot | Meaning |
|---|---|---|
| `LIVE` | `LIVE_MONITORING` | Market-hours behavior with normal freshness maintenance |
| `ANALYSIS` after close, before startup sync completes | `STARTUP_SYNC` | Closed-session catch-up sync is running |
| `ANALYSIS` after close, after startup sync completes | `IDLE_CLOSED_SESSION` | Closed-session idle until next market open |
| any mode during bootstrap before resolution | `BOOTING` | Startup has not resolved behavior yet |

This keeps the contract stable:

- session mode answers "what kind of market session are we in?"
- worker state answers "what is the worker doing right now?"

### Worker States

The adaptive sync worker should use a small, explicit state model:

- `BOOTING`
- `STARTUP_SYNC`
- `IDLE_CLOSED_SESSION`
- `LIVE_MONITORING`

This is a conceptual runtime model. Internal persisted values can remain compatible with current payloads, but the behavior should map cleanly to these states.

## Startup Flow

### Packaged Run After Market Close

1. Load configuration and market schedule.
2. Compute `effective_session_mode=ANALYSIS`.
3. Log configured mode, force state, effective mode, and reason.
4. Start API and scheduler.
5. Start the adaptive sync worker in startup mode.
6. Run one sync pass.
7. Re-evaluate freshness.
8. Persist final state:
   - `FRESH` if thresholds pass
   - `DEGRADED` if thresholds still miss
   - `DEGRADED` with error details if sync threw
9. Enter `IDLE_CLOSED_SESSION`.
10. Sleep until the next market-open boundary.

Boundary-crossing rule:

- if the market opens while the one-time startup sync is still running, the sync is allowed to finish
- immediately after that sync completes, the worker must re-check market-open status before entering closed-session idle
- if the market is now open, transition directly to `LIVE_MONITORING` instead of `IDLE_CLOSED_SESSION`
- if the market is still closed, proceed to closed-session idle as originally planned

This avoids missing the open window because of a startup race.

### Packaged Run During Market Hours

1. Compute `effective_session_mode=LIVE`.
2. Start normal worker behavior.
3. Continue freshness maintenance and market-hour retries as usual.

## Closed-Session Rules

After market close, packaged startup must follow these rules:

- exactly one startup sync attempt
- no repeated retry loop after that attempt
- degraded status is allowed and should be reported without triggering after-hours retry churn
- actual sync exceptions should be logged and persisted, but should still end in closed-session idle
- the next retry opportunity is the next market-open transition, not a short backoff timer

### Wake Ownership and Restart Rules

Wake responsibility should be owned by one place only: the adaptive sync worker.

Rules:

- the scheduler may continue managing normal market-hour jobs
- the worker owns the closed-session wait loop and the decision to resume active sync behavior
- the worker wakes by re-checking the market-open boundary, not by creating a second retry timer system
- on process restart after close, startup repeats the same rule set: one sync attempt, then idle
- if the process is interrupted while idle, no special recovery is required beyond normal startup evaluation on the next launch
- if the process is interrupted during the startup sync, the next launch performs a fresh closed-session startup evaluation and one new sync attempt

This avoids duplicate ownership between scheduler and worker logic.

### Calendar and Boundary Failure Handling

If market-schedule lookup or next-open boundary computation fails, packaged startup should fail safe in a bounded way.

Fallback rules:

- if market status cannot be resolved at boot at all, default to fail-closed behavior:
  - set `effective_session_mode=ANALYSIS`
  - do not enter live monitoring
  - do not schedule repeated sync retries
  - use coarse periodic market-status re-checks until resolution is available
- if current market-open status can still be determined, use that to resolve `effective_session_mode`
- if next-open timestamp cannot be computed after a closed-session sync, persist closed-session idle intent and fall back to periodic coarse re-checks using the existing market-open predicate
- the fallback re-check interval should be conservative, such as hourly, and must not trigger repeated sync attempts while the market remains closed
- the failure should be logged explicitly as a schedule-resolution warning, not silently downgraded

This keeps after-hours behavior calm even when calendar helpers are imperfect.

## Logging and Observability

Startup logs should make the decision path obvious. Example:

```text
[Startup] Session mode config=LIVE forced=false effective=ANALYSIS reason=market_closed
[SyncWorker] Closed-session startup sync beginning.
[SyncWorker] Closed-session startup sync completed with state=DEGRADED. Idling until market reopens.
```

Persisted worker state should include, either directly or via compatible extensions:

- `configured_session_mode`
- `effective_session_mode`
- `forced_mode`
- `closed_session_idle`
- `next_wake_reason`
- `last_startup_sync_result`

This is meant to make debugging possible without reconstructing behavior from scattered logs.

### Worker-State Compatibility Contract

Worker-state extensions must be additive.

Compatibility rules:

- existing required fields keep their current names and meanings
- new fields are optional for older readers
- readers that do not understand new fields must still be able to parse the payload and rely on existing fields
- no existing field should be repurposed to mean both session mode and worker lifecycle state

Minimum bounded schema expectation for new fields:

- `configured_session_mode`: string
- `effective_session_mode`: string
- `forced_mode`: boolean
- `closed_session_idle`: boolean
- `next_wake_reason`: one of `market_open`, `coarse_market_recheck`, or `null`
- `last_startup_sync_result`: one of `fresh`, `degraded`, `error`, or `null`

This gives implementation planning a clear compatibility target without requiring a breaking state-file redesign.

## Compatibility Notes

- Existing browser prompt behavior should remain unchanged.
- Existing scheduler jobs may remain registered, but after-hours worker behavior should no longer rely on retry backoff.
- Existing source/dev workflows that intentionally force session mode should keep working.
- Current worker-state consumers should remain compatible where possible.

## Testing Strategy

Add or update tests to cover:

- packaged startup after close resolves to `effective_session_mode=ANALYSIS` even if `.env` says `SESSION_MODE=LIVE`
- after-hours packaged startup runs exactly one sync
- after-hours packaged startup idles even when freshness remains degraded
- after-hours packaged startup idles even when the sync raises an exception
- market open wakes the worker and resumes live behavior
- explicit forced-mode override still wins when intentionally enabled
- browser prompt choice does not change backend sync behavior

## Recommended Implementation Shape

Keep the change focused and localized:

- add a startup mode-resolution helper
- use that helper during packaged startup before post-ready services begin
- normalize worker behavior around closed-session idle semantics
- extend logging and worker-state payloads for clarity

Do not introduce a second broad configuration system if a small force flag and effective-mode resolver are enough.

## Risks

- If mode resolution is scattered across startup and worker code, the app can still produce conflicting states.
- If after-hours degraded status is treated as retryable freshness debt, the retry loop can reappear.
- If packaged and source runs are not distinguished clearly, development workflows may regress.

## Recommendation

Adopt packaged-run auto-detection as the default, keep explicit force behavior available, and define closed-session packaged startup as:

- one sync
- honest final state
- idle until next market open

This best matches the approved product behavior and keeps logs, scheduler behavior, and worker behavior aligned.
