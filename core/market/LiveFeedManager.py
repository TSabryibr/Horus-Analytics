from core.settings import settings
import datetime
import logging
import threading
import json
import time
import zmq
import pandas as pd
from pathlib import Path
from data_engine import parquet_writer
from core.signals.system_monitor import check_exit_conditions
from core import AlertManager
logger = logging.getLogger(__name__)

class LiveFeedManager:
    _zmq_context = None
    _thread = None
    _stop_event = threading.Event()
    _lock = threading.Lock()
    
    # Caches
    _resistance_cache = {} # {ticker: {Res_20D, Key_1, Key_2}}
    _triggered_today = set() # {ticker_SignalType}
    _confirmed_breakouts = set() # {ticker_SignalType}
    _candle_buffers = {} # {ticker: {'bucket': ts, 'open': f, 'high': f, 'low': f, 'close': f, 'volume': f, 'ticks': int, 'consecutive_above': int}}
    _last_refresh_date = None

    @classmethod
    def update_ticker(cls, ticker: str, df: pd.DataFrame, signal: str | None = None) -> None:
        """Helper to receive external ticker updates gracefully."""
        if not ticker:
            return
        ticker = str(ticker).strip().upper()
        if df is not None and not df.empty:
            last_close = float(df['close'].iloc[-1]) if 'close' in df.columns else float(df['Close'].iloc[-1])
            cls.evaluate_breakout(ticker, price=last_close, volume=0.0, is_confirmed=True)

    @classmethod
    def evaluate_breakout(
        cls,
        ticker: str,
        price: float,
        volume: float = 0.0,
        is_confirmed: bool = False,
        bar_open: float = 0.0,
    ) -> None:
        """
        Evaluates breakout for ticker against cached resistance levels.
        - is_confirmed=True: 5-minute candle has closed above resistance (+1.5%).
        - is_confirmed=False: in-progress provisional warning (requires multi-tick persistence).
        """
        if ticker not in cls._resistance_cache:
            return

        levels_data = cls._resistance_cache[ticker]
        raw_checks = [
            ('Resistance_20D', levels_data.get('R20')),
            ('Key_Resistance_1', levels_data.get('K1')),
            ('Key_Resistance_2', levels_data.get('K2'))
        ]
        active_checks = sorted(
            [(label, val) for label, val in raw_checks if val and not pd.isna(val)],
            key=lambda x: x[1]
        )

        for label, level in active_checks:
            trigger_key = f"{ticker}_{label}"
            threshold = level * 1.015  # 1.5% hurdle

            if price > threshold:
                if is_confirmed:
                    if trigger_key in cls._confirmed_breakouts:
                        continue
                    cls._confirmed_breakouts.add(trigger_key)
                    cls._triggered_today.add(trigger_key)
                    penetration_pct = ((price - level) / level) * 100.0
                    logger.info(
                        "[Live] 5M Confirmed Breakout ticker=%s level=%s resistance=%.2f close=%.2f (+%.1f%%) vol=%.0f",
                        ticker, label, level, price, penetration_pct, volume,
                    )
                    if settings.ENABLE_INTRADAY_ALERTS:
                        msg = (
                            f"🚀 *INTRADAY BREAKOUT (5M CONFIRMED)*\n"
                            f"Symbol: *{ticker}*\n"
                            f"Level: {label} ({level:.2f})\n"
                            f"Close: {price:.2f} (+{penetration_pct:.1f}% Penetration)\n"
                            f"Bar Volume: {volume:,.0f} shares\n"
                            f"✅ *Confirmed 5-Minute Candle Close*"
                        )
                        AlertManager.broadcast_alert(msg)
                    break
                else:
                    if trigger_key in cls._triggered_today:
                        continue
                    cls._triggered_today.add(trigger_key)
                    penetration_pct = ((price - level) / level) * 100.0
                    logger.info(
                        "[Live] Provisional Breakout ticker=%s level=%s resistance=%.2f price=%.2f (+%.1f%%)",
                        ticker, label, level, price, penetration_pct,
                    )
                    if settings.ENABLE_INTRADAY_ALERTS:
                        msg = (
                            f"⚠️ *INTRADAY BREAKOUT (PROVISIONAL)*\n"
                            f"Symbol: *{ticker}*\n"
                            f"Level: {label} ({level:.2f})\n"
                            f"Price: {price:.2f} (+{penetration_pct:.1f}% Penetration)\n"
                            f"Status: *Candle Forming (Multi-Tick Persistence)*"
                        )
                        AlertManager.broadcast_alert(msg)
                    break

    @classmethod
    def _compute_fallback_resistance(cls) -> dict:
        """
        Computes 20-day high resistance directly from historical parquet data
        when shared analytics scan rows are not yet available.
        """
        cache = {}
        try:
            from core.DataManager import DataManager
            from core.DailyScanner import _list_tickers_with_cold_retry, get_excluded_tickers_upper, normalize_ticker
            tickers = _list_tickers_with_cold_retry()
            excluded_set = get_excluded_tickers_upper()
            tickers = [
                t for t in tickers
                if normalize_ticker(t) not in excluded_set and normalize_ticker(t) not in ['REPORT', 'EGX30_70_100']
            ]
            if tickers:
                df = DataManager.get_universe_data(tickers, history_limit=25, include_live=False)
                if df is not None and not df.empty:
                    for ticker, g in df.groupby(level=0):
                        ticker_clean = str(ticker).strip().upper()
                        highs = g['high'] if 'high' in g.columns else g.get('High')
                        if highs is not None and len(highs) >= 5:
                            r20 = float(highs.tail(20).max())
                            if r20 > 0:
                                cache[ticker_clean] = {
                                    'R20': r20,
                                    'K1': round(r20 * 1.03, 2),
                                    'K2': round(r20 * 1.06, 2),
                                }
        except Exception as e:
            logger.warning("[LiveFeed] Fallback resistance calculation error: %s", e)
        return cache

    @staticmethod
    def refresh_resistance_levels():
        """
        Background task to load resistance levels from the shared analytics
        universe snapshot. Should be run once per day.
        """
        if LiveFeedManager._last_refresh_date == datetime.date.today() and LiveFeedManager._resistance_cache:
            return # Already fresh
            
        logger.info("[LiveFeed] Refreshing resistance levels from shared analytics snapshot")
        try:
            from routes.analytics import ensure_analytics_rows

            scan_id = f"livefeed_{datetime.date.today().isoformat()}"
            rows = ensure_analytics_rows(scan_id=scan_id, allow_stale=True)

            refreshed_cache = {}
            for row in rows:
                ticker = str(row.get("Ticker") or "").strip().upper()
                if not ticker:
                    continue
                refreshed_cache[ticker] = {
                    'R20': row.get('Resistance_20D'),
                    'K1': row.get('Key_Resistance_1'),
                    'K2': row.get('Key_Resistance_2')
                }

            if not refreshed_cache:
                logger.info("[LiveFeed] No analytics snapshot rows available yet. Computing fallback resistance from historical parquet...")
                refreshed_cache = LiveFeedManager._compute_fallback_resistance()
                if not refreshed_cache:
                    logger.info("[LiveFeed] Parquet history also not available yet (will populate after scan)")
                    return

            LiveFeedManager._resistance_cache = refreshed_cache
            LiveFeedManager._last_refresh_date = datetime.date.today()
            # Clear daily triggers and candle buffers
            LiveFeedManager._triggered_today.clear()
            LiveFeedManager._confirmed_breakouts.clear()
            LiveFeedManager._candle_buffers.clear()
            logger.info("[LiveFeed] Loaded resistance levels for %s tickers", len(refreshed_cache))
            
        except Exception as e:
            logger.exception("[LiveFeed] Error refreshing resistance: %s", e)

    @staticmethod
    def start_monitoring():
        """
        Starts the Live Market ZMQ Listener in a background thread.
        """
        with LiveFeedManager._lock:
            if LiveFeedManager._thread and LiveFeedManager._thread.is_alive():
                logger.info("[LiveFeed] ZMQ Listener already running")
                return
            LiveFeedManager._zmq_context = None
            LiveFeedManager._thread = None

        # Initialize Cache in Background
        threading.Thread(target=LiveFeedManager.refresh_resistance_levels, daemon=True).start()

        logger.info("[LiveFeed] Starting real-time market ZMQ listener")
        
        # Define the callback that handles new data
        def on_market_update(bar):
            """
            Triggered whenever a ticker updates.
            bar = {'ticker': 'COMI', 'close': 75.5, ...}
            """
            # === MARKET HOURS CHECK ===
            if not settings.is_market_open():
                return
                
            ticker = str(bar.get('ticker', '')).strip().upper()
            if not ticker:
                return
            price = float(bar['close'])
            raw_vol = float(bar.get('volume', 0.0) or 0.0)
            
            # 1. Check Trade Exits (Stop Loss / Take Profit)
            try:
                check_exit_conditions(ticker, current_price=price)
            except Exception as e:
                logger.warning("[Live] Exit check error ticker=%s err=%s", ticker, e)

            # 2. 5-MINUTE CANDLE AGGREGATION
            ts = bar.get('timestamp') or bar.get('time') or datetime.datetime.now()
            if not isinstance(ts, datetime.datetime):
                try:
                    ts = pd.to_datetime(ts).to_pydatetime()
                except Exception:
                    ts = datetime.datetime.now()

            bucket_minute = (ts.minute // 5) * 5
            current_bucket = ts.replace(minute=bucket_minute, second=0, microsecond=0)

            buf = LiveFeedManager._candle_buffers.get(ticker)
            closed_bar = None

            if buf is None:
                LiveFeedManager._candle_buffers[ticker] = {
                    'bucket': current_bucket,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': raw_vol,
                    'ticks': 1,
                    'consecutive_above': 0,
                }
                buf = LiveFeedManager._candle_buffers[ticker]
            elif buf['bucket'] != current_bucket:
                # Previous 5-minute candle closed!
                closed_bar = dict(buf)
                LiveFeedManager._candle_buffers[ticker] = {
                    'bucket': current_bucket,
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': raw_vol,
                    'ticks': 1,
                    'consecutive_above': 0,
                }
                buf = LiveFeedManager._candle_buffers[ticker]
            else:
                buf['high'] = max(buf['high'], price)
                buf['low'] = min(buf['low'], price)
                buf['close'] = price
                buf['volume'] += raw_vol
                buf['ticks'] += 1

            # 3. BREAKOUT SIGNAL EVALUATION
            # A. If a 5-minute candle closed, evaluate confirmed breakout
            if closed_bar is not None:
                LiveFeedManager.evaluate_breakout(
                    ticker,
                    price=closed_bar['close'],
                    volume=closed_bar['volume'],
                    is_confirmed=True,
                    bar_open=closed_bar['open'],
                )
                # Persist completed 5M bar to Data Lake
                try:
                    bar_df = pd.DataFrame([{
                        'timestamp': closed_bar['bucket'],
                        'open': closed_bar['open'],
                        'high': closed_bar['high'],
                        'low': closed_bar['low'],
                        'close': closed_bar['close'],
                        'volume': closed_bar['volume'],
                    }])
                    parquet_writer.save_stream(ticker, bar_df, folder='intraday')
                except Exception as e:
                    logger.exception("[Live] Data Lake 5M update error ticker=%s err=%s", ticker, e)

            # B. In-progress multi-tick provisional filter (3+ consecutive ticks above resistance)
            threshold_crossed = False
            if ticker in LiveFeedManager._resistance_cache:
                for lvl in LiveFeedManager._resistance_cache[ticker].values():
                    if lvl and not pd.isna(lvl) and price > (lvl * 1.015):
                        threshold_crossed = True
                        break

            if threshold_crossed:
                buf['consecutive_above'] += 1
                if buf['consecutive_above'] >= 3:
                    LiveFeedManager.evaluate_breakout(
                        ticker,
                        price=price,
                        volume=buf['volume'],
                        is_confirmed=False,
                    )
            else:
                buf['consecutive_above'] = 0

        def _zmq_listener(callback):
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.setsockopt(zmq.LINGER, 0)
            socket.setsockopt_string(zmq.SUBSCRIBE, "TICK")
            # Connect to the local host running the DDE script.
            zmq_host = getattr(settings, "ZMQ_HOST", "127.0.0.1")
            zmq_port = getattr(settings, "ZMQ_PORT", "5556")
            connection_str = f"tcp://{zmq_host}:{zmq_port}"
            socket.connect(connection_str)
            
            with LiveFeedManager._lock:
                LiveFeedManager._zmq_context = context

            logger.info(f"[LiveFeed] Connected to ZeroMQ stream on {connection_str}")
            
            while not LiveFeedManager._stop_event.is_set():
                try:
                    # Non-blocking receive with timeout so we can check stop_event
                    if socket.poll(1000):
                        msg = socket.recv_string()
                        # msg format: "TICK {"ticker": "COMI", "price": 10.5, ...}"
                        if msg.startswith("TICK "):
                            payload = json.loads(msg[5:])
                            
                            bar = {
                                "ticker": payload.get("ticker"),
                                "close": payload.get("price"),
                                "open": payload.get("price"),
                                "high": payload.get("price"),
                                "low": payload.get("price"),
                                "volume": payload.get("volume"),
                                "timestamp": datetime.datetime.fromtimestamp(payload.get("timestamp", time.time()))
                            }
                            callback(bar)
                except zmq.error.ContextTerminated:
                    break
                except Exception as e:
                    logger.error("[LiveFeed] ZMQ listener error: %s", e)
            
            socket.close()
            context.term()
            logger.info("[LiveFeed] ZMQ listener terminated.")

        LiveFeedManager._stop_event.clear()
        thread = threading.Thread(target=_zmq_listener, args=(on_market_update,), daemon=True)
        thread.start()
        with LiveFeedManager._lock:
            LiveFeedManager._thread = thread

    @staticmethod
    def stop_monitoring():
        with LiveFeedManager._lock:
            thread = LiveFeedManager._thread
            context = LiveFeedManager._zmq_context
            LiveFeedManager._thread = None
            LiveFeedManager._zmq_context = None
            
        LiveFeedManager._stop_event.set()

        if thread and thread.is_alive():
            thread.join(timeout=5)
        logger.info("[LiveFeed] ZMQ monitoring stopped")

    @staticmethod
    def is_running():
        thread = LiveFeedManager._thread
        return bool(thread and thread.is_alive())
    @staticmethod
    def get_last_update_time():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_session_stats():
        return {
            "tickers_tracked": len(LiveFeedManager._resistance_cache),
            "alerts_fired": len(LiveFeedManager._triggered_today)
        }
