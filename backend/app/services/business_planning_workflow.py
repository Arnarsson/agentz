"""Business planning workflow service."""
import uuid
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate

class BusinessPlanningWorkflowService:
    """Business planning workflow service."""

    @staticmethod
    async def create_workflow(db: AsyncSession, workflow_data: WorkflowCreate) -> Workflow:
        """Create a new business planning workflow."""
        workflow = Workflow(
            id=str(uuid.uuid4()),
            title=workflow_data.title,
            description=workflow_data.description,
            type="business-planning",
            status="pending",
            error=None,
            memory="{}",
            tools="[]",
            llm_config="{}",
            start_time=None,
            end_time=None,
            execution_time=None,
            execution_status=None
        )
        db.add(workflow)
        await db.commit()
        await db.refresh(workflow)
        return workflow

    @staticmethod
    async def list_workflows(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Workflow]:
        """List all business planning workflows."""
        query = select(Workflow).filter(Workflow.type == "business-planning").offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_workflow(db: AsyncSession, workflow_id: str, load_agents: bool = False) -> Workflow:
        """Get a specific business planning workflow."""
        query = select(Workflow).filter(Workflow.id == workflow_id)
        if load_agents:
            query = query.options(selectinload(Workflow.agents))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_workflow(db: AsyncSession, workflow_id: str, workflow_data: WorkflowUpdate) -> Workflow:
        """Update a specific business planning workflow."""
        workflow = await BusinessPlanningWorkflowService.get_workflow(db, workflow_id)
        if not workflow:
            return None

        for field, value in workflow_data.dict(exclude_unset=True).items():
            setattr(workflow, field, value)

        await db.commit()
        await db.refresh(workflow)
        return workflow

    @staticmethod
    async def execute_workflow(db: AsyncSession, workflow_id: str) -> dict:
        """Execute a specific business planning workflow."""
        workflow = await BusinessPlanningWorkflowService.get_workflow(db, workflow_id, load_agents=True)
        if not workflow:
            return None

        workflow.status = "running"
        workflow.start_time = datetime.datetime.utcnow().isoformat()
        await db.commit()

        try:
            # Execute workflow logic here
            workflow.status = "completed"
            workflow.end_time = datetime.datetime.utcnow().isoformat()
            workflow.execution_time = str((datetime.datetime.fromisoformat(workflow.end_time) - 
                                        datetime.datetime.fromisoformat(workflow.start_time)).total_seconds())
            workflow.execution_status = "success"
            await db.commit()
            return {"status": "success", "message": "Workflow executed successfully"}
        except Exception as e:
            workflow.status = "failed"
            workflow.error = str(e)
            workflow.end_time = datetime.datetime.utcnow().isoformat()
            workflow.execution_time = str((datetime.datetime.fromisoformat(workflow.end_time) - 
                                        datetime.datetime.fromisoformat(workflow.start_time)).total_seconds())
            workflow.execution_status = "failed"
            await db.commit()
            raise 