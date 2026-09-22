# Horus Analytics v1.0.0 — Developer & Agent Guide

> **Institutional-grade technical market scanner, analytics, and execution engine for the Egyptian Stock Exchange (EGX).**

---

## 🛠️ Environment & Tooling Conventions

- **Operating System:** Windows 10/11 (PowerShell / CMD).
- **Python Runtime:** Python 3.13 (`C:\Users\TSabr\AppData\Local\Programs\Python\Python313\python.exe`).
  - Use `python` or direct system python. Notice that `.venv313` may have missing packages like `duckdb`; system Python 3.13 is fully provisioned.
  - Tests should be executed using `pytest` directly or `python scripts/run_backend_tests.py`.
- **Node.js / Frontend:** Next.js 16.1.7, React 19, TypeScript.
  - Run frontend dev: `npm run dev --prefix frontend` or `cd frontend && npm run dev`
  - Hostname: `127.0.0.1`, Port: `3100`.
  - Backend API runs on `http://127.0.0.1:8000`.

---

## 🏛️ Architectural Invariants & Coding Standards

1. **EGX Session Schedule & Watchdog Invariant:**
   - Always query `settings.get_market_session_phase()` and `settings.is_continuous_trading()`.
   - Never assume continuous order matching continues past `14:15:00` (or `13:15:00` during Ramadan).
   - The period `14:15 – 14:25` is the official **Closing Auction & Adjust Session** (orders are gathered for clearing price; continuous bars halt).
   - The period `14:25 – 14:30` is **Trade-at-Close** (trades at fixed closing price).
   - The Market Feed Watchdog must NEVER raise `MARKET FEED STALLED` alerts during Closing Auction or Trade-at-Close if bars reached the 14:15 continuous close.
2. **Timezone & Temporal Safety:**
   - NEVER use `datetime.datetime.now()` or `date.today()` directly for business logic.
   - ALWAYS use `core.TimeUtils.now()` and `core.TimeUtils.today()`, which strictly account for Cairo local time (`Africa/Cairo`).
3. **Route Registration & API Versioning:**
   - Routes must be registered via `config/route_registry.py`.
   - API Version is strictly `1.0.0` (matching `pyproject.toml`, `VERSION`, and `frontend/package.json`).
4. **Data Isolation & Storage:**
   - SQLite DB is initialized via `database.py` with WAL mode enabled.
   - Core persistent data resides under `data/`, cached rates in `.parallel_rate_cache.json`.
   - When referencing feeds in `core/data/`, ensure imports from `core.data.ParallelUSDFeed` are respected.

---

## 🧪 Testing Commands

```powershell
# Run the watchdog and SLA test suite:
pytest tests/test_signal_sla_and_watchdog.py

# Run route health and API contracts:
pytest tests/test_health_routes.py tests/test_api_endpoints.py

# Run parallel USD / RVU conversion tests:
pytest tests/test_usd_feed.py tests/test_preclose_freshness_notice.py

# Full backend batch test runner:
python scripts/run_backend_tests.py
```

---

## 🚀 gstack Integration

This project supports [gstack](https://github.com/garrytan/gstack) for AI-assisted workflows:
- `/qa` — Test and verify web UI & user flows.
- `/review` — Pre-landing code & diff review.
- `/investigate` — Root-cause systematic debugging.
- `/browse` — AI browser control.
