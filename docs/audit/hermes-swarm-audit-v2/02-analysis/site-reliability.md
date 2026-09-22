# Layer 2: Site Reliability Engineering Audit (Audit V2)

**Specialist Profile:** `site-reliability-engineer` (Hermes Swarm)  
**Target:** Live Trading Session Resilience, Scheduler Durability, and Disaster Recovery  
**Service Window:** EGX Trading Session (Sunday – Thursday, 10:00 – 14:30 EEST)  

---

## 1. Service Level Objectives (SLO) Architecture

For a proprietary commercial signal engine, reliability translates directly into trading revenue and subscriber retention:

```mermaid
graph TD
    subgraph Market Hours SLO Architecture (10:00 - 14:30 EEST)
        SLO1["SLO 1: Feed Freshness<br/>Max Feed Lag < 5m<br/>Target: 99.0%"]
        SLO2["SLO 2: Dispatch Latency<br/>Telegram RTT < 5000ms<br/>Target: 95.0%"]
        SLO3["SLO 3: Trade Exit Precision<br/>Monitor Loop < 30s<br/>Target: 99.5%"]
        SLO4["SLO 4: Daily Pipeline Execution<br/>Run on-time by 14:45<br/>Target: 100.0%"]
    end
```

| SLO | SLI (Metric) | Target | Current Status | Post-Phase 2 Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Feed Freshness** | Minutes elapsed since newest bar | `< 5.0m` | **Monitored & Self-Healed** | `MarketFeedWatchdog.check_and_heal()` |
| **Dispatch Latency** | Telegram round-trip latency (`latency_ms`) | `< 5,000ms (p95)` | **Measured & Tracked** | `SignalDelivery.latency_ms` + `/sla` |
| **Exit Precision** | Scheduled trade monitor interval | `30s ticks` | **Consolidated** | `SystemMonitor.monitor_system_positions` |
| **Daily Pipeline** | Execution of daily signal run | `14:45 EEST` | **At Risk (Misfire Bug)** | Needs `misfire_grace_time=300` |

---

## 2. Windows Workstation OS Power State & Sleep Hazard (P0 SRE Risk)

### The Problem: Modern Standby & Inactivity Sleep
The admin workstation runs Windows 11. By default, Windows enters "Modern Standby" or system sleep after 15–30 minutes of user inactivity (mouse/keyboard idle).

When Windows enters sleep:
1. All user-mode threads (including Uvicorn, Python, and APScheduler) are suspended by the Windows kernel.
2. APScheduler timers halt.
3. Real-time tick processing in `LiveFeedManager` stops.
4. Intraday stop-losses and take-profit targets are **not monitored**.
5. Scheduled 14:45 daily signal broadcasts **do not execute**.

### Why the Existing PowerShell Script is Insufficient
Horus has a helper script in [`scripts/horus_keepalive.ps1`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/scripts/horus_keepalive.ps1). However:
- It requires the admin to manually open an external PowerShell terminal and execute the script separately.
- If the admin forgets or closes the terminal, sleep protection is gone.
- It is decoupled from the actual backend process lifecycle.

### Recommended Solution: Embedded Kernel32 Execution State
Embed Windows keep-alive directly into [`config/lifespan.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/lifespan.py):
```python
import ctypes
import os

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_AWAYMODE_REQUIRED = 0x00000040

def set_windows_keep_alive(enable: bool = True) -> None:
    """Prevents Windows from entering sleep mode during active trading sessions."""
    if os.name != 'nt':
        return
    try:
        flags = ES_CONTINUOUS | (ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED if enable else 0)
        ctypes.windll.kernel32.SetThreadExecutionState(flags)
        logger.info(f"[SRE] Windows Keep-Alive state set to: enable={enable}")
    except Exception as exc:
        logger.warning(f"[SRE] Failed to set Windows Execution State: {exc}")
```
*Lifecycle Hook:* When `scheduled_enter_live_mode` triggers at 09:30, activate keep-alive. When `scheduled_enter_analysis_mode` triggers post-market at 15:30, release keep-alive.

---

## 3. APScheduler Misfire Dropping Audit

### The Misfire Vulnerability
In [`config/scheduler_setup.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/scheduler_setup.py):
```python
# Lines 102-108
scheduler.add_job(
    scheduling.scheduled_daily_signal_pipeline,
    'cron',
    hour=_env_int("SIGNAL_DAILY_RUN_HOUR", 14),
    minute=_env_int("SIGNAL_DAILY_RUN_MINUTE", 45),
    id='signal_daily_pipeline'
    # MISFIRE_GRACE_TIME MISSING!
)
```

**Impact:** APScheduler default `misfire_grace_time` is **1 second**. If the admin is exporting a large report, running a browser benchmark, or if Windows CPU is momentarily pegged at 14:45:00, the job misses its 1-second window. APScheduler logs `Run time of job ... was missed by 0:00:02` and **cancels the job completely**. The entire subscriber base misses their daily signals for that day.

**Fix:** Add explicit misfire grace times across all cron jobs:
```python
misfire_grace_time=300,  # 5-minute window
coalesce=True,           # Merge duplicate ticks into 1 execution
```

---

## 4. Zero-Downtime SQLite Backup & Disaster Recovery (RPO/RTO)

`horus.db` is the single point of truth for:
- 1,000+ Signal runs and candidate recommendations.
- All historical subscriber delivery records and latency telemetry.
- Active portfolio cash balances and position cost bases.

### Current RPO / RTO:
- **RPO (Recovery Point Objective):** Indefinite (Depends on manual git commits or manual file copies).
- **RTO (Recovery Time Objective):** Hours (Manual disaster reconstruction).

### Target SRE Backup Architecture
Add an automated daily backup job in `config/scheduler_setup.py` running at 15:45 (post-market):
1. **Checkpoint WAL:** `PRAGMA wal_checkpoint(TRUNCATE)` to flush dirty pages.
2. **Online Backup:** Use `sqlite3.connect().backup()` to snapshot `horus.db` to `data/backups/horus_backup_YYYYMMDD.db`.
3. **Integrity Check:** Execute `PRAGMA integrity_check` on the backup to ensure zero corruption.
4. **Prune Retention:** Retain the last 14 daily backups, deleting older files to prevent disk exhaustion.
- **Result:** RPO ≤ 24 hours, RTO ≤ 2 minutes (simple file rename).

---

## Sources & Deeper Analysis
- Executive Summary: [`01-summary/executive-summary.md`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/docs/audit/hermes-swarm-audit-v2/01-summary/executive-summary.md)
- Technical Architecture: [`02-analysis/technical-architecture.md`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/docs/audit/hermes-swarm-audit-v2/02-analysis/technical-architecture.md)
- Security Posture: [`02-analysis/security-posture.md`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/docs/audit/hermes-swarm-audit-v2/02-analysis/security-posture.md)
- Reliability & Telemetry Dossier: [`03-dossiers/reliability-telemetry.md`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/docs/audit/hermes-swarm-audit-v2/03-dossiers/reliability-telemetry.md)
