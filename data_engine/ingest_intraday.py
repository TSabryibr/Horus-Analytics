from core.exclusions import get_all_exclusions
from core.settings import settings
from pathlib import Path
import time
import os

import pandas as pd

from core import TimeUtils
from data_engine import intraday_store
from data_engine import parquet_writer
from data_engine import api as data_engine_api
from data_engine.provider_selection import resolve_timeframe_provider
from data_engine.directfn_feed_source import (
    detect_layout as detect_directfn_layout,
    iter_intraday_files as directfn_iter_intraday_files,
    load_symbol_map as load_directfn_symbol_map,
    read_intraday_file as directfn_read_intraday_file,
)
from data_engine.metastock_dat_source import (
    detect_layout as detect_metastock_dat_layout,
    iter_intraday_files as metastock_dat_iter_intraday_files,
    load_symbol_map as load_metastock_dat_symbol_map,
    read_intraday_file as metastock_dat_read_intraday_file,
)
from data_engine.mubasher_sqlite_source import (
    build_paths,
    epoch_minute_to_local_naive,
    get_intraday_latest_bars,
    list_intraday_symbols,
    load_intraday_dataframe,
    local_naive_to_epoch_minute,
)
from data_engine.mubasher_realtime_source import fetch_realtime_snapshots
from data_engine.observability import emit_event
from data_engine.ticker_filters import is_supported_ticker

try:
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover - optional optimization
    pq = None


from datetime import timedelta
import contextlib


_LAST_INGEST_INTRADAY_SUMMARY: dict[str, object] = {}


def _set_last_ingest_intraday_summary(**summary) -> None:
    _LAST_INGEST_INTRADAY_SUMMARY.clear()
    _LAST_INGEST_INTRADAY_SUMMARY.update(summary)


def get_last_ingest_intraday_summary() -> dict[str, object]:
    return dict(_LAST_INGEST_INTRADAY_SUMMARY)

@contextlib.contextmanager
def _ingestion_lock():
    lock_file = Path(settings.DATA_ROOT) / "ingest_intraday.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Simple PID-based lock file
    if lock_file.exists():
        try:
            # Check if process is still alive (crude but effective)
            old_pid = int(lock_file.read_text().strip())
            # Cross-session PID checks can be unreliable on Windows, so treat
            # fresh lock files as active and stale ones as recoverable.
            mtime = lock_file.stat().st_mtime
            if (time.time() - mtime) < 600:
                # Still fresh, assume locked
                yield False
                return
        except Exception:
            pass
            
    try:
        lock_file.write_text(str(os.getpid()))
        yield True
    finally:
        try:
            if lock_file.exists():
                lock_file.unlink()
        except Exception:
            pass


def _intraday_file_path(ticker: str, realm: str = "EGX") -> Path:
    return Path(settings.DATA_ROOT) / realm / "intraday" / f"{ticker}.parquet"


def _read_parquet_max_timestamp(file_path: Path):
    if pq is None:
        return None
    try:
        pf = pq.ParquetFile(file_path)
        meta = pf.metadata
        max_ts = None
        for rg_idx in range(meta.num_row_groups):
            row_group = meta.row_group(rg_idx)
            for col_idx in range(row_group.num_columns):
                col = row_group.column(col_idx)
                if col.path_in_schema not in ("timestamp", "__index_level_0__"):
                    continue
                stats = col.statistics
                if stats is None or stats.max is None:
                    continue
                candidate = pd.to_datetime(stats.max, errors="coerce")
                if pd.isna(candidate):
                    continue
                if max_ts is None or candidate > max_ts:
                    max_ts = candidate
        return max_ts
    except Exception:
        return None


def _get_last_parquet_minute(ticker: str, realm: str = "EGX") -> int | None:
    df = data_engine_api.get_data(ticker, timeframe="intraday", realm=realm)
    if df is None or df.empty:
        return None
    max_ts = pd.to_datetime(df.index.max(), errors="coerce")
    if pd.isna(max_ts):
        return None
    return local_naive_to_epoch_minute(max_ts)


def _get_last_ingested_minute(ticker: str, realm: str = "EGX") -> tuple[int | None, bool]:
    store_last_ts = intraday_store.get_last_timestamp(ticker, realm=realm)
    if store_last_ts is not None:
        minute = local_naive_to_epoch_minute(store_last_ts)
        if minute is not None:
            return minute, True
    return _get_last_parquet_minute(ticker, realm=realm), False


def _latest_bars_by_ticker(df: pd.DataFrame) -> dict[str, dict[str, object]]:
    if df is None or df.empty:
        return {}

    out: dict[str, dict[str, object]] = {}
    for row in df.itertuples(index=False):
        ticker = str(getattr(row, "ticker", "")).strip().upper()
        timestamp = pd.to_datetime(getattr(row, "timestamp", None), errors="coerce")
        if not ticker or pd.isna(timestamp):
            continue
        try:
            out[ticker] = {
                "timestamp": timestamp,
                "open": float(getattr(row, "open")),
                "high": float(getattr(row, "high")),
                "low": float(getattr(row, "low")),
                "close": float(getattr(row, "close")),
                "volume": float(getattr(row, "volume")),
            }
        except (TypeError, ValueError):
            continue
    return out


def _latest_bar_needs_refresh(
    store_latest: dict[str, object] | None,
    source_latest: dict[str, object] | None,
) -> bool:
    if not source_latest:
        return False
    if not store_latest:
        return True

    store_ts = pd.to_datetime(store_latest.get("timestamp"), errors="coerce")
    source_ts = pd.to_datetime(source_latest.get("timestamp"), errors="coerce")
    if pd.isna(store_ts) or pd.isna(source_ts) or store_ts != source_ts:
        return True

    eps = 1e-12
    for col in ("open", "high", "low", "close", "volume"):
        try:
            if abs(float(store_latest[col]) - float(source_latest[col])) > eps:
                return True
        except (KeyError, TypeError, ValueError):
            return True
    return False


def _latest_bar_frame(bar: dict[str, object]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": bar["timestamp"],
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
                "volume": bar["volume"],
            }
        ]
    )


def _source_minute_timestamp(source_tmin: int | None):
    if source_tmin is None:
        return None
    try:
        source_ts = epoch_minute_to_local_naive(pd.Series([int(source_tmin)])).iloc[0]
        source_ts = pd.to_datetime(source_ts, errors="coerce")
    except Exception:
        return None
    if pd.isna(source_ts):
        return None
    return source_ts


def _source_minute_before_today(source_tmin: int | None) -> bool:
    source_ts = _source_minute_timestamp(source_tmin)
    if source_ts is None:
        return False
    return source_ts.date() < TimeUtils.today()


def _source_archive_lags_live_day(source_last_minutes: dict[str, int]) -> bool:
    if not source_last_minutes:
        return False
    if not settings.is_market_open():
        return False
    try:
        latest_source_tmin = max(int(v) for v in source_last_minutes.values() if v is not None)
    except ValueError:
        return False

    source_ts = _source_minute_timestamp(latest_source_tmin)
    if source_ts is None:
        return False
    if source_ts.date() < TimeUtils.today():
        return True

    now_ts = pd.to_datetime(TimeUtils.now(), errors="coerce")
    if pd.isna(now_ts):
        return False
    if getattr(now_ts, "tzinfo", None) is not None:
        now_ts = now_ts.tz_localize(None)
    stale_minutes = max(1, int(getattr(settings, "LOCAL_INTRADAY_DB_STALE_MINUTES", 20)))
    age_minutes = (now_ts - source_ts).total_seconds() / 60.0
    return age_minutes >= stale_minutes


def _ingest_mubasher_realtime_overlay(symbols: list[str]) -> tuple[int, int]:
    if not getattr(settings, "MUBASHER_REALTIME_OVERLAY_ENABLED", False):
        return 0, 0
    if not symbols or not settings.is_market_open():
        return 0, 0

    try:
        snapshots = fetch_realtime_snapshots(
            symbols,
            Path(settings.MUBASHER_ROOT_DIR),
            user_id=(settings.MUBASHER_USER_ID or None),
        )
    except Exception as exc:
        print(f"[Warn] Mubasher realtime overlay unavailable: {exc}")
        return 0, 0

    today = TimeUtils.today()
    updated = 0
    rows_loaded = 0
    for ticker, snapshot in snapshots.items():
        frame = snapshot.to_intraday_frame()
        if frame.empty:
            continue
        ts = pd.to_datetime(frame["timestamp"].iloc[-1], errors="coerce")
        if pd.isna(ts) or ts.date() != today:
            continue
        written = intraday_store.upsert_intraday(ticker, frame, realm="EGX")
        if written <= 0:
            continue
        if getattr(settings, "INTRADAY_PARQUET_MIRROR", False):
            parquet_writer.save_stream(ticker, frame, folder="intraday")
        rows_loaded += int(written)
        updated += 1

    if snapshots:
        print(
            f"[Info] Mubasher realtime overlay: snapshots={len(snapshots)}, "
            f"updated={updated}, rows_loaded={rows_loaded}"
        )
    return updated, rows_loaded


def _ingest_intraday_from_csv() -> int:
    intraday_path = Path(settings.METASTOCK_INTRADAY_FOLDER)
    if not intraday_path.exists():
        print(f"[Error] Intraday path not found: {intraday_path}")
        return 0

    csv_files = list(intraday_path.glob("*.csv"))
    if not csv_files:
        return 0

    print(f"[Info] Found {len(csv_files)} intraday CSV files to ingest.")
    excluded = get_all_exclusions()
    updated = 0
    
    # We'll collect all updates and apply them in fewer store calls to reduce SQLite locking contention
    batch_size = 50
    current_batch: list[tuple[str, pd.DataFrame]] = []

    def flush_batch(batch):
        count = 0
        for t, d in batch:
            try:
                intraday_store.upsert_intraday(t, d, realm="EGX")
                if getattr(settings, "INTRADAY_PARQUET_MIRROR", False):
                    parquet_writer.save_stream(t, d, folder="intraday")
                count += 1
            except Exception as batch_e:
                if "locked" in str(batch_e).lower():
                    # Database is locked; this batch member failed. 
                    # We don't print full stack trace to avoid log spam during contention.
                    pass
                else:
                    print(f"[Error] Failed to store {t}: {batch_e}")
        return count

    for file_path in csv_files:
        try:
            ticker = file_path.stem.upper()
            if not is_supported_ticker(ticker) or ticker in excluded:
                continue

            # Check if file exists and is accessible before trying to read it
            # This minimizes noise from [Errno 2] during glob-to-read races
            if not file_path.exists():
                continue

            try:
                df = pd.read_csv(file_path)
            except (OSError, IOError) as io_e:
                # Handle transient filesystem errors common during file handoff.
                if getattr(io_e, 'errno', 0) in (2, 5, 14): # ENOENT, EIO, EFAULT
                    continue
                raise

            if "<DTYYYYMMDD>" not in df.columns or "<HHMMSS>" not in df.columns:
                continue

            date_str = df["<DTYYYYMMDD>"].astype(str)
            time_str = df["<HHMMSS>"].astype(str).str.zfill(6)
            df["timestamp"] = pd.to_datetime(date_str + time_str, format="%Y%m%d%H%M%S", errors="coerce")

            df.rename(
                columns={
                    "<OPEN>": "open",
                    "<HIGH>": "high",
                    "<LOW>": "low",
                    "<CLOSE>": "close",
                    "<VOL>": "volume",
                },
                inplace=True,
            )
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]
            df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])
            if df.empty:
                continue

            last_ts = intraday_store.get_last_timestamp(ticker, realm="EGX")
            if last_ts is not None:
                df = df[df["timestamp"] > last_ts]
                if df.empty:
                    continue

            current_batch.append((ticker, df))
            if len(current_batch) >= batch_size:
                updated += flush_batch(current_batch)
                current_batch = []
                
        except Exception as e:
            # Catch-all for other parsing errors
            print(f"[Error] Failed to ingest {file_path.name}: {e}")

    if current_batch:
        updated += flush_batch(current_batch)

    return updated


def _ingest_intraday_from_mubasher_db() -> int:
    try:
        paths = build_paths(
            Path(settings.MUBASHER_ROOT_DIR),
            user_id=(settings.MUBASHER_USER_ID or None),
        )
    except Exception as e:
        print(f"[Error] Mubasher DB source not available: {e}")
        return -1

    if not paths.intraday_db.exists():
        print(f"[Error] Mubasher intraday DB not found: {paths.intraday_db}")
        return -1

    excluded = get_all_exclusions()
    symbols = list_intraday_symbols(paths)
    eligible_symbols = [
        ticker
        for ticker in symbols
        if is_supported_ticker(ticker) and ticker not in excluded
    ]
    source_latest_bars = get_intraday_latest_bars(paths)
    source_last_minutes = {
        ticker: int(bar["tmin"])
        for ticker, bar in source_latest_bars.items()
        if bar.get("tmin") is not None
    }
    store_latest_bars = _latest_bars_by_ticker(
        intraday_store.get_latest_bars(eligible_symbols, realm="EGX")
    )
    store_latest_minutes: dict[str, int] = {}
    for ticker, bar in store_latest_bars.items():
        minute = local_naive_to_epoch_minute(bar.get("timestamp"))
        if minute is not None:
            store_latest_minutes[ticker] = minute

    realtime_overlay_enabled = _source_archive_lags_live_day(source_last_minutes)
    print(f"[Info] Found {len(symbols)} intraday symbols in Mubasher DB.")

    updated = 0
    skipped_unchanged = 0
    rows_loaded = 0
    live_symbols: list[str] = []
    for ticker in eligible_symbols:
        live_symbols.append(ticker)
        try:
            source_max_tmin = source_last_minutes.get(ticker)
            if source_max_tmin is None:
                continue

            local_max_tmin = store_latest_minutes.get(ticker)
            from_store = local_max_tmin is not None
            if local_max_tmin is None:
                local_max_tmin = _get_last_parquet_minute(ticker)
            if local_max_tmin is not None and local_max_tmin > source_max_tmin:
                if realtime_overlay_enabled and _source_minute_before_today(source_max_tmin):
                    skipped_unchanged += 1
                    continue
                # Local cache is ahead of Mubasher DB (typically from coarse CSV).
                # Rebuild this ticker from DB to restore source-of-truth precision.
                full_df = load_intraday_dataframe(paths, ticker, min_tmin=None)
                if full_df.empty:
                    continue
                rows_loaded += len(full_df)
                intraday_store.replace_intraday(ticker, full_df, realm="EGX")
                if getattr(settings, "INTRADAY_PARQUET_MIRROR", False):
                    parquet_writer.save_stream(ticker, full_df, folder="intraday")
                updated += 1
                continue

            if local_max_tmin is not None and local_max_tmin == source_max_tmin:
                refreshed_same_minute = False
                refresh_equal_minute = bool(getattr(settings, "INTRADAY_REFRESH_EQUAL_MINUTE", True))

                # Some feeds revise OHLCV inside the same minute (same TMIN).
                # Compare cached latest bars and upsert only when the latest bar actually changed.
                if refresh_equal_minute and from_store:
                    source_latest = source_latest_bars.get(ticker)
                    store_latest = store_latest_bars.get(ticker)
                    if _latest_bar_needs_refresh(store_latest, source_latest):
                        refresh_df = _latest_bar_frame(source_latest)
                        intraday_store.upsert_intraday(ticker, refresh_df, realm="EGX", accumulate_volume=False)
                        if getattr(settings, "INTRADAY_PARQUET_MIRROR", False):
                            parquet_writer.save_stream(ticker, refresh_df, folder="intraday")
                        rows_loaded += len(refresh_df)
                        updated += 1
                        refreshed_same_minute = True

                if refreshed_same_minute:
                    continue

                if (
                    not from_store
                    and getattr(settings, "INTRADAY_STORE_BOOTSTRAP_MISSING", True)
                ):
                    parquet_file = _intraday_file_path(ticker, realm="EGX")
                    if parquet_file.exists():
                        try:
                            seed_df = pd.read_parquet(parquet_file)
                            if seed_df is not None and not seed_df.empty:
                                intraday_store.upsert_intraday(ticker, seed_df, realm="EGX")
                        except Exception:
                            pass
                skipped_unchanged += 1
                continue

            df = load_intraday_dataframe(paths, ticker, min_tmin=local_max_tmin)
            if df.empty:
                continue
            rows_loaded += len(df)
            intraday_store.upsert_intraday(ticker, df, realm="EGX")
            if getattr(settings, "INTRADAY_PARQUET_MIRROR", False):
                parquet_writer.save_stream(ticker, df, folder="intraday")
            updated += 1
        except Exception as e:
            print(f"[Error] Failed to ingest {ticker} from Mubasher DB: {e}")

    print(
        f"[Info] Mubasher intraday delta ingest: updated={updated}, "
        f"rows_loaded={rows_loaded}, skipped_unchanged={skipped_unchanged}"
    )
    if realtime_overlay_enabled:
        live_updated, live_rows = _ingest_mubasher_realtime_overlay(live_symbols)
        updated += live_updated
        rows_loaded += live_rows
    return updated


def _ingest_intraday_from_directfn() -> int:
    layout = detect_directfn_layout(
        Path(settings.METASTOCK_HISTORY_FOLDER),
        Path(settings.METASTOCK_INTRADAY_FOLDER),
    )
    if layout is None:
        print(f"[Error] DirectFN intraday layout not found for path: {settings.METASTOCK_INTRADAY_FOLDER}")
        return -1

    symbol_map = load_directfn_symbol_map(layout.symbol_map)
    if not symbol_map:
        print("[Error] DirectFN symbolmapping.csv missing or unreadable.")
        return -1

    tradable_whitelist: set[str] | None = None
    try:
        paths = build_paths(
            Path(settings.MUBASHER_ROOT_DIR),
            user_id=(settings.MUBASHER_USER_ID or None),
        )
        if paths.intraday_db.exists():
            tradable_whitelist = set(list_intraday_symbols(paths))
            if tradable_whitelist:
                print(f"[Info] DirectFN intraday restricted to Mubasher tradable universe ({len(tradable_whitelist)} symbols).")
    except Exception:
        tradable_whitelist = None

    lookback_days = int(getattr(settings, "DIRECTFN_INTRADAY_LOOKBACK_DAYS", 5))
    excluded = get_all_exclusions()
    grouped: dict[str, list[pd.DataFrame]] = {}

    for ticker, path in directfn_iter_intraday_files(layout, symbol_map, lookback_days=lookback_days):
        if tradable_whitelist is not None and ticker not in tradable_whitelist:
            continue
        if not is_supported_ticker(ticker) or ticker in excluded:
            continue
        try:
            df = directfn_read_intraday_file(path)
            if df is not None and not df.empty:
                grouped.setdefault(ticker, []).append(df)
        except Exception as e:
            print(f"[Error] Failed to read DirectFN intraday file {path}: {e}")

    updated = 0
    rows_loaded = 0
    skipped = 0

    for ticker, frames in grouped.items():
        try:
            combined = pd.concat(frames, ignore_index=True)
            combined = combined.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
            if combined.empty:
                continue

            combined["tmin"] = combined["timestamp"].apply(local_naive_to_epoch_minute)
            combined = combined.dropna(subset=["tmin"])
            combined["tmin"] = combined["tmin"].astype(int)

            last_minute, _ = _get_last_ingested_minute(ticker)
            if last_minute is not None:
                combined = combined[combined["tmin"] > last_minute]
            if combined.empty:
                skipped += 1
                continue

            df_out = combined.drop(columns=["tmin"])
            intraday_store.upsert_intraday(ticker, df_out, realm="EGX")
            if getattr(settings, "INTRADAY_PARQUET_MIRROR", False):
                parquet_writer.save_stream(ticker, df_out, folder="intraday")
            rows_loaded += len(df_out)
            updated += 1
        except Exception as e:
            print(f"[Error] Failed to ingest DirectFN intraday {ticker}: {e}")

    print(f"[Info] DirectFN intraday ingest: updated={updated}, rows_loaded={rows_loaded}, skipped={skipped}")
    return updated


def _ingest_intraday_from_metastock_dat() -> int:
    history_dir = Path(getattr(settings, "METASTOCK_DAT_HISTORY_FOLDER", ""))
    intraday_dir = Path(getattr(settings, "METASTOCK_DAT_INTRADAY_FOLDER", ""))

    layout = None
    symbol_map = {}
    for attempt in range(3):
        layout = detect_metastock_dat_layout(history_dir, intraday_dir)
        if layout is not None:
            symbol_map = load_metastock_dat_symbol_map(layout)
            if symbol_map:
                break
        if attempt < 2:
            time.sleep(0.4)

    if layout is None:
        print(f"[Error] MetaStock DAT intraday layout not found: history={history_dir} intraday={intraday_dir}")
        return -1
    if not symbol_map:
        print("[Error] MetaStock DAT symbol map unavailable after retries.")
        return -1

    tradable_whitelist: set[str] | None = None
    try:
        paths = build_paths(
            Path(settings.MUBASHER_ROOT_DIR),
            user_id=(settings.MUBASHER_USER_ID or None),
        )
        if paths.intraday_db.exists():
            tradable_whitelist = set(list_intraday_symbols(paths))
            if tradable_whitelist:
                print(
                    "[Info] MetaStock DAT intraday restricted to Mubasher tradable universe "
                    f"({len(tradable_whitelist)} symbols)."
                )
    except Exception:
        tradable_whitelist = None

    lookback_days = int(getattr(settings, "METASTOCK_DAT_INTRADAY_LOOKBACK_DAYS", 5))
    excluded = get_all_exclusions()
    grouped: dict[str, list[pd.DataFrame]] = {}

    for ticker, path in metastock_dat_iter_intraday_files(layout, symbol_map, lookback_days=lookback_days):
        if tradable_whitelist is not None and ticker not in tradable_whitelist:
            continue
        if not is_supported_ticker(ticker) or ticker in excluded:
            continue
        try:
            df = metastock_dat_read_intraday_file(path)
            if df is not None and not df.empty:
                grouped.setdefault(ticker, []).append(df)
        except Exception as e:
            print(f"[Error] Failed to read MetaStock DAT intraday file {path}: {e}")

    updated = 0
    rows_loaded = 0
    skipped = 0

    for ticker, frames in grouped.items():
        try:
            combined = pd.concat(frames, ignore_index=True)
            combined = combined.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
            if combined.empty:
                continue

            combined["tmin"] = combined["timestamp"].apply(local_naive_to_epoch_minute)
            combined = combined.dropna(subset=["tmin"])
            combined["tmin"] = combined["tmin"].astype(int)

            last_minute, _ = _get_last_ingested_minute(ticker)
            if last_minute is not None:
                combined = combined[combined["tmin"] > last_minute]
            if combined.empty:
                skipped += 1
                continue

            df_out = combined.drop(columns=["tmin"])
            intraday_store.upsert_intraday(ticker, df_out, realm="EGX")
            if getattr(settings, "INTRADAY_PARQUET_MIRROR", False):
                parquet_writer.save_stream(ticker, df_out, folder="intraday")
            rows_loaded += len(df_out)
            updated += 1
        except Exception as e:
            print(f"[Error] Failed to ingest MetaStock DAT intraday {ticker}: {e}")

    print(f"[Info] MetaStock DAT intraday ingest: updated={updated}, rows_loaded={rows_loaded}, skipped={skipped}")
    return updated


def ingest_intraday(provider: str | None = None) -> int:
    """
    Ingest intraday bars into the Parquet Data Lake.
    Provider options: CSV | MUBASHER_DB | DIRECTFN | METASTOCK_DAT | AUTO.
    """
    with _ingestion_lock() as acquired:
        if not acquired:
            # Another process is already ingesting. 
            # We return -2 to signal 'already running' or similar if needed, 
            # but usually 0 or -1 is fine.
            _set_last_ingest_intraday_summary(
                requested_provider=provider or "AUTO",
                used_provider=None,
                fallback_from=None,
                failure_mode="already_running",
                updated=0,
                status="skipped_locked",
            )
            return 0

        requested_provider = provider or "AUTO"
        selected_provider, _ = resolve_timeframe_provider(timeframe="intraday", provider=provider)

        if selected_provider == "MUBASHER_DB":
            updated = _ingest_intraday_from_mubasher_db()
            if updated >= 0:
                _set_last_ingest_intraday_summary(
                    requested_provider=requested_provider,
                    used_provider=selected_provider,
                    fallback_from=None,
                    failure_mode=None,
                    updated=updated,
                    status="completed",
                )
                return updated
            print("[Warn] Mubasher DB intraday source unavailable. Falling back to CSV.")
        if selected_provider == "DIRECTFN":
            updated = _ingest_intraday_from_directfn()
            if updated >= 0:
                _set_last_ingest_intraday_summary(
                    requested_provider=requested_provider,
                    used_provider=selected_provider,
                    fallback_from=None,
                    failure_mode=None,
                    updated=updated,
                    status="completed",
                )
                return updated
            print("[Warn] DirectFN intraday source unavailable. Falling back to CSV.")
        if selected_provider == "METASTOCK_DAT":
            updated = _ingest_intraday_from_metastock_dat()
            if updated >= 0:
                _set_last_ingest_intraday_summary(
                    requested_provider=requested_provider,
                    used_provider=selected_provider,
                    fallback_from=None,
                    failure_mode=None,
                    updated=updated,
                    status="completed",
                )
                return updated
            print("[Warn] MetaStock DAT intraday source unavailable. Falling back to CSV.")

        updated = _ingest_intraday_from_csv()
        if selected_provider != "CSV":
            emit_event(
                "pipeline.ingest_intraday.provider_fallback",
                level="warning",
                requested_provider=requested_provider,
                selected_provider=selected_provider,
                fallback_provider="CSV",
                failure_mode="source_unavailable",
                updated=updated,
            )
            _set_last_ingest_intraday_summary(
                requested_provider=requested_provider,
                used_provider="CSV",
                fallback_from=selected_provider,
                failure_mode="source_unavailable",
                updated=updated,
                status="completed_with_fallback",
            )
            return updated

        _set_last_ingest_intraday_summary(
            requested_provider=requested_provider,
            used_provider="CSV",
            fallback_from=None,
            failure_mode=None,
            updated=updated,
            status="completed",
        )
        return updated


if __name__ == "__main__":
    ingest_intraday()
