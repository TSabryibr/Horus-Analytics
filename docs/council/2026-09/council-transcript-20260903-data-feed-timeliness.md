# LLM Council Transcript: Data Feed Timeliness & App Tab Consumption Audit
## Full Pipeline: Source Ingestion → Freshness Evaluation → Sync Worker → Scheduled Scans → App Tab Delivery

**Date:** September 3, 2026  
**Session ID:** `council-20260903-data-feed-timeliness`  
**Topic:** Is the data feed arriving on time, and are the app tabs consuming the data feed correctly and promptly?  
**Framework:** Andrej Karpathy LLM Council (5 Cognitive Lenses + Peer Review + Chairman Synthesis)

---

## 1. Question Framing

### The Question
> *Evaluate the data feed pipeline end-to-end: Does data arrive on time from source providers through ingestion, freshness evaluation, and sync worker? Do the app tabs (scanner, data status, live feed) consume this data on time? Are there latency gaps, race conditions, stale-data risks, or timing mismatches between when data becomes available and when the app tabs use it?*

### System Under Audit
| Component | File | Role |
|---|---|---|
| **Mubasher SQLite Source** | `data_engine/mubasher_sqlite_source.py` | Primary data provider (1M candles from Mubasher desktop) |
| **DirectFN Feed Source** | `data_engine/directfn_feed_source.py` | Alternative CSV-based feed |
| **Ingest Intraday** | `data_engine/ingest_intraday.py` | Reads source → writes Parquet to intraday store |
| **Ingest History** | `data_engine/ingest_history.py` | EOD history ingestion to Parquet |
| **Freshness Evaluator** | `data_engine/freshness.py` | 592-line freshness engine with caching |
| **Pipeline Worker** | `data_engine/pipeline_worker.py` | Adaptive sync loop with exponential backoff |
| **Sync Orchestrator** | `data_engine/sync.py` | 3-stage pipeline: intraday → history → ticks |
| **Scheduler Setup** | `config/scheduler_setup.py` | APScheduler cron/interval job registration |
| **LiveFeedManager** | `core/market/LiveFeedManager.py` | ZeroMQ tick stream → 5M candle aggregation |
| **DailyScanner** | `core/DailyScanner.py` | `_maybe_sync_intraday()` + freshness gating |
| **Data Routes** | `routes/data.py` | REST API endpoints for data status/sync |

---

## 2. Independent Advisor Responses

### Advisor 1: The Contrarian
**Focus:** What timing failures are hiding in the pipeline?

The pipeline has several timing vulnerabilities:

1. **Freshness cache TTL creates a blind spot.** `_HISTORY_CACHE_TTL_SEC` defaults to 60s, and `_EVALUATE_FRESHNESS_CACHE` has a thread-locked cache. When `evaluate_freshness()` is called rapidly (e.g., scanner + pipeline worker + data status endpoint all within 60s), they share a cached result. If data arrives between cache refreshes, the system reports stale data for up to 60s after it's actually fresh. During market hours, this means the scanner could run against a cached freshness report that misses a just-completed ingest.

2. **`_maybe_sync_intraday()` throttle vs scan frequency mismatch.** The throttle is `INTRADAY_SYNC_MINUTES=5` (5 minutes minimum between syncs). But intraday scans fire every 5 minutes too. If the scan fires 1 second after the last sync completed, `_maybe_sync_intraday()` skips — but if Mubasher wrote new bars in that 1 second, the scan runs against stale data. The sync and scan are **not coordinated** — they're independent timers.

3. **Pipeline worker `_is_mubasher_unreachable()` uses a 30-minute staleness window** (`time.time() - mtime > 1800`). During EGX lunch breaks or low-activity periods, this can falsely flag the provider as unreachable, triggering provider_unreachable backoff (minimum 300s) and suppressing sync attempts even when the market reopens.

4. **`DATA_STATUS_CACHE_TTL_SEC` is 30s when market is open.** The data status endpoint serves cached status for 30s. A user checking the "Data" tab right after a sync completes might still see the pre-sync status. Not a data correctness issue, but a UX freshness issue.

---

### Advisor 2: The First Principles Thinker
**Focus:** Information flow invariants and theoretical correctness.

The data pipeline has a clear flow invariant:

$$\text{Source (Mubasher)} \xrightarrow{t_1} \text{Parquet Store} \xrightarrow{t_2} \text{Freshness Cache} \xrightarrow{t_3} \text{Scanner/App}$$

**End-to-end latency = $t_1 + t_2 + t_3$**

- $t_1$ (ingestion): Bounded by `ingest_intraday()` execution time (~10-30s for ~250 symbols).
- $t_2$ (cache invalidation): `invalidate_freshness_cache()` is called AFTER ingest completes. But the freshness cache TTL is 60s, so other consumers might still see stale cache for up to 60s.
- $t_3$ (consumption): Scanner calls `evaluate_freshness()` at scan start. If the cache was populated right before ingest completed, the scanner sees stale freshness for up to 60s.

**Theoretical worst-case latency:** Ingest takes 30s, cache was refreshed 1s before ingest started → cache remains valid for 59 more seconds → scanner fires 58s later → uses cache from 89s ago → **scanner sees data that is 89 seconds stale.**

**In practice:** The `_maybe_sync_intraday()` function explicitly calls `ingest_intraday()` when freshness is not OK, which writes new data AND implicitly makes the next `evaluate_freshness()` call see the new data. The issue is only for **concurrent consumers** (pipeline worker + scanner + API endpoint running simultaneously).

**The `invalidate_freshness_cache()` function is the critical correctness mechanism.** It's called in `sync.py` after each stage. This is correct — but only if all data paths go through `sync_all()`. The `_maybe_sync_intraday()` path in DailyScanner calls `ingest_intraday()` directly WITHOUT calling `invalidate_freshness_cache()`.

---

### Advisor 3: The Expansionist
**Focus:** What's working well and what opportunities exist?

The `AdaptiveSyncWorker` architecture is excellent:
- **Exponential backoff with jitter** prevents thundering herd on source recovery
- **FRESH/STALE/DEGRADED tri-state** gives clear operational visibility
- **Closed-session verification** — one final sync pass before idling prevents EOD data gaps
- **ANALYSIS→LIVE mode promotion** — detects market open during startup and transitions automatically
- **Provider unreachability detection** — checks Mubasher DB mtime to avoid hammering a dead source

**Session mode transitions are well-timed:**
- LIVE mode enters 30 minutes before market open
- ANALYSIS mode enters at market close
- The watchdog pauses `intraday_scan` and `trade_monitor` when market closes

**Opportunity: The freshness evaluation returns rich metadata** (`fresh_ratio`, `live_ratio`, `age_mins`, per-ticker staleness) that could power a real-time data health dashboard tab. Currently the data status endpoint caches for 30s which is reasonable but could be more granular.

---

### Advisor 4: The Outsider
**Focus:** What's confusing or inconsistent about the data flow?

1. **Two independent sync paths.** `_maybe_sync_intraday()` in DailyScanner calls `ingest_intraday()` directly. `AdaptiveSyncWorker._run_loop()` calls `sync_all()` which calls `ingest_intraday()` + `ingest_history()` + `ingest_ticks()`. These two paths can **race**: if the scanner triggers `_maybe_sync_intraday()` while the pipeline worker is also running `sync_all()`, they both call `ingest_intraday()`. The `_ingestion_lock()` (PID file) prevents concurrent execution, but the second caller silently skips — meaning one of them thinks sync completed when it actually didn't run.

2. **The Mubasher harvester runs on a separate 5-minute interval** (line 219 in scheduler_setup.py). So we have THREE independent timers touching intraday data: (a) harvester extracts Mubasher → CSV, (b) pipeline worker syncs CSV → Parquet, (c) scanner's `_maybe_sync_intraday()`. These are not phase-locked.

3. **The `LiveFeedManager` ZMQ tick stream is a completely separate data path** from the batch ingestion. It receives raw ticks via ZeroMQ, aggregates into 5M candles, and evaluates breakouts against cached resistance levels. But the DailyScanner doesn't consume LiveFeedManager data — it reads from the Parquet intraday store. So there's a **dual-path divergence**: LiveFeedManager might fire a breakout alert from real-time ticks, but the DailyScanner's next scan might not see the same data because the Parquet store hasn't been updated yet.

4. **Freshness cache invalidation is called in `sync.py`** (line 5: `from data_engine.freshness import invalidate_freshness_cache`), but I don't see it called inside `ingest_intraday()` itself. If `_maybe_sync_intraday()` calls `ingest_intraday()` directly (bypassing `sync_all()`), the freshness cache is NOT invalidated.

---

### Advisor 5: The Executor
**Focus:** Operational reliability and scheduling correctness.

**Scheduler job timing analysis (EGX market hours ~10:00-14:30):**

| Job | Schedule | When |
|---|---|---|
| `session_enter_live` | Cron, 30m before market open | ~09:30 |
| `intraday_scan` | Interval, 5m (paused when market closed) | 10:00-14:30 |
| `pre_close_scan` | Cron, before market close | ~14:10 |
| `daily_signal_scan` | Cron, after market close | ~14:45 |
| `signal_daily_pipeline` | Cron, env-configured | 14:45 |
| `trade_monitor` | Interval, 30s (paused when market closed) | 10:00-14:30 |
| `market_watchdog` | Interval, 5m | Always |
| `mubasher_extractor` | Interval, 5m (if enabled) | Always |
| `session_enter_analysis` | Cron, at market close | ~14:30 |

**Timing correctness:**
- Pre-market (09:30): LIVE mode enters, pipeline worker starts syncing
- Market open (10:00): Watchdog resumes intraday_scan and trade_monitor
- During session: intraday_scan (5m), trade_monitor (30s), pipeline worker (adaptive)
- Pre-close (14:10): Pre-close scan fires
- Close (14:30): Watchdog pauses heavy jobs, session → ANALYSIS
- Post-close (14:45): Daily signal pipeline runs with EOD data

**One concern:** The `coalesce=True` on most jobs means if a job fires while the previous instance is still running, the new instance is coalesced (dropped). If `ingest_intraday()` takes longer than 5 minutes (e.g., Mubasher DB is slow), the next intraday_scan fires, calls `_maybe_sync_intraday()`, which skips because the throttle timestamp was set by the still-running sync. This means **one slow sync can cause the next scan to use stale data.**

---

## 3. Peer Review

| Reviewer | Strongest | Biggest Blind Spot | What ALL Missed |
|---|---|---|---|
| **Contrarian** | Outsider | First Principles missed that `_maybe_sync_intraday()` doesn't call `invalidate_freshness_cache()` | Race between pipeline worker and scanner sync paths isn't just theoretical — it happens every market day |
| **First Principles** | Outsider | Expansionist didn't address the dual-path divergence (LiveFeed vs Parquet) | The lock file approach in `_ingestion_lock()` has a 10-minute stale lock recovery window — too long for intraday |
| **Expansionist** | First Principles | Contrarian's 30-minute unreachable window might be appropriate for EGX (no lunch break, but low-activity periods) | None addressed the data quality layer (`data_engine/data_quality.py`) and whether rejected rows affect timeliness |
| **Outsider** | Contrarian | Executor didn't mention that `misfire_grace_time` on signal jobs could cause late scans | The Mubasher harvester → CSV → Parquet pipeline has 3 hops, each with independent timing |
| **Executor** | Outsider | Contrarian exaggerated the 89s worst case — `invalidate_freshness_cache()` in sync.py mitigates this | WebSocket push to dashboard isn't addressed — how does the frontend know when data refreshes? |

---

## 4. Chairman Verdict

### Where the Council Agrees
> **The data feed pipeline is architecturally sound and operationally robust.** The AdaptiveSyncWorker with tri-state classification, exponential backoff, closed-session verification, and provider reachability detection is production-grade. Scheduler job timing aligns with EGX market hours. The freshness evaluation provides rich metadata for operational monitoring.

### Where the Council Clashes

| Issue | Position A | Position B | Resolution |
|---|---|---|---|
| **Freshness cache invalidation gap** | First Principles + Outsider: `_maybe_sync_intraday()` doesn't call `invalidate_freshness_cache()` — stale cache persists | Executor: The cache TTL is only 60s, so it self-heals | **P1 Fix needed** — add `invalidate_freshness_cache()` after `ingest_intraday()` in `_maybe_sync_intraday()` |
| **Dual-path divergence (LiveFeed vs Parquet)** | Outsider: LiveFeedManager and DailyScanner see different data | Expansionist: These serve different purposes (real-time alerts vs batch signals) | **By design** — LiveFeed is for tick-level breakout alerts, Scanner is for signal generation |
| **Race between sync paths** | Outsider: Pipeline worker and scanner sync can race | Executor: `_ingestion_lock()` prevents concurrent execution | **Acceptable** — lock prevents corruption, the skip is safe behavior |

### Blind Spots the Council Caught

1. **`_maybe_sync_intraday()` bypasses `invalidate_freshness_cache()`.** When DailyScanner directly calls `ingest_intraday()`, the freshness cache is not cleared. Subsequent `evaluate_freshness()` calls by other consumers (pipeline worker, data status API) return stale freshness reports for up to 60 seconds. **Severity: Medium. Priority: P1.**

2. **Three independent timers touching intraday data are not phase-locked.** Harvester (5m) → Pipeline worker (adaptive) → Scanner sync (5m). In the worst case, data flows through 3 async hops before reaching the scanner. **Severity: Low. Priority: P3** (inherent in async architecture).

3. **WebSocket/frontend refresh mechanism not audited.** How does the dashboard tab know when to re-fetch data status? If it polls on a timer, there's an additional display latency. **Severity: Low. Priority: P3.**

### The Recommendation
> **The data feed arrives on time in the common case.** The end-to-end latency is bounded by ingestion time (~30s) + cache TTL (60s) + scan interval (5m) ≈ **~6 minutes worst case** from source update to scanner consumption. This is acceptable for a 5-minute interval scanner.
>
> **One fix is required:** Add `invalidate_freshness_cache()` to `_maybe_sync_intraday()` after `ingest_intraday()` completes successfully. This ensures that when the scanner syncs data itself, the freshness cache reflects the new data immediately.

### The One Thing to Do First
> Add `invalidate_freshness_cache()` call to `_maybe_sync_intraday()` in `DailyScanner.py` after the `ingest_intraday.ingest_intraday()` call on line 114.
