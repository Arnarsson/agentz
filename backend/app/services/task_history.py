from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app.models.task import TaskHistory
from app.schemas.task import (
    TaskHistoryCreate,
    TaskHistoryUpdate,
    TaskAnalytics,
    TimeRange,
    TaskMetrics
)
from app.core.logging import log_agent_action
import uuid

class TaskHistoryService:
    """Service for managing task history and analytics."""
    
    @staticmethod
    async def create_task_history(
        db: Session,
        task_data: TaskHistoryCreate,
        metrics: Optional[TaskMetrics] = None
    ) -> TaskHistory:
        """Create a new task history entry."""
        now = datetime.utcnow().isoformat()
        
        db_task = TaskHistory(
            id=str(uuid.uuid4()),
            agent_id=task_data.agent_id,
            task=task_data.task,
            status="executing",
            context=task_data.context,
            tools_used=[],  # Will be updated during execution
            result=None,
            error=None,
            execution_time=metrics.execution_time if metrics else None,
            tokens_used=metrics.tokens_used if metrics else None,
            iterations=metrics.iterations if metrics else None,
            memory_usage=metrics.memory_usage if metrics else None,
            created_at=now,
            updated_at=now
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        log_agent_action(
            agent_id=task_data.agent_id,
            action="task_history_create",
            details={"task_id": db_task.id}
        )
        
        return db_task

    @staticmethod
    async def update_task_history(
        db: Session,
        task_id: str,
        update_data: TaskHistoryUpdate,
        metrics: Optional[TaskMetrics] = None
    ) -> Optional[TaskHistory]:
        """Update a task history entry."""
        db_task = db.query(TaskHistory).filter(TaskHistory.id == task_id).first()
        if not db_task:
            return None
            
        # Update task attributes
        update_dict = update_data.dict(exclude_unset=True)
        if metrics:
            update_dict.update(metrics.dict(exclude_unset=True))
            
        for field, value in update_dict.items():
            setattr(db_task, field, value)
            
        # Update timestamps
        db_task.updated_at = datetime.utcnow().isoformat()
        if update_data.status in ["completed", "error"]:
            db_task.completed_at = datetime.utcnow().isoformat()
            
        db.commit()
        db.refresh(db_task)
        
        log_agent_action(
            agent_id=db_task.agent_id,
            action="task_history_update",
            details={
                "task_id": task_id,
                "status": update_data.status
            }
        )
        
        return db_task

    @staticmethod
    async def get_task_history(
        db: Session,
        task_id: str
    ) -> Optional[TaskHistory]:
        """Get a task history entry by ID."""
        return db.query(TaskHistory).filter(TaskHistory.id == task_id).first()

    @staticmethod
    async def list_agent_tasks(
        db: Session,
        agent_id: str,
        time_range: Optional[TimeRange] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskHistory]:
        """List task history for an agent."""
        query = db.query(TaskHistory).filter(TaskHistory.agent_id == agent_id)
        
        if time_range:
            if time_range.start_time:
                query = query.filter(TaskHistory.created_at >= time_range.start_time)
            if time_range.end_time:
                query = query.filter(TaskHistory.created_at <= time_range.end_time)
                
        return query.order_by(desc(TaskHistory.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    async def get_agent_analytics(
        db: Session,
        agent_id: str,
        time_range: Optional[TimeRange] = None
    ) -> TaskAnalytics:
        """Get analytics for an agent's tasks."""
        query = db.query(TaskHistory).filter(TaskHistory.agent_id == agent_id)
        
        if time_range:
            if time_range.start_time:
                query = query.filter(TaskHistory.created_at >= time_range.start_time)
            if time_range.end_time:
                query = query.filter(TaskHistory.created_at <= time_range.end_time)
        
        # Get basic metrics
        total_tasks = query.count()
        completed_tasks = query.filter(TaskHistory.status == "completed").count()
        failed_tasks = query.filter(TaskHistory.status == "error").count()
        
        # Calculate averages
        avg_execution = db.query(func.avg(TaskHistory.execution_time)).filter(
            TaskHistory.agent_id == agent_id,
            TaskHistory.execution_time.isnot(None)
        ).scalar()
        
        total_tokens = db.query(func.sum(TaskHistory.tokens_used)).filter(
            TaskHistory.agent_id == agent_id,
            TaskHistory.tokens_used.isnot(None)
        ).scalar()
        
        # Get common errors
        error_tasks = query.filter(
            TaskHistory.status == "error",
            TaskHistory.error.isnot(None)
        ).limit(10).all()
        
        common_errors = [
            {
                "error": task.error,
                "task": task.task,
                "timestamp": task.created_at
            }
            for task in error_tasks
        ]
        
        # Calculate tool usage
        tools_usage: Dict[str, int] = {}
        tasks_with_tools = query.filter(TaskHistory.tools_used.isnot(None)).all()
        for task in tasks_with_tools:
            for tool in task.tools_used:
                tool_name = tool.get("name")
                if tool_name:
                    tools_usage[tool_name] = tools_usage.get(tool_name, 0) + 1
        
        return TaskAnalytics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            average_execution_time=float(avg_execution) if avg_execution else None,
            total_tokens_used=int(total_tokens) if total_tokens else None,
            success_rate=completed_tasks / total_tasks if total_tasks > 0 else 0.0,
            common_errors=common_errors,
            tools_usage=tools_usage
        )

    @staticmethod
    async def update_agent_analytics_summary(
        db: Session,
        agent_id: str
    ) -> None:
        """Update the analytics summary stored in the agent record."""
        # Get analytics for different time ranges
        ranges = {
            "last_24h": TimeRange(
                start_time=(datetime.utcnow() - timedelta(days=1)).isoformat()
            ),
            "last_7d": TimeRange(
                start_time=(datetime.utcnow() - timedelta(days=7)).isoformat()
            ),
            "all_time": None
        }
        
        analytics_summary = {}
        for range_name, time_range in ranges.items():
            analytics = await TaskHistoryService.get_agent_analytics(
                db, agent_id, time_range
            )
            analytics_summary[range_name] = analytics.dict()
            
        # Update agent's analytics field
        db.query(TaskHistory).filter(
            TaskHistory.agent_id == agent_id
        ).update({
            "analytics": analytics_summary,
            "updated_at": datetime.utcnow().isoformat()
        })
        
        db.commit() 