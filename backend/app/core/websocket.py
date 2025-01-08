from fastapi import WebSocket
from typing import Dict, Set, Optional, Any
import json
from datetime import datetime

class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        # agent_id -> Set of WebSocket connections
        self.agent_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> agent_id mapping for quick lookup
        self.connection_agents: Dict[WebSocket, str] = {}
        
    async def connect(self, websocket: WebSocket, agent_id: str):
        """Connect a WebSocket to an agent's updates."""
        await websocket.accept()
        
        if agent_id not in self.agent_connections:
            self.agent_connections[agent_id] = set()
        self.agent_connections[agent_id].add(websocket)
        self.connection_agents[websocket] = agent_id
        
        # Send initial connection message
        await websocket.send_json({
            "type": "connection_established",
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket."""
        agent_id = self.connection_agents.get(websocket)
        if agent_id:
            self.agent_connections[agent_id].remove(websocket)
            if not self.agent_connections[agent_id]:
                del self.agent_connections[agent_id]
            del self.connection_agents[websocket]
    
    async def broadcast_to_agent(self, agent_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections for an agent."""
        if agent_id in self.agent_connections:
            message["timestamp"] = datetime.utcnow().isoformat()
            disconnected = set()
            
            for connection in self.agent_connections[agent_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for connection in disconnected:
                await self.disconnect(connection)
    
    async def broadcast_status_update(
        self,
        agent_id: str,
        status: str,
        execution_status: Optional[Dict[str, Any]] = None
    ):
        """Broadcast a status update for an agent."""
        message = {
            "type": "status_update",
            "agent_id": agent_id,
            "status": status,
            "execution_status": execution_status
        }
        await self.broadcast_to_agent(agent_id, message)
    
    async def broadcast_task_update(
        self,
        agent_id: str,
        task_id: str,
        status: str,
        progress: int,
        message: str,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ):
        """Broadcast a task execution update."""
        update = {
            "type": "task_update",
            "agent_id": agent_id,
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "message": message
        }
        if result is not None:
            update["result"] = result
        if error is not None:
            update["error"] = error
            
        await self.broadcast_to_agent(agent_id, update)

# Global WebSocket manager instance
ws_manager = WebSocketManager() 