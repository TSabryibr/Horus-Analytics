# Layer 3: Component & Architecture Inventory (Audit V2)

**System:** Horus Analytics II  
**Audited By:** `orchestrator`, `technical-architect`  

---

## 1. Core Component Matrix

| Subsystem | Primary Modules | Framework / Tech | Operational Purpose | Status |
| :--- | :--- | :--- | :--- | :--- |
| **API & Gateway** | `api.py`, `config/lifespan.py`, `config/middleware.py` | FastAPI, Uvicorn, Starlette | Local REST API & WebSocket server on 127.0.0.1 | Active |
| **Database & ORM** | `database/connection.py`, `database/models/*.py`, `database/migrations.py` | Peewee ORM, SQLite WAL | Single-writer transactional state for runs, deliveries, portfolios | Hardened |
| **Job Scheduler** | `config/scheduler_setup.py`, `core/scheduling.py` | APScheduler | Background periodic tasks (trade monitor, feed watchdog, scans) | Needs Grace Time fix |
| **Feed Watchdog** | `core/market/feed_watchdog.py` | Python 3.13, pandas | Stalled feed detection, cache invalidation, incremental resync, alert cooldown | Active (New) |
| **Position Monitor** | `core/signals/system_monitor.py` | Python 3.13, Peewee | Unified trade monitor for SYSTEM and Horus portfolios | Consolidated |
| **Signal Desk & Lifecycle**| `core/signals/desk.py`, `core/signals/lifecycle.py`, `core/signals/publishing.py` | Peewee, Telegram Bot API | Signal run creation, publishing to Telegram, latency measurement | Latency Tracked |
| **SLA Telemetry Engine** | `core/signals/sla.py`, `core/signals/workspace.py` | NumPy, Peewee | Delivery latency distribution, breach rates, success rate % | Active (New) |
| **Data Engine & Storage** | `data_engine/intraday_store.py`, `data_engine/sync.py`, `data_engine/freshness.py` | DuckDB, PyArrow, SQLite | Compacted Parquet stores for ticks, 1m intraday bars, daily history | Active |
| **Mubasher Harvester** | `data_engine/mubasher_extractor.py`, `data_engine/harvester_service.py` | SQLite, Windows NT | Shadow copy ingestion from Mubasher Pro client | Needs sqlite3.backup |
| **Frontend Terminal** | `frontend/src/` | Next.js 15, React 19, Tailwind CSS | Single-operator trading terminal UI on localhost:3000 | Active |

---

## 2. Deprecated & Pruned Components

| Module | Former Purpose | Current Status | Replacement |
| :--- | :--- | :--- | :--- |
| `database_async.py` | Unused SQLAlchemy 2.0 async duplicate models | **Archived to `Legacy_Archive/`** | Unified Peewee ORM in `database/` |
| `core/horus/monitor.py` | Legacy separate Horus managed portfolio monitor | **Deprecated & Merged** | `core/signals/system_monitor.py` |
| `AutoTrader.monitor_positions` | Legacy monolithic position loop | **Deprecated & Replaced** | `SystemMonitor.monitor_system_positions` |

---

## Sources & Deeper Analysis
- Executive Summary: [`01-summary/executive-summary.md`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/docs/audit/hermes-swarm-audit-v2/01-summary/executive-summary.md)
- Technical Architecture: [`02-analysis/technical-architecture.md`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/docs/audit/hermes-swarm-audit-v2/02-analysis/technical-architecture.md)
- Site Reliability: [`02-analysis/site-reliability.md`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/docs/audit/hermes-swarm-audit-v2/02-analysis/site-reliability.md)
