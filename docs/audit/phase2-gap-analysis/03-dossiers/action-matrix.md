# Phase 2 Action Matrix & Remediation Blueprint
**Artifact Layer:** Layer 3 (Dossier & Specifications)  
**Authors:** Swarm Review Swarm (`reviewer`, `site-reliability-engineer`, `qa-engineer`)  
**Target:** Implementation Blueprint for Phase 3 Execution

---

## 1. Remediation Priority Summary

```
        ┌────────────────────────────────────────────────────────┐
        │  P0 (CRITICAL) - 2 ITEMS                              │
        │  • Telegram Unrecoverable Error Fast-Abort & Pause     │
        │  • Market Watchdog Scheduler Coalescing & Off-Hours   │
        └──────────────────────────┬─────────────────────────────┘
                                   │
        ┌──────────────────────────┴─────────────────────────────┐
        │  P1 (HIGH) - 4 ITEMS                                  │
        │  • ConfluenceEngine Module/Class Name Collision        │
        │  • TimeUtils Wall-Clock Determinism Fix                │
        │  • Ollama Manager HTTP Network Timeouts               │
        │  • Subscriber Delivery Blocked Diagnosis               │
        └──────────────────────────┬─────────────────────────────┘
                                   │
        ┌──────────────────────────┴─────────────────────────────┐
        │  P2 (POLISH & DX) - 3 ITEMS                            │
        │  • Standardize Scanner & AutoTrader File Loggers       │
        │  • Add pythonpath = . to pytest.ini                    │
        │  • Permanent Failure QA Test Suite Expansion           │
        └────────────────────────────────────────────────────────┘
```

---

## 2. Priority P0: Critical Operational & Dispatch Resilience

### Item P0-1: Telegram Unrecoverable Error Fast-Abort & Subscriber Auto-Pause
- **File:** [`core/signals/publishing.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/signals/publishing.py)
- **Target Lines:** Lines 587–632
- **Issue:**
  1. Unrecoverable Telegram errors (403 Forbidden: bot blocked, user deactivated; 400 Bad Request: chat not found) undergo the full exponential retry backoff (`max_retries` attempts with `backoff_ms` sleep), blocking the publisher loop sequentially for all other subscribers.
  2. Auto-pausing subscribers only checks `if "chat not found" in str(delivery.last_error).lower():`. Blocked subscribers are never paused, causing perpetual multi-second delays on every signal run.
- **Proposed Implementation:**
  ```python
  # Define unrecoverable error signatures
  UNRECOVERABLE_TELEGRAM_PATTERNS = {
      "chat not found",
      "bot was blocked by the user",
      "user is deactivated",
      "bot can't initiate conversation",
      "chat was deleted",
      "group chat was deactivated",
  }

  def _is_unrecoverable_telegram_error(resp: Optional[dict]) -> bool:
      if not resp or not isinstance(resp, dict):
          return False
      if resp.get("ok"):
          return False
      error_code = resp.get("error_code")
      desc = str(resp.get("description", "")).lower()
      if error_code in (400, 403):
          return any(pat in desc for pat in UNRECOVERABLE_TELEGRAM_PATTERNS)
      return False
  ```
  In the retry loop:
  ```python
  for attempt in range(req.max_retries + 1):
      delivery.attempts += 1
      tg_resp = _send_delivery_message(...)
      if tg_resp and tg_resp.get("ok"):
          break
      if _is_unrecoverable_telegram_error(tg_resp):
          logger.warning(f"[Publisher] Permanent Telegram error encountered: {tg_resp.get('description')}. Aborting retries.")
          break  # Do NOT sleep, do NOT retry
      if attempt < req.max_retries and req.backoff_ms > 0:
          sleep_fn((req.backoff_ms / 1000.0) * (2 ** attempt))
  ```
  In client failure handling:
  ```python
  error_desc = str(delivery.last_error).lower()
  is_permanent = any(pat in error_desc for pat in UNRECOVERABLE_TELEGRAM_PATTERNS)
  if is_permanent:
      client.delivery_fail_count += 1
      if client.delivery_fail_count >= 3:
          client.delivery_paused = True
          logger.warning(
              f"[Publisher] Client {client.name} (ID: {client.id}) delivery automatically paused "
              f"due to {client.delivery_fail_count} consecutive delivery failures: {delivery.last_error}"
          )
      client.save()
  ```

---

### Item P0-2: Market Watchdog Scheduler Coalescing & Off-Hours Pause
- **Files:** [`config/startup.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/startup.py), [`config/scheduler_setup.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/scheduler_setup.py)
- **Target Lines:** `config/startup.py:105`, `config/scheduler_setup.py:50`
- **Issue:**
  1. `market_watchdog` interval job lacks `coalesce=True`, `max_instances=1`, risking overlapping ticks during heavy parquet sync.
  2. `market_watchdog` is omitted from `market_jobs` in `config/scheduler_setup.py:50`, meaning it ticks 24/7 during nights and weekends.
- **Proposed Implementation:**
  In [`config/startup.py:105`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/startup.py#L105):
  ```python
  scheduler.add_job(
      callback,
      'interval',
      minutes=5,
      id='market_watchdog',
      coalesce=True,
      max_instances=1,
      misfire_grace_time=60,
  )
  ```
  In [`config/scheduler_setup.py:50`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/scheduler_setup.py#L50):
  ```python
  market_jobs = ['intraday_scan', 'trade_monitor', 'signal_delivery_retry', 'market_watchdog']
  ```

---

## 3. Priority P1: Architecture, Time Semantics & Integration

### Item P1-1: Resolve `ConfluenceEngine` Class & Module Collision
- **Files:** [`core/ConfluenceEngine.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/ConfluenceEngine.py) -> [`core/sovereign_confluence.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/sovereign_confluence.py)
- **Issue:** Two distinct files (`core/confluence.py` vs `core/ConfluenceEngine.py`) define `class ConfluenceEngine`, causing casing risks on Linux and cognitive confusion.
- **Proposed Implementation:**
  1. Create `core/sovereign_confluence.py` with `class SovereignConfluenceEngine` and `sovereign_confluence_engine = SovereignConfluenceEngine()`.
  2. In `core/ConfluenceEngine.py`, provide a deprecation-wrapped shim:
     ```python
     from core.sovereign_confluence import SovereignConfluenceEngine as ConfluenceEngine, sovereign_confluence_engine as confluence_engine
     import warnings
     warnings.warn("core.ConfluenceEngine is deprecated. Use core.sovereign_confluence instead.", DeprecationWarning, stacklevel=2)
     ```
  3. Update references in `core/AutoTrader.py`, `core/ai_report/snapshot.py`, and `core/signals/system_monitor.py`.

---

### Item P1-2: Fix Direct Wall-Clock Leaks to Restore Deterministic Simulation Time
- **Files:** [`core/confluence.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/confluence.py), [`core/AutoTrader.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/AutoTrader.py), [`core/analyzers/SlippageReconciler.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/analyzers/SlippageReconciler.py), [`core/AuditEngine.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/AuditEngine.py), [`core/signals/publishing.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/signals/publishing.py)
- **Target Changes:**
  - `core/confluence.py:71`: `current_month = TimeUtils.now().month`
  - `core/AutoTrader.py:533`: `if (TimeUtils.now() - entry_dt).total_seconds() < 10:`
  - `core/analyzers/SlippageReconciler.py:20`: `cutoff_date = TimeUtils.now() - datetime.timedelta(days=lookback_days)`
  - `core/AuditEngine.py:28, 41`: Use `TimeUtils.now()`
  - `core/signals/publishing.py:264`: Use `TimeUtils.now() - datetime.timedelta(days=1)`

---

### Item P1-3: Add HTTP Timeouts to `utils/ollama_manager.py`
- **File:** [`utils/ollama_manager.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/utils/ollama_manager.py)
- **Target Lines:** 146, 161
- **Target Changes:**
  ```python
  # Line 146
  response = requests.get(f"{self.base_url}/api/tags", timeout=5.0)

  # Line 161
  requests.post(f"{self.base_url}/api/pull", json={"name": model_name}, timeout=(5.0, 300.0))
  ```

---

### Item P1-4: Subscriber Delivery Blocked Diagnosis Decoupling
- **File:** [`core/subscriptions/delivery.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/subscriptions/delivery.py)
- **Target Lines:** 397–410
- **Target Changes:**
  Add a diagnosis branch for private subscriber bot blocks:
  ```python
  if "bot was blocked" in error or "user is deactivated" in error:
      return {
          "action_code": "SUBSCRIBER_BLOCKED_BOT",
          "severity": "BLOCKED",
          "operator_action": "Subscriber has blocked the bot or deleted their Telegram account. Contact via phone or pause delivery.",
          "technical_reason": "Telegram 403 Forbidden: bot was blocked by user or user deactivated.",
      }
  ```

---

## 4. Priority P2: Quality of Life, Logging & DX

### Item P2-1: Standardize Scanner & AutoTrader File Loggers
- **Files:** [`core/DailyScanner.py:48-53`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/DailyScanner.py#L48-L53), [`core/AutoTrader.py:31-36`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/AutoTrader.py#L31-L36)
- **Target Changes:**
  Replace local `RotatingFileHandler('scanner.log')` and `RotatingFileHandler('autotrader.log')` with `setup_logger("horus.scanner")` and `setup_logger("horus.autotrader")` from `utils.logger`.

### Item P2-2: Add `pythonpath = .` in `pytest.ini`
- **File:** [`pytest.ini`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/pytest.ini)
- **Target Changes:**
  Add `pythonpath = .` to allow frictionless `pytest` execution directly from terminal.

### Item P2-3: Permanent Failure QA Test Suite Expansion
- **File:** [`tests/test_signal_delivery_failures.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/tests/test_signal_delivery_failures.py) (NEW)
- **Target Changes:**
  Add comprehensive tests for:
  - Immediate abort on 403 Forbidden without exponential backoff sleeps.
  - Verification that 3 consecutive 403 or 400 errors set `client.delivery_paused = True`.
  - Diagnosis check in `/api/v1/subscribers/...` returning `SUBSCRIBER_BLOCKED_BOT`.

---

SOURCES (LAYER 2 NAVIGATION)
docs/audit/phase2-gap-analysis/00-index.md
 -> Root index and navigation hub
docs/audit/phase2-gap-analysis/01-summary/executive-summary.md
 -> High-level synthesis of gap analysis findings
docs/audit/phase2-gap-analysis/02-analysis/code-review.md
 -> Code review, naming collisions, and time semantics analysis
docs/audit/phase2-gap-analysis/02-analysis/reliability-failure-modes.md
 -> SRE review of runtime failure modes and Telegram retry loops
docs/audit/phase2-gap-analysis/02-analysis/qa-coverage-matrix.md
 -> QA test coverage matrix and untested failure branches
