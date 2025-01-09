from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Task routes
celery_app.conf.task_routes = {
    "app.tasks.execute_agent_task": {"queue": "agent_tasks"},
    "app.tasks.process_task_result": {"queue": "results"}
}

# Task settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True
) 