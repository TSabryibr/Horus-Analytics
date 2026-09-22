from core.settings import settings
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
import os
import logging
import json
import datetime
from pathlib import Path

from core import TelegramBot_Alerts
from core import ReportGenerator
from core import TimeUtils
from peewee import fn
from database import Position, Trade, Signal, SignalRecommendation, SignalOutcome, TickerStrategyMetrics
from core.exclusions import normalize_ticker, purge_blacklisted_data
from routes.shared import SignalCardRequest, purge_all_caches
from core.auth import get_api_key
from data_engine.mubasher_sqlite_source import build_paths, list_trade_dates

public_router = APIRouter(tags=["settings"])
router = APIRouter(tags=["settings"], dependencies=[Depends(get_api_key)])
logger = logging.getLogger("horus.settings")

SENSITIVE_SETTING_KEYS = {
    "TELEGRAM_TOKEN",
    "CHAT_ID",
    "TELEGRAM_TEST_BOT_TOKEN",
    "TELEGRAM_TEST_CHAT_ID",
    "OLLAMA_API_KEY",
}


def _secret_preview(value: object) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) <= 8:
        return "[set]"
    return f"{text[:4]}...{text[-4:]}"


def _redact_sensitive_settings(payload: dict) -> dict:
    redacted = dict(payload)
    for key in SENSITIVE_SETTING_KEYS:
        raw_value = redacted.get(key) or getattr(settings, key, "")
        redacted[f"{key}_CONFIGURED"] = bool(str(raw_value or "").strip())
        redacted[f"{key}_PREVIEW"] = _secret_preview(raw_value)
        redacted[key] = ""
    return redacted


def _sanitize_settings_update_payload(payload: dict) -> dict:
    sanitized = dict(payload or {})
    for key in SENSITIVE_SETTING_KEYS:
        configured_key = f"{key}_CONFIGURED"
        preview_key = f"{key}_PREVIEW"
        configured = bool(sanitized.pop(configured_key, False))
        sanitized.pop(preview_key, None)
        if key not in sanitized:
            continue
        incoming = sanitized.get(key)
        existing = getattr(settings, key, "")
        if configured and str(existing or "").strip() and not str(incoming or "").strip():
            sanitized.pop(key, None)

    # Numerical boundary protections
    for key, (min_val, max_val) in {
        "SL_PCT": (0.01, 50.0),
        "TP1_PCT": (0.01, 100.0),
        "RSI_MIN": (0.0, 100.0),
        "RSI_MAX": (0.0, 100.0),
        "MAX_POSITIONS": (1, 100),
        "RISK_PER_TRADE": (0.01, 50.0),
    }.items():
        if key in sanitized and sanitized[key] is not None:
            try:
                val = float(sanitized[key])
                if val < min_val or val > max_val:
                    raise ValueError(f"{key} must be between {min_val} and {max_val}.")
            except (TypeError, ValueError) as exc:
                if "must be between" in str(exc):
                    raise
                raise ValueError(f"Invalid numeric value for {key}") from exc

    return sanitized


def _normalize_ticker_list(values: List[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values or []:
        symbol = normalize_ticker(value)
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        output.append(symbol)
    return output


def _mubasher_stream_payload() -> dict:
    root_dir = str(getattr(settings, "MUBASHER_ROOT_DIR", "") or "")
    user_id = str(getattr(settings, "MUBASHER_USER_ID", "") or "").strip()
    payload: Dict[str, Any] = {
        "MUBASHER_ROOT_DIR": root_dir,
        "MUBASHER_USER_ID": user_id,
        "MUBASHER_HISTORY_DB_PATH": "",
        "MUBASHER_HISTORY_DB_AVAILABLE": False,
        "MUBASHER_INTRADAY_DB_PATH": "",
        "MUBASHER_INTRADAY_DB_AVAILABLE": False,
        "MUBASHER_HISTORICAL_TRADE_FOLDER": "",
        "MUBASHER_HISTORICAL_TRADE_AVAILABLE": False,
        "MUBASHER_HISTORICAL_TRADE_DB_COUNT": 0,
        "MUBASHER_HISTORICAL_TRADE_LATEST_DATE": None,
        "MUBASHER_STREAM_DISCOVERY_ERROR": None,
    }

    try:
        paths = build_paths(Path(root_dir), user_id=(user_id or None))
    except Exception as exc:
        payload["MUBASHER_STREAM_DISCOVERY_ERROR"] = str(exc)
        return payload

    trade_dates = list_trade_dates(paths)
    payload.update(
        {
            "MUBASHER_USER_ID": paths.user_id,
            "MUBASHER_HISTORY_DB_PATH": str(paths.history_db),
            "MUBASHER_HISTORY_DB_AVAILABLE": paths.history_db.is_file(),
            "MUBASHER_INTRADAY_DB_PATH": str(paths.intraday_db),
            "MUBASHER_INTRADAY_DB_AVAILABLE": paths.intraday_db.is_file(),
            "MUBASHER_HISTORICAL_TRADE_FOLDER": str(paths.historical_trade_dir),
            "MUBASHER_HISTORICAL_TRADE_AVAILABLE": paths.historical_trade_dir.is_dir(),
            "MUBASHER_HISTORICAL_TRADE_DB_COUNT": len(trade_dates),
            "MUBASHER_HISTORICAL_TRADE_LATEST_DATE": trade_dates[-1] if trade_dates else None,
        }
    )
    return payload


def _settings_payload():
    intraday_csv_path = getattr(settings, "METASTOCK_INTRADAY_FOLDER", "")
    intraday_dat_path = getattr(settings, "METASTOCK_DAT_INTRADAY_FOLDER", "")
    history_dat_path = getattr(settings, "METASTOCK_DAT_HISTORY_FOLDER", "")
    payload = {
        "LOOKBACK": settings.LOOKBACK,
        "VOL_SPIKE": settings.VOL_SPIKE,
        "MOMENTUM": settings.MOMENTUM,
        "RSI_MIN": settings.RSI_MIN,
        "RSI_MAX": settings.RSI_MAX,
        "SL_PCT": settings.SL_PCT,
        "TP1_PCT": settings.TP1_PCT,
        "MIN_TURNOVER": settings.MIN_TURNOVER,
        "TRICKSTER_RSI_MAX": getattr(settings, "TRICKSTER_RSI_MAX", 30.0),
        "TRICKSTER_REL_VOL_MIN": getattr(settings, "TRICKSTER_REL_VOL_MIN", 1.2),
        "TRICKSTER_STRETCH_ATR": getattr(settings, "TRICKSTER_STRETCH_ATR", 2.0),
        "MAX_POSITIONS": settings.MAX_POSITIONS,
        "RISK_PER_TRADE": settings.RISK_PER_TRADE,
        "MIN_RISK_REWARD": getattr(settings, "MIN_RISK_REWARD", 1.0),
        "MIN_SIGNAL_SCORE": getattr(settings, "MIN_SIGNAL_SCORE", 0.0),
        "MIN_SIGNAL_CONFIDENCE": getattr(settings, "MIN_SIGNAL_CONFIDENCE", 0.0),
        "MAX_DAILY_TRADES": getattr(settings, "MAX_DAILY_TRADES", 3),
        "MAX_PORTFOLIO_HEAT": getattr(settings, "MAX_PORTFOLIO_HEAT", 6.0),
        "PENDING_ENTRY_MAX_GAP_PCT": getattr(settings, "PENDING_ENTRY_MAX_GAP_PCT", 1.5),
        "TRAILING_STOP_ENABLED": getattr(settings, "TRAILING_STOP_ENABLED", False),
        "TRAILING_STOP_TYPE": getattr(settings, "TRAILING_STOP_TYPE", "FIXED"),
        "TRAILING_STOP_VALUE": getattr(settings, "TRAILING_STOP_VALUE", 2.0),
        "REGIME_FILTER_ENABLED": getattr(settings, "REGIME_FILTER_ENABLED", False),
        "REGIME_MODE": getattr(settings, "REGIME_MODE", "AUTO"),
        "SECTOR_LIMIT_ENABLED": getattr(settings, "SECTOR_LIMIT_ENABLED", False),
        "MAX_PER_SECTOR": getattr(settings, "MAX_PER_SECTOR", 2),
        "SLIPPAGE_PCT": getattr(settings, "SLIPPAGE_PCT", 0.0),
        "COMMISSION_PCT": getattr(settings, "COMMISSION_PCT", 0.0),
        "LIVE_REQUIRE_NONZERO_COSTS": getattr(settings, "LIVE_REQUIRE_NONZERO_COSTS", True),
        "LIVE_MAX_RISK_PER_TRADE_PCT": getattr(settings, "LIVE_MAX_RISK_PER_TRADE_PCT", 2.0),
        "LIVE_MAX_DAILY_LOSS_PCT": getattr(settings, "LIVE_MAX_DAILY_LOSS_PCT", 3.0),
        "LIVE_MAX_WEEKLY_LOSS_PCT": getattr(settings, "LIVE_MAX_WEEKLY_LOSS_PCT", 6.0),
        "LIVE_MAX_DRAWDOWN_PCT": getattr(settings, "LIVE_MAX_DRAWDOWN_PCT", 20.0),
        "LIVE_MAX_STRESS_DRAWDOWN_PCT": getattr(settings, "LIVE_MAX_STRESS_DRAWDOWN_PCT", 35.0),
        "LIVE_MAX_CONSECUTIVE_LOSSES": getattr(settings, "LIVE_MAX_CONSECUTIVE_LOSSES", 4),
        "LIVE_LOSS_COOLDOWN_MINUTES": getattr(settings, "LIVE_LOSS_COOLDOWN_MINUTES", 60.0),
        "LIVE_MAX_CRISIS_CORRELATION": getattr(settings, "LIVE_MAX_CRISIS_CORRELATION", 0.85),
        "LIVE_MAX_LIQUIDITY_EXIT_PCT": getattr(settings, "LIVE_MAX_LIQUIDITY_EXIT_PCT", 5.0),
        "USE_ATR_EXITS": settings.USE_ATR_EXITS,
        "AUTO_TRADE_ENABLED": settings.AUTO_TRADE_ENABLED,
        "SIGNAL_AUTO_EXECUTION_ENABLED": getattr(settings, "SIGNAL_AUTO_EXECUTION_ENABLED", False),
        "LIVE_ARM_GUARD_ENABLED": getattr(settings, "LIVE_ARM_GUARD_ENABLED", False),
        "LIVE_EXECUTION_ARMED": settings.is_live_execution_armed(),
        "LIVE_EXECUTION_ARMED_RAW": bool(getattr(settings, "LIVE_EXECUTION_ARMED", False)),
        "LIVE_EXECUTION_ARMED_ON": getattr(settings, "LIVE_EXECUTION_ARMED_ON", None),
        "HEAT_PROTECTION_ENABLED": getattr(settings, "HEAT_PROTECTION_ENABLED", True),
        "LOCAL_HISTORY_PROVIDER": getattr(settings, "LOCAL_HISTORY_PROVIDER", "MUBASHER_DB"),
        "LOCAL_INTRADAY_PROVIDER": getattr(settings, "LOCAL_INTRADAY_PROVIDER", "MUBASHER_DB"),
        "LOCAL_TICKS_PROVIDER": getattr(settings, "LOCAL_TICKS_PROVIDER", "MUBASHER_DB"),
        "TICK_SYNC_ENABLED": getattr(settings, "TICK_SYNC_ENABLED", True),
        "METASTOCK_INTRADAY_FOLDER": intraday_csv_path,
        "METASTOCK_INTRADAY_AVAILABLE": bool(intraday_csv_path and os.path.isdir(intraday_csv_path)),
        "METASTOCK_DAT_HISTORY_FOLDER": history_dat_path,
        "METASTOCK_DAT_HISTORY_AVAILABLE": bool(history_dat_path and os.path.isdir(history_dat_path)),
        "METASTOCK_DAT_INTRADAY_FOLDER": intraday_dat_path,
        "METASTOCK_DAT_INTRADAY_AVAILABLE": bool(intraday_dat_path and os.path.isdir(intraday_dat_path)),
        "ATR_TP_MULTIPLIER": getattr(settings, "ATR_TP_MULTIPLIER", 2.0),
        "ATR_SL_MULTIPLIER": getattr(settings, "ATR_SL_MULTIPLIER", 1.5),
        "TELEGRAM_TOKEN": settings.TELEGRAM_TOKEN,
        "CHAT_ID": settings.CHAT_ID,
        "TELEGRAM_AUTO_BROADCAST_INTRADAY": getattr(settings, "TELEGRAM_AUTO_BROADCAST_INTRADAY", True),
        "TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS": getattr(settings, "TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS", False),
        "TELEGRAM_AUTO_BROADCAST_DAILY": getattr(settings, "TELEGRAM_AUTO_BROADCAST_DAILY", True),
        "TELEGRAM_AUTO_BROADCAST_HORUS_EYE": getattr(settings, "TELEGRAM_AUTO_BROADCAST_HORUS_EYE", True),
        "TELEGRAM_AUTO_BROADCAST_AI_REPORT": getattr(settings, "TELEGRAM_AUTO_BROADCAST_AI_REPORT", False),
        "TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT": getattr(settings, "TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT", False),
        "TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT": getattr(settings, "TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT", False),
        "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL": getattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "none"),
        "TELEGRAM_REPORT_LANGUAGE": getattr(settings, "TELEGRAM_REPORT_LANGUAGE", "EN"),
        "ENABLE_INTRADAY_ALERTS": settings.ENABLE_INTRADAY_ALERTS,
        "PIPELINE_STALE_SOUND_ALERT_ENABLED": getattr(settings, "PIPELINE_STALE_SOUND_ALERT_ENABLED", True),
        "PIPELINE_STALE_SOUND_ALERT_COOLDOWN_SEC": getattr(settings, "PIPELINE_STALE_SOUND_ALERT_COOLDOWN_SEC", 600),
        "OLLAMA_API_KEY": getattr(settings, "OLLAMA_API_KEY", ""),
        "OLLAMA_BASE_URL": getattr(settings, "OLLAMA_BASE_URL", "http://10.168.183.175:11434"),
        "AI_REPORT_OLLAMA_MODEL": getattr(settings, "AI_REPORT_OLLAMA_MODEL", "gemma4:31b-cloud"),
        "PINE_IMPORT_TRANSLATION_PROVIDER": getattr(settings, "PINE_IMPORT_TRANSLATION_PROVIDER", "LOCAL"),
        "OLLAMA_CONTEXT_LENGTH": getattr(settings, "OLLAMA_CONTEXT_LENGTH", 8192),
        "AI_REPORT_OLLAMA_NUM_CTX": getattr(settings, "AI_REPORT_OLLAMA_NUM_CTX", 8192),
        "MARKET_START_HHMM_NORMAL": getattr(settings, "MARKET_START_HHMM_NORMAL", "1000"),
        "MARKET_END_HHMM_NORMAL": getattr(settings, "MARKET_END_HHMM_NORMAL", "1415"),
        "MARKET_START_HHMM_RAMADAN": getattr(settings, "MARKET_START_HHMM_RAMADAN", "1000"),
        "MARKET_END_HHMM_RAMADAN": getattr(settings, "MARKET_END_HHMM_RAMADAN", "1330"),
        "RAMADAN_MODE": getattr(settings, "RAMADAN_MODE", False),
        "HISTORICAL_BACKFILL_TRADING_DAYS": getattr(settings, "HISTORICAL_BACKFILL_TRADING_DAYS", 252),
        "HISTORICAL_BACKFILL_SIGNAL_LANES": getattr(settings, "HISTORICAL_BACKFILL_SIGNAL_LANES", "BOTH"),
        "PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS": getattr(settings, "PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS", 15),
        "PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES": getattr(settings, "PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES", True),
        "PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT": getattr(settings, "PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT", 15),
        "PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT": getattr(settings, "PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT", 10),
        "PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT": getattr(settings, "PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT", 8),
        "PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT": getattr(settings, "PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT", 3.0),
        "PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT": getattr(settings, "PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT", 1.0),
        "PORTFOLIO_MGMT_TP2_PCT": getattr(settings, "PORTFOLIO_MGMT_TP2_PCT", 4.0),
        "PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN": getattr(settings, "PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN", 3500),
        "TELEGRAM_TEST_BOT_TOKEN": getattr(settings, "TELEGRAM_TEST_BOT_TOKEN", ""),
        "TELEGRAM_TEST_CHAT_ID": getattr(settings, "TELEGRAM_TEST_CHAT_ID", ""),
    }
    payload.update(_mubasher_stream_payload())
    return payload


def _save_settings_snapshot() -> str | None:
    try:
        snapshots_dir = Path("config_snapshots")
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        snapshot_file = snapshots_dir / f"settings_{timestamp}.json"
        snapshot_data = _settings_payload()
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, indent=2, default=str)
        return str(snapshot_file)
    except Exception as exc:
        logger.warning("[Settings] Failed to save config snapshot: %s", exc)
        return None


@public_router.get("/api/v1/settings")
def get_settings():
    return _redact_sensitive_settings(_settings_payload())


@router.post("/api/v1/settings")
def update_settings_api(payload: dict):
    try:
        payload = _sanitize_settings_update_payload(payload)
        auto_trade_before = bool(getattr(settings, "AUTO_TRADE_ENABLED", False))
        market_hours_changed = any(k in payload for k in (
            'MARKET_START_HHMM_NORMAL', 'MARKET_END_HHMM_NORMAL',
            'MARKET_START_HHMM_RAMADAN', 'MARKET_END_HHMM_RAMADAN', 'RAMADAN_MODE',
            'PRE_CLOSE_OFFSET_MINS', 'DAILY_SIGNAL_OFFSET_MINS', 'INTRADAY_INTERVAL_MINS'
        ))
        success = settings.update(payload)
        if success:
            snapshot_path = _save_settings_snapshot()
            from routes.shared import STRATEGY_CACHE
            STRATEGY_CACHE.update({"data": [], "timestamp": None, "version": -1})
            if "AUTO_TRADE_ENABLED" in payload:
                auto_trade_after = bool(getattr(settings, "AUTO_TRADE_ENABLED", False))
                logger.info(
                    "[Settings] AUTO_TRADE_ENABLED update requested=%s previous=%s current=%s changed=%s",
                    bool(payload.get("AUTO_TRADE_ENABLED")),
                    auto_trade_before,
                    auto_trade_after,
                    auto_trade_before != auto_trade_after,
                )
            if market_hours_changed:
                try:
                    from core.scheduling import reschedule_market_jobs
                    reschedule_market_jobs()
                except Exception:
                    pass  # Scheduler may not be running in tests
            return {
                "status": "updated",
                "settings": _redact_sensitive_settings(_settings_payload()),
                "snapshot_path": snapshot_path,
            }
        raise HTTPException(status_code=500, detail="Failed to persist settings")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/settings/snapshots")
def list_settings_snapshots_api():
    snapshots_dir = Path("config_snapshots")
    if not snapshots_dir.exists():
        return {"snapshots": []}
    files = sorted(snapshots_dir.glob("settings_*.json"), key=os.path.getmtime, reverse=True)
    results = []
    for f in files:
        results.append({
            "filename": f.name,
            "path": str(f),
            "created_at": datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            "size_bytes": f.stat().st_size,
        })
    return {"snapshots": results}


@router.post("/api/v1/settings/snapshots/restore")
def restore_settings_snapshot_api(payload: dict):
    filename = str(payload.get("filename") or "").strip()
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid snapshot filename")
    snapshots_dir = Path("config_snapshots")
    target_file = snapshots_dir / filename
    if not target_file.is_file():
        raise HTTPException(status_code=404, detail="Snapshot file not found")
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            snapshot_data = json.load(f)
        snapshot_data = _sanitize_settings_update_payload(snapshot_data)
        success = settings.update(snapshot_data)
        if success:
            from routes.shared import STRATEGY_CACHE
            STRATEGY_CACHE.update({"data": [], "timestamp": None, "version": -1})
            return {
                "status": "restored",
                "filename": filename,
                "settings": _redact_sensitive_settings(_settings_payload()),
            }
        raise HTTPException(status_code=500, detail="Failed to restore snapshot settings")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to restore snapshot: {str(exc)}")


@router.get("/api/v1/telegram/config")
def get_telegram_config():
    token = settings.TELEGRAM_TOKEN
    chat_id = settings.CHAT_ID
    return {
        "configured": bool(token and chat_id),
        "chat_id": "",
        "chat_id_configured": bool(chat_id),
        "chat_id_preview": _secret_preview(chat_id),
        "token_configured": bool(token),
        "token_preview": _secret_preview(token),
        "auto_intraday": settings.TELEGRAM_AUTO_BROADCAST_INTRADAY,
        "broadcast_no_intraday_signals": getattr(settings, "TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS", False),
        "auto_daily": settings.TELEGRAM_AUTO_BROADCAST_DAILY,
        "auto_horus_eye": settings.TELEGRAM_AUTO_BROADCAST_HORUS_EYE,
        "auto_ai_daily_report": getattr(settings, "TELEGRAM_AUTO_BROADCAST_AI_REPORT", False),
        "auto_weekly_report": getattr(settings, "TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT", False),
        "auto_monthly_report": getattr(settings, "TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT", False),
        "main_channel_signal_level": getattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "none"),
        "report_language": getattr(settings, "TELEGRAM_REPORT_LANGUAGE", "EN"),
    }


@router.post("/api/v1/telegram/config")
def update_telegram_config(payload: dict):
    token = payload.get("token")
    chat_id = payload.get("chat_id")
    auto_intraday = payload.get("auto_intraday")
    broadcast_no_intraday_signals = payload.get("broadcast_no_intraday_signals")
    if broadcast_no_intraday_signals is None:
        broadcast_no_intraday_signals = payload.get("TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS")
    auto_daily = payload.get("auto_daily")
    auto_horus_eye = payload.get("auto_horus_eye")
    auto_ai_daily_report = payload.get("auto_ai_daily_report")
    auto_weekly_report = payload.get("auto_weekly_report")
    auto_monthly_report = payload.get("auto_monthly_report")
    main_channel_signal_level = payload.get("main_channel_signal_level")
    report_language = payload.get("report_language")

    if token:
        settings.TELEGRAM_TOKEN = token.strip()
    if chat_id:
        settings.CHAT_ID = chat_id.strip()
    if auto_intraday is not None:
        settings.TELEGRAM_AUTO_BROADCAST_INTRADAY = bool(auto_intraday)
    if broadcast_no_intraday_signals is not None:
        settings.TELEGRAM_BROADCAST_NO_INTRADAY_SIGNALS = bool(broadcast_no_intraday_signals)
    if auto_daily is not None:
        settings.TELEGRAM_AUTO_BROADCAST_DAILY = bool(auto_daily)
    if auto_horus_eye is not None:
        settings.TELEGRAM_AUTO_BROADCAST_HORUS_EYE = bool(auto_horus_eye)
    if auto_ai_daily_report is not None:
        settings.TELEGRAM_AUTO_BROADCAST_AI_REPORT = bool(auto_ai_daily_report)
    if auto_weekly_report is not None:
        settings.TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT = bool(auto_weekly_report)
    if auto_monthly_report is not None:
        settings.TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT = bool(auto_monthly_report)
    if main_channel_signal_level is not None:
        try:
            settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL = (
                settings._normalize_main_channel_signal_level(main_channel_signal_level)
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if report_language is not None:
        language = str(report_language or "EN").strip().upper() or "EN"
        if language not in {"EN", "AR"}:
            raise HTTPException(status_code=400, detail="report_language must be EN or AR.")
        settings.TELEGRAM_REPORT_LANGUAGE = language
        
    # Save preferences to settings.json
    settings.save_settings()

    return {"status": "success", "configured": bool(settings.TELEGRAM_TOKEN and settings.CHAT_ID)}


@router.post("/api/v1/telegram/broadcast")
def broadcast_message(payload: dict):
    msg = payload.get("message")
    img_b64 = payload.get("image_base64")
    if not msg and not img_b64:
        raise HTTPException(status_code=400, detail="Message or Image required")
    try:
        results = {}
        if img_b64:
            import base64
            import io

            if "base64," in img_b64:
                img_b64 = img_b64.split("base64,")[1]
            buf = io.BytesIO(base64.b64decode(img_b64))
            results["image"] = TelegramBot_Alerts.send_image(buf, caption=msg)
        elif msg:
            results["message"] = TelegramBot_Alerts.send_message(msg)

        for _, value in results.items():
            if not value or not value.get("ok"):
                raise HTTPException(
                    status_code=502,
                    detail=f"Telegram API Failed: {value.get('description') if value else 'No response'}",
                )

        return {"status": "sent", "response": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/telegram/signal-card")
def broadcast_signal_card(req: SignalCardRequest):
    try:
        img_buf = ReportGenerator.create_horus_signal_card(
            ticker=req.ticker,
            entry=req.entry,
            stop_loss=req.sl,
            tp1=req.tp1,
            tp2=req.tp2,
            score=req.score,
            rsi=req.rsi,
            volume_x=req.volume_x,
            confirmation=req.confirmation,
            regime=req.regime,
            signal_data_date=req.signal_date,
            signal_label=req.confirmation or "MANUAL SIGNAL",
        )
        caption = req.caption or (
            f"PREMIUM SIGNAL: #{req.ticker.upper()}\n"
            f"Entry: {req.entry}\n"
            f"SL: {req.sl} | TP1: {req.tp1}\n"
            f"Score: {req.score if req.score is not None else 'N/A'} | "
            f"RSI: {req.rsi if req.rsi is not None else 'N/A'} | "
            f"Vol: {req.volume_x if req.volume_x is not None else 'N/A'}x"
        )

        res = TelegramBot_Alerts.send_image(img_buf, caption=caption)
        if not res or not res.get("ok"):
            raise HTTPException(
                status_code=502,
                detail=f"Telegram API Failed: {res.get('description') if res else 'No response'}",
            )

        return {"status": "sent", "response": res}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/alerts/test")
@router.post("/api/v1/telegram/test")
def test_telegram_alert(payload: Optional[dict] = None):
    try:
        from core import TimeUtils
        payload = payload or {}

        token = payload.get("token") or settings.TELEGRAM_TOKEN
        chat_id = payload.get("chat_id") or settings.CHAT_ID

        msg = "HORUS SYSTEM CHECK\nYour Telegram integration is now linked.\n"
        msg += f"Timestamp: {TimeUtils.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Override internally for the test if token/chat_id provided
        if token and chat_id:
            res = TelegramBot_Alerts.send_message(msg, token=token, chat_id=chat_id)
        else:
            res = TelegramBot_Alerts.send_message(msg)
            
        if res and res.get("ok"):
            return {
                "status": "success",
                "message": f"Primary Telegram test sent to {chat_id}.",
                "target_chat_id": str(chat_id),
            }
        raise HTTPException(status_code=400, detail=f"Telegram Error: {res.get('description', 'Unknown')}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/telegram/test-bot/config")
def get_test_telegram_config():
    """Get the test Telegram bot configuration used by Replay & Dry Run."""
    token = getattr(settings, "TELEGRAM_TEST_BOT_TOKEN", "") or ""
    chat_id = getattr(settings, "TELEGRAM_TEST_CHAT_ID", "") or ""
    return {
        "configured": bool(token and chat_id),
        "chat_id": "",
        "chat_id_configured": bool(chat_id),
        "chat_id_preview": _secret_preview(chat_id),
        "token_configured": bool(token),
        "token_preview": _secret_preview(token),
    }


@router.post("/api/v1/telegram/test-bot/config")
def update_test_telegram_config(payload: dict):
    """Set the test Telegram bot token and chat ID for Replay & Dry Run."""
    token = payload.get("token")
    chat_id = payload.get("chat_id")

    if token is not None:
        settings.TELEGRAM_TEST_BOT_TOKEN = str(token).strip()
    if chat_id is not None:
        settings.TELEGRAM_TEST_CHAT_ID = str(chat_id).strip()

    settings.save_settings()

    configured = bool(
        settings.TELEGRAM_TEST_BOT_TOKEN
        and settings.TELEGRAM_TEST_CHAT_ID
    )
    return {"status": "success", "configured": configured}


@router.post("/api/v1/telegram/test-bot/test")
def test_test_telegram(payload: Optional[dict] = None):
    """Send a verification message through the test Telegram bot."""
    from core import TimeUtils
    payload = payload or {}

    token = payload.get("token") or getattr(settings, "TELEGRAM_TEST_BOT_TOKEN", "")
    chat_id = payload.get("chat_id") or getattr(settings, "TELEGRAM_TEST_CHAT_ID", "")

    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="Test Telegram bot token and chat ID are required.")

    msg = (
        "🧪 HORUS TEST BOT CHECK\n"
        "This channel receives Market Replay & Dry Run alerts.\n"
        f"Timestamp: {TimeUtils.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    res = TelegramBot_Alerts.send_message(msg, token=token, chat_id=chat_id)
    if res and res.get("ok"):
        return {"status": "success", "message": "Test message sent to test bot!"}
    raise HTTPException(status_code=400, detail=f"Telegram Error: {res.get('description', 'Unknown')}")


from core.exclusions import get_all_exclusions, save_exclusions, add_exclusion, remove_exclusion

@public_router.get("/api/v1/exclusions")
@public_router.get("/api/v1/settings/exclusions")
def get_exclusions_api():
    return _normalize_ticker_list(list(get_all_exclusions()))


@router.post("/api/v1/settings/exclusions")
def update_exclusions_api(tickers: List[str]):
    normalized = _normalize_ticker_list(tickers)
    save_exclusions(normalized)
    purged = purge_blacklisted_data(set(normalized))
    purge_all_caches()
    return {
        "message": "Exclusions updated",
        "count": len(normalized),
        "tickers": normalized,
        "purged": purged,
    }


@router.post("/api/v1/exclusions")
def add_exclusion_api(payload: dict):
    ticker = normalize_ticker(payload.get("ticker"))
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker required")
    add_exclusion(ticker)
    purged = purge_blacklisted_data({ticker})
    purge_all_caches()
    return {"status": "success", "ticker": ticker, "purged": purged}


@router.delete("/api/v1/exclusions/{ticker}")
def remove_exclusion_api(ticker: str):
    symbol = normalize_ticker(ticker)
    if not symbol:
        raise HTTPException(status_code=400, detail="Ticker required")
    remove_exclusion(symbol)
    purge_all_caches()
    return {"status": "success", "ticker": symbol}
