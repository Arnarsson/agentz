"""WebSocket endpoints for real-time updates."""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from loguru import logger
from app.core.websocket import ws_manager
from app.core.auth.clerk_middleware import ClerkAuth, TokenPayload

router = APIRouter(tags=["websocket"])
clerk_auth = ClerkAuth()

@router.websocket("/agents/{agent_id}/ws")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for agent communication."""
    await ws_manager.connect(websocket, agent_id, "agent")
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, agent_id, "agent")
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
        await ws_manager.disconnect(websocket, agent_id, "agent")

@router.websocket("/tasks/{task_id}/ws")
async def task_websocket(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for task updates."""
    await ws_manager.connect(websocket, task_id, "task")
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, task_id, "task")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        await ws_manager.disconnect(websocket, task_id, "task")

@router.websocket("/users/{user_id}/ws")
async def user_websocket(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for user notifications."""
    await ws_manager.connect(websocket, user_id, "user")
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, user_id, "user")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await ws_manager.disconnect(websocket, user_id, "user")

@router.post("/agents/{agent_id}/broadcast")
async def broadcast_to_agent(
    agent_id: str,
    message: dict,
    token: TokenPayload = Depends(clerk_auth)
):
    """Broadcast a message to all clients connected to an agent."""
    await ws_manager.broadcast_agent_update(
        agent_id=agent_id,
        status=message.get("status", "update"),
        details=message.get("details", {})
    )
    return {"status": "ok"}

@router.post("/tasks/{task_id}/broadcast")
async def broadcast_to_task(
    task_id: str,
    message: dict,
    token: TokenPayload = Depends(clerk_auth)
):
    """Broadcast a message to all clients connected to a task."""
    await ws_manager.broadcast_task_update(
        task_id=task_id,
        status=message.get("status", "update"),
        details=message.get("details", {})
    )
    return {"status": "ok"}

@router.post("/users/{user_id}/notify")
async def notify_user(
    user_id: str,
    notification: dict,
    token: TokenPayload = Depends(clerk_auth)
):
    """Send a notification to a specific user."""
    await ws_manager.broadcast_user_notification(
        user_id=user_id,
        notification=notification
    )
    return {"status": "ok"} 