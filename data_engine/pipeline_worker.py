from __future__ import annotations
from core.settings import settings

import json
import logging
import os
import random
import threading
import time
from pathlib import Path

from core import TimeUtils
from data_engine.freshness import evaluate_freshness
from data_engine.sync import sync_all


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _state_file_path() -> Path:
    raw = os.getenv("PIPELINE_WORKER_STATE_FILE", "data/pipeline_worker_state.json")
    return Path(raw)


def read_worker_state(path: str | None = None) -> dict:
    target = Path(path) if path else _state_file_path()
    if not target.exists():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}


_WORKER_STATE_LOCK = threading.Lock()
_SYNC_ALL_ACTIVE_LOCK = threading.Lock()
_SYNC_ALL_ACTIVE = None

def _write_worker_state(payload: dict, path: str | None = None) -> None:
    target = Path(path) if path else _state_file_path()
    
    with _WORKER_STATE_LOCK:
        for attempt in range(3):
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                tmp_path = target.with_suffix(target.suffix + ".tmp")
                tmp_path.write_text(json.dumps(payload, separators=(",", ":"), default=str), encoding="utf-8")
                # Using replace is atomic on most OSs but can fail on Windows if target is open
                tmp_path.replace(target)
                return
            except (PermissionError, IOError, OSError) as e:
                if attempt == 2:
                    logging.getLogger("horus.pipeline_worker").error(f"Failed to write worker state after 3 attempts: {e}")
                else:
                    time.sleep(0.1)


def _classify_pipeline_state(freshness: dict, *, min_history_ratio: float, min_intraday_ratio: float) -> tuple[str, dict]:
    history_ratio = float((((freshness or {}).get("history") or {}).get("kpis") or {}).get("fresh_ratio", 0.0))
    intraday_ratio = float((((freshness or {}).get("intraday") or {}).get("kpis") or {}).get("live_ratio", 0.0))
    market_open = bool(settings.is_market_open())
    history_ok = bool(((freshness or {}).get("history") or {}).get("ok", False))
    intraday_signal_ok = bool(((freshness or {}).get("intraday") or {}).get("ok", False))
    intraday_ok = intraday_signal_ok if market_open else True

    if history_ok and intraday_ok:
        state = "FRESH"
    elif history_ok:
        state = "STALE"
    else:
        state = "DEGRADED"

    metrics = {
        "history_fresh_ratio": float(int(float(history_ratio or 0.0) * 10000)) / 10000.0,
        "intraday_live_ratio": float(int(float(intraday_ratio or 0.0) * 10000)) / 10000.0,
        "history_ok": history_ok,
        "intraday_ok": intraday_ok,
        "market_open": market_open,
        "overall_ok": state == "FRESH",
        "checked_at": TimeUtils.now().isoformat(),
    }
    return state, metrics


def worker_retry_reason(worker_state: dict | None) -> str | None:
    if not worker_state:
        return None

    explicit = worker_state.get("retry_reason")
    if explicit:
        return str(explicit)

    if bool(worker_state.get("syncing", False)):
        return "sync_in_progress"

    pipeline_state = str(worker_state.get("pipeline_state", "")).upper()
    next_retry_seconds = int(worker_state.get("next_retry_seconds", 0) or 0)
    if pipeline_state not in {"STALE", "DEGRADED"} or next_retry_seconds <= 0:
        return None

    last_error = str(worker_state.get("last_error") or "")
    if "freshness remains below thresholds" in last_error:
        return "freshness_below_threshold"
    if last_error:
        return "sync_failed"
    return None


def worker_state_is_recovering(worker_state: dict | None) -> bool:
    if not worker_state:
        return False

    if not bool(worker_state.get("running", False)):
        return False

    return worker_retry_reason(worker_state) is not None


def _sync_all_with_timeout(timeout_seconds: int) -> None:
    global _SYNC_ALL_ACTIVE

    if timeout_seconds <= 0:
        sync_all()
        return

    with _SYNC_ALL_ACTIVE_LOCK:
        active = _SYNC_ALL_ACTIVE
        if active is None or bool(active["done"].is_set()):
            active = {
                "done": threading.Event(),
                "error": None,
            }

            def _runner(state=active):
                global _SYNC_ALL_ACTIVE
                try:
                    sync_all()
                except Exception as e:  # pragma: no cover - defensive catch for worker loop resilience
                    state["error"] = e
                finally:
                    state["done"].set()
                    with _SYNC_ALL_ACTIVE_LOCK:
                        if _SYNC_ALL_ACTIVE is state:
                            _SYNC_ALL_ACTIVE = None

            _SYNC_ALL_ACTIVE = active
            threading.Thread(target=_runner, daemon=True).start()

    if not active["done"].wait(timeout_seconds):
        raise TimeoutError(f"sync_all exceeded timeout ({timeout_seconds}s)")
    if active.get("error") is not None:
        raise active["error"]


def _background_sync_paused_for_time_travel() -> bool:
    if TimeUtils.is_simulating():
        return True
    try:
        from core.market.HistoricalBackfill import  is_backfill_running
        return bool(is_backfill_running())
    except Exception:
        return False


class AdaptiveSyncWorker:
    """
    Keeps data pipeline fresh with adaptive retries.
    Designed for internal thread mode and dedicated worker-container mode.
    """

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("horus.sync_worker")
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._closed_session_verified = False

        self.realm = os.getenv("PIPELINE_WORKER_REALM", "EGX")
        self.sync_timeout_sec = _env_int("PIPELINE_WORKER_SYNC_TIMEOUT_SEC", 900)
        self.healthy_interval_sec = _env_int("PIPELINE_WORKER_HEALTHY_INTERVAL_SEC", 300)
        self.base_backoff_sec = _env_int("PIPELINE_WORKER_RETRY_BASE_SEC", 30)
        self.max_backoff_sec = _env_int("PIPELINE_WORKER_RETRY_MAX_SEC", 900)
        self.min_history_ratio = getattr(settings, "FRESHNESS_MIN_HISTORY_RATIO", 0.90)
        self.min_intraday_ratio = getattr(settings, "FRESHNESS_MIN_INTRADAY_RATIO", 0.65)

        self.fail_count = 0
        self.last_success_at: str | None = None
        self.last_failure_at: str | None = None
        self.last_attempt_at: str | None = None
        self.last_error: str | None = None
        self.provider_unreachable = False

    def _is_mubasher_unreachable(self) -> bool:
        provider = str(getattr(settings, "LOCAL_INTRADAY_PROVIDER", "MUBASHER_DB")).strip().upper()
        if provider != "MUBASHER_DB":
            return False
        root_dir = getattr(settings, "MUBASHER_ROOT_DIR", None)
        if not root_dir:
            return False
        from pathlib import Path
        if "PYTEST_CURRENT_TEST" in os.environ:
            if not os.getenv("TEST_MUBASHER_REACHABILITY_CHECK"):
                return False
        try:
            from data_engine.mubasher_sqlite_source import build_paths
            import time
            
            paths = build_paths(
                Path(root_dir),
                user_id=(getattr(settings, "MUBASHER_USER_ID", None) or None),
            )
            db_path = paths.intraday_db
            if not db_path.exists():
                return True
            if settings.is_market_open():
                mtime = db_path.stat().st_mtime
                if time.time() - mtime > 1800:
                    return True
            return False
        except Exception:
            return True

    def start(self) -> None:
        t = self._thread
        if t is not None and t.is_alive():
            return
        self._stop_event.clear()
        t = threading.Thread(target=self._run_loop, daemon=True, name="horus-sync-worker")
        self._thread = t
        t.start()

    def stop(self, timeout_sec: int = 5) -> None:
        self._stop_event.set()
        t = self._thread
        if t is not None and t.is_alive():
            t.join(timeout=timeout_sec)

    def is_running(self) -> bool:
        t = self._thread
        return bool(t is not None and t.is_alive())

    def run_forever(self) -> None:
        """Blocking mode for dedicated worker container/command."""
        self._stop_event.clear()
        try:
            self._run_loop()
        finally:
            self._stop_event.set()

    def _snapshot(
        self,
        *,
        pipeline_state: str,
        freshness: dict,
        next_retry_seconds: int,
        backoff_seconds: int,
        syncing: bool = False,
        retry_reason: str | None = None,
    ) -> dict:
        payload = {
            "enabled": True,
            "running": True,
            "syncing": bool(syncing),
            "pipeline_state": pipeline_state,
            "last_heartbeat_at": TimeUtils.now().isoformat(),
            "last_attempt_at": self.last_attempt_at,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "last_error": self.last_error,
            "fail_count": int(self.fail_count),
            "next_retry_seconds": int(max(0, next_retry_seconds)),
            "backoff_seconds": int(max(0, backoff_seconds)),
            "freshness": freshness,
            "provider_unreachable": bool(self.provider_unreachable),
        }
        if retry_reason:
            payload["retry_reason"] = retry_reason
        else:
            payload["retry_reason"] = worker_retry_reason(payload)
        payload["recovering"] = worker_state_is_recovering(payload)
        return payload

    def _is_closed_session(self) -> bool:
        return not bool(settings.is_market_open())

    def _persist_fresh_state(self, metrics: dict) -> None:
        self.fail_count = 0
        self.last_error = None
        self.last_success_at = TimeUtils.now().isoformat()
        _write_worker_state(
            self._snapshot(
                pipeline_state="FRESH",
                freshness=metrics,
                next_retry_seconds=self.healthy_interval_sec,
                backoff_seconds=0,
            )
        )

    def _persist_closed_session_verified_state(self, *, pipeline_state: str, freshness: dict) -> None:
        self.fail_count = 0
        self.last_error = None
        now_iso = TimeUtils.now().isoformat()
        if str(pipeline_state or "").upper() == "FRESH":
            self.last_success_at = now_iso
            self.last_failure_at = None
        else:
            self.last_success_at = None
            self.last_failure_at = now_iso
        _write_worker_state(
            self._snapshot(
                pipeline_state=pipeline_state,
                freshness=freshness,
                next_retry_seconds=0,
                backoff_seconds=0,
            )
        )

    def _wait_until_market_reopens_or_stop(self, interval_sec: int = 3600) -> None:
        while not self._stop_event.is_set() and self._is_closed_session():
            self._stop_event.wait(interval_sec)

    def _promote_to_live_if_market_open(self, *, started_closed_session: bool) -> bool:
        if not started_closed_session or self._is_closed_session():
            return False
        if str(getattr(settings, "SESSION_MODE", "")).upper() != "ANALYSIS":
            return False

        try:
            from core.session_mode import apply_mode_transition

            apply_mode_transition("LIVE")
        except Exception as exc:  # pragma: no cover - defensive fallback
            settings.SESSION_MODE = "LIVE"
            self.logger.warning(
                "[SyncWorker] Market opened during startup sync. "
                f"Falling back to direct LIVE mode promotion: {exc}"
            )
        return True

    def _run_loop(self) -> None:
        self.logger.info("[SyncWorker] Started.")
        while not self._stop_event.is_set():
            try:
                if _background_sync_paused_for_time_travel():
                    self.logger.info("[SyncWorker] Time travel/backfill active. Pausing background sync.")
                    self._stop_event.wait(max(1, min(self.base_backoff_sec, 30)))
                    continue

                closed_session = self._is_closed_session()
                if not closed_session:
                    self._closed_session_verified = False

                freshness = evaluate_freshness(realm=self.realm, run_date=TimeUtils.today(), scan_type="INTRADAY")
                pipeline_state, metrics = _classify_pipeline_state(
                    freshness,
                    min_history_ratio=self.min_history_ratio,
                    min_intraday_ratio=self.min_intraday_ratio,
                )

                if pipeline_state == "FRESH":
                    if closed_session and not self._closed_session_verified:
                        self.last_attempt_at = TimeUtils.now().isoformat()
                        _write_worker_state(
                            self._snapshot(
                                pipeline_state="SYNCING",
                                freshness=metrics,
                                next_retry_seconds=0,
                                backoff_seconds=0,
                                syncing=True,
                                retry_reason="sync_in_progress",
                            )
                        )
                        self.logger.info(
                            "[SyncWorker] Closed session detected with complete history. "
                            "Running one verification sync pass before idling."
                        )

                        _sync_all_with_timeout(self.sync_timeout_sec)

                        post_freshness = evaluate_freshness(realm=self.realm, run_date=TimeUtils.today(), scan_type="INTRADAY")
                        post_state, post_metrics = _classify_pipeline_state(
                            post_freshness,
                            min_history_ratio=self.min_history_ratio,
                            min_intraday_ratio=self.min_intraday_ratio,
                        )
                        self._promote_to_live_if_market_open(started_closed_session=closed_session)
                        closed_session = self._is_closed_session()

                        if post_state == "FRESH":
                            if closed_session:
                                self._closed_session_verified = True
                            self._persist_fresh_state(post_metrics)
                            if closed_session:
                                self._wait_until_market_reopens_or_stop()
                                continue

                        if closed_session:
                            self._closed_session_verified = True
                            self._persist_closed_session_verified_state(
                                pipeline_state=post_state,
                                freshness=post_metrics,
                            )
                            self.logger.info(
                                "[SyncWorker] Closed-session verification completed with "
                                f"state={post_state} (history_ratio={post_metrics['history_fresh_ratio']}, "
                                f"intraday_ratio={post_metrics['intraday_live_ratio']}). "
                                "Deferring further retries until market reopens."
                            )
                            self._wait_until_market_reopens_or_stop()
                            continue

                    self._persist_fresh_state(metrics)
                    if closed_session:
                        self._wait_until_market_reopens_or_stop()
                        continue
                    
                    if settings.SESSION_MODE == "ANALYSIS":
                        self.logger.info("[SyncWorker] Analysis session complete. Entering idle state.")
                        while not self._stop_event.is_set():
                            self._stop_event.wait(3600)
                        break

                    self._stop_event.wait(self.healthy_interval_sec)
                    continue

                self.provider_unreachable = self._is_mubasher_unreachable()
                if self.provider_unreachable:
                    self.logger.warning("Intraday provider MUBASHER_DB unreachable — source path has no updates in 30+ minutes")
                    self.fail_count += 1
                    self.last_failure_at = TimeUtils.now().isoformat()
                    self.last_error = "Intraday provider MUBASHER_DB unreachable — source path has no updates in 30+ minutes"
                    
                    backoff = min(self.max_backoff_sec, self.base_backoff_sec * (2 ** max(0, self.fail_count - 1)))
                    jittered = max(300, int(round(backoff * random.uniform(0.8, 1.2))))
                    
                    _write_worker_state(
                        self._snapshot(
                            pipeline_state=pipeline_state,
                            freshness=metrics,
                            next_retry_seconds=jittered,
                            backoff_seconds=jittered,
                            syncing=False,
                            retry_reason="provider_unreachable",
                        )
                    )
                    self._stop_event.wait(jittered)
                    continue

                self.last_attempt_at = TimeUtils.now().isoformat()
                _write_worker_state(
                    self._snapshot(
                        pipeline_state="SYNCING",
                        freshness=metrics,
                        next_retry_seconds=0,
                        backoff_seconds=0,
                        syncing=True,
                        retry_reason="sync_in_progress",
                    )
                )
                self.logger.info(
                    f"[SyncWorker] Data not fresh (state={pipeline_state}, "
                    f"history_ratio={metrics['history_fresh_ratio']}, intraday_ratio={metrics['intraday_live_ratio']}). "
                    "Running sync_all..."
                )

                _sync_all_with_timeout(self.sync_timeout_sec)

                post_freshness = evaluate_freshness(realm=self.realm, run_date=TimeUtils.today(), scan_type="INTRADAY")
                post_state, post_metrics = _classify_pipeline_state(
                    post_freshness,
                    min_history_ratio=self.min_history_ratio,
                    min_intraday_ratio=self.min_intraday_ratio,
                )
                self._promote_to_live_if_market_open(started_closed_session=closed_session)
                closed_session = self._is_closed_session()

                if post_state == "FRESH":
                    if closed_session:
                        self._closed_session_verified = True
                    self._persist_fresh_state(post_metrics)
                    if closed_session:
                        self._wait_until_market_reopens_or_stop()
                        continue
                    
                    if settings.SESSION_MODE == "ANALYSIS":
                        self.logger.info("[SyncWorker] Analysis session complete. Entering idle state.")
                        while not self._stop_event.is_set():
                            self._stop_event.wait(3600)
                        break

                    self._stop_event.wait(self.healthy_interval_sec)
                    continue
                else: # post_state is not FRESH
                    if closed_session:
                        self._closed_session_verified = True
                        self._persist_closed_session_verified_state(
                            pipeline_state=post_state,
                            freshness=post_metrics,
                        )
                        self.logger.info(
                            "[SyncWorker] Closed-session sync completed with "
                            f"state={post_state} (history_ratio={post_metrics['history_fresh_ratio']}, "
                            f"intraday_ratio={post_metrics['intraday_live_ratio']}). "
                            "Deferring further retries until market reopens."
                        )
                        self._wait_until_market_reopens_or_stop()
                        continue

                    self.fail_count += 1
                    self.last_failure_at = TimeUtils.now().isoformat()
                    self.last_error = (
                        "sync_all completed but freshness remains below thresholds "
                        f"(state={post_state}, history_ratio={post_metrics['history_fresh_ratio']}, "
                        f"intraday_ratio={post_metrics['intraday_live_ratio']})"
                    )
                    backoff = min(self.max_backoff_sec, self.base_backoff_sec * (2 ** max(0, self.fail_count - 1)))
                    jittered = max(1, int(round(backoff * random.uniform(0.8, 1.2))))
                    _write_worker_state(
                        self._snapshot(
                            pipeline_state=post_state,
                            freshness=post_metrics,
                            next_retry_seconds=jittered,
                            backoff_seconds=backoff,
                            retry_reason="freshness_below_threshold",
                        )
                    )
                    
                    if settings.SESSION_MODE == "ANALYSIS":
                        self.logger.info("[SyncWorker] Analysis session check complete. Disabling further synchronization.")
                        while not self._stop_event.is_set():
                            self._stop_event.wait(3600)
                        break

                    self.logger.warning(f"[SyncWorker] {self.last_error}. Retrying in {jittered}s.")
                    self._stop_event.wait(jittered)
            except Exception as e:  # pragma: no cover - resilience path
                self.fail_count += 1
                self.last_failure_at = TimeUtils.now().isoformat()
                self.last_error = str(e)
                backoff = min(self.max_backoff_sec, self.base_backoff_sec * (2 ** max(0, self.fail_count - 1)))
                jittered = max(1, int(round(backoff * random.uniform(0.8, 1.2))))
                _write_worker_state(
                    self._snapshot(
                        pipeline_state="DEGRADED",
                        freshness={
                            "history_fresh_ratio": 0.0,
                            "intraday_live_ratio": 0.0,
                            "history_ok": False,
                            "intraday_ok": False,
                            "market_open": bool(settings.is_market_open()),
                            "overall_ok": False,
                            "checked_at": TimeUtils.now().isoformat(),
                        },
                        next_retry_seconds=jittered,
                        backoff_seconds=backoff,
                        retry_reason="sync_failed",
                    )
                )
                self.logger.error(f"[SyncWorker] Error: {e}. Retrying in {jittered}s.")
                self._stop_event.wait(jittered)

        self.logger.info("[SyncWorker] Stopped.")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    worker = AdaptiveSyncWorker()
    try:
        worker.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
