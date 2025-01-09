"""
Crew management service for orchestrating agent teams and workflows.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from crewai import Crew, Process
from app.schemas.crew import (
    CrewCreate, CrewUpdate, CrewInDB,
    WorkflowConfig, CrewMetrics
)
from app.services.agent_service import AgentService
from app.core.errors import CrewError, WorkflowError
from app.core.logging import log_crew_action
from app.core.websocket import ws_manager
from datetime import datetime
import uuid

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
                    "last_error": None
                },
                metrics=CrewMetrics(
                    total_tasks=0,
                    successful_tasks=0,
                    failed_tasks=0,
                    average_completion_time=0.0,
                    agent_performance={},
                    last_active=now
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
                
                # Update metrics on success
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                await CrewService.update_crew_metrics(db, crew_id, {
                    "total_tasks": crew.metrics["total_tasks"] + 1,
                    "successful_tasks": crew.metrics["successful_tasks"] + 1,
                    "average_completion_time": (
                        crew.metrics["average_completion_time"] * crew.metrics["total_tasks"] +
                        execution_time
                    ) / (crew.metrics["total_tasks"] + 1)
                })

                # Update final state
                await CrewService.update_crew_state(db, crew_id, {
                    "status": "completed",
                    "progress": 100,
                    "current_task": None
                })

                return {
                    "status": "completed",
                    "result": result,
                    "execution_time": execution_time
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
                        "previous_status": crew.state.get("status"),
                        "new_status": state_update.get("status"),
                        "reason": detailed_status.get("reason") if detailed_status else None
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
        """List all crews with pagination."""
        return db.query(CrewInDB).offset(skip).limit(limit).all()

    @staticmethod
    async def pause_workflow(db: Session, crew_id: str) -> CrewInDB:
        """Pause a running workflow."""
        try:
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            if crew.state["status"] != "executing":
                raise WorkflowError("No active workflow to pause")

            # Update state
            await CrewService.update_crew_state(db, crew_id, {
                "status": "paused",
                "last_error": None
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
                raise WorkflowError("Workflow is not paused")

            # Update state
            await CrewService.update_crew_state(db, crew_id, {
                "status": "executing",
                "last_error": None
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
                raise WorkflowError("No active workflow to stop")

            # Update state
            await CrewService.update_crew_state(db, crew_id, {
                "status": "stopped",
                "current_task": None,
                "progress": 0,
                "last_error": None
            })

            log_crew_action(
                crew_id=crew_id,
                action="workflow_stop",
                details={"final_progress": crew.state.get("progress", 0)}
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

            # Validate template structure
            if "tasks" not in template_data:
                raise WorkflowError("Template must include tasks")

            # Create template record
            template_id = str(uuid.uuid4())
            template = {
                "id": template_id,
                "crew_id": crew_id,
                "name": template_data.get("name", "Unnamed Template"),
                "description": template_data.get("description"),
                "tasks": template_data["tasks"],
                "dependencies": template_data.get("dependencies", {}),
                "config": template_data.get("config", {}),
                "created_at": datetime.utcnow().isoformat()
            }

            # Store template (implementation depends on storage solution)
            # For now, we'll assume templates are stored in the crew's workflow_config
            crew.workflow_config = crew.workflow_config or {}
            templates = crew.workflow_config.get("templates", [])
            templates.append(template)
            crew.workflow_config["templates"] = templates

            # Update crew
            crew.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(crew)

            log_crew_action(
                crew_id=crew_id,
                action="create_template",
                details={
                    "template_id": template_id,
                    "name": template["name"],
                    "task_count": len(template["tasks"])
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
            if update_data:
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
        """Update progress for a specific task in the workflow."""
        try:
            crew = await CrewService.get_crew(db, crew_id)
            if not crew:
                raise CrewError(f"Crew {crew_id} not found")

            # Calculate overall workflow progress
            tasks = crew.workflow_config.get("tasks", [])
            task_weights = {task["id"]: task.get("weight", 1) for task in tasks}
            total_weight = sum(task_weights.values())
            
            # Update task progress
            current_state = crew.state
            task_progress = current_state.get("task_progress", {})
            task_progress[task_id] = progress_data
            
            # Calculate overall progress
            completed_weight = sum(
                task_weights[task_id] * (progress.get("progress", 0) / 100)
                for task_id, progress in task_progress.items()
            )
            overall_progress = int((completed_weight / total_weight) * 100) if total_weight > 0 else 0

            # Update state with detailed progress
            detailed_status = {
                "agent_states": {
                    agent_id: await AgentService.get_agent_status(db, agent_id)
                    for agent_id in crew.agent_ids
                },
                "task_progress": task_progress,
                "resource_usage": await CrewService._get_resource_usage(crew_id),
                "performance_metrics": {
                    "task_completion_rate": len([p for p in task_progress.values() if p.get("status") == "completed"]) / len(tasks) if tasks else 0,
                    "average_task_duration": progress_data.get("duration", 0),
                    "error_rate": len([p for p in task_progress.values() if p.get("status") == "error"]) / len(tasks) if tasks else 0
                },
                "warnings": progress_data.get("warnings", []),
                "next_steps": await CrewService._determine_next_steps(crew, task_progress)
            }

            # Update crew state
            await CrewService.update_crew_state(
                db,
                crew_id,
                {
                    "status": progress_data.get("status", crew.state.get("status")),
                    "current_task": task_id,
                    "progress": overall_progress,
                    "task_progress": task_progress
                },
                detailed_status=detailed_status
            )

            return crew

        except Exception as e:
            raise CrewError(f"Failed to update task progress: {str(e)}")

    @staticmethod
    async def _get_resource_usage(crew_id: str) -> Dict[str, Any]:
        """Get current resource usage for the crew."""
        # Implement resource monitoring logic
        return {
            "memory_usage": 0,  # Implement actual memory tracking
            "cpu_usage": 0,     # Implement actual CPU tracking
            "api_calls": 0,     # Track API usage
            "token_usage": 0    # Track token usage
        }

    @staticmethod
    async def _determine_next_steps(
        crew: CrewInDB,
        task_progress: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Determine next steps based on current progress."""
        next_steps = []
        workflow_config = crew.workflow_config or {}
        tasks = workflow_config.get("tasks", [])
        dependencies = workflow_config.get("dependencies", {})

        for task in tasks:
            task_id = task["id"]
            # Skip completed tasks
            if task_progress.get(task_id, {}).get("status") == "completed":
                continue

            # Check if dependencies are met
            deps = dependencies.get(task_id, [])
            deps_met = all(
                task_progress.get(dep, {}).get("status") == "completed"
                for dep in deps
            )

            if deps_met and task_progress.get(task_id, {}).get("status") != "executing":
                next_steps.append({
                    "task_id": task_id,
                    "task_name": task.get("name", "Unnamed Task"),
                    "priority": task.get("priority", 1),
                    "estimated_duration": task.get("estimated_duration"),
                    "required_agents": task.get("required_agents", [])
                })

        # Sort by priority
        next_steps.sort(key=lambda x: x["priority"], reverse=True)
        return next_steps 