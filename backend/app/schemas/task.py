"""Task schema module."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .retry import RetryConfig

class TaskMetrics(BaseModel):
    """Task metrics schema."""
    execution_time: Optional[float] = None
    retry_count: int = 0
    tokens_used: Optional[int] = None
    memory_usage: Optional[float] = None
    success_rate: Optional[float] = None
    tool_usage: Dict[str, int] = Field(default_factory=dict)

class TaskBase(BaseModel):
    """Base schema for task."""
    title: str = Field(..., description="The title of the task")
    description: str = Field(..., description="The description of the task")
    priority: int = Field(default=1, description="Task priority (higher number = higher priority)")
    requires_delegation: bool = Field(default=False, description="Whether the task requires delegation")
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="The tools required for the task")
    context: Dict[str, Any] = Field(default_factory=dict, description="The context for the task")
    execution_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for task execution")

class TaskCreate(TaskBase):
    """Schema for creating a task."""
    agent_id: str = Field(..., description="The ID of the agent assigned to the task")
    retry_config: Optional[RetryConfig] = None

class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    context: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None
    priority: Optional[int] = None
    requires_delegation: Optional[bool] = None
    execution_params: Optional[Dict[str, Any]] = None
    retry_config: Optional[RetryConfig] = None
    metrics: Optional[TaskMetrics] = None

class TaskResponse(TaskBase):
    """Schema for task response."""
    id: str
    status: str = Field(..., description="Task status (pending, executing, completed, failed, cancelled, retry_scheduled)")
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    agent_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    retry_config: Optional[RetryConfig] = None
    metrics: TaskMetrics = Field(default_factory=TaskMetrics)
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True

class TaskHistory(BaseModel):
    """Schema for task history."""
    task_id: str
    status: str
    agent_id: str
    timestamp: datetime
    details: Dict[str, Any] = Field(default_factory=dict)
    metrics: Optional[TaskMetrics] = None

class TaskAnalytics(BaseModel):
    """Schema for task analytics."""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_execution_time: Optional[float] = None
    success_rate: float
    retry_rate: float
    common_errors: List[Dict[str, Any]] = Field(default_factory=list)
    tool_usage: Dict[str, int] = Field(default_factory=dict)
    performance_by_priority: Dict[int, Dict[str, Any]] = Field(default_factory=dict) 