# CrewAI Web Backend

This is the backend service for CrewAI Web, providing a REST API for managing AI agents and workflows using the CrewAI framework.

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
- Copy `.env.example` to `.env`
- Update the values in `.env` with your configuration

4. Run the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API documentation: `http://localhost:8000/docs`
- OpenAPI specification: `http://localhost:8000/api/v1/openapi.json`

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── agents.py      # Agent management endpoints
│   │   ├── tasks.py       # Task management endpoints
│   │   └── workflows.py   # Workflow management endpoints
│   ├── core/
│   │   └── config.py      # Application configuration
│   └── main.py           # FastAPI application
├── tests/                # Test files
├── .env                 # Environment variables
└── requirements.txt     # Python dependencies
```

## Development

### Running Tests
```bash
pytest
```

### Code Style
The project follows PEP 8 guidelines. Before committing, ensure your code is properly formatted.

## Features

- Agent Management
  - Create and configure AI agents
  - List available agents
  - Get agent details

- Task Management
  - Create tasks for agents
  - Execute tasks
  - Monitor task status

- Workflow Management
  - Create agent workflows
  - Execute workflows
  - Monitor workflow status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 