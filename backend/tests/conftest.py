"""Test configuration and fixtures."""
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator

# Set environment variables for testing
os.environ["APP_NAME"] = "AgentZ"
os.environ["DEBUG"] = "False"
os.environ["API_V1_STR"] = "/api/v1"
os.environ["PROJECT_NAME"] = "CrewAI API"

# Authentication
os.environ["CLERK_SECRET_KEY"] = "test_clerk_secret"
os.environ["CLERK_JWT_VERIFICATION_KEY"] = "test_clerk_jwt_key"

# Database
os.environ["SUPABASE_URL"] = "http://localhost:54321"
os.environ["SUPABASE_KEY"] = "test_key"
os.environ["SUPABASE_JWT_SECRET"] = "test_jwt_secret"
os.environ["SUPABASE_DB_PASSWORD"] = "test_password"
os.environ["DATABASE_URL"] = "sqlite:///./data/test.db"

# AI/ML
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["SERPER_API_KEY"] = "test_serper_key"

# Task Queue
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

# Testing
os.environ["FIXED_TIME"] = "2025-01-05T17:12:22+01:00"

# Logging
os.environ["LOG_LEVEL"] = "INFO"

# Test mode
os.environ["IS_TEST"] = "true"

import importlib
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock modules before importing app
sys.modules["supabase"] = importlib.import_module("tests.mocks.supabase")

from tests.mocks.database import test_db  # noqa

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 