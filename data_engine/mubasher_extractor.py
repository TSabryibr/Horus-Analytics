"""
Mubasher Data Extractor & Harvester
Shadow copies Mubasher SQLite databases using the atomic SQLite online backup API
to prevent lock errors and torn pages, runs the ingestion pipelines, and cleans up.
"""
from __future__ import annotations

import logging
import os
import shutil
import sqlite3
import threading
import time
from pathlib import Path

from core.settings import settings
from data_engine.ingest_history import ingest_history
from data_engine.ingest_intraday import ingest_intraday

logger = logging.getLogger(__name__)

_EXTRACTION_LOCK = threading.Lock()


def safe_sqlite_backup(source_path: Path, dest_path: Path) -> bool:
    """
    Atomic, non-blocking snapshot of a live SQLite database.
    Uses read-only URI (mode=ro) to eliminate lock contention with active writer processes,
    while correctly syncing WAL/active transactions and ensuring immediate file handle closure.
    """
    if not source_path.exists():
        return False
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    src_conn = None
    dst_conn = None
    try:
        src_uri = f"file:{source_path.resolve().as_posix()}?mode=ro"
        src_conn = sqlite3.connect(src_uri, uri=True, timeout=10)
        dst_conn = sqlite3.connect(str(dest_path), timeout=10)
        src_conn.backup(dst_conn, pages=200, sleep=0.01)
        return True
    except Exception as exc:
        logger.warning(f"[MubasherExtractor] SQLite online backup failed for {source_path}: {exc}. Trying fallback copy.")
        try:
            shutil.copy2(source_path, dest_path)
            return True
        except Exception as copy_exc:
            logger.error(f"[MubasherExtractor] Fallback copy also failed for {source_path}: {copy_exc}")
            return False
    finally:
        if dst_conn is not None:
            try:
                dst_conn.close()
            except Exception:
                pass
        if src_conn is not None:
            try:
                src_conn.close()
            except Exception:
                pass


def perform_extraction() -> bool:
    """
    Safely snapshots live Mubasher SQLite databases and runs the ingestion pipelines.
    Guarded by _EXTRACTION_LOCK to prevent concurrent shadow directory collisions.
    """
    if not _EXTRACTION_LOCK.acquire(blocking=False):
        logger.info("[MubasherExtractor] Extraction already in progress; skipping duplicate tick.")
        return False

    try:
        logger.info("Starting Mubasher data extraction (Atomic SQLite Backup)")

        # 1. Resolve source paths
        live_root = Path(getattr(settings, "MUBASHER_ROOT_DIR", r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt"))
        live_user_data = live_root / "UserData"

        if not live_user_data.exists():
            logger.error(f"Live Mubasher UserData not found at {live_user_data}")
            return False

        user_id = getattr(settings, "MUBASHER_USER_ID", "").strip()
        if not user_id:
            user_dirs = sorted([d for d in live_user_data.iterdir() if d.is_dir()], key=lambda p: p.name)
            if not user_dirs:
                logger.error(f"No user folders found under {live_user_data}")
                return False
            user_id = user_dirs[0].name

        logger.info(f"Targeting Mubasher User ID: {user_id}")

        live_history = live_user_data / user_id / "History" / "CASE" / "history.db"
        live_intraday = live_user_data / user_id / "Intraday" / "CASE" / "INTRADAY_MASTER.db"

        # 2. Setup shadow directory mirroring the original structure
        shadow_root = (Path(settings.DATA_ROOT) / ".tmp" / "mubasher_shadow").resolve()
        shadow_user_dir = shadow_root / "UserData" / user_id
        shadow_history_dir = shadow_user_dir / "History" / "CASE"
        shadow_intraday_dir = shadow_user_dir / "Intraday" / "CASE"

        shadow_history_dir.mkdir(parents=True, exist_ok=True)
        shadow_intraday_dir.mkdir(parents=True, exist_ok=True)

        shadow_history = shadow_history_dir / "history.db"
        shadow_intraday = shadow_intraday_dir / "INTRADAY_MASTER.db"

        # Step 3: Safe Atomic Shadow Backup
        history_copied = False
        intraday_copied = False

        if live_history.exists():
            logger.info(f"Backing up {live_history} -> {shadow_history}")
            history_copied = safe_sqlite_backup(live_history, shadow_history)
        else:
            logger.warning(f"Live history DB not found at {live_history}")

        if live_intraday.exists():
            logger.info(f"Backing up {live_intraday} -> {shadow_intraday}")
            intraday_copied = safe_sqlite_backup(live_intraday, shadow_intraday)
        else:
            logger.warning(f"Live intraday DB not found at {live_intraday}")

        if not history_copied and not intraday_copied:
            logger.warning("[MubasherExtractor] No databases were successfully backed up. Skipping ingestion.")
            return False

        # Step 4: Patch settings to point to shadow root
        original_root_dir = getattr(settings, "MUBASHER_ROOT_DIR", None)
        original_user_id = getattr(settings, "MUBASHER_USER_ID", None)

        settings.MUBASHER_ROOT_DIR = str(shadow_root)
        settings.MUBASHER_USER_ID = user_id

        # Step 5: Run Ingestion Pipelines using the shadow DBs
        try:
            if intraday_copied:
                logger.info("Running Intraday Ingestion...")
                ingest_intraday(provider="mubasher_sqlite")

            if history_copied:
                logger.info("Running History Ingestion...")
                ingest_history(provider="mubasher_sqlite")
        finally:
            # Restore settings
            if original_root_dir is not None:
                settings.MUBASHER_ROOT_DIR = original_root_dir
            else:
                try:
                    delattr(settings, "MUBASHER_ROOT_DIR")
                except AttributeError:
                    pass

            if original_user_id is not None:
                settings.MUBASHER_USER_ID = original_user_id
            else:
                try:
                    delattr(settings, "MUBASHER_USER_ID")
                except AttributeError:
                    pass

        return True

    except Exception as e:
        logger.error(f"Error during extraction: {e}", exc_info=True)
        return False
    finally:
        # Step 6: Immediately clean up shadow copies
        logger.info("Cleaning up shadow copies...")
        try:
            shadow_root = (Path(settings.DATA_ROOT) / ".tmp" / "mubasher_shadow").resolve()
            if shadow_root.exists():
                shutil.rmtree(shadow_root, ignore_errors=True)
        except Exception as cleanup_err:
            logger.debug(f"Failed to clean up shadow root: {cleanup_err}")
        _EXTRACTION_LOCK.release()


def run_scheduler():
    logger.info("Starting Mubasher Extractor Scheduler (Every 5 minutes)")
    while True:
        try:
            perform_extraction()
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
        logger.info("Sleeping for 5 minutes...")
        time.sleep(300)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    run_scheduler()
