from core.settings import settings
from core.exclusions import get_all_exclusions
import pandas as pd
from pathlib import Path
from contextlib import closing
from datetime import date, timedelta
import time

from core import TimeUtils
from data_engine import parquet_writer
from data_engine import api as data_engine_api
from data_engine.provider_selection import resolve_timeframe_provider
from data_engine.directfn_feed_source import (
    detect_layout as detect_directfn_layout,
    iter_history_files as directfn_iter_history_files,
    load_symbol_map as load_directfn_symbol_map,
    read_history_file as directfn_read_history_file,
)
from data_engine.metastock_dat_source import (
    detect_layout as detect_metastock_dat_layout,
    iter_history_files as metastock_dat_iter_history_files,
    load_symbol_map as load_metastock_dat_symbol_map,
    read_history_file as metastock_dat_read_history_file,
)
from data_engine.mubasher_sqlite_source import (
    build_paths,
    get_history_last_dates,
    list_history_symbols,
    load_history_dataframe,
    open_history_connection,
)
from data_engine.history_watermarks import (
    cached_flat_date,
    load_index as load_history_watermark_index,
    save_index as save_history_watermark_index,
    update_flat_date as update_history_flat_date,
)
from data_engine.observability import emit_event
from data_engine.ticker_filters import is_supported_ticker

try:
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover
    pq = None


_LAST_INGEST_HISTORY_SUMMARY: dict[str, object] = {}


def _set_last_ingest_history_summary(**summary) -> None:
    _LAST_INGEST_HISTORY_SUMMARY.clear()
    _LAST_INGEST_HISTORY_SUMMARY.update(summary)


def get_last_ingest_history_summary() -> dict[str, object]:
    return dict(_LAST_INGEST_HISTORY_SUMMARY)


def _auto_force_recent_days() -> int:
    """
    Auto rule:
    - Before 14:30 -> strict date-delta mode.
    - At/after 14:30 -> refresh at least same-day bars to capture late corrections.
    """
    now = TimeUtils.now()
    if (now.hour, now.minute) >= (14, 30):
        return 1
    return 0


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


def _read_csv_last_date(file_path: Path):
    try:
        if not file_path.exists() or file_path.stat().st_size == 0:
            return None
        with file_path.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            block = b""
            pos = size
            while pos > 0 and block.count(b"\n") < 20:
                step = min(4096, pos)
                pos -= step
                fh.seek(pos)
                block = fh.read(step) + block
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        for raw in reversed(lines):
            line = raw.decode("utf-8", errors="ignore")
            if not line:
                continue
            if line.lstrip().startswith("<"):
                continue
            parts = [p.strip().replace('"', "") for p in line.split(",")]
            if not parts:
                continue
            date_text = parts[0]
            if len(date_text) == 8 and date_text.isdigit():
                parsed = pd.to_datetime(date_text, format="%Y%m%d", errors="coerce")
                if not pd.isna(parsed):
                    return parsed.date()
            return None
    except Exception:
        return None
    return None


def _get_last_parquet_date(ticker: str):
    from data_engine.api import DATA_ROOT
    try:
        ticker = str(ticker).upper().strip()
        flat_path = DATA_ROOT / "EGX" / "history" / f"{ticker}.parquet"
        max_ts = _read_parquet_max_timestamp(flat_path) if flat_path.exists() else None
        partition_root = DATA_ROOT / "EGX" / "history" / "by_date"
        if partition_root.exists():
            try:
                day_dirs = sorted(
                    [d for d in partition_root.iterdir() if d.is_dir()],
                    key=lambda p: p.name,
                    reverse=True,
                )
                for day_dir in day_dirs:
                    partition_file = day_dir / f"{ticker}.parquet"
                    if not partition_file.exists():
                        continue
                    partition_ts = _read_parquet_max_timestamp(partition_file)
                    if partition_ts is None:
                        partition_ts = pd.to_datetime(day_dir.name, errors="coerce")
                    if partition_ts is not None and not pd.isna(partition_ts):
                        if max_ts is None or partition_ts > max_ts:
                            max_ts = partition_ts
                        break
            except Exception:
                pass
        if max_ts is not None:
            return pd.to_datetime(max_ts).date()
        return None
    except Exception:
        return None


def _timestamp_to_date(value) -> date | None:
    if value is None:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return ts.date()


def _get_last_parquet_dates(tickers: list[str], realm: str = "EGX") -> dict[str, date]:
    from data_engine.api import DATA_ROOT

    target = {str(ticker).upper().strip() for ticker in tickers if str(ticker).strip()}
    if not target:
        return {}

    history_dir = DATA_ROOT / realm / "history"
    if not history_dir.exists():
        return {}

    out: dict[str, date] = {}
    watermark_index = load_history_watermark_index(history_dir)
    watermark_dirty = False
    try:
        for flat_path in history_dir.glob("*.parquet"):
            ticker = flat_path.stem.upper()
            if ticker not in target:
                continue
            last_date = cached_flat_date(watermark_index, ticker, flat_path)
            if last_date is None:
                last_date = _timestamp_to_date(_read_parquet_max_timestamp(flat_path))
                if last_date is not None:
                    watermark_dirty = (
                        update_history_flat_date(watermark_index, ticker, flat_path, last_date)
                        or watermark_dirty
                    )
            if last_date is not None:
                out[ticker] = last_date
    except Exception:
        pass
    finally:
        if watermark_dirty:
            try:
                save_history_watermark_index(history_dir, watermark_index)
            except Exception:
                pass

    partition_root = history_dir / "by_date"
    if not partition_root.exists():
        return out

    try:
        day_dirs: list[tuple[date, Path]] = []
        for day_dir in partition_root.iterdir():
            if not day_dir.is_dir():
                continue
            partition_date = _timestamp_to_date(day_dir.name)
            if partition_date is None:
                continue
            day_dirs.append((partition_date, day_dir))
        day_dirs.sort(key=lambda item: item[0], reverse=True)

        remaining = set(target)
        for partition_date, day_dir in day_dirs:
            if not remaining:
                break
            for partition_file in day_dir.glob("*.parquet"):
                ticker = partition_file.stem.upper()
                if ticker not in remaining:
                    continue
                last_date = partition_date
                current = out.get(ticker)
                if current is None or last_date > current:
                    out[ticker] = last_date
                remaining.remove(ticker)
    except Exception:
        pass

    return out


def _ingest_history_from_csv(force_recent_days: int = 0) -> int:
    history_path = Path(settings.METASTOCK_HISTORY_FOLDER)
    if not history_path.exists():
        print(f"[Error] History path not found: {history_path}")
        return 0

    csv_files = list(history_path.glob("*.csv"))
    print(f"[Info] Found {len(csv_files)} history CSV files to ingest.")

    updated = 0
    missing = 0
    failed = 0
    excluded = get_all_exclusions()

    for file_path in csv_files:
        try:
            ticker = file_path.stem.upper()
            if not is_supported_ticker(ticker):
                continue
            if ticker in excluded:
                continue

            parquet_last_date = _get_last_parquet_date(ticker)
            csv_last_date = _read_csv_last_date(file_path)
            if (
                force_recent_days <= 0
                and parquet_last_date is not None
                and csv_last_date is not None
                and parquet_last_date >= csv_last_date
            ):
                continue

            df = pd.read_csv(file_path, usecols=lambda c: c in {"<DATE>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<VOL>"})
            df.rename(
                columns={
                    "<DATE>": "timestamp",
                    "<OPEN>": "open",
                    "<HIGH>": "high",
                    "<LOW>": "low",
                    "<CLOSE>": "close",
                    "<VOL>": "volume",
                },
                inplace=True,
            )

            if "timestamp" not in df.columns:
                continue

            df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%d", errors="coerce")
            df = df.dropna(subset=["timestamp"])
            if df.empty:
                continue

            if parquet_last_date is not None:
                if force_recent_days > 0:
                    floor_date = parquet_last_date - timedelta(days=int(force_recent_days))
                    # Re-read a small recent window to capture same-day corrections.
                    df = df[df["timestamp"].dt.date >= floor_date]
                else:
                    df = df[df["timestamp"].dt.date > parquet_last_date]
                if df.empty:
                    continue

            parquet_writer.save_stream(ticker, df, folder="history")
            updated += 1
        except FileNotFoundError as e:
            missing += 1
            print(f"[Warn] Skipped missing history CSV {file_path.name}: {e}")
        except Exception as e:
            failed += 1
            print(f"[Error] Failed to ingest {file_path.name}: {e}")

    if missing or failed:
        print(f"[Info] history CSV ingest completed: updated={updated} missing={missing} failed={failed}")

    return updated


def _ingest_history_from_mubasher_db(force_recent_days: int = 0) -> int:
    try:
        paths = build_paths(
            Path(settings.MUBASHER_ROOT_DIR),
            user_id=(settings.MUBASHER_USER_ID or None),
        )
    except Exception as e:
        print(f"[Error] Mubasher DB source not available: {e}")
        return -1

    if not paths.history_db.exists():
        print(f"[Error] Mubasher history DB not found: {paths.history_db}")
        return -1

    excluded = get_all_exclusions()
    symbols = list_history_symbols(paths)
    eligible_symbols = [
        ticker
        for ticker in symbols
        if is_supported_ticker(ticker) and ticker not in excluded
    ]
    local_last_dates = _get_last_parquet_dates(eligible_symbols, realm="EGX")
    print(f"[Info] Found {len(symbols)} history symbols in Mubasher DB.")

    updated = 0
    rows_loaded = 0
    skipped_unchanged = 0
    with closing(open_history_connection(paths)) as history_conn:
        source_last_dates = get_history_last_dates(paths, conn=history_conn)
        for ticker in eligible_symbols:
            try:
                parquet_last_date = local_last_dates.get(ticker)
                parquet_last_text = parquet_last_date.strftime("%Y%m%d") if parquet_last_date is not None else None
                source_last_text = source_last_dates.get(ticker)
                if (
                    force_recent_days <= 0
                    and source_last_text
                    and parquet_last_text
                    and parquet_last_text >= source_last_text
                ):
                    skipped_unchanged += 1
                    continue

                min_date = parquet_last_date
                if force_recent_days > 0 and parquet_last_date is not None:
                    min_date = parquet_last_date - timedelta(days=int(force_recent_days))

                df = load_history_dataframe(paths, ticker, min_date=min_date, conn=history_conn)
                if df.empty:
                    continue

                rows_loaded += len(df)
                parquet_writer.save_stream(ticker, df, folder="history")
                updated += 1
            except Exception as e:
                print(f"[Error] Failed to ingest {ticker} from Mubasher DB: {e}")

    print(
        f"[Info] Mubasher history delta ingest: updated={updated}, "
        f"rows_loaded={rows_loaded}, skipped_unchanged={skipped_unchanged}"
    )
    return updated


def _ingest_history_from_directfn(force_recent_days: int = 0) -> int:
    layout = detect_directfn_layout(
        Path(settings.METASTOCK_HISTORY_FOLDER),
        Path(settings.METASTOCK_INTRADAY_FOLDER),
    )
    if layout is None:
        print(f"[Error] DirectFN history layout not found for path: {settings.METASTOCK_HISTORY_FOLDER}")
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
        if paths.history_db.exists():
            tradable_whitelist = set(list_history_symbols(paths))
            if tradable_whitelist:
                print(f"[Info] DirectFN history restricted to Mubasher tradable universe ({len(tradable_whitelist)} symbols).")
    except Exception:
        tradable_whitelist = None

    excluded = get_all_exclusions()
    updated = 0
    rows_loaded = 0
    skipped = 0
    source_floor_date = None
    if force_recent_days > 0:
        # Fast-path for rolling updates: avoid per-symbol parquet lookups and
        # refresh only a small recent source window.
        source_floor_date = TimeUtils.today() - timedelta(days=int(force_recent_days) + 2)

    for ticker, path in directfn_iter_history_files(layout, symbol_map):
        if tradable_whitelist is not None and ticker not in tradable_whitelist:
            continue
        if not is_supported_ticker(ticker) or ticker in excluded:
            continue
        try:
            parquet_last_date = None
            min_date = None
            if source_floor_date is None:
                parquet_last_date = _get_last_parquet_date(ticker)
                min_date = parquet_last_date

            df = directfn_read_history_file(path)
            if df.empty:
                continue

            if source_floor_date is not None:
                df = df[df["timestamp"].dt.date >= source_floor_date]
            elif min_date is not None:
                df = df[df["timestamp"].dt.date > min_date]
            if df.empty:
                skipped += 1
                continue

            parquet_writer.save_stream(ticker, df, folder="history")
            rows_loaded += len(df)
            updated += 1
        except Exception as e:
            print(f"[Error] Failed to ingest DirectFN {ticker}: {e}")

    print(f"[Info] DirectFN history ingest: updated={updated}, rows_loaded={rows_loaded}, skipped={skipped}")
    return updated


def _ingest_history_from_metastock_dat(force_recent_days: int = 0) -> int:
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
        print(f"[Error] MetaStock DAT history layout not found: history={history_dir} intraday={intraday_dir}")
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
        if paths.history_db.exists():
            tradable_whitelist = set(list_history_symbols(paths))
            if tradable_whitelist:
                print(
                    "[Info] MetaStock DAT history restricted to Mubasher tradable universe "
                    f"({len(tradable_whitelist)} symbols)."
                )
    except Exception:
        tradable_whitelist = None

    excluded = get_all_exclusions()
    updated = 0
    rows_loaded = 0
    skipped = 0
    source_floor_date = None
    if force_recent_days > 0:
        source_floor_date = TimeUtils.today() - timedelta(days=int(force_recent_days) + 2)

    for ticker, path in metastock_dat_iter_history_files(layout, symbol_map):
        if tradable_whitelist is not None and ticker not in tradable_whitelist:
            continue
        if not is_supported_ticker(ticker) or ticker in excluded:
            continue
        try:
            parquet_last_date = None
            min_date = None
            if source_floor_date is None:
                parquet_last_date = _get_last_parquet_date(ticker)
                min_date = parquet_last_date

            df = metastock_dat_read_history_file(path)
            if df.empty:
                continue

            if source_floor_date is not None:
                df = df[df["timestamp"].dt.date >= source_floor_date]
            elif min_date is not None:
                df = df[df["timestamp"].dt.date > min_date]
            if df.empty:
                skipped += 1
                continue

            parquet_writer.save_stream(ticker, df, folder="history")
            rows_loaded += len(df)
            updated += 1
        except Exception as e:
            print(f"[Error] Failed to ingest MetaStock DAT {ticker}: {e}")

    print(f"[Info] MetaStock DAT history ingest: updated={updated}, rows_loaded={rows_loaded}, skipped={skipped}")
    return updated


def ingest_history(provider: str | None = None, force_recent_days: int = -1) -> int:
    """
    Ingest daily history into the Parquet Data Lake.
    Provider options: CSV | MUBASHER_DB | DIRECTFN | METASTOCK_DAT | AUTO.
    """
    requested_provider = provider or "AUTO"
    selected_provider, _ = resolve_timeframe_provider(timeframe="history", provider=provider)

    # force_recent_days:
    # -1 => automatic cutoff rule (before/after 14:30)
    #  0 => strict date delta only
    # >0 => force re-read recent window
    if force_recent_days is None:
        force_recent_days = -1
    force_recent_days = int(force_recent_days)
    if force_recent_days < 0:
        force_recent_days = _auto_force_recent_days()
    force_recent_days = max(0, force_recent_days)

    if selected_provider == "MUBASHER_DB":
        updated = _ingest_history_from_mubasher_db(force_recent_days=force_recent_days)
        if updated >= 0:
            _set_last_ingest_history_summary(
                requested_provider=requested_provider,
                used_provider=selected_provider,
                fallback_from=None,
                failure_mode=None,
                updated=updated,
                status="completed",
            )
            return updated
        print("[Warn] Mubasher DB history source unavailable. Falling back to CSV.")
    if selected_provider == "DIRECTFN":
        updated = _ingest_history_from_directfn(force_recent_days=force_recent_days)
        if updated >= 0:
            _set_last_ingest_history_summary(
                requested_provider=requested_provider,
                used_provider=selected_provider,
                fallback_from=None,
                failure_mode=None,
                updated=updated,
                status="completed",
            )
            return updated
        print("[Warn] DirectFN history source unavailable. Falling back to CSV.")
    if selected_provider == "METASTOCK_DAT":
        updated = _ingest_history_from_metastock_dat(force_recent_days=force_recent_days)
        if updated >= 0:
            _set_last_ingest_history_summary(
                requested_provider=requested_provider,
                used_provider=selected_provider,
                fallback_from=None,
                failure_mode=None,
                updated=updated,
                status="completed",
            )
            return updated
        print("[Warn] MetaStock DAT history source unavailable. Falling back to CSV.")

    updated = _ingest_history_from_csv(force_recent_days=force_recent_days)
    if selected_provider != "CSV":
        emit_event(
            "pipeline.ingest_history.provider_fallback",
            level="warning",
            requested_provider=requested_provider,
            selected_provider=selected_provider,
            fallback_provider="CSV",
            failure_mode="source_unavailable",
            updated=updated,
        )
        _set_last_ingest_history_summary(
            requested_provider=requested_provider,
            used_provider="CSV",
            fallback_from=selected_provider,
            failure_mode="source_unavailable",
            updated=updated,
            status="completed_with_fallback",
        )
        return updated

    _set_last_ingest_history_summary(
        requested_provider=requested_provider,
        used_provider="CSV",
        fallback_from=None,
        failure_mode=None,
        updated=updated,
        status="completed",
    )
    return updated


if __name__ == "__main__":
    ingest_history()
