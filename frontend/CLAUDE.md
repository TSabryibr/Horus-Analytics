# Horus Analytics Frontend — Developer & Agent Guide

> **Modern Next.js 16 Trading Dashboard & Cockpit for Horus Analytics v1.0**

---

## 🛠️ Stack & Conventions

- **Framework:** Next.js 16.1.7 (App Router), React 19.2.3, TypeScript 5.
- **Port & Host:** Default dev server runs on `http://127.0.0.1:3100`.
- **Backend API:** Connects to FastAPI backend at `http://127.0.0.1:8000` via environment variable `NEXT_PUBLIC_API_URL`.
- **WebSocket:** Connects to `ws://127.0.0.1:8000/ws/live` for real-time market updates.
- **Styling:** Modular CSS / Tailwind with dark-mode institutional trading desk aesthetic.
- **Charting Engine:** TradingView `lightweight-charts` (v5.1.0) with custom candlestick indicators, trade geometry markers, and volume profiles.

---

## 📂 Project Architecture

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx            # Master shell, Asgardian dark theme, Navigation
│   ├── page.tsx              # Live Trading Terminal & EGX30 benchmark
│   ├── scanner/              # Technical Breakout & VSA Scanner Desk
│   ├── strategy/             # Strategy Lab & Price Action Backtester
│   ├── portfolio/            # Portfolio Risk Desk, Ledger, Position Forms
│   ├── ai-report/            # Local Ollama AI Narrative Reports
│   └── settings/             # System Controls, Live Arm Guard, Holidays
│
├── components/               # Reusable React components
│   ├── charts/               # TradingView Lightweight-Charts wrappers
│   ├── navigation/           # Top bar session timeline badge & side menu
│   ├── signals/              # Signal cards, trade geometry cards
│   └── common/               # Modals, badges, indicators, data tables
│
└── public/                   # Static assets, fonts, icons
```

---

## ⚡ Key Frontend Invariants

1. **EGX Session Status Awareness:**
   - The top navigation bar must dynamically display the active `session_phase` (`PRE_MARKET`, `CONTINUOUS_TRADING`, `CLOSING_AUCTION`, `TRADE_AT_CLOSE`, `CLOSED`).
   - If `CLOSING_AUCTION` (14:15–14:25) is active, do not display a "stalled" warning; indicate that the continuous market is closed and price discovery is in progress.
2. **Safety First (Live Execution Guard):**
   - The UI must prominently indicate the live execution state (`ARMED (LIVE)` vs. `DISARMED (SAFE MODE)`).
   - Live order buttons must remain disabled unless the user has confirmed the daily trading plan and armed the system.
3. **No Hardcoded Dates/Times:**
   - Format all timestamps using `Africa/Cairo` locale formatting.

---

## 🧪 Testing Commands

```bash
# Run unit test suite:
npm test

# Run tests in watch mode:
npm run test:watch

# Run Playwright E2E tests:
npm run test:e2e

# Run TypeScript typecheck:
npm run typecheck
```
