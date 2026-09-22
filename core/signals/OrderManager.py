import time
import random
import logging
from core.settings import settings
from core.risk.kill_switch import is_kill_switch_active
from core.market.ThndrBrokerClient import ThndrBrokerClient
from core.DataManager import DataManager
from database import BrokerOrder, Portfolio, db
from core import TimeUtils

logger = logging.getLogger("OrderManager")

class OrderManager:
    @staticmethod
    def submit_live_order(portfolio_id: int, symbol: str, side: str, quantity: int, theoretical_price: float) -> dict:
        """
        Registers a new order in the database and submits it to the live broker.
        """
        symbol = str(symbol or "").strip().upper()
        side = str(side or "BUY").strip().upper()
        quantity = int(quantity)
        theoretical_price = float(theoretical_price)

        # 1. Enforce Risk Kill Switch Deadbolt
        if is_kill_switch_active():
            logger.error(f"[OrderManager] LIVE ORDER BLOCKED: Global emergency kill switch is active for symbol={symbol}")
            return {"success": False, "reason": "emergency_kill_switch_active"}

        # 2. Create local database pending order record
        try:
            with db.atomic():
                order = BrokerOrder.create(
                    portfolio=portfolio_id,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=theoretical_price,
                    state="PENDING",
                    created_at=TimeUtils.now(),
                    updated_at=TimeUtils.now()
                )
        except Exception as db_err:
            logger.error(f"[OrderManager] Failed to create database order record: {db_err}")
            return {"success": False, "reason": "database_error", "message": str(db_err)}

        # 3. Place order via broker client
        client = ThndrBrokerClient()
        start_time = time.time()
        result = client.place_order(symbol, quantity, side, theoretical_price)
        latency_ms = int((time.time() - start_time) * 1000.0)

        # 4. Process broker response & transition order state
        try:
            if result.get("success"):
                broker_order_id = result.get("broker_order_id")
                order.broker_order_id = broker_order_id
                order.state = "SUBMITTED"
                order.updated_at = TimeUtils.now()
                order.save()
                
                logger.info(
                    f"[OrderManager] Order submitted: id={order.id} broker_id={broker_order_id} "
                    f"symbol={symbol} qty={quantity} state=SUBMITTED latency={latency_ms}ms"
                )
                
                # Perform immediate reconciliation check (covers sandbox instant fills)
                OrderManager.reconcile_order(order.id, latency_ms)
                return {"success": True, "order_id": order.id, "state": "SUBMITTED", "broker_order_id": broker_order_id}
            else:
                reason = result.get("reason", "broker_rejection")
                order.state = "REJECTED"
                order.updated_at = TimeUtils.now()
                order.save()
                
                logger.warning(f"[OrderManager] Order rejected: id={order.id} symbol={symbol} reason={reason}")
                return {"success": False, "order_id": order.id, "state": "REJECTED", "reason": reason}
        except Exception as save_err:
            logger.error(f"[OrderManager] Failed to update order status: {save_err}")
            return {"success": False, "reason": "status_save_error", "order_id": order.id}

    @staticmethod
    def reconcile_order(order_id: int, latency_ms: int = 0) -> bool:
        """
        Fetches the current status of an order from the broker and updates the database.
        """
        try:
            order = BrokerOrder.get_by_id(order_id)
        except BrokerOrder.DoesNotExist:
            logger.error(f"[OrderManager] Reconcile error: BrokerOrder id={order_id} not found.")
            return False

        if order.state in ("FILLED", "REJECTED"):
            return True

        client = ThndrBrokerClient()
        result = client.query_order_status(order.broker_order_id)
        if not result.get("success"):
            logger.warning(f"[OrderManager] Could not fetch status for broker_id={order.broker_order_id}: {result.get('reason')}")
            return False

        status = result.get("status")
        if status == "FILLED":
            # Determine fill price
            filled_price = result.get("filled_price")
            if filled_price is None:
                # Sandbox or fallback: query market price cache and apply a slight random drift
                market_price = float(order.price)
                try:
                    df = DataManager.get_intraday_data(order.symbol, limit=1, refresh_if_stale=False)
                    if df is not None and not df.empty:
                        market_price = float(df.iloc[-1]['Close'])
                except Exception:
                    pass
                
                # Apply 0.05% to 0.15% execution slippage for buys, negative for sells
                drift = random.uniform(0.0005, 0.0015)
                if order.side == "BUY":
                    filled_price = market_price * (1.0 + drift)
                else:
                    filled_price = market_price * (1.0 - drift)

            filled_price = max(0.01, round(float(filled_price), 4))
            
            # Compute slippage in basis points (1 bps = 0.01%)
            price_diff = filled_price - order.price
            if order.price > 0:
                if order.side == "BUY":
                    slippage_bps = int(round((price_diff / order.price) * 10000.0))
                else:
                    slippage_bps = int(round((-price_diff / order.price) * 10000.0))
            else:
                slippage_bps = 0

            with db.atomic():
                order.state = "FILLED"
                order.filled_price = filled_price
                order.slippage_bps = slippage_bps
                order.updated_at = TimeUtils.now()
                order.save()
            
            logger.info(
                f"[OrderManager] Reconciled Order: id={order.id} state=FILLED symbol={order.symbol} "
                f"price={order.price:.2f} filled={filled_price:.2f} slippage={slippage_bps}bps"
            )
            return True
            
        elif status == "REJECTED":
            order.state = "REJECTED"
            order.updated_at = TimeUtils.now()
            order.save()
            logger.warning(f"[OrderManager] Reconciled Order: id={order.id} state=REJECTED symbol={order.symbol}")
            return False

        return False
