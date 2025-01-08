from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from crewai import Agent as CrewAgent
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate, ToolConfig, LLMConfig
from app.schemas.task import TaskHistoryCreate, TaskHistoryUpdate, TaskMetrics
from app.core.config import settings
from app.core.logging import log_agent_action
from app.core.errors import AgentNotFoundError, AgentBusyError, TaskExecutionError
from app.core.websocket import ws_manager
from app.services.task_history import TaskHistoryService
from app.services.retry import RetryService
import uuid
from datetime import datetime
import time
import asyncio
from functools import partial

class AgentService:
    """Service for managing agents."""
    
    @staticmethod
    def _create_crew_agent(agent_data: AgentCreate) -> CrewAgent:
        """Create a CrewAI agent instance."""
        llm_config = agent_data.llm_config.dict() if agent_data.llm_config else {}
        tools = [tool.dict() for tool in agent_data.tools] if agent_data.tools else []
        
        return CrewAgent(
            role=agent_data.role,
            goal=agent_data.goal,
            backstory=agent_data.backstory,
            allow_delegation=agent_data.allow_delegation,
            verbose=agent_data.verbose,
            llm_config=llm_config,
            tools=tools,
            max_iterations=agent_data.max_iterations
        )

    @staticmethod
    async def create_agent(db: Session, agent_data: AgentCreate) -> Agent:
        """Create a new agent."""
        try:
            # Create CrewAI agent
            crew_agent = AgentService._create_crew_agent(agent_data)

            # Create database record
            now = datetime.utcnow().isoformat()
            agent_id = str(uuid.uuid4())
            
            db_agent = Agent(
                id=agent_id,
                role=agent_data.role,
                goal=agent_data.goal,
                backstory=agent_data.backstory,
                allow_delegation=agent_data.allow_delegation,
                verbose=agent_data.verbose,
                memory={},  # Initialize empty memory
                tools=agent_data.tools,
                llm_config=agent_data.llm_config,
                max_iterations=agent_data.max_iterations,
                created_at=now,
                updated_at=now,
                status="active",
                execution_status={"state": "idle", "last_update": now}
            )
            
            db.add(db_agent)
            db.commit()
            db.refresh(db_agent)
            
            log_agent_action(
                agent_id=agent_id,
                action="create",
                details={
                    "role": agent_data.role,
                    "goal": agent_data.goal,
                    "tools_count": len(agent_data.tools) if agent_data.tools else 0
                }
            )
            
            return db_agent
            
        except Exception as e:
            log_agent_action(
                agent_id=agent_id if 'agent_id' in locals() else "unknown",
                action="create",
                details={"error": str(e)},
                status="error",
                error=e
            )
            raise

    @staticmethod
    async def get_agent(db: Session, agent_id: str) -> Agent:
        """Get agent by ID."""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise AgentNotFoundError(agent_id)
        return agent

    @staticmethod
    async def get_agent_by_role(db: Session, role: str) -> Optional[Agent]:
        """Get agent by role."""
        return db.query(Agent).filter(Agent.role == role).first()

    @staticmethod
    async def list_agents(db: Session, skip: int = 0, limit: int = 100) -> List[Agent]:
        """List all agents."""
        return db.query(Agent).offset(skip).limit(limit).all()

    @staticmethod
    async def update_agent(
        db: Session, agent_id: str, agent_data: AgentUpdate
    ) -> Agent:
        """Update agent."""
        db_agent = await AgentService.get_agent(db, agent_id)
        if not db_agent:
            raise AgentNotFoundError(agent_id)

        try:
            # Update agent attributes
            update_data = agent_data.dict(exclude_unset=True)
            if update_data:
                update_data["updated_at"] = datetime.utcnow().isoformat()
                for field, value in update_data.items():
                    setattr(db_agent, field, value)

            db.commit()
            db.refresh(db_agent)
            
            log_agent_action(
                agent_id=agent_id,
                action="update",
                details={"updated_fields": list(update_data.keys())}
            )
            
            return db_agent
            
        except Exception as e:
            log_agent_action(
                agent_id=agent_id,
                action="update",
                details={"error": str(e)},
                status="error",
                error=e
            )
            raise

    @staticmethod
    async def delete_agent(db: Session, agent_id: str) -> bool:
        """Delete agent."""
        db_agent = await AgentService.get_agent(db, agent_id)
        if not db_agent:
            raise AgentNotFoundError(agent_id)

        try:
            db.delete(db_agent)
            db.commit()
            
            log_agent_action(
                agent_id=agent_id,
                action="delete",
                details={"role": db_agent.role}
            )
            
            return True
            
        except Exception as e:
            log_agent_action(
                agent_id=agent_id,
                action="delete",
                details={"error": str(e)},
                status="error",
                error=e
            )
            raise

    @staticmethod
    async def update_agent_status(
        db: Session, 
        agent_id: str, 
        status: str,
        execution_status: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """Update agent status and execution state."""
        db_agent = await AgentService.get_agent(db, agent_id)
        if not db_agent:
            raise AgentNotFoundError(agent_id)

        try:
            now = datetime.utcnow().isoformat()
            db_agent.status = status
            db_agent.updated_at = now
            
            if execution_status:
                execution_status["last_update"] = now
                db_agent.execution_status = execution_status

            db.commit()
            db.refresh(db_agent)
            
            # Log the status update
            log_agent_action(
                agent_id=agent_id,
                action="status_update",
                details={
                    "status": status,
                    "execution_status": execution_status
                }
            )
            
            # Broadcast status update via WebSocket
            await ws_manager.broadcast_status_update(
                agent_id=agent_id,
                status=status,
                execution_status=execution_status
            )
            
            return db_agent
            
        except Exception as e:
            log_agent_action(
                agent_id=agent_id,
                action="status_update",
                details={"error": str(e)},
                status="error",
                error=e
            )
            raise

    @staticmethod
    async def get_agent_instance(db: Session, agent_id: str) -> CrewAgent:
        """Get a CrewAI agent instance for a stored agent."""
        db_agent = await AgentService.get_agent(db, agent_id)
        if not db_agent:
            raise AgentNotFoundError(agent_id)
            
        # Convert stored agent to CrewAI agent
        agent_data = AgentCreate(
            role=db_agent.role,
            goal=db_agent.goal,
            backstory=db_agent.backstory,
            allow_delegation=db_agent.allow_delegation,
            verbose=db_agent.verbose,
            tools=db_agent.tools,
            llm_config=db_agent.llm_config,
            max_iterations=db_agent.max_iterations
        )
        return AgentService._create_crew_agent(agent_data)

    @staticmethod
    async def execute_task(
        db: Session,
        agent_id: str,
        task_id: str,
        crew_agent: CrewAgent,
        task_data: Dict[str, Any]
    ) -> None:
        """Execute a task with a CrewAI agent in the background."""
        start_time = time.time()
        task_history = None
        tools_used = []
        
        async def execute_with_tools() -> Dict[str, Any]:
            """Execute task with configured tools."""
            nonlocal tools_used
            if task_data.get("tools"):
                crew_agent.tools.extend(task_data["tools"])
                tools_used.extend(task_data["tools"])
                await ws_manager.broadcast_task_update(
                    agent_id=agent_id,
                    task_id=task_id,
                    status="executing",
                    progress=10,
                    message="Tools configured"
                )
            
            return await crew_agent.execute(
                task_data["task"],
                context=task_data.get("context", {})
            )
        
        try:
            # Create task history entry
            task_history = await TaskHistoryService.create_task_history(
                db,
                TaskHistoryCreate(
                    agent_id=agent_id,
                    task=task_data["task"],
                    context=task_data.get("context")
                )
            )
            
            # Update and broadcast initial status
            execution_status = {
                "state": "executing",
                "task_id": task_id,
                "progress": 0,
                "message": "Initializing task execution"
            }
            await AgentService.update_agent_status(
                db,
                agent_id,
                "working",
                execution_status=execution_status
            )
            
            await ws_manager.broadcast_task_update(
                agent_id=agent_id,
                task_id=task_id,
                status="executing",
                progress=0,
                message="Initializing task execution"
            )

            log_agent_action(
                agent_id=agent_id,
                action="task_start",
                details={
                    "task_id": task_id,
                    "task": task_data["task"]
                }
            )

            # Execute task with retry mechanism
            retry_config = RetryService.get_task_retry_config()
            result = await RetryService.with_retry(
                operation=execute_with_tools,
                config=retry_config,
                agent_id=agent_id,
                context={
                    "task_id": task_id,
                    "task": task_data["task"]
                }
            )

            # Calculate metrics
            execution_time = time.time() - start_time
            metrics = TaskMetrics(
                execution_time=execution_time,
                tokens_used=getattr(crew_agent, "tokens_used", None),
                iterations=getattr(crew_agent, "iterations", None),
                memory_usage=crew_agent.memory if hasattr(crew_agent, "memory") else None
            )

            # Update task history
            if task_history:
                await TaskHistoryService.update_task_history(
                    db,
                    task_history.id,
                    TaskHistoryUpdate(
                        status="completed",
                        tools_used=tools_used,
                        result=result
                    ),
                    metrics=metrics
                )

            # Update and broadcast completion status
            completion_status = {
                "state": "completed",
                "task_id": task_id,
                "progress": 100,
                "message": "Task completed successfully",
                "result": result
            }
            await AgentService.update_agent_status(
                db,
                agent_id,
                "active",
                execution_status=completion_status
            )
            
            await ws_manager.broadcast_task_update(
                agent_id=agent_id,
                task_id=task_id,
                status="completed",
                progress=100,
                message="Task completed successfully",
                result=result
            )
            
            log_agent_action(
                agent_id=agent_id,
                action="task_complete",
                details={
                    "task_id": task_id,
                    "result": result,
                    "execution_time": execution_time
                }
            )

            # Update analytics summary
            await TaskHistoryService.update_agent_analytics_summary(db, agent_id)

        except Exception as e:
            error_msg = f"Task execution failed: {str(e)}"
            error_status = {
                "state": "error",
                "task_id": task_id,
                "progress": 0,
                "message": error_msg,
                "error": str(e)
            }
            
            # Update task history with error
            if task_history:
                execution_time = time.time() - start_time
                metrics = TaskMetrics(
                    execution_time=execution_time,
                    tokens_used=getattr(crew_agent, "tokens_used", None),
                    iterations=getattr(crew_agent, "iterations", None),
                    memory_usage=crew_agent.memory if hasattr(crew_agent, "memory") else None
                )
                
                await TaskHistoryService.update_task_history(
                    db,
                    task_history.id,
                    TaskHistoryUpdate(
                        status="error",
                        tools_used=tools_used,
                        error={"message": str(e)}
                    ),
                    metrics=metrics
                )
            
            # Update and broadcast error status
            await AgentService.update_agent_status(
                db,
                agent_id,
                "active",
                execution_status=error_status
            )
            
            await ws_manager.broadcast_task_update(
                agent_id=agent_id,
                task_id=task_id,
                status="error",
                progress=0,
                message=error_msg,
                error=str(e)
            )
            
            log_agent_action(
                agent_id=agent_id,
                action="task_error",
                details={
                    "task_id": task_id,
                    "error": str(e),
                    "execution_time": time.time() - start_time
                },
                status="error",
                error=e
            )
            
            # Update analytics summary even on error
            await TaskHistoryService.update_agent_analytics_summary(db, agent_id)
            
            raise TaskExecutionError(
                task_id=task_id,
                reason=str(e),
                details={"agent_id": agent_id}
            ) 