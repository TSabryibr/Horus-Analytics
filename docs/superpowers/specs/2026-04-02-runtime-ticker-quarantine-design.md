# Runtime Ticker Quarantine Design

Date: 2026-04-02
Status: Proposed

## Summary

Horus currently keeps some stale rights-style symbols and dormant names inside the runtime tracked universe. That creates avoidable freshness noise and wastes scan/backtest effort on symbols that are no longer meaningful for normal operations.

This design introduces a runtime-only ticker quarantine policy with three parts:

1. Auto-filter rights-style symbols such as `_R1`, `_R2`, `_R3`
2. Auto-quarantine dormant symbols older than 90 trading days with no recent intraday activity
3. Produce a reviewable report that separates auto-quarantined symbols from review-only stale symbols

The policy is runtime-only. It does not mutate the saved manual exclusions list.

## Goals

- Remove obvious rights and dormant symbols from the runtime universe
- Align freshness, scans, and universe listing to the same tracked symbol set
- Preserve the user's manual exclusions as a separate, human-controlled list
- Surface a clear review list for borderline stale symbols without hiding them automatically

## Non-Goals

- Persisting system-generated exclusions into `settings.json`
- Hiding borderline source-stale symbols automatically in phase 1
- Building a frontend management UI in phase 1
- Changing the underlying ingest engine behavior in phase 1

## Problem

Recent diagnostics showed:

- history freshness warning noise was partly caused by stale symbols that should not count toward the tracked runtime universe
- many stale symbols were rights/corporate-action instruments with `_R<number>` suffixes
- several others were dormant symbols with no meaningful recent activity
- the remaining stale set included some source-stale but still recently active names that should stay visible for review

The current runtime universe logic is too permissive:

- `is_supported_ticker()` applies only cheap structural filters
- manual exclusions are respected
- but obvious rights-style symbols and dormant names still remain in the active runtime universe

## Proposed Approach

Use a central runtime universe policy.

Add one shared runtime filter layer that:

- excludes rights-style symbols automatically
- excludes dormant symbols automatically
- leaves borderline source-stale symbols visible
- exposes a reviewable report of both auto-quarantined and review-only symbols

This filter layer becomes the shared source of truth for:

- freshness calculations
- `DataManager.list_tickers()`
- scanner and backtest paths that inherit the runtime universe through `DataManager.list_tickers()`

## Runtime Policy

### 1. Rights Auto-Filter

A symbol is runtime-quarantined as `RIGHTS` if it matches the rights/corporate-action suffix pattern:

- `_R1`
- `_R2`
- `_R3`
- more generally: `_R<number>`

These symbols are excluded from the runtime tracked universe automatically.

### 2. Dormant Runtime Quarantine

A non-rights symbol is runtime-quarantined as `DORMANT` when:

- its last history date is older than 90 trading days
- and it has no meaningful recent intraday activity

This rule is runtime-only and recalculated from current data.

### 3. Review-Only Source-Stale Symbols

Symbols that are stale but still show signs of recent activity remain in the runtime universe for phase 1.

These are not auto-quarantined. They appear in a review list with reason `SOURCE_STALE`.

This preserves visibility for names that may still be tradable or thinly active while avoiding an overly aggressive quarantine policy.

## Architecture

### Shared Runtime Filter Boundary

Extend `data_engine/ticker_filters.py` with runtime helpers:

- `is_rights_style_ticker()`
- `is_runtime_quarantined_ticker(...)`
- `classify_runtime_ticker_state(...)`

Keep `is_supported_ticker()` as the cheap structural filter.

The runtime quarantine layer should sit on top of:

- structural support checks
- manual exclusion checks
- last history date
- recent intraday timestamp

### Consumers

Use the runtime policy in:

- `data_engine/freshness.py`
- `core/DataManager.py`
- any universe-based paths that rely on `DataManager.list_tickers()`

This keeps freshness, scans, and runtime universe listing aligned.

## Data Inputs

The quarantine logic should use:

- history last date from the same freshness/history source already used by Horus
- recent intraday timestamp from `intraday_store`
- trading-day age rather than calendar-day age

The dormant threshold is:

- `90` trading days

## Report Surface

Phase 1 does not require a frontend UI.

Provide a backend-accessible runtime report that separates:

- `runtime_quarantined`
- `review_candidates`

Each item should include:

- `symbol`
- `last_history_date`
- `last_intraday_timestamp`
- `reason`

Valid reasons:

- `RIGHTS`
- `DORMANT`
- `SOURCE_STALE`

The same report can also be used to generate a ready-to-paste human review list in terminal output when needed.

## Behavior by Classification

### Auto-Quarantined

The following classes are auto-quarantined from the runtime universe:

- rights-style symbols
- dormant symbols older than 90 trading days without recent intraday activity

These symbols do not participate in:

- runtime freshness denominator
- active universe listing
- scanner/backtest universe paths that inherit from the runtime list

### Review-Only

Source-stale but still recently active symbols:

- remain in the runtime universe
- appear in the review report
- are not written into saved exclusions

## Expected Classification From Current Diagnostics

### Expected `RIGHTS`

- `ADIB_R3`
- `ARAB_R1`
- `ATLC_R3`
- `CCRS_R1`
- `CRST_R5`
- `IFAP_R2`
- `MBEN_R1`
- `MCRO_R1`
- `NIPH_R2`
- `PHGC_R1`
- `SPHT_R3`

### Expected `DORMANT`

- `IDHC`
- `MEGM`
- `NDRL`
- `RMTV`
- `SPHT`

### Expected `SOURCE_STALE`

- `CPME`
- `DEIN`
- `GPPL`
- `ICLE`
- `MISR`
- `MMAT`
- `PACH`
- `SAIB`
- `TRTO`
- `WATP`

This means the current observed stale set would likely auto-quarantine about 16 symbols and leave 10 as review-only.

## Testing Strategy

Add backend tests for:

- rights-style symbols are removed from the runtime universe
- dormant symbols older than 90 trading days with no intraday activity are runtime-quarantined
- source-stale but recently active symbols remain visible in the runtime universe
- freshness calculations use the runtime-tracked universe
- `DataManager.list_tickers()` excludes runtime-quarantined symbols without mutating manual exclusions
- runtime report separates quarantined symbols from review-only symbols and includes the expected reason

## Rollout Safety

- runtime-only means no writes to `settings.json`
- manual exclusions remain authoritative and untouched
- phase 1 applies first to freshness and universe listing
- scanner and backtest behavior inherit the policy naturally via `DataManager.list_tickers()`
- borderline symbols are reported, not silently hidden

## Risks

Main risk:

- accidentally hiding a still-meaningful thinly traded symbol

Mitigation:

- rights symbols are auto-filtered confidently
- dormant quarantine requires both stale history and no recent intraday activity
- source-stale but recently active symbols remain review-only in phase 1

## Recommendation

Implement the central runtime universe policy with:

- rights auto-filter
- dormant runtime quarantine at 90 trading days
- review-only reporting for source-stale symbols

This gives Horus a cleaner runtime universe, quieter freshness behavior, and a safer path to future symbol hygiene without overwriting user intent.
