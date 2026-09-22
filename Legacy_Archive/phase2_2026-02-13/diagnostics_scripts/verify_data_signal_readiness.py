from __future__ import annotations

import json
import traceback
import contextlib
import os

from core import DailyScanner
from core.DataManager import DataManager
from data_engine.local_feed_selector import resolve_timeframe_provider
from data_engine.sync import sync_all
from routes.data import get_data_status_logic


def main() -> None:
    report: dict = {"status": "ok"}
    try:
        history_provider, _ = resolve_timeframe_provider("history")
        intraday_provider, _ = resolve_timeframe_provider("intraday")
        report["providers"] = {
            "history": history_provider,
            "intraday": intraday_provider,
        }

        with open(os.devnull, "w") as devnull, contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            sync_all()
        report["data_status"] = get_data_status_logic()

        tickers = DataManager.list_tickers()[:5]
        sample_checks = []
        for t in tickers:
            row = {"ticker": t}
            try:
                daily = DataManager.get_stock_data(t, include_live=False)
                intra_merged = DataManager.get_stock_data(t, include_live=True)
                row["daily_rows"] = 0 if daily is None else len(daily)
                row["merged_rows"] = 0 if intra_merged is None else len(intra_merged)
                row["daily_ok"] = row["daily_rows"] >= 60
                row["merged_ok"] = row["merged_rows"] >= 60
            except Exception as e:
                row["error"] = str(e)
            sample_checks.append(row)
        report["sample_ticker_checks"] = sample_checks

        with open(os.devnull, "w") as devnull, contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            daily_signals, _, daily_breadth, daily_regime = DailyScanner.get_market_signals(
                index_choice="EGX30",
                is_intraday=False,
            )
            intra_signals, _, intra_breadth, intra_regime = DailyScanner.get_market_signals(
                index_choice="EGX30",
                is_intraday=True,
            )
        report["signal_scan"] = {
            "daily": {
                "signals": len(daily_signals),
                "breadth": round(float(daily_breadth), 2),
                "regime": daily_regime,
            },
            "intraday": {
                "signals": len(intra_signals),
                "breadth": round(float(intra_breadth), 2),
                "regime": intra_regime,
            },
        }
    except Exception as e:
        report["status"] = "error"
        report["error"] = str(e)
        report["traceback"] = traceback.format_exc()

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
