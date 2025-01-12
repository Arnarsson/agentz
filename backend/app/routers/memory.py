"""Memory management router."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.memory import MemoryService, MemoryEntry
from app.schemas.user import User

router = APIRouter(prefix="/memory", tags=["memory"])

@router.post("/store", response_model=MemoryEntry)
async def store_memory(
    agent_id: str,
    content: Dict[str, Any],
    memory_type: str,
    metadata: Optional[Dict[str, Any]] = None,
    importance: float = Query(default=0.0, ge=0.0, le=1.0),
    context: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Store a new memory entry."""
    try:
        return await MemoryService.store_memory(
            db=db,
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            metadata=metadata,
            importance=importance,
            context=context
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/query", response_model=List[MemoryEntry])
async def query_memories(
    agent_id: str,
    query: str,
    memory_type: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=100),
    min_importance: float = Query(default=0.0, ge=0.0, le=1.0),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Query agent memories based on semantic similarity."""
    try:
        time_range = (start_time, end_time) if start_time and end_time else None
        return await MemoryService.query_memories(
            db=db,
            agent_id=agent_id,
            query=query,
            memory_type=memory_type,
            limit=limit,
            min_importance=min_importance,
            time_range=time_range
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/recent", response_model=List[MemoryEntry])
async def get_recent_memories(
    agent_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    memory_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get most recent memories for an agent."""
    try:
        return await MemoryService.get_recent_memories(
            db=db,
            agent_id=agent_id,
            limit=limit,
            memory_type=memory_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{memory_id}/importance")
async def update_memory_importance(
    memory_id: str,
    importance: float = Query(ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update importance score of a memory."""
    try:
        return await MemoryService.update_memory_importance(
            db=db,
            memory_id=memory_id,
            importance=importance
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{memory_id}")
async def forget_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a memory entry."""
    try:
        success = await MemoryService.forget_memory(db=db, memory_id=memory_id)
        if success:
            return {"message": "Memory forgotten successfully"}
        raise HTTPException(status_code=404, detail="Memory not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/consolidate")
async def consolidate_memories(
    agent_id: str,
    memory_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    consolidation_type: str = Query(
        default="summary",
        description="Type of consolidation to perform: summary, insights, or patterns"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consolidate and summarize memories."""
    try:
        time_range = (start_time, end_time) if start_time and end_time else None
        return await MemoryService.consolidate_memories(
            db=db,
            agent_id=agent_id,
            memory_type=memory_type,
            time_range=time_range,
            consolidation_type=consolidation_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reflect")
async def reflect_on_memories(
    agent_id: str,
    focus_areas: Optional[List[str]] = Query(default=None),
    memory_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate reflective insights from memories."""
    try:
        time_range = (start_time, end_time) if start_time and end_time else None
        return await MemoryService.reflect_on_memories(
            db=db,
            agent_id=agent_id,
            focus_areas=focus_areas,
            memory_type=memory_type,
            time_range=time_range
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats/{agent_id}")
async def get_memory_stats(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get memory usage statistics for an agent."""
    try:
        return await MemoryService.get_memory_stats(db=db, agent_id=agent_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/knowledge/search")
async def search_knowledge_base(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search the knowledge base."""
    try:
        return await MemoryService.search_knowledge_base(
            db=db,
            query=query,
            filters=filters,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/knowledge/add")
async def add_to_knowledge_base(
    content: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    references: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add new information to the knowledge base."""
    try:
        return await MemoryService.add_to_knowledge_base(
            db=db,
            content=content,
            metadata=metadata,
            references=references
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/knowledge/{entry_id}")
async def update_knowledge_base(
    entry_id: str,
    updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update existing knowledge base entry."""
    try:
        return await MemoryService.update_knowledge_base(
            db=db,
            entry_id=entry_id,
            updates=updates
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/context/{agent_id}")
async def get_context_window(
    agent_id: str,
    window_size: int = Query(default=10, ge=1, le=100),
    context_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current context window for an agent."""
    try:
        return await MemoryService.get_context_window(
            db=db,
            agent_id=agent_id,
            window_size=window_size,
            context_type=context_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/context/{agent_id}")
async def update_context(
    agent_id: str,
    context_update: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update agent's current context."""
    try:
        return await MemoryService.update_context(
            db=db,
            agent_id=agent_id,
            context_update=context_update
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 