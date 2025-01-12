"""Error handling module."""
from typing import Dict, Any, Optional

class AgentError(Exception):
    """Base class for agent-related errors."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        """Initialize error."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class AgentNotFoundError(AgentError):
    """Error raised when an agent is not found."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize error."""
        super().__init__(message, status_code=404, details=details)

class AgentBusyError(AgentError):
    """Error raised when an agent is busy."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize error."""
        super().__init__(message, status_code=409, details=details)

class AgentMemoryError(AgentError):
    """Error raised when agent memory operations fail."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize error."""
        super().__init__(message, status_code=500, details=details)

class TaskError(Exception):
    """Base class for task-related errors."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        """Initialize error."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class TaskNotFoundError(TaskError):
    """Error raised when a task is not found."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize error."""
        super().__init__(message, status_code=404, details=details)

class TaskExecutionError(TaskError):
    """Error raised when task execution fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize error."""
        super().__init__(message, status_code=500, details=details)

"""Custom error classes for the application."""

class MemoryError(Exception):
    """Error raised when memory operations fail."""
    pass

class EmbeddingError(Exception):
    """Error raised when embedding operations fail."""
    pass

class ConsolidationError(Exception):
    """Error raised when memory consolidation fails."""
    pass 