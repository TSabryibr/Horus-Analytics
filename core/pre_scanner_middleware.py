import pandas as pd
import numpy as np
import datetime
import uuid
from core.settings import settings
from core import TimeUtils
from utils.currency_fetcher import get_historical_usd_egp_rate, get_parallel_usd_egp_rate
from core.data.ParallelUSDFeed import usd_parallel_feed

# USD stocks that do not need normalization
USD_STOCKS = {'EGBE', 'TRTO', 'NAHO', 'GPPL', 'SAIB', 'NDRL', 'FAITA', 'EGSA', 'MOIL', 'CFGH', 'GTEX'}

class DataValidationError(Exception):
    """Exception raised for errors in data validation."""
    pass

class PreScannerMiddleware:
    @staticmethod
    def process(ticker: str, df: pd.DataFrame) -> tuple[pd.DataFrame, str, dict]:
        """
        Processes a stock DataFrame before scanning:
        1. Generates a unique signal_id.
        2. Validates data freshness and integrity.
        3. Converts EGP tickers to Synthetic USD-Denominated time series.
        4. Captures the pre-scanner raw inputs snapshot.

        Returns (df_processed: pd.DataFrame, signal_id: str, raw_snapshot: dict).
        """
        ticker_upper = str(ticker).upper().strip()
        signal_id = f"SIG-{ticker_upper}-{uuid.uuid4().hex[:12].upper()}"

        # 1. Validation
        if df is None or df.empty:
            raise DataValidationError(f"DataFrame for {ticker_upper} is empty or None")

        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise DataValidationError(f"Missing required columns in {ticker_upper}: {missing_cols}")

        if len(df) < 100:
            raise DataValidationError(f"Insufficient data points for {ticker_upper}: has {len(df)}, need at least 100")

        # Check for NaNs/nulls in critical columns on the last bar
        last_row = df.iloc[-1]
        for col in required_cols:
            if pd.isna(last_row[col]) or (col != 'Volume' and last_row[col] <= 0):
                raise DataValidationError(f"Invalid last bar for {ticker_upper}: {col} is null or <= 0")

        # Check freshness of the latest timestamp
        latest_ts = df.index[-1]
        if isinstance(latest_ts, pd.Timestamp):
            latest_dt = latest_ts.to_pydatetime()
        else:
            latest_dt = pd.to_datetime(latest_ts).to_pydatetime()

        current_time = TimeUtils.now()
        # Convert timezone-aware current_time to naive if latest_dt is naive
        if latest_dt.tzinfo is None and current_time.tzinfo is not None:
            current_time = current_time.replace(tzinfo=None)
        elif latest_dt.tzinfo is not None and current_time.tzinfo is None:
            import pytz
            current_time = pytz.utc.localize(current_time)

        freshness_threshold_days = float(getattr(settings, "FRESHNESS_THRESHOLD_DAYS", 3.0))
        delta_days = (current_time - latest_dt).total_seconds() / 86400.0
        if delta_days > freshness_threshold_days:
            # We raise a validation warning (stale data)
            raise DataValidationError(
                f"Data for {ticker_upper} is stale. Last update: {latest_dt.isoformat()}, "
                f"delta: {delta_days:.1f} days (limit: {freshness_threshold_days} days)"
            )

        # 2. Capture raw EGP nominal snapshot before conversion
        raw_snapshot = {
            "raw_open_egp": float(last_row['Open']),
            "raw_high_egp": float(last_row['High']),
            "raw_low_egp": float(last_row['Low']),
            "raw_close_egp": float(last_row['Close']),
            "raw_volume": int(last_row['Volume']),
            "currency": "USD" if ticker_upper in USD_STOCKS else "EGP",
            "usd_egp_rate_spot": (lambda r, f: r)(*usd_parallel_feed.get_live_rvu_rate())
        }

        # 3. Currency Normalization (EGP -> USD Synthetic)
        df_processed = df.copy()
        if raw_snapshot["currency"] == "EGP":
            # Map index dates to historical exchange rates
            rates = df_processed.index.map(lambda dt: get_historical_usd_egp_rate(dt))
            rates_series = pd.Series(rates, index=df_processed.index)

            # Divide price columns by exchange rate series
            for col in ['Open', 'High', 'Low', 'Close']:
                df_processed[col] = df_processed[col] / rates_series

            # Add USD prefix keys to snapshot
            raw_snapshot["raw_close_usd"] = float(last_row['Close'] / rates_series.iloc[-1])
        else:
            raw_snapshot["raw_close_usd"] = float(last_row['Close'])

        return df_processed, signal_id, raw_snapshot
