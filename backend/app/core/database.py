"""Database configuration module."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import os
from sqlalchemy.engine import URL

# Create SQLite database URL
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dev.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# Create SQLAlchemy engine with SQLite dialect
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

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