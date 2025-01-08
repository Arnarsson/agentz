from pydantic import Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from .base import BaseSchema

class RetryConfig(BaseSchema):
    """Configuration for retry behavior."""
    max_attempts: int = Field(3, ge=1, description="Maximum number of retry attempts")
    initial_delay: float = Field(1.0, ge=0, description="Initial delay between retries in seconds")
    max_delay: float = Field(30.0, ge=0, description="Maximum delay between retries in seconds")
    exponential_base: float = Field(2.0, ge=1, description="Base for exponential backoff")
    retry_on_errors: List[str] = Field(
        default_factory=lambda: ["rate_limit", "timeout", "connection"],
        description="List of error types to retry on"
    )
    
    @validator("max_delay")
    def validate_max_delay(cls, v, values):
        if "initial_delay" in values and v < values["initial_delay"]:
            raise ValueError("max_delay must be greater than or equal to initial_delay")
        return v

class RetryState(BaseSchema):
    """State tracking for retries."""
    attempt: int = Field(1, ge=1, description="Current attempt number")
    next_retry: Optional[str] = Field(None, description="Timestamp for next retry")
    last_error: Optional[Dict[str, Any]] = Field(None, description="Details of last error")
    error_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of errors encountered"
    )

    def should_retry(self, config: RetryConfig) -> bool:
        """Check if another retry should be attempted."""
        if not self.last_error:
            return False
        
        if self.attempt >= config.max_attempts:
            return False
            
        error_type = self.last_error.get("type")
        if error_type not in config.retry_on_errors:
            return False
            
        return True
    
    def get_next_delay(self, config: RetryConfig) -> float:
        """Calculate delay for next retry using exponential backoff."""
        delay = config.initial_delay * (config.exponential_base ** (self.attempt - 1))
        return min(delay, config.max_delay)
    
    def update_for_retry(self, config: RetryConfig, error: Exception) -> None:
        """Update state for next retry attempt."""
        error_info = {
            "type": getattr(error, "type", type(error).__name__),
            "message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "attempt": self.attempt
        }
        
        self.error_history.append(error_info)
        self.last_error = error_info
        self.attempt += 1
        
        if self.should_retry(config):
            delay = self.get_next_delay(config)
            self.next_retry = (datetime.utcnow() + timedelta(seconds=delay)).isoformat()
            
    def reset(self) -> None:
        """Reset retry state."""
        self.attempt = 1
        self.next_retry = None
        self.last_error = None
        self.error_history = [] 