import pytest
from datetime import datetime, timedelta
from app.services.task_history import TaskHistoryService
from app.schemas.task import (
    TaskHistoryCreate,
    TaskHistoryUpdate,
    TaskMetrics,
    TimeRange
)

@pytest.fixture
def task_data(test_agent):
    """Create test task data."""
    return TaskHistoryCreate(
        agent_id=test_agent.id,
        task="Test task",
        context={"test": "context"}
    )

@pytest.fixture
def task_metrics():
    """Create test task metrics."""
    return TaskMetrics(
        execution_time=1.5,
        tokens_used=100,
        iterations=3,
        memory_usage={"test": "memory"}
    )

async def test_create_task_history(db_session, task_data):
    """Test creating task history."""
    task = await TaskHistoryService.create_task_history(db_session, task_data)
    assert task.id is not None
    assert task.agent_id == task_data.agent_id
    assert task.task == task_data.task
    assert task.status == "executing"
    assert task.context == task_data.context

async def test_update_task_history(db_session, task_data, task_metrics):
    """Test updating task history."""
    task = await TaskHistoryService.create_task_history(db_session, task_data)
    
    update_data = TaskHistoryUpdate(
        status="completed",
        tools_used=[{"name": "test_tool"}],
        result={"output": "test"}
    )
    
    updated_task = await TaskHistoryService.update_task_history(
        db_session,
        task.id,
        update_data,
        metrics=task_metrics
    )
    
    assert updated_task.status == "completed"
    assert updated_task.tools_used == [{"name": "test_tool"}]
    assert updated_task.result == {"output": "test"}
    assert updated_task.execution_time == task_metrics.execution_time
    assert updated_task.completed_at is not None

async def test_list_agent_tasks(db_session, test_agent, task_data):
    """Test listing agent tasks."""
    # Create multiple tasks
    for i in range(3):
        task_data.task = f"Test task {i}"
        await TaskHistoryService.create_task_history(db_session, task_data)
    
    tasks = await TaskHistoryService.list_agent_tasks(db_session, test_agent.id)
    assert len(tasks) == 3
    assert all(task.agent_id == test_agent.id for task in tasks)

async def test_list_agent_tasks_with_time_range(db_session, test_agent, task_data):
    """Test listing agent tasks with time range."""
    # Create tasks with different timestamps
    now = datetime.utcnow()
    
    # Old task
    task_data.task = "Old task"
    old_task = await TaskHistoryService.create_task_history(db_session, task_data)
    old_task.created_at = (now - timedelta(days=2)).isoformat()
    db_session.commit()
    
    # Recent task
    task_data.task = "Recent task"
    await TaskHistoryService.create_task_history(db_session, task_data)
    
    # Query with time range
    time_range = TimeRange(
        start_time=(now - timedelta(days=1)).isoformat()
    )
    
    tasks = await TaskHistoryService.list_agent_tasks(
        db_session,
        test_agent.id,
        time_range=time_range
    )
    
    assert len(tasks) == 1
    assert tasks[0].task == "Recent task"

async def test_get_agent_analytics(db_session, test_agent, task_data):
    """Test getting agent analytics."""
    # Create tasks with different statuses
    statuses = ["completed", "completed", "error"]
    for status in statuses:
        task = await TaskHistoryService.create_task_history(db_session, task_data)
        update_data = TaskHistoryUpdate(
            status=status,
            tools_used=[{"name": "test_tool"}],
            result={"output": "test"} if status == "completed" else None,
            error={"message": "test error"} if status == "error" else None
        )
        await TaskHistoryService.update_task_history(
            db_session,
            task.id,
            update_data,
            metrics=TaskMetrics(
                execution_time=1.0,
                tokens_used=100
            )
        )
    
    analytics = await TaskHistoryService.get_agent_analytics(db_session, test_agent.id)
    
    assert analytics.total_tasks == 3
    assert analytics.completed_tasks == 2
    assert analytics.failed_tasks == 1
    assert analytics.success_rate == 2/3
    assert analytics.average_execution_time == 1.0
    assert analytics.total_tokens_used == 300
    assert len(analytics.common_errors) == 1

async def test_update_agent_analytics_summary(db_session, test_agent, task_data):
    """Test updating agent analytics summary."""
    # Create some tasks
    for i in range(3):
        task = await TaskHistoryService.create_task_history(db_session, task_data)
        update_data = TaskHistoryUpdate(
            status="completed",
            tools_used=[{"name": "test_tool"}],
            result={"output": "test"}
        )
        await TaskHistoryService.update_task_history(
            db_session,
            task.id,
            update_data,
            metrics=TaskMetrics(execution_time=1.0, tokens_used=100)
        )
    
    # Update analytics summary
    await TaskHistoryService.update_agent_analytics_summary(db_session, test_agent.id)
    
    # Verify agent's analytics field is updated
    agent = db_session.query(Agent).filter_by(id=test_agent.id).first()
    assert agent.analytics is not None
    assert "last_24h" in agent.analytics
    assert "last_7d" in agent.analytics
    assert "all_time" in agent.analytics
    assert agent.analytics["all_time"]["total_tasks"] == 3 