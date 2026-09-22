# Portfolio Signal Tracking Redesign

## Overview

Restructure the Horus Analytics portfolio system from the current fragmented architecture (2 simulation portfolios + Horus executor + AutoTrader) into a unified signal tracking system with 3 signal-type portfolios, a single execution engine, and comprehensive performance tracking.

### Goals

1. **Clear signal-type separation** — Intraday, Swing, and Position signals each get their own System portfolio
2. **Unified execution** — One executor replaces both `AutoTrader.process_scanner_signals()` and `horus/executor.py`
3. **Unified monitoring** — One monitor replaces both `AutoTrader.monitor_positions()` and `monitor_horus_positions()`
4. **Full lifecycle tracking** — Every signal execution gets a `HorusExecution` record with complete audit trail
5. **Performance dashboards** — Per-portfolio metrics and cross-portfolio comparison

### Non-Goals

- Client portfolio system (deferred to future phase)
- Changes to the `PublishedSignalLifecycle` subscriber tracking system
- Changes to the `LiveFeedManager` real-time exit checks

---

## Section 1: Portfolio Structure & Data Model

### New Portfolio Hierarchy

```
SYSTEM portfolios (auto-executed, track record)
├── "Intraday Signals"   ← INTRADAY scan
├── "Swing Signals"      ← PRE_CLOSE + DAILY scan
└── "Position Signals"   ← Weekly report (future, starts empty)

ADMIN portfolio (manual only, personal book)
└── "Admin"              ← replaces current "Horus" + "My Portfolio" roles

CLIENT portfolios (future phase)
└── (deferred)
```

### Portfolio Type Enum

```
type: "SYSTEM" | "USER" | "ADMIN" | "CLIENT"
```

- `SYSTEM` — Auto-executed signal portfolios (Intraday, Swing, Position)
- `ADMIN` — Owner's manual portfolio (one per system)
- `USER` — Legacy, kept for backward compatibility
- `CLIENT` — Future phase

### HorusExecution `trigger_source` Expansion

```
trigger_source: "INTRADAY" | "PRE_CLOSE" | "DAILY" | "DAILY_NEXT_OPEN" | "WEEKLY"
```

This table becomes the universal signal execution record for ALL System portfolios.

### Initialization Changes (`database.py` → `initialize_db()`)

New portfolios created if missing:

| Name | Type | Cash EGP | Auto Manage |
|------|------|----------|-------------|
| Intraday Signals | SYSTEM | 500,000 | True |
| Swing Signals | SYSTEM | 500,000 | True |
| Position Signals | SYSTEM | 500,000 | True |
| Admin | ADMIN | 0 | False |

Legacy portfolios preserved (no deletion):
- `My Portfolio` (USER) — historical data intact
- `Horus` (USER) — historical data intact
- `Daily Simulation` (SYSTEM) — historical archive
- `Intraday Simulation` (SYSTEM) — historical archive

---

## Section 2: Signal Routing

### Routing Map

| Scan Type | Target Portfolio |
|-----------|-----------------|
| `INTRADAY` | Intraday Signals |
| `PRE_CLOSE` | Swing Signals |
| `DAILY` | Swing Signals |
| `DAILY_NEXT_OPEN` | Swing Signals |
| `WEEKLY` | Position Signals (future) |

### New Module: `core/signals/routing.py`

```python
def resolve_target_portfolio(scan_type: str) -> Optional[Portfolio]:
    """Maps a scan type to its target System portfolio."""
    routing = {
        "INTRADAY": "Intraday Signals",
        "PRE_CLOSE": "Swing Signals",
        "DAILY": "Swing Signals",
        "DAILY_NEXT_OPEN": "Swing Signals",
        "WEEKLY": "Position Signals",
    }
    name = routing.get(scan_type.upper())
    if not name:
        return None
    return Portfolio.get_or_none(
        (Portfolio.name == name) & (Portfolio.type == "SYSTEM")
    )
```

### Flow Change in `scheduling.py`

**Before (dual path):**
```
scheduled_scan_logic() → AutoTrader.process_scanner_signals(signals, target_port)  # line 279
                       → execute_run_for_horus(run_id)                              # line 170
```

**After (single path):**
```
scheduled_scan_logic() → _persist_scheduler_signal_run()
                       → SignalExecutor.execute_run(run_id)  # replaces both paths
```

### DAILY_NEXT_OPEN Preserved

`DAILY` scan signals create `PENDING_OPEN` HorusExecution records. The next morning's `scheduled_intraday_scan()` calls `SignalExecutor.execute_pending_entries()` which fills at the actual open price with gap-check logic.

---

## Section 3: Unified Signal Executor

### New Module: `core/signals/executor.py`

Replaces both `AutoTrader.process_scanner_signals()` and `core/horus/executor.py`.

### Entry Points

```python
class SignalExecutor:
    @staticmethod
    def execute_run(run_id: int) -> dict:
        """Execute all ACTIVE recommendations from a persisted SignalRun."""

    @staticmethod
    def execute_pending_entries(max_gap_pct: float = 1.5) -> dict:
        """Execute PENDING_OPEN entries across all System portfolios at market open."""
```

### Risk Gate Pipeline

Every signal passes through these gates in order:

| # | Gate | Source | Block Behavior |
|---|------|--------|----------------|
| 1 | Portfolio Heat | `RiskManager.calculate_portfolio_heat()` | Block ALL entries if heat ≥ `MAX_PORTFOLIO_HEAT` |
| 2 | Mimir WFA Gate | `Mimir_WFA.get_trade_permission()` | Block per-ticker if WFA fails |
| 3 | Whale Trap Enforcement | Signal `Enforcement_State` | Block if `BLOCK_EXECUTION` |
| 4 | Sovereign Confluence | `confluence_engine.get_active_trap()` | Block BUY if sovereign bear trap active |
| 5 | Correlation Check | `RiskManager.check_new_trade_correlation()` | Block if too correlated with open positions |
| 6 | Velocity Limit | `MAX_DAILY_TRADES` per portfolio per day | Block if daily trade limit reached |
| 7 | Macro Regime Filter | EGX30 EMA10/EMA20 | Block BUY breakouts in choppy/bear |

### Position Sizing

```
risk_amount = ACCOUNT_BALANCE × (RISK_PER_TRADE / 100)
if regime == CHOPPY_OR_BEAR and signal_type == TRICKSTER:
    risk_amount /= 2

shares = risk_amount / (entry_price - stop_loss)
cap: shares × entry_price ≤ 20% of ACCOUNT_BALANCE
```

### Execution Record

Every execution attempt (success or failure) creates a `HorusExecution` record:
- `portfolio` → target System portfolio (resolved via routing)
- `trigger_source` → scan type
- `state` → `OPEN` | `PENDING_OPEN` | `SKIPPED` | `FAILED`
- `details_json` → blocking gate name, risk data, shares calculation

### Retired Code

| Module | Status |
|--------|--------|
| `AutoTrader.process_scanner_signals()` | **Retired** — merged into SignalExecutor |
| `core/horus/executor.py` (`execute_run_for_horus`, `execute_pending_daily_entries_for_horus`) | **Retired** — merged into SignalExecutor |
| `AutoTrader.check_exit_conditions()` | **Kept** — used by LiveFeedManager |
| `AutoTrader._notify_exit()` | **Kept** — shared utility |

---

## Section 4: Unified Monitor

### New Module: `core/signals/monitor.py`

Replaces both `AutoTrader.monitor_positions()` and `core/horus/monitor.py`.

### Called From

`scheduling.py` → `scheduled_trade_monitor()` (every 30 seconds):

```python
def scheduled_trade_monitor():
    # ... existing guards ...
    monitor_system_positions()              # NEW — replaces AutoTrader.monitor + horus monitor
    monitor_published_signal_lifecycles()    # UNCHANGED — subscriber tracking
    process_signal_followups(...)           # UNCHANGED
```

### Monitor Logic Per Position

For each OPEN position across all SYSTEM portfolios:

```
1. Fetch latest intraday bar
2. Skip if bar timestamp ≤ entry_date (avoid lookahead)
3. Skip if data is stale (>1 day old), increment stale counter

4. STOP LOSS — low ≤ active_stop_loss
   → Close position via PositionTracker
   → Update HorusExecution: state=CLOSED, close_reason=STOP_LOSS or TRAILING_STOP
   → Send exit notification (image card + text)

5. TP1 — high ≥ target_price AND tp1_hit=False
   → Scale out 50% of shares via PositionTracker
   → Move stop to breakeven, set tp1_hit=True
   → Update HorusExecution: state=UPDATED
   → Send notification

6. TP2 — high ≥ target_price_2 AND tp1_hit=True
   → Close remaining position
   → Update HorusExecution: state=CLOSED, close_reason=TARGET_2
   → Send notification

7. TRAILING STOP — if enabled or sovereign bear trap
   → Calculate potential_sl = close × (1 - trail_pct/100)
   → If potential_sl > current stop: ratchet up
   → Update Position.stop_loss + HorusExecution.trailing_state + active_stop_loss
```

### Stale Data Alert

If >50% of positions have stale data, broadcast critical warning via Telegram.

### Improvements Over Current Split System

| Aspect | Current | New |
|--------|---------|-----|
| Exit tracking | AutoTrader closes without HorusExecution record | Every exit updates HorusExecution |
| TP1 scaling | Tracked only in Position model | Tracked in both Position + HorusExecution |
| Trailing stop | Updates Position only | Updates Position + HorusExecution.trailing_state |
| Notifications | Text-only from AutoTrader | Unified image card + execution message_id tracking |

### What Stays Separate

- **`PublishedSignalLifecycle` monitor** — independent subscriber signal tracking
- **`AutoTrader.check_exit_conditions()`** — LiveFeedManager real-time tick processing

---

## Section 5: Performance Tracking

### New Module: `core/portfolio/performance.py`

Pure computation module — queries trades, executions, snapshots. No side effects, easily testable.

### Per-Portfolio Performance

API: `GET /api/portfolio/{id}/performance`

| Metric | Computation |
|--------|-------------|
| Win Rate | % trades with pnl > 0 |
| Avg PnL % | mean(trade.pnl_pct) |
| Total PnL | sum(trade.pnl) in EGP |
| Sharpe Ratio | annualized risk-adjusted return |
| Max Drawdown | largest peak-to-trough from PortfolioSnapshot |
| Profit Factor | gross_profits / gross_losses |
| Avg Holding Period | mean(exit_date - entry_date) in days |
| Best/Worst Trade | extremes |
| Trades This Week/Month | activity count |
| Equity Curve | daily PortfolioSnapshot series |

### Per-Signal Execution Detail

API: `GET /api/portfolio/{id}/executions`

Returns HorusExecution records with full lifecycle:
- Signal origin (trigger_source, run_id, recommendation)
- Entry quality (planned vs actual price, gap_pct)
- Current risk state (active stop, target, trailing)
- Exit details (close_reason, trade_id → PnL)
- Timeline (created_at → updated_at)

### System Comparison Dashboard

API: `GET /api/portfolio/system-comparison`

Side-by-side view of all 3 System portfolios:

```
                 Intraday    Swing      Position
Win Rate         62%         55%        —
Avg PnL %        +1.2%       +3.8%      —
Total Trades     47          23         0
Sharpe           1.4         1.1        —
Max Drawdown     -4.2%       -6.1%      —
Equity           512,400     528,700    500,000
```

---

## Section 6: Migration & Rollout

### Rollout Phases

| Phase | Change | Risk |
|-------|--------|------|
| 1 | Create new portfolios in `database.py` | Zero — additive only |
| 2 | Create `core/signals/routing.py` | Zero — new file |
| 3 | Create `core/signals/executor.py` | Zero — new file, not wired |
| 4 | Create `core/signals/monitor.py` | Zero — new file, not wired |
| 5 | Wire `scheduling.py` to new executor + monitor | **Medium** — replaces live paths |
| 6 | Create `core/portfolio/performance.py` | Zero — new file |
| 7 | Add API endpoints in routes | Low — new endpoints |
| 8 | Retire old code paths (deprecation logs) | Low |

### Backward Compatibility

- Old portfolios keep data — queryable forever
- `AutoTrader.check_exit_conditions()` stays for LiveFeedManager
- All existing portfolio management API endpoints unchanged
- `PublishedSignalLifecycle` system untouched
- Settings (`AUTO_TRADE_ENABLED`, `RISK_PER_TRADE`, etc.) continue working

### Rollback Strategy

Environment variable: `HORUS_USE_LEGACY_EXECUTOR=true`

When set, `scheduling.py` falls back to old `AutoTrader.process_scanner_signals()` + `horus/executor.py` paths. Simple boolean switch, no code revert needed.

---

## Files Affected Summary

### New Files

| File | Purpose |
|------|---------|
| `core/signals/routing.py` | Scan type → portfolio resolver |
| `core/signals/executor.py` | Unified signal executor |
| `core/signals/monitor.py` | Unified position monitor |
| `core/portfolio/performance.py` | Performance metrics computation |

### Modified Files

| File | Change |
|------|--------|
| `database.py` | Add ADMIN type, new portfolio init, `trigger_source` expansion |
| `core/scheduling.py` | Wire new executor + monitor, add rollback flag |
| `routes/portfolio.py` | New performance/comparison API endpoints |

### Deprecated (Not Deleted)

| File | Status |
|------|--------|
| `core/AutoTrader.py` `process_scanner_signals()` | Wrapped with deprecation log |
| `core/horus/executor.py` | Wrapped with deprecation log |
| `core/horus/monitor.py` | Wrapped with deprecation log |
