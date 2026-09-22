# Horus Analytics II Historical Provisioning Implementation Plan

Date: 2026-03-25
Based on:

- `docs/superpowers/specs/2026-03-25-historical-provisioning-design.md`
- `HistoricalBackfill.py`
- `api.py`
- `routes/analysis_reports.py`
- `frontend/src/app/settings/hooks/useSettingsOperations.ts`
- `frontend/src/app/settings/components/SettingsOperationsSection.tsx`

Track: Startup Reliability And Report Quality
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved historical provisioning design into an execution-ready sequence for one owner.

The implementation must leave five things true:

1. Fresh systems automatically provision historical signal context without manual Settings action.
2. Provisioning replays `252` trading days by default instead of `30` calendar days.
3. The system does not claim `READY` until provisioning completes or completes with explicit warnings.
4. Weekly and monthly reports continue using daily replay history as the analytical base.
5. Status, health, and Settings surfaces tell the same truth about provisioning progress and degraded coverage.

## 2. In Scope

Primary backend targets:

- `HistoricalBackfill.py`
- `api.py`
- readiness and startup-state helpers already used by health/status routes
- `routes/system.py` if startup/status payloads need additive provisioning fields
- `routes/analysis_reports.py`
- `database.py` or the current database model home for provisioning metadata

Primary frontend targets:

- `frontend/src/app/settings/hooks/useSettingsOperations.ts`
- `frontend/src/app/settings/components/SettingsOperationsSection.tsx`
- startup/status consumers that surface system readiness or provisioning detail

Out of scope:

- report page visual redesign
- weekly or monthly standalone signal engines
- unrelated pipeline refactors
- changing signal-scoring behavior

## 3. Execution Rules

These rules apply to every package in this slice:

1. No readiness-gating change without tests first.
2. No provisioning metadata schema without a clear hard-reset lifecycle.
3. No startup-state copy change unless health, status, and Settings surfaces stay aligned.
4. No report fallback behavior change without direct tests for partial benchmark context.
5. Keep manual reprovision as a supported repair path even after automatic provisioning lands.

## 4. Work Package Sequence

Execute this slice in the following order:

1. `HP-P1` Provisioning metadata and state contract
2. `HP-P2` Trading-day-targeted backfill engine
3. `HP-P3` Startup and readiness gating
4. `HP-P4` Report fallback and richer-history validation
5. `HP-P5` Settings/status UX alignment and closeout

This order is intentional:

- the metadata/state contract must exist before startup and UI can reason about provisioning correctly
- the engine must support trading-day targets before startup can rely on it
- readiness gating should move only after the engine and metadata are trustworthy
- report semantics should be updated after richer history exists
- Settings and status messaging should close the loop once backend behavior is stable

## 5. Work Packages

### HP-P1. Provisioning Metadata and State Contract

Purpose:

Create one durable source of truth for provisioning lifecycle state and define the mapping between startup state, backfill state, and readiness.

Target files:

- `database.py`
- any current model modules used for system metadata
- `HistoricalBackfill.py`
- `api.py`
- targeted backend tests

Tasks:

1. Add a dedicated provisioning metadata record/table in the database.
2. Store target trading days, completed trading days, started/completed timestamps, status, and last error.
3. Define the supported durable statuses:
   - `IDLE`
   - `RUNNING`
   - `COMPLETED`
   - `COMPLETED_WITH_WARNINGS`
   - `ERROR`
4. Define the in-memory to durable status mapping used by startup, health, and UI.
5. Ensure the existing hard-reset flow clears provisioning metadata together with the rest of the DB state.
6. Add direct tests for lifecycle creation, updates, reset clearing, and status mapping.

Deliverables:

- durable provisioning metadata model
- explicit state contract used by startup and UI
- regression tests for lifecycle semantics

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_historical_backfill.py tests/test_routes_settings.py -q`

Acceptance criteria:

- the system has exactly one durable provisioning lifecycle source
- hard reset does not leave stale provisioning state behind
- startup/readiness code can consume the state contract without special-case guesswork

### HP-P2. Trading-Day-Targeted Backfill Engine

Purpose:

Convert historical backfill from a calendar-day helper into a provisioning engine that targets the most recent `252` eligible EGX trading sessions.

Target files:

- `HistoricalBackfill.py`
- `GlobalSettings` or any holiday/trading-day helpers it relies on
- targeted backfill tests

Tasks:

1. Replace the current `days=N calendar days ago` selection logic with trading-session targeting.
2. Exclude EGX weekends, configured holidays, and the current live day from replay.
3. Add support for `automatic` vs `manual` provisioning mode in the progress payload.
4. Keep the single-run lock behavior intact.
5. Define deterministic behavior for:
   - short available history
   - isolated per-day data failures
   - systemic replay failures
6. Emit `COMPLETED_WITH_WARNINGS` when the reachable historical window is shorter than target but otherwise usable.
7. Add tests for trading-day counting, holiday skipping, warning completion, and hard failure behavior.

Deliverables:

- trading-day-targeted provisioning engine
- richer progress payload
- deterministic short-history and data-gap behavior

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_historical_backfill.py -q`

Acceptance criteria:

- default provisioning target is `252` trading days
- the engine no longer depends on a raw `30`-day calendar approximation
- warning and failure modes are explicit and test-backed

### HP-P3. Startup and Readiness Gating

Purpose:

Wire automatic provisioning into fresh-start boot and make system readiness honest.

Target files:

- `api.py`
- `routes/system.py`
- any startup/status helper modules used by packaged startup
- health/status tests

Tasks:

1. Detect whether automatic provisioning is required on startup.
2. Enter `PROVISIONING` when provisioning starts automatically.
3. Keep the app reachable while readiness remains false.
4. Transition to:
   - `READY` after `COMPLETED`
   - `READY` with warning semantics after `COMPLETED_WITH_WARNINGS`
   - `ERROR` after provisioning failure
5. Ensure `/api/v1/health` and `/api/v1/system/status` expose consistent provisioning fields and messages.
6. Ensure normal restarts skip automatic provisioning once target coverage is already satisfied.
7. Add tests for fresh boot, already-provisioned boot, failed provisioning, and warning completion.

Deliverables:

- startup-triggered automatic provisioning
- honest readiness gating
- consistent health/status payloads

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_health_routes.py tests/test_api_endpoints.py tests/test_startup_browser_autolaunch.py -q`

Acceptance criteria:

- fresh or reset systems no longer jump straight to `READY`
- already-provisioned systems do not rerun the full replay on every restart
- health and status say the same thing about provisioning

### HP-P4. Report Fallback and Richer-History Validation

Purpose:

Make weekly and monthly reports behave predictably when benchmark context is missing while benefiting from the richer daily replay window.

Target files:

- `routes/analysis_reports.py`
- analysis report tests

Tasks:

1. Keep daily replay history as the core analytical input for weekly and monthly reports.
2. Make benchmark context additive and explicitly partial when unavailable.
3. Ensure report payloads remain successful or partial rather than failing when only benchmark context is missing.
4. Add notes and warnings that align with the spec’s partial-result semantics.
5. Verify cache behavior stays correct for partial reports.
6. Add tests for:
   - full benchmark context
   - missing benchmark context
   - incomplete provisioning history
   - legacy signal fallback plus richer replay coverage

Deliverables:

- explicit partial-report semantics
- stronger report tests aligned with the provisioning model

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_analysis_reports.py tests/test_scanner_and_data.py -q`

Acceptance criteria:

- weekly/monthly report routes degrade gracefully when benchmark context is absent
- richer replay history improves report confidence without requiring separate weekly/monthly engines

### HP-P5. Settings and Status UX Alignment

Purpose:

Align the user-facing copy and operational controls with automatic historical provisioning.

Target files:

- `frontend/src/app/settings/hooks/useSettingsOperations.ts`
- `frontend/src/app/settings/components/SettingsOperationsSection.tsx`
- any frontend status surfaces that display startup state
- related frontend tests

Tasks:

1. Replace `30 days` backfill copy with `Historical Provisioning` language.
2. Show progress in trading days rather than calendar days.
3. Keep a manual reprovision action for repair/rebuild use cases.
4. Surface `COMPLETED_WITH_WARNINGS` in a way that is clear but not alarming.
5. Ensure status and Settings banners use the same provisioning message semantics as backend status.
6. Add frontend tests for updated copy, progress rendering, and warning-state messaging.
7. Run the relevant frontend baseline and smoke tests.

Deliverables:

- updated Settings operations semantics
- aligned readiness/provisioning messaging across UI
- frontend regression coverage for provisioning states

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/settings src/app/scanner src/app/page`
- `npm --prefix frontend run build`

Acceptance criteria:

- the Settings page no longer describes initial history build as a `30`-day optional backfill
- manual reprovision remains available
- frontend copy matches backend provisioning truth

## 6. Verification Matrix

Each work package must declare:

1. protected behavior
2. tests added or updated
3. backend or frontend status surfaces affected
4. release gates impacted
5. rollback or recovery expectations

Minimum release-quality verification for the full slice:

### Backend

```powershell
$env:HORUS_DB_FILE=':memory:'
$env:HORUS_DISABLE_READINESS_GATE='false'
.\.venv313\Scripts\python -m pytest tests/test_historical_backfill.py tests/test_analysis_reports.py tests/test_health_routes.py tests/test_api_endpoints.py tests/test_routes_settings.py -q
```

### Frontend

```powershell
npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/settings src/app/reports/weekly
npm --prefix frontend run build
```

### Packaged startup smoke check

```powershell
.\.venv313\Scripts\pyinstaller --noconfirm horus.spec
$env:HOST='127.0.0.1'
$env:PORT='8134'
.\dist\HorusApp\HorusAnalytics.exe
```

Manual packaged assertions:

- first fresh-start run enters provisioning instead of immediate ready
- health/status expose provisioning progress
- readiness flips only after provisioning completion
- warning completion, if triggered, stays visible in status

## 7. Risks and Controls

### Risk: startup becomes honest but feels hung

Control:

- provide explicit `PROVISIONING` messages and progress counters early in startup and Settings

### Risk: provisioning reruns on every boot

Control:

- use durable provisioning metadata and coverage checks before triggering replay

### Risk: health and UI drift on warning semantics

Control:

- define additive provisioning fields once and reuse them across health, status, and Settings consumers

### Risk: partial benchmark data causes brittle reports

Control:

- treat benchmark context as additive and test partial-result behavior directly

## 8. Suggested Execution Cadence

For a single owner, the recommended order is:

1. `HP-P1`
2. `HP-P2`
3. `HP-P3`
4. `HP-P4`
5. `HP-P5`

Do not begin the next package until the current package’s targeted tests are green.

## 9. Exit Checklist

This slice is complete when all of the following are true:

- fresh-start systems automatically trigger historical provisioning
- provisioning targets `252` trading days by default
- readiness stays false until provisioning completes or completes with explicit warnings
- health/status/Settings surfaces agree on provisioning semantics
- weekly and monthly reports use the richer daily replay history and degrade gracefully on missing benchmark context
- already-provisioned restarts skip the full replay
- manual reprovision remains available as a repair path

## 10. Recommended Next Move After This Plan

Start `HP-P1` first:

1. add the durable provisioning metadata model
2. codify the startup/backfill/readiness state contract in tests
3. only then move the engine and startup gating
