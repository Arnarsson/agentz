from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    """Base schema with common fields."""
    id: Optional[str] = Field(None, description="Unique identifier")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True 