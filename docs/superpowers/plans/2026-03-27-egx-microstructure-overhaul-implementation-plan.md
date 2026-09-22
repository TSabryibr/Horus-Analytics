# Horus Analytics II EGX Microstructure Overhaul Implementation Plan

Date: 2026-03-27
Based on:

- `docs/superpowers/specs/2026-03-27-egx-microstructure-overhaul-design.md`
- `PortfolioSimulator.py`
- `core/SignalEngine.py`
- `core/DailyScanner.py`
- `MarketLists.py`
- `SectorAnalysis.py`
- scanner/runtime consumers that surface signal metadata

Track: EGX Execution Realism, Signal Validation, and Route Profiling
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved EGX microstructure design into an execution-ready sequence for one owner.

The implementation must leave six things true:

1. Backtests stop assuming frictionless same-bar fills.
2. Long breakout signals require institutional-style volume confirmation rather than price-only technical triggers.
3. EGX30 and EGX70 candidates are routed through distinct market profiles.
4. Sector-relative strength participates in trade allow/block decisions, not just reporting.
5. The first rollout can run in shadow mode before it becomes fully enforced.
6. Scanner, simulator, and later runtime surfaces share one rule vocabulary instead of drifting.

## 2. In Scope

Primary backend targets:

- `PortfolioSimulator.py`
- `core/SignalEngine.py`
- `core/DailyScanner.py`
- new shared seams under `core/`:
  - `core/market_profiles.py`
  - `core/execution_model.py`
  - `core/signal_validation.py`
  - `core/regime_router.py`
- `MarketLists.py`
- `SectorAnalysis.py` or a closely-related helper if sector basket logic needs extraction
- targeted tests for simulator, signal validation, routing, and scanner metadata

Potential frontend/runtime touchpoints:

- scanner-facing surfaces only if new metadata becomes visible in the first slice
- operator-facing status or report surfaces only if they need additive explanatory fields

Out of scope:

- live broker execution
- full order-book replay
- intraday market-impact modeling
- broad portfolio-risk redesign unrelated to EGX microstructure
- unrelated scanner UI redesign

## 3. Execution Rules

These rules apply to every package in this slice:

1. No execution-realism change without tests first.
2. No new EGX behavior may live only inside `PortfolioSimulator.py`; shared rules must live in reusable seams.
3. No scanner/runtime enforcement before simulator shadow diagnostics are available.
4. No hard-coded EGX30 or EGX70 branching scattered across multiple call sites; use the router seam.
5. No rule tightening without observability counters for vetoes, caps, and slippage buckets.
6. Prefer vectorized pandas and numpy paths for universe-scale work; do not introduce row-by-row loops into hot paths.

## 4. Work Package Sequence

Execute this slice in the following order:

1. `EM-P1` Measurement and shared contract scaffolding
2. `EM-P2` Market profiles and execution model
3. `EM-P3` Simulator enforcement
4. `EM-P4` Signal validation seam
5. `EM-P5` Regime router and sector RS
6. `EM-P6` Scanner/runtime metadata integration and closeout

This order is intentional:

- diagnostics must exist before realism changes can be trusted
- execution truth should land in simulator first
- signal truth should move after fill truth is measurable
- routing belongs on top of validated candidates, not raw ones
- scanner/runtime should consume already-stable seams rather than invent new copies

## 5. Work Packages

### EM-P1. Measurement and Shared Contract Scaffolding

Purpose:

Define the shared EGX microstructure vocabulary and add shadow diagnostics so later enforcement has before-and-after evidence.

Target files:

- new seam modules under `core/`
- `PortfolioSimulator.py`
- targeted tests

Tasks:

1. Define shared metadata fields for candidates and fills:
   - `route_profile`
   - `liquidity_tier`
   - `adv_10_shares`
   - `adv_10_notional`
   - `volume_mult_20`
   - `sector_rs_14`
   - `vsa_valid`
   - `trap_risk`
   - `expected_slippage_pct`
   - `execution_cap_shares`
2. Add a small diagnostics payload or helper shape that can be reused by simulator and scanner.
3. Add initial counters for:
   - liquidity-cap hits
   - rejected notional
   - slippage bucket usage
   - VSA veto count
   - sector RS veto count
   - EGX30 vs EGX70 route counts
4. Add tests that lock the metadata contract before enforcement logic lands.

Deliverables:

- shared metadata vocabulary
- shadow diagnostics contract
- seam-level regression tests for metadata shape

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_simulation_performance.py tests/test_scanner_and_data.py -q`

Acceptance criteria:

- all later packages can emit and consume one shared microstructure vocabulary
- diagnostics exist before enforcement changes historical behavior

### EM-P2. Market Profiles and Execution Model

Purpose:

Create the reusable policy and fill-realism seams that backtests will consume first.

Target files:

- `core/market_profiles.py`
- `core/execution_model.py`
- `PortfolioSimulator.py`
- targeted simulator tests

Tasks:

1. Add market-profile definitions for:
   - `EGX30_TREND_PROFILE`
   - `EGX70_TACTICAL_PROFILE`
   - `ILLIQUID_NO_TRADE_PROFILE`
2. Define execution-model inputs and outputs.
3. Implement 10-day ADV calculations using:
   - notional ADV as the primary unit
   - share ADV as supporting metadata
4. Implement participation-rate-based slippage and partial-fill logic.
5. Keep the first version parameterized by profile values rather than hard-coded in the simulator.
6. Add direct tests for:
   - low, medium, and capped participation
   - partial fills
   - rejected remainder accounting
   - exit-side liquidity handling

Deliverables:

- reusable market-profile policy seam
- reusable execution-model seam
- tests for slippage and liquidity-cap behavior

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_strategy_and_system.py tests/test_simulation_performance.py -q`

Acceptance criteria:

- fill realism is no longer a flat one-line slippage assumption
- execution policy can be reused outside the simulator later

### EM-P3. Simulator Enforcement

Purpose:

Apply the execution model to backtests and remove frictionless same-bar fills.

Target files:

- `PortfolioSimulator.py`
- targeted simulator tests

Tasks:

1. Replace same-bar close execution with next-bar execution semantics.
2. Apply execution-model output to both entries and exits.
3. Preserve existing performance outputs while adding new diagnostics:
   - filled shares
   - rejected shares
   - realized slippage
   - liquidity-cap warnings
4. Ensure insufficient liquidity leads to smaller fills or no fills rather than silent fantasy execution.
5. Add tests for:
   - next-bar entry timing
   - partial-fill capital accounting
   - exit-side illiquidity
   - reduced fill size changing portfolio cash and PnL correctly

Deliverables:

- simulator no longer assumes perfect fills
- simulator diagnostics expose liquidity realism directly

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_simulation_performance.py tests/test_routes_simulation.py -q`

Acceptance criteria:

- backtests degrade honestly under liquidity pressure
- partial fills and rejected notional are visible and test-backed

### EM-P4. Signal Validation Seam

Purpose:

Turn abnormal participation into a hard long-entry gate rather than a soft score ingredient.

Target files:

- `core/signal_validation.py`
- `core/SignalEngine.py`
- targeted signal tests

Tasks:

1. Add VSA-style validation helpers for long candidates.
2. Implement base validation fields:
   - `volume_mult_20`
   - turnover floor
   - EFI-positive confirmation
   - candle-quality check if available
3. Define profile-aware volume thresholds so EGX30 and EGX70 can differ later without branching inside `SignalEngine`.
4. Make `SignalEngine` emit raw technical candidates and validated outcomes cleanly.
5. Add direct tests for:
   - raw setup passes but VSA veto blocks it
   - valid institutional-participation breakout passes
   - insufficient turnover blocks the signal
   - vectorized masks align with iterative checks

Deliverables:

- reusable signal-validation seam
- hard institutional-participation gate for long entries
- tests proving veto behavior directly

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py tests/test_signals_coverage.py -q`

Acceptance criteria:

- breakout candidates without abnormal participation no longer pass as actionable longs
- validation rules remain reusable outside a single signal path

### EM-P5. Regime Router and Sector RS

Purpose:

Introduce explicit EGX30 vs EGX70 routing and sector-relative trade gating.

Target files:

- `core/regime_router.py`
- `MarketLists.py`
- `SectorAnalysis.py` or a new extracted sector-return helper
- `core/DailyScanner.py`
- targeted routing and sector tests

Tasks:

1. Add sector-basket return helpers using current ticker-sector metadata.
2. Implement rolling 14-day sector RS against EGX30 benchmark.
3. Define router outputs:
   - selected profile
   - allowed or blocked
   - routing reason
   - sector RS metadata
4. Add routing rules for:
   - EGX30 trend profile
   - EGX70 tactical profile
   - illiquid / fallback no-trade profile
5. Ensure router decisions can downgrade nominal EGX30 or EGX70 names based on liquidity and sector state.
6. Add tests for:
   - EGX30 membership routing
   - EGX70 membership routing
   - positive vs negative sector RS
   - illiquid downgrade behavior

Deliverables:

- reusable regime router seam
- sector RS computation path
- tests for routing correctness

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py tests/test_api_endpoints.py -q`

Acceptance criteria:

- EGX30 and EGX70 stop sharing one implicit personality
- sector RS can block weak-theme longs directly

### EM-P6. Scanner and Runtime Metadata Integration

Purpose:

Push the new seams into scanner-facing outputs so operators can see why candidates pass, fail, or get downgraded.

Target files:

- `core/DailyScanner.py`
- `routes/scanner.py`
- scanner-facing frontend consumers only if needed
- targeted tests

Tasks:

1. Enrich candidate payloads with the shared microstructure metadata.
2. Make scanner output distinguish:
   - raw technical setup
   - validated institutional setup
   - route profile
   - trap risk
   - expected liquidity cap / slippage
3. Keep runtime behavior in shadow mode first if full enforcement is too risky for the first slice.
4. Add tests for:
   - metadata presence
   - veto reason exposure
   - EGX30 vs EGX70 route visibility
   - no-trade profile exposure
5. Run the affected scanner frontend tests if payload shape changes surface there.

Deliverables:

- scanner/runtime metadata aligned with the new seams
- operator-facing explanation of why signals are allowed or blocked

Verification:

- `.\.venv313\Scripts\python -m pytest tests/test_scanner_and_data.py tests/test_strategy_and_system.py -q`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner`

Acceptance criteria:

- operators can see why a candidate was validated, vetoed, capped, or downgraded
- scanner metadata stays aligned with simulator assumptions

## 6. Verification Matrix

Each work package must declare:

1. protected behavior
2. tests added or updated
3. simulator, scanner, or runtime surfaces affected
4. observability counters added
5. rollout mode: shadow-only or enforced

Minimum release-quality verification for the full slice:

### Backend

```powershell
$env:HORUS_DB_FILE=':memory:'
.\.venv313\Scripts\python -m pytest tests/test_simulation_performance.py tests/test_scanner_and_data.py tests/test_signals_coverage.py tests/test_strategy_and_system.py tests/test_api_endpoints.py -q
```

### Frontend

```powershell
npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner
npm --prefix frontend run build
```

### Manual simulation sanity check

```powershell
.\.venv313\Scripts\python - <<'PY'
from PortfolioSimulator import run_simulation
result = run_simulation(cap=200000, start_date='2025-01-01', end_date='2025-12-31', index_choice='EGX30')
print(result['final_value'])
PY
```

Manual assertions:

- large-position trades no longer fill fully in thin names
- expected slippage rises when participation rises
- some prior technical setups are vetoed for poor institutional participation
- EGX30 and EGX70 routing differs in emitted metadata

## 7. Risks and Controls

### Risk: stricter rules collapse trade count too quickly

Control:

- roll out in shadow mode first and inspect veto diagnostics before enforcing thresholds broadly

### Risk: simulator and scanner drift into different microstructure rules

Control:

- keep the execution, validation, and routing logic in shared seams, not duplicated call-site logic

### Risk: EGX30 and EGX70 thresholds are too rigid initially

Control:

- keep thresholds profile-based and configurable from the start

### Risk: sector RS becomes noisy or brittle

Control:

- test the 14-day rolling logic directly and keep the first release threshold simple (`> 0`)

### Risk: observability is too weak to explain reduced backtest performance

Control:

- add counters, warnings, and diagnostics before enforcement

## 8. Suggested Execution Cadence

For a single owner, the recommended order is:

1. finish `EM-P1` and `EM-P2` together so the simulator has reusable policy inputs
2. complete `EM-P3` and verify the simulator truth shift before touching signal rules
3. land `EM-P4` and `EM-P5` together so validation and routing share one vocabulary
4. close with `EM-P6` once scanner-facing metadata can explain the new behavior

## 9. First Recommended Slice

Start with `EM-P1` first.

The highest-value first edit is:

- create `core/market_profiles.py`
- create `core/execution_model.py`
- wire shadow diagnostics plus simulator-side execution realism before changing scanner candidate rules

That sequence gives the fastest truth improvement with the lowest live-risk surface.

