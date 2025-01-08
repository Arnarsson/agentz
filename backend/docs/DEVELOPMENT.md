# AGENTZ Development Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Development Setup](#development-setup)
3. [Architecture](#architecture)
4. [Development Workflow](#development-workflow)
5. [Testing Strategy](#testing-strategy)
6. [Documentation](#documentation)
7. [Deployment](#deployment)
8. [Progress & Roadmap](#progress--roadmap)

## Project Overview

AGENTZ is a web-based platform for the CrewAI framework, enabling users to create, manage, and monitor AI agents and workflows.

### High-Level Objectives
- **Agent Management**: Create and configure AI agents through an intuitive interface
- **Task Orchestration**: Define and execute tasks using CrewAI's capabilities
- **Workflow Building**: Chain multiple agents and tasks for complex operations
- **Real-time Monitoring**: Track agent activities and task progress
- **Secure Authentication**: Protect user data and agent configurations

## Development Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL
- Redis (optional)
- Supabase account
- OpenAI API key

### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Unix/macOS
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .

# Create .env file
cp .env.example .env
# Edit .env with your configuration
```

### Environment Configuration
```env
# Application
APP_NAME=AgentZ
DEBUG=True
API_V1_STR=/api/v1

# Authentication
CLERK_SECRET_KEY=your-clerk-secret
CLERK_JWT_VERIFICATION_KEY=your-jwt-key

# Database
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# AI/ML
OPENAI_API_KEY=your-openai-key

# Task Queue
REDIS_URL=redis://localhost:6379/0
```

## Architecture

### Project Structure
```
backend/
├── app/
│   ├── api/          # API routes
│   │   ├── agents.py
│   │   ├── tasks.py
│   │   └── workflows.py
│   ├── core/         # Core functionality
│   │   ├── config.py
│   │   └── database.py
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic models
│   └── services/     # Business logic
├── tests/
│   ├── test_api/
│   └── test_services/
├── scripts/          # Utility scripts
└── docs/            # Documentation
```

### Tech Stack
- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM
- **CrewAI**: Agent framework
- **Supabase**: Database and authentication
- **Redis**: Caching and task queue
- **Pytest**: Testing framework

## Development Workflow

### Code Style
```python
# Standard library imports
from typing import List, Optional

# Third-party imports
from fastapi import FastAPI, Depends
from crewai import Task

# Local imports
from app.core.config import settings
from app.models.agent import Agent
```

### Git Workflow
- **Main Branch**: Production-ready code
- **Develop**: Integration branch
- **Feature Branches**: `feature/<name>`
- **Bugfix Branches**: `bugfix/<name>`

### Pull Request Process
1. Create feature branch
2. Write tests
3. Implement changes
4. Run test suite
5. Submit PR with description

## Testing Strategy

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app

# Run specific test file
pytest tests/test_api/test_agents.py
```

### Test Organization
```python
# tests/test_api/test_agents.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient):
    """Test agent creation endpoint."""
    response = await client.post("/api/v1/agents/", json={
        "name": "Test Agent",
        "description": "Test description"
    })
    assert response.status_code == 200
```

## Documentation

### API Documentation
- OpenAPI/Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### Code Documentation
```python
def create_agent(agent_data: AgentCreate) -> Agent:
    """
    Create a new agent in the system.

    Args:
        agent_data (AgentCreate): The agent configuration data.

    Returns:
        Agent: The created agent instance.

    Raises:
        AgentError: If agent creation fails.
    """
```

## Deployment

### Production Setup
1. Configure production environment
2. Set up monitoring
3. Configure logging
4. Set up backup system

### Docker Configuration
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install -e .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

## Progress & Roadmap

### Completed Features
- [x] FastAPI project structure
- [x] Core settings with Pydantic
- [x] Logging with Loguru
- [x] CORS middleware
- [x] Health check endpoint
- [x] Clerk authentication

### In Progress
- [ ] Agent system implementation
- [ ] Database integration
- [ ] Task management
- [ ] WebSocket support

### Next Steps
1. Implement API authentication
2. Set up rate limiting
3. Configure security headers
4. Add health check endpoints
5. Set up frontend testing

### Known Issues
1. CrewAI V1/V2 model mixing warning (non-critical)
2. Missing rate limiting
3. Incomplete test coverage

## Best Practices

### Security
- Use environment variables for secrets
- Implement rate limiting
- Add security headers
- Validate input data

### Performance
- Use async operations
- Implement caching
- Optimize database queries
- Monitor response times

### Error Handling
```python
from app.core.errors import AgentError
from fastapi import HTTPException

try:
    result = await agent.execute_task(task)
except AgentError as e:
    logger.error(f"Agent execution failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Logging
```python
from loguru import logger

logger.add(
    "logs/agentz.log",
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL
)
```

## Contributing

### Getting Started
1. Fork the repository
2. Create a feature branch
3. Set up development environment
4. Run tests
5. Submit pull request

### Code Review Process
1. Automated tests must pass
2. Code review required
3. Documentation updated
4. No merge conflicts

### Release Process
1. Update version number
2. Update changelog
3. Create release branch
4. Deploy to staging
5. Deploy to production 