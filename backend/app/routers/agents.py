"""
Router for agent-related endpoints.
"""
from fastapi import APIRouter, Depends
from app.core.auth.clerk_middleware import ClerkAuth, TokenPayload

router = APIRouter(prefix="/agents", tags=["agents"])
clerk_auth = ClerkAuth()

@router.get("/")
async def list_agents(token: TokenPayload = Depends(clerk_auth)):
    """
    List all agents for the current user.
    """
    return {
        "message": "List agents endpoint",
        "user_id": token.sub,
        "agents": []  # TODO: Implement agent listing
    }

@router.post("/")
async def create_agent(token: TokenPayload = Depends(clerk_auth)):
    """
    Create a new agent.
    """
    return {
        "message": "Create agent endpoint",
        "user_id": token.sub,
        "agent": {}  # TODO: Implement agent creation
    } 