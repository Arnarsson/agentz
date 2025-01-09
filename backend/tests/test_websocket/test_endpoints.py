import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from unittest.mock import AsyncMock, patch
from app.main import app
from app.core.websocket import ws_manager
from app.services.agent import AgentService
from app.schemas.agent import AgentCreate
from datetime import datetime, UTC
import json

@pytest.fixture
def test_agent(db_session):
    """Create a test agent for WebSocket testing."""
    agent_data = AgentCreate(
        role="test_agent",
        goal="Testing WebSocket functionality",
        backstory="A test agent for WebSocket communication",
        allow_delegation=False,
        verbose=True,
        tools=[],
        llm_config=None,
        max_iterations=5
    )
    return AgentService.create_agent(db_session, agent_data)

@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer test-token"}

async def test_websocket_connection(test_client: TestClient, test_agent, auth_headers):
    """Test WebSocket connection establishment."""
    with test_client.websocket_connect(
        f"/api/v1/agents/{test_agent.id}/ws",
        headers=auth_headers
    ) as websocket:
        # Verify connection message
        data = websocket.receive_json()
        assert data["type"] == "connection_established"
        assert data["agent_id"] == test_agent.id
        assert "timestamp" in data

async def test_websocket_invalid_agent(test_client: TestClient, auth_headers):
    """Test WebSocket connection with invalid agent ID."""
    with pytest.raises(Exception) as exc_info:
        with test_client.websocket_connect(
            "/api/v1/agents/invalid-id/ws",
            headers=auth_headers
        ):
            pass
    assert "4004" in str(exc_info.value)  # WebSocket close code for agent not found

async def test_websocket_unauthorized(test_client: TestClient, test_agent):
    """Test WebSocket connection without authentication."""
    with pytest.raises(Exception) as exc_info:
        with test_client.websocket_connect(f"/api/v1/agents/{test_agent.id}/ws"):
            pass
    assert "4003" in str(exc_info.value)  # WebSocket close code for unauthorized

async def test_websocket_status_request(test_client: TestClient, test_agent, auth_headers):
    """Test requesting agent status via WebSocket."""
    with test_client.websocket_connect(
        f"/api/v1/agents/{test_agent.id}/ws",
        headers=auth_headers
    ) as websocket:
        # Skip connection message
        websocket.receive_json()
        
        # Send status request
        websocket.send_json({
            "type": "status_request",
            "agent_id": test_agent.id
        })
        
        # Verify status response
        data = websocket.receive_json()
        assert data["type"] == "status_update"
        assert data["agent_id"] == test_agent.id
        assert "status" in data
        assert "timestamp" in data

async def test_websocket_broadcast_endpoint(
    test_client: TestClient,
    test_agent,
    auth_headers,
    db_session
):
    """Test broadcasting messages via HTTP endpoint."""
    # Connect WebSocket client
    with test_client.websocket_connect(
        f"/api/v1/agents/{test_agent.id}/ws",
        headers=auth_headers
    ) as websocket:
        # Skip connection message
        websocket.receive_json()
        
        # Send broadcast message via HTTP
        message = {
            "type": "status_update",
            "agent_id": test_agent.id,
            "status": "working"
        }
        response = test_client.post(
            f"/api/v1/agents/{test_agent.id}/broadcast",
            json=message,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify WebSocket client receives the message
        data = websocket.receive_json()
        assert data["type"] == "status_update"
        assert data["status"] == "working"
        assert "timestamp" in data

async def test_websocket_multiple_clients(
    test_client: TestClient,
    test_agent,
    auth_headers
):
    """Test multiple WebSocket clients receiving updates."""
    with test_client.websocket_connect(
        f"/api/v1/agents/{test_agent.id}/ws",
        headers=auth_headers
    ) as ws1, test_client.websocket_connect(
        f"/api/v1/agents/{test_agent.id}/ws",
        headers=auth_headers
    ) as ws2:
        # Skip connection messages
        ws1.receive_json()
        ws2.receive_json()
        
        # Send broadcast message
        message = {
            "type": "status_update",
            "agent_id": test_agent.id,
            "status": "working"
        }
        response = test_client.post(
            f"/api/v1/agents/{test_agent.id}/broadcast",
            json=message,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify both clients receive the message
        for ws in [ws1, ws2]:
            data = ws.receive_json()
            assert data["type"] == "status_update"
            assert data["status"] == "working"

async def test_websocket_reconnection(
    test_client: TestClient,
    test_agent,
    auth_headers,
    db_session
):
    """Test WebSocket reconnection with message queuing."""
    # Send message while no clients are connected
    message = {
        "type": "status_update",
        "agent_id": test_agent.id,
        "status": "working"
    }
    response = test_client.post(
        f"/api/v1/agents/{test_agent.id}/broadcast",
        json=message,
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Connect client and verify queued message is received
    with test_client.websocket_connect(
        f"/api/v1/agents/{test_agent.id}/ws",
        headers=auth_headers
    ) as websocket:
        # Skip connection message
        websocket.receive_json()
        
        # Verify queued message
        data = websocket.receive_json()
        assert data["type"] == "batch_update"
        assert len(data["updates"]) == 1
        assert data["updates"][0]["status"] == "working" 