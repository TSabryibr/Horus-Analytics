import os
import re
import logging
import warnings
from logging.handlers import RotatingFileHandler
import sys
import time

# Suppress known noisy third-party warnings (Matplotlib fonts and deprecations)
warnings.filterwarnings("ignore", category=UserWarning, message=".*Glyph.*missing from font.*")
warnings.filterwarnings("ignore", module="matplotlib.*", message=".*deprecated.*")

# Ensure logs directory exists
LOG_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "horus.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "api_errors.log")
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOGGER_NAME_WIDTH = 24
LOG_FORMAT = "%(asctime)s.%(msecs)03d | %(terminal_level)-8s | %(terminal_name)-24s | %(message)s"


def cleanup_old_logs(log_dir: str = LOG_DIR, max_age_days: int = 30) -> int:
    """Purges rotated backup files (*.log.<number>) in log_dir and project root older than max_age_days.
    Active *.log files are never deleted.
    Invoked explicitly during startup or maintenance operations.
    """
    now = time.time()
    cutoff = now - (max_age_days * 86400)
    removed_count = 0
    backup_pattern = re.compile(r"^.*\.log\.\d+$")

    project_root = os.path.abspath(os.path.join(log_dir, ".."))
    scan_dirs = [d for d in [log_dir, project_root] if os.path.exists(d)]

    for target_dir in scan_dirs:
        try:
            for filename in os.listdir(target_dir):
                if backup_pattern.match(filename):
                    filepath = os.path.join(target_dir, filename)
                    try:
                        if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                            os.remove(filepath)
                            removed_count += 1
                    except Exception as exc:
                        sys.stderr.write(f"[Logger] Failed to delete old log backup {filepath}: {exc}\n")
        except Exception as exc:
            sys.stderr.write(f"[Logger] Failed to list directory {target_dir} for cleanup: {exc}\n")
    return removed_count


def _compact_logger_name(name: str, width: int = LOGGER_NAME_WIDTH) -> str:
    clean_name = (name or "root").strip() or "root"
    if len(clean_name) <= width:
        return clean_name

    parts = [part for part in clean_name.split(".") if part]
    if len(parts) > 1:
        compact = ".".join([parts[0], *[part[:3] for part in parts[1:-1]], parts[-1]])
        if len(compact) <= width:
            return compact

    return f"{clean_name[:width - 1]}~"


class HorusTerminalFormatter(logging.Formatter):
    """Fixed-width formatter for app terminal and file logs."""

    def format(self, record: logging.LogRecord) -> str:
        record.terminal_name = _compact_logger_name(record.name)
        record.terminal_level = record.levelname
        return super().format(record)


def build_log_formatter() -> logging.Formatter:
    return HorusTerminalFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)


class SessionAwareFileHandler(logging.Handler):
    """Dynamic handler routing logs to horus_market.log or horus_analysis.log based on settings.SESSION_MODE."""

    def __init__(self, log_dir: str, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        super().__init__()
        self.market_file = os.path.join(log_dir, "horus_market.log")
        self.analysis_file = os.path.join(log_dir, "horus_analysis.log")
        self.market_handler = RotatingFileHandler(
            self.market_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
        )
        self.analysis_handler = RotatingFileHandler(
            self.analysis_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
        )

    def setFormatter(self, fmt: logging.Formatter | None) -> None:
        super().setFormatter(fmt)
        self.market_handler.setFormatter(fmt)
        self.analysis_handler.setFormatter(fmt)

    def emit(self, record: logging.LogRecord):
        try:
            mode = "ANALYSIS"
            try:
                if getattr(self, "_settings_ref", None) is None:
                    from core.settings import settings
                    self._settings_ref = settings
                mode = str(getattr(self._settings_ref, "SESSION_MODE", "ANALYSIS") or "ANALYSIS").strip().upper()
            except Exception:
                pass

            if mode == "LIVE":
                self.market_handler.emit(record)
            else:
                self.analysis_handler.emit(record)
        except Exception:
            self.handleError(record)

    def close(self):
        self.market_handler.close()
        self.analysis_handler.close()
        super().close()


# Module-level singleton handlers
_CONSOLE_HANDLER: logging.StreamHandler | None = None
_MAIN_FILE_HANDLER: RotatingFileHandler | None = None
_SESSION_FILE_HANDLER: SessionAwareFileHandler | None = None
_ERROR_FILE_HANDLER: RotatingFileHandler | None = None


def _get_shared_handlers() -> list[logging.Handler]:
    global _CONSOLE_HANDLER, _MAIN_FILE_HANDLER, _SESSION_FILE_HANDLER, _ERROR_FILE_HANDLER
    formatter = build_log_formatter()

    if _CONSOLE_HANDLER is None:
        _CONSOLE_HANDLER = logging.StreamHandler(sys.stdout)
        _CONSOLE_HANDLER.setFormatter(formatter)

    if _MAIN_FILE_HANDLER is None:
        try:
            _MAIN_FILE_HANDLER = RotatingFileHandler(
                LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8'
            )
            _MAIN_FILE_HANDLER.setFormatter(formatter)
        except Exception as e:
            sys.stderr.write(f"Failed to set up main file logger: {e}\n")

    if _SESSION_FILE_HANDLER is None:
        try:
            _SESSION_FILE_HANDLER = SessionAwareFileHandler(LOG_DIR, max_bytes=10 * 1024 * 1024, backup_count=5)
            _SESSION_FILE_HANDLER.setFormatter(formatter)
        except Exception as e:
            sys.stderr.write(f"Failed to set up session-segregated logger: {e}\n")

    if _ERROR_FILE_HANDLER is None:
        try:
            _ERROR_FILE_HANDLER = RotatingFileHandler(
                ERROR_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
            )
            _ERROR_FILE_HANDLER.setLevel(logging.ERROR)
            _ERROR_FILE_HANDLER.setFormatter(formatter)
        except Exception as e:
            sys.stderr.write(f"Failed to set up error file logger: {e}\n")

    handlers = []
    if _CONSOLE_HANDLER:
        handlers.append(_CONSOLE_HANDLER)
    if _MAIN_FILE_HANDLER:
        handlers.append(_MAIN_FILE_HANDLER)
    if _SESSION_FILE_HANDLER:
        handlers.append(_SESSION_FILE_HANDLER)
    if _ERROR_FILE_HANDLER:
        handlers.append(_ERROR_FILE_HANDLER)
    return handlers


def setup_logger(name: str) -> logging.Logger:
    """Configures and returns a structured logger using shared singleton handlers."""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in _get_shared_handlers():
        logger.addHandler(handler)

    return logger


# Configure the root logger once using shared handlers
root_logger = logging.getLogger()
if not root_logger.handlers:
    root_logger.setLevel(logging.INFO)
    for h in _get_shared_handlers():
        root_logger.addHandler(h)
