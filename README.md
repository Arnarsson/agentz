# AgentZ - AI Agent Management Platform

AgentZ is a powerful platform for managing and orchestrating AI agents built with CrewAI. It provides a robust backend API and real-time communication capabilities for managing agent tasks, monitoring execution progress, and handling agent-to-agent communication.

## Features

- **Agent Management**
  - Create, update, and delete agents
  - Configure agent roles and capabilities
  - Manage agent tools and LLM configurations
  - Monitor agent status and health

- **Task Execution**
  - Execute tasks with specific agents
  - Real-time progress monitoring
  - Task history and analytics
  - Automatic retry mechanism with exponential backoff

- **Real-time Communication**
  - WebSocket-based real-time updates
  - Message queuing for offline clients
  - Efficient batch updates
  - Connection heartbeat mechanism

- **Monitoring and Analytics**
  - Task execution metrics
  - Agent performance analytics
  - Connection statistics
  - Structured logging

## Technology Stack

- **Backend**
  - FastAPI (Python web framework)
  - SQLAlchemy (ORM)
  - CrewAI (Agent framework)
  - WebSockets (Real-time communication)
  - Pydantic (Data validation)

- **Frontend** (Coming soon)
  - Next.js
  - Tailwind CSS
  - TypeScript
  - React Query

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+ (for frontend)
- PostgreSQL

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/agentz.git
cd agentz
```

2. Create a virtual environment and install dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
alembic upgrade head
```

5. Start the backend server:
```bash
uvicorn app.main:app --reload
```

### Development

1. Run tests:
```bash
pytest
```

2. Check code style:
```bash
black .
flake8
```

3. Generate API documentation:
```bash
python scripts/generate_openapi.py
```

## Documentation

- [API Documentation](docs/api.md)
- [WebSocket Protocol](docs/websocket.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)

## Project Structure

```
agentz/
├── backend/
│   ├── alembic/          # Database migrations
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core functionality
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── tests/        # Test suite
│   ├── scripts/          # Utility scripts
│   └── requirements.txt  # Python dependencies
├── frontend/            # Next.js frontend (coming soon)
├── docs/               # Documentation
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [CrewAI](https://github.com/joaomdmoura/crewAI) - AI agent framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Next.js](https://nextjs.org/) - React framework 