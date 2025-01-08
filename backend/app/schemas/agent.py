from pydantic import Field, validator
from typing import Optional, Dict, Any
from .base import BaseSchema

class AgentBase(BaseSchema):
    """Base schema for agent data."""
    role: str = Field(..., min_length=1, description="Agent's role or title")
    goal: str = Field(..., min_length=1, description="Agent's primary goal or objective")
    backstory: Optional[str] = Field(None, description="Agent's background story")
    allow_delegation: bool = Field(True, description="Whether agent can delegate tasks")
    verbose: bool = Field(False, description="Enable verbose logging")
    memory: Optional[Dict[str, Any]] = Field(None, description="Agent's memory state")
    
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
    pass

class AgentResponse(AgentBase):
    """Schema for agent response."""
    status: str = Field("active", description="Current status of the agent") 