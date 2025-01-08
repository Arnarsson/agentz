# Development Guide

## Development Environment Setup

### Backend Setup

1. Install Python 3.12+:
```bash
# On macOS with Homebrew
brew install python@3.12

# On Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv
```

2. Set up the development environment:
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

3. Install pre-commit hooks:
```bash
pre-commit install
```

### Database Setup

1. Install PostgreSQL:
```bash
# On macOS with Homebrew
brew install postgresql@14
brew services start postgresql@14

# On Ubuntu/Debian
sudo apt install postgresql-14
```

2. Create database and user:
```sql
CREATE DATABASE agentz;
CREATE USER agentz WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE agentz TO agentz;
```

3. Run migrations:
```bash
alembic upgrade head
```

## Development Workflow

### Code Style

We follow these style guides:
- [PEP 8](https://www.python.org/dev/peps/pep-0008/) - Python code style
- [Black](https://black.readthedocs.io/) - Code formatting
- [isort](https://pycqa.github.io/isort/) - Import sorting
- [Flake8](https://flake8.pycqa.org/) - Linting

Format code before committing:
```bash
# Format code
black .

# Sort imports
isort .

# Check style
flake8
```

### Testing

1. Run the test suite:
```bash
# Run all tests
pytest

# Run specific test file
pytest app/tests/test_api/test_websocket.py

# Run with coverage
pytest --cov=app
```

2. Test WebSocket endpoints:
```bash
# Using wscat
wscat -c ws://localhost:8000/agents/test-agent/ws
```

### Database Migrations

1. Create a new migration:
```bash
# After modifying models
alembic revision --autogenerate -m "description of changes"
```

2. Apply migrations:
```bash
# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### API Documentation

1. Generate OpenAPI schema:
```bash
python scripts/generate_openapi.py
```

2. View API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

### Backend Structure
```
backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration scripts
│   └── env.py           # Migration environment
├── app/
│   ├── api/             # API endpoints
│   │   ├── agents.py    # Agent endpoints
│   │   └── tasks.py     # Task endpoints
│   ├── core/            # Core functionality
│   │   ├── config.py    # Configuration
│   │   ├── database.py  # Database setup
│   │   ├── errors.py    # Error handling
│   │   ├── logging.py   # Logging setup
│   │   └── websocket.py # WebSocket manager
│   ├── models/          # Database models
│   │   ├── agent.py     # Agent model
│   │   └── task.py      # Task model
│   ├── schemas/         # Pydantic schemas
│   │   ├── agent.py     # Agent schemas
│   │   └── task.py      # Task schemas
│   ├── services/        # Business logic
│   │   ├── agent.py     # Agent service
│   │   └── task.py      # Task service
│   └── tests/           # Test suite
│       ├── api/         # API tests
│       └── services/    # Service tests
├── scripts/             # Utility scripts
└── requirements.txt     # Dependencies
```

### Code Organization

1. **API Layer** (`app/api/`)
   - FastAPI route definitions
   - Request/response handling
   - Input validation
   - Error handling

2. **Service Layer** (`app/services/`)
   - Business logic
   - Database operations
   - External service integration
   - Error handling

3. **Model Layer** (`app/models/`)
   - SQLAlchemy models
   - Database relationships
   - Model methods

4. **Schema Layer** (`app/schemas/`)
   - Pydantic models
   - Request/response schemas
   - Validation rules

5. **Core Layer** (`app/core/`)
   - Application configuration
   - Database setup
   - Logging configuration
   - WebSocket management
   - Error definitions

## Best Practices

### General
1. Follow the Single Responsibility Principle
2. Write descriptive commit messages
3. Keep functions and methods focused
4. Document complex logic
5. Handle errors gracefully

### API Development
1. Use appropriate HTTP methods
2. Validate all inputs
3. Return consistent error responses
4. Include proper status codes
5. Document all endpoints

### Database
1. Use migrations for schema changes
2. Include appropriate indexes
3. Use relationships appropriately
4. Handle transactions properly
5. Write efficient queries

### Testing
1. Write unit tests for all features
2. Include integration tests
3. Test error conditions
4. Use fixtures appropriately
5. Maintain test coverage

### Security
1. Validate all inputs
2. Sanitize all outputs
3. Use proper authentication
4. Implement rate limiting
5. Follow security best practices

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```
   sqlalchemy.exc.OperationalError: could not connect to server
   ```
   - Check PostgreSQL service is running
   - Verify database credentials
   - Check network connectivity

2. **Migration Issues**
   ```
   alembic.util.CommandError: Target database is not up to date
   ```
   - Run `alembic upgrade head`
   - Check migration history
   - Resolve conflicts manually if needed

3. **WebSocket Connection Issues**
   ```
   WebSocket connection failed
   ```
   - Check WebSocket URL
   - Verify agent exists
   - Check client implementation

### Debugging

1. Enable debug logging:
```python
# In .env
LOG_LEVEL=DEBUG
```

2. Use FastAPI debug mode:
```bash
uvicorn app.main:app --reload --log-level debug
```

3. Debug database queries:
```python
# In code
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Deployment

See [Deployment Guide](deployment.md) for detailed deployment instructions. 