from __future__ import annotations

import datetime
import os
import threading
from typing import Any, Callable, Optional

from core import TimeUtils
from database import db

from .state import (
    BACKFILL_STATE,
    DEFAULT_BACKFILL_SIGNAL_LANES,
    DEFAULT_BACKFILL_UNIVERSE_CHOICE,
    DEFAULT_PROVISIONING_TRADING_DAYS,
    _available_tickers,
    _backfill_lock,
    _get_or_create_provisioning_row,
    _history_window_start_date,
    _normalize_market_signal_payload,
    _persist_provisioning_state,
    _recent_market_days,
    logger,
    normalize_backfill_signal_lanes,
    normalize_backfill_universe_choice,
    resolve_backfill_market_choice,
)
from .intraday import (
    _apply_intraday_entry_prices,
    _intraday_checkpoints_for_day,
    _normalize_simulation_cutoff_for_universe,
    _store_intraday_checkpoint_snapshot,
    _store_signals_for_day,
)


def run_backfill(
    days: int = DEFAULT_PROVISIONING_TRADING_DAYS,
    mode: str = "MANUAL",
    progress_callback: Optional[Callable[[dict], None]] = None,
    universe_choice: str = DEFAULT_BACKFILL_UNIVERSE_CHOICE,
    signal_lanes: str = DEFAULT_BACKFILL_SIGNAL_LANES,
) -> dict[str, Any]:
    """
    Replay DailyScanner analysis for each of the most recent *days* trading sessions.

    This function is blocking. The API endpoint launches it in a background
    thread. Progress is reported via ``BACKFILL_STATE`` and an optional
    ``progress_callback``.
    """
    if not _backfill_lock.acquire(blocking=False):
        return {"status": "ALREADY_RUNNING"}

    target_trading_days = max(1, int(days))
    normalized_mode = str(mode or "MANUAL").strip().upper() or "MANUAL"
    normalized_universe_choice = normalize_backfill_universe_choice(universe_choice)
    normalized_signal_lanes = normalize_backfill_signal_lanes(signal_lanes)
    run_intraday = normalized_signal_lanes in {"INTRADAY", "BOTH"}
    run_swing = normalized_signal_lanes in {"SWING", "BOTH"}
    provisioning_row = _get_or_create_provisioning_row(target_trading_days, normalized_mode)

    try:
        started_at = TimeUtils.now()
        _persist_provisioning_state(
            provisioning_row,
            target_trading_days=target_trading_days,
            completed_trading_days=0,
            status="RUNNING",
            mode=normalized_mode,
            universe_choice=normalized_universe_choice,
            started_at=started_at,
            completed_at=None,
            last_error=None,
        )

        BACKFILL_STATE.update({
            "status": "RUNNING",
            "current_day": None,
            "progress": 0,
            "total_days": 0,
            "signals_found": 0,
            "swing_signals_found": 0,
            "intraday_signals_found": 0,
            "intraday_checkpoint_rows": 0,
            "mode": normalized_mode,
            "target_kind": "TRADING_DAYS",
            "universe_choice": normalized_universe_choice,
            "signal_lanes": normalized_signal_lanes,
            "error": None,
        })

        available_tickers = _available_tickers()
        if not available_tickers:
            warning = "Historical provisioning skipped: no tickers are available in the Data Engine yet."
            BACKFILL_STATE["status"] = "COMPLETED_WITH_WARNINGS"
            BACKFILL_STATE["total_days"] = 0
            BACKFILL_STATE["error"] = warning
            _persist_provisioning_state(
                provisioning_row,
                target_trading_days=target_trading_days,
                completed_trading_days=0,
                status="COMPLETED_WITH_WARNINGS",
                mode=normalized_mode,
                universe_choice=normalized_universe_choice,
                completed_at=TimeUtils.now(),
                last_error=warning,
            )
            logger.info(warning)
            return {
                "status": "COMPLETED_WITH_WARNINGS",
                "total_days": 0,
                "signals_found": 0,
                "swing_signals_found": 0,
                "intraday_signals_found": 0,
                "intraday_checkpoint_rows": 0,
                "target_kind": "TRADING_DAYS",
                "universe_choice": normalized_universe_choice,
                "signal_lanes": normalized_signal_lanes,
                "error": warning,
            }

        end_date = TimeUtils.today()
        earliest_available_date = _history_window_start_date(available_tickers)
        market_days = _recent_market_days(
            end_date,
            target_trading_days,
            earliest_available_date=earliest_available_date,
        )

        total = len(market_days)
        BACKFILL_STATE["total_days"] = total
        logger.info(
            "Backfill starting: %d trading days ending before %s using universe %s",
            total,
            end_date,
            normalized_universe_choice,
        )

        warning_messages: list[str] = []
        if total < target_trading_days:
            warning_messages.append(
                f"Reachable history window is shorter than target: {total} of {target_trading_days} trading days."
            )

        if total == 0:
            final_status = "COMPLETED_WITH_WARNINGS" if warning_messages else "COMPLETED"
            warning_text = " ".join(warning_messages) if warning_messages else None
            BACKFILL_STATE["status"] = final_status
            BACKFILL_STATE["error"] = warning_text
            _persist_provisioning_state(
                provisioning_row,
                target_trading_days=target_trading_days,
                completed_trading_days=0,
                status=final_status,
                mode=normalized_mode,
                universe_choice=normalized_universe_choice,
                completed_at=TimeUtils.now(),
                last_error=warning_text,
            )
            return {
                "status": final_status,
                "total_days": 0,
                "signals_found": 0,
                "swing_signals_found": 0,
                "intraday_signals_found": 0,
                "intraday_checkpoint_rows": 0,
                "target_kind": "TRADING_DAYS",
                "universe_choice": normalized_universe_choice,
                "signal_lanes": normalized_signal_lanes,
                "error": warning_text,
            }

        from core import DailyScanner
        from core.DataManager import DataManager
        from core.market import MarketLists

        total_signals = 0
        total_swing_signals = 0
        total_intraday_signals = 0
        total_intraday_checkpoint_rows = 0
        failed_replay_days = 0
        failed_lane_runs = 0

        db.connect(reuse_if_open=True)

        market_choice = resolve_backfill_market_choice(normalized_universe_choice)
        selected_tickers = list(MarketLists.get_market_list(market_choice))
        if not selected_tickers:
            warning = f"Historical provisioning skipped: resolved backfill universe {normalized_universe_choice} is empty."
            BACKFILL_STATE["status"] = "COMPLETED_WITH_WARNINGS"
            BACKFILL_STATE["total_days"] = 0
            BACKFILL_STATE["error"] = warning
            _persist_provisioning_state(
                provisioning_row,
                target_trading_days=target_trading_days,
                completed_trading_days=0,
                status="COMPLETED_WITH_WARNINGS",
                mode=normalized_mode,
                universe_choice=normalized_universe_choice,
                completed_at=TimeUtils.now(),
                last_error=warning,
            )
            logger.warning(warning)
            return {
                "status": "COMPLETED_WITH_WARNINGS",
                "total_days": 0,
                "signals_found": 0,
                "swing_signals_found": 0,
                "intraday_signals_found": 0,
                "intraday_checkpoint_rows": 0,
                "target_kind": "TRADING_DAYS",
                "universe_choice": normalized_universe_choice,
                "signal_lanes": normalized_signal_lanes,
                "error": warning,
            }

        logger.info(
            "Pre-loading universe history for massive backfill speedup using %s (%d tickers)...",
            normalized_universe_choice,
            len(selected_tickers),
        )

        from core.settings import settings as qs
        lookback = int(getattr(qs, "LOOKBACK", 99))
        required_history = int(target_trading_days) + lookback + 30

        original_limit = os.getenv("UNIVERSE_HISTORY_LIMIT")
        os.environ["UNIVERSE_HISTORY_LIMIT"] = str(required_history)

        try:
            full_universe = DataManager.get_universe_data(selected_tickers, include_live=False)
        finally:
            if original_limit is not None:
                os.environ["UNIVERSE_HISTORY_LIMIT"] = original_limit
            else:
                os.environ.pop("UNIVERSE_HISTORY_LIMIT", None)

        if full_universe is None or full_universe.empty:
            logger.error("H1 Optimization Failed: Could not pre-load universe. Falling back to legacy sequential loading.")
            full_universe = None

        for idx, day in enumerate(market_days):
            BACKFILL_STATE["current_day"] = day.isoformat()
            BACKFILL_STATE["progress"] = idx
            day_had_success = False

            if run_intraday:
                intraday_checkpoints = _intraday_checkpoints_for_day(day)
                intraday_found_total = 0
                intraday_summary_total = {
                    "stored": 0,
                    "inserted": 0,
                    "updated": 0,
                    "unchanged": 0,
                    "invalid": 0,
                    "errors": 0,
                    "error_samples": [],
                }
                intraday_snapshot_total = {
                    "stored": 0,
                    "inserted": 0,
                    "updated": 0,
                    "unchanged": 0,
                    "invalid": 0,
                    "errors": 0,
                }
                intraday_checkpoint_failures = 0

                for intraday_dt in intraday_checkpoints:
                    TimeUtils.set_simulation(intraday_dt)
                    try:
                        intraday_slice = None
                        if full_universe is not None:
                            intraday_cutoff = _normalize_simulation_cutoff_for_universe(full_universe, intraday_dt)
                            intraday_slice = full_universe.loc[full_universe.index.get_level_values(1) <= intraday_cutoff]

                        intraday_signals, _monitored, _breadth, _regime = _normalize_market_signal_payload(
                            DailyScanner.get_market_signals(
                                index_choice=market_choice,
                                is_intraday=True,
                                universe_df=intraday_slice,
                            )
                        )
                        intraday_signals = _apply_intraday_entry_prices(
                            intraday_signals,
                            sim_date=day,
                            cutoff_dt=intraday_dt,
                            universe_df=intraday_slice,
                        )
                        intraday_found_total += len(intraday_signals)
                        intraday_summary = _store_signals_for_day(
                            intraday_signals,
                            day,
                            source="BackfillIntraday",
                            include_diagnostics=True,
                        )
                        intraday_summary_total["stored"] += int(intraday_summary.get("stored", 0))
                        intraday_summary_total["inserted"] += int(intraday_summary.get("inserted", 0))
                        intraday_summary_total["updated"] += int(intraday_summary.get("updated", 0))
                        intraday_summary_total["unchanged"] += int(intraday_summary.get("unchanged", 0))
                        intraday_summary_total["invalid"] += int(intraday_summary.get("invalid_ticker", 0)) + int(
                            intraday_summary.get("invalid_payload", 0)
                        )
                        intraday_summary_total["errors"] += int(intraday_summary.get("errors", 0))
                        samples = intraday_summary.get("error_samples") or []
                        for sample in samples:
                            if len(intraday_summary_total["error_samples"]) >= 3:
                                break
                            intraday_summary_total["error_samples"].append(sample)
                        intraday_snapshot_summary = _store_intraday_checkpoint_snapshot(
                            intraday_signals,
                            session_date=day,
                            checkpoint_at=intraday_dt,
                            source="BackfillIntraday",
                            universe_choice=normalized_universe_choice,
                        )
                        intraday_snapshot_total["stored"] += int(intraday_snapshot_summary.get("stored", 0))
                        intraday_snapshot_total["inserted"] += int(intraday_snapshot_summary.get("inserted", 0))
                        intraday_snapshot_total["updated"] += int(intraday_snapshot_summary.get("updated", 0))
                        intraday_snapshot_total["unchanged"] += int(intraday_snapshot_summary.get("unchanged", 0))
                        intraday_snapshot_total["invalid"] += int(
                            intraday_snapshot_summary.get("invalid_ticker", 0)
                        ) + int(intraday_snapshot_summary.get("invalid_payload", 0))
                        intraday_snapshot_total["errors"] += int(intraday_snapshot_summary.get("errors", 0))
                        day_had_success = True
                    except Exception as exc:
                        intraday_checkpoint_failures += 1
                        logger.warning(
                            "Backfill intraday checkpoint error on %s at %s: %s",
                            day,
                            intraday_dt.strftime("%H:%M"),
                            exc,
                            exc_info=True,
                        )

                intraday_stored = int(intraday_summary_total.get("stored", 0))
                total_intraday_signals += intraday_stored
                total_signals += intraday_stored
                intraday_snapshot_stored = int(intraday_snapshot_total.get("stored", 0))
                total_intraday_checkpoint_rows += intraday_snapshot_stored
                logger.info(
                    "Day %s (%d/%d) [%s] [INTRADAY]: checkpoints=%d found=%d stored=%d inserted=%d updated=%d unchanged=%d invalid=%d errors=%d snapshot_rows=%d snapshot_inserted=%d snapshot_updated=%d snapshot_unchanged=%d snapshot_invalid=%d snapshot_errors=%d",
                    day,
                    idx + 1,
                    total,
                    normalized_universe_choice,
                    len(intraday_checkpoints),
                    intraday_found_total,
                    intraday_stored,
                    int(intraday_summary_total.get("inserted", 0)),
                    int(intraday_summary_total.get("updated", 0)),
                    int(intraday_summary_total.get("unchanged", 0)),
                    int(intraday_summary_total.get("invalid", 0)),
                    int(intraday_summary_total.get("errors", 0)),
                    intraday_snapshot_stored,
                    int(intraday_snapshot_total.get("inserted", 0)),
                    int(intraday_snapshot_total.get("updated", 0)),
                    int(intraday_snapshot_total.get("unchanged", 0)),
                    int(intraday_snapshot_total.get("invalid", 0)),
                    int(intraday_snapshot_total.get("errors", 0)),
                )
                if intraday_summary_total.get("error_samples"):
                    logger.warning(
                        "Backfill intraday diagnostics %s: %s",
                        day,
                        intraday_summary_total.get("error_samples"),
                    )
                if intraday_checkpoint_failures:
                    failed_lane_runs += intraday_checkpoint_failures

            if run_swing:
                swing_dt = datetime.datetime(day.year, day.month, day.day, 14, 30)
                TimeUtils.set_simulation(swing_dt)
                try:
                    day_slice = None
                    if full_universe is not None:
                        swing_cutoff = _normalize_simulation_cutoff_for_universe(full_universe, swing_dt)
                        day_slice = full_universe.loc[full_universe.index.get_level_values(1) <= swing_cutoff]

                    swing_signals, _monitored, _breadth, _regime = _normalize_market_signal_payload(
                        DailyScanner.get_market_signals(
                            index_choice=market_choice,
                            is_intraday=False,
                            universe_df=day_slice,
                        )
                    )
                    swing_summary = _store_signals_for_day(
                        swing_signals,
                        day,
                        source="Backfill",
                        include_diagnostics=True,
                    )
                    swing_stored = int(swing_summary.get("stored", 0))
                    total_swing_signals += swing_stored
                    total_signals += swing_stored
                    day_had_success = True
                    logger.info(
                        "Day %s (%d/%d) [%s] [SWING]: found=%d stored=%d inserted=%d updated=%d unchanged=%d invalid=%d errors=%d",
                        day,
                        idx + 1,
                        total,
                        normalized_universe_choice,
                        len(swing_signals),
                        swing_stored,
                        int(swing_summary.get("inserted", 0)),
                        int(swing_summary.get("updated", 0)),
                        int(swing_summary.get("unchanged", 0)),
                        int(swing_summary.get("invalid_ticker", 0)) + int(swing_summary.get("invalid_payload", 0)),
                        int(swing_summary.get("errors", 0)),
                    )
                    if swing_summary.get("error_samples"):
                        logger.warning(
                            "Backfill swing diagnostics %s: %s",
                            day,
                            swing_summary.get("error_samples"),
                        )
                except Exception as exc:
                    failed_lane_runs += 1
                    logger.warning("Backfill swing lane error on %s: %s", day, exc, exc_info=True)

            if not day_had_success:
                failed_replay_days += 1

            BACKFILL_STATE["signals_found"] = total_signals
            BACKFILL_STATE["swing_signals_found"] = total_swing_signals
            BACKFILL_STATE["intraday_signals_found"] = total_intraday_signals
            BACKFILL_STATE["intraday_checkpoint_rows"] = total_intraday_checkpoint_rows

            if progress_callback:
                progress_callback(dict(BACKFILL_STATE))

            if (idx + 1) % 10 == 0 or (idx + 1) == total:
                _persist_provisioning_state(
                    provisioning_row,
                    target_trading_days=target_trading_days,
                    completed_trading_days=idx + 1,
                    status=str(BACKFILL_STATE.get("status", "RUNNING")),
                    mode=normalized_mode,
                    universe_choice=normalized_universe_choice,
                    last_error=None,
                )

        if failed_replay_days >= total and total > 0:
            warning_text = f"Provisioning failed for all {total} replay day(s)."
            BACKFILL_STATE["progress"] = total
            BACKFILL_STATE["status"] = "ERROR"
            BACKFILL_STATE["error"] = warning_text
            _persist_provisioning_state(
                provisioning_row,
                target_trading_days=target_trading_days,
                completed_trading_days=total,
                status="ERROR",
                mode=normalized_mode,
                universe_choice=normalized_universe_choice,
                completed_at=TimeUtils.now(),
                last_error=warning_text,
            )
            return {
                "status": "ERROR",
                "total_days": total,
                "signals_found": total_signals,
                "swing_signals_found": total_swing_signals,
                "intraday_signals_found": total_intraday_signals,
                "intraday_checkpoint_rows": total_intraday_checkpoint_rows,
                "target_kind": "TRADING_DAYS",
                "universe_choice": normalized_universe_choice,
                "signal_lanes": normalized_signal_lanes,
                "error": warning_text,
            }

        if failed_replay_days:
            warning_messages.append(f"{failed_replay_days} failed replay day(s) were skipped during provisioning.")
        if failed_lane_runs:
            warning_messages.append(f"{failed_lane_runs} lane run(s) failed and were skipped during provisioning.")

        final_status = "COMPLETED_WITH_WARNINGS" if warning_messages else "COMPLETED"
        warning_text = " ".join(warning_messages) if warning_messages else None

        BACKFILL_STATE["progress"] = total
        BACKFILL_STATE["status"] = final_status
        BACKFILL_STATE["error"] = warning_text
        _persist_provisioning_state(
            provisioning_row,
            target_trading_days=target_trading_days,
            completed_trading_days=total,
            status=final_status,
            mode=normalized_mode,
            universe_choice=normalized_universe_choice,
            completed_at=TimeUtils.now(),
            last_error=warning_text,
        )
        logger.info(
            "Backfill complete for %s: %d signals across %d days (intraday checkpoint rows=%d)",
            normalized_universe_choice,
            total_signals,
            total,
            total_intraday_checkpoint_rows,
        )

        return {
            "status": final_status,
            "total_days": total,
            "signals_found": total_signals,
            "swing_signals_found": total_swing_signals,
            "intraday_signals_found": total_intraday_signals,
            "intraday_checkpoint_rows": total_intraday_checkpoint_rows,
            "target_kind": "TRADING_DAYS",
            "universe_choice": normalized_universe_choice,
            "signal_lanes": normalized_signal_lanes,
            "error": warning_text,
        }

    except Exception as exc:
        logger.error("Backfill failed: %s", exc, exc_info=True)
        BACKFILL_STATE["status"] = "ERROR"
        BACKFILL_STATE["error"] = str(exc)
        try:
            _persist_provisioning_state(
                provisioning_row,
                target_trading_days=target_trading_days,
                completed_trading_days=int(BACKFILL_STATE.get("progress", 0) or 0),
                status="ERROR",
                mode=normalized_mode,
                universe_choice=BACKFILL_STATE.get("universe_choice", DEFAULT_BACKFILL_UNIVERSE_CHOICE),
                completed_at=TimeUtils.now(),
                last_error=str(exc),
            )
        except Exception:
            logger.debug("Provisioning state persist failed after backfill error", exc_info=True)
        return {
            "status": "ERROR",
            "universe_choice": BACKFILL_STATE.get("universe_choice", DEFAULT_BACKFILL_UNIVERSE_CHOICE),
            "signal_lanes": BACKFILL_STATE.get("signal_lanes", DEFAULT_BACKFILL_SIGNAL_LANES),
            "intraday_checkpoint_rows": int(BACKFILL_STATE.get("intraday_checkpoint_rows", 0) or 0),
            "error": str(exc),
        }

    finally:
        TimeUtils.clear_simulation()
        _backfill_lock.release()


def start_background_backfill(
    days: int = DEFAULT_PROVISIONING_TRADING_DAYS,
    mode: str = "MANUAL",
    universe_choice: str = DEFAULT_BACKFILL_UNIVERSE_CHOICE,
    signal_lanes: str = DEFAULT_BACKFILL_SIGNAL_LANES,
) -> bool:
    """Launch historical backfill asynchronously in a daemon thread."""
    if _backfill_lock.locked():
        return False

    thread = threading.Thread(
        target=run_backfill,
        kwargs={
            "days": days,
            "mode": mode,
            "universe_choice": universe_choice,
            "signal_lanes": signal_lanes,
        },
        daemon=True,
        name="HistoricalBackfillWorker",
    )
    thread.start()
    return True


def resume_provisioning_if_needed(target_trading_days: int = DEFAULT_PROVISIONING_TRADING_DAYS) -> bool:
    """Check if provisioning was interrupted and resume if appropriate."""
    from database import ProvisioningState
    try:
        row = ProvisioningState.get_or_none(ProvisioningState.name == "HISTORICAL_SIGNAL_PROVISIONING")
        if not row:
            return False
        if str(row.status).upper() in {"RUNNING", "IDLE"}:
            logger.info("Resuming historical provisioning from state: %s", row.status)
            return start_background_backfill(
                days=row.target_trading_days or target_trading_days,
                mode="AUTO_RESUME",
                universe_choice=getattr(row, "backfill_universe_choice", DEFAULT_BACKFILL_UNIVERSE_CHOICE),
            )
    except Exception as exc:
        logger.debug("Failed to check provisioning resume state: %s", exc)
    return False
