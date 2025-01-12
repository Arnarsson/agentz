"""Workflow API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowInDB
from app.services.idea_workflow import IdeaWorkflowService
from app.services.business_planning_workflow import BusinessPlanningWorkflowService

router = APIRouter()

# Idea Workflow Endpoints
@router.post("/idea", response_model=WorkflowInDB)
async def create_idea_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_async_db)
) -> WorkflowInDB:
    """Create a new idea creation workflow."""
    try:
        workflow = await IdeaWorkflowService.create_workflow(db, workflow_data)
        return workflow
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/idea", response_model=List[WorkflowInDB])
async def list_idea_workflows(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
) -> List[WorkflowInDB]:
    """List all idea creation workflows."""
    try:
        workflows = await IdeaWorkflowService.list_workflows(db, skip, limit)
        return workflows
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/idea/{workflow_id}", response_model=WorkflowInDB)
async def get_idea_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> WorkflowInDB:
    """Get a specific idea creation workflow."""
    workflow = await IdeaWorkflowService.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.patch("/idea/{workflow_id}", response_model=WorkflowInDB)
async def update_idea_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_async_db)
) -> WorkflowInDB:
    """Update a specific idea creation workflow."""
    try:
        workflow = await IdeaWorkflowService.update_workflow(db, workflow_id, workflow_data)
        return workflow
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/idea/{workflow_id}/execute")
async def execute_idea_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Execute a specific idea creation workflow."""
    try:
        results = await IdeaWorkflowService.execute_workflow(db, workflow_id)
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Business Planning Workflow Endpoints
@router.post("/business-planning", response_model=WorkflowInDB)
async def create_business_planning_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_async_db)
) -> WorkflowInDB:
    """Create a new business planning workflow."""
    try:
        workflow = await BusinessPlanningWorkflowService.create_workflow(db, workflow_data)
        return workflow
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/business-planning", response_model=List[WorkflowInDB])
async def list_business_planning_workflows(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
) -> List[WorkflowInDB]:
    """List all business planning workflows."""
    try:
        workflows = await BusinessPlanningWorkflowService.list_workflows(db, skip, limit)
        return workflows
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/business-planning/{workflow_id}", response_model=WorkflowInDB)
async def get_business_planning_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> WorkflowInDB:
    """Get a specific business planning workflow."""
    workflow = await BusinessPlanningWorkflowService.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.patch("/business-planning/{workflow_id}", response_model=WorkflowInDB)
async def update_business_planning_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_async_db)
) -> WorkflowInDB:
    """Update a specific business planning workflow."""
    try:
        workflow = await BusinessPlanningWorkflowService.update_workflow(db, workflow_id, workflow_data)
        return workflow
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/business-planning/{workflow_id}/execute")
async def execute_business_planning_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Execute a specific business planning workflow."""
    try:
        results = await BusinessPlanningWorkflowService.execute_workflow(db, workflow_id)
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 