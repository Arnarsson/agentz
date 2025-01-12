"""Comprehensive retry service with enhanced tracking and metrics."""
from typing import Optional, Dict, Any, Callable, Awaitable, TypeVar, cast, List
from datetime import datetime, timedelta
import asyncio
import json
from app.schemas.retry import RetryConfig, RetryState, RetryMetrics
from app.core.logging import log_agent_action
from app.core.websocket import ws_manager

T = TypeVar('T')

class RetryService:
    """Service for managing retries with exponential backoff and metrics tracking."""
    
    _retry_metrics: Dict[str, RetryMetrics] = {}
    
    @staticmethod
    def _is_retriable_error(error: Exception, config: RetryConfig) -> bool:
        """Check if an error should be retried based on configuration."""
        error_type = getattr(error, "type", type(error).__name__)
        return error_type in config.retry_on_errors

    @staticmethod
    def _update_metrics(
        agent_id: str,
        success: bool,
        attempts: int,
        total_delay: float,
        error_type: Optional[str] = None
    ) -> None:
        """Update retry metrics for an agent."""
        if agent_id not in RetryService._retry_metrics:
            RetryService._retry_metrics[agent_id] = RetryMetrics(
                total_retries=0,
                successful_retries=0,
                failed_retries=0,
                total_delay=0.0,
                error_counts={},
                last_updated=datetime.utcnow()
            )
        
        metrics = RetryService._retry_metrics[agent_id]
        metrics.total_retries += 1
        metrics.total_delay += total_delay
        
        if success:
            metrics.successful_retries += 1
        else:
            metrics.failed_retries += 1
            
        if error_type:
            metrics.error_counts[error_type] = (
                metrics.error_counts.get(error_type, 0) + 1
            )
            
        metrics.last_updated = datetime.utcnow()

    @staticmethod
    async def with_retry(
        operation: Callable[[], Awaitable[T]],
        config: RetryConfig,
        agent_id: str,
        context: Dict[str, Any]
    ) -> T:
        """Execute an operation with retry logic and metrics tracking."""
        state = RetryState()
        start_time = datetime.utcnow()
        total_delay = 0.0
        
        while True:
            try:
                result = await operation()
                if state.attempt > 1:
                    # Update metrics for successful retry
                    RetryService._update_metrics(
                        agent_id=agent_id,
                        success=True,
                        attempts=state.attempt,
                        total_delay=total_delay
                    )
                    
                    # Log successful retry
                    log_agent_action(
                        agent_id=agent_id,
                        action="retry_success",
                        details={
                            "attempts": state.attempt,
                            "error_history": state.error_history,
                            "total_delay": total_delay,
                            "execution_time": (
                                datetime.utcnow() - start_time
                            ).total_seconds(),
                            **context
                        }
                    )
                    
                    # Broadcast retry success
                    await ws_manager.broadcast_agent_retry(
                        agent_id=agent_id,
                        status="success",
                        details={
                            "attempts": state.attempt,
                            "total_delay": total_delay,
                            "metrics": RetryService._retry_metrics[agent_id].dict()
                        }
                    )
                    
                return result
                
            except Exception as e:
                state.update_for_retry(config, e)
                error_type = getattr(e, "type", type(e).__name__)
                
                if not state.should_retry(config):
                    # Update metrics for final failure
                    RetryService._update_metrics(
                        agent_id=agent_id,
                        success=False,
                        attempts=state.attempt,
                        total_delay=total_delay,
                        error_type=error_type
                    )
                    
                    # Log final failure
                    log_agent_action(
                        agent_id=agent_id,
                        action="retry_exhausted",
                        details={
                            "attempts": state.attempt,
                            "error_history": state.error_history,
                            "total_delay": total_delay,
                            "execution_time": (
                                datetime.utcnow() - start_time
                            ).total_seconds(),
                            **context
                        },
                        status="error",
                        error=e
                    )
                    
                    # Broadcast retry failure
                    await ws_manager.broadcast_agent_retry(
                        agent_id=agent_id,
                        status="failed",
                        details={
                            "attempts": state.attempt,
                            "total_delay": total_delay,
                            "error": str(e),
                            "metrics": RetryService._retry_metrics[agent_id].dict()
                        }
                    )
                    
                    raise
                
                # Calculate next delay
                delay = state.get_next_delay(config)
                total_delay += delay
                
                # Log retry attempt
                log_agent_action(
                    agent_id=agent_id,
                    action="retry_attempt",
                    details={
                        "attempt": state.attempt,
                        "next_retry": state.next_retry,
                        "delay": delay,
                        "total_delay": total_delay,
                        "error": state.last_error,
                        **context
                    }
                )
                
                # Broadcast retry attempt
                await ws_manager.broadcast_agent_retry(
                    agent_id=agent_id,
                    status="retrying",
                    details={
                        "attempt": state.attempt,
                        "delay": delay,
                        "total_delay": total_delay,
                        "error": str(e)
                    }
                )
                
                # Wait before retry
                await asyncio.sleep(delay)

    @staticmethod
    def create_default_config(
        max_attempts: Optional[int] = None,
        initial_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        retry_on_errors: Optional[list[str]] = None,
        jitter: Optional[float] = None,
        backoff_factor: Optional[float] = None
    ) -> RetryConfig:
        """Create a RetryConfig with optional overrides and enhanced options."""
        config_data = {
            "max_attempts": max_attempts or 3,
            "initial_delay": initial_delay or 1.0,
            "max_delay": max_delay or 30.0,
            "retry_on_errors": retry_on_errors or [
                "rate_limit",
                "timeout",
                "connection",
                "server_error"
            ],
            "jitter": jitter or 0.1,
            "backoff_factor": backoff_factor or 2.0
        }
            
        return RetryConfig(**config_data)

    @staticmethod
    def get_task_retry_config() -> RetryConfig:
        """Get retry configuration for task execution with enhanced settings."""
        return RetryConfig(
            max_attempts=3,
            initial_delay=2.0,
            max_delay=30.0,
            retry_on_errors=[
                "rate_limit",
                "timeout",
                "connection",
                "server_error",
                "resource_exhausted",
                "temporary_failure"
            ],
            jitter=0.2,
            backoff_factor=2.0
        )

    @staticmethod
    def get_api_retry_config() -> RetryConfig:
        """Get retry configuration for API calls with enhanced settings."""
        return RetryConfig(
            max_attempts=5,
            initial_delay=1.0,
            max_delay=15.0,
            retry_on_errors=[
                "rate_limit",
                "timeout",
                "connection",
                "server_error",
                "bad_gateway",
                "service_unavailable"
            ],
            jitter=0.1,
            backoff_factor=1.5
        )

    @staticmethod
    def get_agent_retry_metrics(agent_id: str) -> Optional[RetryMetrics]:
        """Get retry metrics for a specific agent."""
        return RetryService._retry_metrics.get(agent_id)

    @staticmethod
    def get_all_retry_metrics() -> Dict[str, RetryMetrics]:
        """Get retry metrics for all agents."""
        return RetryService._retry_metrics

    @staticmethod
    def clear_old_metrics(max_age: timedelta = timedelta(hours=24)) -> None:
        """Clear metrics older than specified age."""
        now = datetime.utcnow()
        to_remove = [
            agent_id for agent_id, metrics in RetryService._retry_metrics.items()
            if now - metrics.last_updated > max_age
        ]
        for agent_id in to_remove:
            del RetryService._retry_metrics[agent_id]

    @staticmethod
    def get_retry_summary(
        agent_ids: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get summary of retry metrics for specified agents and time range."""
        metrics = RetryService._retry_metrics
        if agent_ids:
            metrics = {
                k: v for k, v in metrics.items()
                if k in agent_ids
            }
        if start_time:
            metrics = {
                k: v for k, v in metrics.items()
                if v.last_updated >= start_time
            }
        if end_time:
            metrics = {
                k: v for k, v in metrics.items()
                if v.last_updated <= end_time
            }
            
        if not metrics:
            return {
                "total_agents": 0,
                "total_retries": 0,
                "success_rate": 0.0,
                "average_delay": 0.0,
                "error_distribution": {}
            }
            
        total_retries = sum(m.total_retries for m in metrics.values())
        total_success = sum(m.successful_retries for m in metrics.values())
        total_delay = sum(m.total_delay for m in metrics.values())
        
        # Aggregate error counts
        error_counts: Dict[str, int] = {}
        for m in metrics.values():
            for error_type, count in m.error_counts.items():
                error_counts[error_type] = error_counts.get(error_type, 0) + count
                
        return {
            "total_agents": len(metrics),
            "total_retries": total_retries,
            "success_rate": (
                total_success / total_retries if total_retries > 0 else 0.0
            ),
            "average_delay": (
                total_delay / total_retries if total_retries > 0 else 0.0
            ),
            "error_distribution": error_counts
        } 