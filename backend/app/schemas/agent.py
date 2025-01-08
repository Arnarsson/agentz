from pydantic import Field, validator
from typing import Optional, Dict, Any, List
from .base import BaseSchema

class ToolConfig(BaseSchema):
    """Configuration for agent tools."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    function: str = Field(..., description="Function name or reference")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Tool parameters")

class LLMConfig(BaseSchema):
    """Configuration for agent's LLM."""
    model: str = Field("gpt-4", description="LLM model to use")
    temperature: float = Field(0.7, description="Temperature for LLM responses")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for responses")
    streaming: bool = Field(False, description="Enable streaming responses")

class AgentBase(BaseSchema):
    """Base schema for agent data."""
    role: str = Field(..., min_length=1, description="Agent's role or title")
    goal: str = Field(..., min_length=1, description="Agent's primary goal or objective")
    backstory: Optional[str] = Field(None, description="Agent's background story")
    allow_delegation: bool = Field(True, description="Whether agent can delegate tasks")
    verbose: bool = Field(False, description="Enable verbose logging")
    memory: Optional[Dict[str, Any]] = Field(None, description="Agent's memory state")
    tools: Optional[List[ToolConfig]] = Field(default_factory=list, description="Agent's available tools")
    llm_config: Optional[LLMConfig] = Field(None, description="Agent's LLM configuration")
    max_iterations: Optional[int] = Field(None, description="Maximum iterations for task execution")
    
    @validator('role')
    def validate_role(cls, v):
        if not v.strip():
            raise ValueError('Role cannot be empty')
        return v.strip()
    
    @validator('goal')
    def validate_goal(cls, v):
        if not v.strip():
            raise ValueError('Goal cannot be empty')
        return v.strip()

class AgentCreate(AgentBase):
    """Schema for creating a new agent."""
    pass

class AgentUpdate(AgentBase):
    """Schema for updating an existing agent."""
    role: Optional[str] = None
    goal: Optional[str] = None

class AgentInDB(AgentBase):
    """Schema for agent as stored in database."""
    id: str = Field(..., description="Unique identifier for the agent")
    created_at: str = Field(..., description="Timestamp of creation")
    updated_at: str = Field(..., description="Timestamp of last update")

class AgentResponse(AgentBase):
    """Schema for agent response."""
    id: str = Field(..., description="Unique identifier for the agent")
    status: str = Field("active", description="Current status of the agent")
    created_at: str = Field(..., description="Timestamp of creation")
    updated_at: str = Field(..., description="Timestamp of last update")
    current_task: Optional[str] = Field(None, description="ID of current task being executed")
    execution_status: Optional[Dict[str, Any]] = Field(None, description="Current execution status and metrics") 