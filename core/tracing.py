"""
HORUS ANALYTICS - REQUEST & RUN TRACING SYSTEM
==============================================
ContextVar-backed distributed tracing helpers, structured JSON logging,
and request correlation utilities.
"""

from __future__ import annotations

import contextvars
import json
import logging
import uuid
from typing import Any, Dict, Optional

# Context variable singletons for request and execution tracing
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)
run_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("run_id", default=None)


def get_request_id() -> Optional[str]:
    """Retrieves the current request ID from context."""
    return request_id_ctx.get()


def set_request_id(request_id: Optional[str]) -> contextvars.Token[Optional[str]]:
    """Sets the request ID in context, returning a token for reset."""
    return request_id_ctx.set(request_id)


def generate_request_id() -> str:
    """Generates a new UUID4 string for request tracing."""
    return str(uuid.uuid4())


def get_run_id() -> Optional[str]:
    """Retrieves the current pipeline/signal run ID from context."""
    return run_id_ctx.get()


def set_run_id(run_id: Optional[str]) -> contextvars.Token[Optional[str]]:
    """Sets the pipeline run ID in context, returning a token for reset."""
    return run_id_ctx.set(run_id)


class TracingLogFilter(logging.Filter):
    """
    Logging filter that injects 'request_id' and 'run_id' into LogRecord instances.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        record.run_id = get_run_id() or "-"
        return True


class StructuredJsonFormatter(logging.Formatter):
    """
    JSON formatter emitting machine-readable structured logs with tracing fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", get_request_id() or "-"),
            "run_id": getattr(record, "run_id", get_run_id() or "-"),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include custom extra metadata if supplied
        extra_data = getattr(record, "extra_data", None)
        if isinstance(extra_data, dict):
            log_entry["data"] = extra_data

        return json.dumps(log_entry)
