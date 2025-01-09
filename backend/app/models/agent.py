"""Agent model module."""
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Agent(Base):
    """Agent model."""
    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True)
    role = Column(String, unique=True, index=True)
    goal = Column(String)
    backstory = Column(String)
    allow_delegation = Column(Boolean, default=True)
    verbose = Column(Boolean, default=True)
    memory = Column(JSON, default=dict)
    tools = Column(JSON, default=list)
    llm_config = Column(JSON, default=dict)
    max_iterations = Column(Integer, default=5)
    status = Column(String, default="active")
    execution_status = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="agent")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Agent {self.id}: {self.role}>" 