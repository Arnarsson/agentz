from sqlalchemy import Column, String, Boolean, JSON, Integer
from sqlalchemy.orm import relationship
from .base import BaseModel

class Agent(BaseModel):
    """SQLAlchemy model for agents."""
    __tablename__ = "agents"

    # Core fields
    id = Column(String, primary_key=True, index=True)
    role = Column(String, nullable=False, unique=True, index=True)
    goal = Column(String, nullable=False)
    backstory = Column(String, nullable=True)
    allow_delegation = Column(Boolean, default=True)
    verbose = Column(Boolean, default=False)
    
    # State and memory
    memory = Column(JSON, nullable=True)
    status = Column(String, default="active")
    execution_status = Column(JSON, nullable=True)
    current_task = Column(String, nullable=True)
    
    # Configuration
    tools = Column(JSON, nullable=True)  # List of ToolConfig
    llm_config = Column(JSON, nullable=True)  # LLMConfig
    max_iterations = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(String, nullable=False)  # ISO format
    updated_at = Column(String, nullable=False)  # ISO format

    # Relationships
    tasks = relationship("TaskHistory", back_populates="agent", cascade="all, delete-orphan")
    
    # Analytics summary (updated periodically)
    analytics = Column(JSON, nullable=True, default=dict)

    def __repr__(self):
        return f"<Agent {self.role}>" 