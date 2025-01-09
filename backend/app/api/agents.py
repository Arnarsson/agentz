"""Agent API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.services.agent import AgentService
from app.core.errors import AgentError, AgentNotFoundError, AgentBusyError
from app.core.logging import log_agent_action
from app.core.websocket import ws_manager
from pydantic import BaseModel
import uuid
import json

router = APIRouter(
    tags=["agents"],
    responses={404: {"description": "Not found"}},
)

class TaskExecution(BaseModel):
    """Schema for task execution request."""
    task: str
    tools: List[Dict[str, Any]] = []
    context: Dict[str, Any] = {}

class TaskResponse(BaseModel):
    """Schema for task execution response."""
    task_id: str
    agent_id: str
    status: str
    message: str

@router.post("/", response_model=AgentResponse, status_code=201)
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
        
    except AgentError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all agents."""
    try:
        agents = await AgentService.list_agents(db, skip=skip, limit=limit)
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Get agent by ID."""
    try:
        agent = await AgentService.get_agent(db, agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent with ID {agent_id} not found")
        return agent
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db)
):
    """Update agent."""
    try:
        agent = await AgentService.update_agent(db, agent_id, agent_data)
        if not agent:
            raise AgentNotFoundError(f"Agent with ID {agent_id} not found")
        return agent
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Delete agent."""
    try:
        await AgentService.delete_agent(db, agent_id)
        return {"message": f"Agent with ID {agent_id} deleted"}
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{agent_id}/execute", response_model=TaskResponse)
async def execute_task(
    agent_id: str,
    task_data: TaskExecution,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Execute a task with an agent."""
    try:
        agent = await AgentService.get_agent(db, agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent with ID {agent_id} not found")
        
        task_id = str(uuid.uuid4())
        background_tasks.add_task(
            AgentService.execute_task,
            db,
            agent,
            task_data.task,
            task_id,
            task_data.tools,
            task_data.context
        )
        
        return {
            "task_id": task_id,
            "agent_id": agent_id,
            "status": "started",
            "message": f"Task execution started with ID {task_id}"
        }
        
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AgentBusyError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/{agent_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time agent communication."""
    try:
        await ws_manager.connect(websocket, agent_id)
        agent = await AgentService.get_agent(db, agent_id)
        if not agent:
            await ws_manager.disconnect(websocket, agent_id)
            return
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message["type"] == "task":
                    task_id = str(uuid.uuid4())
                    await AgentService.execute_task(
                        db,
                        agent,
                        message["task"],
                        task_id,
                        message.get("tools", []),
                        message.get("context", {})
                    )
                
                # Log agent action
                log_agent_action(agent_id, message["type"], message)
                
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket, agent_id)
            
    except Exception as e:
        await ws_manager.disconnect(websocket, agent_id)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ws/stats")
async def get_websocket_stats() -> Dict[str, int]:
    """Get current WebSocket connection statistics."""
    return ws_manager.get_stats() 