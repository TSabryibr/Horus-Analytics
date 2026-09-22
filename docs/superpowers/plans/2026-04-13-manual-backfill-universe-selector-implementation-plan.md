# Manual Backfill Universe Selector Implementation Plan

Date: 2026-04-13
Based on:

- `docs/superpowers/specs/2026-04-13-manual-backfill-universe-selector-design.md`
- `HistoricalBackfill.py`
- `routes/system.py`
- `tests/test_historical_backfill.py`
- `frontend/src/app/settings/hooks/useSettingsOperations.ts`
- `frontend/src/app/settings/hooks/useSettingsOperations.test.tsx`
- `frontend/src/app/settings/components/SettingsOperationsSection.tsx`
- `frontend/src/app/settings/components/SettingsOperationsSection.test.tsx`

Track: Manual Backfill Universe Selection
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Implement the approved manual backfill universe selector so Horus:

1. lets the operator choose `EGX30`, `EGX70`, `EGX100`, or `FULL` before launching manual backfill
2. carries that choice through the route, runtime state, and backfill engine
3. removes the current hard-coded manual `EGX30` preload behavior
4. keeps trading-day targeting and existing backfill lifecycle semantics intact
5. verifies the new contract with focused backend and frontend tests

## 2. In Scope

Primary implementation targets:

- manual backfill universe normalization and validation
- manual backfill route parameter support
- `HistoricalBackfill` universe resolution and preload selection
- runtime backfill state exposure for the selected universe
- Settings UI universe selector and request wiring
- focused regression coverage for route, engine, and Settings behavior

Primary files expected to move:

- `HistoricalBackfill.py`
- `routes/system.py`
- `tests/test_historical_backfill.py`
- `frontend/src/app/settings/hooks/useSettingsOperations.ts`
- `frontend/src/app/settings/hooks/useSettingsOperations.test.tsx`
- `frontend/src/app/settings/components/SettingsOperationsSection.tsx`
- `frontend/src/app/settings/components/SettingsOperationsSection.test.tsx`

Out of scope for this slice:

- saving a persistent global default for manual backfill universe
- changing automatic provisioning or startup backfill policy
- redesigning scanner logic or market-list metadata
- adding custom ticker-list or sector-specific backfill scopes
- broad status-dashboard redesign beyond consuming the existing backfill status payload

## 3. Execution Rules

These rules apply across the slice:

1. Treat universe normalization as the root contract; do not scatter ad hoc uppercase or alias handling across route, engine, and UI code.
2. Preserve existing backfill locking, progress polling, and day-target behavior unless the approved spec explicitly changes them.
3. Keep automatic/startup callers stable by defaulting missing universe choices to the current manual baseline.
4. Expose the active universe in runtime state so logs and UI are reading one source of truth.
5. Write the failing backend and frontend tests first, then implement only enough production code to satisfy them.

## 4. Work Package Sequence

Execute in this order:

1. `MBUS-P1` Backend universe contract and route seam
2. `MBUS-P2` Backfill engine preload and runtime-state integration
3. `MBUS-P3` Settings selector wiring and regression lock

This order is intentional:

- the route and normalization contract need to exist before the frontend can call them safely
- the engine must consume the same canonical universe values before UI work can be considered complete
- frontend copy and request wiring should lock against the final backend contract, not an intermediate assumption

## 5. Work Packages

### MBUS-P1. Backend Universe Contract and Route Seam

Purpose:

Add one canonical manual-backfill universe contract and thread it through the `/api/v1/system/backfill` route.

Target files:

- `routes/system.py`
- `HistoricalBackfill.py`
- `tests/test_historical_backfill.py`

Tasks:

1. Introduce a small normalization helper for allowed universe values: `EGX30`, `EGX70`, `EGX100`, `FULL`.
2. Make the route accept an optional `universe` query parameter.
3. Default missing `universe` values to `EGX30` for backward compatibility.
4. Reject invalid values with `400`.
5. Pass the canonical universe value into `run_backfill(...)`.
6. Update route response payloads so the selected universe is visible immediately after launch.

Deliverables:

- canonical manual-backfill universe validator
- route support for `?universe=<choice>`
- explicit response payload including selected universe

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_historical_backfill.py -k "api_start or invalid_universe" -q`

Acceptance criteria:

- `/api/v1/system/backfill` accepts `EGX30`, `EGX70`, `EGX100`, and `FULL`
- missing `universe` defaults cleanly to `EGX30`
- invalid values fail with `400`
- route launches `run_backfill(...)` with the normalized universe choice

### MBUS-P2. Backfill Engine Preload and Runtime-State Integration

Purpose:

Replace the hard-coded `EGX30` manual preload with universe-aware backfill execution and status reporting.

Target files:

- `HistoricalBackfill.py`
- `tests/test_historical_backfill.py`

Tasks:

1. Extend `run_backfill(...)` with `universe_choice`.
2. Add a universe-to-market-list resolver that maps:
   - `EGX30` -> `MarketLists.get_market_list("EGX30")`
   - `EGX70` -> `MarketLists.get_market_list("EGX70")`
   - `EGX100` -> `MarketLists.get_market_list("EGX100")`
   - `FULL` -> `MarketLists.get_market_list("ALL")`
3. Replace the hard-coded `MarketLists.get_market_list("EGX30")` preload call with the selected basket.
4. Store `universe_choice` in `BACKFILL_STATE` from launch through completion and error paths.
5. Update logging and warning text so the active universe is explicit during preloading and replay.
6. Handle empty resolved baskets with `COMPLETED_WITH_WARNINGS` rather than silent fallback.

Deliverables:

- universe-aware manual backfill preload path
- runtime status payload including `universe_choice`
- warning behavior for empty resolved market baskets

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_historical_backfill.py -k "full_resolves or universe_choice or backfill_generates_signals" -q`

Acceptance criteria:

- manual backfill no longer hard-codes `EGX30`
- `FULL` resolves through `MarketLists.get_market_list("ALL")`
- runtime backfill status includes the active universe
- empty universe resolution produces a warning outcome instead of a misleading successful run

### MBUS-P3. Settings Selector Wiring and Regression Lock

Purpose:

Add the operator-facing universe selector to Settings and lock the end-to-end request/status behavior with focused frontend tests.

Target files:

- `frontend/src/app/settings/hooks/useSettingsOperations.ts`
- `frontend/src/app/settings/hooks/useSettingsOperations.test.tsx`
- `frontend/src/app/settings/components/SettingsOperationsSection.tsx`
- `frontend/src/app/settings/components/SettingsOperationsSection.test.tsx`

Tasks:

1. Add a `backfillUniverseChoice` input contract to the Settings operations hook and component boundary.
2. Render a selector with the four fixed options: `EGX30`, `EGX70`, `EGX100`, `FULL`.
3. Include the selected universe in:
   - the confirmation prompt
   - the backfill route request
   - the running/completed/warning status copy
4. Keep existing trading-days behavior and disabled-state behavior unchanged.
5. Add hook tests for confirmation text and request URL.
6. Add component tests for selector rendering and visible universe-aware status copy.

Deliverables:

- Settings manual-backfill universe selector
- request wiring for `days` plus `universe`
- focused frontend regression tests covering the new operator flow

Verification:

- `npm --prefix frontend test -- --runInBand src/app/settings/hooks/useSettingsOperations.test.tsx src/app/settings/components/SettingsOperationsSection.test.tsx`

Acceptance criteria:

- Settings exposes a universe selector before running manual backfill
- the request URL includes both `days` and `universe`
- confirmation and status copy clearly state the selected universe
- frontend tests covering the new selector behavior pass

## 6. Risks and Controls

Risk: the route and engine normalize universe values differently.
Control: keep one small canonical normalization helper and reuse it rather than duplicating logic.

Risk: `FULL` runs could be slower and make the UI look stuck.
Control: preserve the existing progress polling behavior and surface the universe explicitly so operators understand the requested scope.

Risk: startup or automatic provisioning behavior drifts unintentionally.
Control: keep defaults backward compatible and limit the new universe parameter to explicit manual entry points in this slice.

Risk: tests only verify query-string wiring and miss runtime-state behavior.
Control: include backend tests that assert resolved preload scope and `BACKFILL_STATE` payload values, not just route arguments.

## 7. Recommended Execution Notes

- Keep universe normalization close to `HistoricalBackfill` or the route seam so later settings or status consumers can reuse it without drift.
- Avoid introducing a persisted setting in this slice; the approved behavior is an operator-selected action parameter.
- Preserve existing `BackfillStatus` shape and extend it minimally with `universe_choice` rather than redesigning the polling contract.

## 8. Recommended Next Move After This Plan

Start with `MBUS-P1` plus `MBUS-P2`: add the canonical universe normalization contract, wire `routes/system.py` to accept `universe`, and update `HistoricalBackfill.py` to preload the chosen basket while exposing `universe_choice` in runtime state. Then finish with `MBUS-P3` by wiring the Settings selector and locking the full flow with focused frontend tests.
