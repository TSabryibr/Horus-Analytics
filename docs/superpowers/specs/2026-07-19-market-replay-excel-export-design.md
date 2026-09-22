# Market Replay & Backfill Excel Export System — Technical Design Document

**Date:** 2026-07-19  
**Status:** Approved  
**Scope:** Horus Analytics II — Market Replay & Simulation Engine Excel Export  

---

## 1. Goal & Overview

Provide an on-demand, professionally formatted Excel (`.xlsx`) export for Market Replay and Backfill session results. The Excel file features a 4-sheet multi-tab architecture built using `openpyxl`, with dark header styling, clear visual color coding for P&L / trade outcomes, formatted currency/percentage cells, auto-adjusted column widths, and complete metric breakdowns.

---

## 2. System Architecture & Component Breakdown

```
[ Frontend: ReplayPanel.tsx / useReplay.ts ]
                 │
                 │  GET /api/v1/replay/export/excel
                 ▼
[ FastApi Route: routes/replay.py ]
                 │
                 │  Fetch active/completed _REPLAY_STATE
                 ▼
[ Excel Engine: core/excel_generator.py ]
                 │
                 │  Build OpenPyXL Workbook (4 Sheets)
                 ▼
[ StreamingResponse: Horus_Replay_YYYYMMDD_HHMMSS.xlsx ]
```

---

## 3. Detailed Specifications

### 3.1 Core Excel Generator (`core/excel_generator.py`)
Module function: `build_replay_excel_report(replay_state: dict) -> bytes`

- **Visual Styling Standards:**
  - Header Row: Dark Slate background (`#1E293B`), Bold white text (`#FFFFFF`), centered alignment, thin bottom border.
  - Alternating Rows: Zebra striping (`#FFFFFF` and `#F8FAFC`).
  - Font: Aptos / Arial / Segoe UI (10pt body, 11pt headers bold).
  - P&L / Trade Outcome Fills:
    - Target 1 / Target 2 / Profit: Soft Green background (`#DCFCE7`), Dark Green text (`#15803D`).
    - Stop Loss / Loss: Soft Red background (`#FEE2E2`), Dark Red text (`#B91C1C`).
    - Open / Pending: Soft Blue background (`#E0F2FE`), Dark Blue text (`#0369A1`).
  - Column Auto-Fit: Calculate maximum string length per column + 4 padding spaces.

- **Sheet 1: Executive Summary**
  - Section 1: Session Parameters (Replay Date, Speed, Market, Profile Name, Mode, Start Time, Completed Time).
  - Section 2: Core Key Performance Indicators (Total Ticks, Unique Signals Found, Executed Trades, Win Rate %, Total Realized PnL in EGP).
  - Section 3: Daily Phase Reconciliation Summary (Pre-close previews recorded vs confirmed daily signals).

- **Sheet 2: Executed Trades**
  - Data columns:
    1. Ticker
    2. Side
    3. State (`OPEN`, `TP1_HIT`, `CLOSED`)
    4. Entry Time
    5. Entry Price (EGP)
    6. Position Shares
    7. Exit Time
    8. Exit Price (EGP)
    9. Exit Reason (`TARGET_1`, `TARGET_2`, `STOP_LOSS`, `BREAKEVEN_STOP`, `REPLAY_END_FLAT`)
    10. Gross P&L (EGP)
    11. Net P&L (%)

- **Sheet 3: Signals & Intake**
  - Data columns:
    1. Ticker
    2. Score (0–10)
    3. Signal Type (`BUY`, `STRONG_BUY`)
    4. Planned Entry (EGP)
    5. Stop Loss (EGP)
    6. Target Price 1 (EGP)
    7. Target Price 2 (EGP)
    8. RSI
    9. Volume Spike Ratio (Volume_x)
    10. Alpha Rationale
    11. Action / Status (`QUEUED`, `SKIPPED`, `EXECUTED`)

- **Sheet 4: Tick-by-Tick Log**
  - Data columns:
    1. Tick Index
    2. Simulated Time
    3. Scan Label (`INTRADAY`, `PRE-CLOSE`, `DAILY SIGNAL`)
    4. Market Regime
    5. Market Breadth Ratio
    6. Signals Found Count
    7. Pending Entries Remaining

---

### 3.2 Backend API Endpoint (`routes/replay.py`)

Add route:
```python
@public_router.get("/api/v1/replay/export/excel")
def api_export_replay_excel():
    """Generate and download a styled Excel report for the current or last completed replay session."""
```
- Returns `StreamingResponse(io.BytesIO(excel_bytes))`
- Content Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content Disposition Header: `attachment; filename=Horus_Replay_[DATE]_[TIMESTAMP].xlsx`
- Error Handling: If `_REPLAY_STATE` is idle or empty, returns `400 Bad Request` with `{"detail": "No replay session data available for export"}`.

---

### 3.3 Frontend Integration (`ReplayPanel.tsx` & `useReplay.ts`)

1. **Hook Updates (`useReplay.ts`):**
   - Add `downloadExcelReport: () => Promise<void>`
   - Triggers `window.open('/api/v1/replay/export/excel', '_blank')` or fetches blob and triggers browser file download.

2. **UI Button (`ReplayPanel.tsx`):**
   - Add button: `Download Excel Report` with `FileSpreadsheet` icon from `lucide-react`.
   - Placed in the action controls header next to `Launch Replay` / status summary.
   - Disabled when `replayStatus` is null or has 0 ticks completed.

---

## 4. Verification Plan

### 4.1 Automated Tests
- `tests/test_excel_generator.py`: Verify `build_replay_excel_report()` handles empty states, open positions, closed positions, formatting rules, and returns non-empty valid XLSX binary data.
- `tests/test_api_endpoints.py`: Verify `GET /api/v1/replay/export/excel` returns HTTP 200 with correct headers and filename.
- `frontend/src/app/simulation/components/ReplayPanel.test.tsx`: Verify `Download Excel Report` button renders and triggers download callback.

### 4.2 Manual Verification
- Launch backend & frontend.
- Run a 1-day market replay for `2026-07-19` at 50x speed.
- Click `Download Excel Report`.
- Open `.xlsx` in Microsoft Excel to verify formatting, color fills, tab structure, numbers, and formulas.
