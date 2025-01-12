"""Task management router."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.clerk_middleware import ClerkAuth, TokenPayload
from app.core.database import get_async_db
from app.services.task import TaskService
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskHistory,
    TaskAnalytics, TaskResult
)

router = APIRouter(prefix="/tasks", tags=["tasks"])
clerk_auth = ClerkAuth()

@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    token: TokenPayload = Depends(clerk_auth)
):
    """Create a new task."""
    try:
        task = await TaskService.create_task(db, task_data)
        # Queue task execution in background
        background_tasks.add_task(
            TaskService.execute_task,
            db,
            task.id,
            task_data.execution_params
        )
        return task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_async_db),
    token: TokenPayload = Depends(clerk_auth)
):
    """Get task by ID."""
    try:
        return await TaskService.get_task(db, task_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    requires_delegation: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    token: TokenPayload = Depends(clerk_auth)
):
    """List tasks with filtering options."""
    try:
        return await TaskService.list_tasks(
            db,
            agent_id=agent_id,
            status=status,
            priority=priority,
            requires_delegation=requires_delegation,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_async_db),
    token: TokenPayload = Depends(clerk_auth)
):
    """Update task details."""
    try:
        return await TaskService.update_task(db, task_id, task_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_async_db),
    token: TokenPayload = Depends(clerk_auth)
):
    """Delete a task."""
    try:
        success = await TaskService.delete_task(db, task_id)
        if success:
            return {"message": "Task deleted successfully"}
        raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_async_db),
    token: TokenPayload = Depends(clerk_auth)
):
    """Cancel a running or pending task."""
    try:
        return await TaskService.cancel_task(db, task_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    db: AsyncSession = Depends(get_async_db),
    token: TokenPayload = Depends(clerk_auth)
):
    """Retry a failed task."""
    try:
        return await TaskService.retry_task(db, task_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{task_id}/history", response_model=List[TaskHistory])
async def get_task_history(
    task_id: str,
    db: AsyncSession = Depends(get_async_db),
    token: TokenPayload = Depends(clerk_auth)
):
    """Get task execution history."""
    try:
        return await TaskService.get_task_history(db, task_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{task_id}/result", response_model=TaskResponse)
async def store_task_result(
    task_id: str,
    result: TaskResult,
    db: AsyncSession = Depends(get_async_db),
    token: TokenPayload = Depends(clerk_auth)
):
    """Store task execution result."""
    try:
        return await TaskService.store_task_result(db, task_id, result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analytics/summary", response_model=TaskAnalytics)
async def get_task_analytics(
    agent_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_async_db),
    token: TokenPayload = Depends(clerk_auth)
):
    """Get task analytics summary."""
    try:
        metrics = await TaskService.get_task_metrics_summary(
            db,
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date
        )
        return TaskAnalytics(
            total_tasks=metrics["total_tasks"],
            completed_tasks=metrics["completed_tasks"],
            failed_tasks=metrics["failed_tasks"],
            average_execution_time=metrics["average_execution_time"],
            success_rate=metrics["completed_tasks"] / metrics["total_tasks"] if metrics["total_tasks"] > 0 else 0,
            retry_rate=metrics["total_retries"] / metrics["total_tasks"] if metrics["total_tasks"] > 0 else 0,
            tool_usage=metrics["metrics_aggregation"].get("tool_usage", {}),
            performance_by_priority={}  # TODO: Implement priority-based metrics
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 