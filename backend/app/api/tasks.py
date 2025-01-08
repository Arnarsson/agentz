from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Any
from crewai import Task
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.task import (
    TaskHistoryResponse,
    TaskAnalytics,
    TimeRange
)
from app.services.task_history import TaskHistoryService
from app.core.errors import AgentError

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

@router.get("/{task_id}", response_model=TaskHistoryResponse)
async def get_task_history(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get task history by ID."""
    try:
        task = await TaskHistoryService.get_task_history(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task history not found")
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/{agent_id}", response_model=List[TaskHistoryResponse])
async def list_agent_tasks(
    agent_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List task history for an agent."""
    try:
        time_range = TimeRange(start_time=start_time, end_time=end_time)
        tasks = await TaskHistoryService.list_agent_tasks(
            db,
            agent_id,
            time_range=time_range,
            skip=skip,
            limit=limit
        )
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/{agent_id}/analytics", response_model=TaskAnalytics)
async def get_agent_analytics(
    agent_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get analytics for an agent's tasks."""
    try:
        time_range = TimeRange(start_time=start_time, end_time=end_time)
        analytics = await TaskHistoryService.get_agent_analytics(
            db,
            agent_id,
            time_range=time_range
        )
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/{agent_id}/analytics/refresh")
async def refresh_agent_analytics(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Refresh analytics summary for an agent."""
    try:
        await TaskHistoryService.update_agent_analytics_summary(db, agent_id)
        return {"message": "Analytics summary updated successfully"}
    except AgentError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 