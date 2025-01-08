from typing import Optional, Dict, Any, Callable, Awaitable, TypeVar, cast
from datetime import datetime
import asyncio
from app.schemas.retry import RetryConfig, RetryState
from app.core.logging import log_agent_action

T = TypeVar('T')

class RetryService:
    """Service for managing retries with exponential backoff."""
    
    @staticmethod
    def _is_retriable_error(error: Exception, config: RetryConfig) -> bool:
        """Check if an error should be retried based on configuration."""
        error_type = getattr(error, "type", type(error).__name__)
        return error_type in config.retry_on_errors

    @staticmethod
    async def with_retry(
        operation: Callable[[], Awaitable[T]],
        config: RetryConfig,
        agent_id: str,
        context: Dict[str, Any]
    ) -> T:
        """Execute an operation with retry logic."""
        state = RetryState()
        
        while True:
            try:
                result = await operation()
                if state.attempt > 1:
                    # Log successful retry
                    log_agent_action(
                        agent_id=agent_id,
                        action="retry_success",
                        details={
                            "attempts": state.attempt,
                            "error_history": state.error_history,
                            **context
                        }
                    )
                return result
                
            except Exception as e:
                state.update_for_retry(config, e)
                
                if not state.should_retry(config):
                    # Log final failure
                    log_agent_action(
                        agent_id=agent_id,
                        action="retry_exhausted",
                        details={
                            "attempts": state.attempt,
                            "error_history": state.error_history,
                            **context
                        },
                        status="error",
                        error=e
                    )
                    raise
                
                # Log retry attempt
                log_agent_action(
                    agent_id=agent_id,
                    action="retry_attempt",
                    details={
                        "attempt": state.attempt,
                        "next_retry": state.next_retry,
                        "delay": state.get_next_delay(config),
                        "error": state.last_error,
                        **context
                    }
                )
                
                # Wait before retry
                await asyncio.sleep(state.get_next_delay(config))

    @staticmethod
    def create_default_config(
        max_attempts: Optional[int] = None,
        initial_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        retry_on_errors: Optional[list[str]] = None
    ) -> RetryConfig:
        """Create a RetryConfig with optional overrides."""
        config_data = {}
        
        if max_attempts is not None:
            config_data["max_attempts"] = max_attempts
        if initial_delay is not None:
            config_data["initial_delay"] = initial_delay
        if max_delay is not None:
            config_data["max_delay"] = max_delay
        if retry_on_errors is not None:
            config_data["retry_on_errors"] = retry_on_errors
            
        return RetryConfig(**config_data)

    @staticmethod
    def get_task_retry_config() -> RetryConfig:
        """Get retry configuration for task execution."""
        return RetryConfig(
            max_attempts=3,
            initial_delay=2.0,
            max_delay=30.0,
            retry_on_errors=[
                "rate_limit",
                "timeout",
                "connection",
                "server_error",
                "resource_exhausted"
            ]
        )

    @staticmethod
    def get_api_retry_config() -> RetryConfig:
        """Get retry configuration for API calls."""
        return RetryConfig(
            max_attempts=5,
            initial_delay=1.0,
            max_delay=15.0,
            retry_on_errors=[
                "rate_limit",
                "timeout",
                "connection",
                "server_error"
            ]
        ) 