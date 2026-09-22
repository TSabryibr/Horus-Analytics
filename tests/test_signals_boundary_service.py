import datetime

import pytest
from fastapi import HTTPException

from core.signals.boundary import (
    bool_env,
    error_context,
    get_publish_window_status,
    int_env,
    noop_context,
    parse_run_date,
    validated_publish_channel,
    validation_error,
)


def test_parse_run_date_uses_today_when_missing():
    assert parse_run_date(None, today_fn=lambda: datetime.date(2026, 3, 17)) == datetime.date(2026, 3, 17)


def test_parse_run_date_invalid_raises_structured_http_error():
    with pytest.raises(HTTPException) as exc_info:
        parse_run_date("bad-date")

    assert exc_info.value.status_code == 400
    detail = exc_info.value.detail
    assert detail["error_type"] == "validation"
    assert detail["error_reason"] == "invalid_run_date"
    assert detail["parameter"] == "run_date"
    assert detail["run_date"] == "bad-date"


def test_get_publish_window_status_reports_window_closed():
    now = datetime.datetime(2026, 3, 17, 17, 0, 0)
    result = get_publish_window_status(datetime.date(2026, 3, 17), now_dt=now)

    assert result["ok"] is False
    assert result["reason"] == "window_closed"


def test_int_env_falls_back_on_invalid_value():
    assert int_env("SIGNAL_TEST_INT", 14, env_get_fn=lambda name: "bad") == 14


def test_bool_env_accepts_truthy_strings():
    assert bool_env("SIGNAL_TEST_BOOL", False, env_get_fn=lambda name: "yes") is True


def test_validation_and_noop_contexts_are_shaped_consistently():
    validation = validation_error("invalid_scan_type", "scan_type must be DAILY or INTRADAY", parameter="scan_type")
    noop = noop_context("retry", "no_failed_deliveries", "No failed deliveries to retry.")
    error = error_context("state", "run_not_completed", "Run must be COMPLETED before publish.")

    assert validation["error_type"] == "validation"
    assert validation["parameter"] == "scan_type"
    assert noop["noop_type"] == "retry"
    assert noop["noop_reason"] == "no_failed_deliveries"
    assert error["error_type"] == "state"


def test_validated_publish_channel_rejects_unknown_channel():
    with pytest.raises(HTTPException) as exc_info:
        validated_publish_channel("EMAIL")

    assert exc_info.value.status_code == 400
    detail = exc_info.value.detail
    assert detail["error_type"] == "validation"
    assert detail["error_reason"] == "unsupported_channel"
    assert detail["channel"] == "EMAIL"
