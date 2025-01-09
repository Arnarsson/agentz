"""
Core agent service implementation with CrewAI integration.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from crewai import Agent as CrewAgent
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentInDB,
    ToolConfig, LLMConfig, ProcessConfig, DelegationConfig
)
from app.core.errors import AgentError, DelegationError
from app.core.logging import log_agent_action
from app.core.websocket import ws_manager
from datetime import datetime
import uuid

class AgentService:
    """Service for managing AI agents with CrewAI integration."""

    @staticmethod
    def _create_crew_agent(agent_data: AgentCreate) -> CrewAgent:
        """Create a CrewAI agent instance with custom configurations."""
        # Convert our tool configs to CrewAI format
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

        # Create CrewAI agent with full configuration
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

            # Create database record with full configuration
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

            # Save to database
            db.add(db_agent)
            db.commit()
            db.refresh(db_agent)

            # Log agent creation
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

            return db_agent

        except Exception as e:
            log_agent_action(
                agent_id=agent_id if 'agent_id' in locals() else "unknown",
                action="create",
                status="error",
                error=str(e)
            )
            raise AgentError(f"Failed to create agent: {str(e)}")

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

            # Update delegation configuration
            agent.delegation_config = delegation_config
            agent.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(agent)

            log_agent_action(
                agent_id=agent_id,
                action="configure_delegation",
                details=delegation_config.dict()
            )

            return agent

        except Exception as e:
            raise DelegationError(f"Failed to configure delegation: {str(e)}")

    @staticmethod
    async def configure_process(
        db: Session,
        agent_id: str,
        process_config: ProcessConfig
    ) -> AgentInDB:
        """Configure agent's process execution settings."""
        try:
            agent = await AgentService.get_agent(db, agent_id)
            if not agent:
                raise AgentError(f"Agent {agent_id} not found")

            # Update process configuration
            agent.process_config = process_config
            agent.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(agent)

            log_agent_action(
                agent_id=agent_id,
                action="configure_process",
                details=process_config.dict()
            )

            return agent

        except Exception as e:
            raise AgentError(f"Failed to configure process: {str(e)}")

    @staticmethod
    async def update_agent_metrics(
        db: Session,
        agent_id: str,
        metrics_update: Dict[str, Any]
    ) -> AgentInDB:
        """Update agent's performance metrics."""
        try:
            agent = await AgentService.get_agent(db, agent_id)
            if not agent:
                raise AgentError(f"Agent {agent_id} not found")

            # Update metrics
            current_metrics = agent.metrics.dict()
            current_metrics.update(metrics_update)
            agent.metrics = current_metrics
            agent.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(agent)

            # Broadcast metrics update via WebSocket
            await ws_manager.broadcast_agent_metrics(
                agent_id=agent_id,
                metrics=agent.metrics
            )

            return agent

        except Exception as e:
            raise AgentError(f"Failed to update metrics: {str(e)}")

    @staticmethod
    async def delegate_task(
        db: Session,
        from_agent_id: str,
        to_agent_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delegate a task from one agent to another."""
        try:
            # Get both agents
            from_agent = await AgentService.get_agent(db, from_agent_id)
            to_agent = await AgentService.get_agent(db, to_agent_id)

            if not from_agent or not to_agent:
                raise DelegationError("One or both agents not found")

            # Validate delegation permissions
            if not from_agent.allow_delegation:
                raise DelegationError("Source agent not allowed to delegate")

            if to_agent_id not in from_agent.delegation_config.allowed_delegates:
                raise DelegationError("Target agent not in allowed delegates list")

            # Create delegation record and execute task
            delegation_id = str(uuid.uuid4())
            result = await AgentService._execute_delegated_task(
                db, delegation_id, from_agent, to_agent, task_data
            )

            return {
                "delegation_id": delegation_id,
                "status": "completed",
                "result": result
            }

        except Exception as e:
            raise DelegationError(f"Delegation failed: {str(e)}")

    @staticmethod
    async def _execute_delegated_task(
        db: Session,
        delegation_id: str,
        from_agent: AgentInDB,
        to_agent: AgentInDB,
        task_data: Dict[str, Any]
    ) -> Any:
        """Execute a delegated task with proper tracking and metrics."""
        start_time = datetime.utcnow()

        try:
            # Create CrewAI agent instance for execution
            crew_agent = AgentService._create_crew_agent(to_agent)

            # Execute task
            result = await crew_agent.execute_task(task_data)

            # Update metrics for both agents
            await AgentService.update_agent_metrics(db, from_agent.id, {
                "delegation_stats": {
                    "delegated_tasks": from_agent.metrics.delegation_stats.get("delegated_tasks", 0) + 1
                }
            })

            await AgentService.update_agent_metrics(db, to_agent.id, {
                "total_tasks": to_agent.metrics.total_tasks + 1,
                "successful_tasks": to_agent.metrics.successful_tasks + 1,
                "average_response_time": (datetime.utcnow() - start_time).total_seconds()
            })

            return result

        except Exception as e:
            # Update error metrics
            await AgentService.update_agent_metrics(db, to_agent.id, {
                "total_tasks": to_agent.metrics.total_tasks + 1,
                "failed_tasks": to_agent.metrics.failed_tasks + 1
            })
            raise 