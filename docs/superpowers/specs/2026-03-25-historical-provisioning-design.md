# Horus Analytics II Historical Provisioning Design

Date: 2026-03-25
Based on:

- `HistoricalBackfill.py`
- `api.py`
- `routes/analysis_reports.py`
- `frontend/src/app/settings/hooks/useSettingsOperations.ts`
- `frontend/src/app/settings/components/SettingsOperationsSection.tsx`

Track: Startup Reliability And Report Quality
Status: Proposed design
Owner model: Single owner

## 1. Goal

Replace the current thin `30`-day manual historical backfill with an automatic first-run provisioning flow that builds enough real signal history to support richer weekly and monthly reports.

The new default should optimize for report quality rather than startup speed:

- replay `252` trading days of daily signal generation
- derive weekly and monthly report context from that daily history
- mark the system `READY` only after provisioning completes successfully

The system should stay honest during startup: reachable, visible, and explicit about being in provisioning rather than pretending to be fully ready.

## 2. Scope

Primary backend areas affected:

- `HistoricalBackfill.py`
- `api.py`
- status / readiness helpers already used by startup and health routes
- report-generation logic in `routes/analysis_reports.py`

Primary frontend areas affected:

- settings operations state and copy
- status surfaces that describe startup state and readiness

Primary behavior changes:

- backfill target changes from `30` calendar days to `252` trading days
- backfill runs automatically on first clean boot or after a hard reset
- readiness stays false until provisioning finishes
- weekly and monthly reports summarize richer daily replay history

Out of scope:

- creating separate weekly or monthly signal engines
- adding a second backfill store for weekly or monthly data
- redesigning report pages
- changing trade or signal scoring logic

## 3. Current Problems

The current implementation has four gaps that directly limit report quality:

1. `HistoricalBackfill.py` replays only `30` calendar days, which yields too few actual EGX trading sessions.
2. Backfill is manual from Settings, so a fresh system can claim readiness before it has enough historical signal coverage.
3. Weekly and monthly reports in `routes/analysis_reports.py` rely on daily `SignalRun`, `SignalOutcome`, and recommendation history, so thin daily replay leads to thin report quality.
4. The Settings UI still frames backfill as an optional repair step instead of part of initial system provisioning.

## 4. Recommended Architecture

Use one stronger historical provisioning pipeline instead of three separate backfill systems.

### Core principle

Daily replay remains the single source of truth for:

- `SignalRun`
- `SignalRecommendation`
- `SignalOutcome`
- legacy `Signal` fallback coverage

Weekly and monthly reports continue to summarize daily history. They do not require their own weekly or monthly replay engines.

### Provisioning target

The automatic provisioning pass should replay:

- `252` trading days of daily market analysis for report-quality signal history

Additional report context should be derived, not stored separately:

- roughly `52` weeks of benchmark context
- roughly `24` months of benchmark context

This context should come from daily OHLC data already managed by the system and should be computed inside report generation or a small report-context helper.

## 5. Startup And Readiness Flow

Fresh-start or post-reset startup should follow this order:

1. process starts normally
2. database is created and initialized
3. startup detects whether historical provisioning is required
4. if required, system enters `PROVISIONING`
5. automatic historical replay begins
6. readiness remains false until replay completes successfully
7. system transitions to `READY`

The app may serve the frontend and status endpoints during provisioning, but readiness and operational health must clearly show that historical build-out is still in progress.

### Required state model

The startup state model should explicitly represent:

- `STARTING`
- `PROVISIONING`
- `READY`
- `ERROR`

`PROVISIONING` must not be treated as equivalent to `READY`.

### Health and status expectations

- `/api/v1/health` should continue to expose operational detail, but it should not report an overall ready state while provisioning is active.
- `/api/v1/system/status` should expose provisioning progress and message text that explains why the system is waiting.
- frontend status surfaces should mirror the same truth and not imply that reports are fully prepared before provisioning finishes.

## 6. Provisioning Trigger Rules

Automatic provisioning should run when the system lacks required historical run coverage.

Recommended trigger conditions:

- the database is newly created
- a hard reset has just occurred
- provisioning metadata indicates the previous run did not complete successfully
- required historical run coverage is missing or materially below the `252`-trading-day target

Automatic provisioning should not rerun on every restart once the system is already provisioned.

To support this cleanly, the system should persist provisioning metadata in a dedicated database table. This is the only durable source of truth for provisioning lifecycle state, and it should be cleared by the existing hard-reset flow along with the rest of the database.

The provisioning table should capture:

- target trading days
- completed trading days
- started timestamp
- completed timestamp
- status
- last error, if any

## 7. Backfill Engine Design

`HistoricalBackfill.py` should change from a simple `days=N calendar days ago` replay into a trading-day-targeted provisioning engine.

### Engine rules

- accept a target count of trading days, defaulting to `252`
- compute the most recent `252` EGX trading sessions before the live day
- continue excluding the current live trading day from replay
- update shared progress state in trading days completed, not calendar days
- keep the run single-owner via the existing backfill lock
- use the provisioning table as the durable lifecycle record

### State contract

The startup state and backfill state must be explicitly connected rather than inferred separately.

| Startup state | Backfill state | Ready? | Health expectation | UI expectation |
|---|---|---:|---|---|
| `STARTING` | `IDLE` | No | startup in progress | initial loading |
| `PROVISIONING` | `RUNNING` | No | not ready; provisioning active | provisioning progress shown |
| `READY` | `COMPLETED` | Yes | healthy/ready | normal operational UI |
| `READY` | `COMPLETED_WITH_WARNINGS` | Yes, degraded | ready with reduced confidence | ready plus warning banner |
| `ERROR` | `ERROR` | No | degraded/error | explicit provisioning failure |

Rules:

- `PROVISIONING` is entered when automatic historical replay starts.
- `READY` is allowed only after provisioning reaches `COMPLETED`.
- `READY` is also allowed after `COMPLETED_WITH_WARNINGS`, but health and UI must keep the warning visible.
- `ERROR` is required if provisioning terminates unsuccessfully.
- manual reprovision should temporarily move the system back to `PROVISIONING` until it completes.

### Progress payload

Backfill state should continue exposing:

- `status`
- `current_day`
- `progress`
- `total_days`
- `signals_found`
- `error`

It should also add enough context for startup and UI messaging, such as:

- `mode` (`manual` vs `automatic`)
- `target_kind` (`trading_days`)
- optional `phase_message`

### Failure behavior

If provisioning fails:

- the system remains non-ready
- the failure is surfaced in health, status, and settings
- metadata is persisted so the next startup knows provisioning did not complete

Resume behavior should be deterministic. If safe incremental resume is straightforward, it is acceptable. If not, restarting the provisioning pass from a known clean boundary is preferred over ambiguous partial completion.

### Coverage and data-gap rules

Provisioning should target the most recent `252` eligible trading sessions before the live day, but it must behave deterministically when full coverage is unavailable.

Rules:

- exchange weekends and configured market holidays are excluded from the target set
- the current live day is excluded from replay
- if fewer than `252` eligible historical sessions exist in the source data, provisioning completes as `COMPLETED_WITH_WARNINGS`
- `COMPLETED_WITH_WARNINGS` should record the achieved count and a warning that historical coverage is shorter than target
- the system may transition to `READY` from `COMPLETED_WITH_WARNINGS`, but health/status must expose reduced confidence
- isolated per-day data failures should be recorded as warnings when the overall replay can still finish
- systemic failures that prevent the replay from completing the reachable window should produce `ERROR`, not a partial silent success

## 8. Report Data Design

Weekly and monthly reports should continue using replayed daily history as their analytical base.

### Weekly report

The weekly report should summarize the most recent completed trading week using daily replayed runs in that window for:

- run count
- signals generated
- closed / open / no-trade outcomes
- win rate
- average PnL
- expectancy
- what worked / what failed
- latest recommendation snapshot

Broader market context may also summarize approximately `52` weeks of benchmark history derived from daily data.

### Monthly report

The monthly report should summarize the most recent completed trading month using daily replayed runs in that window for the same signal-review metrics.

Broader market context may also summarize approximately `24` months of benchmark history derived from daily data.

### Benchmark context fallback

Benchmark context is additive, not required for the core report payload.

Rules:

- if enough benchmark history exists, reports should include the derived weekly/monthly context
- if benchmark history is incomplete or unavailable, the report should still return success using the signal-review payload
- missing benchmark context should downgrade the report to a partial result with explicit notes and warnings
- missing benchmark context should not be a hard failure unless the core daily report window itself cannot be resolved
- cache behavior should follow the final payload status; partial reports are cacheable under the same period key

### Non-goals

The design does not introduce:

- a weekly `SignalRun` cadence
- a monthly `SignalRun` cadence
- separate weekly or monthly report materialization tables

## 9. UX And Messaging

The Settings operations area should stop describing backfill as a `30`-day optional task.

Recommended copy direction:

- describe it as `Historical Provisioning`
- explain that first-run provisioning builds report-quality weekly and monthly context
- show progress as `X / 252 trading days`
- keep a manual rerun action for repair and rebuild cases

Startup and status messages should clearly communicate:

- the system is building historical signal context
- reports will be limited until provisioning completes
- readiness will switch automatically when provisioning finishes

The app should feel busy but intentional, not stuck.

## 10. Error Handling And Recovery

The design should explicitly cover these cases:

- fresh boot with empty database
- restart while provisioning is already in progress
- restart after partial provisioning failure
- manual hard reset followed by startup
- user-triggered manual reprovision after a successful prior run

Recovery rules:

- never silently mark the system ready after a failed provisioning pass
- never launch two provisioning jobs concurrently
- if a prior incomplete run is detected, surface that fact in status and continue deterministically
- manual reprovision should use the same engine and state model as automatic provisioning

## 11. Testing And Safety

Minimum planning targets should include:

- unit tests for trading-day target selection
- startup tests proving fresh systems enter `PROVISIONING` automatically
- readiness tests proving the system stays non-ready until provisioning completes
- skip tests proving already provisioned systems do not rerun the full replay
- failure tests proving provisioning errors keep the system non-ready
- report tests proving weekly and monthly routes work correctly with richer replayed history
- settings/UI tests for updated copy and progress semantics

Safety rules:

- preserve current EGX trading-day handling
- preserve the existing single-run lock behavior
- avoid duplicate signal writes for the same day and ticker
- keep current report endpoint contracts unless a small additive field is required for status clarity

## 12. Completion Definition

This design should be considered complete in implementation when:

- fresh-start systems automatically trigger historical provisioning
- provisioning targets `252` trading days by default
- readiness stays false until provisioning succeeds
- weekly and monthly reports summarize the richer daily replay history
- settings and status surfaces describe provisioning accurately
- normal restarts skip provisioning once the target coverage is already satisfied

## 13. Recommended Next Move After This Spec

Write the implementation plan next, then execute in this order:

1. persist provisioning metadata and trading-day-targeted backfill logic
2. wire startup and readiness gating to provisioning state
3. update settings/status messaging
4. strengthen report tests and coverage around the richer replay window
