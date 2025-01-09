#!/bin/bash

# Set environment variables for testing
export TESTING=1
export LOG_LEVEL=INFO
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/agentz_test"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Create test database if it doesn't exist
echo "Creating test database..."
PGPASSWORD=postgres psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS agentz_test;"
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE agentz_test;"

# Run migrations
echo "Running migrations..."
alembic upgrade head

# Run pytest with coverage
echo "Running tests..."
pytest \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    -v \
    tests/

# Check the exit status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi

# Clean up test database
echo "Cleaning up..."
PGPASSWORD=postgres psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS agentz_test;" 