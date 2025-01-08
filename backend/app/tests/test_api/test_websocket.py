import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from ...core.websocket import WebSocketManager, ws_manager
from datetime import datetime, UTC
import json
import asyncio
from unittest.mock import AsyncMock, patch

@pytest.fixture
def ws_manager_test():
    return WebSocketManager(
        heartbeat_interval=1,
        max_queue_size=5,
        batch_interval=0.1
    )

@pytest.mark.asyncio
async def test_websocket_connection(ws_manager_test):
    """Test WebSocket connection and initial message."""
    mock_ws = AsyncMock(spec=WebSocket)
    agent_id = "test-agent"
    
    await ws_manager_test.connect(mock_ws, agent_id)
    
    # Verify connection accepted
    mock_ws.accept.assert_called_once()
    
    # Verify initial message sent
    mock_ws.send_json.assert_called_once()
    message = mock_ws.send_json.call_args[0][0]
    assert message["type"] == "connection_established"
    assert message["agent_id"] == agent_id
    
    # Verify stats updated
    stats = ws_manager_test.get_stats()
    assert stats["total_connections"] == 1
    assert stats["active_connections"] == 1

@pytest.mark.asyncio
async def test_websocket_heartbeat(ws_manager_test):
    """Test WebSocket heartbeat mechanism."""
    mock_ws = AsyncMock(spec=WebSocket)
    agent_id = "test-agent"
    
    await ws_manager_test.connect(mock_ws, agent_id)
    
    # Wait for heartbeat
    await asyncio.sleep(1.1)
    
    # Verify heartbeat sent
    calls = mock_ws.send_json.call_args_list
    assert len(calls) >= 2  # Initial message + at least one heartbeat
    heartbeat = calls[-1][0][0]
    assert heartbeat["type"] == "ping"

@pytest.mark.asyncio
async def test_message_queuing(ws_manager_test):
    """Test message queuing for offline clients."""
    agent_id = "test-agent"
    test_message = {
        "type": "test",
        "content": "test message"
    }
    
    # Queue message for offline client
    await ws_manager_test.broadcast_to_agent(agent_id, test_message)
    
    # Verify message is queued
    assert agent_id in ws_manager_test.message_queues
    assert len(ws_manager_test.message_queues[agent_id]) == 1
    queued_message = ws_manager_test.message_queues[agent_id][0]
    assert queued_message["content"] == test_message["content"]
    
    # Connect client
    mock_ws = AsyncMock(spec=WebSocket)
    await ws_manager_test.connect(mock_ws, agent_id)
    
    # Wait for any async operations
    await asyncio.sleep(0.1)
    
    # Get all messages sent to the client
    calls = mock_ws.send_json.call_args_list
    messages = [call[0][0] for call in calls]
    
    # Verify we got both the connection message and the queued message
    assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}: {messages}"
    
    # Verify the connection message
    assert messages[0]["type"] == "connection_established"
    assert messages[0]["agent_id"] == agent_id
    
    # Verify the batch update message
    assert messages[1]["type"] == "batch_update"
    assert len(messages[1]["updates"]) == 1
    assert messages[1]["updates"][0]["content"] == test_message["content"]
    
    # Verify queue is cleared after sending
    assert len(ws_manager_test.message_queues[agent_id]) == 0

@pytest.mark.asyncio
async def test_batch_updates(ws_manager_test):
    """Test batch update mechanism."""
    mock_ws = AsyncMock(spec=WebSocket)
    agent_id = "test-agent"
    
    await ws_manager_test.connect(mock_ws, agent_id)
    
    # Send multiple updates
    updates = [
        {"type": "test", "id": i} for i in range(3)
    ]
    for update in updates:
        await ws_manager_test.broadcast_to_agent(agent_id, update)
    
    # Wait for batch processing
    await asyncio.sleep(0.2)
    
    # Verify batch update sent
    calls = mock_ws.send_json.call_args_list
    batch_updates = [
        call[0][0] for call in calls 
        if call[0][0].get("type") == "batch_update"
    ]
    assert len(batch_updates) > 0
    assert len(batch_updates[0]["updates"]) == 3

@pytest.mark.asyncio
async def test_connection_stats(ws_manager_test):
    """Test WebSocket connection statistics."""
    mock_ws1 = AsyncMock(spec=WebSocket)
    mock_ws2 = AsyncMock(spec=WebSocket)
    agent_id = "test-agent"
    
    # Connect two clients
    await ws_manager_test.connect(mock_ws1, agent_id)
    await ws_manager_test.connect(mock_ws2, agent_id)
    
    # Disconnect one client
    await ws_manager_test.disconnect(mock_ws1)
    
    # Verify stats
    stats = ws_manager_test.get_stats()
    assert stats["total_connections"] == 2
    assert stats["active_connections"] == 1

@pytest.mark.asyncio
async def test_error_handling(ws_manager_test):
    """Test error handling in WebSocket manager."""
    mock_ws = AsyncMock(spec=WebSocket)
    agent_id = "test-agent"
    
    # Simulate send error
    mock_ws.send_json.side_effect = Exception("Test error")
    
    # Verify error is handled
    with pytest.raises(Exception, match="Test error"):
        await ws_manager_test.connect(mock_ws, agent_id)
    
    # Verify error counted and connection cleaned up
    stats = ws_manager_test.get_stats()
    assert stats["errors"] > 0
    assert stats["active_connections"] == 0 