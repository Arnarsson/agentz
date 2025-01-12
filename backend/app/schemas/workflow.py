"""Workflow schemas."""
from typing import Optional
from pydantic import BaseModel

class WorkflowBase(BaseModel):
    """Base workflow schema."""
    title: str
    description: Optional[str] = None

class WorkflowCreate(WorkflowBase):
    """Workflow creation schema."""
    pass

class WorkflowUpdate(BaseModel):
    """Workflow update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    memory: Optional[str] = None
    tools: Optional[str] = None
    llm_config: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    execution_time: Optional[str] = None
    execution_status: Optional[str] = None

class WorkflowInDB(WorkflowBase):
    """Workflow database schema."""
    id: str
    type: str
    status: Optional[str] = None
    error: Optional[str] = None
    memory: Optional[str] = None
    tools: Optional[str] = None
    llm_config: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    execution_time: Optional[str] = None
    execution_status: Optional[str] = None

    class Config:
        """Pydantic config."""
        orm_mode = True 