"""Test agent creation functionality."""
import pytest
from pydantic import ValidationError

from app.core.errors import AgentError
from app.schemas.agent import AgentCreate
from app.schemas.tool import Tool, ToolConfig
from app.services.agent import AgentService

@pytest.fixture
def basic_agent_data():
    """Basic agent data fixture."""
    return {
        "role": "BasicAgent",
        "goal": "Research and analyze data efficiently",
        "backstory": "An AI researcher specialized in data analysis",
        "allow_delegation": True,
        "verbose": True,
        "memory": {},
        "tools": [],
        "llm_config": {
            "temperature": 0.7,
            "model": "gpt-4"
        },
        "max_iterations": 5
    }

@pytest.fixture
def tool_enabled_agent_data():
    """Tool-enabled agent data fixture."""
    return {
        "role": "ToolAgent",
        "goal": "Research and analyze data efficiently",
        "backstory": "An AI researcher specialized in data analysis",
        "allow_delegation": True,
        "verbose": True,
        "memory": {},
        "tools": [
            Tool(
                name="search",
                description="Search the web",
                config=ToolConfig(
                    api_key="valid_key",
                    endpoint="https://api.search.com"
                )
            )
        ],
        "llm_config": {
            "temperature": 0.7,
            "model": "gpt-4"
        },
        "max_iterations": 5
    }

async def test_create_basic_agent(test_db, basic_agent_data):
    """Test creation of a basic agent without tools."""
    agent_data = AgentCreate(**basic_agent_data)
    agent = await AgentService.create_agent(test_db, agent_data)

    assert agent.role == basic_agent_data["role"]
    assert agent.goal == basic_agent_data["goal"]
    assert agent.backstory == basic_agent_data["backstory"]
    assert agent.allow_delegation == basic_agent_data["allow_delegation"]
    assert agent.verbose == basic_agent_data["verbose"]
    assert agent.memory == basic_agent_data["memory"]
    assert agent.tools == basic_agent_data["tools"]
    
    # Compare only the provided LLM config fields
    for key, value in basic_agent_data["llm_config"].items():
        assert agent.llm_config[key] == value
    
    assert agent.max_iterations == basic_agent_data["max_iterations"]
    assert agent.status == "active"

async def test_create_tool_enabled_agent(test_db, tool_enabled_agent_data):
    """Test creation of an agent with tools."""
    agent_data = AgentCreate(**tool_enabled_agent_data)
    agent = await AgentService.create_agent(test_db, agent_data)

    assert agent.role == tool_enabled_agent_data["role"]
    assert len(agent.tools) == 1
    assert agent.tools[0]["name"] == "search"
    assert agent.tools[0]["description"] == "Search the web"
    assert agent.tools[0]["config"]["api_key"] == "valid_key"
    assert agent.tools[0]["config"]["endpoint"] == "https://api.search.com"

async def test_create_agent_validation(test_db, basic_agent_data):
    """Test agent creation validation."""
    # Test missing required fields
    invalid_data = basic_agent_data.copy()
    del invalid_data["role"]

    with pytest.raises(ValidationError) as exc_info:
        await AgentService.create_agent(test_db, AgentCreate(**invalid_data))
    assert "role" in str(exc_info.value)

async def test_create_agent_with_invalid_tool(test_db, tool_enabled_agent_data):
    """Test agent creation with invalid tool configuration."""
    # Create invalid tool data
    invalid_tool_data = tool_enabled_agent_data.copy()
    invalid_tool_data["role"] = "InvalidToolAgent"
    invalid_tool_data["tools"] = [
        Tool(
            name="invalid_tool",
            description="Tool with invalid config",
            config=ToolConfig(
                api_key="",  # Empty API key should fail validation
                endpoint="https://api.example.com"
            )
        )
    ]

    with pytest.raises(ValidationError) as exc_info:
        await AgentService.create_agent(test_db, AgentCreate(**invalid_tool_data))
    assert "api_key" in str(exc_info.value)

async def test_create_duplicate_agent_role(test_db, basic_agent_data):
    """Test creating agents with duplicate roles."""
    agent_data = AgentCreate(**basic_agent_data)
    duplicate_data = basic_agent_data.copy()
    duplicate_data["role"] = "DuplicateAgent"

    # Create first agent
    await AgentService.create_agent(test_db, AgentCreate(**duplicate_data))

    # Attempt to create second agent with same role
    with pytest.raises(AgentError) as exc_info:
        await AgentService.create_agent(test_db, AgentCreate(**duplicate_data))
    assert "already exists" in str(exc_info.value)

async def test_create_agent_with_memory_initialization(test_db, basic_agent_data):
    """Test agent creation with initial memory state."""
    initial_memory = {
        "context": {
            "domain": "scientific_research",
            "specialization": "data_analysis"
        },
        "preferences": {
            "data_format": "json",
            "output_style": "concise"
        }
    }

    memory_agent_data = basic_agent_data.copy()
    memory_agent_data["role"] = "MemoryAgent"
    memory_agent_data["memory"] = initial_memory

    agent = await AgentService.create_agent(test_db, AgentCreate(**memory_agent_data))
    assert agent.memory == initial_memory 