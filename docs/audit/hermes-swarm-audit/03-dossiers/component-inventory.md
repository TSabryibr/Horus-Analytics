# Layer 3: Component Inventory & Subsystem Matrix

**Author:** `technical-architect`  
**System:** Horus Analytics II (`c:\Users\TSabr\Horus\Horus-Analytics-II`)

---

## 1. Codebase Scale & Module Distribution

A comprehensive audit of the repository reveals **314 Python source files** totaling **3,129,965 bytes (~115,000 LOC)** across the core execution and web layers:

| Subsystem Directory | File Count | Primary Purpose | Key Technologies |
| :--- | :---: | :--- | :--- |
| [`core/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core) | 53 files | Trading logic, risk management, scanners, state | NumPy, Pandas, Scipy, APScheduler |
| [`core/signals/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/signals) | 22 files | Modular signal generation, execution, desk, lifecycle | Peewee, WebSockets, Event Models |
| [`data_engine/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/data_engine) | 25 files | Mubasher ingestion, Parquet lake, freshness | DuckDB, PyArrow, FastParquet |
| [`routes/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/routes) | 22 files | FastAPI endpoint definitions and routers | FastAPI, Pydantic v2, SlowAPI |
| [`database/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/database) | 5 files | Active Peewee ORM models and migrations | Peewee, SQLite (WAL) |
| [`config/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config) | 10 files | App factory, lifespan, scheduler setup, middleware | FastAPI, Uvicorn, Starlette |
| [`frontend/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/frontend) | 100+ files | Institutional terminal web dashboard | Next.js 15, TypeScript, Tailwind |

---

## 2. ORM Comparison Matrix: Peewee vs. Orphaned SQLAlchemy

The table below contrasts the active Peewee schema ([`database/models/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/database/models)) with the disconnected SQLAlchemy schema ([`database_async.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/database_async.py)):

| Entity / Table | Active in `database/` (Peewee) | Present in `database_async.py` (SQLAlchemy) | Usage in `routes/` |
| :--- | :---: | :---: | :--- |
| `Portfolio` | Yes (`horus.db`) | Yes (`horus_async.db`) | Core: Portfolio tracking, intake, metrics |
| `Position` | Yes (`horus.db`) | Yes (`horus_async.db`) | Core: Active positions, cost basis, stop losses |
| `Trade` | Yes (`horus.db`) | Yes (`horus_async.db`) | Core: Execution history and PnL ledger |
| `BrokerOrder` | Yes (`horus.db`) | Yes (`horus_async.db`) | AutoTrader & order dispatcher |
| `Signal` | Yes (`horus.db`) | Yes (`horus_async.db`) | Scanner signal persistence |
| `SignalRun` | Yes (`horus.db`) | Yes (`horus_async.db`) | Daily and intraday scan metadata |
| `SignalRecommendation` | Yes (`horus.db`) | Yes (`horus_async.db`) | Published recommendation cards |
| `SignalDelivery` | Yes (`horus.db`) | Yes (`horus_async.db`) | Telegram & webhook dispatch audit |
| `SignalOutcome` | Yes (`horus.db`) | Yes (`horus_async.db`) | Hit-rate calculation and WFA evaluation |
| `PublishedSignalLifecycle` | Yes (`horus.db`) | Yes (`horus_async.db`) | Multi-day signal lifecycle tracking |
| `SignalGuardState` | Yes (`horus.db`) | Yes (`horus_async.db`) | System publish circuit breakers |
| `ProvisioningState` | Yes (`horus.db`) | Yes (`horus_async.db`) | Historical backfill startup gates |

---

## 3. Deprecation Inventory

| Deprecated Component | Successor Component | Reason for Deprecation | File References |
| :--- | :--- | :--- | :--- |
| `AutoTrader.process_scanner_signals` | `core.signals.executor.SignalExecutor` | Monolithic coupling between scanner and execution | [`core/AutoTrader.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/AutoTrader.py), [`pytest.ini`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/pytest.ini) |
| `execute_run_for_horus` | `core.signals.executor.SignalExecutor` | Hardcoded simulation defaults without attribution | [`core/AutoTrader.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/AutoTrader.py) |
| `monitor_horus_positions` | `core.signals.system_monitor.monitor_system_positions` | Replaced by multi-portfolio aware monitor | [`core/AutoTrader.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/AutoTrader.py) |
