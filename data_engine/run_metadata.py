from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def _db_path(realm: str = "EGX") -> Path:
    from core.settings import settings
    root = Path(settings.DATA_ROOT) / realm
    root.mkdir(parents=True, exist_ok=True)
    return root / "pipeline_metadata.sqlite"


def _connect(realm: str = "EGX") -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(realm), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_runs (
            run_id TEXT PRIMARY KEY,
            stage TEXT NOT NULL,
            provider TEXT,
            realm TEXT NOT NULL,
            stream TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            duration_ms INTEGER,
            status TEXT NOT NULL,
            rows_read INTEGER,
            rows_written INTEGER,
            rows_rejected INTEGER,
            watermark_before TEXT,
            watermark_after TEXT,
            error TEXT,
            provider_context TEXT
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_ingestion_runs_stage_started "
        "ON ingestion_runs(stage, started_at DESC)"
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(ingestion_runs)").fetchall()}
    if "provider_context" not in columns:
        conn.execute("ALTER TABLE ingestion_runs ADD COLUMN provider_context TEXT")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def start_run(
    stage: str,
    stream: str,
    realm: str = "EGX",
    provider: str | None = None,
    watermark_before: str | None = None,
    provider_context: dict | None = None,
) -> str:
    run_id = uuid.uuid4().hex
    context_json = json.dumps(provider_context, default=str, separators=(",", ":")) if provider_context else None
    with closing(_connect(realm)) as conn, conn:
        conn.execute(
            """
            INSERT INTO ingestion_runs
                (run_id, stage, provider, realm, stream, started_at, status, watermark_before, provider_context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, stage, provider, realm, stream, _now_iso(), "RUNNING", watermark_before, context_json),
        )
    return run_id


def finish_run(
    run_id: str,
    *,
    realm: str = "EGX",
    status: str = "COMPLETED",
    rows_read: int | None = None,
    rows_written: int | None = None,
    rows_rejected: int | None = None,
    watermark_after: str | None = None,
    error: str | None = None,
    provider_context: dict | None = None,
) -> None:
    finished_at = _now_iso()
    context_json = json.dumps(provider_context, default=str, separators=(",", ":")) if provider_context else None
    with closing(_connect(realm)) as conn, conn:
        row = conn.execute("SELECT started_at FROM ingestion_runs WHERE run_id = ?", (run_id,)).fetchone()
        duration_ms = None
        if row and row[0]:
            try:
                started = datetime.fromisoformat(str(row[0]))
                ended = datetime.fromisoformat(finished_at)
                duration_ms = int((ended - started).total_seconds() * 1000)
            except Exception:
                duration_ms = None
        conn.execute(
            """
            UPDATE ingestion_runs
            SET finished_at = ?,
                duration_ms = ?,
                status = ?,
                rows_read = COALESCE(?, rows_read),
                rows_written = COALESCE(?, rows_written),
                rows_rejected = COALESCE(?, rows_rejected),
                watermark_after = COALESCE(?, watermark_after),
                error = COALESCE(?, error),
                provider_context = COALESCE(?, provider_context)
            WHERE run_id = ?
            """,
            (
                finished_at,
                duration_ms,
                status,
                rows_read,
                rows_written,
                rows_rejected,
                watermark_after,
                error,
                context_json,
                run_id,
            ),
        )


def list_runs(realm: str = "EGX", limit: int = 50) -> list[dict]:
    with closing(_connect(realm)) as conn, conn:
        rows = conn.execute(
            """
            SELECT run_id, stage, provider, realm, stream, started_at, finished_at, duration_ms, status,
                   rows_read, rows_written, rows_rejected, watermark_before, watermark_after, error, provider_context
            FROM ingestion_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    cols = [
        "run_id",
        "stage",
        "provider",
        "realm",
        "stream",
        "started_at",
        "finished_at",
        "duration_ms",
        "status",
        "rows_read",
        "rows_written",
        "rows_rejected",
        "watermark_before",
        "watermark_after",
        "error",
        "provider_context",
    ]
    out = []
    for row in rows:
        record = dict(zip(cols, row))
        raw_context = record.get("provider_context")
        if raw_context:
            try:
                record["provider_context"] = json.loads(str(raw_context))
            except Exception:
                record["provider_context"] = None
        else:
            record["provider_context"] = None
        out.append(record)
    return out
