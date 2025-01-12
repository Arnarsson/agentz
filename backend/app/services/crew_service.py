"""
Crew management service for orchestrating agent teams and workflows.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from crewai import Crew, Process, Agent as CrewAgent, Task
from app.schemas.crew import (
    CrewCreate, CrewUpdate, CrewInDB,
    WorkflowConfig, CrewMetrics
)
from app.services.agent import AgentService
from app.core.errors import CrewError, WorkflowError
from app.core.logging import log_crew_action
from app.core.websocket import ws_manager
from datetime import datetime
import uuid
from langchain_openai import ChatOpenAI

from backend.app.core.config import Settings

class CrewService:
    """Service for managing AI agent crews and workflows."""

    @staticmethod
    async def _create_crew_instance(
        db: Session,
        crew_data: CrewCreate,
        agents: List[Dict[str, Any]]
    ) -> Crew:
        """Create a CrewAI crew instance with configured agents."""
        # Convert process type string to CrewAI Process enum
        process_type = getattr(Process, crew_data.process_type.lower())
        
        # Create CrewAI agent instances
        crew_agents = []
        for agent_data in agents:
            crew_agent = await AgentService._create_crew_agent(agent_data)
            crew_agents.append(crew_agent)

        # Create crew with configuration
        return Crew(
            agents=crew_agents,
            process=process_type,
            verbose=crew_data.verbose,
            max_iterations=crew_data.max_iterations,
            manager_llm_config=crew_data.manager_llm_config.dict() if crew_data.manager_llm_config else None
        )

    @staticmethod
    async def create_crew(
        db: Session,
        crew_data: CrewCreate
    ) -> CrewInDB:
        """Create a new crew with configured agents and workflow."""
        try:
            # Validate and get all agents
            agents = []
            for agent_id in crew_data.agent_ids:
                agent = await AgentService.get_agent(db, agent_id)
                if not agent:
                    raise CrewError(f"Agent {agent_id} not found")
                agents.append(agent)

            # Create CrewAI instance
            crew_instance = await CrewService._create_crew_instance(
                db, crew_data, agents
            )

            # Initialize crew record
            now = datetime.utcnow()
            crew_id = str(uuid.uuid4())

            db_crew = CrewInDB(
                id=crew_id,
                name=crew_data.name,
                description=crew_data.description,
                agent_ids=crew_data.agent_ids,
                process_type=crew_data.process_type,
                workflow_config=crew_data.workflow_config,
                verbose=crew_data.verbose,
                max_iterations=crew_data.max_iterations,
                manager_llm_config=crew_data.manager_llm_config,
                state={
                    "status": "idle",
                    "current_task": None,
                    "progress": 0,
                    "last_error": None,
                    "agent_states": {},
                    "resource_usage": {
                        "memory": 0,
                        "cpu": 0,
                        "tokens": 0
                    }
                },
                metrics=CrewMetrics(
                    total_tasks=0,
                    successful_tasks=0,
                    failed_tasks=0,
                    average_completion_time=0.0,
                    agent_performance={},
                    last_active=now,
                    resource_efficiency=1.0,
                    collaboration_score=0.0,
                    task_distribution={}
                ).dict(),
                created_at=now,
                updated_at=now
            )

            # Save to database
            db.add(db_crew)
            db.commit()
            db.refresh(db_crew)

            # Log crew creation
            log_crew_action(
                crew_id=crew_id,
                action="create",
                details={
                    "name": crew_data.name,
                    "process_type": crew_data.process_type,
                    "agent_count": len(agents)
                }
            )

            # Broadcast crew creation
            await ws_manager.broadcast_crew_update(
                crew_id=crew_id,
                status="created",
                details=db_crew.dict()
            )

            return db_crew

        except Exception as e:
            log_crew_action(
                crew_id=crew_id if 'crew_id' in locals() else "unknown",
                action="create",
                status="error",
                error=str(e)
            )
            raise CrewError(f"Failed to create crew: {str(e)}")

    @staticmethod
    async def execute_workflow(
        db: Session,
        crew_id: str,
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow with the crew."""
        try:
            # Get crew and validate
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            # Get all agents
            agents = []
            for agent_id in crew.agent_ids:
                agent = await AgentService.get_agent(db, agent_id)
                if not agent:
                    raise CrewError(f"Agent {agent_id} not found")
                agents.append(agent)

            # Create CrewAI instance
            crew_instance = await CrewService._create_crew_instance(
                db, crew, agents
            )

            # Update crew state
            await CrewService.update_crew_state(db, crew_id, {
                "status": "executing",
                "current_task": workflow_data.get("task_id"),
                "progress": 0
            })

            # Execute workflow
            start_time = datetime.utcnow()
            try:
                result = await crew_instance.kickoff(inputs=workflow_data)
                
                # Calculate execution metrics
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                resource_usage = await CrewService._get_resource_usage(crew_id)
                
                # Update metrics on success
                metrics_update = {
                    "total_tasks": crew.metrics["total_tasks"] + 1,
                    "successful_tasks": crew.metrics["successful_tasks"] + 1,
                    "average_completion_time": (
                        crew.metrics["average_completion_time"] * crew.metrics["total_tasks"] +
                        execution_time
                    ) / (crew.metrics["total_tasks"] + 1),
                    "resource_efficiency": resource_usage["efficiency"],
                    "collaboration_score": resource_usage["collaboration_score"],
                    "task_distribution": {
                        **crew.metrics.get("task_distribution", {}),
                        workflow_data.get("task_id", "unknown"): {
                            "execution_time": execution_time,
                            "resource_usage": resource_usage
                        }
                    }
                }
                
                await CrewService.update_crew_metrics(db, crew_id, metrics_update)

                # Update final state
                await CrewService.update_crew_state(db, crew_id, {
                    "status": "completed",
                    "progress": 100,
                    "current_task": None,
                    "resource_usage": resource_usage
                })

                return {
                    "status": "completed",
                    "result": result,
                    "execution_time": execution_time,
                    "resource_usage": resource_usage
                }

            except Exception as e:
                # Update metrics on failure
                await CrewService.update_crew_metrics(db, crew_id, {
                    "total_tasks": crew.metrics["total_tasks"] + 1,
                    "failed_tasks": crew.metrics["failed_tasks"] + 1
                })

                # Update error state
                await CrewService.update_crew_state(db, crew_id, {
                    "status": "error",
                    "last_error": str(e),
                    "current_task": None
                })

                raise WorkflowError(f"Workflow execution failed: {str(e)}")

        except Exception as e:
            raise CrewError(f"Failed to execute workflow: {str(e)}")

    @staticmethod
    async def update_crew_state(
        db: Session,
        crew_id: str,
        state_update: Dict[str, Any],
        detailed_status: Optional[Dict[str, Any]] = None
    ) -> CrewInDB:
        """Update crew state and broadcast via WebSocket with detailed status."""
        try:
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            # Update state with detailed information
            current_state = crew.state
            current_state.update(state_update)

            # Add detailed status information if provided
            if detailed_status:
                current_state["detailed_status"] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_states": detailed_status.get("agent_states", {}),
                    "task_progress": detailed_status.get("task_progress", {}),
                    "resource_usage": detailed_status.get("resource_usage", {}),
                    "performance_metrics": detailed_status.get("performance_metrics", {}),
                    "warnings": detailed_status.get("warnings", []),
                    "next_steps": detailed_status.get("next_steps", [])
                }

            crew.state = current_state
            crew.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(crew)

            # Broadcast comprehensive state update
            await ws_manager.broadcast_crew_state(
                crew_id=crew_id,
                state=crew.state
            )

            # Log significant state changes
            if state_update.get("status") != crew.state.get("status"):
                log_crew_action(
                    crew_id=crew_id,
                    action="state_change",
                    details={
                        "old_status": crew.state.get("status"),
                        "new_status": state_update.get("status"),
                        "progress": state_update.get("progress")
                    }
                )

            return crew

        except Exception as e:
            raise CrewError(f"Failed to update crew state: {str(e)}")

    @staticmethod
    async def update_crew_metrics(
        db: Session,
        crew_id: str,
        metrics_update: Dict[str, Any]
    ) -> CrewInDB:
        """Update crew metrics and broadcast via WebSocket."""
        try:
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            # Update metrics
            current_metrics = crew.metrics
            current_metrics.update(metrics_update)
            crew.metrics = current_metrics
            crew.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(crew)

            # Broadcast metrics update
            await ws_manager.broadcast_crew_metrics(
                crew_id=crew_id,
                metrics=crew.metrics
            )

            return crew

        except Exception as e:
            raise CrewError(f"Failed to update crew metrics: {str(e)}")

    @staticmethod
    async def get_crew(db: Session, crew_id: str) -> Optional[CrewInDB]:
        """Get crew by ID."""
        return db.query(CrewInDB).filter(CrewInDB.id == crew_id).first()

    @staticmethod
    async def list_crews(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[CrewInDB]:
        """List all crews."""
        return db.query(CrewInDB).offset(skip).limit(limit).all()

    @staticmethod
    async def pause_workflow(db: Session, crew_id: str) -> CrewInDB:
        """Pause a running workflow."""
        try:
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            if crew.state["status"] != "executing":
                raise WorkflowError("Workflow is not currently executing")

            # Update state
            await CrewService.update_crew_state(db, crew_id, {
                "status": "paused",
                "detailed_status": {
                    "pause_time": datetime.utcnow().isoformat(),
                    "reason": "user_requested"
                }
            })

            log_crew_action(
                crew_id=crew_id,
                action="workflow_pause",
                details={"current_task": crew.state.get("current_task")}
            )

            return crew

        except Exception as e:
            raise CrewError(f"Failed to pause workflow: {str(e)}")

    @staticmethod
    async def resume_workflow(db: Session, crew_id: str) -> CrewInDB:
        """Resume a paused workflow."""
        try:
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            if crew.state["status"] != "paused":
                raise WorkflowError("Workflow is not currently paused")

            # Update state
            await CrewService.update_crew_state(db, crew_id, {
                "status": "executing",
                "detailed_status": {
                    "resume_time": datetime.utcnow().isoformat()
                }
            })

            log_crew_action(
                crew_id=crew_id,
                action="workflow_resume",
                details={"current_task": crew.state.get("current_task")}
            )

            return crew

        except Exception as e:
            raise CrewError(f"Failed to resume workflow: {str(e)}")

    @staticmethod
    async def stop_workflow(db: Session, crew_id: str) -> CrewInDB:
        """Stop a running or paused workflow."""
        try:
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            if crew.state["status"] not in ["executing", "paused"]:
                raise WorkflowError("Workflow is not currently active")

            # Update state
            await CrewService.update_crew_state(db, crew_id, {
                "status": "stopped",
                "current_task": None,
                "detailed_status": {
                    "stop_time": datetime.utcnow().isoformat(),
                    "reason": "user_requested"
                }
            })

            log_crew_action(
                crew_id=crew_id,
                action="workflow_stop",
                details={
                    "final_progress": crew.state.get("progress"),
                    "last_task": crew.state.get("current_task")
                }
            )

            return crew

        except Exception as e:
            raise CrewError(f"Failed to stop workflow: {str(e)}")

    @staticmethod
    async def create_workflow_template(
        db: Session,
        crew_id: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a reusable workflow template."""
        try:
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            # Validate template data
            required_fields = ["name", "description", "steps", "inputs"]
            missing_fields = [
                field for field in required_fields
                if field not in template_data
            ]
            if missing_fields:
                raise CrewError(
                    f"Missing required template fields: {', '.join(missing_fields)}"
                )

            # Create template
            template_id = str(uuid.uuid4())
            template = {
                "id": template_id,
                "crew_id": crew_id,
                "name": template_data["name"],
                "description": template_data["description"],
                "steps": template_data["steps"],
                "inputs": template_data["inputs"],
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }

            # Store template (implementation depends on storage solution)
            # For now, we'll assume it's stored in the crew's workflow_config
            crew.workflow_config["templates"] = crew.workflow_config.get("templates", [])
            crew.workflow_config["templates"].append(template)
            crew.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(crew)

            log_crew_action(
                crew_id=crew_id,
                action="create_template",
                details={
                    "template_id": template_id,
                    "name": template_data["name"]
                }
            )

            return template

        except Exception as e:
            raise CrewError(f"Failed to create workflow template: {str(e)}")

    @staticmethod
    async def update_crew(
        db: Session,
        crew_id: str,
        crew_data: CrewUpdate
    ) -> CrewInDB:
        """Update crew configuration."""
        try:
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            # Update fields
            update_data = crew_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(crew, field, value)

            crew.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(crew)

            log_crew_action(
                crew_id=crew_id,
                action="update",
                details={"updated_fields": list(update_data.keys())}
            )

            return crew

        except Exception as e:
            raise CrewError(f"Failed to update crew: {str(e)}")

    @staticmethod
    async def update_task_progress(
        db: Session,
        crew_id: str,
        task_id: str,
        progress_data: Dict[str, Any]
    ) -> CrewInDB:
        """Update task progress and crew state."""
        try:
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            # Calculate overall progress
            current_progress = progress_data.get("progress", 0)
            resource_usage = await CrewService._get_resource_usage(crew_id)
            next_steps = await CrewService._determine_next_steps(crew, progress_data)

            # Update state with comprehensive information
            state_update = {
                "progress": current_progress,
                "current_task": task_id,
                "resource_usage": resource_usage,
                "detailed_status": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "task_progress": progress_data,
                    "resource_usage": resource_usage,
                    "next_steps": next_steps,
                    "warnings": progress_data.get("warnings", [])
                }
            }

            # Update crew state
            await CrewService.update_crew_state(db, crew_id, state_update)

            # Update metrics if task completed
            if current_progress == 100:
                metrics_update = {
                    "task_distribution": {
                        **crew.metrics.get("task_distribution", {}),
                        task_id: {
                            "completion_time": datetime.utcnow().isoformat(),
                            "resource_usage": resource_usage
                        }
                    }
                }
                await CrewService.update_crew_metrics(db, crew_id, metrics_update)

            return crew

        except Exception as e:
            raise CrewError(f"Failed to update task progress: {str(e)}")

    @staticmethod
    async def _get_resource_usage(crew_id: str) -> Dict[str, Any]:
        """Get current resource usage metrics."""
        # Implementation depends on monitoring setup
        return {
            "memory": 0,  # Placeholder
            "cpu": 0,     # Placeholder
            "tokens": 0,  # Placeholder
            "efficiency": 1.0,
            "collaboration_score": 0.8
        }

    @staticmethod
    async def _determine_next_steps(
        crew: CrewInDB,
        task_progress: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Determine next steps based on current progress."""
        # Implementation depends on workflow logic
        return [
            {
                "step": "next_task",
                "description": "Continue with workflow execution",
                "estimated_time": "unknown"
            }
        ]

    """CrewAI integration service."""

    @staticmethod
    def create_agent(
        name: str,
        role: str,
        goal: str,
        backstory: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        allow_delegation: bool = True,
        verbose: bool = True,
        memory: bool = True
    ) -> CrewAgent:
        """Create a CrewAI agent with specified configuration."""
        try:
            # Configure agent with GPT-4 for complex reasoning
            agent = CrewAgent(
                role=role,
                goal=goal,
                backstory=backstory or f"You are {name}, an expert {role} focused on {goal}",
                verbose=verbose,
                allow_delegation=allow_delegation,
                tools=tools or [],
                memory=memory,
                llm=ChatOpenAI(
                    model="gpt-4-turbo-preview",
                    temperature=0.7,
                    api_key=Settings.OPENAI_API_KEY
                )
            )
            logger.info(f"Created agent: {name} ({role})")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}")
            raise

    @staticmethod
    def create_task(
        description: str,
        agent: CrewAgent,
        context: Optional[Dict[str, Any]] = None,
        expected_output: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        async_execution: bool = False,
        output_file: Optional[str] = None
    ) -> Task:
        """Create a CrewAI task with specified configuration."""
        try:
            task = Task(
                description=description,
                agent=agent,
                context=context or {},
                expected_output=expected_output,
                tools=tools or [],
                async_execution=async_execution,
                output_file=output_file
            )
            logger.info(f"Created task for agent: {agent.role}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            raise

    @staticmethod
    def create_crew(
        agents: List[CrewAgent],
        tasks: List[Task],
        process: Process = Process.sequential,
        verbose: bool = True,
        max_iterations: int = 1
    ) -> Crew:
        """Create a CrewAI crew with specified configuration."""
        try:
            crew = Crew(
                agents=agents,
                tasks=tasks,
                process=process,
                verbose=verbose,
                max_iterations=max_iterations
            )
            logger.info(f"Created crew with {len(agents)} agents and {len(tasks)} tasks")
            return crew
            
        except Exception as e:
            logger.error(f"Failed to create crew: {str(e)}")
            raise

    @staticmethod
    async def execute_workflow(
        agents: List[CrewAgent],
        tasks: List[Task],
        process: Process = Process.sequential,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Execute a workflow with the specified agents and tasks."""
        try:
            # Create and configure the crew
            crew = Crew(
                agents=agents,
                tasks=tasks,
                process=process,
                verbose=verbose
            )
            
            # Execute the workflow
            logger.info("Starting workflow execution")
            results = crew.kickoff()
            logger.info("Workflow execution completed")
            
            return {
                "status": "completed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            raise 