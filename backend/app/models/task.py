"""Task model module."""
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Integer, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Task(Base):
    """Task model."""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    status = Column(String, default="pending")  # pending, executing, completed, failed, cancelled, retry_scheduled
    result = Column(JSON, nullable=True)
    error = Column(JSON, nullable=True)
    tools = Column(JSON, default=list)
    context = Column(JSON, default=dict)
    agent_id = Column(String, ForeignKey("agents.id"))
    priority = Column(Integer, default=1)
    requires_delegation = Column(Boolean, default=False)
    execution_params = Column(JSON, default=dict)
    
    # Metrics and monitoring
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)
    retry_count = Column(Integer, default=0)
    retry_config = Column(JSON, nullable=True)
    metrics = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="tasks")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Task {self.id}: {self.title} ({self.status})>" 