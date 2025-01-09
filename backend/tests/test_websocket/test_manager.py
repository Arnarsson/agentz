import pytest
import asyncio
from datetime import datetime, UTC
from app.core.websocket import WebSocketManager
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def ws_manager():
    """Create a WebSocket manager instance for testing."""
    return WebSocketManager(
        heartbeat_interval=1,
        max_queue_size=10,
        batch_interval=0.1
    )

@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    websocket = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_json = AsyncMock()
    return websocket

async def test_connect_and_disconnect(ws_manager, mock_websocket):
    """Test WebSocket connection and disconnection."""
    agent_id = "test-agent"
    
    # Test connection
    await ws_manager.connect(mock_websocket, agent_id)
    assert agent_id in ws_manager.agent_connections
    assert mock_websocket in ws_manager.agent_connections[agent_id]
    assert ws_manager.connection_agents[mock_websocket] == agent_id
    assert ws_manager.stats["active_connections"] == 1
    
    # Verify connection message
    mock_websocket.send_json.assert_called_once()
    connection_msg = mock_websocket.send_json.call_args[0][0]
    assert connection_msg["type"] == "connection_established"
    assert connection_msg["agent_id"] == agent_id
    
    # Test disconnection
    await ws_manager.disconnect(mock_websocket)
    assert agent_id not in ws_manager.agent_connections
    assert mock_websocket not in ws_manager.connection_agents
    assert ws_manager.stats["active_connections"] == 0

async def test_message_queuing(ws_manager):
    """Test message queuing for offline agents."""
    agent_id = "test-agent"
    test_message = {
        "type": "status_update",
        "status": "working",
        "agent_id": agent_id
    }
    
    # Queue message for offline agent
    await ws_manager.broadcast_to_agent(agent_id, test_message)
    
    # Verify message is queued
    assert agent_id in ws_manager.message_queues
    assert len(ws_manager.message_queues[agent_id]) == 1
    queued_msg = ws_manager.message_queues[agent_id][0]
    assert queued_msg["type"] == "status_update"
    assert queued_msg["status"] == "working"

async def test_batch_updates(ws_manager, mock_websocket):
    """Test batch update processing."""
    agent_id = "test-agent"
    await ws_manager.connect(mock_websocket, agent_id)
    
    # Clear initial connection message
    mock_websocket.send_json.reset_mock()
    
    # Send multiple updates
    updates = [
        {"type": "status_update", "status": "working"},
        {"type": "task_update", "progress": 50}
    ]
    
    for update in updates:
        await ws_manager.broadcast_to_agent(agent_id, update)
    
    # Wait for batch processing
    await asyncio.sleep(0.2)
    
    # Verify batch message
    mock_websocket.send_json.assert_called_once()
    batch_msg = mock_websocket.send_json.call_args[0][0]
    assert batch_msg["type"] == "batch_update"
    assert len(batch_msg["updates"]) == 2

async def test_heartbeat(ws_manager, mock_websocket):
    """Test heartbeat mechanism."""
    agent_id = "test-agent"
    await ws_manager.connect(mock_websocket, agent_id)
    
    # Clear initial connection message
    mock_websocket.send_json.reset_mock()
    
    # Wait for heartbeat
    await asyncio.sleep(1.1)
    
    # Verify heartbeat message
    mock_websocket.send_json.assert_called_once()
    heartbeat_msg = mock_websocket.send_json.call_args[0][0]
    assert heartbeat_msg["type"] == "ping"

async def test_multiple_clients(ws_manager):
    """Test handling multiple clients for the same agent."""
    agent_id = "test-agent"
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    
    # Connect two clients
    await ws_manager.connect(ws1, agent_id)
    await ws_manager.connect(ws2, agent_id)
    
    # Clear connection messages
    ws1.send_json.reset_mock()
    ws2.send_json.reset_mock()
    
    # Broadcast message
    test_message = {"type": "status_update", "status": "working"}
    await ws_manager.broadcast_to_agent(agent_id, test_message)
    
    # Wait for batch processing
    await asyncio.sleep(0.2)
    
    # Verify both clients received the message
    assert ws1.send_json.called
    assert ws2.send_json.called

async def test_error_handling(ws_manager, mock_websocket):
    """Test error handling during message sending."""
    agent_id = "test-agent"
    await ws_manager.connect(mock_websocket, agent_id)
    
    # Simulate send error
    mock_websocket.send_json.side_effect = Exception("Send failed")
    
    # Attempt to send message
    test_message = {"type": "status_update", "status": "working"}
    await ws_manager.broadcast_to_agent(agent_id, test_message)
    
    # Wait for batch processing
    await asyncio.sleep(0.2)
    
    # Verify error is counted and client is disconnected
    assert ws_manager.stats["errors"] == 1
    assert agent_id not in ws_manager.agent_connections 