# Horus Trading System Analysis and Settings Integration

This document analyzes the current Horus trading stack and maps strategy/risk filters to configurable settings.

## 1) Brainstorming Lens
- Core architecture is a dual-path system:
  - **Signal generation**: breakout + VSA confirmation with optional Trickster mean-reversion setup.
  - **Execution governance**: staged risk gates, portfolio constraints, and live guardrails.
- Highest leverage improvements are settings visibility, threshold consistency, and duplicate guardrails between recommendation and execution.

## 2) Trade Journal Lens
- Trade lifecycle states observed:
  - `ACTIVE` recommendation -> `PENDING_OPEN` (daily next-open) or direct open (intraday) -> `OPEN/UPDATED/SKIPPED/FAILED`.
- Reasons are auditable through `details_json` and event logs, enabling post-mortem analysis for skipped setups (e.g., risk-reward, regime, heat, velocity, gap).

## 3) Trading Expert Lens
- **Primary setup**: momentum-breakout with liquidity/volume/RSI constraints and VSA-style validation.
- **Secondary setup (Trickster)**: oversold rebound conditioned on RSI, EMA stretch in ATR units, candle turn, and participation.
- Execution layer treats setup output as candidates, then applies institutional controls before capital deployment.

## 4) Trading Wisdom Lens
- Existing code already follows a strong principle: **signal idea != executable trade**.
- Added settings reinforce this by making risk and quality thresholds explicit and testable, reducing hidden behavior.

## 5) Trading Signals Lens
- Signal scoring and confidence are now configurable minimums:
  - Recommendation pipeline can drop weak candidates early.
  - Execution validation re-checks thresholds to prevent accidental low-quality execution.

## 6) Trade Accounting Lens
- Costs are represented via commission/slippage assumptions and enforced in live risk contract checks.
- Position sizing and realized-loss tracking work with these assumptions to preserve realistic PnL expectations.

## 7) Trading Psychology Lens
- Guardrails reduce impulsive overtrading:
  - Daily trade velocity caps
  - Portfolio heat ceilings
  - Manual override lockout logic
  - Regime and sector concentration controls

## 8) Trading Visualization Lens
- Dashboard/Settings now expose operationally critical controls that were previously hidden.
- This improves operator comprehension of why trades are skipped and how to tune behavior safely.

## 9) Trading Plan Generator Lens
- The system supports plan-style operation:
  - Signal quality floors
  - Explicit risk-per-trade and minimum R:R
  - Heat/velocity/sector caps
  - Pending-open gap tolerance
- These map cleanly to a repeatable daily playbook.

## 10) Algorithmic Trading Lens
- Execution flow is deterministic and layered:
  1. Candidate build
  2. Numeric geometry validation
  3. Risk gates (WFA, enforcement, correlation, sector, velocity, regime)
  4. Sizing and live risk contract
  5. Persistence + notifications

## 11) Risk Management Trading Lens
- Risk policy now has explicit knobs for:
  - `MAX_DAILY_TRADES`
  - `MAX_PORTFOLIO_HEAT`
  - `PENDING_ENTRY_MAX_GAP_PCT`
  - `MIN_RISK_REWARD`
  - `MIN_SIGNAL_SCORE` / `MIN_SIGNAL_CONFIDENCE`

## 12) Backtesting Trading Strategies Lens
- Backtest path uses normalized parameter payloads and non-zero cost assumptions.
- Strategy parameter normalization now accepts the expanded risk/quality controls for consistent simulation inputs.

## 13) Backtrader Lens
- Current engine is a custom simulator/executor stack (not native Backtrader runtime), but it already models:
  - Bar-by-bar indicators
  - Pending next-open logic
  - Position sizing and stop/target execution
  - Portfolio-level constraints

---

## Trading Strategy Used (Current)

### Breakout + VSA Validation Flow
1. Compute indicators (`ATR`, `RSI`, `EMA9`, relative volume, turnover, resistance/support).
2. Build raw breakout candidates:
   - liquidity (`MIN_TURNOVER`)
   - relative volume (`VOL_SPIKE`)
   - momentum (`MOMENTUM`)
   - RSI zone (`RSI_MIN` to `RSI_MAX`)
   - close above lookback resistance (`LOOKBACK`)
3. Apply VSA-style validation (`volume_confirmation`, turnover floor, EFI confirmation, candle quality).
4. Score candidate and derive trade geometry (fixed % or ATR exits).

### Trickster Mean-Reversion Flow
1. Detect oversold and stretched conditions around EMA9 in ATR units.
2. Require turning candle and minimum participation.
3. Compute stop/targets via ATR or fixed stop fallback.

### Regime Throttling
- Scanner breadth classifies market to `BULLISH`, `CAUTIOUS`, or `BEARISH`.
- Signal list is constrained by regime-specific limits and score gates.

### Execution/Risk Gates
- Recommendation validation, WFA entry permission, trap/confluence controls, correlation, sector cap, velocity cap, regime check, live risk contract, and portfolio heat checks.

### Backtest Assumptions
- Capital + date window + parameter set + non-zero cost assumptions (`commission_pct`, `slippage_pct`), with holding-period and trade-level outcome calculations.

---

## Settings-to-Engine Mapping

| Setting | Engine Use |
|---|---|
| `LOOKBACK` | Resistance window for breakout candidates |
| `VOL_SPIKE` | Relative volume threshold for breakout |
| `MOMENTUM` | Minimum move threshold |
| `RSI_MIN` / `RSI_MAX` | Breakout RSI band |
| `SL_PCT` / `TP1_PCT` | Fixed stop/target geometry |
| `USE_ATR_EXITS`, `ATR_SL_MULTIPLIER`, `ATR_TP_MULTIPLIER` | ATR-based geometry |
| `TRICKSTER_RSI_MAX`, `TRICKSTER_REL_VOL_MIN`, `TRICKSTER_STRETCH_ATR` | Trickster setup gating |
| `MIN_TURNOVER` | Liquidity floor |
| `MIN_SIGNAL_SCORE`, `MIN_SIGNAL_CONFIDENCE` | Recommendation and execution quality floors |
| `MIN_RISK_REWARD` | Execution geometry quality check |
| `RISK_PER_TRADE` | Sizing risk budget |
| `MAX_DAILY_TRADES` | Velocity cap per portfolio/day |
| `MAX_PORTFOLIO_HEAT` | Portfolio risk-exposure cap |
| `PENDING_ENTRY_MAX_GAP_PCT` | Next-open gap skip threshold |
| `SECTOR_LIMIT_ENABLED`, `MAX_PER_SECTOR` | Sector concentration gate |
| `TRAILING_STOP_ENABLED`, `TRAILING_STOP_TYPE`, `TRAILING_STOP_VALUE` | Dynamic stop management |
| `COMMISSION_PCT`, `SLIPPAGE_PCT` | Cost realism and live risk contract preconditions |

---

## Filter Checkpoint Matrix

| Stage | Filter | Failing Outcome |
|---|---|---|
| Candidate build | Breakout + liquidity/volume/momentum/RSI | Candidate not produced |
| VSA validation | Volume/turnover/EFI/candle quality | Candidate not produced |
| Recommendation build | `MIN_SIGNAL_SCORE`, `MIN_SIGNAL_CONFIDENCE` | Recommendation not persisted |
| Execution validation | Numeric geometry + `MIN_RISK_REWARD` + min score/confidence | `SKIPPED` execution |
| Risk gate | WFA/trap/confluence/correlation/sector/velocity/regime | `SKIPPED` execution |
| Pending open | `PENDING_ENTRY_MAX_GAP_PCT` | `SKIPPED` with gap reason |
| Portfolio-level | Heat check vs `MAX_PORTFOLIO_HEAT` | Execution blocked |
| Live contract | Loss/drawdown/correlation/liquidity/cost checks | `SKIPPED` execution |
