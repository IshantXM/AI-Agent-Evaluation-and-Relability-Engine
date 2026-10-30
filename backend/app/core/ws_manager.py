from __future__ import annotations

import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("aegis.websocket")


class ConnectionManager:
    """Manages active WebSocket connections and pub/sub broadcasts."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected. Active clients: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket disconnected. Active clients: %d", len(self.active_connections))

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcasts an event message across all connected subscribers.
        Dead connections are cleaned up automatically.
        """
        message = {"event_type": event_type, "data": data}
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.warning("Failed sending to client, dropping connection: %s", exc)
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


ws_manager = ConnectionManager()
