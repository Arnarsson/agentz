"""Test task retry functionality."""
import pytest
from datetime import datetime, timedelta
from app.services.task_retry import TaskRetryService
from app.services.task import TaskService
from app.schemas.task import TaskCreate, TaskRetry
from app.core.errors import TaskError

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def test_task_with_retry(test_db, test_agents):
    """Create a test task with retry configuration."""
    agent = test_agents[0]
    
    task_data = TaskCreate(
        title="Test Task",
        description="Task with retry config",
        agent_id=agent.id,
        priority=1,
        retry_config=TaskRetry(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0
        ).dict()
    )
    
    return await TaskService.create_task(test_db, task_data)

async def test_retry_calculation(test_task_with_retry):
    """Test exponential backoff calculation."""
    retry_config = TaskRetry(**test_task_with_retry.retry_config)
    
    # First retry
    retry_config.current_attempt = 0
    next_time = TaskRetryService.calculate_next_retry(retry_config)
    assert isinstance(next_time, datetime)
    assert next_time > datetime.utcnow()
    first_delay = (next_time - datetime.utcnow()).total_seconds()
    assert 1.0 <= first_delay <= 2.0  # Base delay
    
    # Second retry
    retry_config.current_attempt = 1
    next_time = TaskRetryService.calculate_next_retry(retry_config)
    second_delay = (next_time - datetime.utcnow()).total_seconds()
    assert 2.0 <= second_delay <= 3.0  # Base delay * 2
    
    # Third retry (should hit max_delay)
    retry_config.current_attempt = 2
    next_time = TaskRetryService.calculate_next_retry(retry_config)
    third_delay = (next_time - datetime.utcnow()).total_seconds()
    assert third_delay <= 10.0  # Max delay

async def test_should_retry_logic(test_db, test_task_with_retry):
    """Test retry decision logic."""
    # Should retry on general error
    should_retry = await TaskRetryService.should_retry(
        test_db,
        test_task_with_retry.id,
        Exception("General error")
    )
    assert should_retry is True
    
    # Should not retry on non-retryable error
    should_retry = await TaskRetryService.should_retry(
        test_db,
        test_task_with_retry.id,
        Exception("AuthenticationError: Invalid token")
    )
    assert should_retry is False
    
    # Should not retry if max attempts reached
    retry_config = TaskRetry(**test_task_with_retry.retry_config)
    retry_config.current_attempt = retry_config.max_attempts
    await TaskService.update_task(
        test_db,
        test_task_with_retry.id,
        {"retry_config": retry_config.dict()}
    )
    
    should_retry = await TaskRetryService.should_retry(
        test_db,
        test_task_with_retry.id,
        Exception("General error")
    )
    assert should_retry is False

async def test_retry_scheduling(test_db, test_task_with_retry):
    """Test retry scheduling functionality."""
    error = Exception("Test error")
    
    # Schedule first retry
    next_retry = await TaskRetryService.schedule_retry(
        test_db,
        test_task_with_retry.id,
        error
    )
    
    assert next_retry is not None
    assert next_retry > datetime.utcnow()
    
    # Verify task state
    task = await TaskService.get_task(test_db, test_task_with_retry.id)
    assert task.status == "retry_scheduled"
    assert task.retry_config["current_attempt"] == 1
    assert task.retry_config["errors"] == ["Test error"]
    assert task.metrics["retry_count"] == 1

async def test_retry_execution(test_db, test_task_with_retry):
    """Test retry execution process."""
    # First attempt fails
    with pytest.raises(TaskError):
        await TaskRetryService.execute_retry(test_db, test_task_with_retry.id)
    
    # Verify retry was scheduled
    task = await TaskService.get_task(test_db, test_task_with_retry.id)
    assert task.status == "retry_scheduled"
    assert task.retry_config["current_attempt"] > 0
    
    # Mock successful retry
    result = await TaskRetryService.execute_retry(test_db, test_task_with_retry.id)
    assert result["status"] == "completed"
    
    # Verify final state
    task = await TaskService.get_task(test_db, test_task_with_retry.id)
    assert task.status == "completed"
    assert task.metrics["success_rate"] > 0.0 