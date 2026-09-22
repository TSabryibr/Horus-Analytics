"""
TELEGRAM ALERTS MODULE
======================
Sends trading signals and position alerts to your Telegram.

How to get your IDs:
1. Search for @BotFather on Telegram. Create a bot and get the TOKEN.
2. Search for @userinfobot to get your CHAT_ID.
"""

from core.settings import settings
import io
import os
import requests
import logging
import time
import threading
import datetime
import re

# Path logging for debugging shadow imports
logger = logging.getLogger("horus.telegram")
logger.info(f"TelegramBot_Alerts loaded from: {os.path.abspath(__file__)}")


_TELEGRAM_BOT_URL_RE = re.compile(r"/bot[^/\s]+/")


def _redact_telegram_secret(value) -> str:
    text = str(value)
    text = _TELEGRAM_BOT_URL_RE.sub("/bot<redacted>/", text)
    for secret in (
        getattr(settings, "TELEGRAM_TOKEN", ""),
        getattr(settings, "TELEGRAM_TEST_BOT_TOKEN", ""),
    ):
        secret = str(secret or "").strip()
        if secret:
            text = text.replace(secret, "<redacted>")
    return text


def _is_transient_telegram_error(exc) -> bool:
    return isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout))


def _coerce_telegram_config(config):
    if isinstance(config, dict):
        return (
            str(config.get("token") or "").strip(),
            str(config.get("chat_id") or "").strip(),
        )
    token, chat_id = config
    return str(token or "").strip(), str(chat_id or "").strip()


def _normalize_telegram_overrides(token=None, chat_id=None):
    token_text = str(token or "").strip()
    chat_id_text = str(chat_id or "").strip()
    if token_text and chat_id_text and ":" not in token_text and ":" in chat_id_text:
        return chat_id_text, token_text
    return token, chat_id

def _current_telegram_config(override_token=None, override_chat_id=None):
    from core import TimeUtils
    # If in simulation or replay mode, default to test credentials to avoid main channel noise
    replay_live_routing = (
        getattr(TimeUtils, "is_replay_live_channel_routing", lambda: False)()
    )
    if (
        not override_token
        and not override_chat_id
        and (TimeUtils.is_simulating() or TimeUtils.is_replay())
        and not replay_live_routing
    ):
        test_token = (getattr(settings, "TELEGRAM_TEST_BOT_TOKEN", "") or "").strip()
        test_chat_id = (getattr(settings, "TELEGRAM_TEST_CHAT_ID", "") or "").strip()
        if test_token and test_chat_id:
            return {"token": test_token, "chat_id": test_chat_id}
        else:
            return {"token": "", "chat_id": ""}

    token = (override_token or settings.TELEGRAM_TOKEN or "").strip()
    chat_id = (override_chat_id or settings.CHAT_ID or "").strip()
    return {"token": token, "chat_id": chat_id}


def _test_telegram_config():
    """Get the test Telegram bot credentials (for Replay & Dry Run).
    Falls back to production credentials if test bot is not configured."""
    test_token = (getattr(settings, "TELEGRAM_TEST_BOT_TOKEN", "") or "").strip()
    test_chat_id = (getattr(settings, "TELEGRAM_TEST_CHAT_ID", "") or "").strip()
    if test_token and test_chat_id:
        return test_token, test_chat_id
    # Fallback to production
    config = _current_telegram_config()
    return config['token'], config['chat_id']


def _has_markdown_parse_error(res_json) -> bool:
    description = str((res_json or {}).get("description", "")).lower()
    return "parse entities" in description


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _telegram_api_error_text(res_json) -> str:
    if not isinstance(res_json, dict):
        return "Telegram API error"
    error_code = res_json.get("error_code")
    description = res_json.get("description") or "Telegram API error"
    prefix = f"{error_code}: " if error_code else ""
    return _redact_telegram_secret(f"{prefix}{description}")


def _update_env_chat_id(chat_id):
    """Keep migrated Telegram chat IDs visible to runtime settings."""
    normalized_chat_id = str(chat_id).strip()
    os.environ["TELEGRAM_CHAT_ID"] = normalized_chat_id
    try:
        settings.CHAT_ID = normalized_chat_id
        settings.save_settings("custom")
    except Exception as exc:
        logger.warning(f"Unable to persist migrated Telegram chat ID: {exc}")


def send_message(text, token=None, chat_id=None, parse_mode="Markdown", **kwargs):
    """
    Sends a text message to the configured Telegram chat with retry logic.
    """
    token, chat_id = _normalize_telegram_overrides(token, chat_id)
    config = _current_telegram_config(token, chat_id)
    token = config['token']
    chat_id = config['chat_id']
    
    if not token or token == "YOUR_BOT_TOKEN_HERE" or not chat_id:
        return {'ok': False, 'description': 'Telegram not configured'}
        
    if os.getenv("HORUS_SANDBOX") == "1" or os.getenv("HORUS_TELEGRAM_SANDBOX") == "1":
        logger.info(f"[TELEGRAM SANDBOX] Suppressing message dispatch (mock success): {text[:60]}...")
        return {'ok': True, 'result': {'message_id': 9999, 'text': text}}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }

    max_retries = 3
    last_api_error = None
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=15)
            res_json = response.json()

            # Supergroup Migration Logic
            if not res_json.get("ok"):
                last_api_error = res_json
                migrate_id = res_json.get("parameters", {}).get("migrate_to_chat_id")
                if migrate_id:
                    logger.info(f"🔄 Group migrated! Updating CHAT_ID to {migrate_id}")
                    settings.CHAT_ID = str(migrate_id)
                    _update_env_chat_id(migrate_id)
                    payload["chat_id"] = str(migrate_id)
                    # No continue here, we retry the next iteration with the new ID
                elif payload.get("parse_mode") and _has_markdown_parse_error(res_json):
                    # Strip markdown and retry immediately
                    payload.pop("parse_mode", None)
                    continue
                else:
                    # If it's a permanent error (e.g. 403 Forbidden), don't retry
                    error_code = res_json.get("error_code")
                    if error_code in [400, 401, 403]:
                        return res_json
                    if error_code == 429 and attempt < max_retries - 1:
                        retry_after = res_json.get("parameters", {}).get("retry_after")
                        try:
                            wait_seconds = min(max(int(retry_after or 1), 1), 30)
                        except (TypeError, ValueError):
                            wait_seconds = 3
                        logger.warning(f"Telegram rate limited message send. Retrying in {wait_seconds}s...")
                        time.sleep(wait_seconds)
                        continue
            else:
                return res_json

        except Exception as e:
            error_text = _redact_telegram_secret(e)
            if attempt == max_retries - 1:
                log_fn = logger.warning if _is_transient_telegram_error(e) else logger.error
                log_fn(f"Final Telegram failure after {max_retries} attempts: {error_text}")
                return {'ok': False, 'description': error_text}

            backoff = 2 * (attempt + 1)
            logger.warning(f"Telegram timeout/error (attempt {attempt+1}/{max_retries}): {error_text}. Retrying in {backoff}s...")
            time.sleep(backoff)

    if last_api_error:
        return {'ok': False, 'description': _telegram_api_error_text(last_api_error)}
    return {'ok': False, 'description': 'Max retries reached'}

def send_image(image_buffer, caption="", token=None, chat_id=None, **kwargs):
    """
    Sends an image to Telegram with retry logic.
    """
    config = _current_telegram_config(token, chat_id)
    token = config['token']
    chat_id = config['chat_id']
    
    if not token or token == "YOUR_BOT_TOKEN_HERE" or not chat_id:
        return {'ok': False, 'description': 'Telegram not configured'}
         
    if os.getenv("HORUS_SANDBOX") == "1" or os.getenv("HORUS_TELEGRAM_SANDBOX") == "1":
        logger.info(f"[TELEGRAM SANDBOX] Suppressing image dispatch (mock success): {caption[:60]}...")
        return {'ok': True, 'result': {'message_id': 9999, 'caption': caption}}

    url = f"https://api.telegram.org/bot{token}/sendPhoto"

    max_retries = 3
    last_api_error = None
    parse_mode = 'Markdown'
    for attempt in range(max_retries):
        try:
            # Reset buffer pointer for each attempt
            image_buffer.seek(0)
            files = {'photo': ('image.png', image_buffer, 'image/png')}
            data = {'chat_id': chat_id, 'caption': caption}
            if parse_mode:
                data['parse_mode'] = parse_mode

            response = requests.post(url, files=files, data=data, timeout=25)
            res_json = response.json()

            if not res_json.get("ok"):
                last_api_error = res_json
                migrate_id = res_json.get("parameters", {}).get("migrate_to_chat_id")
                if migrate_id:
                    logger.info(f"🔄 Group migrated (Image)! Updating CHAT_ID to {migrate_id}")
                    settings.CHAT_ID = str(migrate_id)
                    _update_env_chat_id(migrate_id)
                    chat_id = str(migrate_id) # Update for next retry
                elif parse_mode and _has_markdown_parse_error(res_json):
                    # Retry once without Markdown parsing, matching send_message.
                    parse_mode = None
                    continue
                else:
                    error_code = res_json.get("error_code")
                    if error_code in [400, 401, 403]:
                        return res_json
                    if error_code == 429 and attempt < max_retries - 1:
                        retry_after = res_json.get("parameters", {}).get("retry_after")
                        try:
                            wait_seconds = min(max(int(retry_after or 1), 1), 30)
                        except (TypeError, ValueError):
                            wait_seconds = 3
                        logger.warning(f"Telegram rate limited image send. Retrying in {wait_seconds}s...")
                        time.sleep(wait_seconds)
                        continue
            else:
                return res_json

        except Exception as e:
            error_text = _redact_telegram_secret(e)
            if attempt == max_retries - 1:
                log_fn = logger.warning if _is_transient_telegram_error(e) else logger.error
                log_fn(f"Final Telegram image failure after {max_retries} attempts: {error_text}")
                return {'ok': False, 'description': error_text}

            backoff = 3 * (attempt + 1)
            logger.warning(f"Telegram image timeout/error (attempt {attempt+1}/{max_retries}): {error_text}. Retrying in {backoff}s...")
            time.sleep(backoff)

    if last_api_error:
        return {'ok': False, 'description': _telegram_api_error_text(last_api_error)}
    return {'ok': False, 'description': 'Max retries reached'}

def format_signal_alert(
    signals,
    language: str | None = None,
    regime: str | None = None,
    scan_label: str | None = None,
) -> str:
    """Formats a list of signals into an institutional-grade, readable Telegram message."""
    if not signals:
        return ""

    resolved_lang = str(
        language
        or getattr(settings, "TELEGRAM_REPORT_LANGUAGE", "EN")
        or "EN"
    ).strip().upper()
    is_ar = resolved_lang == "AR"
    precision = int(getattr(settings, "TELEGRAM_PRICE_PRECISION", 2))

    regime_str = str(regime or "").strip()
    scan_str = str(scan_label or "").strip()

    if is_ar:
        regime_labels = {
            "BULLISH": "صاعد 🟢",
            "BEARISH": "هابط 🔴",
            "CAUTIOUS": "حذر 🟡",
            "NEUTRAL": "محايد ⚪",
        }
        regime_display = regime_labels.get(regime_str.upper(), regime_str or "نشط ⚡")
        scan_display = "إشارة يومية" if "DAILY" in scan_str.upper() else ("قبل الإغلاق" if "PRE" in scan_str.upper() else (scan_str or "مسح حورس"))
        msg = "🚀 *إشارات حورس الذكية*\n"
        msg += f"📋 المسح: *{scan_display}* | نظام السوق: *{regime_display}*\n"
        msg += "═════════════════════════\n\n"
    else:
        regime_display = regime_str.upper() if regime_str else "ACTIVE"
        scan_display = scan_str.upper() if scan_str else "DAILY SIGNAL"
        msg = "🚀 *HORUS INTELLIGENCE | TRADING SIGNALS*\n"
        msg += f"📋 Scan: *{scan_display}* | Market Regime: *{regime_display}*\n"
        msg += "═════════════════════════\n\n"

    max_signals = int(getattr(settings, "TELEGRAM_SUMMARY_MAX_SIGNALS", 10))
    currency = "ج.م" if is_ar else "LE"

    for s in signals[:max_signals]:
        entry = _safe_float((s or {}).get("Entry_Price", 0))
        stop_loss = _safe_float((s or {}).get("Stop_Loss", 0))
        tp1 = _safe_float((s or {}).get("Target_Price", 0))
        fallback_tp2 = tp1 * 1.04 if tp1 else 0
        tp2 = _safe_float((s or {}).get("Target_Price_2", fallback_tp2), fallback_tp2)
        ticker = str((s or {}).get("Ticker", "N/A")).strip().upper() or "N/A"
        score = (s or {}).get("Score", 0)

        volume_x = (s or {}).get("Volume_x")
        vol_text = f"{_safe_float(volume_x):.1f}".rstrip("0").rstrip(".") if volume_x is not None else "N/A"
        if vol_text.endswith("."):
            vol_text = vol_text[:-1]

        # Calculate Upside / Downside % & R:R
        tp1_pct = ((tp1 - entry) / entry * 100) if entry > 0 and tp1 > 0 else 0.0
        tp2_pct = ((tp2 - entry) / entry * 100) if entry > 0 and tp2 > 0 else 0.0
        sl_pct = ((entry - stop_loss) / entry * 100) if entry > 0 and stop_loss > 0 else 0.0

        risk = entry - stop_loss
        reward = tp1 - entry
        rr_ratio = (reward / risk) if risk > 0 and reward > 0 else 0.0
        rr_str = f"1 : {rr_ratio:.1f}" if rr_ratio > 0 else "N/A"

        if is_ar:
            msg += f"🔹 *{ticker}* | التقييم: *{score}/10*\n"
            msg += f"   • سعر الدخول: *{entry:.{precision}f} {currency}*\n"
            msg += f"   • الهدف الأول: *{tp1:.{precision}f} {currency}* (+{tp1_pct:.1f}%)\n"
            if tp2 > 0:
                msg += f"   • الهدف الثاني: *{tp2:.{precision}f} {currency}* (+{tp2_pct:.1f}%)\n"
            msg += f"   • وقف الخسارة: *{stop_loss:.{precision}f} {currency}* (-{sl_pct:.1f}%)\n"
            msg += f"   • العائد للمخاطرة: *{rr_str}* | طفرة الحجم: *{vol_text}x*\n\n"
        else:
            msg += f"🔹 *{ticker}* | Score: *{score}/10*\n"
            msg += f"   • Entry: *{entry:.{precision}f} {currency}*\n"
            msg += f"   • TP1: *{tp1:.{precision}f} {currency}* (+{tp1_pct:.1f}%)\n"
            if tp2 > 0:
                msg += f"   • TP2: *{tp2:.{precision}f} {currency}* (+{tp2_pct:.1f}%)\n"
            msg += f"   • Stop Loss: *{stop_loss:.{precision}f} {currency}* (-{sl_pct:.1f}%)\n"
            msg += f"   • Risk/Reward: *{rr_str}* | Vol Spike: *{vol_text}x*\n\n"

    if is_ar:
        msg += "═════════════════════════\n"
        msg += "📈 الأولوية لحماية رأس المال. التزم بوقف الخسارة بدقة."
    else:
        msg += "═════════════════════════\n"
        msg += "📈 Capital preservation first. Respect stops strictly."

    return msg

def _build_telegram_session() -> requests.Session:
    """Builds a requests.Session configured with retries and connection pooling."""
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def handle_commands():
    """Polls for new messages and handles commands with persistent session keepalive."""
    token, chat_id = _coerce_telegram_config(_current_telegram_config())
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        return

    last_update_id = 0
    logger = logging.getLogger('TelegramBot')
    logger.info("Starting Telegram Command Listener...")

    error_count = 0
    max_sleep = 60
    last_error_log_time = 0
    session = _build_telegram_session()

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            # Use 20s long-poll timeout with 25s HTTP timeout to avoid NAT/ISP TCP drops
            params = {"offset": int(last_update_id) + 1, "timeout": 20}
            if getattr(requests.get, "__module__", "") != "requests.api":
                resp = requests.get(url, params=params, timeout=25)
            else:
                resp = session.get(url, params=params, timeout=25)
            response = resp.json() if hasattr(resp, "json") else resp

            if response.get("ok"):
                # Reset backoff on success
                error_count = 0
                for update in response.get("result", []):
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    sender_chat_id = str(msg.get("chat", {}).get("id", ""))

                    if not text:
                        continue

                    # SPECIAL CASE: /chatid is allowed from ANYWHERE to help debug migration
                    if text.startswith("/chatid"):
                        send_message(f"🆔 This Chat ID is: `{sender_chat_id}`", sender_chat_id, token)
                        continue

                    if sender_chat_id != chat_id:
                        continue # Ignore unauthorized chats

                    if text.startswith("/"):
                        _process_command(text, chat_id, token)

        except Exception as e:
            is_transient = _is_transient_telegram_error(e)
            if is_transient:
                # Fast retry for transient network blips (socket reset, timeout)
                sleep_time = 2
            else:
                error_count += 1
                sleep_time = min(5 * (2 ** (error_count - 1)), max_sleep)
            
            # Rate limit logging (once every 5 minutes if error persists)
            current_time = time.time()
            if current_time - last_error_log_time > 300:
                log_fn = logger.warning if is_transient else logger.error
                log_fn(f"Telegram polling error (retry in {sleep_time}s): {_redact_telegram_secret(e)}")
                last_error_log_time = current_time
            
            # Recreate session if connection was severed
            if isinstance(e, requests.exceptions.ConnectionError):
                try:
                    session.close()
                except Exception:
                    pass
                session = _build_telegram_session()

            time.sleep(sleep_time)

def _process_command(command, chat_id, token):
    """Router for bot commands."""
    cmd = command.split()[0].lower()
    
    if cmd == "/status":
        from routes.shared import get_system_state_snapshot
        state = get_system_state_snapshot()
        msg = f"🛰 *HORUS STATUS REPORT*\nState: {state.get('pipeline_state')}\nStatus: {state.get('status')}\nStep: {state.get('step')}\nProgress: {state.get('progress')}%"
        send_message(msg, token=token, chat_id=chat_id)
        
    elif cmd == "/positions":
        from database import Position
        open_pos = Position.select().where(Position.status == "OPEN").count()
        msg = f"💼 *PORTFOLIO SUMMARY*\nOpen Positions: {open_pos}"
        send_message(msg, token=token, chat_id=chat_id)
        
    elif cmd in ["/help", "/start"]:
        msg = "🤖 *HORUS COMMAND CENTER*\n/status - System Health\n/positions - Active Trades\n/accuracy - Strategy Wins"
        send_message(msg, token=token, chat_id=chat_id)

def start_polling():
    """Starts the command listener in a background thread."""
    thread = threading.Thread(target=handle_commands, daemon=True)
    thread.start()

if __name__ == "__main__":
    # Test message
    print("Sending test message...")
    send_message("✅ Market Analysis System: Telegram Alerts are now ACTIVE.")
