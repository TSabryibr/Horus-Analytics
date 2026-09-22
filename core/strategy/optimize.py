import logging
import pandas as pd
from fastapi import HTTPException
from core.DataManager import DataManager
from core.simulation import Optimizer
from routes import shared

logger = logging.getLogger("StrategyAPI")

def _safe_log_exception(message: str) -> None:
    try:
        logger.exception(message)
    except Exception:
        # Never let logging failures mask API errors.
        pass

def _load_price_action_frame(ticker: str, *, intraday: bool) -> pd.DataFrame:
    raw_df = (
        DataManager.get_intraday_data(ticker, refresh_if_stale=False)
        if intraday
        else DataManager.get_stock_data(ticker, include_live=False)
    )
    if raw_df is None or raw_df.empty:
        raise HTTPException(status_code=404, detail=f"No {'intraday' if intraday else 'daily'} data found for ticker '{ticker}'")
    frame = raw_df.copy()
    if "Date" in frame.columns:
        frame["Date"] = pd.to_datetime(frame["Date"])
        frame = frame.set_index("Date")
    if not isinstance(frame.index, pd.DatetimeIndex):
        frame.index = pd.to_datetime(frame.index)
    return frame.sort_index()

def background_optimize_task(index: str):
    try:
        Optimizer.run_optimization_api(index, shared.OPTIMIZATION_STATE)
    except Exception as e:
        with shared.OPTIMIZATION_STATE_LOCK:
            shared.OPTIMIZATION_STATE["status"] = "ERROR"
            shared.OPTIMIZATION_STATE["error"] = str(e)
