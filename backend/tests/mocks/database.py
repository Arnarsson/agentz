"""Mock database module for testing."""
from app.core.database import create_engine, sessionmaker, Base
from app.core.config import settings

# Override database URL for testing
settings.DATABASE_URL = "sqlite:///./data/test.db"

# Create test engine using the same configuration as production
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
    pool_pre_ping=True,
    pool_recycle=300
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_test_db():
    """Initialize test database."""
    Base.metadata.create_all(bind=engine)

def get_test_db():
    """Get test database session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close() 