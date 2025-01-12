"""Database initialization script."""
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import init_db, engine
from app.models.base import Base
from app.models.agent import Agent
from app.models.task import Task

def main():
    """Initialize the database."""
    print("Creating database tables...")
    
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    main() 