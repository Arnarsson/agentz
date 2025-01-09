"""WebSocket manager module."""
from typing import Dict, Set
from fastapi import WebSocket
from app.core.logging import log_error

class WebSocketManager:
    """WebSocket connection manager."""

    def __init__(self):
        """Initialize manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, agent_id: str):
        """Connect a WebSocket client."""
        try:
            await websocket.accept()
            if agent_id not in self.active_connections:
                self.active_connections[agent_id] = set()
            self.active_connections[agent_id].add(websocket)
        except Exception as e:
            log_error("WebSocket", "Connection failed", {"agent_id": agent_id, "error": str(e)})
            raise

    async def disconnect(self, websocket: WebSocket, agent_id: str):
        """Disconnect a WebSocket client."""
        try:
            if agent_id in self.active_connections:
                self.active_connections[agent_id].remove(websocket)
                if not self.active_connections[agent_id]:
                    del self.active_connections[agent_id]
        except Exception as e:
            log_error("WebSocket", "Disconnection failed", {"agent_id": agent_id, "error": str(e)})
            raise

    async def broadcast(self, agent_id: str, message: str):
        """Broadcast a message to all connected clients for an agent."""
        if agent_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[agent_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                log_error("WebSocket", "Broadcast failed", {
                    "agent_id": agent_id,
                    "message": message,
                    "error": str(e)
                })
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection, agent_id)

ws_manager = WebSocketManager() 