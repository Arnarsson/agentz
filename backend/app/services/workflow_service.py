"""Workflow orchestration service for managing complex agent interactions."""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from crewai import Crew, Process
from app.core.errors import WorkflowError
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowExecutionConfig,
    ProcessType
)
from app.services.agent import AgentService
from app.core.logging import log_workflow_action
from app.core.websocket import ws_manager

class WorkflowService:
    """Service for managing complex agent workflows."""

    @staticmethod
    async def create_workflow(
        db: Session,
        workflow_data: WorkflowCreate,
        owner_id: str
    ) -> Dict[str, Any]:
        """Create a new workflow configuration."""
        try:
            workflow_id = str(uuid.uuid4())
            now = datetime.utcnow()

            # Validate all agents exist and are compatible
            agents = []
            for agent_id in workflow_data.agent_ids:
                agent = await AgentService.get_agent(db, agent_id)
                if not agent:
                    raise WorkflowError(f"Agent {agent_id} not found")
                agents.append(agent)

            # Create workflow record
            workflow = {
                "id": workflow_id,
                "name": workflow_data.name,
                "description": workflow_data.description,
                "process_type": workflow_data.process_type,
                "agent_ids": workflow_data.agent_ids,
                "tasks": workflow_data.tasks,
                "execution_config": workflow_data.execution_config.dict(),
                "owner_id": owner_id,
                "state": {
                    "status": "created",
                    "current_step": None,
                    "progress": 0,
                    "last_error": None
                },
                "metrics": {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "average_execution_time": 0,
                    "last_execution": None
                },
                "created_at": now,
                "updated_at": now
            }

            # Store in database
            # TODO: Implement database storage
            
            # Initialize process orchestrator based on type
            orchestrator = await WorkflowService._create_orchestrator(
                process_type=workflow_data.process_type,
                agents=agents,
                tasks=workflow_data.tasks,
                config=workflow_data.execution_config
            )

            # Store orchestrator configuration
            workflow["orchestrator_config"] = orchestrator.get_config()

            log_workflow_action(
                workflow_id=workflow_id,
                action="create",
                details={
                    "name": workflow_data.name,
                    "process_type": workflow_data.process_type,
                    "agent_count": len(agents)
                }
            )

            return workflow

        except Exception as e:
            raise WorkflowError(f"Failed to create workflow: {str(e)}")

    @staticmethod
    async def _create_orchestrator(
        process_type: ProcessType,
        agents: List[Any],
        tasks: List[Dict[str, Any]],
        config: WorkflowExecutionConfig
    ) -> Any:
        """Create appropriate process orchestrator based on type."""
        try:
            if process_type == ProcessType.SEQUENTIAL:
                return SequentialProcessOrchestrator(
                    agents=agents,
                    tasks=tasks,
                    config=config
                )
            elif process_type == ProcessType.HIERARCHICAL:
                return HierarchicalProcessOrchestrator(
                    agents=agents,
                    tasks=tasks,
                    config=config
                )
            elif process_type == ProcessType.EVENT_DRIVEN:
                return EventDrivenProcessOrchestrator(
                    agents=agents,
                    tasks=tasks,
                    config=config
                )
            elif process_type == ProcessType.CUSTOM:
                return CustomProcessOrchestrator(
                    agents=agents,
                    tasks=tasks,
                    config=config
                )
            else:
                raise ValueError(f"Unsupported process type: {process_type}")

        except Exception as e:
            raise WorkflowError(f"Failed to create process orchestrator: {str(e)}")

    @staticmethod
    async def execute_workflow(
        db: Session,
        workflow_id: str,
        execution_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a workflow with real-time monitoring."""
        try:
            # Get workflow configuration
            workflow = await WorkflowService.get_workflow(db, workflow_id)
            if not workflow:
                raise WorkflowError(f"Workflow {workflow_id} not found")

            # Update workflow state
            workflow["state"]["status"] = "executing"
            workflow["state"]["current_step"] = 0
            workflow["metrics"]["last_execution"] = datetime.utcnow()

            # Broadcast execution start
            await ws_manager.broadcast_to_authenticated(
                message={
                    "type": "workflow_execution_started",
                    "data": {
                        "workflow_id": workflow_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )

            # Create crew instance
            crew = Crew(
                agents=[agent for agent in workflow["agents"]],
                tasks=workflow["tasks"],
                process=Process[workflow["process_type"].upper()]
            )

            # Execute workflow
            start_time = datetime.utcnow()
            try:
                result = await crew.kickoff(
                    inputs=execution_params or {}
                )

                # Update metrics
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                workflow["metrics"].update({
                    "total_executions": workflow["metrics"]["total_executions"] + 1,
                    "successful_executions": workflow["metrics"]["successful_executions"] + 1,
                    "average_execution_time": (
                        (workflow["metrics"]["average_execution_time"] * workflow["metrics"]["total_executions"] + execution_time) /
                        (workflow["metrics"]["total_executions"] + 1)
                    )
                })

                # Update final state
                workflow["state"].update({
                    "status": "completed",
                    "progress": 100,
                    "current_step": None,
                    "last_error": None
                })

                # Broadcast completion
                await ws_manager.broadcast_to_authenticated(
                    message={
                        "type": "workflow_execution_completed",
                        "data": {
                            "workflow_id": workflow_id,
                            "execution_time": execution_time,
                            "result": result
                        }
                    }
                )

                return {
                    "status": "completed",
                    "result": result,
                    "execution_time": execution_time
                }

            except Exception as e:
                # Update error state
                workflow["state"].update({
                    "status": "error",
                    "last_error": str(e)
                })
                workflow["metrics"]["failed_executions"] += 1

                # Broadcast error
                await ws_manager.broadcast_to_authenticated(
                    message={
                        "type": "workflow_execution_failed",
                        "data": {
                            "workflow_id": workflow_id,
                            "error": str(e)
                        }
                    }
                )

                raise WorkflowError(f"Workflow execution failed: {str(e)}")

        except Exception as e:
            raise WorkflowError(f"Failed to execute workflow: {str(e)}")

    @staticmethod
    async def get_workflow(db: Session, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
        # TODO: Implement database retrieval
        pass

    @staticmethod
    async def update_workflow(
        db: Session,
        workflow_id: str,
        update_data: WorkflowUpdate
    ) -> Dict[str, Any]:
        """Update workflow configuration."""
        try:
            workflow = await WorkflowService.get_workflow(db, workflow_id)
            if not workflow:
                raise WorkflowError(f"Workflow {workflow_id} not found")

            # Update fields
            for field, value in update_data.dict(exclude_unset=True).items():
                if field in workflow:
                    workflow[field] = value

            workflow["updated_at"] = datetime.utcnow()

            # TODO: Implement database update

            log_workflow_action(
                workflow_id=workflow_id,
                action="update",
                details=update_data.dict(exclude_unset=True)
            )

            return workflow

        except Exception as e:
            raise WorkflowError(f"Failed to update workflow: {str(e)}")

    @staticmethod
    async def delete_workflow(db: Session, workflow_id: str) -> bool:
        """Delete a workflow."""
        try:
            workflow = await WorkflowService.get_workflow(db, workflow_id)
            if not workflow:
                return False

            # TODO: Implement database deletion

            log_workflow_action(
                workflow_id=workflow_id,
                action="delete",
                details={"workflow_id": workflow_id}
            )

            return True

        except Exception as e:
            raise WorkflowError(f"Failed to delete workflow: {str(e)}")

workflow_service = WorkflowService() 