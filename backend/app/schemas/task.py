from pydantic import Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base import BaseSchema

class TaskMetrics(BaseSchema):
    """Schema for task execution metrics."""
    execution_time: Optional[float] = Field(None, description="Task execution time in seconds")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    iterations: Optional[int] = Field(None, description="Number of iterations performed")
    memory_usage: Optional[Dict[str, Any]] = Field(None, description="Memory state changes")

class TaskHistoryBase(BaseSchema):
    """Base schema for task history."""
    task: str = Field(..., description="Task description or prompt")
    context: Optional[Dict[str, Any]] = Field(None, description="Task execution context")
    tools_used: Optional[List[Dict[str, Any]]] = Field(None, description="Tools used during execution")
    result: Optional[Dict[str, Any]] = Field(None, description="Task execution result")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if task failed")
    metrics: Optional[TaskMetrics] = Field(None, description="Task execution metrics")

class TaskHistoryCreate(TaskHistoryBase):
    """Schema for creating task history."""
    agent_id: str = Field(..., description="ID of the agent that executed the task")

class TaskHistoryUpdate(TaskHistoryBase):
    """Schema for updating task history."""
    status: Optional[str] = Field(None, description="Task status")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")

class TaskHistoryResponse(TaskHistoryBase):
    """Schema for task history response."""
    id: str = Field(..., description="Task history ID")
    agent_id: str = Field(..., description="Agent ID")
    status: str = Field(..., description="Task status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")

class TaskAnalytics(BaseSchema):
    """Schema for task analytics."""
    total_tasks: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    failed_tasks: int = Field(..., description="Number of failed tasks")
    average_execution_time: Optional[float] = Field(None, description="Average execution time")
    total_tokens_used: Optional[int] = Field(None, description="Total tokens used")
    success_rate: float = Field(..., description="Task success rate")
    common_errors: Optional[List[Dict[str, Any]]] = Field(None, description="Most common errors")
    tools_usage: Optional[Dict[str, int]] = Field(None, description="Tool usage statistics")

class TimeRange(BaseSchema):
    """Schema for time range queries."""
    start_time: Optional[str] = Field(None, description="Start time (ISO format)")
    end_time: Optional[str] = Field(None, description="End time (ISO format)")

    def get_start_time(self) -> Optional[datetime]:
        """Convert start_time string to datetime."""
        return datetime.fromisoformat(self.start_time) if self.start_time else None

    def get_end_time(self) -> Optional[datetime]:
        """Convert end_time string to datetime."""
        return datetime.fromisoformat(self.end_time) if self.end_time else None 