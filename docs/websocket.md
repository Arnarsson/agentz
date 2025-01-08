# WebSocket Protocol Documentation

## Overview
The WebSocket implementation provides real-time communication between agents and clients, supporting features such as:
- Real-time status updates
- Task execution progress
- Message queuing for offline clients
- Batch updates for efficient communication
- Connection heartbeat mechanism
- Connection statistics

## Connection Endpoint
```
WebSocket URL: ws://your-server/agents/{agent_id}/ws
```

## Message Types

### 1. Connection Established
Sent immediately after a successful WebSocket connection.
```json
{
    "type": "connection_established",
    "agent_id": "string",
    "timestamp": "ISO-8601 timestamp"
}
```

### 2. Status Update
Indicates a change in agent status.
```json
{
    "type": "status_update",
    "agent_id": "string",
    "status": "string",
    "execution_status": {
        "state": "string",
        "task_id": "string",
        "progress": 0,
        "message": "string"
    },
    "timestamp": "ISO-8601 timestamp"
}
```

### 3. Task Update
Provides information about task execution progress.
```json
{
    "type": "task_update",
    "agent_id": "string",
    "task_id": "string",
    "status": "string",
    "progress": 0,
    "message": "string",
    "result": "optional result data",
    "error": "optional error message",
    "timestamp": "ISO-8601 timestamp"
}
```

### 4. Batch Update
Contains multiple updates in a single message for efficiency.
```json
{
    "type": "batch_update",
    "updates": [
        {
            "type": "string",
            "content": "any"
        }
    ],
    "timestamp": "ISO-8601 timestamp"
}
```

### 5. Heartbeat
Keeps the connection alive and verifies client connectivity.
```json
{
    "type": "ping",
    "timestamp": "ISO-8601 timestamp"
}
```

## Features

### Message Queuing
- Messages for offline clients are queued automatically
- Queue size limit: 100 messages per agent (configurable)
- Messages are delivered when the client reconnects
- Queued messages are sent as a batch update

### Batch Processing
- Multiple updates are batched together for efficiency
- Batch interval: 0.1 seconds (configurable)
- Reduces network traffic and message processing overhead
- Maintains message order within batches

### Connection Management
- Heartbeat interval: 30 seconds (configurable)
- Automatic disconnection of unresponsive clients
- Connection statistics tracking
- Multiple connections per agent supported

### Error Handling
- Automatic cleanup of failed connections
- Error tracking and statistics
- Structured error logging
- Graceful disconnection handling

## Statistics
Available via GET `/agents/ws/stats`:
```json
{
    "total_connections": "integer",
    "active_connections": "integer",
    "messages_sent": "integer",
    "errors": "integer"
}
```

## Example Usage

### JavaScript Client
```javascript
const ws = new WebSocket(`ws://your-server/agents/${agentId}/ws`);

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    switch (message.type) {
        case 'connection_established':
            console.log('Connected to agent:', message.agent_id);
            break;
        case 'status_update':
            console.log('Agent status:', message.status);
            break;
        case 'task_update':
            console.log('Task progress:', message.progress);
            break;
        case 'batch_update':
            message.updates.forEach(update => {
                console.log('Batch update:', update);
            });
            break;
        case 'ping':
            // Respond to keep connection alive
            ws.send(JSON.stringify({ type: 'pong' }));
            break;
    }
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('Connection closed');
};
```

## Configuration
The WebSocket manager can be configured with the following parameters:
```python
WebSocketManager(
    heartbeat_interval=30,  # seconds
    max_queue_size=100,    # messages
    batch_interval=0.1     # seconds
)
```

## Best Practices
1. Always handle connection errors and implement reconnection logic
2. Process batch updates efficiently to handle multiple messages
3. Respond to heartbeat messages to maintain connection
4. Monitor connection statistics for system health
5. Implement proper error handling on the client side 