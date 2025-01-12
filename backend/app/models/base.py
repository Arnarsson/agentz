"""Base model for SQLAlchemy models."""
from app.core.database import Base

# Re-export Base for models to use
__all__ = ['Base'] 