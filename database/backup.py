"""
DATABASE BACKUP & DISASTER RECOVERY
====================================
Zero-downtime automated SQLite online backups, integrity checks,
retention pruning, and fast disaster recovery.
"""

from __future__ import annotations

import datetime
import logging
import os
from pathlib import Path
import sqlite3
from typing import Any, Optional

from core.settings import settings

logger = logging.getLogger("horus.database.backup")


def _resolve_db_file(db_file: Optional[Path | str] = None) -> Path:
    if db_file is not None:
        return Path(db_file).resolve()
    configured = os.getenv("HORUS_DB_FILE")
    if configured:
        return Path(configured).resolve()
    return Path(settings.get_persistent_path("horus.db")).resolve()


def _resolve_backup_dir(backup_dir: Optional[Path | str] = None) -> Path:
    if backup_dir is not None:
        target_dir = Path(backup_dir).resolve()
    else:
        target_dir = (Path(settings.DATA_ROOT) / "backups").resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def execute_database_backup(
    db_file: Optional[Path | str] = None,
    backup_dir: Optional[Path | str] = None,
    max_retention_days: int = 14,
    label: Optional[str] = None,
) -> dict[str, Any]:
    """
    Executes an online, non-blocking page-by-page backup from the live SQLite database.
    Performs a WAL checkpoint, validates backup integrity, and enforces retention pruning.
    """
    source_path = _resolve_db_file(db_file)
    target_dir = _resolve_backup_dir(backup_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if not source_path.exists():
        logger.error(f"[Backup] Source database file not found: {source_path}")
        return {
            "status": "error",
            "error": f"Source database file not found: {source_path}",
            "timestamp": datetime.datetime.now().isoformat(),
        }

    # Step 1: Attempt passive WAL checkpoint to flush dirty cache pages without blocking
    try:
        chk_conn = sqlite3.connect(str(source_path), timeout=5)
        chk_conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
        chk_conn.close()
    except Exception as wal_exc:
        logger.debug(f"[Backup] Passive WAL checkpoint notice for {source_path}: {wal_exc}")

    # Generate timestamped backup file name
    timestamp = datetime.datetime.now()
    ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
    clean_label = f"_{label.strip()}" if label and label.strip() else ""
    backup_filename = f"horus_backup_{ts_str}{clean_label}.db"
    backup_path = target_dir / backup_filename

    src_conn = None
    dst_conn = None
    try:
        src_uri = f"file:{source_path.resolve().as_posix()}?mode=ro"
        src_conn = sqlite3.connect(src_uri, uri=True, timeout=15)
        dst_conn = sqlite3.connect(str(backup_path), timeout=15)

        logger.info(f"[Backup] Starting online streaming snapshot: {source_path} -> {backup_path}")
        src_conn.backup(dst_conn, pages=250, sleep=0.01)

        # Close destination connection before integrity check
        dst_conn.close()
        dst_conn = None
        src_conn.close()
        src_conn = None

        # Step 2: Validate integrity on the newly created backup
        chk = sqlite3.connect(str(backup_path), timeout=10)
        res = chk.execute("PRAGMA integrity_check;").fetchone()
        chk.close()

        integrity_result = res[0] if res else "unknown"
        if integrity_result != "ok":
            logger.error(f"[Backup] Integrity check failed on {backup_path}: {integrity_result}")
            if backup_path.exists():
                backup_path.unlink(missing_ok=True)
            return {
                "status": "error",
                "error": f"Integrity check failed: {integrity_result}",
                "timestamp": timestamp.isoformat(),
            }

        size_bytes = backup_path.stat().st_size
        logger.info(f"[Backup] Backup created successfully: {backup_filename} ({size_bytes:,} bytes, integrity=ok)")

        # Step 3: Enforce retention pruning
        pruned_count = prune_backups(target_dir, max_retention_days=max_retention_days)

        all_backups = list_backups(target_dir)

        return {
            "status": "ok",
            "backup_file": str(backup_path),
            "filename": backup_filename,
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "timestamp": timestamp.isoformat(),
            "integrity": "ok",
            "total_backups": len(all_backups),
            "pruned_backups": pruned_count,
        }

    except Exception as exc:
        logger.error(f"[Backup] Backup execution failed for {source_path}: {exc}", exc_info=True)
        if backup_path.exists():
            backup_path.unlink(missing_ok=True)
        return {
            "status": "error",
            "error": str(exc),
            "timestamp": timestamp.isoformat(),
        }
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


def list_backups(backup_dir: Optional[Path | str] = None) -> list[dict[str, Any]]:
    """
    Lists all database backups in the target directory ordered by modification time descending.
    """
    target_dir = _resolve_backup_dir(backup_dir)
    backups: list[dict[str, Any]] = []

    now = datetime.datetime.now()
    for file_path in target_dir.glob("horus_backup_*.db"):
        if not file_path.is_file():
            continue
        try:
            stat = file_path.stat()
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
            age_days = round((now - mtime).total_seconds() / 86400, 2)
            backups.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": mtime.isoformat(),
                "age_days": age_days,
            })
        except OSError:
            continue

    backups.sort(key=lambda b: b["created_at"], reverse=True)
    return backups


def prune_backups(backup_dir: Optional[Path | str] = None, max_retention_days: int = 14) -> int:
    """
    Deletes backup files older than max_retention_days. Returns the count of deleted files.
    """
    target_dir = _resolve_backup_dir(backup_dir)
    cutoff = datetime.datetime.now() - datetime.timedelta(days=max_retention_days)
    pruned = 0

    for file_path in target_dir.glob("horus_backup_*.db"):
        if not file_path.is_file():
            continue
        try:
            mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff:
                logger.info(f"[Backup] Pruning expired backup ({mtime.date()}): {file_path.name}")
                file_path.unlink(missing_ok=True)
                pruned += 1
        except OSError as e:
            logger.warning(f"[Backup] Could not prune {file_path.name}: {e}")

    return pruned


def restore_database_backup(
    backup_file: Path | str,
    target_db_file: Optional[Path | str] = None,
    create_safety_snapshot: bool = True,
) -> dict[str, Any]:
    """
    Restores the live database from a specified backup file.
    Creates an automatic pre-restore safety snapshot before making changes.
    """
    src_backup = Path(backup_file).resolve()
    target_path = _resolve_db_file(target_db_file)

    if not src_backup.exists():
        return {"status": "error", "error": f"Backup file not found: {src_backup}"}

    # Verify backup integrity prior to restore
    chk_conn = None
    try:
        chk_conn = sqlite3.connect(str(src_backup), timeout=10)
        chk_res = chk_conn.execute("PRAGMA integrity_check;").fetchone()
        chk_conn.close()
        chk_conn = None
        if not chk_res or chk_res[0] != "ok":
            return {"status": "error", "error": f"Integrity check failed for {src_backup.name}: {chk_res}"}
    except Exception as exc:
        if chk_conn is not None:
            try:
                chk_conn.close()
            except Exception:
                pass
        return {"status": "error", "error": f"Failed to verify backup integrity: {exc}"}

    # Step 1: Create automatic safety snapshot of the target database if it exists
    safety_snapshot_path = None
    if create_safety_snapshot and target_path.exists():
        safety_dir = target_path.parent / "backups"
        safety_dir.mkdir(parents=True, exist_ok=True)
        ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safety_snapshot_path = safety_dir / f"horus_pre_restore_{ts_str}.db"

        safety_src = None
        safety_dst = None
        try:
            src_uri = f"file:{target_path.resolve().as_posix()}?mode=ro"
            safety_src = sqlite3.connect(src_uri, uri=True, timeout=10)
            safety_dst = sqlite3.connect(str(safety_snapshot_path), timeout=10)
            safety_src.backup(safety_dst)
            safety_dst.close()
            safety_dst = None
            safety_src.close()
            safety_src = None
            logger.info(f"[Backup] Pre-restore safety snapshot created: {safety_snapshot_path.name}")
        except Exception as snap_err:
            logger.warning(f"[Backup] Could not create pre-restore snapshot: {snap_err}")
        finally:
            if safety_dst is not None:
                try:
                    safety_dst.close()
                except Exception:
                    pass
            if safety_src is not None:
                try:
                    safety_src.close()
                except Exception:
                    pass

    # Step 2: Stream restore from backup into target path
    restore_src = None
    restore_dst = None
    try:
        restore_src = sqlite3.connect(f"file:{src_backup.resolve().as_posix()}?mode=ro", uri=True, timeout=15)
        restore_dst = sqlite3.connect(str(target_path), timeout=15)
        restore_src.backup(restore_dst)
        restore_dst.close()
        restore_dst = None
        restore_src.close()
        restore_src = None

        # Step 3: Remove associated -wal and -shm files so SQLite opens cleanly
        wal_file = target_path.with_name(f"{target_path.name}-wal")
        shm_file = target_path.with_name(f"{target_path.name}-shm")
        wal_file.unlink(missing_ok=True)
        shm_file.unlink(missing_ok=True)

        logger.info(f"[Backup] Database successfully restored from {src_backup.name} to {target_path}")
        return {
            "status": "ok",
            "restored_from": str(src_backup),
            "target_database": str(target_path),
            "safety_snapshot": str(safety_snapshot_path) if safety_snapshot_path else None,
            "timestamp": datetime.datetime.now().isoformat(),
        }
    except Exception as exc:
        logger.error(f"[Backup] Failed restoring database: {exc}", exc_info=True)
        return {"status": "error", "error": str(exc)}
    finally:
        if restore_dst is not None:
            try:
                restore_dst.close()
            except Exception:
                pass
        if restore_src is not None:
            try:
                restore_src.close()
            except Exception:
                pass


def get_backup_status(backup_dir: Optional[Path | str] = None) -> dict[str, Any]:
    """
    Returns telemetry metrics for database backup status and health.
    """
    backups = list_backups(backup_dir)
    total_bytes = sum(b["size_bytes"] for b in backups)

    latest = backups[0] if backups else None
    oldest = backups[-1] if backups else None

    # Check live DB size and path
    live_db = _resolve_db_file()
    live_size = live_db.stat().st_size if live_db.exists() else 0

    return {
        "configured": True,
        "backup_count": len(backups),
        "total_size_bytes": total_bytes,
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
        "latest_backup": latest,
        "oldest_backup": oldest,
        "live_db_path": str(live_db),
        "live_db_size_mb": round(live_size / (1024 * 1024), 2),
        "retention_days": 14,
        "status": "HEALTHY" if latest and latest["age_days"] <= 2 else "PENDING" if not latest else "STALE",
    }
