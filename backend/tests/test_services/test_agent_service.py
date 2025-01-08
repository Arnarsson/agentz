import pytest
from app.services.agent import AgentService
from app.schemas.agent import AgentCreate, AgentUpdate

pytestmark = pytest.mark.asyncio

async def test_create_agent(test_db, sample_agent_data):
    """Test creating an agent."""
    agent_data = AgentCreate(**sample_agent_data)
    agent = await AgentService.create_agent(test_db, agent_data)
    
    assert agent.role == sample_agent_data["role"]
    assert agent.goal == sample_agent_data["goal"]
    assert agent.backstory == sample_agent_data["backstory"]
    assert agent.allow_delegation == sample_agent_data["allow_delegation"]
    assert agent.verbose == sample_agent_data["verbose"]
    assert agent.memory == {}

async def test_get_agent(test_db, sample_agent_data):
    """Test retrieving an agent by ID."""
    # Create agent first
    agent_data = AgentCreate(**sample_agent_data)
    created_agent = await AgentService.create_agent(test_db, agent_data)
    
    # Retrieve agent
    agent = await AgentService.get_agent(test_db, created_agent.id)
    assert agent is not None
    assert agent.id == created_agent.id
    assert agent.role == sample_agent_data["role"]

async def test_get_agent_by_role(test_db, sample_agent_data):
    """Test retrieving an agent by role."""
    # Create agent first
    agent_data = AgentCreate(**sample_agent_data)
    await AgentService.create_agent(test_db, agent_data)
    
    # Retrieve agent by role
    agent = await AgentService.get_agent_by_role(test_db, sample_agent_data["role"])
    assert agent is not None
    assert agent.role == sample_agent_data["role"]

async def test_list_agents(test_db, sample_agent_data):
    """Test listing all agents."""
    # Create multiple agents
    agent_data1 = AgentCreate(**sample_agent_data)
    agent_data2 = AgentCreate(**{**sample_agent_data, "role": "Test Agent 2"})
    
    await AgentService.create_agent(test_db, agent_data1)
    await AgentService.create_agent(test_db, agent_data2)
    
    # List agents
    agents = await AgentService.list_agents(test_db)
    assert len(agents) == 2
    assert any(a.role == "Test Agent" for a in agents)
    assert any(a.role == "Test Agent 2" for a in agents)

async def test_update_agent(test_db, sample_agent_data):
    """Test updating an agent."""
    # Create agent first
    agent_data = AgentCreate(**sample_agent_data)
    created_agent = await AgentService.create_agent(test_db, agent_data)
    
    # Update agent
    update_data = AgentUpdate(goal="Updated goal")
    updated_agent = await AgentService.update_agent(test_db, created_agent.id, update_data)
    
    assert updated_agent is not None
    assert updated_agent.id == created_agent.id
    assert updated_agent.goal == "Updated goal"
    assert updated_agent.role == sample_agent_data["role"]  # Unchanged field

async def test_delete_agent(test_db, sample_agent_data):
    """Test deleting an agent."""
    # Create agent first
    agent_data = AgentCreate(**sample_agent_data)
    created_agent = await AgentService.create_agent(test_db, agent_data)
    
    # Delete agent
    success = await AgentService.delete_agent(test_db, created_agent.id)
    assert success is True
    
    # Verify agent is deleted
    deleted_agent = await AgentService.get_agent(test_db, created_agent.id)
    assert deleted_agent is None

async def test_delete_nonexistent_agent(test_db):
    """Test deleting a nonexistent agent."""
    success = await AgentService.delete_agent(test_db, "nonexistent-id")
    assert success is False 