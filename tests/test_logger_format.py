import logging
import re

from utils.logger import _compact_logger_name, build_log_formatter


def test_horus_terminal_formatter_aligns_log_columns():
    formatter = build_log_formatter()
    record = logging.LogRecord(
        name="apscheduler.executors.default",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Running job %s",
        args=("scheduled_intraday_scan",),
        exc_info=None,
    )

    formatted = formatter.format(record)

    assert re.match(
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} "
        r"\| INFO\s+ "
        r"\| apscheduler\.exe\.default\s+ "
        r"\| Running job scheduled_intraday_scan$",
        formatted,
    )


def test_compact_logger_name_keeps_terminal_column_stable():
    assert _compact_logger_name("horus.api") == "horus.api"

    compact = _compact_logger_name("apscheduler.executors.default")
    assert compact == "apscheduler.exe.default"
    assert len(compact) <= 24

    truncated = _compact_logger_name("very.long.logger.name.with.too.many.parts")
    assert len(truncated) <= 24
