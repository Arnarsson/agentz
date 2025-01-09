from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from app.core.websocket import ws_manager

router = APIRouter(tags=["websocket"])

@router.websocket("/agents/{agent_id}/ws")
async def websocket_endpoint(websocket: WebSocket, agent_id: UUID):
    """WebSocket endpoint for agent communication."""
    await ws_manager.connect(websocket, agent_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await ws_manager.send_personal_message(websocket, "pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
        ws_manager.disconnect(websocket)

@router.post("/agents/{agent_id}/broadcast")
async def broadcast_to_agent(agent_id: UUID, message: dict):
    """Broadcast a message to all clients connected to an agent."""
    await ws_manager.broadcast_to_agent(agent_id, message)
    return {"status": "ok"} 