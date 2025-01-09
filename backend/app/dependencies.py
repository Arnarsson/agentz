from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with async_session_factory() as session:
        yield session 