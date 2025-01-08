"""
Agent model for storing agent configurations and state.
"""
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

class Agent(BaseModel):
    """
    Agent model for storing agent configurations and state.
    
    Attributes:
        name: The name of the agent
        description: A description of the agent's purpose
        type: The type of agent (e.g., "assistant", "researcher", "analyst")
        config: JSON configuration for the agent
        status: Current status of the agent
        is_active: Whether the agent is currently active
        owner_id: The ID of the user who owns this agent
        error_count: Number of errors encountered
        version: Agent version number
    """
    
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(String, nullable=False)
    config = Column(JSON, default={})
    status = Column(String, default="idle")
    is_active = Column(Boolean, default=True)
    owner_id = Column(String, nullable=False)
    error_count = Column(Integer, default=0)
    version = Column(Integer, default=1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the agent to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "config": self.config,
            "status": self.status,
            "is_active": self.is_active,
            "owner_id": self.owner_id,
            "error_count": self.error_count,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        } 