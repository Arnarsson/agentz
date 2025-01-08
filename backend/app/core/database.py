"""
Database configuration and connection management.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from supabase import create_client, Client
from loguru import logger

from app.core.config import settings

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = f"{settings.SUPABASE_URL}/rest/v1"
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Supabase client
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session.
    
    Yields:
        AsyncSession: The database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            await session.close()

def get_supabase() -> Client:
    """
    Get the Supabase client.
    
    Returns:
        Client: The Supabase client
    """
    return supabase 