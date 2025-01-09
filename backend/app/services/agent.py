"""Agent service module."""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate
from app.core.errors import AgentError, AgentNotFoundError, AgentBusyError
from app.core.logging import log_agent_action
from app.core.config import settings
import uuid

class AgentService:
    """Service for managing agents."""
    
    @staticmethod
    async def create_agent(db: Session, agent_data: AgentCreate) -> Agent:
        """Create a new agent."""
        try:
            # Create agent
            agent = Agent(
                id=str(uuid.uuid4()),
                role=agent_data.role,
                goal=agent_data.goal,
                backstory=agent_data.backstory,
                allow_delegation=agent_data.allow_delegation,
                verbose=agent_data.verbose,
                memory=agent_data.memory,
                tools=agent_data.tools,
                llm_config=agent_data.llm_config,
                max_iterations=agent_data.max_iterations,
                status="active"
            )
            
            # Add to database
            db.add(agent)
            db.commit()
            db.refresh(agent)
            
            # Log action
            log_agent_action(agent.id, "create", agent_data.dict())
            
            return agent
            
        except Exception as e:
            db.rollback()
            raise AgentError(f"Failed to create agent: {str(e)}")
    
    @staticmethod
    async def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return db.query(Agent).filter(Agent.id == agent_id).first()
    
    @staticmethod
    async def get_agent_by_role(db: Session, role: str) -> Optional[Agent]:
        """Get agent by role."""
        return db.query(Agent).filter(Agent.role == role).first()
    
    @staticmethod
    async def list_agents(db: Session, skip: int = 0, limit: int = 100) -> List[Agent]:
        """List all agents."""
        return db.query(Agent).offset(skip).limit(limit).all()
    
    @staticmethod
    async def update_agent(db: Session, agent_id: str, agent_data: AgentUpdate) -> Optional[Agent]:
        """Update agent."""
        try:
            agent = await AgentService.get_agent(db, agent_id)
            if not agent:
                return None
            
            # Update fields
            for field, value in agent_data.dict(exclude_unset=True).items():
                setattr(agent, field, value)
            
            # Commit changes
            db.commit()
            db.refresh(agent)
            
            # Log action
            log_agent_action(agent.id, "update", agent_data.dict(exclude_unset=True))
            
            return agent
            
        except Exception as e:
            db.rollback()
            raise AgentError(f"Failed to update agent: {str(e)}")
    
    @staticmethod
    async def delete_agent(db: Session, agent_id: str) -> bool:
        """Delete agent."""
        try:
            agent = await AgentService.get_agent(db, agent_id)
            if not agent:
                return False
            
            # Delete agent
            db.delete(agent)
            db.commit()
            
            # Log action
            log_agent_action(agent_id, "delete", {"agent_id": agent_id})
            
            return True
            
        except Exception as e:
            db.rollback()
            raise AgentError(f"Failed to delete agent: {str(e)}")
    
    @staticmethod
    async def execute_task(
        db: Session,
        agent: Agent,
        task: str,
        task_id: str,
        tools: List[Dict[str, Any]] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a task with an agent."""
        try:
            # Check if agent is available
            if agent.status != "active":
                raise AgentBusyError(
                    f"Agent {agent.id} is not active",
                    details={"status": agent.status}
                )
            
            # Update agent status
            agent.status = "working"
            agent.execution_status = {
                "task_id": task_id,
                "state": "executing",
                "progress": 0,
                "message": f"Starting task: {task}"
            }
            db.commit()
            
            # Log action
            log_agent_action(agent.id, "task_start", {
                "task_id": task_id,
                "task": task,
                "tools": tools,
                "context": context
            })
            
            try:
                # TODO: Implement actual task execution logic
                # This is a placeholder that simulates task execution
                result = {
                    "task_id": task_id,
                    "status": "completed",
                    "message": f"Task completed: {task}",
                    "result": "Task execution placeholder"
                }
                
                # Update agent status
                agent.status = "active"
                agent.execution_status = None
                db.commit()
                
                # Log action
                log_agent_action(agent.id, "task_complete", result)
                
                return result
                
            except Exception as task_error:
                # Update agent status on failure
                agent.status = "active"
                agent.execution_status = None
                db.commit()
                
                # Log error
                log_agent_action(agent.id, "task_error", {
                    "task_id": task_id,
                    "error": str(task_error)
                })
                
                raise AgentError(f"Task execution failed: {str(task_error)}")
            
        except Exception as e:
            db.rollback()
            raise AgentError(f"Failed to execute task: {str(e)}") 