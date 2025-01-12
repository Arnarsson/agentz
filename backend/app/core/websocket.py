"""WebSocket manager module."""
from typing import Dict, Set, Any
from fastapi import WebSocket
from app.core.logging import log_error
import json

class WebSocketManager:
    """WebSocket connection manager."""

    def __init__(self):
        """Initialize manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.task_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, connection_type: str = "agent"):
        """Connect a WebSocket client.
        
        Args:
            websocket: The WebSocket connection
            client_id: The ID of the agent/task/user
            connection_type: Type of connection ("agent", "task", or "user")
        """
        try:
            await websocket.accept()
            
            # Select appropriate connection store
            connections = self._get_connection_store(connection_type)
            if client_id not in connections:
                connections[client_id] = set()
            connections[client_id].add(websocket)
            
        except Exception as e:
            log_error("WebSocket", "Connection failed", {
                "client_id": client_id,
                "connection_type": connection_type,
                "error": str(e)
            })
            raise

    async def disconnect(self, websocket: WebSocket, client_id: str, connection_type: str = "agent"):
        """Disconnect a WebSocket client."""
        try:
            connections = self._get_connection_store(connection_type)
            if client_id in connections:
                connections[client_id].remove(websocket)
                if not connections[client_id]:
                    del connections[client_id]
        except Exception as e:
            log_error("WebSocket", "Disconnection failed", {
                "client_id": client_id,
                "connection_type": connection_type,
                "error": str(e)
            })
            raise

    def _get_connection_store(self, connection_type: str) -> Dict[str, Set[WebSocket]]:
        """Get the appropriate connection store based on type."""
        if connection_type == "agent":
            return self.active_connections
        elif connection_type == "task":
            return self.task_connections
        elif connection_type == "user":
            return self.user_connections
        else:
            raise ValueError(f"Invalid connection type: {connection_type}")

    async def _broadcast_to_connections(
        self,
        connections: Set[WebSocket],
        message: Dict[str, Any]
    ) -> Set[WebSocket]:
        """Broadcast message to a set of connections."""
        disconnected = set()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                log_error("WebSocket", "Broadcast failed", {
                    "message": message,
                    "error": str(e)
                })
                disconnected.add(connection)
        return disconnected

    async def broadcast_agent_update(self, agent_id: str, status: str, details: Dict[str, Any]):
        """Broadcast agent update to all connected clients."""
        if agent_id in self.active_connections:
            message = {
                "type": "agent_update",
                "agent_id": agent_id,
                "status": status,
                "details": details,
                "timestamp": str(datetime.utcnow())
            }
            disconnected = await self._broadcast_to_connections(
                self.active_connections[agent_id],
                message
            )
            # Clean up disconnected clients
            for connection in disconnected:
                await self.disconnect(connection, agent_id, "agent")

    async def broadcast_task_update(self, task_id: str, status: str, details: Dict[str, Any]):
        """Broadcast task update to all connected clients."""
        if task_id in self.task_connections:
            message = {
                "type": "task_update",
                "task_id": task_id,
                "status": status,
                "details": details,
                "timestamp": str(datetime.utcnow())
            }
            disconnected = await self._broadcast_to_connections(
                self.task_connections[task_id],
                message
            )
            # Clean up disconnected clients
            for connection in disconnected:
                await self.disconnect(connection, task_id, "task")

    async def broadcast_task_metrics(self, task_id: str, metrics: Dict[str, Any]):
        """Broadcast task metrics update."""
        if task_id in self.task_connections:
            message = {
                "type": "task_metrics",
                "task_id": task_id,
                "metrics": metrics,
                "timestamp": str(datetime.utcnow())
            }
            disconnected = await self._broadcast_to_connections(
                self.task_connections[task_id],
                message
            )
            # Clean up disconnected clients
            for connection in disconnected:
                await self.disconnect(connection, task_id, "task")

    async def broadcast_user_notification(self, user_id: str, notification: Dict[str, Any]):
        """Broadcast notification to a specific user."""
        if user_id in self.user_connections:
            message = {
                "type": "notification",
                "user_id": user_id,
                "notification": notification,
                "timestamp": str(datetime.utcnow())
            }
            disconnected = await self._broadcast_to_connections(
                self.user_connections[user_id],
                message
            )
            # Clean up disconnected clients
            for connection in disconnected:
                await self.disconnect(connection, user_id, "user")

ws_manager = WebSocketManager() 