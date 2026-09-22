# Horus Analytics v1.0.0
> **Institutional-Grade Technical Market Scanner, Quantitative Analytics, and Algorithmic Execution Engine for the Egyptian Stock Exchange (EGX).**

[![Version](https://img.shields.io/badge/Version-1.0.0-gold.svg)](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/VERSION)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.1-black.svg)](https://nextjs.org/)
[![TradingView](https://img.shields.io/badge/Lightweight--Charts-5.1-00bcd4.svg)](https://www.tradingview.com/lightweight-charts/)

---

## 🏛️ System Overview

**Horus Analytics** is a high-performance quantitative trading, market surveillance, and decision-support workstation tailored specifically to the unique market microstructure of the **Egyptian Stock Exchange (EGX)**. 

Integrating real-time market data feeds, multi-factor technical pattern scanning, sovereign FX valuation arbitrage (RVU USD/EGP), and local LLM intelligence (Gemma 4 31B), Horus provides institutional-grade analytics, live portfolio surveillance, and automated risk enforcement.

---

## ⚡ Key Capabilities & Architecture

### 1. Egyptian Stock Exchange (EGX) 4-Phase Session Engine
Horus is engineered with strict awareness of EGX trading phases and Islamic calendar (Ramadan) session shifts:
- **Continuous Trading Session (10:00 – 14:15):** High-frequency order matching and active 1-minute/5-minute candlestick generation. Real-time intraday pattern scanning and volatility breakout tracking.
- **Closing Auction & Adjust Session (14:15 – 14:25):** Continuous order matching is halted. Orders are accumulated to establish theoretical equilibrium prices. The Horus feed watchdog automatically recognizes this auction phase to suppress false-positive stalled feed alarms.
- **Trade-at-Close Session (14:25 – 14:30):** Execution window at the fixed closing price derived from the auction.
- **Closed / Post-Market (14:30+):** Automated end-of-day data reconciliation, daily bar consolidation, signal archive audit, and AI market report generation.
- *Automatic Ramadan Schedule:* Dynamically advances closing schedule by 1 hour (Continuous close at 13:15, Trade-at-Close concludes at 13:30).

### 2. Autonomous Market Feed Watchdog & Self-Healing
- **Adaptive Heartbeat Surveillance:** Continuously monitors live tick and bar streams across all tracked EGX equities.
- **Session-Aware Thresholds:** Automatically adjusts staleness tolerance according to the session phase (continuous vs. auction vs. trade-at-close).
- **Graceful Self-Healing:** Detects process hangs or feed interruptions and triggers automated ingest restarts with a 15-minute alert cooldown to prevent notification fatigue.

### 3. Sovereign FX Parallel USD Feed (RVU Dual-Listed Arbitrage)
- Computes real-time implicit USD/EGP exchange rates using dual-listed equities (e.g., Commercial International Bank `COMI.CA` on EGX vs. `CBKDq.L` ADRs on the London Stock Exchange).
- Provides quantitative sovereign risk hedging, asset re-pricing, and cross-market premium spread tracking.

### 4. Tri-Signal Strategy & Scanning Pipeline
- **Intraday Momentum & Volume Breakout Scanner:** Real-time multi-timeframe indicator confluence (SuperTrend, Hull Moving Average, RSI divergence, Volume Profile, and Whale Accumulation traps).
- **14:10 Pre-Close Candle Preview:** Generates high-conviction swing/position recommendations 5 minutes prior to the continuous trading close.
- **15:00 Post-Close Daily Reconciliation:** Verifies closed candle signals, updates portfolio risk matrices, and archives execution outcomes.

### 5. Institutional Risk Enforcement & Live Arming Gate
- **Live Arming Guard:** Daily-expiring authorization requiring explicit operator confirmation before live trades or automated orders can execute.
- **Max Daily Loss & Consecutive Loss Circuit Breakers:** Automatically triggers portfolio-level lockouts if daily drawdown thresholds (e.g. 3.0%) or consecutive stop-losses are breached.
- **Operator Deviation Journal:** Logs and audits any manual overrides, deviation from trading plans, or rule violations.

### 6. Local AI Intelligence & Market Narratives
- Embedded integration with local **Ollama (Gemma 4 31B)** runtime for private, offline market analysis.
- Generates structured pre-market outlooks, mid-day sentiment audits, and post-close executive intelligence reports.

### 7. Asgardian Command Shell (Next.js 16 Frontend)
- Ultra-responsive, dark-mode terminal inspired by institutional trading desks.
- Interactive TradingView Lightweight-Charts with technical indicator overlays, buy/sell signal markers, order book depth, and live portfolio heatmaps.

---

## 📂 Repository Structure

```
Horus-Analytics-v1/
├── api.py                     # FastAPI application entry point & Uvicorn launcher
├── database.py                # Peewee ORM models (SQLite with WAL mode)
├── Horus_Start.bat            # Interactive launcher menu for all services
├── VERSION                    # Semantic version token (1.0.0)
│
├── config/                    # Application configuration & lifecycle
│   ├── app_factory.py         # FastAPI factory, middleware, CORS, lifecycle
│   ├── route_registry.py      # Modular route registry & API_VERSION declaration
│   ├── lifespan.py            # Startup/shutdown lifecycle handlers
│   └── scheduler_setup.py     # APScheduler background tasks & WAL maintenance
│
├── core/                      # Core business logic & domain engine
│   ├── settings.py            # AppSettings, market schedules, session phases
│   ├── TimeUtils.py           # Cairo timezone-aware datetime calculations
│   ├── app_state.py           # Typed application state singleton
│   ├── data/                  # Market data feeds & Parallel USD / RVU conversion
│   ├── market/                # Market feeds, Ingestion, Feed Watchdog
│   ├── signals/               # Stream health, signal generators, execution engines
│   └── scheduling/            # Intraday, Pre-close, and EOD scan schedules
│
├── data_engine/               # Data ingestion, Parquet Lake & DuckDB cache
├── routes/                    # Modular FastAPI REST and WebSocket endpoints
│   ├── live.py                # Real-time market status, session timeline & feeds
│   ├── system/                # System telemetry, boot status, live arm guard
│   ├── scanner.py             # Intraday technical scanner & signal desk
│   ├── portfolio.py           # Position management, ledger, and risk controls
│   └── ai_report.py           # Ollama AI narrative report generation
│
├── frontend/                  # Next.js 16 Web Dashboard
│   ├── app/                   # App Router pages and layouts
│   ├── components/            # UI components (Lightweight-Charts, Heatmaps)
│   └── package.json           # Frontend dependencies & Next.js scripts
│
├── docs/                      # Architectural specs, guides & runbooks
│   └── HORUS_V1_SYSTEM_GUIDE.md # Complete architectural and operational manual
└── tests/                     # Comprehensive pytest test suite (100+ tests)
```

---

## 🚀 Getting Started

### Prerequisites
- **Operating System:** Windows 10/11 (64-bit)
- **Python:** Python 3.13.x (with `pip` and system PATH configured)
- **Node.js:** Node.js v18+ (LTS) & npm
- **MetaStock / Mubasher PRO:** Configured local data feed folders (optional for live feed ingestion; mocks and file caches available)
- **Ollama (Optional):** Local Ollama service with `gemma:4b` or `gemma:31b` installed for AI reports.

### Installation

1. **Clone or Navigate to the Workspace:**
   ```powershell
   cd c:\Users\TSabr\Horus\Horus-Analytics-v1
   ```

2. **Install Python Dependencies:**
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies:**
   ```powershell
   cd frontend
   npm install
   cd ..
   ```

4. **Configure Environment:**
   Review and adjust `.env` settings as needed:
   ```ini
   PORT=8000
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
   LOCAL_FEED_PROVIDER=AUTO
   METASTOCK_HISTORY_DIR=C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\History\CASE
   METASTOCK_INTRADAY_DIR=C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\Intraday\CASE
   ```

---

## 🖥️ Launching the Application

The fastest and most reliable way to start Horus Analytics is via the master launcher batch file:

```cmd
Horus_Start.bat
```

From the interactive menu:
- **`[1]` Awaken God Mode:** Launches the Chitauri Scepter CLI terminal.
- **`[2]` Engage the Full Stack:** Starts both the FastAPI backend (Port `8000`) and the Next.js frontend (Port `3100`).
- **`[3]` Bridge the Worlds:** Runs a manual MetaStock-to-Parquet synchronization.
- **`[4]` Heimdall's Sight:** Executes the Portfolio Guardian diagnostics.
- **`[5]` Sound the Gjallarhorn:** Launches the live sentinel monitor.
- **`[7]` Temporal Engine:** Starts the background adaptive sync worker.

### Manual Commands
- **Backend API:**
  ```powershell
  python -m uvicorn api:app --port 8000 --reload
  ```
  *Swagger API Documentation:* `http://127.0.0.1:8000/docs`

- **Frontend Interface:**
  ```powershell
  cd frontend
  npm run dev -- --hostname 127.0.0.1 --port 3100
  ```
  *Dashboard:* `http://127.0.0.1:3100`

---

## 🧪 Testing & Verification

Run the comprehensive automated test suite across all subsystems:

```powershell
# Run all backend tests across batches
python scripts/run_backend_tests.py

# Run watchdog and session schedule regression tests
pytest tests/test_signal_sla_and_watchdog.py

# Run API and health routes test
pytest tests/test_health_routes.py tests/test_api_endpoints.py

# Run USD / RVU rate and freshness tests
pytest tests/test_usd_feed.py tests/test_preclose_freshness_notice.py
```

---

## 📖 In-Depth Documentation

For complete architectural diagrams, session phase state machines, operational runbooks, and troubleshooting guides, consult:
- **[System Architecture & Operational Guide](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/docs/HORUS_V1_SYSTEM_GUIDE.md)**
- **[Developer & Agent Working Guide](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/CLAUDE.md)**

---

## ⚖️ License
Proprietary — All rights reserved by Horus Analytics Team.
