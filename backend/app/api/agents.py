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

router = APIRouter()

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
        
    except AgentError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
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
        return agent
    except AgentNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
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
        return agent
    except AgentNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
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
        return {"message": "Agent deleted successfully"}
    except AgentNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
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
        # Get agent
        agent = await AgentService.get_agent(db, agent_id)
        
        # Check if agent is available
        if agent.status != "active" or (agent.execution_status and agent.execution_status.get("state") != "idle"):
            raise AgentBusyError(
                agent_id=agent_id,
                current_task=agent.current_task
            )
        
        # Get CrewAI agent instance
        crew_agent = await AgentService.get_agent_instance(db, agent_id)
        
        # Generate task ID and update status
        task_id = str(uuid.uuid4())
        await AgentService.update_agent_status(
            db, 
            agent_id, 
            "working",
            execution_status={
                "state": "executing",
                "task_id": task_id,
                "progress": 0,
                "message": f"Starting task: {task_data.task}"
            }
        )
        
        # Execute task in background
        background_tasks.add_task(
            AgentService.execute_task,
            db,
            agent_id,
            task_id,
            crew_agent,
            task_data
        )
        
        return TaskResponse(
            task_id=task_id,
            agent_id=agent_id,
            status="started",
            message="Task execution started"
        )
        
    except AgentError as e:
        # Reset agent status on error
        if 'agent_id' in locals():
            await AgentService.update_agent_status(
                db, 
                agent_id, 
                "active",
                execution_status={"state": "idle", "error": str(e)}
            )
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        # Reset agent status on error
        if 'agent_id' in locals():
            await AgentService.update_agent_status(
                db, 
                agent_id, 
                "active",
                execution_status={"state": "idle", "error": str(e)}
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/{agent_id}/ws")
async def agent_websocket(
    websocket: WebSocket,
    agent_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time agent updates."""
    try:
        # Verify agent exists
        await AgentService.get_agent(db, agent_id)
        
        # Accept connection
        await ws_manager.connect(websocket, agent_id)
        
        try:
            while True:
                # Keep connection alive and handle client messages
                data = await websocket.receive_json()
                
                # Handle client messages if needed
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)
            
    except AgentNotFoundError as e:
        # Reject connection if agent doesn't exist
        await websocket.close(code=4004, reason=str(e))
    except Exception as e:
        # Handle other errors
        await websocket.close(code=4000, reason=str(e)) 