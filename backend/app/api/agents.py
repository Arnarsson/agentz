from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.services.agent import AgentService

router = APIRouter()

@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db)
):
    """Create a new agent."""
    try:
        # Check if agent with same role exists
        existing_agent = await AgentService.get_agent_by_role(db, agent_data.role)
        if existing_agent:
            raise HTTPException(
                status_code=400,
                detail=f"Agent with role '{agent_data.role}' already exists"
            )
        
        # Create agent
        agent = await AgentService.create_agent(db, agent_data)
        return agent
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all agents."""
    agents = await AgentService.list_agents(db, skip=skip, limit=limit)
    return agents

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Get agent by ID."""
    agent = await AgentService.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db)
):
    """Update agent."""
    agent = await AgentService.update_agent(db, agent_id, agent_data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Delete agent."""
    success = await AgentService.delete_agent(db, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted successfully"} 