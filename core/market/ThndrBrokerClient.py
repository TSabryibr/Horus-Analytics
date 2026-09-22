import os
import time
import random
import logging
import requests
from core.settings import settings

logger = logging.getLogger("ThndrBrokerClient")

class ThndrBrokerClient:
    def __init__(self):
        self.api_key = getattr(settings, "THNDR_API_KEY", "MOCK_KEY")
        self.secret = getattr(settings, "THNDR_SECRET", "MOCK_SECRET")
        self.base_url = getattr(settings, "THNDR_BASE_URL", "https://sandbox.thndr.app/api/v1")
        self.token = None
        self.token_expiry = 0

    def authenticate(self) -> bool:
        """
        Handles authentication/token retrieval with the Thndr API.
        For sandbox/mock mode, returns True with a mock token.
        """
        if self.api_key == "MOCK_KEY":
            self.token = "MOCK_ACCESS_TOKEN"
            self.token_expiry = time.time() + 3600
            return True

        try:
            url = f"{self.base_url}/auth/token"
            payload = {"apiKey": self.api_key, "secret": self.secret}
            # Simulated timeout for low latency
            resp = requests.post(url, json=payload, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("accessToken")
                # Expire token 5 minutes early
                self.token_expiry = time.time() + int(data.get("expiresIn", 3600)) - 300
                logger.info("[ThndrClient] Authenticated successfully with broker.")
                return True
            else:
                logger.error(f"[ThndrClient] Authentication failed: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.exception(f"[ThndrClient] Exception during broker authentication: {e}")
            return False

    def _ensure_authenticated(self) -> bool:
        if not self.token or time.time() >= self.token_expiry:
            return self.authenticate()
        return True

    def place_order(self, symbol: str, quantity: int, side: str, price: float) -> dict:
        """
        Submits an order to the broker.
        Returns a dictionary representing the order status or rejection.
        """
        symbol = str(symbol or "").strip().upper()
        side = str(side or "BUY").strip().upper()
        quantity = int(quantity)
        price = float(price)

        if not self._ensure_authenticated():
            return {"success": False, "reason": "auth_failure", "message": "Failed to authenticate with broker."}

        # If sandbox or mock mode is active, simulate order submission response
        if self.api_key == "MOCK_KEY" or "sandbox" in self.base_url:
            broker_order_id = f"THNDR-{random.randint(100000, 999999)}"
            logger.info(f"[ThndrClient] [Sandbox] Submitted order {broker_order_id} for {quantity} shares of {symbol} via REST API.")
            return {
                "success": True,
                "broker_order_id": broker_order_id,
                "status": "SUBMITTED",
                "message": "Order submitted successfully."
            }

        try:
            url = f"{self.base_url}/orders"
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "symbol": symbol,
                "quantity": quantity,
                "side": side,
                "type": "LIMIT",
                "price": price
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=2.0)
            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "success": True,
                    "broker_order_id": data.get("orderId"),
                    "status": data.get("status", "SUBMITTED"),
                    "message": "Order placed successfully."
                }
            else:
                logger.error(f"[ThndrClient] Order placement failed: {resp.status_code} - {resp.text}")
                return {
                    "success": False,
                    "reason": "broker_rejection",
                    "message": f"Broker rejected order: {resp.text}"
                }
        except Exception as e:
            logger.exception(f"[ThndrClient] Exception placing order on broker: {e}")
            return {
                "success": False,
                "reason": "connection_error",
                "message": f"Connection error: {e}"
            }

    def query_order_status(self, broker_order_id: str) -> dict:
        """
        Queries the current status of an order on the broker.
        """
        if not self._ensure_authenticated():
            return {"success": False, "reason": "auth_failure"}

        if self.api_key == "MOCK_KEY" or "sandbox" in self.base_url:
            # Simulate fill on sandbox
            # Return filled status with a slight simulated slippage
            return {
                "success": True,
                "status": "FILLED",
                "filled_price": None, # Will let OrderManager calculate or query cache
                "filled_quantity": None
            }

        try:
            url = f"{self.base_url}/orders/{broker_order_id}"
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.get(url, headers=headers, timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "status": data.get("status"), # FILLED, PARTIALLY_FILLED, REJECTED, SUBMITTED
                    "filled_price": data.get("filledPrice"),
                    "filled_quantity": data.get("filledQuantity")
                }
            else:
                return {"success": False, "reason": f"broker_error_{resp.status_code}"}
        except Exception as e:
            logger.error(f"[ThndrClient] Error querying status: {e}")
            return {"success": False, "reason": "connection_error"}
