# Tutorial: Operator First Day — Running Your First EGX Session

> **Document Type:** Diátaxis Tutorial (Learning-Oriented)  
> **Audience:** New Quantitative Traders, Operations Desk Members, Junior Analysts  
> **Estimated Duration:** 25 minutes  
> **Prerequisites:** Windows 10/11 workstation with Python 3.13 and Node.js installed  

---

## What You Will Learn

Welcome to **Horus Analytics v1.0**. In this tutorial, you will take your first hands-on steps through the platform as an operations desk trader:
1. Launch the full-stack system (FastAPI backend + Next.js web dashboard).
2. Explore the Asgardian Command Shell interface.
3. Verify live Egyptian Stock Exchange (EGX) market feed connectivity.
4. Complete your pre-market checklist and confirm today’s trading plan.
5. Safely arm the Live Execution Guard.
6. Experience a live market scan and review the 14:10 pre-close candle preview.
7. Understand what happens during the 14:15 closing auction.

---

## Step 1: Launch the Application

Horus Analytics includes a unified master batch launcher that orchestrates all background workers and web servers.

1. Open your Windows terminal or double-click:
   ```cmd
   Horus_Start.bat
   ```
2. You will be greeted by the Asgardian launcher menu:
   ```
   ======================================================================
         THE INFINITY SCEPTER | HORUS ANALYTICS v1.0 | ASGARDIAN EDITION
   ======================================================================
     "I drink from the well of Mimir, and I drink from the fire of Muspelheim."
   ======================================================================

     [1] AWAKEN THE GOD MODE (Launch Chitauri Scepter CLI)
     [2] ENGAGE THE FULL STACK (API Backend + Next.js Frontend)
     [3] BRIDGE THE WORLDS (Sync MetaStock to Parquet Lake)
     [4] HEIMDALL'S SIGHT (Portfolio Guardian Diagnostics)
     [5] SOUND THE GJALLARHORN (Live Sentinel Monitor)
     [6] RUN THE LEGACY SYNC (Direct CSV/Intraday Ingest)
     [7] ACTIVATE THE TEMPORAL ENGINE (Adaptive Sync Worker)

     [Q] Exit
   ```
3. Type `2` and press **Enter** to select `ENGAGE THE FULL STACK`.
4. When prompted for Session Mode:
   - Press **Enter** (default: `[1] Live Market Session`).
5. Two background command windows will spawn:
   - **Horus API:** FastAPI server running on `http://127.0.0.1:8000`.
   - **Horus UI:** Next.js development server running on `http://127.0.0.1:3100`.

---

## Step 2: Open the Web Dashboard

1. Launch Google Chrome or Microsoft Edge.
2. Navigate to:
   ```
   http://127.0.0.1:3100
   ```
3. You should see the **Horus Asgardian Command Cockpit**:
   - **Top Navigation Bar:** Live EGX session status badge (`CONTINUOUS_TRADING` or `PRE_MARKET`), current Cairo time, and feed heartbeat indicator.
   - **Main Workstation:** TradingView Lightweight-Charts displaying the benchmark index (`EGX30`).
   - **Left Sidebar:** Navigation links to **Scanner**, **Strategy Lab**, **Portfolio Desk**, **Whale Tracking**, and **Settings**.

---

## Step 3: Verify Market Feed Connectivity

Before trading, verify that real-time data is flowing properly.

1. Look at the top status bar:
   - Ensure the feed indicator displays a **Green Pulse** labeled `FEED: HEALTHY`.
   - Confirm the `LATEST BAR` matches recent market minutes (if during market hours).
2. Open a separate terminal tab and test the system health endpoint:
   ```powershell
   curl http://127.0.0.1:8000/api/v1/system/boot-status
   ```
3. Confirm that `"system_ready": true` and `"db_connected": true` are returned.

---

## Step 4: Complete Pre-Market Verification & Confirm the Plan

In Horus v1.0, you cannot place live trades without formally confirming the daily risk budget.

1. In the web dashboard, click on **Portfolio Desk** or navigate to **Settings $\to$ Risk Controls**.
2. Notice that **Live Execution** is marked as `DISARMED (SAFE MODE)`.
3. Open the **Operator Trading Plan Modal**:
   - Review recommended daily limits:
     - Max Daily Trades: `5`
     - Max Risk Per Trade: `1.0%`
     - Max Daily Loss: `3.0%`
4. Click **Confirm Daily Trading Plan**.
5. The system emits an audit event recording your confirmation in the SQLite database.

---

## Step 5: Arm the Live Execution Guard

Now that your plan is confirmed, you can arm the execution engine for today's session:

1. On the dashboard header, locate the **Live Arm Guard** toggle.
2. Click **Arm Live Execution**.
3. A confirmation prompt will ask you to verify that market conditions are acceptable.
4. Click **Confirm Arming**.
5. The badge will shift to **`ARMED (LIVE)`**.

> [!NOTE]
> Horus guards are **daily-expiring**. Live arming automatically resets to safe mode at midnight Cairo time. You will repeat this confirmation every morning.

---

## Step 6: Monitor the Intraday Scanner & Pre-Close Preview

During continuous trading (`10:00 – 14:15`):
1. Navigate to the **Scanner** page.
2. The scanner runs periodically, filtering EGX equities through the Breakout + VSA algorithm.
3. When a candidate qualifies:
   - A signal card appears showing the ticker, entry price, stop-loss ($1.5 \times \text{ATR}$), and target ($3.0 \times \text{ATR}$).
   - The chart plots the trade geometry with entry lines and risk-reward zones.
4. **At 14:10 PM:**
   - Watch for the **14:10 Pre-Close Preview** notification.
   - This special scan alerts you to high-conviction swing setups forming on the daily candle 5 minutes before continuous matching closes.

---

## Step 7: Experience the 14:15 Closing Auction Transition

At **14:15:00**, the EGX market changes state:
1. The top status bar automatically updates from `CONTINUOUS_TRADING` to `CLOSING_AUCTION`.
2. Continuous candlestick bar formation ceases; the latest bar will remain fixed at `14:15:00`.
3. **Important:** The Market Feed Watchdog recognizes the auction phase and will **not** raise false stall alarms.
4. Orders submitted during `14:15 – 14:25` enter the auction book to establish the official closing price.
5. At **14:25**, the market enters the 5-minute **Trade-at-Close** window.
6. At **14:30**, the market closes. Horus automatically initiates end-of-day reconciliation and triggers the local Ollama AI report generator.

---

## Congratulations!

You have completed your first operational walkthrough of **Horus Analytics v1.0**. You now understand how to:
- Launch and monitor the full stack.
- Confirm risk budgets and operate the Live Arm Guard.
- Interpret intraday signals and pre-close previews.
- Navigate the EGX closing auction without feed confusion.

### Next Steps:
- Read [docs/how-to/handling_market_session_phases.md](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/docs/how-to/handling_market_session_phases.md) for deep-dive session mechanics.
- Consult [docs/HORUS_TRADING_SYSTEM_ANALYSIS_AND_SETTINGS.md](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/docs/HORUS_TRADING_SYSTEM_ANALYSIS_AND_SETTINGS.md) to customize risk thresholds.
