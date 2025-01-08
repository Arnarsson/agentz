# API Documentation

## Base URL
```
http://your-server/agents
```

## Authentication
All endpoints require authentication (to be implemented).

## Endpoints

### Agents

#### Create Agent
```http
POST /agents
```

Request Body:
```json
{
    "role": "string",
    "name": "string",
    "description": "string",
    "tools": [
        {
            "name": "string",
            "description": "string",
            "parameters": {}
        }
    ],
    "llm_config": {
        "model": "string",
        "temperature": 0.7,
        "max_tokens": 1000
    }
}
```

Response:
```json
{
    "id": "string",
    "role": "string",
    "name": "string",
    "description": "string",
    "status": "string",
    "tools": [],
    "llm_config": {},
    "created_at": "ISO-8601 timestamp",
    "updated_at": "ISO-8601 timestamp"
}
```

#### List Agents
```http
GET /agents?skip=0&limit=100
```

Response:
```json
[
    {
        "id": "string",
        "role": "string",
        "name": "string",
        "description": "string",
        "status": "string",
        "tools": [],
        "llm_config": {},
        "created_at": "ISO-8601 timestamp",
        "updated_at": "ISO-8601 timestamp"
    }
]
```

#### Get Agent
```http
GET /agents/{agent_id}
```

Response:
```json
{
    "id": "string",
    "role": "string",
    "name": "string",
    "description": "string",
    "status": "string",
    "tools": [],
    "llm_config": {},
    "created_at": "ISO-8601 timestamp",
    "updated_at": "ISO-8601 timestamp"
}
```

#### Update Agent
```http
PUT /agents/{agent_id}
```

Request Body:
```json
{
    "name": "string",
    "description": "string",
    "tools": [],
    "llm_config": {}
}
```

Response:
```json
{
    "id": "string",
    "role": "string",
    "name": "string",
    "description": "string",
    "status": "string",
    "tools": [],
    "llm_config": {},
    "created_at": "ISO-8601 timestamp",
    "updated_at": "ISO-8601 timestamp"
}
```

#### Delete Agent
```http
DELETE /agents/{agent_id}
```

Response:
```json
{
    "message": "Agent deleted successfully"
}
```

### Task Execution

#### Execute Task
```http
POST /agents/{agent_id}/execute
```

Request Body:
```json
{
    "task": "string",
    "tools": [
        {
            "name": "string",
            "parameters": {}
        }
    ],
    "context": {}
}
```

Response:
```json
{
    "task_id": "string",
    "agent_id": "string",
    "status": "string",
    "message": "string"
}
```

### WebSocket Connection

#### Connect to Agent Updates
```
WebSocket: ws://your-server/agents/{agent_id}/ws
```

See [WebSocket Documentation](websocket.md) for detailed protocol information.

#### Get WebSocket Statistics
```http
GET /agents/ws/stats
```

Response:
```json
{
    "total_connections": 0,
    "active_connections": 0,
    "messages_sent": 0,
    "errors": 0
}
```

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Error message explaining the issue"
}
```

### 404 Not Found
```json
{
    "detail": "Agent not found"
}
```

### 409 Conflict
```json
{
    "detail": "Agent with role 'role_name' already exists"
}
```

### 500 Internal Server Error
```json
{
    "detail": "Internal server error message"
}
```

## Rate Limiting
Rate limiting to be implemented.

## Pagination
List endpoints support pagination with `skip` and `limit` parameters:
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum number of items to return (default: 100, max: 1000)

## Best Practices
1. Always include error handling in your client implementation
2. Use WebSocket connection for real-time updates
3. Implement proper retry logic for failed requests
4. Monitor rate limits and implement backoff strategies
5. Keep WebSocket connections alive by responding to heartbeat messages 