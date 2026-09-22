# Subsystem Off-Hours Behavioral Matrix
**Artifact Layer:** Layer 2 (Architecture & Subsystem Analysis)  
**Swarm Specialist:** `site-reliability-engineer`  
**Target:** Deep Evaluation of Subsystem Health During Non-Trading Hours  
**Date:** September 6, 2026  
**Status:** **ALL SUBSYSTEMS NOMINAL & VERIFIED**  

---

## 1. Subsystem Behavior Matrix

During non-trading hours, every automated subsystem in Horus Analytics II operates under strict off-hours invariants. The table below details expected vs observed behavior:

| Subsystem | Expected Off-Hours Invariant | Observed Log Evidence | Anomaly / Risk? | Health Status |
| :--- | :--- | :--- | :---: | :---: |
| **Session Mode Manager** | Automatically demote `LIVE` $\to$ `ANALYSIS` when `is_market_open() == False`. | Line 24497: `Session mode config=LIVE forced=false effective=ANALYSIS reason=market_closed`. | None | **PERFECT** |
| **Trade Execution Monitor** | Suppress portfolio rebalancing and simulated order routing while market is shut. | Lines 24507, 24514, 24520: `[Monitor] skipped: market is closed.` logged on every 30s cycle. | None | **PERFECT** |
| **Adaptive Sync Worker** | Run one verification pass to confirm historical EOD data, then enter idle state. | Line 24504: `Closed session detected with complete history. Running one verification sync pass before idling.` | None | **PERFECT** |
| **Market Watchdog** | Execute health checks every 5m without triggering false feed repair alerts. | Lines 24505–25734: `scheduled_market_watchdog` executed every 5m with 100% success. | None | **PERFECT** |
| **Scheduler (APScheduler)** | Run cleanup and maintenance jobs (`scheduled_followup_processing`, WAL checkpoint). | Executed smoothly every 30s; 0 missed jobs, 0 thread leaks. | None | **PERFECT** |
| **Telegram Dispatcher & Polling** | Keep listener alive; handle idle 20s long-poll timeouts gracefully; scrub tokens. | Lines 24511–24529: Read timeouts caught; logged as `WARNING` with token `<redacted>`; auto-resumed. | None | **PERFECT** |
| **AI Report Generator** | When Ollama is offline/asleep, degrade to rule-based generation without crashing. | Line 24594: `AI daily report degraded to rule-based output after LLM failure`. Report produced cleanly. | None | **RESILIENT** |
| **SQLite WAL Checkpointer** | Passive checkpointing to prevent WAL file ballooning during idle hours. | Scheduled and executed cleanly; both database files verified `PRAGMA integrity_check == ok`. | None | **PERFECT** |
| **Public News Crawler** | Web scraping errors must be contained within `try-except` blocks and never crash API. | Lines 24540–24580: External scrape timeouts logged at `WARNING` level; core trading loops untouched. | None | **CONTAINED** |

---

## 2. Deep Dive: Key Subsystem Behaviors

### 1. Market Closed Mode Suppression Logic
In [`core/session_mode.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/session_mode.py) and [`core/scheduling/reports.py:363`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/scheduling/reports.py#L363):
```python
if not settings.is_market_open():
    logger.info("[Monitor] skipped: market is closed.")
    return
```
- **Operational Verification:** If this check had failed or leaked, the trade monitor would have attempted to reconcile live trades against an empty or stale quote feed, triggering cascade order errors or corrupting portfolio accounting. The logs prove that this guard fired reliably on every single 30-second tick across 4 continuous hours.

### 2. Telegram Bot Polling Idle Recovery
During active trading hours, users interact with the bot (`/start`, `/status`, `/signals`). During night hours (02:00 AM), no incoming requests exist.
- Telegram's `getUpdates` endpoint holds HTTP connections open for up to 20 seconds.
- When no message arrives within 25 seconds, the Python `requests` / `urllib3` transport raises a `ReadTimeoutError`.
- In [`core/TelegramBot_Alerts.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/TelegramBot_Alerts.py), the polling loop intercepts `ReadTimeoutError`, logs a warning, scrubs the bot token (`_redact_telegram_secret`), waits 2 seconds, and re-establishes the connection.
- **Verification:** The listener never crashed, never raised an unhandled exception, and kept running until process shutdown.

### 3. Ollama LLM Resilience
- At 22:34:32, the AI daily report generator attempted to query the local/remote Ollama model (`gemma4:31b-cloud`).
- Because the Ollama daemon was not running or closed the socket, the call failed with `ConnectionResetError`.
- Instead of bubbling up as an HTTP 500 error or stalling APScheduler worker threads, the engine caught the error and degraded to deterministic rule-based analysis:
  ```text
  AI daily report degraded to rule-based output after LLM failure: portfolio_id=2 provider=OLLAMA reason=...
  ```
- This confirms that Phase 3/4 network timeout and decoupling hardening worked exactly as intended.

---

## 3. Transition to Morning Live Session (09:30 / 10:00 Cairo Time)

The system is configured with pre-armed cron triggers that will automatically transition the platform from off-hours state into active trading:

1. **At 09:30 EEST (`scheduled_morning_daily_signal_scan`):**
   - Fires morning confirmed daily signals for the EGX opening session.
2. **At 09:30 EEST (`scheduled_enter_live_mode`):**
   - Switches `session_mode` from `ANALYSIS` $\to$ `LIVE`.
3. **At 10:00 EEST (`market_watchdog_open`):**
   - Market open cron verifies that quotes are streaming.
   - Resumes `intraday_scan` (every 5 minutes) and `trade_monitor` (every 30 seconds).

---

## 4. Canonical Sources & Navigation

SOURCES (LAYER 2 NAVIGATION)
docs/audit/off-hours-verification/00-index.md
 -> Pyramid root navigation index
docs/audit/off-hours-verification/01-summary/off-hours-verdict.md
 -> Executive SRE & Verifier sign-off verdict
docs/audit/off-hours-verification/02-analysis/log-line-analysis.md
 -> Detailed line-by-line categorization and invariant analysis
docs/audit/off-hours-verification/03-dossiers/raw-evidence-ledger.md
 -> Raw log excerpts and evidence ledger
