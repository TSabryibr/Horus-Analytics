import logging
import json
from typing import List, Dict
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("horus.websocket")

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket: New client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket: Client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: str, event_type: str = "alert"):
        """
        Broadcasts a message to all connected clients.
        """
        if not self.active_connections:
            return

        payload = {
            "type": event_type,
            "data": message
        }
        
        # If message is a dict or list, don't double-json escape
        if isinstance(message, (dict, list)):
            payload["data"] = message
        elif isinstance(message, str):
            try:
                # Try to parse if it's already a JSON string
                payload["data"] = json.loads(message)
            except:
                pass

        json_payload = json.dumps(payload)
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json_payload)
            except Exception as e:
                logger.error(f"WebSocket: Broadcast failed for one client: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

# Global Manager Instance
ws_manager = WebSocketManager()
