import os
import sys
import json
import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

if getattr(sys, 'frozen', False):
    BUNDLE_DIR = getattr(sys, '_MEIPASS')
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = os.path.abspath(".")
    BASE_DIR = os.path.abspath(".")

APP_NAME: str = "Horus Analytics"
APP_VERSION: str = "1.0.0"

class AppSettings:
    APP_NAME: str = APP_NAME
    APP_VERSION: str = APP_VERSION

    @staticmethod
    def get_resource_path(relative_path):
        return os.path.join(BUNDLE_DIR, relative_path)

    @staticmethod
    def get_persistent_path(relative_path):
        return os.path.join(BASE_DIR, relative_path)

    def __init__(self):
        self.APP_NAME = APP_NAME
        self.APP_VERSION = APP_VERSION
        caller_env = dict(os.environ)
        load_dotenv(self.get_resource_path(".env"))
        load_dotenv(self.get_persistent_path(".env"), override=True)
        os.environ.update(caller_env)
        # Defaults
        DEFAULT_HISTORY_DIR = r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\History\CASE"
        DEFAULT_INTRADAY_DIR = r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\Intraday\CASE"
        DEFAULT_METASTOCK_DAT_HISTORY_DIR = DEFAULT_HISTORY_DIR
        DEFAULT_METASTOCK_DAT_INTRADAY_DIR = DEFAULT_INTRADAY_DIR

        # Integrate and compute values
        self.DATA_SOURCE_TYPE = "PARQUET"
        self.METASTOCK_HISTORY_FOLDER = os.getenv("METASTOCK_HISTORY_DIR", DEFAULT_HISTORY_DIR)
        self.METASTOCK_INTRADAY_FOLDER = os.getenv("METASTOCK_INTRADAY_DIR", DEFAULT_INTRADAY_DIR)
        self.METASTOCK_DAT_HISTORY_FOLDER = os.getenv("METASTOCK_DAT_HISTORY_DIR", DEFAULT_METASTOCK_DAT_HISTORY_DIR)
        self.METASTOCK_DAT_INTRADAY_FOLDER = os.getenv("METASTOCK_DAT_INTRADAY_DIR", DEFAULT_METASTOCK_DAT_INTRADAY_DIR)
        
        self.VALID_LOCAL_PROVIDERS = {"AUTO", "CSV", "MUBASHER_DB", "DIRECTFN", "METASTOCK_DAT"}
        self.LOCAL_FEED_PROVIDER = os.getenv("LOCAL_FEED_PROVIDER", "AUTO").strip().upper()
        if self.LOCAL_FEED_PROVIDER not in self.VALID_LOCAL_PROVIDERS: self.LOCAL_FEED_PROVIDER = "AUTO"
        
        self.LOCAL_HISTORY_PROVIDER = os.getenv("LOCAL_HISTORY_PROVIDER", "MUBASHER_DB").strip().upper()
        if self.LOCAL_HISTORY_PROVIDER not in self.VALID_LOCAL_PROVIDERS: self.LOCAL_HISTORY_PROVIDER = "MUBASHER_DB"
        
        self.LOCAL_INTRADAY_PROVIDER = os.getenv("LOCAL_INTRADAY_PROVIDER", "MUBASHER_DB").strip().upper()
        if self.LOCAL_INTRADAY_PROVIDER not in self.VALID_LOCAL_PROVIDERS: self.LOCAL_INTRADAY_PROVIDER = "MUBASHER_DB"
        
        self.LOCAL_INTRADAY_DB_STALE_MINUTES = int(os.getenv("LOCAL_INTRADAY_DB_STALE_MINUTES", "20"))
        self.LOCAL_INTRADAY_ALLOW_STALE_FALLBACK = os.getenv("LOCAL_INTRADAY_ALLOW_STALE_FALLBACK", "1").strip().lower() in {"1", "true", "TRUE", "yes", "on"}
        
        self.LOCAL_TICKS_PROVIDER = os.getenv("LOCAL_TICKS_PROVIDER", "MUBASHER_DB").strip().upper()
        if self.LOCAL_TICKS_PROVIDER not in {"AUTO", "MUBASHER_DB"}: self.LOCAL_TICKS_PROVIDER = "MUBASHER_DB"
        
        self.DIRECTFN_INTRADAY_LOOKBACK_DAYS = int(os.getenv("DIRECTFN_INTRADAY_LOOKBACK_DAYS", "5"))
        self.METASTOCK_DAT_INTRADAY_LOOKBACK_DAYS = int(os.getenv("METASTOCK_DAT_INTRADAY_LOOKBACK_DAYS", "5"))
        self.MUBASHER_ROOT_DIR = os.getenv("MUBASHER_ROOT_DIR", r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt")
        self.MUBASHER_USER_ID = os.getenv("MUBASHER_USER_ID", "").strip()
        self.MUBASHER_REALTIME_OVERLAY_ENABLED = os.getenv("MUBASHER_REALTIME_OVERLAY_ENABLED", "0").strip().lower() in {"1", "true", "TRUE", "yes", "on"}
        self.MUBASHER_FEED_DAEMON_ENABLED = os.getenv("MUBASHER_FEED_DAEMON_ENABLED", "0").strip().lower() in {"1", "true", "TRUE", "yes", "on"}
        
        self.TICK_SYNC_ENABLED = os.getenv("TICK_SYNC_ENABLED", "1").strip() in {"1", "true", "TRUE", "yes"}
        self.INTRADAY_PARQUET_MIRROR = os.getenv("INTRADAY_PARQUET_MIRROR", "0").strip() in {"1", "true", "TRUE", "yes"}
        self.INTRADAY_STORE_BOOTSTRAP_MISSING = os.getenv("INTRADAY_STORE_BOOTSTRAP_MISSING", "1").strip() in {"1", "true", "TRUE", "yes"}
        
        self.FRESHNESS_MIN_HISTORY_RATIO = float(os.getenv("FRESHNESS_MIN_HISTORY_RATIO", "0.90"))
        self.FRESHNESS_MIN_INTRADAY_RATIO = float(os.getenv("FRESHNESS_MIN_INTRADAY_RATIO", "0.65"))
        self.FRESHNESS_HISTORY_CACHE_TTL_SEC = int(os.getenv("FRESHNESS_HISTORY_CACHE_TTL_SEC", "60"))
        self.FRESHNESS_REVIEW_ACTIVE_DAYS = int(os.getenv("FRESHNESS_REVIEW_ACTIVE_DAYS", "2"))
        self.PIPELINE_STALE_SOUND_ALERT_ENABLED = os.getenv("PIPELINE_STALE_SOUND_ALERT_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
        self.PIPELINE_STALE_SOUND_ALERT_COOLDOWN_SEC = max(0, int(os.getenv("PIPELINE_STALE_SOUND_ALERT_COOLDOWN_SEC", "600") or 600))

        # Session auto-detection depends on the active market schedule.
        # EGX Session Timeline:
        # 10:00 - 14:15: Continuous Trading Session (Continuous order matching)
        # 14:15 - 14:25: Closing Auction & Adjust Session (Order collection & price calculation)
        # 14:25 - 14:30: Trade-at-Close Session (Trades at fixed closing price)
        # 14:30+: Market Closed
        self.MARKET_START_HHMM_NORMAL = os.getenv("MARKET_START_HHMM_NORMAL", "1000").strip()
        self.CONTINUOUS_TRADING_END_HHMM_NORMAL = os.getenv("CONTINUOUS_TRADING_END_HHMM_NORMAL", "1415").strip()
        self.CLOSING_AUCTION_END_HHMM_NORMAL = os.getenv("CLOSING_AUCTION_END_HHMM_NORMAL", "1425").strip()
        self.MARKET_END_HHMM_NORMAL = os.getenv("MARKET_END_HHMM_NORMAL", "1430").strip()
        self.MARKET_START_HHMM_RAMADAN = os.getenv("MARKET_START_HHMM_RAMADAN", "1000").strip()
        self.CONTINUOUS_TRADING_END_HHMM_RAMADAN = os.getenv("CONTINUOUS_TRADING_END_HHMM_RAMADAN", "1315").strip()
        self.CLOSING_AUCTION_END_HHMM_RAMADAN = os.getenv("CLOSING_AUCTION_END_HHMM_RAMADAN", "1325").strip()
        self.MARKET_END_HHMM_RAMADAN = os.getenv("MARKET_END_HHMM_RAMADAN", "1330").strip()
        self.RAMADAN_MODE = os.getenv("RAMADAN_MODE", "0").strip().lower() in {"1", "true", "yes"}
        
        self.PRE_CLOSE_OFFSET_MINS = int(os.getenv("PRE_CLOSE_OFFSET_MINS", "20"))
        self.DAILY_SIGNAL_OFFSET_MINS = int(os.getenv("DAILY_SIGNAL_OFFSET_MINS", "30"))
        self.INTRADAY_INTERVAL_MINS = int(os.getenv("INTRADAY_INTERVAL_MINS", "5"))
        self.MARKET_WEEKEND = [4, 5]
        
        sess_mode_env = os.getenv("SESSION_MODE", "").strip().upper()
        if sess_mode_env in {"LIVE", "ANALYSIS"}:
            # Explicit env var override
            self.SESSION_MODE = sess_mode_env
        else:
            # Auto-detect from current time and market schedule
            from core.session_mode import compute_session_mode
            self.SESSION_MODE = compute_session_mode(
                now=datetime.datetime.now(),
                market_start_hhmm=self._active_market_start(),
                market_end_hhmm=self._active_market_end(),
                weekend_days=self.MARKET_WEEKEND,
                pre_market_minutes=30,
            )
        
        self.TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "1").strip().lower() in {"1", "true", "yes"}
        self.DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.DISCORD_ENABLED = os.getenv("DISCORD_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
        
        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
        self.REDIS_DB = int(os.getenv("REDIS_DB", "0"))
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
        self.REDIS_ENABLED = os.getenv("REDIS_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}

        # Data Path Unification
        self.DATA_ROOT = self._resolve_data_root()
        self.REPORTS_DIR = os.path.join(self.DATA_ROOT, "reports")
        self.LOGS_DIR = os.path.join(self.DATA_ROOT, "logs")
        self.AUDITS_DIR = os.path.join(self.DATA_ROOT, "audits")
        
        self.DATA_FOLDER = self.METASTOCK_HISTORY_FOLDER
        self.SETTINGS_FILE = os.getenv("HORUS_SETTINGS_FILE", "").strip() or self.get_persistent_path("settings.json")
        self.EXCLUSIONS_FILE = os.path.join(self.DATA_ROOT, "EGX", "exclusions.json")
        
        self.LOOKBACK = 30
        self.VOL_SPIKE = 1.5
        self.MOMENTUM = 2.5
        self.RSI_MIN = 55
        self.RSI_MAX = 85
        self.SL_PCT = 2.5
        self.TP1_PCT = 4.0
        self.MIN_TURNOVER = 2000000
        self.PRICE_PRECISION = 4
        
        self.TRICKSTER_RSI_MAX = 30.0
        self.TRICKSTER_REL_VOL_MIN = 1.2
        self.TRICKSTER_STRETCH_ATR = 2.0
        
        self.COMMISSION_PCT = float(os.getenv("COMMISSION_PCT", "0.15"))
        self.SLIPPAGE_PCT = float(os.getenv("SLIPPAGE_PCT", "0.10"))
        
        self.MAX_POSITIONS = 10
        self.REPLAY_ENTRY_CUTOFF_HHMM = os.getenv("REPLAY_ENTRY_CUTOFF_HHMM", "12:30").strip()
        self.REPLAY_MAX_CONCURRENT_POSITIONS = int(os.getenv("REPLAY_MAX_CONCURRENT_POSITIONS", "5"))
        self.STARTING_CAPITAL = float(os.getenv("ACCOUNT_BALANCE", 0))
        self.ACCOUNT_BALANCE = float(os.getenv("ACCOUNT_BALANCE", 0))
        self.ACCOUNT_BALANCE_USD = float(os.getenv("ACCOUNT_BALANCE_USD", 0))
        self.USD_EGP_RATE = float(os.getenv("USD_EGP_RATE", "48.5"))
        self.USD_DEVALUATION_DAILY_SLOPE = float(os.getenv("USD_DEVALUATION_DAILY_SLOPE", "0.08"))
        self.PPP_MIN_ALPHA_PREMIUM = float(os.getenv("PPP_MIN_ALPHA_PREMIUM", "1.0"))
        self.RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", 2.0))
        self.MIN_RISK_REWARD = max(0.0, float(os.getenv("MIN_RISK_REWARD", "1.0") or 1.0))
        self.MIN_SIGNAL_SCORE = max(0.0, min(float(os.getenv("MIN_SIGNAL_SCORE", "0") or 0), 10.0))
        self.MIN_SIGNAL_CONFIDENCE = max(0.0, min(float(os.getenv("MIN_SIGNAL_CONFIDENCE", "0") or 0), 100.0))
        self.MAX_DAILY_TRADES = max(1, int(os.getenv("MAX_DAILY_TRADES", "3") or 3))
        self.MAX_PORTFOLIO_HEAT = max(0.01, float(os.getenv("MAX_PORTFOLIO_HEAT", "6.0") or 6.0))
        self.PENDING_ENTRY_MAX_GAP_PCT = max(0.01, float(os.getenv("PENDING_ENTRY_MAX_GAP_PCT", "1.5") or 1.5))
        self.TELEGRAM_SUMMARY_MAX_SIGNALS = max(1, int(os.getenv("TELEGRAM_SUMMARY_MAX_SIGNALS", "10") or 10))
        self.AUTO_TRADE_TARGET_PORTFOLIO_NAME = os.getenv("AUTO_TRADE_TARGET_PORTFOLIO_NAME", "").strip() or None
        
        self.TRAILING_STOP_ENABLED = True
        self.TRAILING_STOP_TYPE = "ATR"
        self.TRAILING_STOP_VALUE = 2.0
        self.MAINTENANCE_MODE = False
        self.REGIME_FILTER_ENABLED = False
        self.REGIME_MODE = "AUTO"
        self.MIN_SCORE_CAUTIOUS = 8
        self.SECTOR_LIMIT_ENABLED = False
        self.MAX_PER_SECTOR = 2
        
        self.AUTO_TRADE_ENABLED = True
        self.SIGNAL_AUTO_EXECUTION_ENABLED = os.getenv("SIGNAL_AUTO_EXECUTION_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
        self.LIVE_ARM_GUARD_ENABLED = os.getenv("LIVE_ARM_GUARD_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
        self.LIVE_EXECUTION_ARMED = False
        self.LIVE_EXECUTION_ARMED_ON: str | None = None
        self.LIVE_REQUIRE_NONZERO_COSTS = os.getenv("LIVE_REQUIRE_NONZERO_COSTS", "1").strip().lower() in {"1", "true", "yes", "on"}
        self.LIVE_MAX_RISK_PER_TRADE_PCT = float(os.getenv("LIVE_MAX_RISK_PER_TRADE_PCT", "2.0"))
        self.LIVE_MAX_DAILY_LOSS_PCT = float(os.getenv("LIVE_MAX_DAILY_LOSS_PCT", "3.0"))
        self.LIVE_MAX_WEEKLY_LOSS_PCT = float(os.getenv("LIVE_MAX_WEEKLY_LOSS_PCT", "6.0"))
        self.LIVE_MAX_DRAWDOWN_PCT = float(os.getenv("LIVE_MAX_DRAWDOWN_PCT", "20.0"))
        self.LIVE_MAX_STRESS_DRAWDOWN_PCT = float(os.getenv("LIVE_MAX_STRESS_DRAWDOWN_PCT", "35.0"))
        self.LIVE_MAX_CONSECUTIVE_LOSSES = int(os.getenv("LIVE_MAX_CONSECUTIVE_LOSSES", "4"))
        self.LIVE_LOSS_COOLDOWN_MINUTES = float(os.getenv("LIVE_LOSS_COOLDOWN_MINUTES", "60.0"))
        self.LIVE_MAX_CRISIS_CORRELATION = float(os.getenv("LIVE_MAX_CRISIS_CORRELATION", "0.85"))
        self.LIVE_MAX_LIQUIDITY_EXIT_PCT = float(os.getenv("LIVE_MAX_LIQUIDITY_EXIT_PCT", "5.0"))
        self.LIVE_REQUIRE_DAILY_PLAN_CONFIRMATION = os.getenv("LIVE_REQUIRE_DAILY_PLAN_CONFIRMATION", "1").strip().lower() in {"1", "true", "yes", "on"}
        self.LIVE_MAX_MANUAL_OVERRIDES_PER_DAY = int(os.getenv("LIVE_MAX_MANUAL_OVERRIDES_PER_DAY", "3"))
        self.HEAT_PROTECTION_ENABLED = True
        self.USE_ATR_EXITS = True
        self.ATR_TP_MULTIPLIER = 2.0
        self.ATR_SL_MULTIPLIER = 1.5
        self.PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS = 15
        self.PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES = True
        self.PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT = 15
        self.PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT = 10
        self.PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT = 8
        self.PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT = 3.0
        self.PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT = 1.0
        self.PORTFOLIO_MGMT_TP2_PCT = 4.0
        self.PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN = 3500
        
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8581083386:AAFI-W_V1llOmzzhMpITMGJV_QVPFgIPlUY").strip()
        self.CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1003973409664").strip()
        
        # Test Telegram bot (used exclusively by Market Replay & Dry Run)
        self.TELEGRAM_TEST_BOT_TOKEN = os.getenv("TELEGRAM_TEST_BOT_TOKEN", "8714890040:AAH3Q0hTaPCj_5dVd3jA5AlRtcBnvGvDb74").strip()
        self.TELEGRAM_TEST_CHAT_ID = os.getenv("TELEGRAM_TEST_CHAT_ID", "7503995235").strip()
        
        self.TELEGRAM_AUTO_BROADCAST_INTRADAY = os.getenv("TELEGRAM_AUTO_BROADCAST_INTRADAY", "1").strip().lower() in {"1", "true", "yes"}
        self.TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS = os.getenv("TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS", "0").strip().lower() in {"1", "true", "yes"}
        self.TELEGRAM_AUTO_BROADCAST_DAILY = os.getenv("TELEGRAM_AUTO_BROADCAST_DAILY", "1").strip().lower() in {"1", "true", "yes"}
        self.TELEGRAM_AUTO_BROADCAST_HORUS_EYE = os.getenv("TELEGRAM_AUTO_BROADCAST_HORUS_EYE", "1").strip().lower() in {"1", "true", "yes"}
        self.TELEGRAM_AUTO_BROADCAST_AI_REPORT = os.getenv("TELEGRAM_AUTO_BROADCAST_AI_REPORT", "1").strip().lower() in {"1", "true", "yes"}
        self.TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT = os.getenv("TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT", "1").strip().lower() in {"1", "true", "yes"}
        self.TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT = os.getenv("TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT", "1").strip().lower() in {"1", "true", "yes"}
        self.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL = self._normalize_main_channel_signal_level(
            os.getenv("TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_3")
        )
        self.TELEGRAM_REPORT_LANGUAGE = os.getenv("TELEGRAM_REPORT_LANGUAGE", "EN").strip().upper() or "EN"
        if self.TELEGRAM_REPORT_LANGUAGE not in {"EN", "AR"}:
            self.TELEGRAM_REPORT_LANGUAGE = "EN"
        self.SIGNAL_REPEAT_COOLDOWN_HOURS = max(
            0.0,
            float(os.getenv("SIGNAL_REPEAT_COOLDOWN_HOURS", "4.0") or 4.0),
        )
        
        self.ENABLE_INTRADAY_ALERTS = self.TELEGRAM_AUTO_BROADCAST_INTRADAY
        
        self.OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://10.168.183.175:11434").strip().rstrip("/") or "http://10.168.183.175:11434"
        self.AI_REPORT_OLLAMA_MODEL = os.getenv("AI_REPORT_OLLAMA_MODEL", "gemma4:31b-cloud").strip() or "gemma4:31b-cloud"
        self.AI_REPORT_OLLAMA_TIMEOUT_SEC = int(os.getenv("AI_REPORT_OLLAMA_TIMEOUT_SEC", "300"))
        self.OLLAMA_CONTEXT_LENGTH = int(os.getenv("OLLAMA_CONTEXT_LENGTH", "8192"))
        self.AI_REPORT_OLLAMA_NUM_CTX = int(
            os.getenv("AI_REPORT_OLLAMA_NUM_CTX", str(self.OLLAMA_CONTEXT_LENGTH))
        )
        self.PINE_IMPORT_TRANSLATION_PROVIDER = os.getenv("PINE_IMPORT_TRANSLATION_PROVIDER", "LOCAL").strip().upper() or "LOCAL"
        if self.PINE_IMPORT_TRANSLATION_PROVIDER not in {"LOCAL", "OLLAMA"}:
            self.PINE_IMPORT_TRANSLATION_PROVIDER = "LOCAL"
        
        self.WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
        self.WEBHOOK_ENABLED = os.getenv("WEBHOOK_ENABLED", "0").strip().lower() in {"1", "true", "yes"}

        try:
            self.HISTORICAL_BACKFILL_TRADING_DAYS = max(
                1,
                min(int(os.getenv("HISTORICAL_BACKFILL_TRADING_DAYS", "252")), 365),
            )
        except ValueError:
            self.HISTORICAL_BACKFILL_TRADING_DAYS = 252
        self.HISTORICAL_BACKFILL_SIGNAL_LANES = os.getenv("HISTORICAL_BACKFILL_SIGNAL_LANES", "BOTH").strip().upper() or "BOTH"
        if self.HISTORICAL_BACKFILL_SIGNAL_LANES not in {"SWING", "INTRADAY", "BOTH"}:
            self.HISTORICAL_BACKFILL_SIGNAL_LANES = "BOTH"
        
        # Security
        self.API_KEY = os.getenv("API_KEY", "").strip()

        self.AI_REPORT_PROVIDER = "OLLAMA"

        self._refresh_market_times()
        self.load_settings()

    def _resolve_data_root(self) -> str:
        """
        Resolve the data root path for the current runtime.

        Source-mode runs should stay on the workspace-relative ``data`` folder so
        tests and local development can safely chdir into temp roots. Packaged
        runs should use the persistent sibling ``data`` directory next to the
        executable. ``DATA_ROOT_OVERRIDE`` always wins and does not need to
        pre-exist because callers create directories lazily.
        """
        env_root = os.getenv("DATA_ROOT_OVERRIDE")
        if env_root:
            return env_root

        if getattr(sys, "frozen", False):
            return os.path.join(BASE_DIR, "data")

        return "data"

    def _active_market_start(self) -> str:
        return self.MARKET_START_HHMM_RAMADAN if self.RAMADAN_MODE else self.MARKET_START_HHMM_NORMAL

    def _active_continuous_end(self) -> str:
        return self.CONTINUOUS_TRADING_END_HHMM_RAMADAN if self.RAMADAN_MODE else self.CONTINUOUS_TRADING_END_HHMM_NORMAL

    def _active_auction_end(self) -> str:
        return self.CLOSING_AUCTION_END_HHMM_RAMADAN if self.RAMADAN_MODE else self.CLOSING_AUCTION_END_HHMM_NORMAL

    def _active_market_end(self) -> str:
        return self.MARKET_END_HHMM_RAMADAN if self.RAMADAN_MODE else self.MARKET_END_HHMM_NORMAL

    def _refresh_market_times(self):
        self.MARKET_START_TIME = self._hhmm_to_colon(self._active_market_start())
        self.CONTINUOUS_TRADING_END_TIME = self._hhmm_to_colon(self._active_continuous_end())
        self.CLOSING_AUCTION_END_TIME = self._hhmm_to_colon(self._active_auction_end())
        self.MARKET_END_TIME = self._hhmm_to_colon(self._active_market_end())

    @staticmethod
    def _hhmm_to_colon(hhmm: str) -> str:
        hhmm = hhmm.strip().zfill(4)
        return f"{hhmm[:2]}:{hhmm[2:]}"

    def get_market_open_hour_minute(self) -> tuple[int, int]:
        hhmm = self._active_market_start().zfill(4)
        return int(hhmm[:2]), int(hhmm[2:])

    def get_continuous_trading_end_hour_minute(self) -> tuple[int, int]:
        hhmm = self._active_continuous_end().zfill(4)
        return int(hhmm[:2]), int(hhmm[2:])

    def get_closing_auction_end_hour_minute(self) -> tuple[int, int]:
        hhmm = self._active_auction_end().zfill(4)
        return int(hhmm[:2]), int(hhmm[2:])

    def get_market_close_hour_minute(self) -> tuple[int, int]:
        hhmm = self._active_market_end().zfill(4)
        return int(hhmm[:2]), int(hhmm[2:])

    def get_market_session_phase(self, ref_dt: datetime.datetime | None = None) -> str:
        """
        Returns the current EGX market session phase:
        - "CLOSED": Outside market trading days/hours, weekend, or holiday
        - "PRE_MARKET": On a trading day before market open (< 10:00)
        - "CONTINUOUS_TRADING": 10:00 - 14:15 (continuous order matching in real-time)
        - "CLOSING_AUCTION": 14:15 - 14:25 (closing price discovery, continuous matching paused)
        - "TRADE_AT_CLOSE": 14:25 - 14:30 (executions exclusively at fixed closing price)
        """
        from core import TimeUtils
        if getattr(TimeUtils, '_MARKET_OVERRIDE', False):
            return "CONTINUOUS_TRADING"
        now = ref_dt or TimeUtils.now()
        current_time = now.strftime("%H:%M")
        start = self.MARKET_START_TIME
        cont_end = self.CONTINUOUS_TRADING_END_TIME
        auct_end = self.CLOSING_AUCTION_END_TIME
        mkt_end = self.MARKET_END_TIME

        if ref_dt is not None:
            if now.weekday() in self.MARKET_WEEKEND or self._is_db_holiday(now.date()):
                return "CLOSED"
            if current_time < start:
                return "PRE_MARKET"
            elif start <= current_time < cont_end:
                return "CONTINUOUS_TRADING"
            elif cont_end <= current_time < auct_end:
                return "CLOSING_AUCTION"
            elif auct_end <= current_time <= mkt_end:
                return "TRADE_AT_CLOSE"
            else:
                if self.is_market_open():
                    return "CONTINUOUS_TRADING"
                return "CLOSED"

        if not self.is_market_open():
            if (
                now.weekday() not in self.MARKET_WEEKEND
                and not self._is_db_holiday(now.date())
                and current_time < start
            ):
                return "PRE_MARKET"
            return "CLOSED"

        if current_time < start:
            return "PRE_MARKET"
        elif start <= current_time < cont_end:
            return "CONTINUOUS_TRADING"
        elif cont_end <= current_time < auct_end:
            return "CLOSING_AUCTION"
        elif auct_end <= current_time <= mkt_end:
            return "TRADE_AT_CLOSE"
        else:
            return "CONTINUOUS_TRADING"

    def is_continuous_trading(self, ref_dt: datetime.datetime | None = None) -> bool:
        """True if and only if market is in active Continuous Trading (10:00 - 14:15)."""
        return self.get_market_session_phase(ref_dt) == "CONTINUOUS_TRADING"

    def is_closing_auction(self, ref_dt: datetime.datetime | None = None) -> bool:
        """True if market is in Closing Auction & Adjust session (14:15 - 14:25)."""
        return self.get_market_session_phase(ref_dt) == "CLOSING_AUCTION"

    def is_trade_at_close(self, ref_dt: datetime.datetime | None = None) -> bool:
        """True if market is in Trade-at-Close session (14:25 - 14:30)."""
        return self.get_market_session_phase(ref_dt) == "TRADE_AT_CLOSE"

    def is_market_open(self):
        from core import TimeUtils
        # Replay/DryRun mode forces market open so the full pipeline can run
        if getattr(TimeUtils, '_MARKET_OVERRIDE', False):
            return True
        now = TimeUtils.now()
        if now.weekday() in self.MARKET_WEEKEND: return False
        if self._is_db_holiday(now.date()): return False
        
        current_time = now.strftime("%H:%M")
        start = self.MARKET_START_TIME
        end = self.MARKET_END_TIME
        return start <= current_time <= end

    def get_last_completed_market_day(self, ref_dt=None):
        from core import TimeUtils
        now = ref_dt or TimeUtils.now()
        current_date = now.date()
        current_time = now.strftime("%H:%M")

        if current_date.weekday() in self.MARKET_WEEKEND:
            candidate = current_date
        elif current_time > self.MARKET_END_TIME:
            candidate = current_date
        else:
            candidate = current_date - datetime.timedelta(days=1)

        while candidate.weekday() in self.MARKET_WEEKEND or self._is_db_holiday(candidate):
            candidate -= datetime.timedelta(days=1)
        return candidate

    def is_recent_trading_day(self, check_date: datetime.date, max_trading_days: int = 1, ref_dt=None) -> bool:
        """Check if check_date is within max_trading_days trading days of today/ref_dt.
        Skips Friday/Saturday weekends and DB registered holidays.
        """
        if check_date is None:
            return False
        from core import TimeUtils
        now = ref_dt or TimeUtils.now()
        today_date = now.date()
        if check_date >= today_date:
            return True

        curr = today_date
        valid_days = {curr}
        days_found = 0
        max_lookback = 30  # Safety: never look back more than 30 calendar days
        iterations = 0
        while days_found < max_trading_days and iterations < max_lookback:
            curr -= datetime.timedelta(days=1)
            iterations += 1
            if curr.weekday() not in self.MARKET_WEEKEND and not self._is_db_holiday(curr):
                valid_days.add(curr)
                days_found += 1
        return check_date in valid_days

    def _is_db_holiday(self, check_date: datetime.date) -> bool:
        """Check if a date is registered as a holiday in the database."""
        try:
            from database import Holiday
            return Holiday.select().where(Holiday.date == check_date).exists()
        except Exception:
            # Fallback if DB is not available or model not yet created
            return False

    @staticmethod
    def _normalize_main_channel_signal_level(value) -> str:
        level = str(value or "none").strip().lower()
        aliases = {
            "": "none",
            "off": "none",
            "disabled": "none",
            "type1": "type_1",
            "type 1": "type_1",
            "type2": "type_2",
            "type 2": "type_2",
            "type3": "type_3",
            "type 3": "type_3",
        }
        level = aliases.get(level, level)
        if level not in {"none", "type_1", "type_2", "type_3"}:
            raise ValueError("TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL must be none, type_1, type_2, or type_3.")
        return level

    def update(self, new_settings: dict, *, persist: bool = True):
        for k, v in new_settings.items():
            if hasattr(self, k):
                if k == "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL":
                    setattr(self, k, self._normalize_main_channel_signal_level(v))
                    continue
                if k == "AUTO_TRADE_ENABLED":
                    requested = bool(v)
                    setattr(self, k, requested)
                    # Safety: disabling auto-trade always clears runtime live arming.
                    if not requested:
                        self.disarm_live_execution()
                    continue
                if k == "LIVE_ARM_GUARD_ENABLED":
                    requested = bool(v)
                    setattr(self, k, requested)
                    if requested:
                        self.disarm_live_execution()
                    continue
                if k == "HISTORICAL_BACKFILL_TRADING_DAYS":
                    try:
                        value = int(v)
                    except (TypeError, ValueError):
                        raise ValueError("Historical backfill trading days must be an integer between 1 and 365.")
                    setattr(self, k, max(1, min(value, 365)))
                    continue
                if k == "HISTORICAL_BACKFILL_SIGNAL_LANES":
                    value = str(v or "BOTH").strip().upper() or "BOTH"
                    if value not in {"SWING", "INTRADAY", "BOTH"}:
                        raise ValueError("Historical backfill signal lanes must be one of: SWING, INTRADAY, BOTH.")
                    setattr(self, k, value)
                    continue
                if k == "PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS":
                    try:
                        value = int(v)
                    except (TypeError, ValueError):
                        raise ValueError("Portfolio manager default include positions must be an integer between 1 and 100.")
                    setattr(self, k, max(1, min(value, 100)))
                    continue
                if k in {
                    "PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT",
                    "PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT",
                    "PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT",
                }:
                    try:
                        value = int(v)
                    except (TypeError, ValueError):
                        raise ValueError(f"{k} must be an integer between 1 and 100.")
                    setattr(self, k, max(1, min(value, 100)))
                    continue
                if k == "PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN":
                    try:
                        value = int(v)
                    except (TypeError, ValueError):
                        raise ValueError("Portfolio manager Telegram chunk size must be an integer between 500 and 4096.")
                    setattr(self, k, max(500, min(value, 4096)))
                    continue
                if k in {
                    "PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT",
                    "PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT",
                    "PORTFOLIO_MGMT_TP2_PCT",
                }:
                    try:
                        value = float(v)
                    except (TypeError, ValueError):
                        raise ValueError(f"{k} must be a numeric value greater than or equal to 0.")
                    setattr(self, k, max(0.0, value))
                    continue
                if k == "MIN_RISK_REWARD":
                    try:
                        value = float(v)
                    except (TypeError, ValueError):
                        raise ValueError("MIN_RISK_REWARD must be a numeric value greater than or equal to 0.")
                    setattr(self, k, max(0.0, value))
                    continue
                if k == "MIN_SIGNAL_SCORE":
                    try:
                        value = float(v)
                    except (TypeError, ValueError):
                        raise ValueError("MIN_SIGNAL_SCORE must be a numeric value between 0 and 10.")
                    if value < 0 or value > 10:
                        raise ValueError("MIN_SIGNAL_SCORE must be between 0 and 10.")
                    setattr(self, k, value)
                    continue
                if k == "MIN_SIGNAL_CONFIDENCE":
                    try:
                        value = float(v)
                    except (TypeError, ValueError):
                        raise ValueError("MIN_SIGNAL_CONFIDENCE must be a numeric value between 0 and 100.")
                    if value < 0 or value > 100:
                        raise ValueError("MIN_SIGNAL_CONFIDENCE must be between 0 and 100.")
                    setattr(self, k, value)
                    continue
                if k == "REPLAY_ENTRY_CUTOFF_HHMM":
                    val = str(v or "").strip().replace(":", "")
                    if not (len(val) == 4 and val.isdigit()):
                        raise ValueError("REPLAY_ENTRY_CUTOFF_HHMM must be in HH:MM or HHMM format.")
                    h, m = int(val[:2]), int(val[2:])
                    if h < 0 or h > 23 or m < 0 or m > 59:
                        raise ValueError("REPLAY_ENTRY_CUTOFF_HHMM must be a valid time.")
                    setattr(self, k, f"{h:02d}:{m:02d}")
                    continue
                if k == "REPLAY_MAX_CONCURRENT_POSITIONS":
                    try:
                        value = int(v)
                    except (TypeError, ValueError):
                        raise ValueError("REPLAY_MAX_CONCURRENT_POSITIONS must be an integer between 1 and 50.")
                    if value < 1 or value > 50:
                        raise ValueError("REPLAY_MAX_CONCURRENT_POSITIONS must be an integer between 1 and 50.")
                    setattr(self, k, value)
                    continue
                if k in {
                    "SL_PCT",
                    "COMMISSION_PCT",
                    "SLIPPAGE_PCT",
                    "MAX_PORTFOLIO_HEAT",
                    "PENDING_ENTRY_MAX_GAP_PCT",
                    "LIVE_MAX_RISK_PER_TRADE_PCT",
                    "LIVE_MAX_DAILY_LOSS_PCT",
                    "LIVE_MAX_WEEKLY_LOSS_PCT",
                    "LIVE_MAX_DRAWDOWN_PCT",
                    "LIVE_MAX_STRESS_DRAWDOWN_PCT",
                    "LIVE_LOSS_COOLDOWN_MINUTES",
                    "LIVE_MAX_CRISIS_CORRELATION",
                    "LIVE_MAX_LIQUIDITY_EXIT_PCT",
                    "USD_EGP_RATE",
                    "USD_DEVALUATION_DAILY_SLOPE",
                    "PPP_MIN_ALPHA_PREMIUM",
                }:
                    try:
                        value = float(v)
                    except (TypeError, ValueError):
                        raise ValueError(f"{k} must be a numeric value greater than 0.")
                    if value <= 0:
                        raise ValueError(f"{k} must be greater than 0.")
                    setattr(self, k, value)
                    continue
                if k == "MAX_DAILY_TRADES":
                    try:
                        value = int(v)
                    except (TypeError, ValueError):
                        raise ValueError("MAX_DAILY_TRADES must be an integer >= 1.")
                    if value < 1:
                        raise ValueError("MAX_DAILY_TRADES must be an integer >= 1.")
                    setattr(self, k, value)
                    continue
                if k == "LIVE_MAX_CONSECUTIVE_LOSSES":
                    try:
                        value = int(v)
                    except (TypeError, ValueError):
                        raise ValueError("LIVE_MAX_CONSECUTIVE_LOSSES must be an integer >= 1.")
                    if value < 1:
                        raise ValueError("LIVE_MAX_CONSECUTIVE_LOSSES must be an integer >= 1.")
                    setattr(self, k, value)
                    continue
                if k == "LIVE_MAX_MANUAL_OVERRIDES_PER_DAY":
                    try:
                        value = int(v)
                    except (TypeError, ValueError):
                        raise ValueError("LIVE_MAX_MANUAL_OVERRIDES_PER_DAY must be an integer >= 1.")
                    if value < 1:
                        raise ValueError("LIVE_MAX_MANUAL_OVERRIDES_PER_DAY must be an integer >= 1.")
                    setattr(self, k, value)
                    continue
                if k == "LOCAL_HISTORY_PROVIDER" and str(v).upper() not in self.VALID_LOCAL_PROVIDERS: continue
                if k == "LOCAL_INTRADAY_PROVIDER" and str(v).upper() not in self.VALID_LOCAL_PROVIDERS: continue
                if k == "LOCAL_TICKS_PROVIDER":
                    provider = str(v or "").strip().upper()
                    if provider not in {"AUTO", "MUBASHER_DB"}:
                        continue
                    setattr(self, k, provider)
                    continue
                if k == "LOCAL_INTRADAY_ALLOW_STALE_FALLBACK":
                    if isinstance(v, str):
                        value = v.strip().lower() in {"1", "true", "yes", "on"}
                    else:
                        value = bool(v)
                    setattr(self, k, value)
                    continue
                if k == "TICK_SYNC_ENABLED":
                    if isinstance(v, str):
                        value = v.strip().lower() in {"1", "true", "yes", "on"}
                    else:
                        value = bool(v)
                    setattr(self, k, value)
                    continue
                if k == "AI_REPORT_PROVIDER":
                    setattr(self, k, "OLLAMA")
                    continue
                if k == "PINE_IMPORT_TRANSLATION_PROVIDER":
                    provider = str(v).strip().upper()
                    setattr(self, k, provider if provider in {"LOCAL", "OLLAMA"} else "LOCAL")
                    continue
                if k == "TELEGRAM_REPORT_LANGUAGE":
                    language = str(v or "EN").strip().upper() or "EN"
                    if language not in {"EN", "AR"}:
                        raise ValueError("TELEGRAM_REPORT_LANGUAGE must be EN or AR.")
                    setattr(self, k, language)
                    continue
                setattr(self, k, v.strip() if isinstance(v, str) else v)
        
        self._refresh_market_times()
        if persist:
            self.save_settings("custom")
        return True

    def save_settings(self, preset_name="default"):
        saveable_keys = [
            'LOOKBACK', 'VOL_SPIKE', 'MOMENTUM', 'RSI_MIN', 'RSI_MAX', 'SL_PCT', 'TP1_PCT',
            'MIN_TURNOVER', 'TRICKSTER_RSI_MAX', 'TRICKSTER_REL_VOL_MIN', 'TRICKSTER_STRETCH_ATR',
            'MAX_POSITIONS', 'RISK_PER_TRADE', 'MIN_RISK_REWARD', 'MIN_SIGNAL_SCORE', 'MIN_SIGNAL_CONFIDENCE',
            'MAX_DAILY_TRADES', 'MAX_PORTFOLIO_HEAT', 'PENDING_ENTRY_MAX_GAP_PCT', 'TELEGRAM_SUMMARY_MAX_SIGNALS',
            'COMMISSION_PCT', 'SLIPPAGE_PCT', 'REPLAY_ENTRY_CUTOFF_HHMM', 'REPLAY_MAX_CONCURRENT_POSITIONS',
            'TRAILING_STOP_ENABLED', 'TRAILING_STOP_TYPE', 'TRAILING_STOP_VALUE',
            'REGIME_FILTER_ENABLED', 'REGIME_MODE', 'SECTOR_LIMIT_ENABLED', 'MAX_PER_SECTOR',
            'USE_ATR_EXITS', 'ATR_TP_MULTIPLIER', 'ATR_SL_MULTIPLIER', 'AUTO_TRADE_ENABLED',
            'SIGNAL_AUTO_EXECUTION_ENABLED', 'LIVE_ARM_GUARD_ENABLED',
            'HEAT_PROTECTION_ENABLED',
            'LIVE_REQUIRE_NONZERO_COSTS', 'LIVE_MAX_RISK_PER_TRADE_PCT', 'LIVE_MAX_DAILY_LOSS_PCT',
            'LIVE_MAX_WEEKLY_LOSS_PCT', 'LIVE_MAX_DRAWDOWN_PCT', 'LIVE_MAX_STRESS_DRAWDOWN_PCT',
            'LIVE_MAX_CONSECUTIVE_LOSSES', 'LIVE_LOSS_COOLDOWN_MINUTES', 'LIVE_MAX_CRISIS_CORRELATION',
            'LIVE_MAX_LIQUIDITY_EXIT_PCT', 'LIVE_REQUIRE_DAILY_PLAN_CONFIRMATION',
            'LIVE_MAX_MANUAL_OVERRIDES_PER_DAY',
            'PRE_CLOSE_OFFSET_MINS', 'DAILY_SIGNAL_OFFSET_MINS', 'INTRADAY_INTERVAL_MINS',
            'LOCAL_HISTORY_PROVIDER', 'LOCAL_INTRADAY_PROVIDER', 'LOCAL_INTRADAY_ALLOW_STALE_FALLBACK', 'LOCAL_TICKS_PROVIDER',
            'TICK_SYNC_ENABLED', 'TELEGRAM_TOKEN', 'CHAT_ID',
            'TELEGRAM_AUTO_BROADCAST_INTRADAY', 'TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS', 'TELEGRAM_AUTO_BROADCAST_DAILY',
            'TELEGRAM_AUTO_BROADCAST_HORUS_EYE', 'TELEGRAM_AUTO_BROADCAST_AI_REPORT',
            'TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT', 'TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT',
            'TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL', 'TELEGRAM_REPORT_LANGUAGE',
            'SIGNAL_REPEAT_COOLDOWN_HOURS',
            'PIPELINE_STALE_SOUND_ALERT_ENABLED', 'PIPELINE_STALE_SOUND_ALERT_COOLDOWN_SEC',
            'ENABLE_INTRADAY_ALERTS', 'MARKET_START_HHMM_NORMAL', 'MARKET_END_HHMM_NORMAL',
            'MARKET_START_HHMM_RAMADAN', 'MARKET_END_HHMM_RAMADAN', 'RAMADAN_MODE',
            'HISTORICAL_BACKFILL_TRADING_DAYS',
            'HISTORICAL_BACKFILL_SIGNAL_LANES',
            'PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS', 'PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES',
            'PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT', 'PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT',
            'PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT',
            'PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT', 'PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT',
            'PORTFOLIO_MGMT_TP2_PCT', 'PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN',
            'OLLAMA_API_KEY',
            'OLLAMA_BASE_URL', 'AI_REPORT_OLLAMA_MODEL', 'AI_REPORT_OLLAMA_TIMEOUT_SEC',
            'OLLAMA_CONTEXT_LENGTH', 'AI_REPORT_OLLAMA_NUM_CTX',
            'PINE_IMPORT_TRANSLATION_PROVIDER',
            'ACCOUNT_BALANCE', 'ACCOUNT_BALANCE_USD', 'API_KEY',
            'WEBHOOK_URL', 'WEBHOOK_ENABLED',
            'TELEGRAM_TEST_BOT_TOKEN', 'TELEGRAM_TEST_CHAT_ID',
        ]
        
        settings_dict = {k: getattr(self, k) for k in saveable_keys if hasattr(self, k)}
        settings_dict['preset_name'] = preset_name
        
        all_presets = {}
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r') as f:
                    all_presets = json.load(f)
            except: pass
            
        all_presets[preset_name] = settings_dict
        try:
            settings_dir = os.path.dirname(os.path.abspath(self.SETTINGS_FILE))
            if settings_dir:
                os.makedirs(settings_dir, exist_ok=True)
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(all_presets, f, indent=2)
            return True
        except:
            return False

    def load_settings(self, preset_name="custom"):
        loaded = False
        defaults_file = self.get_resource_path(os.path.join("config", "settings.defaults.json"))
        legacy_defaults_file = self.get_resource_path("settings.json")

        def load_preset(path, requested_preset):
            if not os.path.exists(path):
                return False
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    all_presets = json.load(handle)
                selected = requested_preset
                if selected not in all_presets:
                    selected = "default"
                if selected not in all_presets:
                    return False
                self.update(all_presets[selected], persist=False)
                return True
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                return False

        if os.path.exists(defaults_file):
            loaded = load_preset(defaults_file, "default")
        elif os.path.abspath(legacy_defaults_file) != os.path.abspath(self.SETTINGS_FILE):
            loaded = load_preset(legacy_defaults_file, "default")

        if os.path.exists(self.SETTINGS_FILE):
            loaded = load_preset(self.SETTINGS_FILE, preset_name) or loaded

        return loaded

    def get_saved_presets(self):
        target_file = self.SETTINGS_FILE
        if not os.path.exists(target_file):
            bundle_settings = self.get_resource_path("settings.json")
            if os.path.exists(bundle_settings):
                target_file = bundle_settings
            else:
                return []
        try:
            with open(target_file, 'r') as f:
                return list(json.load(f).keys())
        except:
            return []

    def calculate_kelly_size(self, win_rate, win_loss_ratio, fraction=0.5):
        if win_loss_ratio <= 0: return 0
        kelly_f = win_rate - (1 - win_rate) / win_loss_ratio
        return max(0, kelly_f * fraction)

    def calculate_vol_targeted_size(self, entry_price, atr_pct, target_risk_pct=0.25):
        if atr_pct <= 0 or entry_price <= 0: return 0
        account_risk = self.ACCOUNT_BALANCE * (target_risk_pct / 100)
        risk_per_share = entry_price * (atr_pct / 100)
        return int(account_risk / risk_per_share)

    def calculate_position_size(self, entry_price, stop_loss_price, account_balance=None, risk_pct=None, max_position_pct=100, ticker=None, atr_pct=None):
        acc_bal = account_balance if account_balance is not None else self.ACCOUNT_BALANCE
        r_pct = risk_pct if risk_pct is not None else self.RISK_PER_TRADE
        
        if atr_pct is not None:
             vol_shares = self.calculate_vol_targeted_size(entry_price, atr_pct)
             if vol_shares > 0:
                  max_shares_by_account = int((acc_bal * (max_position_pct / 100)) / entry_price)
                  shares = min(vol_shares, max_shares_by_account)
                  return {
                      'shares': shares,
                      'position_value': round(float(shares * entry_price), 2),
                      'risk_amount': round(float(acc_bal * (r_pct / 100)), 2),
                      'method': 'VOL_TARGETING'
                  }

        risk_amount = acc_bal * (r_pct / 100)
        risk_per_share = abs(entry_price - stop_loss_price)
        
        if risk_per_share <= 0 or entry_price <= 0:
            return {'shares': 0, 'position_value': 0, 'risk_amount': 0, 'capped': False}
            
        shares_by_risk = int(risk_amount / risk_per_share)
        max_position_value = acc_bal * (max_position_pct / 100)
        max_shares_by_account = int(max_position_value / entry_price)
        
        shares = min(shares_by_risk, max_shares_by_account)
        position_value = shares * entry_price
        actual_risk = shares * risk_per_share
        
        return {
            'shares': shares,
            'position_value': round(float(position_value), 2),
            'risk_amount': round(float(risk_amount), 2),
            'actual_risk': round(float(actual_risk), 2),
            'risk_per_share': round(float(risk_per_share), 2),
            'capped': shares < shares_by_risk,
            'method': 'FIXED_FRACTIONAL'
        }

    def arm_live_execution(self, armed_on=None):
        if armed_on is None:
            armed_on = datetime.date.today()
        self.LIVE_EXECUTION_ARMED = True
        self.LIVE_EXECUTION_ARMED_ON = str(armed_on)

    def disarm_live_execution(self):
        self.LIVE_EXECUTION_ARMED = False
        self.LIVE_EXECUTION_ARMED_ON = None

    def is_live_execution_armed(self, today_value=None) -> bool:
        if not bool(getattr(self, "AUTO_TRADE_ENABLED", False)):
            return False
        if not self.LIVE_ARM_GUARD_ENABLED:
            return True
        if not self.LIVE_EXECUTION_ARMED:
            return False
        if today_value is None:
            today_value = datetime.date.today()
        today_str = str(today_value)
        if self.LIVE_EXECUTION_ARMED_ON != today_str:
            self.disarm_live_execution()
            return False
        return True

settings = AppSettings()

def init_app_settings():
    """Initializes app configuration from custom presets."""
    settings.load_settings("custom")
    # We also trigger exclusions load to mimic legacy behavior
    from core.exclusions import get_all_exclusions
    get_all_exclusions()
