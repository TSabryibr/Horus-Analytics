# Manual Backfill Universe Selector Design

Date: 2026-04-13

## Summary

Add a universe selector to the manual historical backfill flow so the operator can choose `EGX30`, `EGX70`, `EGX100`, or `FULL` before launching a run from Settings.

The current system always preloads `EGX30` inside `HistoricalBackfill.run_backfill(...)`, which is why logs show messages such as `Using pre-loaded universe with 32 tickers.` even when the operator expects a broader replay. This design makes the chosen backfill scope explicit at the UI, API, runtime-state, and logging layers.

## Goals

1. Let the operator choose the backfill universe before running a manual backfill.
2. Keep the existing trading-days input and manual confirmation flow intact.
3. Thread the chosen universe through the backend route and backfill engine without changing unrelated behavior.
4. Surface the active universe during polling and after completion so the run scope is always visible.
5. Preserve current startup and automatic provisioning behavior unless a manual request explicitly sets a universe.

## Non-Goals

1. Redesign historical provisioning or automatic startup provisioning policy.
2. Change signal logic inside `DailyScanner`.
3. Introduce a saved global config default for the manual backfill universe.
4. Add per-sector, custom ticker-list, or ad hoc universe definitions.

## Current Problem

The manual backfill flow currently accepts only a trading-day target:

- `frontend/src/app/settings/hooks/useSettingsOperations.ts` posts `/api/v1/system/backfill?days=...`
- `routes/system.py` accepts `days`
- `HistoricalBackfill.py` hard-codes `MarketLists.get_market_list("EGX30")`

As a result:

1. Manual backfill scope is not operator-controlled.
2. Logs can look misleading if the user expects `FULL` coverage.
3. Runtime status does not indicate which universe is being rebuilt.

## Proposed Design

### 1. Universe Contract

Introduce a normalized manual backfill universe choice with four allowed values:

- `EGX30`
- `EGX70`
- `EGX100`
- `FULL`

`FULL` means the combined market universe currently returned by `MarketLists.get_market_list("ALL")`.

Backend normalization should be strict but friendly:

- missing value for manual route requests defaults to `EGX30` for backward compatibility
- case-insensitive inputs normalize to uppercase canonical values
- invalid values return `400`

### 2. Backend Route Changes

Extend the manual backfill route in `routes/system.py`:

- accept `universe: str | None = None`
- normalize and validate the requested value
- pass the canonical value into `run_backfill(days=..., universe_choice=..., mode="MANUAL")`

The response payload should include the selected universe so the frontend can reflect it immediately.

### 3. Backfill Engine Changes

Extend `HistoricalBackfill.run_backfill(...)` with a new optional argument:

- `universe_choice: str = "EGX30"`

The backfill engine should:

1. normalize the requested universe
2. resolve the correct ticker basket through `MarketLists`
3. preload that universe instead of hard-coding `EGX30`
4. store the active universe in `BACKFILL_STATE`
5. log the selected universe clearly at start-up and preload time

Expected preload mapping:

- `EGX30` -> `MarketLists.get_market_list("EGX30")`
- `EGX70` -> `MarketLists.get_market_list("EGX70")`
- `EGX100` -> `MarketLists.get_market_list("EGX100")`
- `FULL` -> `MarketLists.get_market_list("ALL")`

If the resolved ticker list is empty, the backfill should complete with warnings rather than silently proceeding with an empty preload.

### 4. Runtime State and Status

Extend `BACKFILL_STATE` with:

- `universe_choice`

Polling via `/api/v1/system/backfill/status` should expose the same field. This lets the UI show which universe is being analyzed while the run is active and after it completes.

### 5. Frontend Settings Changes

In the Settings operations section:

1. add a new universe selector near the trading-days input
2. expose the four fixed options: `EGX30`, `EGX70`, `EGX100`, `FULL`
3. include the selected universe in the confirmation prompt
4. include it in the backfill API request
5. display it in running/completed status copy

This selector is for the current manual action, not a hidden persistent system default.

### 6. UX Copy

The confirmation dialog should describe both parameters, for example:

`This will rerun historical backfill for up to 252 trading days using the FULL universe to rebuild weekly and monthly report context.`

The running state should read clearly, for example:

`Analyzing 2026-04-10 - trading day 5 of 252 - universe FULL`

The completed state should preserve the existing counts while making the scope visible.

## Data Flow

1. Operator selects trading days and universe in Settings.
2. Frontend calls `/api/v1/system/backfill?days=<n>&universe=<choice>`.
3. Route validates the request and launches `run_backfill(...)` in the background.
4. `HistoricalBackfill` resolves the correct market list and preloads that basket.
5. `DailyScanner` receives per-day `universe_df` slices derived from the selected universe.
6. Polling reflects progress plus the active universe.

## Error Handling

1. Invalid universe values should fail fast with `400`.
2. Empty resolved market lists should produce `COMPLETED_WITH_WARNINGS` with a specific message.
3. Existing backfill locking behavior remains unchanged.
4. Existing partial-day warning/error behavior remains unchanged.

## Testing

Backend tests:

1. Route test that `universe=EGX100` is passed into `run_backfill(...)`.
2. Route test that invalid universe values are rejected.
3. Backfill engine test that `FULL` resolves through `MarketLists.get_market_list("ALL")`.
4. Backfill engine test that runtime state includes `universe_choice`.

Frontend tests:

1. Settings operations section renders the selector with the four options.
2. Hook test confirms the request URL includes both `days` and `universe`.
3. Hook test confirms confirmation text includes the chosen universe.
4. Status rendering test confirms active/completed copy includes universe scope.

## Acceptance Criteria

1. The Settings page shows a universe selector for manual backfill.
2. The operator can run manual backfill against `EGX30`, `EGX70`, `EGX100`, or `FULL`.
3. Backfill logs and runtime state reflect the selected universe.
4. The previous hard-coded `EGX30` preload path is removed from manual backfill execution.
5. Existing manual backfill days behavior still works.
6. Existing tests remain green, with new coverage for the universe parameter.

## Risks

### 1. `FULL` can be materially slower

This is expected. The UI should make the universe choice visible, but no extra throttling is required in this slice.

### 2. `EGX30` metadata may still contain more than 30 symbols

That is a metadata fact, not a selector bug. The selector should reflect the named basket, not enforce a numeric count.

### 3. Automatic provisioning drift

Automatic provisioning should not silently change scope in this slice. The explicit universe selector is only for manual backfill entry points.

## Implementation Boundary

This slice covers:

- `HistoricalBackfill.py`
- `routes/system.py`
- `tests/test_historical_backfill.py`
- `frontend/src/app/settings/hooks/useSettingsOperations.ts`
- `frontend/src/app/settings/hooks/useSettingsOperations.test.tsx`
- `frontend/src/app/settings/components/SettingsOperationsSection.tsx`
- `frontend/src/app/settings/components/SettingsOperationsSection.test.tsx`

This slice does not cover:

- saving a persistent backfill-universe preference
- startup provisioning policy changes
- status dashboard summaries beyond using the new status payload if needed
