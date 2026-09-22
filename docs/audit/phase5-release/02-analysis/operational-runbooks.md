# Horus Analytics II — Operational Runbooks & Standard Operating Procedures (SOPs)
**Artifact Layer:** Layer 2 (Operational Procedures)  
**Swarm Specialist:** `site-reliability-engineer`  
**Target:** Workstation Operator Daily Procedures, Monitoring, and Incident Recovery  
**Date:** September 5, 2026  
**Status:** **OPERATIONAL & PRODUCTION-READY**  

---

## 1. Operational Overview & Workstation Profile

Horus Analytics II is deployed on a dedicated high-performance local workstation operated by a single system owner:
- **Binding:** `127.0.0.1:8000` (loopback only, zero unauthenticated external ingress).
- **Timezone Base:** `Africa/Cairo` (EGX Trading Session: 10:00 – 14:30 Sun–Thu).
- **Execution Runtime:** Python 3.13 (`.venv313`) on Windows 11.
- **Database:** Local SQLite database (`horus.db`) with WAL (Write-Ahead Logging) and automatic daily snapshots.

---

## 2. Standard Operating Procedures (SOPs)

### SOP-01: Pre-Close & Intraday Scanning Operations

#### Context & Objectives
The Pre-Close scan is the primary alpha generation event for EGX equities. It evaluates macro breadth, sector rotation, institutional accumulation, and Sovereign Hedge traps between **14:15 and 14:45 Cairo Time** to generate buy/sell recommendations before market close.

```
       14:00                   14:15                   14:30                   14:45
   ┌───────────┐           ┌───────────┐           ┌───────────┐           ┌───────────┐
   │ Real-time │ ────────► │ Pre-Close │ ────────► │  Market   │ ────────► │ Post-Close│
   │ Intraday  │           │   Scan    │           │   Close   │           │ Reconcile │
   └───────────┘           └───────────┘           └───────────┘           └───────────┘
```

#### Step-by-Step Operator Procedure

1. **Pre-Flight Sanity Verification (14:10 Cairo Time):**
   - Query the system health endpoint:
     ```powershell
     curl -s http://127.0.0.1:8000/api/v1/system/boot-status
     ```
   - Ensure `"system_ready": true` and `"pipeline_state": "FRESH"`.
   - Verify that today is not an EGX trading holiday (`config/egx_holidays.json`).

2. **Automated vs Manual Scan Trigger:**
   - **Automated Execution:** The scheduler automatically triggers `DailyScanner.run_preclose_scan()` at 14:20 Cairo time.
   - **Manual Execution (CLI / API):**
     If automated execution is delayed or operator wishes an early preview:
     ```powershell
     # Via REST API:
     curl -X POST http://127.0.0.1:8000/api/v1/scanner/pre-close/run

     # Or via direct CLI script:
     .venv313\Scripts\python -m core.DailyScanner --mode preclose
     ```

3. **Output Review & Conviction Gate Validation:**
   - Review generated recommendations in the Operator Dashboard (`http://127.0.0.1:3000/signals` or `/api/v1/signals/latest`).
   - Confirm conviction score meets minimum dispatch threshold:
     - **High Conviction:** $\ge 3.5$ (Eligible for instant broadcast).
     - **Moderate Conviction:** $2.5 - 3.4$ (Advisory tier only).
     - **Filtered Out:** $< 2.5$ (Suppressed by Confluence Engine).
   - Check that `SovereignConfluenceEngine.get_active_trap(ticker)` does not flag a bull/bear trap on the candidate asset.

4. **Fallback & Anomaly Handling:**
   - **Stale Feed:** If quote feed is $> 5$ minutes old, the system enters `STALE_MODE`. The UI alerts the operator. Force a synchronous market data pull:
     ```powershell
     curl -X POST http://127.0.0.1:8000/api/v1/data/sync/force
     ```

---

### SOP-02: Market Watchdog & Scheduler Triage

#### Context & Objectives
The Market Watchdog (`core/market_watchdog.py`) runs on a background APScheduler interval (every 5 minutes during trading hours, coalesced to prevent queue flooding during workstation sleep). It ensures pipeline freshness, monitors data ingestion lag, and validates execution readiness.

#### Heartbeat Monitoring & Health Indicators

Check scheduler status at any time:
```powershell
curl -s http://127.0.0.1:8000/api/v1/system/full-status | jq .scheduler
```
Expected output:
```json
{
  "running": true,
  "jobs": [
    {
      "id": "market_watchdog",
      "next_run": "2026-09-06 10:05:00",
      "trigger": "interval[0:05:00]"
    },
    {
      "id": "market_watchdog_open",
      "next_run": "2026-09-06 10:00:00",
      "trigger": "cron[hour='10', minute='0']"
    }
  ]
}
```

#### Triage Matrix for Scheduler Anomalies

| Symptom | Root Cause | Operator Action |
| :--- | :--- | :--- |
| **Scheduler not running** | Background worker thread aborted or unhandled exception during startup. | Restart application via `config/startup.py` or inspect `logs/horus.log` for fatal initialization tracebacks. |
| **`market_watchdog` missing from jobs** | Registration failed during startup. | Check `tests/test_market_watchdog_registration.py` logic and verify `settings.MARKET_WATCHDOG_INTERVAL_MINUTES > 0`. |
| **Misfired jobs after workstation sleep** | PC slept during market hours. APScheduler coalesces jobs safely. | Normal behavior (`coalesce=True`, `misfire_grace_time=60`). The next interval executes cleanly without duplicate spikes. |

---

### SOP-03: Subscriber Lifecycle & Telegram Incident Management

#### Context & Objectives
Signal delivery executes across Telegram channels and private subscriber chats. With Phase 3/4 hardening, unrecoverable errors (e.g. 403 bot blocked, user deactivated, chat not found) fast-abort on attempt 1 and auto-pause subscribers after 3 consecutive failures.

```
                  ┌───────────────────────────────┐
                  │ Signal Generated & Validated  │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                     [ Telegram Dispatch Loop ]
                                  │
         ┌────────────────────────┴────────────────────────┐
         │                                                 │
    [ HTTP 200 OK ]                               [ HTTP 400 / 403 ]
         │                                                 │
         ▼                                                 ▼
Reset Failure Counter                           Fast-Abort Retries (0s sleep)
delivery_paused = False                         Increment Failures
                                                If Failures >= 3: delivery_paused = True
```

#### Diagnosing Delivery Failures
To inspect subscribers currently in failure or paused state:
```powershell
curl -s http://127.0.0.1:8000/api/v1/subscribers?paused_only=true | jq .
```

#### Recovery Runbook by Failure Code

1. **Failure Code: `SUBSCRIBER_BLOCKED_BOT` (HTTP 403)**
   - **Cause:** Subscriber tapped "Stop and Block Bot" in Telegram or deactivated account.
   - **Diagnosis Output:**
     - `failure_code`: `"SUBSCRIBER_BLOCKED_BOT"`
     - `operator_action`: *"The recipient has blocked the Telegram bot or deactivated their account. Verify status with subscriber or remove subscription."*
     - `subscriber_action`: *"Please unblock the bot and send /start in Telegram to resume receiving signals."*
   - **Resolution Steps:**
     1. Notify the subscriber to open Telegram, unblock the Horus bot, and send `/start`.
     2. Once confirmed, unpause the subscriber via the dashboard or API:
        ```powershell
        curl -X POST http://127.0.0.1:8000/api/v1/subscribers/<SUBSCRIBER_ID>/resume
        ```
     3. The system resets `consecutive_delivery_failures = 0` and `delivery_paused = False`.

2. **Failure Code: `CHAT_NOT_FOUND` (HTTP 400)**
   - **Cause:** Invalid or mistyped `telegram_chat_id` during onboarding.
   - **Resolution Steps:**
     1. Prompt subscriber for their numerical chat ID (via `@userinfobot`).
     2. Update chat ID:
        ```powershell
        curl -X PATCH http://127.0.0.1:8000/api/v1/subscribers/<SUBSCRIBER_ID> \
          -H "Content-Type: application/json" \
          -d '{"telegram_chat_id": "<NEW_CHAT_ID>", "delivery_paused": false}'
        ```

3. **Failure Code: `TELEGRAM_RATE_LIMIT` (HTTP 429)**
   - **Cause:** Telegram API rate limits breached.
   - **Behavior:** The dispatcher does **not** abort; it respects Telegram's `retry_after` header and completes delivery.
   - **Action:** No operator intervention needed; automatic recovery.

4. **Secret Redaction Audit:**
   - Verify that no bot tokens are visible in error logs:
     ```powershell
     grep -i "bot" logs/horus.log | grep -v "/bot<redacted>/"
     ```
   - Must return zero lines containing raw tokens.

---

### SOP-04: Disaster Recovery & Database Backup Restoration

#### Context & Objectives
The system uses SQLite in WAL mode. Automated daily snapshots are written to `backups/`. In the event of disk corruption, accidental data modification, or failed migrations, use this procedure to restore full service within 3 minutes.

#### Automated Backup Architecture
- **Tool:** `database/backup.py` (`backup_database()`).
- **Trigger:** APScheduler runs daily backup post-market at 15:30 Cairo time.
- **Location:** `backups/horus_backup_YYYYMMDD_HHMMSS.db`.
- **Retention:** Rolling 30 daily snapshots retained automatically.

#### Verification of Database Integrity
Run periodic integrity checks:
```powershell
.venv313\Scripts\python -c "import sqlite3; con = sqlite3.connect('horus.db'); print(con.execute('PRAGMA integrity_check').fetchall())"
```
Expected output: `[('ok',)]`

#### Point-in-Time Recovery Procedure

1. **Stop Application:**
   Terminate any running backend processes:
   ```powershell
   Get-Process -Name python | Where-Object { $_.Path -like "*Horus*" } | Stop-Process -Force
   ```

2. **Quarantine Corrupted Database:**
   ```powershell
   Move-Item -Path "horus.db" -Destination "horus_corrupt_$(Get-Date -Format yyyyMMdd_HHmmss).db"
   if (Test-Path "horus.db-wal") { Remove-Item "horus.db-wal" }
   if (Test-Path "horus.db-shm") { Remove-Item "horus.db-shm" }
   ```

3. **Select Latest Valid Snapshot:**
   ```powershell
   $latestBackup = Get-ChildItem -Path "backups\horus_backup_*.db" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
   Write-Host "Restoring from: $($latestBackup.FullName)"
   Copy-Item -Path $latestBackup.FullName -Destination "horus.db"
   ```

4. **Validate Snapshot Integrity:**
   ```powershell
   .venv313\Scripts\python -c "import sqlite3; con = sqlite3.connect('horus.db'); assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'; print('Snapshot verified successfully.')"
   ```

5. **Restart Service & Verify Health:**
   Launch backend and confirm via `/api/v1/system/full-status`:
   ```powershell
   .venv313\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

---

## 3. Canonical Sources & Cross References

SOURCES (LAYER 2 NAVIGATION)
docs/audit/phase5-release/00-index.md
 -> Pyramid root navigation index
docs/audit/phase5-release/01-summary/release-summary.md
 -> Executive release declaration and handover
docs/audit/phase5-release/02-analysis/observability-telemetry.md
 -> Telemetry architecture, SLA metrics, and diagnostics
docs/audit/phase5-release/03-dossiers/release-manifest.md
 -> Release manifest, component inventory, and deployment checklist
