# Horus Analytics II — Production Release Manifest & Deployment Dossier
**Artifact Layer:** Layer 3 (Dossier & Specifications)  
**Authors:** Swarm Specialist Swarm (`technical-writer`, `site-reliability-engineer`)  
**Target:** Component Inventory, Deployment Checklist, Smoke Verification, and Release Manifest  
**Date:** September 5, 2026  
**Status:** **READY FOR DEPLOYMENT (v2.4.0-hardened)**  

---

## 1. System Release Metadata

```
========================================================================================
                 HORUS ANALYTICS II — PRODUCTION RELEASE MANIFEST
========================================================================================
 RELEASE TAG           : v2.4.0-hardened
 RELEASE CODENAME      : The Landing (Sovereign Shield)
 RELEASE DATE          : September 5, 2026
 TARGET PROFILE        : Single-Operator High-Performance Workstation
 BINDING SPECIFICATION : 127.0.0.1:8000 (Backend) / 127.0.0.1:3000 (Frontend)
 PYTHON ENVIRONMENT    : Python 3.13 64-bit (.venv313)
 FRONTEND RUNTIME      : Next.js 14 / React 18 / Tailwind CSS / TypeScript
 DATABASE ENGINE       : SQLite 3 (WAL Mode, Automatic Daily Rolling Snapshots)
 TOTAL TEST SUITE      : 123 / 123 Target Tests Passing (100.0%) | 1,672 Core Tests
========================================================================================
```

---

## 2. Subsystem Component Inventory

| Subsystem | Core Modules | Architectural Responsibility | Key Enhancements in v2.4.0 |
| :--- | :--- | :--- | :--- |
| **Intake & Market Pipeline** | [`core/pipeline.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/pipeline.py)<br>[`core/data_engine.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/data_engine.py)<br>[`core/signals/intake.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/signals/intake.py) | Ingests live quotes, historical EOD bars, market breadth, and volume anomalies. | Dynamic stale mode protection; deterministic lookback evaluation via `TimeUtils`. |
| **Conviction & Analysis Engine** | [`core/confluence.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/confluence.py)<br>[`core/sovereign_confluence.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/sovereign_confluence.py)<br>[`core/ConfluenceEngine.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/ConfluenceEngine.py) | Calculates multi-factor conviction scores; isolates Sovereign Hedge institutional traps. | Extracted `SovereignConfluenceEngine` into standalone module; preserved backward-compatible facade. |
| **Dispatch & Transport** | [`core/signals/publishing.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/signals/publishing.py)<br>[`core/TelegramBot_Alerts.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/TelegramBot_Alerts.py)<br>[`core/signals/sla.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/signals/sla.py) | Formats and dispatches signals to Telegram channels and private subscribers. | Added fast-abort for 400/403 unrecoverable errors; universal 3-strike auto-pause; secret redaction. |
| **Subscription Management** | [`core/subscriptions/service.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/subscriptions/service.py)<br>[`core/subscriptions/delivery.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/subscriptions/delivery.py)<br>[`routes/subscriptions.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/routes/subscriptions.py) | Manages client tiers, language routing (Arabic/English), and delivery diagnostics. | Added `SUBSCRIBER_BLOCKED_BOT` actionable diagnosis code and auto-pause recovery endpoint. |
| **Scheduler & Watchdog** | [`config/startup.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/startup.py)<br>[`core/market_watchdog.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/market_watchdog.py)<br>[`routes/system/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/routes/system/) | Schedules scans, interval watchdogs, market open cron, and backup routines. | Added `coalesce=True`, `max_instances=1`, and `misfire_grace_time=60` to prevent sleep wake spikes. |
| **Data Persistence & Backups** | [`database/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/database/)<br>[`database/backup.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/database/backup.py) | Manages SQLite schemas, Peewee models, transactions, and rolling database snapshots. | WAL journaling; verified daily point-in-time snapshot manager. |
| **Heavy Simulation Offloading** | [`core/universe_cache.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/universe_cache.py)<br>[`core/backtest/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/backtest/) | Offloads long-running Monte Carlo and Ragnarok stress tests to background workers. | Dedicated thread pool worker queue; concurrency-safe copy semantics. |

---

## 3. Workstation Deployment Checklist

Follow this linear checklist when staging or updating the local operator workstation:

```
[ ] 1. ENVIRONMENT VERIFICATION
    ├── Ensure Python 3.13 64-bit is active:
    │   .venv313\Scripts\python --version  (Target: Python 3.13.x)
    └── Ensure Node.js is available:
        node --version  (Target: Node 20.x+)

[ ] 2. DEPENDENCY HEALTH CHECK
    ├── Verify Python virtual environment dependencies:
    │   .venv313\Scripts\pip check
    └── Confirm pytest runs with root module discovery:
        .venv313\Scripts\pytest --version

[ ] 3. DATABASE & STORAGE HYGIENE
    ├── Check SQLite database file exists and is intact:
    │   .venv313\Scripts\python -c "import sqlite3; con = sqlite3.connect('horus.db'); assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'"
    ├── Ensure backup directory exists:
    │   if (-not (Test-Path "backups")) { New-Item -ItemType Directory -Path "backups" }
    └── Ensure logs directory exists:
        if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" }

[ ] 4. CONFIGURATION AUDIT (.env)
    ├── Ensure loopback binding: HOST=127.0.0.1, PORT=8000
    ├── Ensure TELEGRAM_TOKEN and TELEGRAM_CHANNEL_ID are populated.
    └── Confirm OLLAMA_BASE_URL is reachable (default: http://127.0.0.1:11434).

[ ] 5. AUTOMATED SMOKE TEST SUITE
    ├── Run the 10 targeted verification suites:
    │   .venv313\Scripts\pytest tests/test_action_matrix_remediations.py tests/test_phase4_adversarial_verification.py
    └── Confirm 13/13 passed.

[ ] 6. SERVICE INITIALIZATION
    ├── Launch the backend API service:
    │   .venv313\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000
    └── Launch the frontend Next.js interface:
        cd frontend && npm run dev (or npm run start)
```

---

## 4. Operational Smoke Test Procedures

Execute these rapid curl smoke tests after launch to verify end-to-end functionality:

### Smoke Test 1: System Boot & Pipeline State
```powershell
curl -s http://127.0.0.1:8000/api/v1/system/boot-status
```
- **Expected Status:** HTTP 200
- **Assertion:** `"system_ready": true`, `"pipeline_state": "FRESH"`.

### Smoke Test 2: Market Watchdog & Scheduler Inventory
```powershell
curl -s http://127.0.0.1:8000/api/v1/system/full-status | jq .scheduler
```
- **Expected Status:** HTTP 200
- **Assertion:** `"running": true`, `jobs` includes both `"market_watchdog"` and `"market_watchdog_open"`.

### Smoke Test 3: Memory Diagnostics & Resource Footprint
```powershell
curl -s http://127.0.0.1:8000/api/v1/system/diagnostics/memory
```
- **Expected Status:** HTTP 200
- **Assertion:** `rss_mb < 600.0`, `threads_count < 25`, all background worker threads `alive: true`.

---

## 5. Rollback & Disaster Recovery Procedures

If a critical unexpected fault emerges in production:
1. **Fast Process Termination:**
   ```powershell
   Get-Process -Name python | Where-Object { $_.Path -like "*Horus*" } | Stop-Process -Force
   ```
2. **Snapshot Restoration:**
   ```powershell
   $latestBackup = Get-ChildItem -Path "backups\horus_backup_*.db" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
   Copy-Item -Path $latestBackup.FullName -Destination "horus.db" -Force
   ```
3. **Commit Pinning:**
   If git rollback is required:
   ```powershell
   git status
   git checkout tags/v2.4.0-hardened
   ```

---

## 6. Canonical Sources & Navigation

SOURCES (LAYER 2 NAVIGATION)
docs/audit/phase5-release/00-index.md
 -> Pyramid root navigation index
docs/audit/phase5-release/01-summary/release-summary.md
 -> Executive release declaration and handover
docs/audit/phase5-release/02-analysis/operational-runbooks.md
 -> Operational Runbooks & SOPs
docs/audit/phase5-release/02-analysis/observability-telemetry.md
 -> Telemetry architecture, SLA metrics, and diagnostics
