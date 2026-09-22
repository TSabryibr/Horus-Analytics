# Layer 3: Architecture Decision Records (ADRs)

**System:** Horus Analytics II  
**Audited By:** `technical-architect`, `orchestrator`  

---

## ADR-001: Migration to SQLite Online Backup API for Mubasher Ingestion

### Status: Proposed (Phase 3 Target)

### Context
Horus ingests 1-minute intraday bars and history from Mubasher Pro SQLite databases located in `%APPDATA%\MubasherTrade\PRO Egypt\UserData\<user_id>\...`.
The current mechanism in `data_engine/mubasher_extractor.py` uses `shutil.copy2` to create a shadow copy in `.tmp/mubasher_shadow`. On Windows, when Mubasher Pro is actively writing, `shutil.copy2` causes `[WinError 32]` file access conflicts or copies torn pages. Furthermore, the function temporarily mutates global `settings.MUBASHER_ROOT_DIR` in-memory.

### Decision
1. Replace `shutil.copy2` with Python `sqlite3.connect().backup()`.
2. Connect to the source SQLite database using URI syntax with `mode=ro&immutable=1` so the OS file handle does not conflict with Mubasher's active writer lock.
3. Stream the backup to the shadow database with a chunked page copier.
4. Pass the shadow directory path explicitly into `ingest_intraday()` and `ingest_history()` as an argument, eliminating global `settings` thread mutation.

### Consequences
- **Positive:** Completely eliminates `[WinError 32]` lock errors on Windows.
- **Positive:** Guarantees atomic, crash-consistent snapshots of Mubasher intraday bars.
- **Positive:** Thread-safe; multiple background jobs can run concurrently without global state corruption.
- **Neutral:** Adds a small (~50ms) CPU overhead to execute page copy through the SQLite backup API.

---

## ADR-002: Embedded OS Execution State Management for Trading Sessions

### Status: Proposed (Phase 3 Target)

### Context
Horus is an automated signal and trade execution engine operated on a Windows workstation. Unattended Windows workstations enter Modern Standby / Sleep after 15–30 minutes of idle time. An external script `scripts/horus_keepalive.ps1` exists but requires manual execution outside the application. If not started, Windows sleep suspends the process, dropping market-hours signals and stop-loss monitoring.

### Decision
Embed Windows `SetThreadExecutionState` directly into `config/lifespan.py` using `ctypes.windll.kernel32`:
- **State Flag:** `ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED` (0x80000041).
- **Activation:** Automatically activated during market hours (10:00 – 14:30 EEST Sun–Thu) or during manual live feed streaming.
- **Deactivation:** Released when switching to post-market analysis mode (14:30 / 15:30) or during application shutdown.

### Consequences
- **Positive:** Zero manual intervention required; signal broadcasts and position monitoring are guaranteed uninterrupted by OS sleep.
- **Positive:** Display screen can safely turn off while the CPU and background timers remain 100% active.
- **Neutral:** Slightly increased workstation power consumption during the 4.5-hour trading window.

---

## ADR-003: Automated Daily SQLite Online Backup & 14-Day Retention

### Status: Proposed (Phase 4 Target)

### Context
The SQLite database `horus.db` holds all critical business data: subscriber accounts, portfolios, trades, signal recommendations, delivery logs, and latency telemetry. Currently, there is no automated backup system.

### Decision
Add a scheduled daily backup task in `config/scheduler_setup.py` at 15:45 (post-market):
1. Flush WAL pages to disk (`PRAGMA wal_checkpoint(TRUNCATE)`).
2. Use `sqlite3.backup()` to create a timestamped backup in `data/backups/horus_YYYYMMDD_HHMMSS.db`.
3. Verify backup integrity (`PRAGMA integrity_check`).
4. Prune snapshots older than 14 days.

### Consequences
- **Positive:** RPO reduced to ≤ 24 hours with zero server downtime.
- **Positive:** Instantaneous disaster recovery by swapping the backup file into place.
- **Neutral:** Consumes ~50MB per snapshot (~700MB total storage for 14 days).

---

## Sources & Deeper Analysis
- Technical Architecture: [`02-analysis/technical-architecture.md`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/docs/audit/hermes-swarm-audit-v2/02-analysis/technical-architecture.md)
- Site Reliability: [`02-analysis/site-reliability.md`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/docs/audit/hermes-swarm-audit-v2/02-analysis/site-reliability.md)
- Executive Summary: [`01-summary/executive-summary.md`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/docs/audit/hermes-swarm-audit-v2/01-summary/executive-summary.md)
