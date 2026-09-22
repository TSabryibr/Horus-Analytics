# Horus Analytics v1.0 — Trading System & Configuration Reference Dictionary

> **Document Type:** Diátaxis Reference (Information-Oriented)  
> **Audience:** Quantitative Traders, Risk Officers, Platform Engineers  
> **System Version:** Horus Analytics v1.0.0  
> **Target Subsystem:** System Settings (`core/settings.py`), Risk Policy & Technical Indicators  

---

## 1. System & Operational Configuration

These parameters govern the underlying application lifecycle, network interfaces, market session timing, and autonomous watchdogs.

### 1.1 Market Hours & EGX Session Timing

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `CONTINUOUS_TRADING_START_HHMM` | `str` | `"1000"` | Continuous trading start time in Cairo (`10:00 AM`). |
| `CONTINUOUS_TRADING_END_HHMM_NORMAL` | `str` | `"1415"` | Continuous order matching end time for standard sessions (`02:15 PM`). |
| `CLOSING_AUCTION_END_HHMM_NORMAL` | `str` | `"1425"` | Closing auction concluding time for standard sessions (`02:25 PM`). |
| `MARKET_CLOSE_HHMM_NORMAL` | `str` | `"1430"` | Market close after Trade-at-Close window (`02:30 PM`). |
| `CONTINUOUS_TRADING_END_HHMM_RAMADAN` | `str` | `"1315"` | Continuous trading end time during Ramadan (`01:15 PM`). |
| `CLOSING_AUCTION_END_HHMM_RAMADAN` | `str` | `"1325"` | Closing auction end time during Ramadan (`01:25 PM`). |
| `MARKET_CLOSE_HHMM_RAMADAN` | `str` | `"1330"` | Market close during Ramadan (`01:30 PM`). |
| `EGX_RAMADAN_MODE` | `bool` | `False` | When `True`, shifts the session schedule forward by 1 hour. |

### 1.2 Feed Watchdog & Stream Health

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `FEED_WATCHDOG_ALERT_COOLDOWN_MINUTES` | `int` | `15` | Minimum cooldown between critical Telegram alerts to prevent notification flooding. |
| `MAX_STALENESS_MINUTES` | `int` | `15` | Maximum bar staleness before an alert fires during continuous trading. |
| `LOCAL_INTRADAY_DB_STALE_MINUTES` | `int` | `20` | Staleness threshold for local SQLite tick databases before fallback to secondary feeds. |
| `LOCAL_INTRADAY_ALLOW_STALE_FALLBACK` | `bool` | `True` | Permits read access to cached bars if live stream disconnects. |

### 1.3 Data Providers & Storage Paths

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `LOCAL_FEED_PROVIDER` | `str` | `"AUTO"` | Priority feed source (`AUTO`, `CSV`, `MUBASHER_DB`, `DIRECTFN`, `METASTOCK_DAT`). |
| `DATA_SOURCE_TYPE` | `str` | `"PARQUET"` | Core analytical lake format (`PARQUET` or `DUCKDB`). |
| `METASTOCK_HISTORY_DIR` | `str` | *Mubasher History* | Directory path containing daily `.DAT` / history files. |
| `METASTOCK_INTRADAY_DIR` | `str` | *Mubasher Intraday* | Directory path containing real-time intraday tick/bar files. |

### 1.4 Sovereign FX & Parallel USD Feed (RVU Arbitrage)

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :---: |
| `PARALLEL_USD_CACHE_TTL_SECONDS` | `int` | `300` | Expiration time for cached implied USD/EGP parallel rate. |
| `RVU_ADR_RATIO_COMI` | `float` | `1.0` | ADR-to-Ordinary share conversion ratio for CIB London (`CBKDq.L`). |
| `DEFAULT_FALLBACK_USD_EGP_RATE` | `float` | `50.0` | Conservative fallback rate if cross-arbitrage feeds are unreachable. |

---

## 2. Institutional Risk & Live Execution Guardrails

These controls enforce capital preservation and prevent rogue algorithmic execution.

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `AUTO_TRADE_ENABLED` | `bool` | `False` | Master switch for live order placement. Fails closed (`False`). |
| `LIVE_ARM_GUARD_ENABLED` | `bool` | `True` | When `True`, requires explicit operator arming per trading day (`expires_daily`). |
| `LIVE_REQUIRE_DAILY_PLAN_CONFIRMATION` | `bool` | `True` | Blocks arming until the operator formally confirms the daily trading plan. |
| `LIVE_MAX_DAILY_LOSS_PCT` | `float` | `3.0` | Maximum portfolio drawdown within a session. Reaching 3.0% triggers an instant lockout. |
| `LIVE_MAX_CONSECUTIVE_LOSSES` | `int` | `4` | Maximum consecutive stop-loss executions before live order submission is halted. |
| `MAX_PORTFOLIO_HEAT` | `float` | `0.15` | Total open portfolio risk ceiling (sum of open stop-loss risks $\le$ 15% of equity). |
| `RISK_PER_TRADE` | `float` | `0.01` | Sizing risk budget per position (default: 1.0% of portfolio equity). |
| `MAX_DAILY_TRADES` | `int` | `5` | Maximum number of new positions permitted in a single trading session. |
| `SECTOR_LIMIT_ENABLED` | `bool` | `True` | Enforces sector concentration limits. |
| `MAX_PER_SECTOR` | `int` | `2` | Maximum concurrent positions allowed in the same economic sector. |

---

## 3. Technical Strategy & Candidate Filters

Parameters controlling the Breakout + VSA and Trickster Mean-Reversion engines.

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `LOOKBACK` | `int` | `20` | Resistance window (in bars) for detecting high-watermark breakouts. |
| `VOL_SPIKE` | `float` | `1.5` | Minimum relative volume ratio ($\ge 150\%$ of 20-bar average) to confirm a breakout. |
| `MOMENTUM` | `float` | `0.02` | Minimum bar percentage gain ($+2.0\%$) to qualify as a breakout candle. |
| `RSI_MIN` | `float` | `45.0` | Lower bound for breakout RSI filter. |
| `RSI_MAX` | `float` | `75.0` | Upper bound for breakout RSI filter (avoids buying extreme overbought tops). |
| `MIN_TURNOVER` | `float` | `500000.0` | Minimum bar turnover in EGP (500k EGP) to filter illiquid penny stocks. |
| `MIN_SIGNAL_SCORE` | `float` | `65.0` | Minimum composite multi-factor score required to emit a trade recommendation. |
| `MIN_SIGNAL_CONFIDENCE` | `float` | `0.70` | Minimum statistical confidence score ($70\%$) required for live trade candidate build. |
| `MIN_RISK_REWARD` | `float` | `1.8` | Minimum acceptable Risk-to-Reward ratio ($\ge 1.8:1$). |
| `PENDING_ENTRY_MAX_GAP_PCT` | `float` | `2.5` | Skips execution if the next-day market open gaps up by $> 2.5\%$. |

---

## 4. Exit Rules & Dynamic Order Management

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `USE_ATR_EXITS` | `bool` | `True` | When `True`, calculates stop-loss and take-profit using ATR volatility multiples. |
| `ATR_SL_MULTIPLIER` | `float` | `1.5` | Stop-loss distance ($1.5 \times \text{ATR}_{14}$). |
| `ATR_TP_MULTIPLIER` | `float` | `3.0` | Take-profit distance ($3.0 \times \text{ATR}_{14}$). |
| `SL_PCT` | `float` | `0.03` | Fixed stop-loss fallback ($3.0\%$) when ATR exits are disabled. |
| `TP1_PCT` | `float` | `0.06` | Fixed take-profit fallback ($6.0\%$) when ATR exits are disabled. |
| `TRAILING_STOP_ENABLED` | `bool` | `True` | Activates trailing stop management once Position reaches $+1.5\text{R}$. |
| `TRAILING_STOP_TYPE` | `str` | `"CHANDELIER"` | Trailing stop calculation engine (`CHANDELIER`, `PARABOLIC_SAR`, `PERCENT`). |
| `TRAILING_STOP_VALUE` | `float` | `2.0` | Trailing multiplier or percentage distance. |

---

## 5. Execution Pipeline Filter Checkpoint Flow

Every potential trade must survive all 8 sequential gates before capital is allocated:

```
[Candlestick Data Ingest]
       │
       ▼  Gate 1: Liquidity & Technical Filter (Turnover ≥ 500k, RelVol ≥ 1.5, RSI 45-75)
[Breakout Candidate]
       │
       ▼  Gate 2: VSA Validation (Effort vs Result, Volume confirmation, Candle close strength)
[Valid Candidate]
       │
       ▼  Gate 3: Quality Scoring (Score ≥ 65.0, Confidence ≥ 0.70, R:R ≥ 1.8)
[Recommendation Built]
       │
       ▼  Gate 4: Pre-Execution Risk Gates (WFA permission, Whale-Trap check, Bear-Trap confluence)
[Permitted Candidate]
       │
       ▼  Gate 5: Portfolio Constraints (Max daily trades ≤ 5, Sector cap ≤ 2, Heat ≤ 15%)
[Sized Order]
       │
       ▼  Gate 6: Live Execution Guard (Armed today? Plan confirmed? Lockout inactive?)
[Live Order Submission]
       │
       ▼  Gate 7: Next-Open Gap Gate (Gap-up ≤ 2.5%)
[Execution Fill]
       │
       ▼  Gate 8: Dynamic Exits (ATR trailing stop & profit targets)
```
