"""Workflow model module."""
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base import Base

class Workflow(Base):
    """Workflow model."""
    __tablename__ = "workflows"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False)
    status = Column(String, nullable=True)
    error = Column(String, nullable=True)
    memory = Column(Text, nullable=True)
    tools = Column(Text, nullable=True)
    llm_config = Column(Text, nullable=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    execution_time = Column(String, nullable=True)
    execution_status = Column(Text, nullable=True)

    agents = relationship("Agent", secondary="workflow_agent", back_populates="workflows")
    tasks = relationship("Task", back_populates="workflow")

    def __repr__(self):
        """String representation of the workflow."""
        return f"<Workflow {self.title}>" 