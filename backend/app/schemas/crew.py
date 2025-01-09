"""
Pydantic models for crew management.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .agent import LLMConfig

class WorkflowConfig(BaseModel):
    """Configuration for crew workflows."""
    tasks: List[Dict[str, Any]] = Field(..., description="List of tasks in the workflow")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Task dependencies")
    timeout: Optional[int] = Field(None, description="Workflow timeout in seconds")
    retry_policy: Dict[str, Any] = Field(default_factory=dict, description="Retry configuration")
    output_handlers: Dict[str, Any] = Field(default_factory=dict, description="Output handling configuration")

class CrewMetrics(BaseModel):
    """Metrics for crew performance."""
    total_tasks: int = Field(default=0, description="Total number of tasks executed")
    successful_tasks: int = Field(default=0, description="Number of successful tasks")
    failed_tasks: int = Field(default=0, description="Number of failed tasks")
    average_completion_time: float = Field(default=0.0, description="Average task completion time")
    agent_performance: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Per-agent performance metrics")
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")

class CrewState(BaseModel):
    """Current state of a crew."""
    status: str = Field(..., description="Current status (idle, executing, error)")
    current_task: Optional[str] = Field(None, description="ID of current task")
    progress: int = Field(default=0, description="Workflow progress percentage")
    last_error: Optional[str] = Field(None, description="Last error message")

class CrewBase(BaseModel):
    """Base schema for crew data."""
    name: str = Field(..., description="Name of the crew")
    description: Optional[str] = Field(None, description="Description of the crew's purpose")
    agent_ids: List[str] = Field(..., description="List of agent IDs in the crew")
    process_type: str = Field(default="sequential", description="Process type (sequential, hierarchical)")
    workflow_config: Optional[WorkflowConfig] = Field(None, description="Workflow configuration")
    verbose: bool = Field(default=True, description="Whether to log detailed information")
    max_iterations: int = Field(default=5, description="Maximum workflow iterations")
    manager_llm_config: Optional[LLMConfig] = Field(None, description="LLM config for manager agent")

class CrewCreate(CrewBase):
    """Schema for creating a new crew."""
    pass

class CrewUpdate(BaseModel):
    """Schema for updating an existing crew."""
    name: Optional[str] = None
    description: Optional[str] = None
    agent_ids: Optional[List[str]] = None
    process_type: Optional[str] = None
    workflow_config: Optional[WorkflowConfig] = None
    verbose: Optional[bool] = None
    max_iterations: Optional[int] = None
    manager_llm_config: Optional[LLMConfig] = None

class CrewInDB(CrewBase):
    """Schema for crew data in database."""
    id: str = Field(..., description="Unique identifier for the crew")
    state: CrewState = Field(..., description="Current crew state")
    metrics: Dict[str, Any] = Field(..., description="Crew performance metrics")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True

class CrewResponse(CrewInDB):
    """Schema for crew response with additional computed fields."""
    agent_count: int = Field(..., description="Number of agents in the crew")
    success_rate: float = Field(..., description="Task success rate percentage")
    total_execution_time: float = Field(..., description="Total execution time in seconds") 