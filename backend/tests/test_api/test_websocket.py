import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.websocket import ws_manager
from app.services.agent import AgentService
from app.schemas.agent import AgentCreate
import json

@pytest.fixture
def test_agent(db_session):
    """Create a test agent."""
    agent_data = AgentCreate(
        role="test_agent",
        goal="Testing WebSocket functionality",
        backstory="A test agent for WebSocket communication"
    )
    return AgentService.create_agent(db_session, agent_data)

def test_websocket_connection(test_client: TestClient, test_agent):
    """Test WebSocket connection establishment."""
    with test_client.websocket_connect(f"/api/v1/agents/{test_agent.id}/ws") as websocket:
        # Verify connection message
        data = websocket.receive_json()
        assert data["type"] == "connection_established"
        assert data["agent_id"] == test_agent.id
        assert "timestamp" in data

def test_websocket_invalid_agent(test_client: TestClient):
    """Test WebSocket connection with invalid agent ID."""
    with pytest.raises(Exception) as exc_info:
        with test_client.websocket_connect("/api/v1/agents/invalid-id/ws"):
            pass
    assert "4004" in str(exc_info.value)  # WebSocket close code for agent not found

def test_websocket_task_updates(test_client: TestClient, test_agent, db_session):
    """Test receiving task updates via WebSocket."""
    with test_client.websocket_connect(f"/api/v1/agents/{test_agent.id}/ws") as websocket:
        # Skip connection message
        websocket.receive_json()
        
        # Simulate task execution
        task_data = {
            "task": "Test task",
            "tools": [],
            "context": {}
        }
        
        # Start task execution
        response = test_client.post(
            f"/api/v1/agents/{test_agent.id}/execute",
            json=task_data
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        
        # Verify task start update
        data = websocket.receive_json()
        assert data["type"] == "task_update"
        assert data["agent_id"] == test_agent.id
        assert data["task_id"] == task_id
        assert data["status"] == "executing"
        assert data["progress"] == 0
        
        # Verify task completion/error update
        data = websocket.receive_json()
        assert data["type"] == "task_update"
        assert data["agent_id"] == test_agent.id
        assert data["task_id"] == task_id
        assert data["status"] in ["completed", "error"]

def test_websocket_ping_pong(test_client: TestClient, test_agent):
    """Test WebSocket ping-pong functionality."""
    with test_client.websocket_connect(f"/api/v1/agents/{test_agent.id}/ws") as websocket:
        # Skip connection message
        websocket.receive_json()
        
        # Send ping
        websocket.send_json({"type": "ping"})
        
        # Verify pong response
        data = websocket.receive_json()
        assert data["type"] == "pong"

def test_websocket_multiple_clients(test_client: TestClient, test_agent, db_session):
    """Test multiple WebSocket clients receiving updates."""
    with test_client.websocket_connect(f"/api/v1/agents/{test_agent.id}/ws") as ws1, \
         test_client.websocket_connect(f"/api/v1/agents/{test_agent.id}/ws") as ws2:
        
        # Skip connection messages
        ws1.receive_json()
        ws2.receive_json()
        
        # Update agent status
        AgentService.update_agent_status(
            db_session,
            test_agent.id,
            "working",
            execution_status={"state": "test"}
        )
        
        # Verify both clients receive the update
        for ws in [ws1, ws2]:
            data = ws.receive_json()
            assert data["type"] == "status_update"
            assert data["agent_id"] == test_agent.id
            assert data["status"] == "working"
            assert data["execution_status"]["state"] == "test" 