"""
DATA MANAGER MODULE
===================
Centralized data access layer.
Now powered by high-performance Parquet Data Lake (data_engine).

Includes a source-validated normalisation cache for history DataFrames
to avoid repeated column reshaping on every call.
"""

from core.settings import settings
from datetime import datetime
import os
import threading
import pandas as pd
from core import Heimdall
from core import TimeUtils
from data_engine import api as data_engine_api
from data_engine.freshness import evaluate_freshness, get_runtime_ticker_report
from data_engine.ticker_filters import is_supported_ticker
from core.exclusions import get_excluded_tickers_upper, normalize_ticker

_LAST_INTRADAY_REFRESH_ATTEMPT = None
_INTRADAY_REFRESH_LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# History DataFrame Cache  (source-validated, NOT TTL-based)
# ---------------------------------------------------------------------------
# Caches the *normalised* result of data_engine_api.get_data + column rename
# + index setup so that normalisation isn't repeated for identical data.
#
# Key  : (ticker, realm)
# Value: (content_fingerprint, normalised_DataFrame)
#
# Every call reads from source first (fast — data_engine_api.get_data has its own
# mtime-based Parquet cache).  The DataManager cache only skips the
# normalisation step (column rename + index + dedup) when the source's
# content fingerprint matches the cached entry.  This guarantees:
#   - None propagates immediately when source has no data.
#   - Source data changes are never masked.
# ---------------------------------------------------------------------------
_HISTORY_CACHE_LOCK = threading.Lock()
_HISTORY_CACHE: dict[tuple[str, str], tuple[tuple, pd.DataFrame]] = {}
_HISTORY_CACHE_MAX = int(os.getenv("DM_HISTORY_CACHE_MAX_ENTRIES", "128"))
_SIMULATION_HISTORY_CACHE_LOCK = threading.Lock()
_SIMULATION_HISTORY_CACHE: dict[tuple[str, str, tuple, str], pd.DataFrame] = {}
_SIMULATION_HISTORY_CACHE_MAX = int(os.getenv("DM_SIMULATION_HISTORY_CACHE_MAX_ENTRIES", "256"))
_SIMULATION_STOCK_DATA_CACHE_LOCK = threading.Lock()
_SIMULATION_STOCK_DATA_CACHE: dict[tuple[str, str, tuple, str, bool], pd.DataFrame] = {}
_SIMULATION_STOCK_DATA_CACHE_MAX = int(os.getenv("DM_SIMULATION_STOCK_CACHE_MAX_ENTRIES", "256"))



def calculate_projected_volume(
    raw_volume: float | pd.Series,
    now_dt: datetime,
    *,
    is_market_open: bool = True,
    is_simulating: bool = False,
    market_open_hm: tuple[int, int] = (10, 0),
    market_close_hm: tuple[int, int] = (14, 30),
    projection_threshold_hm: tuple[int, int] = (10, 45),
) -> float | pd.Series:
    """
    Projects daily live volume based on elapsed market session fraction
    using an empirical EGX U-curve intraday distribution.

    Rules:
    - Never project during replay or simulation (is_simulating=True).
    - Never project when market is closed (is_market_open=False).
    - Never project before projection threshold time (default 10:45 AM).
    - Uses 3-phase EGX volume distribution (35% morning, 40% midday, 25% close).
    - Multiplier is capped at a maximum of 3.5x to prevent phantom spikes.
    """
    if not is_market_open or is_simulating:
        return raw_volume

    open_h, open_m = market_open_hm
    close_h, close_m = market_close_hm
    thresh_h, thresh_m = projection_threshold_hm

    proj_threshold = now_dt.replace(hour=thresh_h, minute=thresh_m, second=0, microsecond=0)
    if now_dt < proj_threshold:
        return raw_volume

    session_start = now_dt.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
    session_end = now_dt.replace(hour=close_h, minute=close_m, second=0, microsecond=0)

    if now_dt >= session_end:
        return raw_volume

    session_total_secs = max(1.0, (session_end - session_start).total_seconds())
    elapsed_secs = (now_dt - session_start).total_seconds()

    if elapsed_secs <= 0 or session_total_secs <= 0:
        return raw_volume

    elapsed_mins = elapsed_secs / 60.0
    # EGX 270-minute session U-curve profile:
    # 0-45m (10:00-10:45): 35% of volume
    # 45-210m (10:45-13:30): 40% of volume (cumulative 75%)
    # 210-270m (13:30-14:30): 25% of volume (cumulative 100%)
    if elapsed_mins <= 45.0:
        expected_cdf = 0.35 * max(0.1, elapsed_mins / 45.0)
    elif elapsed_mins <= 210.0:
        expected_cdf = 0.35 + 0.40 * ((elapsed_mins - 45.0) / 165.0)
    elif elapsed_mins <= 270.0:
        expected_cdf = 0.75 + 0.25 * ((elapsed_mins - 210.0) / 60.0)
    else:
        expected_cdf = 1.0

    # Cap maximum multiplier at 3.5x (expected_cdf >= 0.285)
    effective_cdf = min(1.0, max(0.285, expected_cdf))
    if effective_cdf >= 1.0:
        return raw_volume

    return raw_volume / effective_cdf


def _evict_oldest_if_full(cache: dict, max_size: int) -> None:
    """FIFO eviction when cache exceeds max_size (dict preserves insertion order)."""
    while len(cache) > max_size:
        cache.pop(next(iter(cache)))


def invalidate_history_cache(ticker: str | None = None, realm: str | None = None) -> None:
    """Public helper — sync worker or ingest code can call this after writes."""
    target_realm = realm or getattr(Heimdall, "CURRENT_REALM", "EGX")
    with _HISTORY_CACHE_LOCK:
        if ticker is None:
            _HISTORY_CACHE.clear()
        else:
            _HISTORY_CACHE.pop((ticker.upper(), target_realm), None)
    with _SIMULATION_HISTORY_CACHE_LOCK:
        if ticker is None:
            _SIMULATION_HISTORY_CACHE.clear()
        else:
            symbol = ticker.upper()
            keys_to_remove = [
                key for key in _SIMULATION_HISTORY_CACHE
                if key[0] == symbol and key[1] == target_realm
            ]
            for key in keys_to_remove:
                _SIMULATION_HISTORY_CACHE.pop(key, None)
    with _SIMULATION_STOCK_DATA_CACHE_LOCK:
        if ticker is None:
            _SIMULATION_STOCK_DATA_CACHE.clear()
        else:
            symbol = ticker.upper()
            keys_to_remove = [
                key for key in _SIMULATION_STOCK_DATA_CACHE
                if key[0] == symbol and key[1] == target_realm
            ]
            for key in keys_to_remove:
                _SIMULATION_STOCK_DATA_CACHE.pop(key, None)


def _should_attempt_intraday_refresh(now_ts: pd.Timestamp) -> bool:
    # If a worker is expected externally, the backend should be read-only for writes.
    # This prevents 'database is locked' races during market scans.
    worker_mode = os.getenv("PIPELINE_SYNC_WORKER_MODE", "internal").lower()
    if worker_mode == "external":
        return False

    cooldown_sec = int(os.getenv("INTRADAY_REFRESH_COOLDOWN_SEC", "120"))
    if _LAST_INTRADAY_REFRESH_ATTEMPT is None:
        return True
    elapsed = (now_ts - _LAST_INTRADAY_REFRESH_ATTEMPT).total_seconds()
    return elapsed >= max(5, cooldown_sec)


def _refresh_intraday_cache_once() -> bool:
    """
    Pull latest intraday bars from local source-of-truth into intraday store.
    Uses provider policy (AUTO / CSV / MUBASHER_DB) from 
    """
    global _LAST_INTRADAY_REFRESH_ATTEMPT
    
    # Atomic check-and-set to prevent lock storms in concurrent scans
    with _INTRADAY_REFRESH_LOCK:
        now_ts = TimeUtils.pd_now()
        if not _should_attempt_intraday_refresh(now_ts):
            return False
        
        _LAST_INTRADAY_REFRESH_ATTEMPT = now_ts
        try:
            from data_engine.ingest_intraday import ingest_intraday
            from data_engine.local_feed_selector import resolve_timeframe_provider
            provider, _ = resolve_timeframe_provider(timeframe="intraday")
            updated = ingest_intraday(provider=provider)
            return updated >= 0
        except Exception as e:
            print(f"[DataManager] Intraday refresh failed: {e}")
            return False


def _intraday_is_stale(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return True
    try:
        last_ts = pd.to_datetime(df.index.max())
    except Exception:
        return True
    if pd.isna(last_ts):
        return True
    stale_minutes = int(os.getenv("INTRADAY_STALE_THRESHOLD_MIN", "45"))
    age_minutes = (TimeUtils.pd_now() - last_ts).total_seconds() / 60.0
    return age_minutes > max(1, stale_minutes)


def _normalize_history_df(df: pd.DataFrame | None) -> pd.DataFrame | None:
    """Column rename + DatetimeIndex setup shared by get_stock_data and cache."""
    if df is None or df.empty:
        return None
        
    # Fast path: If already a DatetimeIndex and sorted, skip major processing
    if isinstance(df.index, pd.DatetimeIndex) and df.index.is_monotonic_increasing:
        # Check if we still have the 'Date' column or legacy columns needing rename
        if 'High' in df.columns and 'Close' in df.columns:
            return df

    df = df.reset_index()
    # Optimized rename using dict.get for performance on large column sets if ever applicable
    df = df.rename(columns={
        'index': 'Date', 'timestamp': 'Date',
        'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
    })
    
    if 'Date' in df.columns:
        if not isinstance(df['Date'].dtype, pd.DatetimeTZDtype) and not pd.api.types.is_datetime64_any_dtype(df['Date']):
            df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date').sort_index()
        
    # Only run duplicated check if necessary (expensive on very large DFs)
    if df.index.has_duplicates:
        df = df[~df.index.duplicated(keep='last')]
        
    if 'index' in df.columns:
        df = df.drop(columns=['index'])
    return df


def _source_fingerprint(df: pd.DataFrame) -> tuple:
    """Cheap content fingerprint: (row_count, first_index, last_index)."""
    cached_fp = df.attrs.get("_dm_source_fingerprint")
    if cached_fp is not None:
        return cached_fp
    try:
        first_index = df.index[0]
        last_index = df.index[-1]
        if isinstance(df.index, pd.DatetimeIndex):
            fingerprint = (len(df), first_index.value, last_index.value)
        else:
            fingerprint = (len(df), first_index, last_index)
        df.attrs["_dm_source_fingerprint"] = fingerprint
        return fingerprint
    except Exception:
        return (len(df),)


def _get_cached_history(ticker: str, realm: str, limit: int | None = None) -> pd.DataFrame | None:
    """
    Source-validated normalisation cache.

    Always reads from source first (fast — data_engine_api.get_data has its own
    mtime-based Parquet cache).  The DataManager cache only skips the
    normalisation step (column rename + index + dedup) when the source's
    content fingerprint matches the cached entry.  This guarantees:
      - None propagates immediately when source has no data.
      - Source data changes are never masked.
    """
    cache_key = (ticker.upper(), realm)

    # 1. Always read from source
    # CRITICAL: During simulation, bypass SQL-level LIMIT so we can filter by simulated time first.
    sql_limit = limit if not TimeUtils.is_simulating() else None
    raw_df = data_engine_api.get_data(ticker, timeframe='history', realm=realm, limit=sql_limit)

    # 2. Source returns None → evict cache entry and propagate None
    if raw_df is None or raw_df.empty:
        if limit is None:
            with _HISTORY_CACHE_LOCK:
                _HISTORY_CACHE.pop(cache_key, None)
        return None

    # 3. Limited reads bypass cache (uncommon path)
    if limit is not None and not TimeUtils.is_simulating():
        return _normalize_history_df(raw_df)

    # 4. Check if cached normalisation matches current source data
    fp = _source_fingerprint(raw_df)
    cached_ref = None
    with _HISTORY_CACHE_LOCK:
        cached = _HISTORY_CACHE.get(cache_key)
        if cached is not None and cached[0] == fp:
            cached_ref = cached[1]
    
    if cached_ref is not None:
        cached_copy = cached_ref.copy()
        cached_copy.attrs["_dm_source_fingerprint"] = fp
        return cached_copy

    # 5. Normalise and cache
    df = _normalize_history_df(raw_df)
    if df is None:
        return None
    df.attrs["_dm_source_fingerprint"] = fp

    df_copy = df.copy()
    with _HISTORY_CACHE_LOCK:
        _HISTORY_CACHE[cache_key] = (fp, df_copy)
        _evict_oldest_if_full(_HISTORY_CACHE, _HISTORY_CACHE_MAX)

    return df.copy()


def _get_simulation_filtered_history(
    ticker: str,
    realm: str,
    df: pd.DataFrame,
    cutoff: pd.Timestamp,
    strict: bool = False,
) -> pd.DataFrame | None:
    """
    Cache simulation-era slices to avoid repeated DateTimeIndex filtering inside
    hot backtest loops. Always returns a copy so callers cannot mutate the cache.
    """
    if df is None:
        return None

    normalized_cutoff = pd.Timestamp(cutoff)
    if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None and normalized_cutoff.tzinfo is None:
        normalized_cutoff = normalized_cutoff.tz_localize(df.index.tz)

    cache_key = (
        ticker.upper(),
        realm,
        _source_fingerprint(df),
        normalized_cutoff.isoformat(),
    )

    with _SIMULATION_HISTORY_CACHE_LOCK:
        cached = _SIMULATION_HISTORY_CACHE.get(cache_key)
        if cached is not None:
            return cached.copy()

    if strict:
        # For historical daily bars, we want everything STRICTLY BEFORE the current day
        # to avoid EOD data leaks during intraday replay.
        normalized_cutoff = normalized_cutoff.normalize()
        if isinstance(df.index, pd.DatetimeIndex) and df.index.is_monotonic_increasing:
            cutoff_pos = df.index.searchsorted(normalized_cutoff, side="left")
            filtered = df.iloc[:cutoff_pos].copy()
        else:
            filtered = df.loc[df.index < normalized_cutoff].copy()
    else:
        # Standard filter
        if isinstance(df.index, pd.DatetimeIndex) and df.index.is_monotonic_increasing:
            cutoff_pos = df.index.searchsorted(normalized_cutoff, side="right")
            filtered = df.iloc[:cutoff_pos].copy()
        else:
            filtered = df.loc[:normalized_cutoff].copy()

    with _SIMULATION_HISTORY_CACHE_LOCK:
        _SIMULATION_HISTORY_CACHE[cache_key] = filtered
        _evict_oldest_if_full(_SIMULATION_HISTORY_CACHE, _SIMULATION_HISTORY_CACHE_MAX)

    return filtered.copy()


def _get_cached_simulation_stock_data(cache_key: tuple[str, str, tuple, str, bool]) -> pd.DataFrame | None:
    with _SIMULATION_STOCK_DATA_CACHE_LOCK:
        return _SIMULATION_STOCK_DATA_CACHE.get(cache_key)


def _cache_simulation_stock_data(cache_key: tuple[str, str, tuple, str, bool], df: pd.DataFrame) -> None:
    with _SIMULATION_STOCK_DATA_CACHE_LOCK:
        _SIMULATION_STOCK_DATA_CACHE[cache_key] = df
        _evict_oldest_if_full(_SIMULATION_STOCK_DATA_CACHE, _SIMULATION_STOCK_DATA_CACHE_MAX)


class DataManager:
    
    @staticmethod
    def get_universe_data(
        tickers: list[str],
        include_live: bool = False,
        history_limit: int | None = None,
    ):
        """
        Efficiently loads multiple tickers using the bulk I/O API.
        Returns a MultiIndex DataFrame [Ticker, Date].
        """
        if not tickers:
            return None
            
        realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
        # 1. Bulk load recent history only; the scanner needs a bounded window
        # for ATR/RSI/volume/resistance calculations, not full symbol history.
        if history_limit is None:
            history_limit = int(os.getenv("UNIVERSE_HISTORY_LIMIT", "90"))
        history_limit = max(30, history_limit)
        raw_df = data_engine_api.get_bulk_data(
            tickers,
            timeframe='history',
            realm=realm,
            limit=history_limit,
        )
        if raw_df is None or raw_df.empty:
            return None
            
        # 2. Rename columns
        raw_df = raw_df.rename(columns={
            'timestamp': 'Date',
            'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume',
            'ticker': 'Ticker'
        })
        
        # 3. Fast Datetime Conversion & Indexing
        # Note: Ticker is already UPPER from DuckDB Phase 7
        raw_df['Date'] = pd.to_datetime(raw_df['Date'], format='ISO8601', utc=True)
        
        df = raw_df.drop_duplicates(subset=['Ticker', 'Date'], keep='last')\
                   .set_index(['Ticker', 'Date'])\
                   .sort_index(level=[0, 1])
        
        # 4. Simulation Filter (Global)
        if TimeUtils.is_simulating():
            now_ts = TimeUtils.pd_now()
            # Ensure now_ts is tz-aware if df is
            if isinstance(df.index, pd.MultiIndex) and getattr(df.index.levels[1], 'tz', None) is not None and now_ts.tzinfo is None:
                 now_ts = now_ts.tz_localize('UTC')
            
            # CRITICAL: During simulation, exclude the daily bar for the CURRENT day 
            # if we are in the middle of that day. This prevents "future-leak" where 
            # a daily bar already contains the EOD close/high/low.
            # We only allow bars strictly BEFORE the current simulated day.
            day_cutoff = now_ts.normalize()
            df = df.loc[df.index.get_level_values(1) < day_cutoff]
            
        # 5. LIVE MERGE: Add today's intraday data if it exists
        if include_live:
            try:
                from data_engine.intraday_store import get_bulk_intraday_data
                today_dt = TimeUtils.today()
                if settings.is_market_open() or TimeUtils.is_simulating():
                    since_ts = pd.Timestamp(today_dt).normalize().strftime("%Y-%m-%d 00:00:00")
                else:
                    last_trading_day = getattr(settings, "get_last_completed_market_day", lambda: today_dt)()
                    since_ts = pd.Timestamp(last_trading_day).normalize().strftime("%Y-%m-%d 00:00:00")
                intra_raw = get_bulk_intraday_data(tickers, realm=realm, since_timestamp=since_ts)
                
                # --- GLOBAL TIME TRAVEL FILTER (Intraday) ---
                if TimeUtils.is_simulating():
                    now_ts = TimeUtils.pd_now()
                    if not intra_raw.empty:
                        # Ensure timezone awareness matches
                        if getattr(intra_raw['timestamp'].dt, 'tz', None) is not None and now_ts.tzinfo is None:
                            now_ts = now_ts.tz_localize('UTC')
                        intra_raw = intra_raw[intra_raw['timestamp'] <= now_ts]

                if not intra_raw.empty:
                    # Capture the latest session per ticker and aggregate into a daily bar
                    # Vectorized approach:
                    intra_raw['Date_Normal'] = pd.to_datetime(intra_raw['timestamp']).dt.normalize()
                    
                    # Find absolute latest day present in the intraday store for each ticker
                    latest_days = intra_raw.groupby('ticker')['Date_Normal'].max().reset_index()
                    latest_days.columns = ['ticker', 'latest_session_day']
                    if settings.is_market_open():
                        expected_live_day = pd.Timestamp(TimeUtils.today()).normalize()
                        latest_days = latest_days[
                            pd.to_datetime(latest_days['latest_session_day'], errors='coerce').dt.normalize()
                            == expected_live_day
                        ]
                    
                    # Filter for only those latest session bars
                    if latest_days.empty:
                        session_bars = pd.DataFrame()
                    else:
                        session_bars = intra_raw.merge(latest_days, on='ticker')
                        session_bars = session_bars[session_bars['Date_Normal'] == session_bars['latest_session_day']]
                    
                    if not session_bars.empty:
                        # Aggregate OHLCV
                        live_daily = session_bars.groupby('ticker').agg({
                            'latest_session_day': 'first',
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        })
                        
                        live_daily = live_daily.rename(columns={
                            'latest_session_day': 'Date',
                            'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
                        })

                        # Normalize volume by elapsed session fraction if market is open and after 10:30 AM
                        # Skip during Replay/Simulation — Replay feeds complete session data,
                        # projecting would inflate volumes incorrectly.
                        if settings.is_market_open() and not TimeUtils.is_simulating():
                            open_h, open_m = settings.get_market_open_hour_minute()
                            close_h, close_m = settings.get_market_close_hour_minute()
                            live_daily['Volume'] = calculate_projected_volume(
                                live_daily['Volume'],
                                TimeUtils.now(),
                                is_market_open=settings.is_market_open(),
                                is_simulating=TimeUtils.is_simulating(),
                                market_open_hm=(open_h, open_m),
                                market_close_hm=(close_h, close_m),
                            )

                        live_daily['Ticker'] = live_daily.index
                        live_daily['Date'] = pd.to_datetime(live_daily['Date'], utc=True)
                        live_daily = live_daily.set_index(['Ticker', 'Date'])
                        
                        # Concatenate and drop duplicates (live bars win)
                        df = pd.concat([df, live_daily])
                        df = df[~df.index.duplicated(keep='last')].sort_index()
                        
            except Exception as e:
                print(f"[DataManager] Bulk live merge failed: {e}")
            
        return df

    @staticmethod
    def get_stock_data(
        ticker: str,
        source: str | None = None,
        folder: str | None = None,
        include_live: bool = True,
        limit: int | None = None,
        enrich_obv: bool = False,
    ):
        """
        Load stock data. Automatically switches between Local Parquet and Global APIs.
        If include_live is True, it appends today's intraday data as a running daily bar.
        """
        symbol = normalize_ticker(ticker)
        if symbol in get_excluded_tickers_upper():
            return None

        # 1. Check current source and realm from GlobalSettings/Heimdall
        active_source = getattr(settings, "DATA_SOURCE_TYPE", "PARQUET")
        realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
        
        # 2. If Global API source, use UniversalAdapter
        if active_source not in ["PARQUET", "LOCAL_METASTOCK"]:
            try:
                from core.adapters.UniversalAdapter import  UniversalDataEngine
                return UniversalDataEngine.get_history(symbol, source=active_source)
            except ImportError:
                print("⚠️ UniversalAdapter not found. Falling back to local.")
        
        # 3. Load from cached normalised history
        df = _get_cached_history(symbol, realm=realm, limit=limit)
        if df is None:
            return None
            
        # --- GLOBAL TIME TRAVEL FILTER ---
        now_ref = TimeUtils.now()
        simulation_cache_key = None
        if TimeUtils.is_simulating():
            now_ts = TimeUtils.pd_now()
            simulation_cache_key = (
                symbol,
                realm,
                _source_fingerprint(df),
                pd.Timestamp(now_ts).isoformat(),
                enrich_obv,
            )
            if limit is None and not include_live:
                cached_sim_df = _get_cached_simulation_stock_data(simulation_cache_key)
                if cached_sim_df is not None:
                    return cached_sim_df
            # Hide "future" bars. We use 'strict=True' for history to exclude 
            # the daily bar for the current simulated day (preventing EOD leak).
            df = _get_simulation_filtered_history(symbol, realm, df, now_ts, strict=True)

            # Apply limit manually after time filtering
            if limit is not None and df is not None:
                df = df.tail(limit)

            include_live = False # Never add live feed in simulation

        if df is None or df.empty:
            return df

        # 4. LIVE MERGE: Add today's intraday data if it exists
        if include_live:
            intra_df = DataManager.get_intraday_data(symbol)
            if intra_df is not None and not intra_df.empty:
                # Merge the latest available intraday session (not only "today").
                latest_session_day = pd.to_datetime(intra_df.index.max()).normalize()
                session_intra = intra_df[pd.to_datetime(intra_df.index).normalize() == latest_session_day]

                if not session_intra.empty:
                    live_vol = session_intra['Volume'].sum()
                    live_bar = pd.DataFrame({
                        'Open': [session_intra['Open'].iloc[0]],
                        'High': [session_intra['High'].max()],
                        'Low': [session_intra['Low'].min()],
                        'Close': [session_intra['Close'].iloc[-1]],
                        'Volume': [live_vol]
                    }, index=[latest_session_day])

                    # If history already has a much "richer" bar for same session, keep history.
                    should_merge = True
                    if settings.is_market_open() and latest_session_day.date() != TimeUtils.today():
                        should_merge = False
                    if df is not None and latest_session_day in df.index:
                        hist_row = df.loc[latest_session_day]
                        hist_vol = float(hist_row['Volume']) if not isinstance(hist_row, pd.DataFrame) else float(hist_row['Volume'].iloc[-1])
                        if hist_vol > live_vol * 1.05:
                            should_merge = False

                    if should_merge and df is not None:
                        df = df[df.index != latest_session_day]
                        df = pd.concat([df, live_bar])

        # 5. SAFETY: Deduplicate index (prevents crashes in alignment)
        if df is not None and not df.empty:
            df = df[~df.index.duplicated(keep='last')]
            if 'index' in df.columns:
                df = df.drop(columns=['index'])

            if enrich_obv:
                import numpy as np
                df['OBV'] = (np.sign(df['Close'].diff().fillna(0)) * df['Volume']).cumsum()

        if simulation_cache_key is not None and limit is None and not include_live:
            # Simulation scans are read-heavy and repeatedly request the same
            # snapshot. Cache the final DataFrame to avoid re-slicing/copying
            # on each symbol pass.
            _cache_simulation_stock_data(simulation_cache_key, df)

        return df

    @staticmethod
    def refresh_intraday_cache_if_due() -> bool:
        """
        Refresh intraday storage on active monitoring paths.

        Exit monitoring cannot wait for the broader "stale" threshold because a
        target/stop can be hit while the cached store is only a few minutes old.
        The underlying refresh helper still applies its cooldown and worker-mode
        guard, so callers can invoke this frequently without hammering ingest.
        """
        if TimeUtils.is_simulating():
            return False
        return _refresh_intraday_cache_once()

    @staticmethod
    def get_intraday_data(ticker: str, limit: int | None = None, refresh_if_stale: bool = True):
        """
        Load intraday data from the Data Engine.
        """
        symbol = normalize_ticker(ticker)
        if symbol in get_excluded_tickers_upper():
            return None

        realm = getattr(Heimdall, "CURRENT_REALM", "EGX")

        # 1. Load data first (H5 Optimization: avoids probe query)
        # CRITICAL: During simulation, bypass SQL-level LIMIT so we can filter by simulated time first.
        # Otherwise, SQL LIMIT DESC will return "future" bars that our time filter will then strip, leaving an empty DF.
        sql_limit = limit if not TimeUtils.is_simulating() else None
        df = data_engine_api.get_data(symbol, timeframe='intraday', realm=realm, limit=sql_limit)

        # 2. Check staleness on the result if refresh is enabled
        require_market_open = os.getenv("INTRADAY_REFRESH_REQUIRE_MARKET_OPEN", "0").strip().lower() in {"1", "true", "yes", "on"}
        market_open = settings.is_market_open()

        if refresh_if_stale and not TimeUtils.is_simulating() and (market_open or not require_market_open):
            now_ts = TimeUtils.pd_now()
            # If stale, refresh once and reload
            if _intraday_is_stale(df) and _should_attempt_intraday_refresh(now_ts):
                _refresh_intraday_cache_once()
                df = data_engine_api.get_data(symbol, timeframe='intraday', realm=realm, limit=sql_limit)

        if df is None or df.empty:
            return None
            
        # 3. Normalize Columns
        df = df.reset_index()
        df = df.rename(columns={
            'index': 'timestamp', # ensure we can target it
            'timestamp': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date').sort_index()
            
        # --- GLOBAL TIME TRAVEL FILTER ---
        if TimeUtils.is_simulating():
            now_ts = TimeUtils.pd_now()
            df = df.loc[:now_ts]
            # Apply limit manually after time filtering
            if limit is not None:
                df = df.tail(limit)
            
        # 4. SAFETY: Deduplicate index
        df = df[~df.index.duplicated(keep='last')]

        if 'index' in df.columns:
            df = df.drop(columns=['index'])
            
        return df

    @staticmethod
    def list_tickers(source: str | None = None, folder: str | None = None):
        """
        List available tickers in the Data Lake.
        No DataManager-level cache — data_engine_api.list_tickers() already
        has its own 60 s TTL cache, avoiding a second layer of staleness.
        """
        realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
        tickers = data_engine_api.list_tickers(timeframe='history', realm=realm)
        excluded = get_excluded_tickers_upper()
        runtime_report = get_runtime_ticker_report(realm=realm, ref_date=TimeUtils.today())
        runtime_quarantined = {
            normalize_ticker(item.get("ticker"))
            for item in runtime_report.get("runtime_quarantined", [])
            if normalize_ticker(item.get("ticker"))
        }
        return [
            t
            for t in tickers
            if normalize_ticker(t) not in excluded
            and is_supported_ticker(t)
            and normalize_ticker(t) not in runtime_quarantined
        ]

    @staticmethod
    def get_data_status(folder: str | None = None):
        """
        Check Data Lake status.
        """
        realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
        status = evaluate_freshness(realm=realm, run_date=TimeUtils.today(), scan_type="DAILY")
        history = status.get("history", {})
        kpis = history.get("kpis", {})
        return {
            "status": history.get("status", "UNKNOWN"),
            "last_updated": history.get("last_updated"),
            "expected_last_working_day": history.get("expected_last_working_day"),
            "file_count": kpis.get("symbol_count", 0),
            "fresh_symbols": kpis.get("fresh_symbols", 0),
            "stale_symbols": kpis.get("stale_symbols", 0),
            "fresh_ratio": kpis.get("fresh_ratio", 0.0),
        }
