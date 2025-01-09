"""Test configuration."""
import os

# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"

# Set environment variables for testing
os.environ["APP_NAME"] = "AgentZ"
os.environ["DEBUG"] = "False"
os.environ["API_V1_STR"] = "/api/v1"

# Authentication
os.environ["CLERK_SECRET_KEY"] = "test_clerk_secret"
os.environ["CLERK_JWT_VERIFICATION_KEY"] = "test_clerk_jwt_key"

# Database
os.environ["SUPABASE_URL"] = "http://localhost:54321"
os.environ["SUPABASE_KEY"] = "test_key"
os.environ["SUPABASE_JWT_SECRET"] = "test_jwt_secret"
os.environ["SUPABASE_DB_PASSWORD"] = "test_password"

# AI/ML
os.environ["OPENAI_API_KEY"] = "test_openai_key"

# Task Queue
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

# Logging
os.environ["LOG_LEVEL"] = "INFO"

# Test mode
os.environ["IS_TEST"] = "true" 