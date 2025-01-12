"""Agent model module."""
from datetime import datetime
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base import Base

class Agent(Base):
    """Agent model."""
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    description = Column(String, nullable=True)
    prompt_template = Column(String, nullable=True)
    goal = Column(String, nullable=True)
    backstory = Column(String, nullable=True)
    memory = Column(Text, nullable=False, default="{}")
    tools = Column(Text, nullable=False, default="[]")
    llm_config = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")
    error = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    workflow_id = Column(String, ForeignKey("workflows.id"))

    # Relationships
    workflow = relationship("Workflow", back_populates="agents")
    tasks = relationship("Task", back_populates="agent", cascade="all, delete-orphan") 