"""
Base model with common fields for all models.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from app.core.database import Base

class BaseModel(Base):
    """Base model with common fields."""
    
    __abstract__ = True

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    def __repr__(self) -> str:
        """String representation of the model."""
        attrs = []
        for col in self.__table__.columns:
            value = getattr(self, col.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            attrs.append(f"{col.name}={value}")
        return f"<{self.__class__.__name__} {' '.join(attrs)}>" 