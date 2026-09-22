from data_engine.ingest_history import ingest_history, get_last_ingest_history_summary
from data_engine.ingest_intraday import ingest_intraday, get_last_ingest_intraday_summary
from data_engine.ingest_ticks import ingest_ticks
from data_engine.compaction import compact_folder
from data_engine.freshness import evaluate_freshness, invalidate_freshness_cache
from data_engine.provider_selection import (
    format_quality_report,
    resolve_timeframe_provider,
    resolved_provider_context,
    stage_provider_context,
)
from data_engine.observability import (
    counter_value,
    emit_event,
    incr_counter,
    maybe_emit_freshness_alerts,
    set_gauge,
    snapshot_metrics,
)
from data_engine.run_metadata import finish_run, start_run
import os
import time
import concurrent.futures

from core import TimeUtils
from core.settings import settings

def _stream_watermark(realm: str, stream: str) -> str | None:
    try:
        if stream in {"history", "intraday"}:
            freshness = evaluate_freshness(realm=realm, run_date=TimeUtils.today(), scan_type="DAILY")
            if stream == "history":
                return (freshness.get("history") or {}).get("last_updated")
            return (freshness.get("intraday") or {}).get("last_bar")
        if stream == "ticks":
            from pathlib import Path
            from core.settings import settings
            p = Path(settings.DATA_ROOT) / realm / "ticks"
            if not p.exists():
                return None
            days = sorted([d.name for d in p.iterdir() if d.is_dir()])
            return days[-1] if days else None
    except Exception:
        return None
    return None


def _sync_intraday(realm: str, intraday_provider: str, provider_context: dict | None = None) -> None:
    print("\n[1/3] Syncing Intraday (1min)...")
    intraday_run_id = start_run(
        stage="ingest_intraday",
        stream="intraday",
        realm=realm,
        provider=intraday_provider,
        watermark_before=_stream_watermark(realm, "intraday"),
        provider_context=provider_context,
    )
    before_valid = counter_value("dq.valid_rows.intraday_store")
    before_rejected = counter_value("dq.rejected_rows.intraday_store")
    try:
        updated_intraday = ingest_intraday(provider=intraday_provider)
        ingest_summary = get_last_ingest_intraday_summary()
        stage_context = stage_provider_context(provider_context, ingest_summary)
        finish_run(
            intraday_run_id,
            realm=realm,
            status="COMPLETED",
            rows_read=None,
            rows_written=int(max(0, counter_value("dq.valid_rows.intraday_store") - before_valid)),
            rows_rejected=int(max(0, counter_value("dq.rejected_rows.intraday_store") - before_rejected)),
            watermark_after=_stream_watermark(realm, "intraday"),
            provider_context=stage_context,
        )
        incr_counter("pipeline.stage.success.intraday")
        set_gauge("pipeline.stage.updated_symbols.intraday", float(updated_intraday if updated_intraday is not None else 0))
        emit_event(
            "pipeline.stage.complete",
            stage="intraday",
            provider=intraday_provider,
            provider_context=stage_context,
            ingest_summary=ingest_summary,
            updated_symbols=updated_intraday,
        )
    except Exception as e:
        ingest_summary = get_last_ingest_intraday_summary()
        stage_context = stage_provider_context(provider_context, ingest_summary)
        finish_run(
            intraday_run_id,
            realm=realm,
            status="ERROR",
            rows_rejected=int(max(0, counter_value("dq.rejected_rows.intraday_store") - before_rejected)),
            watermark_after=_stream_watermark(realm, "intraday"),
            error=str(e),
            provider_context=stage_context,
        )
        incr_counter("pipeline.stage.error.intraday")
        emit_event(
            "pipeline.stage.error",
            level="error",
            stage="intraday",
            provider=intraday_provider,
            provider_context=stage_context,
            ingest_summary=ingest_summary,
            error=str(e),
        )
        raise

def _sync_history(
    realm: str,
    history_provider: str,
    force_history_recent_days: int,
    provider_context: dict | None = None,
) -> None:
    print("\n[2/3] Syncing History (Daily)...")
    if force_history_recent_days > 0:
        print(f"[2/3] Forcing recent history refresh window: {force_history_recent_days} day(s)")
    history_run_id = start_run(
        stage="ingest_history",
        stream="history",
        realm=realm,
        provider=history_provider,
        watermark_before=_stream_watermark(realm, "history"),
        provider_context=provider_context,
    )
    before_valid = counter_value("dq.valid_rows.history")
    before_rejected = counter_value("dq.rejected_rows.history")
    try:
        updated = ingest_history(provider=history_provider, force_recent_days=force_history_recent_days)
        ingest_summary = get_last_ingest_history_summary()
        stage_context = stage_provider_context(provider_context, ingest_summary)
        finish_run(
            history_run_id,
            realm=realm,
            status="COMPLETED",
            rows_read=None,
            rows_written=int(max(0, counter_value("dq.valid_rows.history") - before_valid)),
            rows_rejected=int(max(0, counter_value("dq.rejected_rows.history") - before_rejected)),
            watermark_after=_stream_watermark(realm, "history"),
            provider_context=stage_context,
        )
        emit_event(
            "pipeline.stage.complete",
            stage="history",
            provider=history_provider,
            provider_context=stage_context,
            ingest_summary=ingest_summary,
            updated_symbols=updated,
        )
    except Exception as e:
        ingest_summary = get_last_ingest_history_summary()
        stage_context = stage_provider_context(provider_context, ingest_summary)
        finish_run(
            history_run_id,
            realm=realm,
            status="ERROR",
            rows_rejected=int(max(0, counter_value("dq.rejected_rows.history") - before_rejected)),
            watermark_after=_stream_watermark(realm, "history"),
            error=str(e),
            provider_context=stage_context,
        )
        emit_event(
            "pipeline.stage.error",
            level="error",
            stage="history",
            provider=history_provider,
            provider_context=stage_context,
            ingest_summary=ingest_summary,
            error=str(e),
        )
        raise
    if updated == 0:
        print("[2/3] History already up-to-date. Skipping.")

def _sync_ticks(realm: str, ticks_provider: str, provider_context: dict | None = None) -> None:
    if not getattr(settings, "TICK_SYNC_ENABLED", True):
        print("\n[3/3] Tick sync disabled by TICK_SYNC_ENABLED=0.")
        return
    if not settings.is_market_open():
        print("\n[3/3] Market is CLOSED. Skipping Tick Sync.")
        return

    print("\n[3/3] Syncing Ticks (Trade-by-Trade)...")
    ticks_run_id = start_run(
        stage="ingest_ticks",
        stream="ticks",
        realm=realm,
        provider=ticks_provider,
        watermark_before=_stream_watermark(realm, "ticks"),
        provider_context=provider_context,
    )
    try:
        tick_stats = ingest_ticks()
        finish_run(
            ticks_run_id,
            realm=realm,
            status="COMPLETED" if tick_stats.get("status") == "ok" else "WARNING",
            rows_read=None,
            rows_written=int(tick_stats.get("rows_added", 0)),
            rows_rejected=0,
            watermark_after=tick_stats.get("trade_date") or _stream_watermark(realm, "ticks"),
            error=tick_stats.get("message"),
        )
    except Exception as e:
        finish_run(
            ticks_run_id,
            realm=realm,
            status="ERROR",
            rows_rejected=0,
            watermark_after=_stream_watermark(realm, "ticks"),
            error=str(e),
        )
        emit_event(
            "pipeline.stage.error",
            level="error",
            stage="ticks",
            provider=ticks_provider,
            provider_context=provider_context,
            error=str(e),
        )
        raise
    print(
        f"[3/3] Tick sync: status={tick_stats.get('status')} "
        f"date={tick_stats.get('trade_date')} symbols={tick_stats.get('symbols_touched', 0)} "
        f"rows_added={tick_stats.get('rows_added', 0)}"
    )

def sync_all(force_history_recent_days: int = -1):
    realm = "EGX"
    print("--- Starting Data Lake Synchronization ---")
    start = time.time()

    intraday_provider, intraday_report = resolve_timeframe_provider(
        timeframe="intraday",
    )
    history_provider, history_report = resolve_timeframe_provider(
        timeframe="history",
    )
    selection_report = intraday_report or history_report
    intraday_context = resolved_provider_context(
        timeframe="intraday",
        selected_provider=intraday_provider,
        selection_report=selection_report,
    )
    history_context = resolved_provider_context(
        timeframe="history",
        selected_provider=history_provider,
        selection_report=selection_report,
    )
    ticks_provider = str(getattr(settings, "LOCAL_TICKS_PROVIDER", "MUBASHER_DB"))
    ticks_context = resolved_provider_context(
        timeframe="ticks",
        selected_provider=ticks_provider,
        selection_report=None,
    )
    emit_event(
        "pipeline.sync.start",
        realm=realm,
        intraday_provider=intraday_provider,
        intraday_provider_context=intraday_context,
        history_provider=history_provider,
        history_provider_context=history_context,
        ticks_provider=ticks_provider,
        ticks_provider_context=ticks_context,
    )

    if selection_report is not None:
        print(format_quality_report(selection_report))
        print(f"[LocalFeed] Selected intraday provider: {intraday_provider}")
        print(f"[LocalFeed] Selected history provider:  {history_provider}")
    else:
        print(f"[LocalFeed] Provider policy intraday={intraday_provider}, history={history_provider}")
    
    if force_history_recent_days is None:
        force_history_recent_days = -1
    force_history_recent_days = int(force_history_recent_days)

    print(f"\n[Parallel] Dispatching Intraday, History, and Ticks sync stages...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(_sync_intraday, realm, intraday_provider, intraday_context),
            executor.submit(_sync_history, realm, history_provider, force_history_recent_days, history_context),
            executor.submit(_sync_ticks, realm, ticks_provider, ticks_context)
        ]
        concurrent.futures.wait(futures)
        
        for f in futures:
            try:
                f.result()
            except Exception as e:
                print(f"[Pipeline Error] A sync stage failed: {e}")

    # Periodic compaction from partitioned writes to compact symbol files.
    if str(os.getenv("PARQUET_COMPACTION_ENABLED", "1")).strip().lower() in {"1", "true", "yes"}:
        max_tickers = int(os.getenv("PARQUET_COMPACTION_MAX_TICKERS", "500"))
        for folder in ("history", "intraday"):
            stats = compact_folder(realm=realm, folder=folder, max_tickers=max_tickers)
            emit_event("pipeline.compaction.complete", realm=realm, **stats)
            set_gauge(f"pipeline.compaction.compacted.{folder}", float(stats.get("compacted", 0)))

    invalidate_freshness_cache(realm=realm)

    # Freshness/completeness alerts
    freshness = evaluate_freshness(realm=realm, run_date=TimeUtils.today(), scan_type="DAILY")
    alerts = maybe_emit_freshness_alerts(freshness)
    set_gauge("pipeline.fresh_ratio.history", float((((freshness or {}).get("history") or {}).get("kpis") or {}).get("fresh_ratio", 0.0)))
    set_gauge("pipeline.live_ratio.intraday", float((((freshness or {}).get("intraday") or {}).get("kpis") or {}).get("live_ratio", 0.0)))
    if alerts:
        print(f"[Alerts] {alerts}")

    # Invalidate DataManager read cache so consumers see fresh data immediately.
    try:
        from core.DataManager import invalidate_history_cache
        invalidate_history_cache()
    except Exception:
        pass  # DataManager may not be importable in worker-only contexts
    
    elapsed = time.time() - start
    set_gauge("pipeline.sync.duration_sec", float(elapsed))
    duration_sec = round(float(elapsed), 2)
    emit_event(
        "pipeline.sync.complete",
        realm=realm,
        duration_sec=duration_sec,
        metrics=snapshot_metrics(),
    )
    print(f"\n[Done] Synchronization complete in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    sync_all()
