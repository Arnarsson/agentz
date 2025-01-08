from sqlalchemy import Column, String, JSON, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class TaskHistory(BaseModel):
    """SQLAlchemy model for task history."""
    __tablename__ = "task_history"

    # Core fields
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    task = Column(String, nullable=False)
    status = Column(String, nullable=False)  # executing, completed, error
    
    # Execution details
    context = Column(JSON, nullable=True)
    tools_used = Column(JSON, nullable=True)  # List of tools used during execution
    result = Column(JSON, nullable=True)
    error = Column(JSON, nullable=True)
    
    # Analytics metrics
    execution_time = Column(Float, nullable=True)  # in seconds
    tokens_used = Column(Integer, nullable=True)
    iterations = Column(Integer, nullable=True)
    memory_usage = Column(JSON, nullable=True)  # Memory state changes
    
    # Timestamps
    created_at = Column(String, nullable=False)  # ISO format
    updated_at = Column(String, nullable=False)  # ISO format
    completed_at = Column(String, nullable=True)  # ISO format
    
    # Relationships
    agent = relationship("Agent", back_populates="tasks")

    def __repr__(self):
        return f"<TaskHistory {self.id} - {self.status}>" 