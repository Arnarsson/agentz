# AGENTZ API Documentation

## Authentication

All API endpoints require authentication using Clerk. Include the JWT token in the Authorization header:
```http
Authorization: Bearer <your-jwt-token>
```

## Base URL
All endpoints are prefixed with `/api/v1`

## Endpoints

### Health Check

#### GET /health
Check if the API is running.

**Response**
```json
{
    "status": "healthy"
}
```

### Agents

#### GET /agents
List all agents for the current user.

**Response**
```json
{
    "agents": [
        {
            "id": "uuid",
            "name": "Research Agent",
            "description": "Performs research tasks",
            "capabilities": ["web_search", "summarization"],
            "created_at": "2024-01-08T16:53:28.164Z",
            "updated_at": "2024-01-08T16:53:28.164Z"
        }
    ]
}
```

#### POST /agents
Create a new agent.

**Request Body**
```json
{
    "name": "Research Agent",
    "description": "Performs research tasks",
    "capabilities": ["web_search", "summarization"],
    "llm_config": {
        "model": "gpt-4",
        "temperature": 0.7
    }
}
```

**Response**
```json
{
    "id": "uuid",
    "name": "Research Agent",
    "description": "Performs research tasks",
    "capabilities": ["web_search", "summarization"],
    "created_at": "2024-01-08T16:53:28.164Z",
    "updated_at": "2024-01-08T16:53:28.164Z"
}
```

### Tasks

#### GET /tasks
List all tasks.

**Query Parameters**
- `status` (optional): Filter by task status (pending, running, completed, failed)
- `agent_id` (optional): Filter by agent ID
- `limit` (optional): Number of tasks to return (default: 10)
- `offset` (optional): Offset for pagination (default: 0)

**Response**
```json
{
    "tasks": [
        {
            "id": "uuid",
            "description": "Research quantum computing",
            "agent_id": "agent-uuid",
            "status": "completed",
            "result": "Quantum computing research summary...",
            "created_at": "2024-01-08T16:53:28.164Z",
            "completed_at": "2024-01-08T16:54:28.164Z"
        }
    ],
    "total": 100,
    "limit": 10,
    "offset": 0
}
```

#### POST /tasks
Create a new task.

**Request Body**
```json
{
    "description": "Research quantum computing",
    "agent_id": "agent-uuid",
    "priority": "high",
    "deadline": "2024-01-09T16:53:28.164Z"
}
```

**Response**
```json
{
    "id": "uuid",
    "description": "Research quantum computing",
    "agent_id": "agent-uuid",
    "status": "pending",
    "created_at": "2024-01-08T16:53:28.164Z"
}
```

### Workflows

#### GET /workflows
List all workflows.

**Response**
```json
{
    "workflows": [
        {
            "id": "uuid",
            "name": "Research Pipeline",
            "description": "Complete research pipeline",
            "agents": ["agent-uuid-1", "agent-uuid-2"],
            "status": "active",
            "created_at": "2024-01-08T16:53:28.164Z"
        }
    ]
}
```

#### POST /workflows
Create a new workflow.

**Request Body**
```json
{
    "name": "Research Pipeline",
    "description": "Complete research pipeline",
    "agents": ["agent-uuid-1", "agent-uuid-2"],
    "tasks": [
        {
            "description": "Initial research",
            "agent_id": "agent-uuid-1"
        },
        {
            "description": "Summarize findings",
            "agent_id": "agent-uuid-2"
        }
    ],
    "process": "sequential"
}
```

**Response**
```json
{
    "id": "uuid",
    "name": "Research Pipeline",
    "description": "Complete research pipeline",
    "agents": ["agent-uuid-1", "agent-uuid-2"],
    "status": "created",
    "created_at": "2024-01-08T16:53:28.164Z"
}
```

## WebSocket Endpoints

### /ws/tasks/{task_id}
Connect to receive real-time updates about a specific task.

**Messages**
```json
{
    "type": "status_update",
    "data": {
        "status": "running",
        "progress": 0.5,
        "message": "Processing data..."
    }
}
```

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
    "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden
```json
{
    "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
    "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
    "detail": "Internal server error"
}
```

## Rate Limiting

The API implements rate limiting based on the following rules:
- 100 requests per minute per IP address
- 1000 requests per hour per authenticated user

When rate limit is exceeded:
```json
{
    "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

## Pagination

All list endpoints support pagination using `limit` and `offset` parameters:
```http
GET /api/v1/tasks?limit=10&offset=20
```

Response includes pagination metadata:
```json
{
    "items": [...],
    "total": 100,
    "limit": 10,
    "offset": 20
}
```

## Filtering and Sorting

Most list endpoints support filtering and sorting:
```http
GET /api/v1/tasks?status=completed&sort=-created_at
```

- Use query parameters for filtering
- Use `sort` parameter with `-` prefix for descending order

## Versioning

The API uses URL versioning (currently v1). Future versions will be introduced as needed:
- `/api/v1/...` - Current version
- `/api/v2/...` - Future version (when available)

## Best Practices

1. Always include proper authentication headers
2. Use pagination for large result sets
3. Implement proper error handling
4. Monitor rate limits
5. Use WebSocket connections for real-time updates
6. Cache responses when appropriate 