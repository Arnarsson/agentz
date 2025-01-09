"""Test agent execution functionality."""
import pytest
import asyncio
from app.services.agent import AgentService
from app.services.task import TaskService
from app.schemas.agent import AgentCreate, AgentUpdate
from app.schemas.task import TaskCreate
from app.core.errors import AgentError, TaskError

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def test_agents(test_db, sample_agent_data):
    """Create test agents for execution tests."""
    agent1_data = AgentCreate(**{
        **sample_agent_data,
        "role": "Researcher",
        "goal": "Research and analyze data",
        "allow_delegation": True
    })
    
    agent2_data = AgentCreate(**{
        **sample_agent_data,
        "role": "Writer",
        "goal": "Write clear documentation",
        "allow_delegation": True
    })
    
    agent1 = await AgentService.create_agent(test_db, agent1_data)
    agent2 = await AgentService.create_agent(test_db, agent2_data)
    
    return [agent1, agent2]

async def test_agent_task_execution(test_db, test_agents):
    """Test basic task execution by an agent."""
    agent = test_agents[0]
    
    # Create a task
    task_data = TaskCreate(
        title="Research Python AsyncIO",
        description="Research and summarize key AsyncIO concepts",
        agent_id=agent.id,
        priority=1
    )
    
    task = await TaskService.create_task(test_db, task_data)
    
    # Execute task
    result = await AgentService.execute_task(test_db, agent.id, task.id)
    
    assert result["status"] == "completed"
    assert "summary" in result["output"]
    assert result["execution_time"] > 0

async def test_agent_delegation(test_db, test_agents):
    """Test task delegation between agents."""
    researcher, writer = test_agents
    
    # Create a complex task that requires delegation
    task_data = TaskCreate(
        title="Create Technical Documentation",
        description="Research and write documentation for AsyncIO",
        agent_id=researcher.id,
        priority=1,
        requires_delegation=True
    )
    
    task = await TaskService.create_task(test_db, task_data)
    
    # Execute task with delegation
    result = await AgentService.execute_task_with_delegation(
        test_db,
        researcher.id,
        task.id,
        [writer.id]
    )
    
    assert result["status"] == "completed"
    assert result["delegations"]
    assert any(d["agent_id"] == writer.id for d in result["delegations"])
    assert "documentation" in result["output"].lower()

async def test_agent_memory_persistence(test_db, test_agents):
    """Test agent memory persistence across tasks."""
    agent = test_agents[0]
    
    # First task to store information
    task1_data = TaskCreate(
        title="Learn About Python GIL",
        description="Research the Global Interpreter Lock",
        agent_id=agent.id,
        priority=1
    )
    
    task1 = await TaskService.create_task(test_db, task1_data)
    result1 = await AgentService.execute_task(test_db, agent.id, task1.id)
    
    # Second task that requires previous knowledge
    task2_data = TaskCreate(
        title="Compare GIL Impact",
        description="Compare GIL impact on AsyncIO vs Threading",
        agent_id=agent.id,
        priority=1
    )
    
    task2 = await TaskService.create_task(test_db, task2_data)
    result2 = await AgentService.execute_task(test_db, agent.id, task2.id)
    
    # Verify memory persistence
    agent_state = await AgentService.get_agent(test_db, agent.id)
    assert "GIL" in str(agent_state.memory)
    assert result2["output"]

async def test_agent_error_handling(test_db, test_agents):
    """Test agent error handling and recovery."""
    agent = test_agents[0]
    
    # Create a task designed to fail
    task_data = TaskCreate(
        title="Invalid Task",
        description="This task is designed to fail",
        agent_id=agent.id,
        priority=1,
        execution_params={"force_error": True}
    )
    
    task = await TaskService.create_task(test_db, task_data)
    
    # Execute task and expect handled error
    with pytest.raises(TaskError, match="Task execution failed"):
        await AgentService.execute_task(test_db, agent.id, task.id)
    
    # Verify agent state is properly reset
    agent_state = await AgentService.get_agent(test_db, agent.id)
    assert agent_state.execution_status["state"] == "idle"
    assert not agent_state.execution_status.get("current_task")

async def test_agent_concurrent_tasks(test_db, test_agents):
    """Test handling of concurrent task execution attempts."""
    agent = test_agents[0]
    
    # Create multiple tasks
    task_data1 = TaskCreate(
        title="Task 1",
        description="First concurrent task",
        agent_id=agent.id,
        priority=1
    )
    
    task_data2 = TaskCreate(
        title="Task 2",
        description="Second concurrent task",
        agent_id=agent.id,
        priority=2
    )
    
    task1 = await TaskService.create_task(test_db, task_data1)
    task2 = await TaskService.create_task(test_db, task_data2)
    
    # Try to execute both tasks concurrently
    with pytest.raises(AgentError, match="Agent is busy"):
        async def run_concurrent_tasks():
            await asyncio.gather(
                AgentService.execute_task(test_db, agent.id, task1.id),
                AgentService.execute_task(test_db, agent.id, task2.id)
            )
        await run_concurrent_tasks()
    
    # Verify only one task was executed
    agent_state = await AgentService.get_agent(test_db, agent.id)
    assert agent_state.execution_status["state"] == "idle"
    assert len(agent_state.memory.get("completed_tasks", [])) == 1 