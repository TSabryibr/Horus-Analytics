# Horus Analytics II Phase 2 Portfolio Decomposition Implementation Plan

Date: 2026-03-17
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-17-phase-2-portfolio-decomposition-design.md`

Track: Backend/API Stability
Phase: Phase 2 - Structural Repair in High-Risk Areas
Status: Completed on 2026-03-17
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 2 portfolio decomposition design into an executable extraction sequence. The purpose is to turn `routes/portfolio.py` into a thin transport layer without changing endpoint paths, HTTP contracts, or portfolio business behavior.

Phase 2 portfolio work should leave four things true:

1. Route handlers are no longer the primary home of portfolio business logic.
2. Shared portfolio behavior is grouped by capability instead of historical growth.
3. Route-level behavior remains protected while new lower-level seams become directly testable.
4. The extraction pattern is reusable later for `routes/signals.py` and `routes/ai_report.py`.

## 2. In Scope

Primary source file:

- `routes/portfolio.py`

Primary extraction target package:

- `core/portfolio/__init__.py`
- `core/portfolio/identity.py`
- `core/portfolio/commands.py`
- `core/portfolio/queries.py`
- `core/portfolio/import_export.py`
- `core/portfolio/management.py`

Primary route families:

- read/query endpoints
- manual trade commands
- portfolio CRUD and risk-check flows
- CSV import/export and snapshot flows
- holdings intake, report, rebalance, and snapshot/reporting flows

Primary seams to preserve:

- `_resolve_portfolio_id`
- `_enforce_manual_entry_gate`
- `_validation_error_detail`
- `add_trade`
- `close_trade`
- `update_trade`
- `initialize_portfolio_genesis`
- `seed_portfolio_demo`
- `get_portfolio`
- `get_positions`
- `get_trades`
- `get_portfolio_metrics`
- `get_equity_curve`
- `get_portfolio_analysis`
- `export_portfolio_report`
- `import_portfolio_report_csv`
- `intake_portfolio_holdings`
- `get_portfolio_management_report`
- `send_portfolio_management_report`
- `get_portfolio_rebalancing`
- `trigger_portfolio_snapshot`

Out of scope for this Phase 2 slice:

- API redesign
- portfolio schema redesign
- new portfolio features
- moving non-portfolio logic out of other route modules
- business-rule rewrites for `Draupnir`, `RiskManager`, `PositionTracker`, or Telegram delivery

## 3. Existing Test Anchors

Keep these route-level suites green through every extraction package:

- `tests/test_portfolio_operations.py`
- `tests/test_portfolio_remaining.py`
- `tests/test_portfolio_audit.py`
- `tests/test_portfolio_management_service.py`
- `tests/test_portfolio_csv_backup.py`
- `tests/test_api_endpoints.py`
- `tests/test_precision_coverage.py`

Add direct seam tests gradually instead of replacing route coverage early:

- `tests/test_portfolio_identity_service.py`
- `tests/test_portfolio_command_service.py`
- `tests/test_portfolio_query_service.py`
- `tests/test_portfolio_import_export_service.py`
- `tests/test_portfolio_management_service_seams.py`

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `core/portfolio/identity.py`

Owns:

- canonical portfolio resolution
- manual entry gate enforcement
- request-validation detail helpers
- shared portfolio lookup helpers used by reads and commands

### `core/portfolio/commands.py`

Owns:

- genesis initialization
- add/close/update trade orchestration
- seed/demo flows
- portfolio create/delete/risk-check command helpers where they logically fit command behavior

### `core/portfolio/queries.py`

Owns:

- read-only portfolio status
- positions/trades retrieval
- metrics/equity-curve assembly
- analysis route data shaping

### `core/portfolio/import_export.py`

Owns:

- CSV parsing and value normalization helpers
- snapshot table checks
- export/import transform logic

### `core/portfolio/management.py`

Owns:

- holdings intake normalization
- management report assembly and formatting
- Telegram message chunking
- rebalance/report/snapshot orchestration

The route file should remain the public API surface. The new package should not import `routes/portfolio.py`.

## 5. Package Sequence

Execute the portfolio decomposition in this order:

1. `P2-P1` Shared portfolio resolution and boundary helpers
2. `P2-P2` Manual trade command service
3. `P2-P3` Portfolio query service
4. `P2-P4` Import/export service
5. `P2-P5` Management/reporting service

This order is intentional:

- the shared identity/boundary seam removes duplication before larger extractions
- command and query paths are already well covered and easier to isolate
- import/export is dense but comparatively self-contained
- management/reporting is the most cross-cutting and should move last

## 6. Work Packages

### P2-P1. Shared Portfolio Resolution and Boundary Helpers

Status: Completed on 2026-03-17

Purpose:

Establish one reusable portfolio seam before any large route extraction starts.

Target files:

- `routes/portfolio.py`
- `core/portfolio/__init__.py`
- `core/portfolio/identity.py`

Tasks:

1. Create the `core/portfolio` package and move `_resolve_portfolio_id`, `_enforce_manual_entry_gate`, and `_validation_error_detail` into `identity.py`.
2. Add any minimal helper wrappers needed so the route file imports these seams instead of defining them inline.
3. Preserve the current `400`, `403`, `404`, `422`, and `503` route contracts exactly.
4. Add direct tests for fallback portfolio resolution, not-found behavior, ticker normalization, WFA failure, and validation-detail mapping.

Deliverables:

- first reusable portfolio service package
- route file using imported identity/boundary helpers
- direct tests for shared boundary behavior

Verification:

- `python -m pytest tests/test_portfolio_identity_service.py -q`
- `python -m pytest tests/test_portfolio_operations.py tests/test_portfolio_audit.py -k "portfolio_id or blank_ticker or risk_check" -q`

Acceptance criteria:

- all shared route helpers are imported from `core/portfolio/identity.py`
- route-level validation and gate behavior remains unchanged
- new direct tests cover the extracted helper layer

Closeout note:

- Completed with `core/portfolio/identity.py`, route-level wrappers preserved for monkeypatch seams, and direct seam coverage in `tests/test_portfolio_identity_service.py`.

### P2-P2. Manual Trade Command Service

Status: Completed on 2026-03-17

Purpose:

Move the highest-churn mutation paths behind a command seam while keeping the HTTP surface stable.

Target files:

- `routes/portfolio.py`
- `core/portfolio/commands.py`

Tasks:

1. Extract add/close/update/genesis/seed command orchestration into `commands.py`.
2. Keep `Draupnir`, `PositionTracker`, `RiskManager`, and WFA interactions inside the command layer rather than in the route handlers.
3. Keep request-model validation in the route layer unless a lower-level helper is needed for correctness.
4. Add direct command tests for success, blocked-ticker, invalid portfolio, partial close, no-op update rejection, and seed behavior.

Deliverables:

- thin command routes in `routes/portfolio.py`
- direct command-layer tests
- preserved trade lifecycle route behavior

Verification:

- `python -m pytest tests/test_portfolio_command_service.py -q`
- `python -m pytest tests/test_portfolio_operations.py tests/test_portfolio_remaining.py tests/test_portfolio_audit.py -q`

Acceptance criteria:

- trade mutation routes delegate orchestration to `core/portfolio/commands.py`
- route tests stay green without HTTP contract drift
- direct command tests exercise the extracted layer without full route execution

Closeout note:

- Completed with manual trade, genesis, and seed orchestration moved into `core/portfolio/commands.py`, plus direct seam coverage in `tests/test_portfolio_command_service.py`.

### P2-P3. Portfolio Query Service

Status: Completed on 2026-03-17

Purpose:

Separate read composition from route registration and make later performance work easier to target.

Target files:

- `routes/portfolio.py`
- `core/portfolio/queries.py`

Tasks:

1. Extract portfolio reads, positions, trades, metrics, curve, and analysis composition into `queries.py`.
2. Centralize default portfolio resolution and no-invented-default behavior through the identity layer.
3. Keep response shaping and exclusion filtering behavior identical to Phase 1 contracts.
4. Add direct query tests using DB fixtures for empty, normal, and default-fallback cases.

Deliverables:

- query-layer module for portfolio reads
- route handlers reduced to request parsing and response mapping
- direct query tests for metrics/curve/analysis behavior

Verification:

- `python -m pytest tests/test_portfolio_query_service.py -q`
- `python -m pytest tests/test_portfolio_operations.py tests/test_portfolio_remaining.py tests/test_api_endpoints.py -k "portfolio or trades or metrics or curve or analysis" -q`

Acceptance criteria:

- read routes no longer embed most portfolio read composition
- the no-invented-default Phase 1 behavior is preserved
- direct query tests cover default resolution and not-found behavior

Closeout note:

- Completed with portfolio, positions, trades, metrics, curve, and analysis reads moved into `core/portfolio/queries.py`, plus direct seam coverage in `tests/test_portfolio_query_service.py`.

### P2-P4. Import/Export Service

Status: Completed on 2026-03-17

Purpose:

Isolate snapshot and CSV handling so file-format changes stop touching unrelated portfolio flows.

Target files:

- `routes/portfolio.py`
- `core/portfolio/import_export.py`

Tasks:

1. Extract parse helpers, snapshot-table checks, export logic, and CSV import logic into `import_export.py`.
2. Keep the import/export HTTP endpoints and CSV semantics unchanged.
3. Keep row parsing and type normalization private to the import/export layer instead of leaving them in the route file.
4. Add direct tests for parse helpers, malformed row handling, replace-existing behavior, and export structure.

Deliverables:

- import/export module with isolated parsing helpers
- route handlers reduced to transport concerns
- direct import/export seam tests

Verification:

- `python -m pytest tests/test_portfolio_import_export_service.py -q`
- `python -m pytest tests/test_portfolio_csv_backup.py tests/test_portfolio_remaining.py -k "import or export or snapshot" -q`

Acceptance criteria:

- import/export helpers are no longer embedded in `routes/portfolio.py`
- import/export route behavior and CSV semantics are unchanged
- direct tests cover row parsing and snapshot preservation rules

Closeout note:

- Completed with CSV parsing, snapshot checks, export/import orchestration, and normalization helpers moved into `core/portfolio/import_export.py`, plus direct seam coverage in `tests/test_portfolio_import_export_service.py`.

### P2-P5. Management/Reporting Service

Status: Completed on 2026-03-17

Purpose:

Move the densest cross-cutting portfolio area behind a focused management layer after the supporting seams already exist.

Target files:

- `routes/portfolio.py`
- `core/portfolio/management.py`

Tasks:

1. Extract holdings intake normalization, report assembly, report formatting, Telegram chunking, rebalance, and snapshot trigger orchestration.
2. Reuse the identity layer for portfolio lookup and the import/export layer for snapshot-adjacent logic where appropriate.
3. Preserve the current management/reporting error contracts and Telegram delivery behavior.
4. Add direct tests for intake normalization, report text formatting, Telegram message splitting, and rebalance/report orchestration.

Deliverables:

- management/reporting module
- route handlers reduced to request parsing, auth-free transport behavior, and response mapping
- direct tests for report composition and intake behavior

Verification:

- `python -m pytest tests/test_portfolio_management_service_seams.py -q`
- `python -m pytest tests/test_portfolio_management_service.py tests/test_portfolio_remaining.py tests/test_portfolio_audit.py -k "report or intake or rebalance or snapshot" -q`

Acceptance criteria:

- management/reporting logic primarily lives in `core/portfolio/management.py`
- Telegram/report behavior remains compatible with Phase 1 contracts
- the route file is materially smaller and easier to scan by capability

Closeout note:

- Completed with intake/report/rebalance/snapshot orchestration moved into `core/portfolio/management.py`, route-level helper names preserved, and direct seam coverage in `tests/test_portfolio_management_service_seams.py`.

## 7. Week-by-Week Execution

### Week 1

- [x] create `core/portfolio` package
- [x] complete `P2-P1`
- [x] start `P2-P2` with add/close/update extraction

### Week 2

- [x] finish `P2-P2`
- [x] complete `P2-P3`
- [x] run a broad portfolio regression sweep

### Week 3

- [x] complete `P2-P4`
- [x] start `P2-P5` with intake/report composition extraction

### Week 4

- [x] finish `P2-P5`
- [x] run the full portfolio route baseline plus full backend baseline
- [x] write the Phase 2 portfolio checkpoint note

## 8. Focused Command Set

### Shared identity and commands

- `python -m pytest tests/test_portfolio_identity_service.py tests/test_portfolio_command_service.py -q`
- `python -m pytest tests/test_portfolio_operations.py tests/test_portfolio_audit.py tests/test_portfolio_remaining.py -q`

### Queries

- `python -m pytest tests/test_portfolio_query_service.py -q`
- `python -m pytest tests/test_portfolio_operations.py tests/test_portfolio_remaining.py tests/test_api_endpoints.py -k "portfolio or trades or metrics or curve or analysis" -q`

### Import/export

- `python -m pytest tests/test_portfolio_import_export_service.py -q`
- `python -m pytest tests/test_portfolio_csv_backup.py tests/test_portfolio_remaining.py -k "import or export or snapshot" -q`

### Management/reporting

- `python -m pytest tests/test_portfolio_management_service_seams.py -q`
- `python -m pytest tests/test_portfolio_management_service.py tests/test_portfolio_remaining.py tests/test_portfolio_audit.py -k "report or intake or rebalance or snapshot" -q`

### Phase closeout

- `python -m pytest tests/test_portfolio_operations.py tests/test_portfolio_remaining.py tests/test_portfolio_audit.py tests/test_portfolio_management_service.py tests/test_portfolio_csv_backup.py tests/test_api_endpoints.py tests/test_precision_coverage.py -q`
- `python -m pytest tests/ --doctest-modules`

## 9. Risks and Controls

Primary risks:

1. accidentally changing HTTP behavior while extracting shared helpers
2. moving route-level validation into lower layers and silently changing `400`/`422` behavior
3. creating a vague helper bucket instead of capability-based modules
4. coupling new capability modules to each other in a way that recreates route-file sprawl elsewhere

Controls:

1. keep the route module as the HTTP contract owner
2. add direct seam tests only after the extraction exists, not before
3. move code by capability, not by verb or arbitrary file size
4. keep imports one-way: `routes/portfolio.py` imports `core/portfolio/*`, not the reverse

## 10. Phase 2 Exit Checklist for Portfolio Decomposition

- [x] `routes/portfolio.py` is materially smaller and primarily transport-focused
- [x] shared portfolio boundary logic lives in `core/portfolio/identity.py`
- [x] mutation orchestration lives in `core/portfolio/commands.py`
- [x] read composition lives in `core/portfolio/queries.py`
- [x] import/export parsing and snapshot logic lives in `core/portfolio/import_export.py`
- [x] management/reporting logic lives in `core/portfolio/management.py`
- [x] route-level portfolio tests remain green
- [x] new seam-level tests exist for each extracted capability unit
- [x] full backend baseline still passes

Checkpoint artifact:

- `docs/superpowers/reference/2026-03-17-phase-2-portfolio-checkpoint-summary.md`

## 11. Next Planning Boundary

If this plan completes successfully, the next backend Phase 2 planning artifact should use the same pattern for `routes/signals.py`, then reuse the resulting decomposition rules for `routes/ai_report.py`.
