"""Database configuration module."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings
from app.core.base import Base
import os

# Import all models to ensure they are registered with the Base class
from app.models.workflow import Workflow
from app.models.agent import Agent
from app.models.task import Task

# Ensure data directory exists
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
os.makedirs(data_dir, exist_ok=True)

# Use the database URL from settings, ensuring proper path handling
db_path = os.path.join(data_dir, 'dev.db')
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
SYNC_SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# Create sync SQLAlchemy engine for initialization and sync operations
engine = create_engine(
    SYNC_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create async engine for async operations
async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine)

def init_db():
    """Initialize database."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 