from sqlalchemy import Column, String, JSON, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Agent(Base):
    """Agent model for testing."""
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    role = Column(String, unique=True, nullable=False)
    goal = Column(String, nullable=False)
    backstory = Column(String)
    allow_delegation = Column(Boolean, default=False)
    verbose = Column(Boolean, default=True)
    memory = Column(JSON, default=dict)
    tools = Column(JSON, default=list)
    llm_config = Column(JSON, default=dict)
    max_iterations = Column(Integer, default=5)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    status = Column(String, default="active")
    execution_status = Column(JSON, default=dict)

class Task(Base):
    """Task model for testing."""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"))
    priority = Column(Integer, default=1)
    requires_delegation = Column(Boolean, default=False)
    execution_params = Column(JSON, default=dict)
    status = Column(String, default="pending")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    agent = relationship("Agent", backref="tasks") 