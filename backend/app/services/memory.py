"""Memory service for managing agent memory and knowledge base."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
import json
import uuid
from app.core.errors import MemoryError
from app.models.memory import Memory
from app.services.embeddings import embeddings_service
from app.services.consolidation import consolidation_service

class MemoryEntry(BaseModel):
    """Schema for a memory entry."""
    id: str
    agent_id: str
    content: Dict[str, Any]
    type: str  # conversation, task_result, observation, knowledge
    timestamp: datetime
    metadata: Dict[str, Any]
    importance: float = 0.0
    context: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
    references: Optional[List[str]] = None

class MemoryService:
    """Service for managing agent memory and knowledge base."""

    @staticmethod
    async def store_memory(
        db: AsyncSession,
        agent_id: str,
        content: Dict[str, Any],
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.0,
        context: Optional[Dict[str, Any]] = None
    ) -> MemoryEntry:
        """Store a new memory entry."""
        try:
            memory_id = str(uuid.uuid4())
            
            # Generate text representation for embedding
            text_content = json.dumps(content)
            
            # Generate embedding
            embedding = await embeddings_service.generate_embedding(text_content)
            
            # Create memory entry
            memory = Memory(
                id=memory_id,
                agent_id=agent_id,
                content=content,
                type=memory_type,
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
                importance=importance,
                context=context,
                embedding=embedding,
                references=[]
            )
            
            # Store in database
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            
            # Store in vector database
            await embeddings_service.add_memory_embedding(
                memory_id=memory_id,
                text=text_content,
                metadata={
                    "agent_id": agent_id,
                    "type": memory_type,
                    "importance": importance,
                    **(metadata or {})
                }
            )
            
            return MemoryEntry(
                id=memory.id,
                agent_id=memory.agent_id,
                content=memory.content,
                type=memory.type,
                timestamp=memory.timestamp,
                metadata=memory.metadata,
                importance=memory.importance,
                context=memory.context,
                embedding=memory.embedding,
                references=memory.references
            )
        except Exception as e:
            await db.rollback()
            raise MemoryError(f"Failed to store memory: {str(e)}")

    @staticmethod
    async def query_memories(
        db: AsyncSession,
        agent_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_importance: float = 0.0,
        time_range: Optional[tuple[datetime, datetime]] = None
    ) -> List[MemoryEntry]:
        """Query agent memories based on semantic similarity."""
        try:
            # Query vector database
            similar_memories = await embeddings_service.query_similar_memories(
                query=query,
                agent_id=agent_id,
                memory_type=memory_type,
                limit=limit,
                min_importance=min_importance
            )
            
            # Get memory IDs from similar results
            memory_ids = [m["id"] for m in similar_memories]
            
            # Query database for full memory entries
            query = select(Memory).filter(Memory.id.in_(memory_ids))
            
            if time_range:
                query = query.filter(and_(
                    Memory.timestamp >= time_range[0],
                    Memory.timestamp <= time_range[1]
                ))
            
            result = await db.execute(query)
            memories = result.scalars().all()
            
            # Sort memories to match similarity order
            sorted_memories = sorted(
                memories,
                key=lambda x: memory_ids.index(x.id)
            )
            
            return [
                MemoryEntry(
                    id=memory.id,
                    agent_id=memory.agent_id,
                    content=memory.content,
                    type=memory.type,
                    timestamp=memory.timestamp,
                    metadata=memory.metadata,
                    importance=memory.importance,
                    context=memory.context,
                    embedding=memory.embedding,
                    references=memory.references
                )
                for memory in sorted_memories
            ]
        except Exception as e:
            raise MemoryError(f"Failed to query memories: {str(e)}")

    @staticmethod
    async def get_recent_memories(
        db: AsyncSession,
        agent_id: str,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[MemoryEntry]:
        """Get most recent memories for an agent."""
        try:
            query = select(Memory).filter(Memory.agent_id == agent_id)
            
            if memory_type:
                query = query.filter(Memory.type == memory_type)
            
            query = query.order_by(desc(Memory.timestamp)).limit(limit)
            
            result = await db.execute(query)
            memories = result.scalars().all()
            
            return [
                MemoryEntry(
                    id=memory.id,
                    agent_id=memory.agent_id,
                    content=memory.content,
                    type=memory.type,
                    timestamp=memory.timestamp,
                    metadata=memory.metadata,
                    importance=memory.importance,
                    context=memory.context,
                    embedding=memory.embedding,
                    references=memory.references
                )
                for memory in memories
            ]
        except Exception as e:
            raise MemoryError(f"Failed to get recent memories: {str(e)}")

    @staticmethod
    async def update_memory_importance(
        db: AsyncSession,
        memory_id: str,
        importance: float
    ) -> MemoryEntry:
        """Update importance score of a memory."""
        try:
            # Update in database
            result = await db.execute(
                select(Memory).filter(Memory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                raise MemoryError(f"Memory {memory_id} not found")
            
            memory.importance = importance
            memory.metadata = {
                **memory.metadata,
                "importance_updated_at": datetime.utcnow().isoformat()
            }
            
            await db.commit()
            await db.refresh(memory)
            
            # Update in vector database
            text_content = json.dumps(memory.content)
            await embeddings_service.update_memory_embedding(
                memory_id=memory_id,
                text=text_content,
                metadata={
                    "agent_id": memory.agent_id,
                    "type": memory.type,
                    "importance": importance,
                    **memory.metadata
                }
            )
            
            return MemoryEntry(
                id=memory.id,
                agent_id=memory.agent_id,
                content=memory.content,
                type=memory.type,
                timestamp=memory.timestamp,
                metadata=memory.metadata,
                importance=memory.importance,
                context=memory.context,
                embedding=memory.embedding,
                references=memory.references
            )
        except Exception as e:
            await db.rollback()
            raise MemoryError(f"Failed to update memory importance: {str(e)}")

    @staticmethod
    async def forget_memory(
        db: AsyncSession,
        memory_id: str
    ) -> bool:
        """Remove a memory entry."""
        try:
            result = await db.execute(
                select(Memory).filter(Memory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return False
            
            # Delete from database
            await db.delete(memory)
            await db.commit()
            
            # Delete from vector database
            await embeddings_service.delete_memory_embedding(memory_id)
            
            return True
        except Exception as e:
            await db.rollback()
            raise MemoryError(f"Failed to forget memory: {str(e)}")

    @staticmethod
    async def consolidate_memories(
        db: AsyncSession,
        agent_id: str,
        memory_type: Optional[str] = None,
        time_range: Optional[tuple[datetime, datetime]] = None,
        consolidation_type: str = "summary"
    ) -> Dict[str, Any]:
        """Consolidate and summarize memories."""
        try:
            # Get memories to consolidate
            query = select(Memory).filter(Memory.agent_id == agent_id)
            
            if memory_type:
                query = query.filter(Memory.type == memory_type)
            
            if time_range:
                query = query.filter(and_(
                    Memory.timestamp >= time_range[0],
                    Memory.timestamp <= time_range[1]
                ))
            
            result = await db.execute(query)
            memories = result.scalars().all()
            
            if not memories:
                return {
                    "summary": "No memories to consolidate",
                    "key_points": [],
                    "consolidated_at": datetime.utcnow()
                }
            
            # Use consolidation service
            consolidation = await consolidation_service.consolidate_memories(
                memories=memories,
                consolidation_type=consolidation_type
            )
            
            # Store consolidation as a new memory
            await MemoryService.store_memory(
                db=db,
                agent_id=agent_id,
                content=consolidation,
                memory_type="consolidation",
                metadata={
                    "consolidation_type": consolidation_type,
                    "original_memory_count": len(memories),
                    "time_range": [
                        time_range[0].isoformat() if time_range else None,
                        time_range[1].isoformat() if time_range else None
                    ],
                    "memory_type_filter": memory_type
                },
                importance=0.8  # Consolidations are important for long-term memory
            )
            
            return consolidation

        except Exception as e:
            raise MemoryError(f"Failed to consolidate memories: {str(e)}")

    @staticmethod
    async def reflect_on_memories(
        db: AsyncSession,
        agent_id: str,
        focus_areas: Optional[List[str]] = None,
        memory_type: Optional[str] = None,
        time_range: Optional[tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Generate reflective insights from memories."""
        try:
            # Get memories to reflect upon
            query = select(Memory).filter(Memory.agent_id == agent_id)
            
            if memory_type:
                query = query.filter(Memory.type == memory_type)
            
            if time_range:
                query = query.filter(and_(
                    Memory.timestamp >= time_range[0],
                    Memory.timestamp <= time_range[1]
                ))
            
            result = await db.execute(query)
            memories = result.scalars().all()
            
            if not memories:
                return {
                    "reflection": "No memories to reflect upon",
                    "insights": [],
                    "generated_at": datetime.utcnow()
                }
            
            # Use consolidation service for reflection
            reflection = await consolidation_service.generate_reflection(
                memories=memories,
                focus_areas=focus_areas
            )
            
            # Store reflection as a new memory
            await MemoryService.store_memory(
                db=db,
                agent_id=agent_id,
                content=reflection,
                memory_type="reflection",
                metadata={
                    "focus_areas": focus_areas,
                    "memory_count": len(memories),
                    "time_range": [
                        time_range[0].isoformat() if time_range else None,
                        time_range[1].isoformat() if time_range else None
                    ],
                    "memory_type_filter": memory_type
                },
                importance=0.9  # Reflections are very important for learning
            )
            
            return reflection

        except Exception as e:
            raise MemoryError(f"Failed to generate reflection: {str(e)}")

    @staticmethod
    async def get_memory_stats(
        db: AsyncSession,
        agent_id: str
    ) -> Dict[str, Any]:
        """Get memory usage statistics for an agent."""
        try:
            # Get all memories for the agent
            result = await db.execute(
                select(Memory).filter(Memory.agent_id == agent_id)
            )
            memories = result.scalars().all()
            
            # Calculate statistics
            memory_types = {}
            importance_distribution = {
                "low": 0,    # 0.0-0.3
                "medium": 0, # 0.3-0.7
                "high": 0    # 0.7-1.0
            }
            temporal_distribution = {}
            
            for memory in memories:
                # Memory types
                memory_types[memory.type] = memory_types.get(memory.type, 0) + 1
                
                # Importance distribution
                if memory.importance < 0.3:
                    importance_distribution["low"] += 1
                elif memory.importance < 0.7:
                    importance_distribution["medium"] += 1
                else:
                    importance_distribution["high"] += 1
                
                # Temporal distribution (by day)
                day = memory.timestamp.date().isoformat()
                temporal_distribution[day] = temporal_distribution.get(day, 0) + 1
            
            return {
                "total_memories": len(memories),
                "memory_types": memory_types,
                "importance_distribution": importance_distribution,
                "temporal_distribution": temporal_distribution,
                "storage_usage": sum(
                    len(json.dumps(m.content)) for m in memories
                )
            }
        except Exception as e:
            raise MemoryError(f"Failed to get memory stats: {str(e)}")

    @staticmethod
    async def search_knowledge_base(
        db: AsyncSession,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search the knowledge base."""
        try:
            return await embeddings_service.query_knowledge_base(
                query=query,
                filters=filters,
                limit=limit
            )
        except Exception as e:
            raise MemoryError(f"Failed to search knowledge base: {str(e)}")

    @staticmethod
    async def add_to_knowledge_base(
        db: AsyncSession,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        references: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add new information to the knowledge base."""
        try:
            entry_id = str(uuid.uuid4())
            
            # Generate text representation for embedding
            text_content = json.dumps(content)
            
            # Store in vector database
            await embeddings_service.add_knowledge_embedding(
                entry_id=entry_id,
                text=text_content,
                metadata=metadata or {}
            )
            
            # Store in regular database as a memory
            memory = Memory(
                id=entry_id,
                agent_id=None,  # Knowledge base entries don't belong to specific agents
                content=content,
                type="knowledge",
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
                importance=1.0,  # Knowledge base entries are always important
                context=None,
                embedding=await embeddings_service.generate_embedding(text_content),
                references=references
            )
            
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            
            return {
                "id": entry_id,
                "content": content,
                "metadata": metadata,
                "references": references,
                "added_at": memory.timestamp
            }
        except Exception as e:
            await db.rollback()
            raise MemoryError(f"Failed to add to knowledge base: {str(e)}")

    @staticmethod
    async def update_knowledge_base(
        db: AsyncSession,
        entry_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing knowledge base entry."""
        try:
            result = await db.execute(
                select(Memory).filter(
                    and_(Memory.id == entry_id, Memory.type == "knowledge")
                )
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                raise MemoryError(f"Knowledge base entry {entry_id} not found")
            
            # Update content
            memory.content.update(updates)
            memory.metadata["updated_at"] = datetime.utcnow().isoformat()
            
            await db.commit()
            await db.refresh(memory)
            
            # Update in vector database
            text_content = json.dumps(memory.content)
            await embeddings_service.update_knowledge_embedding(
                entry_id=entry_id,
                text=text_content,
                metadata=memory.metadata
            )
            
            return {
                "id": entry_id,
                "updated_at": datetime.utcnow(),
                "changes": updates
            }
        except Exception as e:
            await db.rollback()
            raise MemoryError(f"Failed to update knowledge base: {str(e)}")

    @staticmethod
    async def get_context_window(
        db: AsyncSession,
        agent_id: str,
        window_size: int = 10,
        context_type: Optional[str] = None
    ) -> List[MemoryEntry]:
        """Get the current context window for an agent."""
        try:
            query = select(Memory).filter(Memory.agent_id == agent_id)
            
            if context_type:
                query = query.filter(Memory.type == context_type)
            
            query = query.order_by(desc(Memory.timestamp)).limit(window_size)
            
            result = await db.execute(query)
            memories = result.scalars().all()
            
            return [
                MemoryEntry(
                    id=memory.id,
                    agent_id=memory.agent_id,
                    content=memory.content,
                    type=memory.type,
                    timestamp=memory.timestamp,
                    metadata=memory.metadata,
                    importance=memory.importance,
                    context=memory.context,
                    embedding=memory.embedding,
                    references=memory.references
                )
                for memory in memories
            ]
        except Exception as e:
            raise MemoryError(f"Failed to get context window: {str(e)}")

    @staticmethod
    async def update_context(
        db: AsyncSession,
        agent_id: str,
        context_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update agent's current context."""
        try:
            # Store context update as a memory
            memory = await MemoryService.store_memory(
                db=db,
                agent_id=agent_id,
                content=context_update,
                memory_type="context",
                metadata={
                    "context_type": "update",
                    "timestamp": datetime.utcnow().isoformat()
                },
                importance=0.8  # Context updates are fairly important
            )
            
            return {
                "agent_id": agent_id,
                "context": context_update,
                "memory_id": memory.id,
                "updated_at": datetime.utcnow()
            }
        except Exception as e:
            raise MemoryError(f"Failed to update context: {str(e)}")

memory_service = MemoryService() 