# Site Reliability & Failure Modes Analysis
**Swarm Specialist:** `site-reliability-engineer` (SRE)  
**Target:** Horus Analytics II Production Runtime, Schedulers, and Telegram Dispatch Engine  
**Evaluation Scope:** Failure resilience, timeout safety, retry storms, broadcast loop blocking, and telemetry.

---

## 1. Executive Failure Modes Matrix

| Failure Mode ID | Subsystem | Severity | Failure Mechanism | Operational Impact & Blast Radius |
| :--- | :--- | :--- | :--- | :--- |
| **REL-001** | Signal Publishing | **Critical (P0)** | Unhandled permanent Telegram errors (403 Forbidden: bot blocked / user deactivated) trigger full exponential retry backoffs in broadcast loop and never auto-pause subscriber accounts. | Severe broadcast delay (multiple seconds per dead subscriber) for all paying subscribers; risks Telegram HTTP 429 rate limit. |
| **REL-002** | Market Watchdog | **High (P0)** | `market_watchdog` interval job missing `coalesce=True`, `max_instances=1`, and misfire grace; omitted from market hours pause list, running unnecessary 24/7 checks. | Potential overlapping job execution under high SQLite contention; background worker resource waste when market is closed. |
| **REL-003** | AI Intelligence | **High (P1)** | `utils/ollama_manager.py:146, 161` issues un-timeouted HTTP requests (`requests.get('/api/tags')`, `requests.post('/api/pull')`). | Infinite thread hang / worker exhaustion if local Ollama daemon deadlocks or network stalls. |
| **REL-004** | Notification Delivery | **Medium (P1)** | `core/subscriptions/delivery.py:397` ignores 403 Forbidden on private chats; operator diagnosis UI displays generic failure without remediation advice. | Admin cannot distinguish between transient network issues and subscriber action (bot blocked). |
| **REL-005** | Webhook Engine | **Medium (P1)** | `core/WebhookManager.py:31` uses synchronous `requests.post(timeout=10)` directly within caller thread context. | Risks stalling fast path execution if an external webhook URL becomes unresponsive. |

---

## 2. Deep Dive: Telegram Retry Storm & Subscriber Broadcast Hang (REL-001)

### The Mechanism
In [`core/signals/publishing.py:587-598`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/signals/publishing.py#L587-L598), the broadcast loop iterates through all active subscribers:

```python
for attempt in range(req.max_retries + 1):
    delivery.attempts += 1
    tg_resp = _send_delivery_message(
        send_message_fn,
        message,
        destination_chat_id=destination["destination_chat_id"],
    )
    if tg_resp and tg_resp.get("ok"):
        break
    if attempt < req.max_retries and req.backoff_ms > 0:
        sleep_fn((req.backoff_ms / 1000.0) * (2 ** attempt))
```

And in lines 615-631:
```python
else:
    delivery.status = "FAILED"
    delivery.last_error = (tg_resp or {}).get("description", "Unknown delivery error")
    summary["failed"] += 1
    increment_reason_count_fn(summary["failure_reasons"], delivery.last_error)
    if destination["destination_type"] == "SUBSCRIBER" and destination["destination_id"]:
        try:
            client = Client.get_or_none(Client.id == int(destination["destination_id"]))
            if client:
                if "chat not found" in str(delivery.last_error).lower():
                    client.delivery_fail_count += 1
                    if client.delivery_fail_count >= 3:
                        client.delivery_paused = True
                        logger.warning(...)
                    client.save()
        except Exception as exc:
            ...
```

### The Double Failure
1. **Permanent Error Retries:** When a user blocks the Telegram bot, Telegram immediately responds:
   ```json
   {"ok": false, "error_code": 403, "description": "Forbidden: bot was blocked by the user"}
   ```
   Or if the user deleted their account:
   ```json
   {"ok": false, "error_code": 403, "description": "Forbidden: user is deactivated"}
   ```
   These are permanent, non-retryable errors. Yet, `publishing.py` does not check for permanent status or error codes. With default `max_retries=2` and `backoff_ms=500`, it sleeps 500ms, then 1000ms, hammering the Telegram API three times for a dead user. If 10 clients have blocked the bot, the broadcast loop is delayed by over 15 seconds!
2. **Missing Invalidation:** Line 624 strictly filters `if "chat not found" in str(delivery.last_error).lower():`.
   Because `"Forbidden: bot was blocked by the user"` does NOT contain `"chat not found"`, `client.delivery_fail_count` is **never incremented**! The subscriber is never auto-paused (`delivery_paused=True`).
   On every single daily and intraday signal run, this delay repeats indefinitely.

### Required Architecture Fix
- Define a canonical set of unrecoverable Telegram error keywords:
  `{"chat not found", "bot was blocked by the user", "user is deactivated", "bot can't initiate conversation", "chat was deleted"}`.
- If an unrecoverable error is encountered in `_send_delivery_message`:
  1. Break out of the retry loop immediately without sleeping.
  2. Increment `client.delivery_fail_count += 1`.
  3. Auto-pause (`client.delivery_paused = True`) upon reaching threshold (3 failures).

---

## 3. Deep Dive: Market Watchdog Scheduler Hygiene (REL-002)

### The Mechanism
In [`config/startup.py:104-115`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/startup.py#L104-L115):
```python
def _register_market_watchdog_jobs(scheduler, callback, *, market_open_time):
    scheduler.add_job(callback, 'interval', minutes=5, id='market_watchdog')
    scheduler.add_job(
        callback,
        'cron',
        hour=market_open_time.hour,
        minute=market_open_time.minute,
        id='market_watchdog_open',
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )
```

And in [`config/scheduler_setup.py:50`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/scheduler_setup.py#L50):
```python
market_jobs = ['intraday_scan', 'trade_monitor', 'signal_delivery_retry']
for job_id in market_jobs:
    if market_is_open:
        scheduler.resume_job(job_id)
    else:
        scheduler.pause_job(job_id)
```

### Vulnerability & Operational Risk
1. The interval job `market_watchdog` was registered without `coalesce=True` and `max_instances=1`. If self-healing requires an incremental intraday parquet resync that takes longer than expected, overlapping watchdog instances can run concurrently against the SQLite and Parquet stores.
2. `market_watchdog` is not in `market_jobs`. Even at 3:00 AM on Sunday, APScheduler wakes up every 5 minutes to execute the watchdog callback. While line 39 guards with `if market_is_open:`, the scheduler should cleanly pause the interval job post-market alongside `intraday_scan` and `trade_monitor`.

### Required Fix
- Add `coalesce=True`, `max_instances=1`, and `misfire_grace_time=60` to `_register_market_watchdog_jobs()`.
- Include `market_watchdog` in `market_jobs` in `config/scheduler_setup.py` so it pauses when the market closes and resumes when the market opens.

---

## 4. Deep Dive: Ollama Manager HTTP Timeouts (REL-003)

### The Mechanism
In [`utils/ollama_manager.py:145-167`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/utils/ollama_manager.py#L145-L167):
```python
response = requests.get(f"{self.base_url}/api/tags")  # NO TIMEOUT
...
def pull_model():
    try:
        requests.post(f"{self.base_url}/api/pull", json={"name": model_name})  # NO TIMEOUT
```

### Risk & Blast Radius
While `is_service_running()` has `timeout=2`, `ensure_model_available()` issues bare `requests.get()` and `requests.post()` calls with no timeout. If the Ollama daemon enters a deadlock or TCP half-open socket state, calling threads will block indefinitely, exhausting connection pools.

### Required Fix
- Apply explicit timeouts: `timeout=5.0` for `requests.get('/api/tags')`, and `timeout=300.0` with connection timeout tuple `(5.0, 300.0)` for `requests.post('/api/pull')`.

---

## 5. Failure Diagnosis & Operator Remediation (REL-004)

### The Mechanism
In [`core/subscriptions/delivery.py:371-415`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/subscriptions/delivery.py#L371-L415), `delivery_failure_diagnosis` decodes Telegram error descriptions for display in the admin UI.
However:
```python
if "forbidden" in error and chat_id.startswith("-100"):
    return {
        "action_code": "BOT_NOT_ALLOWED_IN_CHANNEL",
        "severity": "BLOCKED", ...
    }
```
If a private subscriber (whose chat ID does not start with `-100`) blocks the bot, the error is `"Forbidden: bot was blocked by the user"`.
This condition is ignored! The function returns `None`, leaving the operator without diagnostic clarity.

### Required Fix
Add explicit diagnosis branch for private subscriber block:
```python
if "bot was blocked by the user" in error or "user is deactivated" in error:
    return {
        "action_code": "SUBSCRIBER_BLOCKED_BOT",
        "severity": "BLOCKED",
        "operator_action": "Subscriber has blocked the bot or deactivated account. Contact subscriber via secondary channel or pause subscription.",
        "technical_reason": "Telegram returned 403 Forbidden (blocked by user or user deactivated).",
    }
```

---

SOURCES (LAYER 2 NAVIGATION)
docs/audit/phase2-gap-analysis/00-index.md
 -> Root index and navigation hub
docs/audit/phase2-gap-analysis/01-summary/executive-summary.md
 -> High-level synthesis of gap analysis findings
docs/audit/phase2-gap-analysis/02-analysis/code-review.md
 -> Code review, naming collisions, and time semantics analysis
docs/audit/phase2-gap-analysis/02-analysis/qa-coverage-matrix.md
 -> QA test coverage matrix and untested failure branches
docs/audit/phase2-gap-analysis/03-dossiers/action-matrix.md
 -> Prioritized P0/P1/P2 actionable remediation tasks with code diffs
