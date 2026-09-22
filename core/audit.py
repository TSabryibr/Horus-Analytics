import logging
import os
import json
import datetime
from typing import Dict, Any, List
from core import TimeUtils
from database import db
from peewee import Model, CharField, TextField, DateTimeField, FloatField

logger = logging.getLogger("horus.audit")

class AuditLog(Model):
    """
    Institutional Audit Log for tracking system decisions and events.
    """
    timestamp = DateTimeField(default=datetime.datetime.now)
    level = CharField(max_length=20, default="INFO") # INFO, WARNING, ERROR, CRITICAL
    category = CharField(max_length=50) # SIGNAL, TRADE, SYSTEM, SCRAPE, AUTH
    event = CharField(max_length=100)
    ticker = CharField(max_length=20, null=True)
    message = TextField()
    metadata = TextField(null=True) # JSON string

    class Meta:
        database = db

import threading
import queue
import time

# --- BACKGROUND LOGGING SYSTEM (H3.1) ---
_LOG_QUEUE = queue.Queue()
_WORKER_THREAD = None

def _log_worker():
    """Background consumer for audit logs to prevent DB locks from hanging threads."""
    while True:
        try:
            item = _LOG_QUEUE.get()
            if item is None: break
            
            category, event, message, level, ticker, meta_json = item
            
            # Retry logic for SQLite "database is locked" errors
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with db.atomic():
                        AuditLog.create(
                            category=category,
                            event=event,
                            message=message,
                            level=level,
                            ticker=ticker,
                            metadata=meta_json
                        )
                    break 
                except Exception as e:
                    if "locked" in str(e).lower() and attempt < max_retries - 1:
                        time.sleep(0.5 * (attempt + 1))
                        continue
                    logger.error(f"Audit Worker: Write failed for {event}: {e}")
            
            _LOG_QUEUE.task_done()
        except Exception as e:
            logger.error(f"Audit Worker Critical Error: {e}")

def _ensure_worker_alive():
    global _WORKER_THREAD
    if _WORKER_THREAD is None or not _WORKER_THREAD.is_alive():
        _WORKER_THREAD = threading.Thread(target=_log_worker, daemon=True, name="AuditWorker")
        _WORKER_THREAD.start()

def initialize_audit_table():
    try:
        if not AuditLog.table_exists():
            db.create_tables([AuditLog])
            logger.info("Audit: AuditLog table created.")
        _ensure_worker_alive()
    except Exception as e:
        logger.error(f"Audit: Initialization failed: {e}")

def log_event(category: str, event: str, message: str, level: str = "INFO", ticker: str = None, meta: Dict[str, Any] = None):
    """
    Logs a system event. Console logging is immediate; DB logging is backgrounded.
    """
    try:
        from core.tracing import get_request_id, get_run_id

        req_id = get_request_id()
        run_id = get_run_id()

        if req_id or run_id:
            meta = dict(meta) if meta else {}
            if req_id and "request_id" not in meta:
                meta["request_id"] = req_id
            if run_id and "run_id" not in meta:
                meta["run_id"] = run_id

        # 1. Standard Console/File Logging (Immediate)
        trace_suffix = f" [req={req_id or '-'}]" if req_id else ""
        log_msg = f"Audit [{category}] {event}: {message}{trace_suffix}"
        if level == "INFO": logger.info(log_msg)
        elif level == "WARNING": logger.warning(log_msg)
        elif level == "ERROR": logger.error(log_msg)
        
        # 2. Database Logging (Offloaded to Queue)
        meta_json = json.dumps(meta) if meta else None
        _ensure_worker_alive()
        _LOG_QUEUE.put((category, event, message, level, ticker, meta_json))
            
        # 3. Optional: Broadcast to WebSockets (Async Awareness)
        from core.websocket import ws_manager
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            data = {
                "category": category,
                "event": event,
                "message": message,
                "level": level,
                "ticker": ticker,
                "request_id": req_id,
                "run_id": run_id,
                "timestamp": datetime.datetime.now().isoformat()
            }
            loop.create_task(ws_manager.broadcast(data, event_type="audit"))
        except RuntimeError:
            pass
            
    except Exception as e:
        logger.error(f"Audit: Logging dispatch failed: {e}")

def get_recent_logs(limit: int = 100, category: str = None) -> List[Dict]:
    """
    Retrieves recent audit logs.
    """
    try:
        query = AuditLog.select().order_by(AuditLog.timestamp.desc())
        if category:
            query = query.where(AuditLog.category == category)
        
        logs = []
        for l in query.limit(limit):
            logs.append({
                "id": l.id,
                "timestamp": l.timestamp.isoformat(),
                "level": l.level,
                "category": l.category,
                "event": l.event,
                "ticker": l.ticker,
                "message": l.message,
                "metadata": json.loads(l.metadata) if l.metadata else None
            })
        return logs
    except Exception as e:
        logger.error(f"Audit: Retrieval failed: {e}")
        return []
