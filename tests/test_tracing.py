"""
Tests for Horus Distributed Tracing, Structured Logging, and X-Request-ID propagation.
"""

import json
import logging
import pytest
from starlette.testclient import TestClient

from core.tracing import (
    StructuredJsonFormatter,
    TracingLogFilter,
    get_request_id,
    get_run_id,
    set_request_id,
    set_run_id,
)
from core.audit import log_event, get_recent_logs
from config.app_factory import create_app


def test_tracing_context_vars():
    set_request_id("test-req-123")
    set_run_id("test-run-456")

    assert get_request_id() == "test-req-123"
    assert get_run_id() == "test-run-456"

    set_request_id(None)
    set_run_id(None)
    assert get_request_id() is None
    assert get_run_id() is None


def test_structured_json_formatter():
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=40,
        msg="Test structured log message",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-abc"
    record.run_id = "run-xyz"

    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["level"] == "INFO"
    assert data["logger"] == "test.logger"
    assert data["message"] == "Test structured log message"
    assert data["request_id"] == "req-abc"
    assert data["run_id"] == "run-xyz"


def test_request_id_middleware_propagation():
    app = create_app()
    client = TestClient(app)

    # 1. Without incoming X-Request-ID header -> auto-generates and returns in header
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    auto_id = resp.headers["X-Request-ID"]
    assert len(auto_id) > 10

    # 2. With incoming custom X-Request-ID header -> preserves the caller's ID
    resp2 = client.get("/health", headers={"X-Request-ID": "custom-client-trace-999"})
    assert resp2.status_code == 200
    assert resp2.headers.get("X-Request-ID") == "custom-client-trace-999"


def test_audit_event_tracing_enrichment():
    set_request_id("req-audit-777")
    set_run_id("run-audit-888")

    log_event(
        category="SYSTEM",
        event="TRACING_TEST",
        message="Testing trace enrichment in audit",
        level="INFO",
        meta={"source": "pytest"},
    )

    set_request_id(None)
    set_run_id(None)
