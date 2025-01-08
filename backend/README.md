# AGENTZ Backend

## Overview
AGENTZ is a powerful agent-based automation platform built with FastAPI, CrewAI, and Supabase.

## Prerequisites
- Python 3.12+
- Virtual environment management
- Supabase account
- OpenAI API key

## Quick Start

### 1. Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Unix/macOS
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .
```

### 2. Configuration
Create a `.env` file in the `backend` directory:
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

### 3. Run the Application
```bash
uvicorn app.main:app --reload
```

Access the API documentation at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Project Structure
```
backend/
├── app/
│   ├── api/          # API routes
│   ├── core/         # Core functionality
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic models
│   └── services/     # Business logic
├── tests/
│   ├── test_api/
│   └── test_services/
├── scripts/          # Utility scripts
├── pyproject.toml
└── .env
```

## Development Guidelines

### Import Structure
Follow this import organization pattern:
```python
# Standard library
import sys
from typing import List, Optional

# Third-party packages
from fastapi import FastAPI
from crewai import Task
import boto3

# Local imports
from app.core.config import settings
from app.models.agent import Agent
```

### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app

# Run specific test file
pytest tests/test_api/test_agents.py
```

### Code Quality
- Use absolute imports
- Follow PEP 8 style guide
- Add type hints
- Document functions and classes

## API Documentation

### Authentication
All endpoints require authentication using Clerk:
```python
@router.get("/")
async def list_agents(token: TokenPayload = Depends(clerk_auth)):
    """List all agents for the current user."""
    return {"agents": []}
```

### Available Endpoints
- `GET /api/v1/health` - Health check
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks` - Create task

## Troubleshooting

### Import Issues
If you encounter import problems:
1. Verify virtual environment activation
2. Check Python path:
```python
import sys
print(sys.path)
```
3. Reinstall dependencies:
```bash
pip install -e .
```
4. Run the test script:
```bash
python test_imports.py
```

### Common Issues
1. CrewAI V1/V2 Model Mixing Warning
   - This is expected and non-critical
   - Will be resolved in future CrewAI updates

2. Package Conflicts
   ```bash
   # Clear and reinstall dependencies
   pip uninstall -y -r <(pip freeze)
   pip install -e .
   ```

3. Database Connection Issues
   - Verify Supabase credentials
   - Check network connectivity
   - Ensure proper environment variables

## IDE Setup

### VS Code
Create `.vscode/settings.json`:
```json
{
  "python.analysis.extraPaths": ["./"],
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic",
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

### PyCharm
1. Set project interpreter to virtual environment
2. Enable "Add source roots to PYTHONPATH"
3. Configure test runner for pytest

## Contributing
1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## License
[Your License] 