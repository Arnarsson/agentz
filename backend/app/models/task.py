"""Task model module."""
from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base import Base

class Task(Base):
    """Task model."""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    error = Column(String, nullable=True)
    result = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    execution_time = Column(Integer, nullable=True)  # in seconds
    retry_count = Column(Integer, nullable=False, default=0)
    retry_config = Column(Text, nullable=False, default="{}")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    workflow_id = Column(String, ForeignKey("workflows.id"))
    agent_id = Column(String, ForeignKey("agents.id"))

    # Relationships
    workflow = relationship("Workflow", back_populates="tasks")
    agent = relationship("Agent", back_populates="tasks") 