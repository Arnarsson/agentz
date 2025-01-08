"""
Pydantic models for agent request/response validation.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class AgentBase(BaseModel):
    """Base schema for agent data."""
    name: str = Field(..., description="The name of the agent")
    description: Optional[str] = Field(None, description="A description of the agent's purpose")
    type: str = Field(..., description="The type of agent (e.g., 'assistant', 'researcher', 'analyst')")
    config: Dict[str, Any] = Field(default_factory=dict, description="JSON configuration for the agent")

class AgentCreate(AgentBase):
    """Schema for creating a new agent."""
    pass

class AgentUpdate(BaseModel):
    """Schema for updating an existing agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class AgentInDB(AgentBase):
    """Schema for agent data from database."""
    id: str
    status: str
    is_active: bool
    owner_id: str
    error_count: int
    version: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        """Pydantic config."""
        from_attributes = True

class AgentResponse(AgentInDB):
    """Schema for agent response."""
    pass 