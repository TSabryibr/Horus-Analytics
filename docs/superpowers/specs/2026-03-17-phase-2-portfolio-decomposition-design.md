# Horus Analytics II Phase 2 Portfolio Decomposition Design

Date: 2026-03-17
Status: Draft for implementation planning
Document type: Design / explanation for Phase 2 execution
Target audience: Single-owner maintainer of the Horus Analytics II backend
Primary goal: Decompose `routes/portfolio.py` into smaller, testable units without changing behavior

## 1. Purpose

This design defines the Phase 2 decomposition strategy for `routes/portfolio.py`. Phase 1 stabilized the request boundary, tightened error contracts, and expanded regression coverage. Phase 2 should now use that stability to split responsibilities behind explicit seams so further changes stop requiring broad edits to one oversized route file.

This is not a feature design. It is an internal architecture design for safer maintenance, clearer test boundaries, and lower regression risk.

## 2. Current Problem

`routes/portfolio.py` currently mixes multiple unrelated responsibilities in one module:

- request models and validation helpers
- portfolio resolution and route-boundary logic
- manual trade commands
- portfolio reads and metrics
- equity curve and analysis reads
- CSV export and import
- seeded/demo portfolio behavior
- management intake, report building, Telegram send, snapshot, and rebalancing helpers

The file also contains many private parsing and formatting helpers that are only loosely grouped by concern. Even after Phase 1 hardening, this creates three ongoing risks:

1. behavior changes in one portfolio area are likely to spill into unrelated areas
2. route handlers still know too much about domain and persistence details
3. tests are forced to protect behavior through the route surface instead of smaller internal seams

## 3. Phase 2 Objective

Phase 2 should turn `routes/portfolio.py` into a thin transport module backed by focused backend units. The result should preserve all current API behavior while making each major portfolio capability understandable and testable on its own.

Success means:

1. route handlers are mostly request translation and response mapping
2. business logic lives in smaller units grouped by capability
3. existing route behavior and Phase 1 error contracts remain intact
4. extraction can proceed in slices without requiring a big-bang rewrite

## 4. Recommended Approach

Recommended approach: capability-based service extraction behind a stable route surface.

Why this approach:

- Phase 1 already protected the route boundary, so the safest next move is to keep those routes stable and move internals behind them.
- The file divides naturally into a few capability groups that already have helper clusters and test clusters.
- This approach keeps migration incremental. Each extraction slice can preserve HTTP contracts while moving only one capability family at a time.

Rejected alternatives:

### A. Split by HTTP verb only

Example: one file for reads, one file for writes.

Why rejected:

- it groups unrelated domains together
- it leaves shared helper sprawl in place
- it does not produce strong internal ownership boundaries

### B. Full repository-level portfolio package rewrite

Why rejected:

- too much churn for a first Phase 2 slice
- too much risk for one owner
- not needed to get the main maintainability benefit

## 5. Proposed Target Shape

The target is not to redesign the public API. The target is to keep existing endpoints but move the internals toward this structure:

### 5.1 Route surface

Keep `routes/portfolio.py`, but shrink it to:

- request/response models that are truly route-facing
- endpoint registration
- minimal route-boundary validation
- mapping from route calls to service functions

### 5.2 Capability units

Create focused internal backend units for these concerns:

1. `portfolio_identity`
   - portfolio resolution
   - default/fallback portfolio selection
   - portfolio existence checks

2. `portfolio_commands`
   - add trade
   - close trade
   - update trade
   - genesis/seed flows

3. `portfolio_queries`
   - get portfolio
   - positions
   - trades
   - metrics
   - curve
   - analysis

4. `portfolio_import_export`
   - CSV export
   - CSV import
   - snapshot-table support
   - record parsing helpers

5. `portfolio_management`
   - holding intake
   - management report build
   - Telegram send
   - snapshot trigger
   - rebalancing

These do not need to become five separate public modules on day one. They are the target boundaries. The implementation can start with one package or folder containing a few files and expand from there.

## 6. Extraction Order

The extraction order should minimize risk and maximize payoff.

### Package P2-P1: Shared portfolio resolution and boundary helpers

Extract first:

- `_resolve_portfolio_id`
- `_enforce_manual_entry_gate`
- `_validation_error_detail`

Reason:

- these helpers are reused across multiple route families
- they provide the common seam all later slices depend on

Target outcome:

- one shared identity/boundary module used by the existing routes

### Package P2-P2: Manual trade command service

Extract next:

- `add_trade`
- `close_trade`
- `update_trade`
- `initialize_portfolio_genesis`
- `seed_portfolio_demo`

Reason:

- these command paths are already well protected by Phase 1 tests
- they are easier to isolate than management reporting and import/export

Target outcome:

- route handlers call command-layer functions instead of invoking `Draupnir` and `PositionTracker` directly

### Package P2-P3: Portfolio query service

Extract:

- `get_portfolio`
- `get_positions`
- `get_trades`
- `get_portfolio_metrics`
- `get_equity_curve`
- `get_portfolio_analysis`

Reason:

- these reads are cohesive
- they can be tested with direct DB fixtures and simpler outputs

Target outcome:

- read logic is decoupled from route registration and easier to optimize later

### Package P2-P4: Import/export service

Extract:

- `_iso_or_empty`
- parse helpers
- `_ensure_portfolio_snapshot_table`
- `export_portfolio_report`
- `import_portfolio_report_csv`

Reason:

- import/export is internally dense and mostly unrelated to manual trade commands
- the parsing helpers already form a private mini-subsystem

Target outcome:

- CSV and snapshot handling is isolated, making future schema changes safer

### Package P2-P5: Management/reporting service

Extract last:

- `_tp2_from_tp1`
- `_parse_holding_input`
- `_build_portfolio_management_report`
- `_format_portfolio_management_report`
- `_split_telegram_message`
- `intake_portfolio_holdings`
- `get_portfolio_management_report`
- `send_portfolio_management_report`
- `get_portfolio_rebalancing`
- `trigger_portfolio_snapshot`

Reason:

- this is the densest and most cross-cutting area
- it mixes report composition, action logic, messaging, and persistence
- it benefits the most from extraction, but should only happen after the earlier seams exist

## 7. Rules for the Decomposition

These rules keep the refactor safe:

1. No endpoint path or HTTP contract changes during the decomposition wave.
2. No business-behavior changes mixed with structural extraction unless required to preserve correctness.
3. Every extraction slice starts with route-level regression coverage already passing.
4. New lower-level tests should be added as each service seam becomes available.
5. Route modules should not import each other to share portfolio logic.
6. Shared portfolio helpers should move to capability units, not to a new generic `utils` dumping ground.

## 8. Testing Strategy

The decomposition should preserve the current route-level protection while adding service-level tests gradually.

### Existing route anchors to preserve

- `tests/test_portfolio_operations.py`
- `tests/test_portfolio_remaining.py`
- `tests/test_portfolio_audit.py`
- `tests/test_portfolio_management_service.py`
- `tests/test_portfolio_csv_backup.py`

### New test strategy by slice

For each extracted unit:

1. keep the existing route-level tests green
2. add direct tests for the extracted service/helper layer
3. only narrow route mocks after the new service seam exists

Examples:

- `portfolio_identity` should get direct tests for fallback resolution and not-found behavior
- `portfolio_commands` should get direct tests for add/close/update/genesis command dispatch
- `portfolio_import_export` should get direct tests for row parsing and import/export transform rules
- `portfolio_management` should get direct tests for report composition and intake normalization

## 9. Error-Contract Preservation

Phase 1 tightened a number of route-boundary behaviors. Phase 2 must preserve them.

Contracts that must not regress:

- non-positive `portfolio_id` query/body rejection
- blank ticker rejection
- `404` versus `400` portfolio-path distinctions
- management/reporting behavior for missing or invalid inputs
- import/export route semantics

Any extracted service should return structured internal results or raise explicit domain exceptions that the route layer maps back to the existing HTTP contract.

## 10. Operational and Maintenance Benefits

If this design is followed, the next backend changes should become easier in specific ways:

1. portfolio report changes will stop risking trade mutation flows
2. import/export fixes will stop touching analysis and metrics code
3. management-report logic can evolve without growing the route file further
4. future performance or correctness work can target service seams directly
5. Phase 2 for `routes/signals.py` can reuse the same extraction pattern

## 11. Non-Goals

This decomposition does not try to:

- redesign the portfolio API
- introduce a new ORM layer
- move all logic out of the route file in one step
- rewrite business rules for risk, Draupnir, or reporting
- unify portfolio and signals domain logic yet

## 12. Acceptance Criteria

The Phase 2 portfolio decomposition design is successful when:

1. the implementation plan can break the work into 3-5 safe extraction packages
2. each package has a clear test anchor and ownership boundary
3. the target boundaries are understandable without reading all of `routes/portfolio.py`
4. the route surface can remain stable while internals are moved behind it

## 13. Recommended Next Artifact

The next artifact after this design should be an implementation plan for the first decomposition wave of `routes/portfolio.py`, with package-by-package execution order, target files, test anchors, and verification commands.
