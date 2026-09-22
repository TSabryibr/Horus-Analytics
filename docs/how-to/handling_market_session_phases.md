# How to Handle EGX Market Session Phases and Auction Transitions

> **Document Type:** Diátaxis How-To Guide (Problem-Oriented)  
> **Audience:** Trading Desk Operators, Quantitative Analysts, Platform Administrators  
> **System Version:** Horus Analytics v1.0.0  
> **Target System:** Egyptian Stock Exchange (EGX) Market Session Engine  

---

## The Problem

Unlike international exchanges that trade continuously until the closing bell, the **Egyptian Stock Exchange (EGX)** operates across distinct session phases:
1. Continuous matching stops at **14:15**.
2. A 10-minute **Closing Auction (14:15 – 14:25)** accumulates orders to calculate the official closing price (no individual trades are matched).
3. A 5-minute **Trade-at-Close session (14:25 – 14:30)** permits trades exclusively at that fixed price.

If a trading system or feed watchdog assumes continuous 1-minute bars through 14:30, it will interpret the absence of new bars at 14:22 as a **critical feed stall**. 

This guide shows you how to:
- Monitor and identify current EGX market session phases.
- Verify that continuous candlestick bars legitimately halt at 14:15:00.
- Confirm that the Market Feed Watchdog correctly suppresses false alarms during auction phases.
- Switch to and verify the Holy Month of Ramadan schedule.

---

## Prerequisites

- Backend API running on `http://127.0.0.1:8000`.
- Access to the Horus Command Shell or PowerShell terminal.
- Python 3.13 system environment.

---

## EGX Session Timeline Reference

| Session Phase | Standard Non-Ramadan (Cairo) | Ramadan Schedule (Cairo) | Order Matching Behavior | Bar Generation |
| :--- | :--- | :--- | :--- | :--- |
| **Pre-Opening** | `09:30 – 10:00` | `09:30 – 10:00` | Order entry allowed; no trades | No intraday bars |
| **Continuous Trading** | `10:00 – 14:15` | `10:00 – 13:15` | **Active continuous order matching** | **Active 1m / 5m bars** |
| **Closing Auction** | `14:15 – 14:25` | `13:15 – 13:25` | **Matching HALTED**; price discovery | **Bars HALT at 14:15:00** |
| **Trade-at-Close** | `14:25 – 14:30` | `13:25 – 13:30` | Execution at fixed closing price only | Fixed-price tick entries |
| **Market Closed** | `14:30+` | `13:30+` | Market closed | Ingest EOD reconciliation |

---

## Step 1: Check Current Session Phase via API

To inspect what phase Horus currently recognizes:

### Using PowerShell:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/live/status" | Select-Object session_phase, market_open, latest_bar_time, session_timeline | ConvertTo-Json -Depth 4
```

### Expected Response During Continuous Trading (e.g., 11:30 AM):
```json
{
  "session_phase": "CONTINUOUS_TRADING",
  "market_open": true,
  "latest_bar_time": "2026-09-22 11:29:00",
  "session_timeline": {
    "continuous_end": "14:15",
    "closing_auction_end": "14:25",
    "market_close": "14:30",
    "is_ramadan": false
  }
}
```

### Expected Response During Closing Auction (e.g., 14:22 PM):
```json
{
  "session_phase": "CLOSING_AUCTION",
  "market_open": true,
  "latest_bar_time": "2026-09-22 14:15:00",
  "session_timeline": {
    "continuous_end": "14:15",
    "closing_auction_end": "14:25",
    "market_close": "14:30",
    "is_ramadan": false
  }
}
```

> [!NOTE]
> Notice that during `CLOSING_AUCTION`, `latest_bar_time` will show `14:15:00`. This is the intended behavior and does **not** indicate a stalled data feed.

---

## Step 2: Verify Watchdog Behavior During Closing Auction

The `MarketFeedWatchdog` evaluates incoming ticks and bars against session phases:

1. **At 14:15:01**, continuous order matching halts on EGX.
2. The latest bar recorded in the database remains `14:15:00`.
3. When the watchdog runs its periodic health check at 14:20 or 14:22:
   - It queries `settings.get_market_session_phase()`.
   - Recognizing `CLOSING_AUCTION` (or `TRADE_AT_CLOSE`), it checks if `latest_bar_time >= 14:15:00`.
   - Because the data reached continuous close, it marks the feed as **healthy**:
     - `stalled: False`
     - `status: "CLOSING_AUCTION"`
     - `action: "none"`
   - **No Telegram critical alerts or restart routines will fire.**

### How to Verify Watchdog Health via Code / Terminal:
Run the automated watchdog SLA test to confirm current behavior:
```powershell
pytest tests/test_signal_sla_and_watchdog.py -k "test_watchdog_recognizes_closing_auction"
```

---

## Step 3: What to Do During the 14:10 Pre-Close Window

The 5 minutes immediately preceding the 14:15 continuous close (`14:10 – 14:15`) are critical for swing position entry:

1. **At 14:10**, Horus runs the automated **Pre-Close Daily Preview Scanner**:
   - Gathers candles up to `14:10`.
   - Forecasts end-of-day daily candle completion.
   - Generates high-conviction swing/position recommendations.
2. **Operator Action:**
   - Review pending pre-close signals on the Signal Desk dashboard (`http://127.0.0.1:3100`).
   - If taking the trade, place market/limit orders **before 14:15:00** or submit auction orders during `14:15 – 14:25` for execution at the official closing price.

---

## Step 4: Operating Under the Holy Month of Ramadan Schedule

During Ramadan, all session boundaries advance by 1 hour.

### 1. Enable Ramadan Mode in `.env`:
Open `.env` in the repository root and set:
```ini
EGX_RAMADAN_MODE=true
```
*(Or modify via `core/settings.py` `RAMADAN_MODE = True`)*

### 2. Verify Ramadan Boundaries:
Run:
```powershell
python -c "from core.settings import settings; print('Ramadan:', settings.is_ramadan()); print('Continuous End:', settings.get_continuous_trading_end_hour_minute()); print('Auction End:', settings.get_closing_auction_end_hour_minute()); print('Close:', settings.get_market_close_hour_minute())"
```

Expected Output:
```
Ramadan: True
Continuous End: (13, 15)
Auction End: (13, 25)
Close: (13, 30)
```

In Ramadan mode:
- Continuous scanning halts at **13:15**.
- Closing Auction runs from **13:15 to 13:25**.
- Trade-at-Close runs from **13:25 to 13:30**.
- Pre-close preview scanner automatically adjusts to fire at **13:10**.

---

## Step 5: Troubleshooting Genuine Mid-Session Feed Stalls

If a Telegram alert fires:
```
🚨 CRITICAL: MARKET FEED STALLED
Ticker: COMI.CA
Latest Bar: 11:32:00
Current Time: 11:47:00
```

### Diagnostic Checklist:
1. **Check Cairo Clock:** Is the current time between 10:00 and 14:15?
   - If **yes**, this is a **genuine stall** (feed stopped during active trading).
   - If **no** (e.g., time is 14:22), inspect whether the system clock or timezone is out of sync (`core.TimeUtils.now()`).
2. **Inspect Mubasher / MetaStock Ingestion Folder:**
   - Verify that Mubasher PRO or DirectFN is actively connected and writing new `.DAT` or SQLite records.
3. **Trigger Manual Self-Healing Ingestion:**
   ```powershell
   python -c "from data_engine.sync import sync_all; sync_all()"
   ```
4. **Check Feed Watchdog Cooldown:**
   - The watchdog enforces a 15-minute cooldown (`FEED_WATCHDOG_ALERT_COOLDOWN_MINUTES = 15`) between alert notifications to prevent chat flooding while recovery runs.

---

## Related Documentation

- **System Architecture Guide:** [docs/HORUS_V1_SYSTEM_GUIDE.md](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/docs/HORUS_V1_SYSTEM_GUIDE.md)
- **Live Arming Guide:** [docs/how-to/arm_live_execution_and_trading_plans.md](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/docs/how-to/arm_live_execution_and_trading_plans.md)
