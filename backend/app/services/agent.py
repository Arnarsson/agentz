"""
Comprehensive agent service module with CrewAI integration.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from crewai import Agent as CrewAgent
from app.models.agent import Agent
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentInDB,
    ToolConfig, LLMConfig, ProcessConfig, DelegationConfig
)
from app.core.errors import (
    AgentError, AgentNotFoundError, AgentBusyError,
    DelegationError
)
from app.core.logging import log_agent_action
from app.core.websocket import ws_manager
from app.core.config import settings
from app.services.agent_memory import agent_memory_manager
from datetime import datetime
import uuid

class AgentService:
    """Comprehensive service for managing AI agents with CrewAI integration."""

    @staticmethod
    def _create_crew_agent(agent_data: AgentCreate) -> CrewAgent:
        """Create a CrewAI agent instance with custom configurations."""
        # Convert tool configs to CrewAI format
        tools = []
        for tool in agent_data.tools:
            if tool.enabled:
                tool_config = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
                if tool.api_config:
                    tool_config.update(tool.api_config)
                if tool.custom_logic:
                    tool_config.update(tool.custom_logic)
                tools.append(tool_config)

        # Configure LLM settings
        llm_config = {}
        if agent_data.llm_config:
            llm_config = {
                "model": agent_data.llm_config.model,
                "temperature": agent_data.llm_config.temperature,
                "max_tokens": agent_data.llm_config.max_tokens,
                "top_p": agent_data.llm_config.top_p,
                "streaming": agent_data.llm_config.streaming
            }
            if agent_data.llm_config.custom_prompts:
                llm_config["custom_prompts"] = agent_data.llm_config.custom_prompts.dict()

        # Create CrewAI agent
        return CrewAgent(
            role=agent_data.role,
            goal=agent_data.goal,
            backstory=agent_data.backstory,
            allow_delegation=agent_data.allow_delegation,
            verbose=agent_data.verbose,
            tools=tools,
            llm_config=llm_config,
            max_iterations=agent_data.max_iterations,
            memory=agent_data.memory
        )

    @staticmethod
    async def create_agent(db: Session, agent_data: AgentCreate) -> AgentInDB:
        """Create a new agent with full configuration."""
        try:
            # Create CrewAI agent instance
            crew_agent = AgentService._create_crew_agent(agent_data)

            # Initialize agent state and metrics
            now = datetime.utcnow()
            agent_id = str(uuid.uuid4())

            # Create database record
            db_agent = AgentInDB(
                id=agent_id,
                role=agent_data.role,
                goal=agent_data.goal,
                backstory=agent_data.backstory,
                allow_delegation=agent_data.allow_delegation,
                verbose=agent_data.verbose,
                tools=agent_data.tools,
                llm_config=agent_data.llm_config,
                max_iterations=agent_data.max_iterations,
                memory=agent_data.memory,
                owner_id=agent_data.owner_id or "system",
                state={
                    "status": "idle",
                    "health": "healthy",
                    "current_task_id": None,
                    "last_error": None,
                    "current_memory_usage": 0,
                    "execution_stats": {}
                },
                metrics={
                    "total_tasks": 0,
                    "successful_tasks": 0,
                    "failed_tasks": 0,
                    "average_response_time": 0.0,
                    "total_tokens_used": 0,
                    "delegation_stats": {},
                    "last_active": now
                },
                delegation_config=agent_data.delegation_config,
                process_config=agent_data.process_config,
                custom_prompts=agent_data.custom_prompts,
                created_at=now,
                updated_at=now
            )

            db.add(db_agent)
            db.commit()
            db.refresh(db_agent)

            # Initialize agent's memory
            await agent_memory_manager.initialize_agent_memory(
                db=db,
                agent_id=agent_id,
                initial_knowledge={
                    "role": agent_data.role,
                    "goal": agent_data.goal,
                    "backstory": agent_data.backstory,
                    "capabilities": [tool.name for tool in agent_data.tools if tool.enabled],
                    "config": agent_data.llm_config.dict() if agent_data.llm_config else {}
                }
            )

            log_agent_action(
                agent_id=agent_id,
                action="create",
                details={
                    "role": agent_data.role,
                    "goal": agent_data.goal,
                    "tools_count": len(agent_data.tools),
                    "allow_delegation": agent_data.allow_delegation
                }
            )

            # Notify connected clients about new agent
            await ws_manager.broadcast_to_authenticated(
                message={
                    "type": "agent_created",
                    "data": {
                        "agent_id": agent_id,
                        "role": agent_data.role,
                        "status": "idle"
                    }
                }
            )

            return db_agent

        except Exception as e:
            db.rollback()
            log_agent_action(
                agent_id=agent_id if 'agent_id' in locals() else "unknown",
                action="create",
                status="error",
                error=str(e)
            )
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

            # Update basic fields
            for field, value in agent_data.dict(exclude_unset=True).items():
                setattr(agent, field, value)

            agent.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(agent)

            # Update agent's memory if relevant fields changed
            memory_fields = ["role", "goal", "backstory", "tools"]
            if any(field in agent_data.dict(exclude_unset=True) for field in memory_fields):
                await agent_memory_manager.update_agent_knowledge(
                    db=db,
                    agent_id=agent_id,
                    knowledge={
                        "role": agent.role,
                        "goal": agent.goal,
                        "backstory": agent.backstory,
                        "capabilities": [tool.name for tool in agent.tools if tool.enabled],
                    },
                    source="agent_update"
                )

            log_agent_action(agent.id, "update", agent_data.dict(exclude_unset=True))

            # Notify connected clients about agent update
            await ws_manager.broadcast_to_authenticated(
                message={
                    "type": "agent_updated",
                    "data": {
                        "agent_id": agent_id,
                        "role": agent.role,
                        "status": agent.state.get("status", "idle")
                    }
                }
            )

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

            # Delete agent's memory first
            await agent_memory_manager.delete_agent_memory(db=db, agent_id=agent_id)

            # Delete the agent
            db.delete(agent)
            db.commit()

            log_agent_action(agent_id, "delete", {"agent_id": agent_id})

            # Notify connected clients about agent deletion
            await ws_manager.broadcast_to_authenticated(
                message={
                    "type": "agent_deleted",
                    "data": {
                        "agent_id": agent_id
                    }
                }
            )

            return True

        except Exception as e:
            db.rollback()
            raise AgentError(f"Failed to delete agent: {str(e)}")

    @staticmethod
    async def configure_delegation(
        db: Session,
        agent_id: str,
        delegation_config: DelegationConfig
    ) -> AgentInDB:
        """Configure agent's delegation capabilities."""
        try:
            agent = await AgentService.get_agent(db, agent_id)
            if not agent:
                raise AgentError(f"Agent {agent_id} not found")

            agent.delegation_config = delegation_config
            agent.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(agent)

            # Update agent's memory with new delegation capabilities
            await agent_memory_manager.update_agent_knowledge(
                db=db,
                agent_id=agent_id,
                knowledge={
                    "delegation_capabilities": delegation_config.dict(),
                    "updated_at": datetime.utcnow().isoformat()
                },
                source="delegation_update"
            )

            log_agent_action(
                agent_id=agent_id,
                action="configure_delegation",
                details=delegation_config.dict()
            )

            return agent

        except Exception as e:
            db.rollback()
            raise DelegationError(f"Failed to configure delegation: {str(e)}")

agent_service = AgentService() 