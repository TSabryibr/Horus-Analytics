# Layer 2: Site Reliability Engineering (SRE) Analysis (Amended)

**Author:** `site-reliability-engineer`  
**System:** Horus Analytics II (`c:\Users\TSabr\Horus\Horus-Analytics-II`)  
**Context:** **High-Precision Market Signal & Subscriber Dispatch Station**

---

## 1. Commercial SLOs for Signal Services

When operating a subscription signal business, reliability during market hours is paramount:

| Critical Window | Operation | Target SLA | Business Failure Mode |
| :--- | :--- | :--- | :--- |
| **09:45–10:00 Cairo Time** | Pre-market baseline sync & holiday checks | $\ge 99.9\%$ readiness | Terminal enters "DEGRADED" mode; morning signals blocked |
| **10:00–14:30 Cairo Time** | Intraday scanning & trailing stop monitors | $< 2.5\text{s}$ scan latency | SQLite lock delay; missed breakout / exit alerts |
| **14:40–15:00 Cairo Time** | Daily market close signals & report broadcast | On-time delivery by 14:50 | Delayed subscriber updates; diminished service trust |

---

## 2. Root Cause Analysis: The Two Main Operational Bottlenecks

### Bottleneck 1: SQLite Lock Contention During Active Trading
- In [`config/scheduler_setup.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/scheduler_setup.py#L76-L100), `trade_monitor` and `followup_processing` run every 30 seconds.
- In [`data_engine/`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/data_engine), live market ticks are ingested into SQLite checkpoints.
- **The Issue:** While WAL mode permits multiple concurrent readers, SQLite serializes all writes to a single thread. When background sync runs a transaction, user actions on the local terminal UI or outgoing signal status updates queue up.
- **SRE Solution:** Channel non-critical background writes through a queued single-writer thread with exponential backoff so interactive terminal queries and urgent signal dispatches never face a locked database.

### Bottleneck 2: Startup Race Condition Causing 5.2 MB Error Cascade
- In [`api_errors.log.1`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/api_errors.log.1), thousands of recurring tracebacks occur:
  ```text
  peewee.OperationalError: no such table: signalguardstate
  ```
- **The Issue:** When services or scheduler jobs trigger before [`initialize_db()`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/database/connection.py#L150) completes table creation and auto-migrations, the signal publishing desk enters an error state.
- **SRE Solution:** In [`config/lifespan.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/lifespan.py), enforce strict sequential gating: database tables and migrations must be 100% verified before starting the APScheduler or accepting requests.

---

## 3. Test Suite Restoration (98 Regressions)

A reliable signal delivery business requires high confidence in its calculation math. [`failed_tests_r2.txt`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/failed_tests_r2.txt) documents 98 test failures across:
1. **Portfolio Service Intake & Calculations (28 tests):** Risk calculation math, holding inputs, and intake parsing.
2. **Signal Lifecycle & SLA Verification (24 tests):** Verification of signal publishing, guard states, and delivery retries (`TestPublishAndSLA`).
3. **Risk Management & Correlation Deadbolts (15 tests):** Correlation calculations that prevent over-concentration in single sectors.

Fixing these 98 tests ensures that new features or setting changes will never degrade the accuracy or timing of subscriber recommendations.

---

## SOURCES (LAYER 3 NAVIGATION)

- [`03-dossiers/reliability-telemetry.md`](file:///C:/Users/TSabr/.gemini/antigravity/brain/c45fd366-d276-45c2-8215-42dfda3dbf44/03-dossiers/reliability-telemetry.md)  
  $\rightarrow$ Full error log excerpts, stack traces, and the 98-item failed test roster.
