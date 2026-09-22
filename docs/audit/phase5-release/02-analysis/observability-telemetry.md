# Horus Analytics II — Observability, Telemetry & Health Monitoring
**Artifact Layer:** Layer 2 (Telemetry & Observability Architecture)  
**Swarm Specialist:** `site-reliability-engineer`  
**Target:** Metrics, SLA Latency Tracking, Diagnostics, and Logging Architecture  
**Date:** September 5, 2026  
**Status:** **OPERATIONAL & PRODUCTION-READY**  

---

## 1. Observability Architecture Overview

Horus Analytics II implements a defense-in-depth telemetry architecture designed for high-frequency algorithmic scanning, resilient message dispatch, and single-operator local administration.

```
       ┌─────────────────────────────────────────────────────────────┐
       │                   HORUS TELEMETRY ENGINE                    │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│ System & Runtime │        │ Signal Delivery  │        │ Logging & Audit  │
│ Health Endpoints │        │  SLA Latencies   │        │     Trails       │
│  (/full-status,  │        │ (Histogram P99,  │        │ (logs/, Peewee   │
│   /boot-status)  │        │   Breach Rates)  │        │  AuditEvent ORM) │
└──────────────────┘        └──────────────────┘        └──────────────────┘
```

---

## 2. Telemetry Endpoints Specification

### 1. `/api/v1/system/boot-status` (Lightweight Heartbeat)
- **Route:** `GET /api/v1/system/boot-status` (Public loopback)
- **Response Target:** $< 5\text{ms}$
- **Purpose:** Used by startup scripts, container orchestrators, and quick UI status indicators.
- **Key Fields:**
  ```json
  {
    "status": "READY",
    "system_ready": true,
    "pipeline_state": "FRESH",
    "bootstrap_complete": true,
    "stale_mode": false,
    "last_sync": "2026-09-05T14:30:00"
  }
  ```

### 2. `/api/v1/system/full-status` (Comprehensive Deep Health)
- **Route:** `GET /api/v1/system/full-status` (Public loopback)
- **Purpose:** Aggregates overall health across all backend subsystems:
  - **Pipeline State:** Freshness score, synchronization worker status, durable provisioning progress.
  - **Scheduler Status:** Live inventory of active APScheduler jobs with next scheduled trigger times.
  - **Alert Channels:** Telegram bot connection state, Discord webhook status.
  - **Signal Metrics:** Total lifetime signals generated, timestamp of latest signal run.
  - **Database Backup:** Snapshot status, path to latest snapshot, rolling backup count.
  - **Delivery SLA Metrics:** 7-day rolling Telegram delivery latencies and histogram buckets.

### 3. `/api/v1/system/diagnostics/memory` (Process Health & Resource Bounds)
- **Route:** `GET /api/v1/system/diagnostics/memory`
- **Purpose:** Detects memory leaks, uncollected dataframes, and stalled background threads.
- **Payload Structure:**
  ```json
  {
    "pid": 14920,
    "rss_mb": 348.5,
    "vms_mb": 1102.4,
    "threads_count": 8,
    "open_files_count": 42,
    "thread_inventory": [
      {"name": "MainThread", "daemon": false, "alive": true},
      {"name": "APScheduler", "daemon": true, "alive": true},
      {"name": "ComputeWorker-1", "daemon": true, "alive": true}
    ]
  }
  ```

---

## 3. Signal Delivery SLA & Latency Histogram Tracking

### SLA Architecture (`core/signals/sla.py`)
Signal delivery requires predictable, low-latency dispatch to ensure subscribers receive trading signals within execution time windows. Every `SignalDelivery` record captures round-trip dispatch latency in milliseconds (`delivery.latency_ms`).

### Histogram Bucketing Model
Latencies are classified into 6 standardized distribution buckets:

| Bucket Range | Target Category | Operational Significance | Target Distribution |
| :--- | :--- | :--- | :---: |
| **`< 250ms`** | Ideal / Instant | Direct HTTP transport with low network overhead. | $> 60\%$ |
| **`250 - 500ms`** | Standard | Typical Telegram HTTPS round-trip under normal load. | $> 25\%$ |
| **`500 - 1000ms`** | Acceptable | Slight network or TLS handshake delay. | $< 10\%$ |
| **`1.0 - 2.5s`** | Marginal | Batch queue lag or minor external congestion. | $< 5\%$ |
| **`2.5 - 5.0s`** | Latency Breach Risk | Heavy network retry or transient rate-limit pause. | $< 1\%$ |
| **`> 5.0s`** | SLA Breached | Delivery exceeded target threshold ($5000\text{ms}$). | $0\%$ |

### 7-Day Rolling SLA Calculation
The `compute_delivery_sla_metrics(days=7)` function computes:
- **`success_rate_pct`:** $\frac{\text{Sent}}{\text{Sent} + \text{Failed}} \times 100\%$ (Target: $\ge 95.0\%$).
- **`sla_compliant`:** Evaluates `True` only when `success_rate_pct >= 95.0%` **and** `p95 <= 5000ms`.
- **Percentiles:** Calculated using NumPy (`np.percentile`) for $P50$, $P90$, $P95$, and $P99$.
- **Breach Analytics:** Total breached deliveries count and percentage.
- **Multi-Dimensional Breakdown:** Grouped by channel (`TELEGRAM`), subscriber tier (`SIGNALS_ONLY`, `MANAGED_EXECUTION`), and destination type (`PORTFOLIO`, `SUBSCRIBER`, `CHANNEL`).

---

## 4. Heavy Compute Task Decoupling & Queue SLA

### The Compute Offloading Pattern
To prevent Monte Carlo simulations, Ragnarok stress tests, and intensive backtesting runs from blocking the FastAPI event loop or starving the signal dispatcher:
1. **Dedicated Worker Pool:** Background execution is delegated to an isolated thread pool worker (`ThreadPoolExecutor`).
2. **Copy Semantics on Shared Cache:** Symbol universe cache references are shallow-copied under read-locks before passing to worker threads, preventing thread race conditions or cache corruption during live scanning.
3. **Lock Granularity:** Thread-safe read/write locks ensure that live price ingestion continues uninterrupted while compute workers execute heavy analytical passes.

---

## 5. Logging Strategy & Sanitization Hygiene

### Centralized Logger Configuration (`utils/logger.py`)
All subsystems must use the centralized `setup_logger(name)` factory:
- **Directory:** All logs are strictly contained in `logs/`.
- **Rotation:** `RotatingFileHandler` with `maxBytes = 10 * 1024 * 1024` (10 MB) and `backupCount = 5`.
- **Formatting:** `%(asctime)s [%(levelname)s] [%(name)s]: %(message)s`.
- **Zero Ad-Hoc Logs:** Unmanaged root logs (`scanner.log`, `autotrader.log`) have been eliminated.

### Secret Scrubbing Engine
In [`core/TelegramBot_Alerts.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/TelegramBot_Alerts.py), `_redact_telegram_secret()` actively intercepts any string, URL, or traceback containing bot tokens before logging or persisting:
- Matches Telegram bot URL pattern: `/bot[^/\s]+/` $\to$ `/bot<redacted>/`.
- Matches configured `TELEGRAM_TOKEN` and `TELEGRAM_TEST_BOT_TOKEN`.
- Verified by automated regression tests to guarantee zero secret leakage.

---

## 6. Audit Logging & Regulatory Trails

### Database Audit Event Model (`SignalAuditEvent`)
Every administrative action, deviation override, and critical signal event generates a tamper-evident row in `signal_audit_event`:
- `event_type`: e.g., `SIGNAL_CREATED`, `SIGNAL_PUBLISHED`, `SUBSCRIBER_PAUSED`, `OPERATOR_DEVIATION`.
- `severity`: `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- `payload`: Structured JSON metadata detailing before/after state and trigger context.
- `created_at`: Canonical simulated or wall-clock timestamp from `TimeUtils.now()`.

---

## 7. Canonical Sources & Cross References

SOURCES (LAYER 2 NAVIGATION)
docs/audit/phase5-release/00-index.md
 -> Pyramid root navigation index
docs/audit/phase5-release/01-summary/release-summary.md
 -> Executive release declaration and handover
docs/audit/phase5-release/02-analysis/operational-runbooks.md
 -> Operational Runbooks & SOPs
docs/audit/phase5-release/03-dossiers/release-manifest.md
 -> Release manifest, component inventory, and deployment checklist
