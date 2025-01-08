import pytest
from fastapi import status

def test_create_agent(client, sample_agent_data):
    """Test creating an agent via API."""
    response = client.post("/api/v1/agents/", json=sample_agent_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["role"] == sample_agent_data["role"]
    assert data["goal"] == sample_agent_data["goal"]
    assert "id" in data

def test_create_duplicate_agent(client, sample_agent_data):
    """Test creating an agent with duplicate role."""
    # Create first agent
    client.post("/api/v1/agents/", json=sample_agent_data)
    
    # Try to create duplicate
    response = client.post("/api/v1/agents/", json=sample_agent_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]

def test_create_agent_invalid_data(client):
    """Test creating an agent with invalid data."""
    invalid_data = {
        "role": "",  # Empty role should fail validation
        "goal": "Test goal"
    }
    response = client.post("/api/v1/agents/", json=invalid_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_list_agents(client, sample_agent_data):
    """Test listing agents."""
    # Create some agents first
    client.post("/api/v1/agents/", json=sample_agent_data)
    client.post("/api/v1/agents/", json={**sample_agent_data, "role": "Test Agent 2"})
    
    response = client.get("/api/v1/agents/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert any(agent["role"] == "Test Agent" for agent in data)
    assert any(agent["role"] == "Test Agent 2" for agent in data)

def test_get_agent(client, sample_agent_data):
    """Test getting a specific agent."""
    # Create an agent first
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]
    
    # Get the agent
    response = client.get(f"/api/v1/agents/{agent_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == agent_id
    assert data["role"] == sample_agent_data["role"]

def test_get_nonexistent_agent(client):
    """Test getting a nonexistent agent."""
    response = client.get("/api/v1/agents/nonexistent-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_agent(client, sample_agent_data):
    """Test updating an agent."""
    # Create an agent first
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]
    
    # Update the agent
    update_data = {"goal": "Updated goal"}
    response = client.put(f"/api/v1/agents/{agent_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == agent_id
    assert data["goal"] == "Updated goal"
    assert data["role"] == sample_agent_data["role"]  # Unchanged field

def test_update_nonexistent_agent(client):
    """Test updating a nonexistent agent."""
    update_data = {"goal": "Updated goal"}
    response = client.put("/api/v1/agents/nonexistent-id", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_agent(client, sample_agent_data):
    """Test deleting an agent."""
    # Create an agent first
    create_response = client.post("/api/v1/agents/", json=sample_agent_data)
    agent_id = create_response.json()["id"]
    
    # Delete the agent
    response = client.delete(f"/api/v1/agents/{agent_id}")
    assert response.status_code == status.HTTP_200_OK
    
    # Verify agent is deleted
    get_response = client.get(f"/api/v1/agents/{agent_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_nonexistent_agent(client):
    """Test deleting a nonexistent agent."""
    response = client.delete("/api/v1/agents/nonexistent-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND 