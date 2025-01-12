"""Task service module with enhanced task management features."""
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResult
from app.core.errors import TaskError, TaskNotFoundError, TaskStateError
from app.core.logging import log_task_action
from app.core.websocket import ws_manager
from app.core.celery_app import celery_app

class TaskService:
    """Service for managing tasks with enhanced features."""
    
    @staticmethod
    async def create_task(db: AsyncSession, task_data: TaskCreate) -> Task:
        """Create a new task with full configuration."""
        try:
            now = datetime.utcnow()
            task_id = str(uuid.uuid4())
            
            db_task = Task(
                id=task_id,
                title=task_data.title,
                description=task_data.description,
                agent_id=task_data.agent_id,
                priority=task_data.priority,
                requires_delegation=task_data.requires_delegation,
                execution_params=task_data.execution_params,
                status="pending",
                error=None,
                start_time=None,
                end_time=None,
                execution_time=None,
                retry_count=0,
                retry_config=task_data.retry_config,
                metrics={
                    "tokens_used": 0,
                    "api_calls": 0,
                    "memory_usage": 0,
                    "cost": 0.0,
                    "performance_metrics": {}
                },
                created_at=now,
                updated_at=now
            )
            
            db.add(db_task)
            await db.commit()
            await db.refresh(db_task)
            
            log_task_action(
                task_id=task_id,
                action="create",
                details={
                    "title": task_data.title,
                    "agent_id": task_data.agent_id,
                    "priority": task_data.priority
                }
            )
            
            # Broadcast task creation via WebSocket
            await ws_manager.broadcast_task_update(
                task_id=task_id,
                status="created",
                details=db_task.dict()
            )
            
            return db_task
            
        except Exception as e:
            log_task_action(
                task_id=task_id if 'task_id' in locals() else "unknown",
                action="create",
                details={"error": str(e)},
                status="error",
                error=e
            )
            raise TaskError(f"Failed to create task: {str(e)}")

    @staticmethod
    async def get_task(db: AsyncSession, task_id: str) -> Optional[Task]:
        """Get task by ID with error handling."""
        result = await db.execute(select(Task).filter(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return task

    @staticmethod
    async def list_tasks(
        db: AsyncSession,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        requires_delegation: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """List tasks with enhanced filtering options."""
        query = select(Task)
        
        filters = []
        if agent_id:
            filters.append(Task.agent_id == agent_id)
        if status:
            filters.append(Task.status == status)
        if priority:
            filters.append(Task.priority == priority)
        if requires_delegation is not None:
            filters.append(Task.requires_delegation == requires_delegation)
        if start_date:
            filters.append(Task.created_at >= start_date)
        if end_date:
            filters.append(Task.created_at <= end_date)
            
        if filters:
            query = query.filter(and_(*filters))
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_task(
        db: AsyncSession,
        task_id: str,
        task_data: TaskUpdate
    ) -> Task:
        """Update task with enhanced error handling and metrics tracking."""
        db_task = await TaskService.get_task(db, task_id)
        if not db_task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        try:
            # Update task attributes
            update_data = task_data.dict(exclude_unset=True)
            if update_data:
                update_data["updated_at"] = datetime.utcnow()
                
                # Handle status transitions
                if "status" in update_data:
                    new_status = update_data["status"]
                    if new_status == "executing" and not db_task.start_time:
                        update_data["start_time"] = datetime.utcnow()
                    elif new_status in ["completed", "failed", "cancelled"]:
                        update_data["end_time"] = datetime.utcnow()
                        if db_task.start_time:
                            update_data["execution_time"] = (
                                update_data["end_time"] - db_task.start_time
                            ).total_seconds()
                
                for field, value in update_data.items():
                    setattr(db_task, field, value)

            await db.commit()
            await db.refresh(db_task)
            
            log_task_action(
                task_id=task_id,
                action="update",
                details={
                    "updated_fields": list(update_data.keys()),
                    "new_status": update_data.get("status")
                }
            )
            
            # Broadcast task update via WebSocket
            await ws_manager.broadcast_task_update(
                task_id=task_id,
                status=db_task.status,
                details=db_task.dict()
            )
            
            return db_task
            
        except Exception as e:
            log_task_action(
                task_id=task_id,
                action="update",
                details={"error": str(e)},
                status="error",
                error=e
            )
            raise TaskError(f"Failed to update task: {str(e)}")

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: str) -> bool:
        """Delete task with enhanced error handling."""
        db_task = await TaskService.get_task(db, task_id)
        if not db_task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        try:
            await db.delete(db_task)
            await db.commit()
            
            log_task_action(
                task_id=task_id,
                action="delete",
                details={
                    "title": db_task.title,
                    "status": db_task.status
                }
            )
            
            # Broadcast task deletion via WebSocket
            await ws_manager.broadcast_task_update(
                task_id=task_id,
                status="deleted",
                details={"task_id": task_id}
            )
            
            return True
            
        except Exception as e:
            log_task_action(
                task_id=task_id,
                action="delete",
                details={"error": str(e)},
                status="error",
                error=e
            )
            raise TaskError(f"Failed to delete task: {str(e)}")

    @staticmethod
    async def update_task_metrics(
        db: AsyncSession,
        task_id: str,
        metrics_update: Dict[str, Any]
    ) -> Task:
        """Update task metrics."""
        try:
            db_task = await TaskService.get_task(db, task_id)
            if not db_task:
                raise TaskNotFoundError(f"Task {task_id} not found")

            # Update metrics
            current_metrics = db_task.metrics or {}
            current_metrics.update(metrics_update)
            db_task.metrics = current_metrics
            db_task.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(db_task)

            # Broadcast metrics update via WebSocket
            await ws_manager.broadcast_task_metrics(
                task_id=task_id,
                metrics=db_task.metrics
            )

            return db_task

        except Exception as e:
            raise TaskError(f"Failed to update task metrics: {str(e)}")

    @staticmethod
    async def retry_task(db: AsyncSession, task_id: str) -> Task:
        """Retry a failed task."""
        try:
            db_task = await TaskService.get_task(db, task_id)
            if not db_task:
                raise TaskNotFoundError(f"Task {task_id} not found")

            if db_task.status not in ["failed", "cancelled"]:
                raise TaskStateError(
                    f"Cannot retry task in state: {db_task.status}"
                )

            # Check retry limits
            if db_task.retry_config:
                max_retries = db_task.retry_config.get("max_retries", 3)
                if db_task.retry_count >= max_retries:
                    raise TaskError(f"Max retry attempts ({max_retries}) reached")

            # Update task for retry
            update_data = {
                "status": "pending",
                "error": None,
                "start_time": None,
                "end_time": None,
                "execution_time": None,
                "retry_count": db_task.retry_count + 1,
                "updated_at": datetime.utcnow()
            }

            for field, value in update_data.items():
                setattr(db_task, field, value)

            await db.commit()
            await db.refresh(db_task)

            # Broadcast task retry via WebSocket
            await ws_manager.broadcast_task_update(
                task_id=task_id,
                status="retry",
                details=db_task.dict()
            )

            return db_task

        except Exception as e:
            raise TaskError(f"Failed to retry task: {str(e)}")

    @staticmethod
    async def store_task_result(
        db: AsyncSession,
        task_id: str,
        result: TaskResult
    ) -> Task:
        """Store task execution result."""
        try:
            db_task = await TaskService.get_task(db, task_id)
            if not db_task:
                raise TaskNotFoundError(f"Task {task_id} not found")

            # Update task with result
            update_data = {
                "status": "completed",
                "result": result.result,
                "end_time": datetime.utcnow(),
                "execution_time": (
                    datetime.utcnow() - db_task.start_time
                ).total_seconds() if db_task.start_time else None,
                "metrics": {
                    **(db_task.metrics or {}),
                    **result.metrics
                } if result.metrics else db_task.metrics,
                "updated_at": datetime.utcnow()
            }

            for field, value in update_data.items():
                setattr(db_task, field, value)

            await db.commit()
            await db.refresh(db_task)

            # Broadcast task completion via WebSocket
            await ws_manager.broadcast_task_update(
                task_id=task_id,
                status="completed",
                details=db_task.dict()
            )

            return db_task

        except Exception as e:
            raise TaskError(f"Failed to store task result: {str(e)}")

    @staticmethod
    async def get_task_history(
        db: AsyncSession,
        task_id: str
    ) -> List[Dict[str, Any]]:
        """Get task execution history."""
        try:
            db_task = await TaskService.get_task(db, task_id)
            if not db_task:
                raise TaskNotFoundError(f"Task {task_id} not found")

            # Compile task history
            history = []
            if db_task.start_time:
                history.append({
                    "timestamp": db_task.start_time,
                    "event": "started",
                    "details": {"status": "executing"}
                })
            if db_task.end_time:
                history.append({
                    "timestamp": db_task.end_time,
                    "event": "completed" if db_task.status == "completed" else "failed",
                    "details": {
                        "status": db_task.status,
                        "execution_time": db_task.execution_time,
                        "error": db_task.error
                    }
                })
            if db_task.retry_count > 0:
                history.append({
                    "timestamp": db_task.updated_at,
                    "event": "retried",
                    "details": {"retry_count": db_task.retry_count}
                })

            return sorted(history, key=lambda x: x["timestamp"])

        except Exception as e:
            raise TaskError(f"Failed to get task history: {str(e)}")

    @staticmethod
    async def cancel_task(db: AsyncSession, task_id: str) -> Task:
        """Cancel a running or pending task."""
        try:
            db_task = await TaskService.get_task(db, task_id)
            if not db_task:
                raise TaskNotFoundError(f"Task {task_id} not found")

            if db_task.status not in ["pending", "executing"]:
                raise TaskStateError(
                    f"Cannot cancel task in state: {db_task.status}"
                )

            # Update task status
            update_data = {
                "status": "cancelled",
                "end_time": datetime.utcnow(),
                "execution_time": (
                    datetime.utcnow() - db_task.start_time
                ).total_seconds() if db_task.start_time else None,
                "updated_at": datetime.utcnow()
            }

            for field, value in update_data.items():
                setattr(db_task, field, value)

            await db.commit()
            await db.refresh(db_task)

            # Broadcast task cancellation via WebSocket
            await ws_manager.broadcast_task_update(
                task_id=task_id,
                status="cancelled",
                details=db_task.dict()
            )

            return db_task

        except Exception as e:
            raise TaskError(f"Failed to cancel task: {str(e)}")

    @staticmethod
    async def get_task_metrics_summary(
        db: AsyncSession,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get summary of task metrics."""
        try:
            query = select(Task)
            
            filters = []
            if agent_id:
                filters.append(Task.agent_id == agent_id)
            if start_date:
                filters.append(Task.created_at >= start_date)
            if end_date:
                filters.append(Task.created_at <= end_date)
                
            if filters:
                query = query.filter(and_(*filters))
                
            result = await db.execute(query)
            tasks = result.scalars().all()

            # Compile metrics summary
            summary = {
                "total_tasks": len(tasks),
                "completed_tasks": len([t for t in tasks if t.status == "completed"]),
                "failed_tasks": len([t for t in tasks if t.status == "failed"]),
                "cancelled_tasks": len([t for t in tasks if t.status == "cancelled"]),
                "average_execution_time": sum(
                    t.execution_time or 0 for t in tasks if t.execution_time
                ) / len([t for t in tasks if t.execution_time]) if tasks else 0,
                "total_retries": sum(t.retry_count or 0 for t in tasks),
                "metrics_aggregation": {
                    "total_tokens": sum(
                        t.metrics.get("tokens_used", 0) for t in tasks if t.metrics
                    ),
                    "total_api_calls": sum(
                        t.metrics.get("api_calls", 0) for t in tasks if t.metrics
                    ),
                    "total_cost": sum(
                        t.metrics.get("cost", 0.0) for t in tasks if t.metrics
                    )
                }
            }

            return summary

        except Exception as e:
            raise TaskError(f"Failed to get task metrics summary: {str(e)}") 