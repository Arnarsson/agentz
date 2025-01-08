from fastapi import WebSocket
from typing import Dict, Set, Optional, Any, List, Deque
import json
from datetime import datetime, UTC
from collections import deque
import asyncio
from ..core.logging import log_websocket_action

class WebSocketManager:
    """Manages WebSocket connections and broadcasts with enhanced features."""
    
    def __init__(self, 
                 heartbeat_interval: int = 30,
                 max_queue_size: int = 100,
                 batch_interval: float = 0.1):
        # agent_id -> Set of WebSocket connections
        self.agent_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> agent_id mapping for quick lookup
        self.connection_agents: Dict[WebSocket, str] = {}
        # Message queues for offline clients
        self.message_queues: Dict[str, Deque[Dict[str, Any]]] = {}
        # Connection statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "errors": 0
        }
        # Batch update buffers
        self.update_buffers: Dict[str, List[Dict[str, Any]]] = {}
        
        self.heartbeat_interval = heartbeat_interval
        self.max_queue_size = max_queue_size
        self.batch_interval = batch_interval
        
    async def connect(self, websocket: WebSocket, agent_id: str):
        """Connect a WebSocket to an agent's updates."""
        try:
            await websocket.accept()
            
            # Initialize message queues if not exists
            if agent_id not in self.message_queues:
                self.message_queues[agent_id] = deque(maxlen=self.max_queue_size)
            
            # Get any queued messages before initializing connections
            queued_messages = list(self.message_queues[agent_id]) if self.message_queues[agent_id] else []
            if queued_messages:
                log_websocket_action(f"Found {len(queued_messages)} queued messages for agent {agent_id}")
            
            # Initialize connections
            if agent_id not in self.agent_connections:
                self.agent_connections[agent_id] = set()
                self.update_buffers[agent_id] = []
                
            self.agent_connections[agent_id].add(websocket)
            self.connection_agents[websocket] = agent_id
            
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
            # Send initial connection message
            await websocket.send_json({
                "type": "connection_established",
                "agent_id": agent_id,
                "timestamp": datetime.now(UTC).isoformat()
            })
            
            # Send queued messages
            if queued_messages:
                log_websocket_action(f"Sending batch update with {len(queued_messages)} messages to agent {agent_id}")
                batch_message = {
                    "type": "batch_update",
                    "updates": queued_messages,
                    "timestamp": datetime.now(UTC).isoformat()
                }
                await websocket.send_json(batch_message)
                self.stats["messages_sent"] += 1
                log_websocket_action(f"Batch update sent to agent {agent_id}")
                self.message_queues[agent_id].clear()
            else:
                log_websocket_action(f"No queued messages found for agent {agent_id}")
            
            # Start heartbeat task
            asyncio.create_task(self._heartbeat(websocket))
            # Start batch update task
            asyncio.create_task(self._process_batch_updates(agent_id))
            
            log_websocket_action(f"WebSocket connected for agent {agent_id}")
        except Exception as e:
            self.stats["errors"] += 1
            log_websocket_action(f"WebSocket connection failed for agent {agent_id}: {str(e)}", level="error")
            if agent_id in self.agent_connections and websocket in self.agent_connections[agent_id]:
                await self.disconnect(websocket)
            raise
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket."""
        agent_id = self.connection_agents.get(websocket)
        if agent_id:
            self.agent_connections[agent_id].remove(websocket)
            if not self.agent_connections[agent_id]:
                # Keep the message queue when no active connections
                del self.agent_connections[agent_id]
            del self.connection_agents[websocket]
            self.stats["active_connections"] -= 1
            log_websocket_action(f"WebSocket disconnected for agent {agent_id}")
    
    async def _heartbeat(self, websocket: WebSocket):
        """Send periodic heartbeat to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": datetime.now(UTC).isoformat()
                })
        except Exception:
            await self.disconnect(websocket)
    
    async def _process_batch_updates(self, agent_id: str):
        """Process batched updates periodically."""
        try:
            while True:
                await asyncio.sleep(self.batch_interval)
                if agent_id in self.update_buffers and self.update_buffers[agent_id]:
                    updates = self.update_buffers[agent_id]
                    self.update_buffers[agent_id] = []
                    
                    batch_message = {
                        "type": "batch_update",
                        "updates": updates,
                        "timestamp": datetime.now(UTC).isoformat()
                    }
                    await self._send_or_queue(agent_id, batch_message)
        except Exception as e:
            log_websocket_action(f"Batch update processing failed for agent {agent_id}: {str(e)}", level="error")
    
    async def _send_or_queue(self, agent_id: str, message: Dict[str, Any]):
        """Send message to connected clients or queue for offline clients."""
        if agent_id in self.agent_connections and self.agent_connections[agent_id]:
            disconnected = set()
            for connection in self.agent_connections[agent_id]:
                try:
                    await connection.send_json(message)
                    self.stats["messages_sent"] += 1
                except Exception:
                    disconnected.add(connection)
                    self.stats["errors"] += 1
            
            # Clean up disconnected clients
            for connection in disconnected:
                await self.disconnect(connection)
        else:
            # Queue message for offline clients
            if agent_id not in self.message_queues:
                self.message_queues[agent_id] = deque(maxlen=self.max_queue_size)
            if message.get("type") == "batch_update":
                # If it's a batch update, queue individual updates
                for update in message["updates"]:
                    self.message_queues[agent_id].append(update)
            else:
                self.message_queues[agent_id].append(message)
    
    async def broadcast_to_agent(self, agent_id: str, message: Dict[str, Any]):
        """Buffer message for batch broadcasting."""
        message = message.copy()  # Create a copy to avoid modifying the original
        message["timestamp"] = datetime.now(UTC).isoformat()
        
        # If there are active connections, buffer for batch update
        if agent_id in self.agent_connections and self.agent_connections[agent_id]:
            if agent_id not in self.update_buffers:
                self.update_buffers[agent_id] = []
            self.update_buffers[agent_id].append(message)
        # If no active connections, queue the message
        else:
            if agent_id not in self.message_queues:
                self.message_queues[agent_id] = deque(maxlen=self.max_queue_size)
            self.message_queues[agent_id].append(message)
            log_websocket_action(f"Message queued for offline agent {agent_id}: {message['type']}")
    
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
    
    def get_stats(self) -> Dict[str, int]:
        """Get current WebSocket connection statistics."""
        return self.stats.copy()

# Global WebSocket manager instance
ws_manager = WebSocketManager() 