from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.analytics import analytics_service
from app.core.auth import get_current_user
from app.schemas.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/task-metrics")
async def get_task_metrics(
    agent_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive task metrics summary."""
    return await analytics_service.get_task_metrics_summary(
        db=db,
        agent_id=agent_id,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/task-trends")
async def get_task_trends(
    agent_id: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task execution trends over time."""
    return await analytics_service.get_task_trends(
        db=db,
        agent_id=agent_id,
        days=days
    )

@router.get("/agent-performance/{agent_id}")
async def get_agent_performance(
    agent_id: str,
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed agent performance metrics."""
    return await analytics_service.get_agent_performance(
        db=db,
        agent_id=agent_id,
        days=days
    )

@router.get("/error-insights")
async def get_error_insights(
    days: int = Query(default=30, ge=1, le=90),
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get insights into task errors and failures."""
    return await analytics_service.get_error_insights(
        db=db,
        days=days,
        limit=limit
    ) 