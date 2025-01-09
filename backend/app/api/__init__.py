"""API package."""
from fastapi import APIRouter
from app.api.agents import router as agents_router
from app.api.tasks import router as tasks_router
from app.api.websocket import router as websocket_router

# Create API router
api_router = APIRouter()

# Include all routers with their prefixes
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(websocket_router, tags=["websocket"])

# Export routers
agents = agents_router
tasks = tasks_router
websocket = websocket_router 