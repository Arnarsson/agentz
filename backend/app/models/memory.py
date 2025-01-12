"""Memory model module."""
from sqlalchemy import Column, String, Float, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class Memory(Base):
    """Memory model for storing agent memories and knowledge base entries."""
    __tablename__ = "memories"

    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)  # Nullable for knowledge base entries
    content = Column(JSON, nullable=False)
    type = Column(String, nullable=False)  # conversation, task_result, observation, knowledge
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    importance = Column(Float, default=0.0)
    context = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)  # Store vector embeddings
    references = Column(JSON, nullable=True)  # Store related memory/knowledge references

    # Relationships
    agent = relationship("Agent", back_populates="memories")

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_memories_agent_type", "agent_id", "type"),
        Index("ix_memories_timestamp", "timestamp"),
        Index("ix_memories_importance", "importance"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Memory {self.id}: {self.type} ({self.agent_id})>" 