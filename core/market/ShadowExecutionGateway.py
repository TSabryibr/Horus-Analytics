import time
import random
import logging
from core.settings import settings
from core.risk.kill_switch import is_kill_switch_active
from core.DataManager import DataManager

logger = logging.getLogger("ShadowExecutionGateway")

class ShadowExecutionGateway:
    @staticmethod
    def place_shadow_order(ticker: str, shares: int, side: str, theoretical_price: float, signal_id: str = None) -> dict:
        """
        Simulates sending an order to a broker with network roundtrip latency and slippage.
        """
        ticker = str(ticker or "").strip().upper()
        side = str(side or "BUY").strip().upper()
        
        # 1. Check Global Risk Kill Switch
        if is_kill_switch_active():
            logger.error(f"[ShadowBroker] Order blocked. Global Emergency Kill Switch is active for ticker={ticker}")
            return {
                "success": False,
                "reason": "emergency_kill_switch_active",
                "message": "Global emergency kill switch is active. Execution blocked."
            }

        # 2. Simulate network roundtrip latency (e.g., 200ms - 500ms)
        latency_ms = random.randint(200, 500)
        time.sleep(latency_ms / 1000.0)

        # 3. Retrieve the latest market price from DB cache representing live quote stream
        market_price = theoretical_price
        try:
            # Query the database cache for the latest tick
            df = DataManager.get_intraday_data(ticker, limit=1, refresh_if_stale=False)
            if df is not None and not df.empty:
                market_price = float(df.iloc[-1]['Close'])
            else:
                daily_df = DataManager.get_stock_data(ticker, include_live=False)
                if daily_df is not None and not daily_df.empty:
                    market_price = float(daily_df.iloc[-1]['Close'])
        except Exception as e:
            logger.warning(f"[ShadowBroker] Could not query latest price cache for {ticker}: {e}. Defaulting to signal price.")

        # 4. Apply simulated price drift (slippage penalty representing spread and queue time)
        # Typically fills are slightly worse than the theoretical target price in a thin market.
        # Drift: BUY orders get filled slightly higher (0.0% to 0.15%), SELL orders slightly lower.
        drift_factor = random.uniform(0.0, 0.0015)
        if side == "BUY":
            fill_price = market_price * (1.0 + drift_factor)
        else:
            fill_price = market_price * (1.0 - drift_factor)

        # Ensure price is valid
        fill_price = max(0.01, round(fill_price, 4))

        # 5. Compute slippage in basis points (bps)
        # 1 bps = 0.01%
        price_diff = fill_price - theoretical_price
        if theoretical_price > 0:
            if side == "BUY":
                slippage_bps = int(round((price_diff / theoretical_price) * 10000.0))
            else:
                slippage_bps = int(round((-price_diff / theoretical_price) * 10000.0))
        else:
            slippage_bps = 0

        logger.info(
            f"[ShadowBroker] Order Filled: ticker={ticker} shares={shares} side={side} "
            f"theoretical={theoretical_price:.2f} fill={fill_price:.2f} "
            f"slippage={slippage_bps}bps latency={latency_ms}ms"
        )

        return {
            "success": True,
            "fill_price": fill_price,
            "slippage_bps": slippage_bps,
            "latency_ms": latency_ms,
            "signal_id": signal_id
        }
