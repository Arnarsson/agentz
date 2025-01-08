import pytest
from datetime import datetime, timedelta
import asyncio
from app.services.retry import RetryService
from app.schemas.retry import RetryConfig, RetryState

class TestError(Exception):
    """Test error for retry testing."""
    type = "test_error"

class RateLimitError(Exception):
    """Simulated rate limit error."""
    type = "rate_limit"

@pytest.fixture
def retry_config():
    """Create test retry configuration."""
    return RetryConfig(
        max_attempts=3,
        initial_delay=0.1,  # Short delays for testing
        max_delay=0.3,
        retry_on_errors=["rate_limit", "timeout"]
    )

async def test_retry_success_after_failure():
    """Test successful retry after initial failure."""
    attempt = 0
    
    async def test_operation():
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            raise RateLimitError("Rate limit exceeded")
        return "success"
    
    result = await RetryService.with_retry(
        operation=test_operation,
        config=RetryConfig(
            max_attempts=3,
            initial_delay=0.1,
            max_delay=0.3,
            retry_on_errors=["rate_limit"]
        ),
        agent_id="test_agent",
        context={"test": "context"}
    )
    
    assert result == "success"
    assert attempt == 2

async def test_retry_exhaustion():
    """Test retry exhaustion after max attempts."""
    attempt = 0
    
    async def test_operation():
        nonlocal attempt
        attempt += 1
        raise RateLimitError("Rate limit exceeded")
    
    with pytest.raises(RateLimitError):
        await RetryService.with_retry(
            operation=test_operation,
            config=RetryConfig(
                max_attempts=3,
                initial_delay=0.1,
                max_delay=0.3,
                retry_on_errors=["rate_limit"]
            ),
            agent_id="test_agent",
            context={"test": "context"}
        )
    
    assert attempt == 3

async def test_no_retry_for_unspecified_error():
    """Test that unspecified errors are not retried."""
    attempt = 0
    
    async def test_operation():
        nonlocal attempt
        attempt += 1
        raise TestError("Unspecified error")
    
    with pytest.raises(TestError):
        await RetryService.with_retry(
            operation=test_operation,
            config=RetryConfig(
                max_attempts=3,
                initial_delay=0.1,
                max_delay=0.3,
                retry_on_errors=["rate_limit"]
            ),
            agent_id="test_agent",
            context={"test": "context"}
        )
    
    assert attempt == 1

async def test_exponential_backoff():
    """Test exponential backoff timing."""
    delays = []
    start_times = []
    
    async def test_operation():
        start_times.append(datetime.utcnow())
        raise RateLimitError("Rate limit exceeded")
    
    config = RetryConfig(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=0.4,
        retry_on_errors=["rate_limit"]
    )
    
    with pytest.raises(RateLimitError):
        await RetryService.with_retry(
            operation=test_operation,
            config=config,
            agent_id="test_agent",
            context={"test": "context"}
        )
    
    # Calculate actual delays
    for i in range(1, len(start_times)):
        delay = (start_times[i] - start_times[i-1]).total_seconds()
        delays.append(delay)
    
    # Verify exponential increase
    assert delays[1] > delays[0]
    assert 0.1 <= delays[0] <= 0.15  # Initial delay
    assert 0.2 <= delays[1] <= 0.25  # Second delay (exponential)

def test_retry_state_management():
    """Test retry state management."""
    state = RetryState()
    config = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=5.0,
        retry_on_errors=["rate_limit"]
    )
    
    # Test initial state
    assert state.attempt == 1
    assert state.next_retry is None
    assert state.error_history == []
    
    # Test state update
    error = RateLimitError("Test error")
    state.update_for_retry(config, error)
    
    assert state.attempt == 2
    assert state.last_error is not None
    assert state.last_error["type"] == "rate_limit"
    assert len(state.error_history) == 1
    
    # Test should_retry logic
    assert state.should_retry(config) is True
    state.attempt = config.max_attempts
    assert state.should_retry(config) is False
    
    # Test reset
    state.reset()
    assert state.attempt == 1
    assert state.next_retry is None
    assert state.error_history == []

def test_retry_config_validation():
    """Test retry configuration validation."""
    # Test valid config
    config = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=5.0,
        retry_on_errors=["rate_limit"]
    )
    assert config.max_attempts == 3
    
    # Test invalid max_delay
    with pytest.raises(ValueError):
        RetryConfig(
            max_attempts=3,
            initial_delay=5.0,
            max_delay=1.0,  # Less than initial_delay
            retry_on_errors=["rate_limit"]
        )

def test_default_configs():
    """Test default retry configurations."""
    # Test task config
    task_config = RetryService.get_task_retry_config()
    assert task_config.max_attempts == 3
    assert "rate_limit" in task_config.retry_on_errors
    assert "resource_exhausted" in task_config.retry_on_errors
    
    # Test API config
    api_config = RetryService.get_api_retry_config()
    assert api_config.max_attempts == 5
    assert "rate_limit" in api_config.retry_on_errors
    assert "server_error" in api_config.retry_on_errors 