from fastapi import WebSocketDisconnect
import pytest
import asyncio
from typing import List
from uuid import uuid4
from tests.models import TestAgent

@pytest.fixture
async def test_agents(db_session) -> List[TestAgent]:
    """Create multiple test agents for load testing."""
    agents = []
    for i in range(5):
        agent = TestAgent(
            id=uuid4(),
            role=f"load_test_agent_{i}",
            goal="Load testing WebSocket functionality",
            backstory="Created for load testing",
            allow_delegation=False,
            verbose=True,
            memory={},
            tools=[],
            llm_config=None,
            max_iterations=5,
            status="active",
            execution_status={}
        )
        db_session.add(agent)
        agents.append(agent)
    
    await db_session.commit()
    return agents

async def test_concurrent_connections(test_client, test_agents):
    """Test handling of multiple concurrent WebSocket connections."""
    from app.core.websocket import ws_manager

    # Create multiple WebSocket connections
    with test_client.websocket_connect(f"/api/v1/agents/{test_agents[0].id}/ws") as ws1:
        with test_client.websocket_connect(f"/api/v1/agents/{test_agents[1].id}/ws") as ws2:
            # Send test messages
            ws1.send_text("Hello from client 1")
            ws2.send_text("Hello from client 2")

            # Verify responses
            response1 = ws1.receive_text()
            response2 = ws2.receive_text()

            assert response1 == "Hello from client 1"
            assert response2 == "Hello from client 2"

async def test_message_broadcast_load(test_client, test_agents):
    """Test broadcasting messages to multiple clients."""
    from app.core.websocket import ws_manager

    # Create WebSocket connections for all agents
    with test_client.websocket_connect(f"/api/v1/agents/{test_agents[0].id}/ws") as ws1:
        with test_client.websocket_connect(f"/api/v1/agents/{test_agents[1].id}/ws") as ws2:
            # Broadcast a message
            message = {"type": "status_update", "data": {"status": "running"}}
            await ws_manager.broadcast_to_agent(str(test_agents[0].id), message)

            # Verify that only the correct client receives the message
            response1 = ws1.receive_json()
            assert response1 == message

            # Verify that other client doesn't receive the message
            with pytest.raises(WebSocketDisconnect):
                ws2.receive_json()

async def test_connection_recovery(test_client, test_agents):
    """Test connection recovery and message queue handling."""
    from app.core.websocket import ws_manager

    # Connect, disconnect, and reconnect
    for _ in range(3):
        with test_client.websocket_connect(f"/api/v1/agents/{test_agents[0].id}/ws") as ws:
            # Send a test message
            ws.send_text("Test message")
            response = ws.receive_text()
            assert response == "Test message"

            # Queue a message while connected
            await ws_manager.broadcast_to_agent(str(test_agents[0].id), {"type": "test", "data": "queued"})
            response = ws.receive_json()
            assert response == {"type": "test", "data": "queued"} 