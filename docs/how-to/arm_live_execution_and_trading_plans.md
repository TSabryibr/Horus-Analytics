# How to Arm Live Execution and Confirm Daily Trading Plans

> **Document Type:** Diátaxis How-To Guide (Problem-Oriented)  
> **Audience:** Trading Desk Operators, Risk Officers, System Administrators  
> **System Version:** Horus Analytics v1.0.0  
> **Target Subsystem:** Execution Governance & Risk Enforcement Gates  

---

## The Problem

In automated and algorithmic trading systems, accidentally executing live market orders without pre-session verification, or letting a bot trade through an account drawdown, can cause catastrophic losses.

Horus Analytics v1.0 enforces a **two-key safety architecture**:
1. **Trading Plan Confirmation:** The operator must formally acknowledge and confirm risk limits for the session.
2. **Daily-Expiring Live Arm Guard:** Live execution is disabled by default and requires explicit daily arming. If armed today, it automatically disarms at midnight.
3. **Automated Circuit Breakers:** Live trading automatically locks out if daily loss limits (3.0%) or consecutive loss thresholds (4 losses) are breached.

This guide provides a step-by-step recipe to safely prepare, confirm, arm, monitor, and emergency-disarm live execution on Horus Analytics.

---

## Prerequisites

- Backend API running on `http://127.0.0.1:8000`.
- Valid API Key (if network authentication is configured; default header `X-API-Key`).
- Environment variable `AUTO_TRADE_ENABLED=true` set in `.env` (or enabled in `settings.json`).

---

## Step 1: Verify Pre-Market System Health

Before confirming any plan or arming execution, check that data feeds and the database are ready.

### Check Boot Status:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/system/boot-status" | Select-Object system_ready, message, db_connected, pipeline_state | ConvertTo-Json
```

### Expected Output:
```json
{
  "system_ready": true,
  "message": "System Operational",
  "db_connected": true,
  "pipeline_state": "READY"
}
```

> [!CAUTION]
> If `system_ready` is `false` or `db_connected` is `false`, **do not arm execution**. Resolve data feed or database issues first.

---

## Step 2: Confirm the Daily Trading Plan

Execution cannot be armed without a confirmed trading plan for the current calendar date (`Africa/Cairo`).

### Submit Plan Confirmation via API:
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    checklist_confirmed = $true
    session = "CONTINUOUS"
    max_trades = 5
    max_risk_per_trade_pct = 1.0
    max_daily_loss_pct = 3.0
    notes = "Morning pre-market plan verified. Focusing on EGX30 momentum breakouts."
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/system/operator/trading-plan/confirm" -Headers $headers -Body $body
```

### Verify Plan Status:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/system/operator/trading-plan/status"
```
Ensure `trading_plan.confirmed` returns `true` for today's date.

---

## Step 3: Arm the Live Execution Guard

Once the daily plan is confirmed, you can arm the execution engine for the current session.

### Arm Live Execution via API:
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{ armed = $true } | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/system/live-execution" -Headers $headers -Body $body
```

### Response on Success:
```json
{
  "status": "success",
  "live_execution": {
    "guard_enabled": true,
    "auto_trade_enabled": true,
    "armed": true,
    "armed_on": "2026-09-22",
    "today": "2026-09-22",
    "expires_daily": true,
    "lockout": {
      "lockout_active": false
    }
  }
}
```

### Guard Conditions Enforced by the Backend:
If you attempt to arm without satisfying prerequisites, the server returns `HTTP 409 Conflict`:
- `AUTO_TRADE_ENABLED must be true before arming live execution.`
- `Daily trading plan confirmation is required before arming live execution.`
- `Operator lockout is active (daily-loss, consecutive-loss, or manual-override limits).`

---

## Step 4: Monitor Circuit Breakers During the Session

During active trading (10:00 – 14:15), Horus continuously monitors realized equity drawdowns across all trading portfolios (`Intraday Signals`, `Swing Signals`, `Position Signals`).

### Circuit Breaker Rules:
1. **Daily Loss Ceiling (`LIVE_MAX_DAILY_LOSS_PCT` = 3.0%):**
   If the portfolio loses $\ge 3.0\%$ of starting capital on the day, `lockout_active` becomes `true`. All subsequent live entries are rejected.
2. **Consecutive Losses (`LIVE_MAX_CONSECUTIVE_LOSSES` = 4):**
   If 4 consecutive trades hit stop-loss, the system halts live entries until manual operator review.

### Inspect Lockout State:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/system/live-execution" | Select-Object -ExpandProperty live_execution | Select-Object -ExpandProperty lockout
```

---

## Step 5: Logging Operator Deviations & Manual Overrides

To maintain institutional compliance and avoid cognitive biases, any manual intervention must be recorded in the audit ledger.

### When to Log a Deviation:
- You skipped a valid high-conviction setup emitted by the scanner.
- You took a discretionary manual trade outside system rules.
- You modified a stop-loss or take-profit order manually.
- You manually exited early before the strategy target or stop was reached.

### How to Submit a Deviation Entry:
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    category = "manual_override"
    ticker = "COMI.CA"
    severity = "WARNING"
    message = "Early manual exit taken on COMI.CA."
    reason_note = "Macro news alert on central bank rate decision; de-risking prior to auction."
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/system/operator/deviation" -Headers $headers -Body $body
```

### Valid Categories:
`valid_signal_skipped`, `invalid_manual_trade`, `manual_trade_taken`, `exit_rule_violation`, `stop_modification`, `manual_override`.

### Inspecting Today's Journal:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/system/operator/deviation-journal"
```

---

## Step 6: Emergency Disarm Protocol

In the event of unexpected market volatility, data feed anomalies, or platform maintenance:

### Immediate Disarm via API:
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{ armed = $false } | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/system/live-execution" -Headers $headers -Body $body
```

### Verify Disarm State:
Ensure `"armed": false` is returned. When disarmed:
- Signal scanning and chart generation continue uninterrupted.
- No live broker or simulation orders will execute.
- Pending orders will not be promoted.

---

## Daily Operational Checklist Summary

```
[ ] 09:30 AM (Pre-Market)  : Check /api/v1/system/boot-status -> verify green
[ ] 09:45 AM (Pre-Market)  : Review candidate watchlist & confirm Daily Trading Plan
[ ] 09:55 AM (Pre-Market)  : Arm Live Execution Guard
[ ] 10:00 AM - 02:15 PM    : Monitor Intraday Scans & Circuit Breakers
[ ] 02:10 PM (Pre-Close)   : Review 14:10 Pre-Close Candle Preview
[ ] 02:30 PM (Post-Close)  : Confirm Live Guard disarms; review EOD Deviation Journal
```

---

## Related Documentation

- **EGX Session Phases Guide:** [docs/how-to/handling_market_session_phases.md](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/docs/how-to/handling_market_session_phases.md)
- **System Architecture Guide:** [docs/HORUS_V1_SYSTEM_GUIDE.md](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/docs/HORUS_V1_SYSTEM_GUIDE.md)
