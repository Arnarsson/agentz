from sqlalchemy import Column, String, Boolean, JSON
from .base import BaseModel

class Agent(BaseModel):
    """SQLAlchemy model for agents."""
    __tablename__ = "agents"

    role = Column(String, nullable=False, unique=True, index=True)
    goal = Column(String, nullable=False)
    backstory = Column(String, nullable=True)
    allow_delegation = Column(Boolean, default=True)
    verbose = Column(Boolean, default=False)
    memory = Column(JSON, nullable=True)
    status = Column(String, default="active")

    def __repr__(self):
        return f"<Agent {self.role}>" 