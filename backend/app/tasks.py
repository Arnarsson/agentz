from typing import Dict, Any
from celery import shared_task
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.agent import AgentService
from app.services.task import TaskService
from app.core.logging import log_task_action
import asyncio

@shared_task(name="app.tasks.execute_agent_task")
def execute_agent_task(task_id: str, agent_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a task with an agent asynchronously."""
    db = SessionLocal()
    try:
        # Get event loop or create new one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Execute task
        result = loop.run_until_complete(
            _execute_task(db, task_id, agent_id, task_data)
        )
        
        # Process result
        process_task_result.delay(task_id, result)
        
        return result
    finally:
        db.close()

@shared_task(name="app.tasks.process_task_result")
def process_task_result(task_id: str, result: Dict[str, Any]) -> None:
    """Process and store task execution results."""
    db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            TaskService.update_task(
                db,
                task_id,
                {"status": "completed", "result": result}
            )
        )
    finally:
        db.close()

async def _execute_task(
    db: Session,
    task_id: str,
    agent_id: str,
    task_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Internal function to execute task with proper async handling."""
    try:
        # Get agent
        agent = await AgentService.get_agent(db, agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Get agent instance from CrewAI
        crew_agent = await AgentService.get_agent_instance(db, agent_id)
        
        # Execute task
        result = await crew_agent.execute_task(task_data)
        
        # Log success
        log_task_action(
            task_id=task_id,
            action="execute",
            details={"status": "completed", "result": result}
        )
        
        return result
        
    except Exception as e:
        # Log error
        log_task_action(
            task_id=task_id,
            action="execute",
            details={"status": "error", "error": str(e)},
            error=e
        )
        raise 