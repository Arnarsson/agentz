"""Agent schema module."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AgentBase(BaseModel):
    """Base schema for agent."""
    role: str = Field(..., description="The role of the agent")
    goal: str = Field(..., description="The goal of the agent")
    backstory: str = Field(..., description="The backstory of the agent")
    allow_delegation: bool = Field(True, description="Whether the agent can delegate tasks")
    verbose: bool = Field(True, description="Whether the agent should be verbose")
    memory: Dict[str, Any] = Field(default_factory=dict, description="The agent's memory configuration")
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="The tools available to the agent")
    llm_config: Dict[str, Any] = Field(default_factory=dict, description="The LLM configuration for the agent")
    max_iterations: int = Field(5, description="Maximum number of iterations for task execution")

class AgentCreate(AgentBase):
    """Schema for creating an agent."""
    pass

class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    role: Optional[str] = None
    goal: Optional[str] = None
    backstory: Optional[str] = None
    allow_delegation: Optional[bool] = None
    verbose: Optional[bool] = None
    memory: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    llm_config: Optional[Dict[str, Any]] = None
    max_iterations: Optional[int] = None
    status: Optional[str] = None
    execution_status: Optional[Dict[str, Any]] = None

class AgentResponse(AgentBase):
    """Schema for agent response."""
    id: str
    status: str
    execution_status: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True 