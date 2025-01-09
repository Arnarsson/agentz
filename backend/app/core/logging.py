"""Logging configuration module."""
from typing import Dict, Any
from loguru import logger
from datetime import datetime

def log_agent_action(agent_id: str, action: str, data: Dict[str, Any]) -> None:
    """Log agent action."""
    logger.info(
        f"Agent {agent_id} - {action}",
        agent_id=agent_id,
        action=action,
        data=data,
        timestamp=datetime.utcnow().isoformat()
    )

def log_task_action(task_id: str, action: str, data: Dict[str, Any]) -> None:
    """Log task action."""
    logger.info(
        f"Task {task_id} - {action}",
        task_id=task_id,
        action=action,
        data=data,
        timestamp=datetime.utcnow().isoformat()
    )

def log_error(error_type: str, message: str, details: Dict[str, Any]) -> None:
    """Log error."""
    logger.error(
        f"{error_type}: {message}",
        error_type=error_type,
        message=message,
        details=details,
        timestamp=datetime.utcnow().isoformat()
    ) 