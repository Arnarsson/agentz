"""Agent memory router."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.agent_memory import agent_memory_manager
from app.schemas.user import User

router = APIRouter(prefix="/agent-memory", tags=["agent-memory"])

@router.post("/{agent_id}/task-execution")
async def remember_task_execution(
    agent_id: str,
    task_id: str,
    execution_result: Dict[str, Any],
    success: bool,
    metadata: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Store task execution memory."""
    try:
        return await agent_memory_manager.remember_task_execution(
            db=db,
            agent_id=agent_id,
            task_id=task_id,
            execution_result=execution_result,
            success=success,
            metadata=metadata
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{agent_id}/experience")
async def get_relevant_experience(
    agent_id: str,
    task_description: str,
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get relevant past experiences for a task."""
    try:
        return await agent_memory_manager.get_relevant_experience(
            db=db,
            agent_id=agent_id,
            task_description=task_description,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{agent_id}/learn")
async def learn_from_experience(
    agent_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate learning insights from recent experiences."""
    try:
        time_window = (start_time, end_time) if start_time and end_time else None
        return await agent_memory_manager.learn_from_experience(
            db=db,
            agent_id=agent_id,
            time_window=time_window
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{agent_id}/decision-context")
async def get_decision_context(
    agent_id: str,
    decision_type: str,
    relevant_factors: List[str] = Query(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get memory-based context for decision making."""
    try:
        return await agent_memory_manager.get_decision_context(
            db=db,
            agent_id=agent_id,
            decision_type=decision_type,
            relevant_factors=relevant_factors
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{agent_id}/knowledge")
async def update_agent_knowledge(
    agent_id: str,
    knowledge: Dict[str, Any],
    source: str,
    confidence: float = Query(default=1.0, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update agent's knowledge base."""
    try:
        return await agent_memory_manager.update_agent_knowledge(
            db=db,
            agent_id=agent_id,
            knowledge=knowledge,
            source=source,
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 