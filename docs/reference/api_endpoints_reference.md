# Horus Analytics v1.0 — API Endpoints & WebSocket Reference

> **Document Type:** Diátaxis Reference (Information-Oriented)  
> **Audience:** Frontend Engineers, Integration Developers, Quantitative Desk Operators  
> **Base URL:** `http://127.0.0.1:8000`  
> **API Version:** `1.0.0` (`API_VERSION = "1.0.0"`)  
> **Interactive Docs (Swagger UI):** `http://127.0.0.1:8000/docs`  

---

## 1. Authentication & Headers

Horus uses API key authentication for protected operational and mutation routes.

| Header | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `X-API-Key` | `string` | On protected endpoints | API authentication key configured in `.env` (`API_KEY`). On strictly local loopback (`127.0.0.1`), development mode bypasses this requirement if configured. |
| `Content-Type` | `string` | On `POST`/`PUT` requests | Must be `application/json`. |

---

## 2. System & Telemetry Endpoints (`/api/v1/system`)

### 2.1 Boot Status
- **Method:** `GET`
- **Path:** `/api/v1/system/boot-status`
- **Auth:** Public
- **Description:** Lightweight health endpoint polled by frontend startup screens and CLI diagnostic tools.
- **Response `200 OK`:**
  ```json
  {
    "app_name": "Horus Analytics",
    "app_version": "1.0.0",
    "system_ready": true,
    "message": "System Operational",
    "pipeline_state": "READY",
    "provisioning_status": "COMPLETED",
    "provisioning_target_trading_days": 252,
    "provisioning_completed_trading_days": 252,
    "db_connected": true,
    "scheduler": { "running": true },
    "live_execution": {
      "guard_enabled": true,
      "armed": false,
      "auto_trade_enabled": false
    },
    "timestamp": "2026-09-22T14:15:00.123456+02:00"
  }
  ```

### 2.2 Live Execution Guard Status
- **Method:** `GET`
- **Path:** `/api/v1/system/live-execution`
- **Auth:** Protected
- **Description:** Returns the current arming status, lockout conditions, and plan confirmation state.

### 2.3 Set Live Execution Guard (Arm / Disarm)
- **Method:** `POST`
- **Path:** `/api/v1/system/live-execution`
- **Auth:** Protected
- **Request Body:**
  ```json
  {
    "armed": true
  }
  ```
- **Response `200 OK`:** Returns updated `live_execution` status.
- **Errors:**
  - `409 Conflict`: `AUTO_TRADE_ENABLED must be true before arming live execution.`
  - `409 Conflict`: `Daily trading plan confirmation is required before arming live execution.`
  - `409 Conflict`: `Operator lockout is active (daily-loss, consecutive-loss, or manual-override limits).`

### 2.4 Confirm Operator Trading Plan
- **Method:** `POST`
- **Path:** `/api/v1/system/operator/trading-plan/confirm`
- **Auth:** Protected
- **Request Body:**
  ```json
  {
    "checklist_confirmed": true,
    "session": "CONTINUOUS",
    "max_trades": 5,
    "max_risk_per_trade_pct": 1.0,
    "max_daily_loss_pct": 3.0,
    "notes": "Morning checklist verified. Tracking EGX30 breakouts."
  }
  ```

### 2.5 Log Operator Deviation
- **Method:** `POST`
- **Path:** `/api/v1/system/operator/deviation`
- **Auth:** Protected
- **Request Body:**
  ```json
  {
    "category": "manual_override",
    "ticker": "COMI.CA",
    "severity": "WARNING",
    "message": "Manual exit taken early.",
    "reason_note": "News release prior to auction."
  }
  ```
- **Allowed Categories:** `valid_signal_skipped`, `invalid_manual_trade`, `manual_trade_taken`, `exit_rule_violation`, `stop_modification`, `manual_override`.

### 2.6 Deviation Journal
- **Method:** `GET`
- **Path:** `/api/v1/system/operator/deviation-journal`
- **Auth:** Protected
- **Query Params:** `date_from` (ISO), `date_to` (ISO), `category` (string), `limit` (int, default 200).

---

## 3. Live Market & Feed Endpoints (`/api/v1/live`)

### 3.1 Live Market Status & Session Phase
- **Method:** `GET`
- **Path:** `/api/v1/live/status`
- **Auth:** Public
- **Description:** Exposes real-time EGX session phase, timeline, and bar freshness.
- **Response `200 OK`:**
  ```json
  {
    "market_open": true,
    "session_phase": "CONTINUOUS_TRADING",
    "latest_bar_time": "2026-09-22 14:14:00",
    "session_timeline": {
      "continuous_end": "14:15",
      "closing_auction_end": "14:25",
      "market_close": "14:30",
      "is_ramadan": false
    },
    "parallel_usd_rate": 48.75,
    "active_tickers_count": 185
  }
  ```

---

## 4. Technical Scanner & Strategy Endpoints (`/api/v1/scanner`, `/api/v1/strategy`)

### 4.1 Trigger Technical Scan
- **Method:** `POST`
- **Path:** `/api/v1/scanner/scan`
- **Auth:** Protected
- **Query Params:** `timeframe` (`"1m"`, `"5m"`, `"15m"`, `"1d"`), `universe` (`"EGX30"`, `"EGX70"`, `"ALL"`).

### 4.2 Pre-Close 14:10 Daily Preview
- **Method:** `GET`
- **Path:** `/api/v1/scanner/pre-close-preview`
- **Auth:** Protected
- **Description:** Returns projected daily candle breakouts generated at 14:10 before continuous trading ends.

### 4.3 Price Action Strategy Catalog
- **Method:** `GET`
- **Path:** `/api/v1/strategy/price-action/catalog`
- **Auth:** Protected
- **Description:** Lists all available price-action and candlestick pattern strategy definitions.

### 4.4 Run Strategy Backtest
- **Method:** `POST`
- **Path:** `/api/v1/strategy/price-action/backtest`
- **Auth:** Protected
- **Request Body:**
  ```json
  {
    "strategy_id": "breakout_vsa_v1",
    "ticker": "COMI.CA",
    "date_from": "2025-01-01",
    "date_to": "2026-09-01",
    "capital": 100000.0,
    "commission_pct": 0.0015,
    "slippage_pct": 0.0010
  }
  ```

---

## 5. Portfolio & Ledger Endpoints (`/api/v1/portfolio`)

### 5.1 Portfolio Summary
- **Method:** `GET`
- **Path:** `/api/v1/portfolio/summary`
- **Auth:** Protected
- **Description:** Current equity, cash, margin, open positions, realized PnL, and current portfolio heat.

### 5.2 Open Positions
- **Method:** `GET`
- **Path:** `/api/v1/portfolio/positions`
- **Auth:** Protected
- **Description:** Active positions with entry price, current price, unrealized PnL, stop-loss, and take-profit targets.

---

## 6. Local AI Intelligence Endpoints (`/api/v1/ai-report`)

### 6.1 Generate Narrative Market Report
- **Method:** `POST`
- **Path:** `/api/v1/ai-report/generate`
- **Auth:** Protected
- **Description:** Triggers the local Ollama (Gemma 4 31B) engine to synthesize pre-market, mid-day, or post-close executive intelligence reports.

### 6.2 Fetch Latest Report
- **Method:** `GET`
- **Path:** `/api/v1/ai-report/latest`
- **Auth:** Protected

---

## 7. WebSocket Live Streaming (`/ws/live`)

- **Protocol:** WebSocket (`ws://127.0.0.1:8000/ws/live`)
- **Connection Lifecycle:**
  1. Client initiates connection.
  2. Server sends initial connection handshake with `session_phase` and system readiness.
  3. Real-time messages are pushed to connected clients:
     - `TICK_UPDATE`: Price, volume, and turnover update for tracked tickers.
     - `BAR_CLOSED`: Formed candlestick bar (1m / 5m).
     - `SIGNAL_ALERT`: Breakout or pre-close signal trigger.
     - `SESSION_TRANSITION`: Session phase shift (e.g. Continuous $\to$ Closing Auction).
     - `WATCHDOG_HEARTBEAT`: Periodic stream health verification.
