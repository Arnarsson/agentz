"""Task service module."""
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.core.errors import TaskError
from app.core.logging import log_task_action

class TaskService:
    """Service for managing tasks."""
    
    @staticmethod
    async def create_task(db: AsyncSession, task_data: TaskCreate) -> Task:
        """Create a new task."""
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
                metrics={},
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
                    "agent_id": task_data.agent_id
                }
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
            raise

    @staticmethod
    async def get_task(db: AsyncSession, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        result = await db.execute(select(Task).filter(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise TaskError(f"Task {task_id} not found")
        return task

    @staticmethod
    async def list_tasks(
        db: AsyncSession,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """List tasks with optional filters."""
        query = select(Task)
        
        if agent_id:
            query = query.filter(Task.agent_id == agent_id)
        if status:
            query = query.filter(Task.status == status)
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_task(
        db: AsyncSession,
        task_id: str,
        task_data: TaskUpdate
    ) -> Task:
        """Update task."""
        db_task = await TaskService.get_task(db, task_id)
        if not db_task:
            raise TaskError(f"Task {task_id} not found")

        try:
            # Update task attributes
            update_data = task_data.dict(exclude_unset=True)
            if update_data:
                update_data["updated_at"] = datetime.utcnow()
                for field, value in update_data.items():
                    setattr(db_task, field, value)

            await db.commit()
            await db.refresh(db_task)
            
            log_task_action(
                task_id=task_id,
                action="update",
                details={"updated_fields": list(update_data.keys())}
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
            raise

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: str) -> bool:
        """Delete task."""
        db_task = await TaskService.get_task(db, task_id)
        if not db_task:
            raise TaskError(f"Task {task_id} not found")

        try:
            await db.delete(db_task)
            await db.commit()
            
            log_task_action(
                task_id=task_id,
                action="delete",
                details={"title": db_task.title}
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
            raise 