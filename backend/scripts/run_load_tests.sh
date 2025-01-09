#!/bin/bash
set -e

echo "Starting WebSocket Load Tests"
echo "=============================="

echo "Setting up test database..."
PGPASSWORD=root psql -h localhost -U root -d postgres -c "DROP DATABASE IF EXISTS agentz_test;"
PGPASSWORD=root psql -h localhost -U root -d postgres -c "CREATE DATABASE agentz_test;"

echo "Running test migrations..."
cd tests/migrations
alembic upgrade head
cd ../..

echo "Running load tests..."
PYTHONPATH=. pytest tests/test_websocket/test_load.py -v --asyncio-mode=auto

status=$?

echo "Cleaning up..."
PGPASSWORD=root psql -h localhost -U root -d postgres -c "DROP DATABASE IF EXISTS agentz_test;"

if [ $status -ne 0 ]; then
    echo "Load tests failed"
    exit 1
fi

echo "Load tests completed successfully" 