from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any

class AgentError(Exception):
    """Base exception for agent-related errors."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class AgentNotFoundError(AgentError):
    """Raised when an agent is not found."""
    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent not found: {agent_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"agent_id": agent_id}
        )

class AgentBusyError(AgentError):
    """Raised when an agent is busy with another task."""
    def __init__(self, agent_id: str, current_task: Optional[str] = None):
        super().__init__(
            message=f"Agent is busy: {agent_id}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "agent_id": agent_id,
                "current_task": current_task
            }
        )

class TaskExecutionError(AgentError):
    """Raised when task execution fails."""
    def __init__(self, task_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Task execution failed: {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={
                "task_id": task_id,
                **(details or {})
            }
        )

async def agent_error_handler(request: Request, exc: AgentError):
    """Global exception handler for agent-related errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": type(exc).__name__
        }
    ) 