# Horus Analytics II Runtime Ticker Quarantine Implementation Plan

Date: 2026-04-02
Based on:

- `docs/superpowers/specs/2026-04-02-runtime-ticker-quarantine-design.md`
- `data_engine/ticker_filters.py`
- `data_engine/freshness.py`
- `core/DataManager.py`
- `data_engine/intraday_store.py`
- `routes/data.py`
- `routes/system.py`
- `tests/test_data_freshness_canonical.py`
- `tests/test_scanner_and_data.py`
- `tests/test_datamanager.py`

Track: Runtime Ticker Quarantine
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved runtime ticker quarantine design into a safe implementation sequence that keeps symbol hygiene runtime-only and aligned across freshness and universe listing.

The implementation must leave seven things true:

1. Rights-style symbols matching `_R<number>` are removed from the runtime universe automatically.
2. Dormant symbols older than `90` trading days with no meaningful recent intraday activity are removed from the runtime universe automatically.
3. Borderline source-stale but recently active symbols remain visible and are reported, not auto-hidden.
4. Freshness calculations, `DataManager.list_tickers()`, and universe-driven scanner/backtest paths use the same runtime-tracked universe.
5. Manual exclusions remain untouched and authoritative.
6. Runtime quarantine never writes to `settings.json` or mutates saved exclusions.
7. Horus can produce a reviewable report that separates `RIGHTS`, `DORMANT`, and `SOURCE_STALE` classifications.

## 2. In Scope

Primary backend/runtime targets:

- `data_engine/ticker_filters.py`
- `data_engine/freshness.py`
- `core/DataManager.py`
- `routes/data.py`
- optional `routes/system.py` or adjacent status/report surface if a better report location exists

Primary test targets:

- `tests/test_data_freshness_canonical.py`
- `tests/test_datamanager.py`
- `tests/test_scanner_and_data.py`
- optional new runtime ticker quarantine test file if existing files become crowded

Primary workflow capabilities to add:

- runtime classification of tracked symbols
- rights auto-filtering
- dormant auto-quarantine
- report-only source-stale classification
- a reviewable runtime quarantine report

Out of scope for this phase:

- persisting system-generated exclusions
- frontend management UI for quarantine review
- changing source-provider ingest behavior
- quarantining all stale symbols automatically
- changing manual exclusion UX

## 3. Current Constraints

These existing facts shape the rollout:

1. `data_engine/ticker_filters.py` currently only performs cheap structural filtering and does not know about runtime dormancy or rights-style symbol policy.
2. `data_engine/freshness.py` already performs tracked-universe filtering for supported symbols and manual exclusions, but it does not yet centralize runtime quarantine policy.
3. `core/DataManager.py` uses `data_engine.api.list_tickers()` plus `is_supported_ticker()` and manual exclusions to build the runtime universe.
4. Universe-driven scanner and backtest paths inherit their symbol list through `DataManager.list_tickers()`, so changing that seam affects multiple workflows at once.
5. The user explicitly chose runtime-only quarantine, so system-generated quarantine must not be persisted.
6. The user explicitly chose a `90` trading-day dormant threshold.
7. The current stale-symbol diagnostics showed three meaningful classes:
   - obvious rights instruments
   - dormant/no-activity symbols
   - source-stale but still recently active symbols

The implementation must preserve those distinctions.

## 4. Execution Rules

These rules apply across the whole rollout:

1. No runtime quarantine decision may write into saved exclusions.
2. No borderline `SOURCE_STALE` symbol may be auto-hidden in phase 1.
3. Rights-style quarantine should be cheap and deterministic.
4. Dormant quarantine must require both stale history and missing recent intraday activity.
5. Trading-day age, not calendar-day age, must drive dormancy.
6. Freshness and universe listing must consume the same quarantine policy, not parallel copies.
7. Existing supported/manual exclusion behavior must not regress.

## 5. Target Module Map

The implementation should converge on this shape.

### Runtime policy seams

- `data_engine/ticker_filters.py`

### Freshness seams

- `data_engine/freshness.py`

### Universe-list seams

- `core/DataManager.py`

### Report seams

- `routes/data.py`
- optional report/status endpoint surface

### Test seams

- `tests/test_data_freshness_canonical.py`
- `tests/test_datamanager.py`
- `tests/test_scanner_and_data.py`

## 6. Work Package Sequence

Execute this slice in the following order:

1. `RTQ-P1` Runtime classification scaffolding
2. `RTQ-P2` Rights and dormant quarantine logic
3. `RTQ-P3` Freshness alignment
4. `RTQ-P4` Universe listing alignment
5. `RTQ-P5` Runtime quarantine report surface
6. `RTQ-P6` Regression coverage and live verification

This order is intentional:

- the classifier must exist before multiple consumers can share it
- the quarantine rules should be stabilized before freshness and universe listing adopt them
- the report should reflect the already-final runtime policy
- regression coverage should close the loop after the shared behavior is in place

## 7. Work Packages

### RTQ-P1. Runtime Classification Scaffolding

Purpose:

Create one shared runtime classification layer for rights, dormant, source-stale, and normal symbols.

Target files:

- `data_engine/ticker_filters.py`
- focused backend tests

Tasks:

1. Add helper for rights-style symbol detection:
   - `is_rights_style_ticker()`
2. Add runtime classification helper, for example:
   - `classify_runtime_ticker_state(...)`
3. Define normalized reasons:
   - `RIGHTS`
   - `DORMANT`
   - `SOURCE_STALE`
   - `ACTIVE`
4. Keep `is_supported_ticker()` as the cheap structural filter, not the runtime policy owner.

Deliverables:

- shared runtime classification contract
- normalized reason vocabulary

Verification:

- focused tests for rights pattern detection and classification output shape

Acceptance criteria:

- one backend helper can classify a symbol consistently without mutating saved exclusions

### RTQ-P2. Rights and Dormant Quarantine Logic

Purpose:

Implement the real quarantine decisions on top of the classification layer.

Target files:

- `data_engine/ticker_filters.py`
- `data_engine/freshness.py` helpers as needed
- focused tests

Tasks:

1. Auto-quarantine rights-style symbols by pattern.
2. Implement dormant detection using:
   - last history date
   - last intraday timestamp
   - `90` trading-day threshold
3. Keep recently active but source-stale symbols classified as `SOURCE_STALE`, not quarantined.
4. Expose helper such as:
   - `is_runtime_quarantined_ticker(...)`

Deliverables:

- working runtime quarantine decision helper

Verification:

- tests for:
   - rights => quarantined
   - dormant => quarantined
   - source-stale but recently active => not quarantined

Acceptance criteria:

- quarantine behavior matches the approved design boundaries

### RTQ-P3. Freshness Alignment

Purpose:

Make freshness calculations use the runtime-tracked universe.

Target files:

- `data_engine/freshness.py`
- `tests/test_data_freshness_canonical.py`

Tasks:

1. Route history freshness denominator through the runtime classification/quarantine policy.
2. Route intraday freshness denominator through the same policy.
3. Preserve existing manual exclusion handling.
4. Ensure source-stale review symbols still count as tracked.

Deliverables:

- freshness calculations aligned to runtime-tracked symbols

Verification:

- canonical freshness tests for excluded, rights, dormant, and active source-stale cases

Acceptance criteria:

- freshness ratio reflects the same runtime universe users actually interact with

### RTQ-P4. Universe Listing Alignment

Purpose:

Make runtime universe listing use the same shared quarantine policy.

Target files:

- `core/DataManager.py`
- `tests/test_datamanager.py`
- `tests/test_scanner_and_data.py`

Tasks:

1. Update `DataManager.list_tickers()` so runtime-quarantined symbols do not appear.
2. Preserve:
   - manual exclusions
   - structural ticker filtering
3. Confirm scanner/backtest paths naturally inherit the cleaner universe.

Deliverables:

- runtime-universe list aligned with freshness

Verification:

- `DataManager.list_tickers()` tests
- scanner/universe tests where relevant

Acceptance criteria:

- rights and dormant symbols disappear from the runtime universe without touching saved exclusions

### RTQ-P5. Runtime Quarantine Report Surface

Purpose:

Expose a reviewable report that separates auto-quarantined symbols from review-only stale symbols.

Target files:

- `routes/data.py`
- optional status/system report surface
- targeted tests

Tasks:

1. Add a small report helper or endpoint returning:
   - `runtime_quarantined`
   - `review_candidates`
2. Include for each item:
   - `symbol`
   - `last_history_date`
   - `last_intraday_timestamp`
   - `reason`
3. Keep the report backend-only in phase 1.

Deliverables:

- runtime quarantine report surface

Verification:

- backend tests for report shape and classification grouping

Acceptance criteria:

- Horus can expose the exact review list without any persistence side effects

### RTQ-P6. Regression Coverage and Live Verification

Purpose:

Close the loop with targeted tests and live checks using current EGX data.

Target files:

- existing and new tests above

Tasks:

1. Run targeted backend suites for freshness, DataManager, and scanner/universe behavior.
2. Recompute live freshness metrics after the change.
3. Verify:
   - rights/dormant symbols drop from runtime-tracked counts
   - source-stale review symbols remain visible
   - no saved exclusions were mutated
4. Produce a live review list summary for the current EGX state.

Deliverables:

- green test sweep
- live runtime quarantine verification summary

Verification:

- targeted pytest runs
- live backend payload checks

Acceptance criteria:

- runtime quarantine is active, explainable, and stable under tests and live data

## 8. Initial Expected Outcome

Based on the current diagnostics, the first implementation pass should likely:

- auto-quarantine about 11 rights-style symbols
- auto-quarantine about 5 dormant symbols
- leave about 10 source-stale symbols as review-only

That should reduce the active runtime dead weight materially without hiding recently active borderline names.

## 9. Risks and Mitigations

### Risk: Hiding a still-meaningful thinly traded symbol

Mitigation:

- dormant quarantine requires both stale history and no recent intraday activity
- source-stale but recently active symbols remain review-only in phase 1

### Risk: Divergent logic between freshness and universe listing

Mitigation:

- both must call the same runtime classification/quarantine helpers

### Risk: Hidden mutation of user intent

Mitigation:

- runtime-only policy
- no writes to `settings.json`
- no automatic edits to manual exclusions

## 10. Recommended First Coding Slice

Start with `RTQ-P1` and `RTQ-P2` together using TDD:

1. write failing tests for rights-style and dormant classification
2. implement the shared runtime classifier
3. keep freshness and DataManager untouched until classification behavior is stable

That gives the rest of the rollout a clean, trusted seam to build on.
