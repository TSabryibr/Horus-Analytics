# Horus Analytics v1.0.0 — Comprehensive System Architecture & Operational Guide
> **Document Classification:** Hermes Artifact Pyramid — Layer 2 (System Architecture & Operational Reference)  
> **Release Version:** `Horus Analytics v1.0.0`  
> **Target Audience:** Systems Architects, Quantitative Traders, Platform Engineers, Hermes Autonomous Subagents  
> **Date:** September 2026

---

## 1. Executive Architecture Summary

Horus Analytics is an institutional quantitative trading, surveillance, and execution architecture specifically tailored for the **Egyptian Stock Exchange (EGX)**. The platform integrates:
- Real-time heterogeneous market data ingestion (MetaStock DAT, Mubasher DB, DirectFN, Parquet Lake, DuckDB).
- Native understanding of EGX market microstructure, including auction periods and Ramadan schedule variations.
- Sovereign parallel exchange rate modeling (USD/EGP RVU dual-listed arbitrage).
- Self-healing watchdogs with automated process remediation and alert cooldown protocols.
- Tri-signal strategy pipeline (real-time intraday momentum, 14:10 pre-close candle preview, 15:00 post-close reconciliation).
- Institutional risk controls, live order execution gates, and operator deviation tracking.
- Local LLM narrative synthesis powered by Ollama (Gemma 4 31B).
- Modern Next.js 16 dark-mode trading cockpit with TradingView Lightweight-Charts integration.

---

## 2. Layered System Architecture (C4 Component Model)

```
+-------------------------------------------------------------------------------+
|                           PRESENTATION LAYER                                  |
|  Next.js 16 Dashboard (Port 3100) | TradingView Charts | Live Portfolio Desk |
+---------------------------------------+---------------------------------------+
                                        | HTTP / REST & WebSockets (Port 8000)
+---------------------------------------v---------------------------------------+
|                           API & ROUTING LAYER                                 |
|  FastAPI 0.115 Application Factory (`config/app_factory.py`)                 |
|  Route Registry (`config/route_registry.py`) - API_VERSION = "1.0.0"          |
|  Subsystems: /system, /live, /scanner, /portfolio, /analytics, /ai_report     |
|  Middleware: CORS, Token Auth, Readiness Gate, Exception Wrapping            |
+---------------------------------------+---------------------------------------+
                                        |
+---------------------------------------v---------------------------------------+
|                     APPLICATION & COORDINATION LAYER                          |
|  Typed App State (`core/app_state.py`)                                        |
|  APScheduler Lifecycle (`config/scheduler_setup.py`)                          |
|  - Continuous Scanning Worker (10:00 - 14:15)                                 |
|  - Pre-Close Preview Job (14:10)                                              |
|  - EOD Reconciliation Job (15:00)                                             |
|  - SQLite WAL Checkpoint Maintenance (Hourly)                                 |
|  Watchdogs: Market Feed Watchdog & Stream Health Sentinel                     |
+-------------------+-------------------------------+---------------------------+
                    |                               |
+-------------------v---------------+   +-----------v---------------------------+
|       DOMAIN & STRATEGY LAYER     |   |         DATA INGESTION LAYER          |
|  Technical Signal Generators      |   |  Multi-Source Feed Ingestors          |
|  - SuperTrend, Hull MA, Volume Prof|  |  - MetaStock DAT Ingest               |
|  Whale & Trap Enforcers           |   |  - Mubasher SQLite Real-Time Ticks    |
|  Pine Strategy Runtime & Profiler |   |  - DirectFN File Listeners            |
|  Portfolio Risk & Drawdown Breaker|   |  Parquet Lake Storage Engine          |
|  Live Arming & Execution Gates    |   |  DuckDB High-Performance Cache        |
|  Local Ollama AI Reporting        |   |  Parallel USD / RVU Foreign Exchange  |
+-------------------+---------------+   +-----------+---------------------------+
                    |                               |
+-------------------v-------------------------------v---------------------------+
|                          PERSISTENCE LAYER                                    |
|  Primary Database: SQLite 3 with Write-Ahead Logging (WAL) & Foreign Keys     |
|  Historical Data Lake: Parquet Columns partitioned by Ticker & Date          |
|  Configuration & Rate Cache: `.parallel_rate_cache.json`, `market_metadata.json`
+-------------------------------------------------------------------------------+
```

---

## 3. EGX Market Microstructure & Session Lifecycle

The Egyptian Stock Exchange adheres to unique operational session timelines that differ from international equity markets. Horus Analytics strictly encodes this schedule within `core/settings.py`:

### Standard Non-Ramadan Schedule

| Session Phase | Time Range (Cairo) | Order Matching Status | Horus Engine Behavior |
| :--- | :--- | :--- | :--- |
| **Pre-Opening** | `09:30 – 10:00` | Order entry allowed; no continuous trades executed. | Pre-market baseline initialization; historical lake verification. |
| **Continuous Trading** | `10:00 – 14:15` | **Active continuous matching.** Real-time trades and 1-minute/5-minute candlestick generation. | Intraday scanning active; stream health monitors tick freshness; watchdog actively monitors for data stalls. |
| **Closing Auction & Adjust** | `14:15 – 14:25` | **Continuous matching HALTED.** Orders are accumulated; system calculates theoretical closing price. | **Continuous bars cease at 14:15:00.** Feed watchdog detects auction phase and **suppresses false-positive stall alarms**. |
| **Trade-at-Close** | `14:25 – 14:30` | Execution permitted **only at the fixed theoretical closing price**. | Trades logged at fixed closing price; preparation for end-of-day jobs. |
| **Market Closed** | `14:30+` | Market closed. | Intraday scans stopped; 15:00 EOD reconciliation executed; Ollama AI daily report generated. |

### Holy Month of Ramadan Schedule

During Ramadan, market hours advance by 1 hour:
- **Continuous Trading:** `10:00 – 13:15`
- **Closing Auction & Adjust:** `13:15 – 13:25`
- **Trade-at-Close:** `13:25 – 13:30`
- **Market Closed:** `13:30+`

---

## 4. Market Feed Watchdog & Self-Healing Sentinel

### The False-Positive Challenge
In real-time trading systems, a watchdog that measures the elapsed time since the latest candlestick will report a feed stall if no bars arrive. At `14:22`, the latest bar on EGX is legitimately `14:15:00` because continuous order matching stopped at 14:15. A naive watchdog raises critical alarms during the closing auction.

### Horus v1.0.0 Solution
The `MarketFeedWatchdog` (`core/market/feed_watchdog.py`) integrates session-phase context:
1. **Phase Classification:** When checking heartbeat freshness, it queries `settings.get_market_session_phase(now)`.
2. **Auction Grace:** If the phase is `CLOSING_AUCTION` (14:15–14:25) or `TRADE_AT_CLOSE` (14:25–14:30) and the latest bar is at or past continuous session close (`14:15:00`), it marks the feed as healthy (`stalled=False`, `status="CLOSING_AUCTION"`), returning `action="none"`.
3. **Mid-Session Stall Detection:** If the feed halts during continuous trading (e.g., latest bar is `11:30` when the clock is `11:45`), it correctly identifies a genuine stall (`stalled=True`, `status="STALLED"`).
4. **Self-Healing Remediation:** If stalled, the watchdog executes automatic remediation:
   - Restarts ingest processes.
   - Clears deadlocks.
   - Broadcasts a Telegram alert with an automatic **15-minute cooldown** to eliminate alarm storms.

---

## 5. Parallel USD & RVU Valuation Architecture

The Egyptian economy frequently experiences dual exchange rate dynamics between the official Central Bank rate and implicit parallel FX market rates. Horus embeds a specialized valuation engine (`core/data/ParallelUSDFeed.py`):

1. **Dual-Listed Cross-Arbitrage (RVU):**
   - Compares the primary listing on EGX (e.g. Commercial International Bank `COMI.CA` in EGP) against its global GDR/ADR listing on the London Stock Exchange (e.g. `CBKDq.L` in USD).
   - Computes the implied FX rate:
     $$\text{Implied USD/EGP} = \frac{\text{EGX Price (EGP)}}{\text{LSE Price (USD)} \times \text{ADR Ratio}}$$
2. **Sovereign Hedge Factor:**
   - Evaluates equities with dollarized revenues (fertilizers, shipping, petrochemicals) against the parallel rate.
   - Adjusts target exit prices and valuation multiples based on the real purchasing power of the Egyptian Pound.

---

## 6. Tri-Signal Strategy & Operational Pipeline

Horus coordinates a three-tier algorithmic scanning pipeline:

```
[10:00 - 14:15] Real-Time Intraday Momentum Scanner
     │  - Scans EGX 30, EGX 70, EGX 100 on 5m/15m intervals
     │  - Emits real-time breakout alerts & volume spikes
     ▼
[14:10] Pre-Close Daily Preview (5 min before Continuous Close)
     │  - Evaluates daily candle structure before order matching stops
     │  - Issues actionable swing trade entries for same-day auction fill
     ▼
[15:00] Post-Close Daily Reconciliation
        - Ingests finalized daily closing prices
        - Reconciles signal outcomes (Win/Loss/Hold)
        - Updates historical equity curves and portfolio risk metrics
        - Triggers Ollama AI summary narrative generation
```

---

## 7. Institutional Risk Controls & Execution Guard

To protect trading capital, Horus enforces strict risk gates before any trade signal can be executed:
- **Daily Expiring Live Arm Guard:** The system will NOT place live orders unless the human operator explicitly arms the system (`POST /api/v1/system/live-execution-guard/arm`) for the current trading day. This permission automatically expires at midnight.
- **Max Daily Drawdown Circuit Breaker:** If a portfolio incurs realized losses exceeding `LIVE_MAX_DAILY_LOSS_PCT` (default: 3.0%), all algorithmic execution is suspended.
- **Consecutive Loss Lockout:** If 4 consecutive stop-loss orders are triggered, the engine enters an operator lockout state requiring manual review.
- **Operator Deviation Journal:** Every manual override, discretionary entry, or rule violation is permanently logged in the SQLite audit ledger.

---

## 8. Operational Runbook & Maintenance

### Starting the System
1. Launch `Horus_Start.bat` and select `[2] ENGAGE THE FULL STACK`.
2. Confirm the FastAPI backend is listening on `http://127.0.0.1:8000`.
3. Confirm the Next.js frontend is accessible at `http://127.0.0.1:3100`.

### Health & Observability Endpoints
- **System Boot Status:** `GET /api/v1/system/boot-status` (validates database connection, pipeline state, provisioning, and scheduler).
- **Comprehensive System Status:** `GET /api/v1/system/status`.
- **Live Feed & Session Status:** `GET /api/v1/live/status` (exposes EGX session phase, timeline, and tick freshness).

### Database WAL Maintenance
Horus uses SQLite Write-Ahead Logging for high concurrency. An automated hourly scheduler job executes:
```sql
PRAGMA wal_checkpoint(PASSIVE);
```
To force a manual truncate checkpoint during maintenance windows:
```powershell
python -c "from config.scheduler_setup import _wal_checkpoint; _wal_checkpoint()"
```

### System Reset Protocol
To cleanly clear temporary caches, reset stalled provisioning jobs, or purge transient states, use the root administrative utility:
```powershell
powershell -ExecutionPolicy Bypass -File RESET_APP_STATE.ps1
```

---

## 9. Verification & Automated Quality Assurance

All critical invariants are protected by automated tests. Execute tests regularly:

```powershell
# Verify session timeline, closing auction behavior, and watchdog self-healing:
pytest tests/test_signal_sla_and_watchdog.py

# Verify system health, boot status payloads, and API contracts:
pytest tests/test_health_routes.py tests/test_api_endpoints.py

# Verify RVU parallel USD rate engine and freshness logic:
pytest tests/test_usd_feed.py tests/test_preclose_freshness_notice.py
```

---
*End of Horus Analytics v1.0.0 System Guide.*
