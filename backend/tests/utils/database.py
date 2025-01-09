from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    raise NotImplementedError("This is a placeholder that should be overridden in tests") 