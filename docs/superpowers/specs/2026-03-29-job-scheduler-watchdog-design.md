---
title: Scheduler Watchdog Implementation Design
date: 2026-03-29
author: Antigravity
status: Draft
---

# Scheduler Watchdog Implementation Design

## Context

The Horus Analytics backend uses `apscheduler` to run regular maintenance tasks:
- `scheduled_intraday_scan` (every 10 minutes)
- `scheduled_trade_monitor` (every 30 seconds)
- `scheduled_failed_delivery_retry` (every 10 minutes)

Currently, these jobs run continuously on simple interval triggers. When the market is closed, they execute but immediately exit because of internal checks against `GlobalSettings.is_market_open()`. 

While functionally safe, this fills the application logs with noise regarding skipped operations and unnecessarily spins up CPU resources to handle background tasks that are strictly tied to market activity.

## Objective

Eliminate execution overhead and log noise from market-dependent jobs during off-hours, weekends, and database-registered holidays without utilizing rigid `cron` times that cannot handle impromptu or seasonal (Ramadan) schedules.

## Approach: The Watchdog Pauser

We will introduce a lightweight "watcher" job that assumes responsibility for dynamically pausing and resuming all other market-dependent jobs within the APScheduler instance.

### System Architecture

1. **Job Categorization**:
   - Jobs are classified as either `market_dependent` or `always_on`.
   - `always_on` jobs include the Watchdog itself.
   - `market_dependent` jobs are paused when the market is closed and resumed when it opens.

2. **The Watchdog Task**:
   - Runs on a safe interval (e.g., every 5 minutes).
   - Examines `GlobalSettings.is_market_open()`.
   - Interacts directly with the APScheduler instance (`scheduler.pause_job(id)` / `scheduler.resume_job(id)`).

3. **State Tracking**:
   - The Watchdog must remember its current known state (`last_known_market_state`) so it does not repeatedly issue pause/resume commands or spam the logs every 5 minutes telling the user "Market is still closed".

### Implementation Details

#### 1. Setup inside `api.py`

In `api.py` (or wherever `scheduler` jobs are registered):

```python
from apscheduler.jobstores.base import JobLookupError
from core.settings import GlobalSettings
import logging

logger = logging.getLogger(__name__)

# The global tracker
_market_was_open_last_check = None

def scheduled_market_watchdog():
    global _market_was_open_last_check
    
    # We must access the scheduler instance globally or pass it in.
    # Assuming `scheduler` is accessible globally in api.py
    market_is_open = GlobalSettings.is_market_open()
    
    if market_is_open == _market_was_open_last_check:
        return # State hasn't changed. Do nothing.
        
    # State transitioned!
    _market_was_open_last_check = market_is_open
    
    market_jobs = ['intraday_scan', 'trade_monitor', 'delivery_retry'] # list of known job IDs
    
    for job_id in market_jobs:
        try:
            if market_is_open:
                scheduler.resume_job(job_id)
            else:
                scheduler.pause_job(job_id)
        except JobLookupError:
            pass

    if market_is_open:
        logger.info("[Watchdog] Market opened. Heavy background tasks resumed.")
    else:
        logger.info("[Watchdog] Market closed. Heavy background tasks paused.")
```

#### 2. Registration

Add the watchdog to the scheduler during app startup:

```python
scheduler.add_job(
    scheduled_market_watchdog, 
    'interval', 
    minutes=5, 
    id='market_watchdog'
)
```

### Trade-offs & Risks
- **Risk**: A job might be paused mid-execution if the state transition happens. APScheduler's `pause_job` only stops *future* runs, so active runs will finish gracefully.
- **Risk**: The watchdog interval. If it runs every 5 minutes, it could take up to 5 minutes after the market officially opens before the trade monitor or scanner resumes. Given standard architecture, waiting <5 minutes for the first scan is acceptable. The `trade_monitor` may miss the very first few seconds of market open, but since open signals usually require the first candle to print anyway, this delay is negligible.

## Success Criteria
- The console logs completely silence `APScheduler` operations related to `scheduled_intraday_scan` and `scheduled_trade_monitor` after the market closes.
- The logs clearly show `[Watchdog] Market closed. Heavy background tasks paused.` exactly once upon transition.
- The `market_watchdog` job itself is the only job silently looping during closed sessions without spamming.
