"""Agent memory management service."""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from app.core.errors import AgentMemoryError
from app.services.memory import MemoryService
from app.services.consolidation import consolidation_service
from app.models.memory import Memory
from sqlalchemy.ext.asyncio import AsyncSession

class AgentMemoryManager:
    """Service for managing agent memory interactions and learning."""

    @staticmethod
    async def remember_task_execution(
        db: AsyncSession,
        agent_id: str,
        task_id: str,
        execution_result: Dict[str, Any],
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store task execution memory."""
        try:
            # Calculate importance based on success and impact
            importance = 0.7 if success else 0.9  # Failed tasks are more important to remember
            
            # Store execution memory
            memory = await MemoryService.store_memory(
                db=db,
                agent_id=agent_id,
                content={
                    "task_id": task_id,
                    "result": execution_result,
                    "success": success
                },
                memory_type="task_execution",
                metadata={
                    "task_id": task_id,
                    "success": success,
                    **metadata or {}
                },
                importance=importance
            )
            
            # If task failed, trigger immediate reflection
            if not success:
                reflection = await MemoryService.reflect_on_memories(
                    db=db,
                    agent_id=agent_id,
                    focus_areas=["task_failures", "error_patterns"],
                    memory_type="task_execution",
                )
                
                return {
                    "memory_id": memory.id,
                    "reflection": reflection
                }
            
            return {"memory_id": memory.id}

        except Exception as e:
            raise AgentMemoryError(f"Failed to store task execution memory: {str(e)}")

    @staticmethod
    async def get_relevant_experience(
        db: AsyncSession,
        agent_id: str,
        task_description: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get relevant past experiences for a task."""
        try:
            # Query similar task memories
            memories = await MemoryService.query_memories(
                db=db,
                agent_id=agent_id,
                query=task_description,
                memory_type="task_execution",
                limit=limit
            )
            
            return [
                {
                    "task_id": memory.content["task_id"],
                    "success": memory.content["success"],
                    "result": memory.content["result"],
                    "timestamp": memory.timestamp,
                    "importance": memory.importance
                }
                for memory in memories
            ]

        except Exception as e:
            raise AgentMemoryError(f"Failed to get relevant experience: {str(e)}")

    @staticmethod
    async def learn_from_experience(
        db: AsyncSession,
        agent_id: str,
        time_window: Optional[tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Generate learning insights from recent experiences."""
        try:
            # Get consolidated insights
            consolidation = await MemoryService.consolidate_memories(
                db=db,
                agent_id=agent_id,
                memory_type="task_execution",
                time_range=time_window,
                consolidation_type="insights"
            )
            
            # Generate focused reflection
            reflection = await MemoryService.reflect_on_memories(
                db=db,
                agent_id=agent_id,
                focus_areas=[
                    "success_patterns",
                    "failure_patterns",
                    "improvement_areas",
                    "skill_gaps"
                ],
                memory_type="task_execution",
                time_range=time_window
            )
            
            # Store learning outcome
            learning = await MemoryService.store_memory(
                db=db,
                agent_id=agent_id,
                content={
                    "insights": consolidation.get("insights", []),
                    "lessons": reflection.get("lessons_learned", []),
                    "improvements": reflection.get("recommendations", [])
                },
                memory_type="learning",
                metadata={
                    "time_window": [
                        time_window[0].isoformat() if time_window else None,
                        time_window[1].isoformat() if time_window else None
                    ]
                },
                importance=1.0  # Learning outcomes are critical
            )
            
            return {
                "memory_id": learning.id,
                "insights": consolidation.get("insights", []),
                "lessons": reflection.get("lessons_learned", []),
                "improvements": reflection.get("recommendations", [])
            }

        except Exception as e:
            raise AgentMemoryError(f"Failed to learn from experience: {str(e)}")

    @staticmethod
    async def get_decision_context(
        db: AsyncSession,
        agent_id: str,
        decision_type: str,
        relevant_factors: List[str]
    ) -> Dict[str, Any]:
        """Get memory-based context for decision making."""
        try:
            # Get recent context
            context = await MemoryService.get_context_window(
                db=db,
                agent_id=agent_id,
                window_size=5
            )
            
            # Get relevant memories
            query = f"Decision making context for {decision_type} considering {', '.join(relevant_factors)}"
            relevant_memories = await MemoryService.query_memories(
                db=db,
                agent_id=agent_id,
                query=query,
                limit=10
            )
            
            # Get applicable learnings
            learnings = await MemoryService.query_memories(
                db=db,
                agent_id=agent_id,
                query=query,
                memory_type="learning",
                limit=5
            )
            
            return {
                "current_context": [
                    {
                        "type": memory.type,
                        "content": memory.content,
                        "timestamp": memory.timestamp
                    }
                    for memory in context
                ],
                "relevant_experiences": [
                    {
                        "type": memory.type,
                        "content": memory.content,
                        "importance": memory.importance,
                        "timestamp": memory.timestamp
                    }
                    for memory in relevant_memories
                ],
                "applicable_learnings": [
                    {
                        "insights": memory.content.get("insights", []),
                        "lessons": memory.content.get("lessons", []),
                        "timestamp": memory.timestamp
                    }
                    for memory in learnings
                ]
            }

        except Exception as e:
            raise AgentMemoryError(f"Failed to get decision context: {str(e)}")

    @staticmethod
    async def update_agent_knowledge(
        db: AsyncSession,
        agent_id: str,
        knowledge: Dict[str, Any],
        source: str,
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Update agent's knowledge base."""
        try:
            # Store in knowledge base
            kb_entry = await MemoryService.add_to_knowledge_base(
                db=db,
                content=knowledge,
                metadata={
                    "source": source,
                    "confidence": confidence,
                    "agent_id": agent_id,
                    "added_at": datetime.utcnow().isoformat()
                }
            )
            
            # Create agent memory of learning this knowledge
            memory = await MemoryService.store_memory(
                db=db,
                agent_id=agent_id,
                content={
                    "knowledge_id": kb_entry["id"],
                    "knowledge": knowledge,
                    "source": source
                },
                memory_type="knowledge_acquisition",
                metadata={
                    "source": source,
                    "confidence": confidence
                },
                importance=0.8
            )
            
            return {
                "knowledge_id": kb_entry["id"],
                "memory_id": memory.id,
                "added_at": kb_entry["added_at"]
            }

        except Exception as e:
            raise AgentMemoryError(f"Failed to update agent knowledge: {str(e)}")

agent_memory_manager = AgentMemoryManager() 