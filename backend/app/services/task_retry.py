"""Task retry service module."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.task import TaskRetry, TaskUpdate
from app.core.errors import TaskError
from app.services.task import TaskService

class TaskRetryService:
    """Service for handling task retries with exponential backoff."""

    @staticmethod
    def calculate_next_retry(retry_config: TaskRetry) -> datetime:
        """Calculate next retry time using exponential backoff."""
        if retry_config.current_attempt >= retry_config.max_attempts:
            raise TaskError("Maximum retry attempts exceeded")

        # Calculate delay with exponential backoff: base_delay * 2^attempt
        delay = min(
            retry_config.base_delay * (2 ** retry_config.current_attempt),
            retry_config.max_delay
        )
        return datetime.utcnow() + timedelta(seconds=delay)

    @staticmethod
    async def should_retry(
        db: AsyncSession,
        task_id: str,
        error: Exception
    ) -> bool:
        """Determine if a task should be retried based on error and config."""
        task = await TaskService.get_task(db, task_id)
        if not task or not task.retry_config:
            return False

        retry_config = TaskRetry(**task.retry_config)
        
        # Don't retry if max attempts reached
        if retry_config.current_attempt >= retry_config.max_attempts:
            return False

        # Don't retry certain errors (can be expanded)
        non_retryable_errors = [
            "InvalidInputError",
            "AuthenticationError",
            "PermissionError"
        ]
        if any(err in str(error) for err in non_retryable_errors):
            return False

        return True

    @staticmethod
    async def schedule_retry(
        db: AsyncSession,
        task_id: str,
        error: Exception
    ) -> Optional[datetime]:
        """Schedule a task for retry."""
        task = await TaskService.get_task(db, task_id)
        if not task or not task.retry_config:
            return None

        retry_config = TaskRetry(**task.retry_config)
        
        # Update retry configuration
        retry_config.current_attempt += 1
        retry_config.last_attempt = datetime.utcnow()
        retry_config.next_attempt = TaskRetryService.calculate_next_retry(retry_config)
        retry_config.errors.append(str(error))

        # Update task with new retry config and status
        await TaskService.update_task(
            db,
            task_id,
            TaskUpdate(
                status="retry_scheduled",
                retry_config=retry_config.dict(),
                metrics={
                    "retry_count": retry_config.current_attempt,
                    "success_rate": 0.0,  # Will be updated on successful completion
                    "last_error": str(error)
                }
            )
        )

        return retry_config.next_attempt

    @staticmethod
    async def execute_retry(
        db: AsyncSession,
        task_id: str
    ) -> Dict[str, Any]:
        """Execute a retry attempt for a task."""
        # Import here to avoid circular imports
        from app.services.agent import AgentService

        task = await TaskService.get_task(db, task_id)
        if not task:
            raise TaskError(f"Task {task_id} not found")

        # Get the agent
        agent = await AgentService.get_agent(db, task.agent_id)
        if not agent:
            raise TaskError(f"Agent {task.agent_id} not found")

        try:
            # Execute the task
            result = await AgentService.execute_task(db, agent.id, task_id)

            # Update success metrics
            retry_config = TaskRetry(**task.retry_config)
            success_rate = (retry_config.max_attempts - retry_config.current_attempt) / retry_config.max_attempts
            
            await TaskService.update_task(
                db,
                task_id,
                TaskUpdate(
                    status="completed",
                    metrics={
                        "success_rate": success_rate,
                        "retry_count": retry_config.current_attempt
                    }
                )
            )

            return result

        except Exception as e:
            # Check if we should retry again
            if await TaskRetryService.should_retry(db, task_id, e):
                next_retry = await TaskRetryService.schedule_retry(db, task_id, e)
                return {
                    "status": "retry_scheduled",
                    "next_retry": next_retry,
                    "error": str(e)
                }
            else:
                # Mark as failed if no more retries
                await TaskService.update_task(
                    db,
                    task_id,
                    TaskUpdate(
                        status="failed",
                        error=str(e)
                    )
                )
                raise TaskError(f"Task failed after {task.retry_config['current_attempt']} retries: {str(e)}") 