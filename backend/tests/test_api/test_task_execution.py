import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.agent import AgentService
from app.schemas.agent import AgentCreate
from app.schemas.task import TaskCreate
import asyncio
from typing import Dict, Any

@pytest.fixture
async def test_agent(db_session: Session) -> Dict[str, Any]:
    """Create a test agent for task execution."""
    agent_data = AgentCreate(
        role="test_executor",
        goal="Execute test tasks",
        backstory="A test agent for executing tasks",
        allow_delegation=False,
        verbose=True,
        tools=[],
        max_iterations=3
    )
    
    agent = await AgentService.create_agent(db_session, agent_data)
    return {
        "id": agent.id,
        "role": agent.role,
        "instance": agent
    }

async def test_task_lifecycle(
    test_client: TestClient,
    test_agent: Dict[str, Any],
    db_session: Session
):
    """Test complete task lifecycle: creation, execution, and status updates."""
    # 1. Create Task
    task_data = TaskCreate(
        description="Test task execution",
        agent_role=test_agent["role"],
        expected_output="Test output",
        context={"test": True},
        async_execution=True
    )
    
    response = await test_client.post(
        "/api/tasks/",
        json=task_data.dict()
    )
    assert response.status_code == 200
    task_id = response.json()["id"]
    
    # 2. Execute Task and Monitor Updates
    with test_client.websocket_connect(f"/ws/agent/{test_agent['id']}") as websocket:
        # Start execution
        response = await test_client.post(f"/api/tasks/{task_id}/execute")
        assert response.status_code == 200
        
        # Monitor status updates
        updates = []
        for _ in range(3):  # We expect at least: start, progress, completion
            data = websocket.receive_json()
            updates.append(data)
        
        # Verify update sequence
        statuses = [u["status"] for u in updates]
        assert "executing" in statuses
        assert "completed" in statuses
        
        # 3. Verify Final State
        task_response = await test_client.get(f"/api/tasks/{task_id}")
        assert task_response.status_code == 200
        assert task_response.json()["status"] == "completed"

async def test_task_error_handling(
    test_client: TestClient,
    test_agent: Dict[str, Any],
    db_session: Session
):
    """Test error handling during task execution."""
    # Create a task designed to fail
    task_data = TaskCreate(
        description="Test error handling",
        agent_role=test_agent["role"],
        expected_output="Error test",
        context={"force_error": True},
        async_execution=True
    )
    
    # Create and execute task
    response = await test_client.post(
        "/api/tasks/",
        json=task_data.dict()
    )
    assert response.status_code == 200
    task_id = response.json()["id"]
    
    # Monitor execution and error handling
    with test_client.websocket_connect(f"/ws/agent/{test_agent['id']}") as websocket:
        response = await test_client.post(f"/api/tasks/{task_id}/execute")
        assert response.status_code == 200
        
        # Verify error updates
        updates = []
        for _ in range(2):  # We expect: start and error
            data = websocket.receive_json()
            updates.append(data)
        
        # Verify error state
        assert any(u["status"] == "error" for u in updates)
        
        # Verify final error state
        task_response = await test_client.get(f"/api/tasks/{task_id}")
        assert task_response.status_code == 200
        assert task_response.json()["status"] == "error" 