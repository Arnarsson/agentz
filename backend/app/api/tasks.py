from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from crewai import Task

router = APIRouter()

class TaskCreate(BaseModel):
    """Schema for creating a task."""
    description: str
    agent_role: str
    expected_output: Optional[str] = None
    context: Optional[str] = None
    async_execution: bool = False
    output: Optional[Any] = None

class TaskResponse(BaseModel):
    """Schema for task response."""
    description: str
    agent_role: str
    expected_output: Optional[str]
    context: Optional[str]
    async_execution: bool
    output: Optional[Any]

@router.post("/", response_model=TaskResponse)
async def create_task(task_data: TaskCreate):
    """Create a new task."""
    try:
        task = Task(
            description=task_data.description,
            agent=task_data.agent_role,  # This will need to be updated to use actual agent instance
            expected_output=task_data.expected_output,
            context=task_data.context,
            async_execution=task_data.async_execution
        )
        return TaskResponse(
            description=task.description,
            agent_role=task_data.agent_role,  # Using the role since we don't have the agent instance
            expected_output=task.expected_output,
            context=task.context,
            async_execution=task.async_execution,
            output=None  # Task hasn't been executed yet
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[TaskResponse])
async def list_tasks():
    """List all tasks (to be implemented with database)."""
    # TODO: Implement database integration
    return []

@router.post("/{task_id}/execute")
async def execute_task(task_id: str):
    """Execute a specific task (to be implemented)."""
    # TODO: Implement task execution
    raise HTTPException(status_code=501, detail="Not implemented yet") 