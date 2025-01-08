from loguru import logger
from typing import Dict, Any
from datetime import datetime

def setup_logging():
    """Configure loguru logger with structured format."""
    logger.remove()  # Remove default handler
    logger.add(
        "logs/agent_{time}.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
        serialize=True
    )

def log_agent_action(
    agent_id: str,
    action: str,
    details: Dict[str, Any],
    status: str = "info",
    error: Exception = None
):
    """Log agent actions in a structured format."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": agent_id,
        "action": action,
        "details": details,
        "status": status
    }
    
    if error:
        log_data["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "details": getattr(error, "details", None)
        }
        logger.error(log_data)
    else:
        logger.info(log_data) 