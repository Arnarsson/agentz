"""Database utilities for testing."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal

async def get_test_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for testing."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 