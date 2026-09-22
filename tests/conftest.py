import os
import tempfile

os.environ.setdefault("HORUS_DISABLE_READINESS_GATE", "1")
os.environ.setdefault("HORUS_DISABLE_STARTUP_THREAD", "1")
os.environ.setdefault("SKIP_STARTUP_SYNC", "true")
os.environ.setdefault("LIVE_ARM_GUARD_ENABLED", "0")
os.environ.setdefault(
    "HORUS_SETTINGS_FILE",
    os.path.join(tempfile.gettempdir(), f"horus_pytest_settings_{os.getpid()}.json"),
)

from core.settings import settings, init_app_settings
init_app_settings()
from core.exclusions import get_all_exclusions, GlobalExclusions

import pytest
import warnings
from fastapi.testclient import TestClient
from peewee import SqliteDatabase

from database import (
    db,
    Position,
    Trade,
    BrokerOrder,
    Signal,
    BackfillIntradayCheckpoint,
    Portfolio,
    SignalRun,
    SignalRecommendation,
    SignalDelivery,
    SignalOutcome,
    LegacySignalOutcome,
    PublishedSignalLifecycle,
    PublishedSignalLifecycleEvent,
    PublishedSignalFollowUp,
    HorusExecution,
    SignalExecutionAttribution,
    PortfolioDefaultState,
    SignalValidationRun,
    TickerStrategyMetrics,
    SignalGuardState,
    SignalDeskState,
    ProvisioningState,
    SignalSuppressionLog,
    Holiday,
    Client,
    ClientApiKey,
    ClientEntitlement,
    SubscriptionDelivery,
    SignalAuditEvent,
    PortfolioSnapshot,
    SovereignState,
    ScannerStrategyProfile,
    SignalStateArchive,
)

warnings.filterwarnings(
    "ignore",
    message=r"Exception ignored in: <function Variable\.__del__.*",
    category=pytest.PytestUnraisableExceptionWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"Exception ignored in: <function Image\.__del__.*",
    category=pytest.PytestUnraisableExceptionWarning,
)

@pytest.fixture(autouse=True)
def setup_test_db():
    import uuid
    import tempfile
    from routes.shared import update_system_state

    test_db_path = os.path.join(tempfile.gettempdir(), f"test_horus_{uuid.uuid4().hex}.db")
    test_db = SqliteDatabase(test_db_path, check_same_thread=False, thread_safe=False)

    db.initialize(test_db)
    db.connect(reuse_if_open=True)
    db.create_tables(
        [
            Portfolio,
            Position,
            Trade,
            BrokerOrder,
            Signal,
            BackfillIntradayCheckpoint,
            SignalRun,
            SignalRecommendation,
            SignalDelivery,
            SignalOutcome,
            PublishedSignalLifecycle,
            PublishedSignalLifecycleEvent,
            PublishedSignalFollowUp,
            HorusExecution,
            SignalExecutionAttribution,
            PortfolioDefaultState,
            SignalValidationRun,
            TickerStrategyMetrics,
            SignalGuardState,
            SignalDeskState,
            ProvisioningState,
            SignalSuppressionLog,
            Holiday,
            Client,
            ClientApiKey,
            ClientEntitlement,
            SubscriptionDelivery,
            SignalAuditEvent,
            PortfolioSnapshot,
            SovereignState,
            ScannerStrategyProfile,
            SignalStateArchive,
            LegacySignalOutcome,
        ],
        safe=True
    )

    update_system_state(
        {
            "status": "READY",
            "pipeline_state": "FRESH",
            "message": "Test Mode",
            "bootstrap_complete": True,
            "progress": 100,
            "step": "Ready",
        }
    )

    Portfolio.get_or_create(name="Intraday Signals", defaults={"type": "SYSTEM"})
    Portfolio.get_or_create(name="Swing Signals", defaults={"type": "SYSTEM"})
    Portfolio.get_or_create(name="Position Signals", defaults={"type": "SYSTEM"})

    yield db

    try:
        db.close()
    except Exception:
        pass
    try:
        test_db.close()
    except Exception:
        pass

    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except PermissionError:
            pass

    from database import real_db
    db.initialize(real_db)


@pytest.fixture(autouse=True)
def isolate_dynamic_exclusions(tmp_path, monkeypatch):
    exclusions_file = tmp_path / "data" / "EGX" / "exclusions.json"
    exclusions_file.parent.mkdir(parents=True, exist_ok=True)
    exclusions_file.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(settings, "EXCLUSIONS_FILE", str(exclusions_file), raising=False)
    monkeypatch.setattr(GlobalExclusions, "file_path", str(exclusions_file), raising=False)
    get_all_exclusions()
    yield
    get_all_exclusions()


@pytest.fixture(autouse=True)
def reset_backfill_state():
    try:
        from core.market import HistoricalBackfill
        HistoricalBackfill.BACKFILL_STATE.update({
            "status": "IDLE",
            "progress": 0,
            "current_day": None,
            "total_days": 0,
            "error": None,
            "mode": "AUTOMATIC"
        })
        if hasattr(HistoricalBackfill, "_backfill_lock") and HistoricalBackfill._backfill_lock.locked():
            try:
                HistoricalBackfill._backfill_lock.release()
            except RuntimeError:
                pass
    except ImportError:
        pass
    yield


@pytest.fixture
def mock_live_feed(mocker):
    mocker.patch("LiveFeedManager.LiveFeedManager.is_running", return_value=True)
    mocker.patch("LiveFeedManager.LiveFeedManager.get_last_update_time", return_value="2026-01-01 12:00:00")
    mocker.patch("LiveFeedManager.LiveFeedManager.get_session_stats", return_value={"tickers": 10})
