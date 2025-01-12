"""Memory consolidation service using LLM."""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.errors import ConsolidationError
from app.models.memory import Memory

class ConsolidationService:
    """Service for consolidating and summarizing memories using LLM."""

    def __init__(self):
        """Initialize the consolidation service."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def consolidate_memories(
        self,
        memories: List[Memory],
        consolidation_type: str = "summary"
    ) -> Dict[str, Any]:
        """Consolidate memories using LLM."""
        try:
            if not memories:
                return {
                    "summary": "No memories to consolidate",
                    "key_points": [],
                    "consolidated_at": datetime.utcnow()
                }

            # Prepare memories for consolidation
            memory_texts = []
            for memory in memories:
                timestamp = memory.timestamp.isoformat()
                content = (
                    memory.content
                    if isinstance(memory.content, str)
                    else json.dumps(memory.content)
                )
                memory_texts.append(f"[{timestamp}] ({memory.type}): {content}")

            # Create prompt based on consolidation type
            if consolidation_type == "summary":
                prompt = self._create_summary_prompt(memory_texts)
            elif consolidation_type == "insights":
                prompt = self._create_insights_prompt(memory_texts)
            elif consolidation_type == "patterns":
                prompt = self._create_patterns_prompt(memory_texts)
            else:
                prompt = self._create_summary_prompt(memory_texts)

            # Get LLM response
            response = await self.client.chat.completions.create(
                model="gpt-4-1106-preview",  # Using latest GPT-4 for better analysis
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI memory consolidation system. Your task is to analyze and consolidate memories to extract key information, patterns, and insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more focused analysis
                response_format={ "type": "json" }
            )

            # Parse and validate response
            consolidation = json.loads(response.choices[0].message.content)
            
            return {
                **consolidation,
                "consolidated_at": datetime.utcnow(),
                "consolidation_type": consolidation_type,
                "memory_count": len(memories)
            }

        except Exception as e:
            raise ConsolidationError(f"Failed to consolidate memories: {str(e)}")

    def _create_summary_prompt(self, memory_texts: List[str]) -> str:
        """Create prompt for memory summarization."""
        memories = "\n".join(memory_texts)
        return f"""Analyze the following memories and provide a JSON response with:
1. A concise summary of the main events and information
2. Key points extracted from the memories
3. Any important patterns or trends noticed
4. Potential action items or recommendations

Memories to analyze:
{memories}

Provide your response in the following JSON format:
{{
    "summary": "Concise summary of the memories",
    "key_points": ["Key point 1", "Key point 2", ...],
    "patterns": ["Pattern 1", "Pattern 2", ...],
    "action_items": ["Action 1", "Action 2", ...]
}}"""

    def _create_insights_prompt(self, memory_texts: List[str]) -> str:
        """Create prompt for extracting insights."""
        memories = "\n".join(memory_texts)
        return f"""Analyze the following memories and provide a JSON response focusing on insights:
1. Deep analysis of the information
2. Hidden connections between memories
3. Potential implications
4. Areas for further investigation

Memories to analyze:
{memories}

Provide your response in the following JSON format:
{{
    "insights": ["Insight 1", "Insight 2", ...],
    "connections": ["Connection 1", "Connection 2", ...],
    "implications": ["Implication 1", "Implication 2", ...],
    "investigation_areas": ["Area 1", "Area 2", ...]
}}"""

    def _create_patterns_prompt(self, memory_texts: List[str]) -> str:
        """Create prompt for pattern recognition."""
        memories = "\n".join(memory_texts)
        return f"""Analyze the following memories and provide a JSON response focusing on patterns:
1. Temporal patterns (time-based trends)
2. Behavioral patterns
3. Recurring themes
4. Anomalies or outliers

Memories to analyze:
{memories}

Provide your response in the following JSON format:
{{
    "temporal_patterns": ["Pattern 1", "Pattern 2", ...],
    "behavioral_patterns": ["Pattern 1", "Pattern 2", ...],
    "recurring_themes": ["Theme 1", "Theme 2", ...],
    "anomalies": ["Anomaly 1", "Anomaly 2", ...]
}}"""

    async def generate_reflection(
        self,
        memories: List[Memory],
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate reflective insights from memories."""
        try:
            if not memories:
                return {
                    "reflection": "No memories to reflect upon",
                    "insights": [],
                    "generated_at": datetime.utcnow()
                }

            # Prepare memories for reflection
            memory_texts = []
            for memory in memories:
                timestamp = memory.timestamp.isoformat()
                content = (
                    memory.content
                    if isinstance(memory.content, str)
                    else json.dumps(memory.content)
                )
                memory_texts.append(f"[{timestamp}] ({memory.type}): {content}")

            # Create reflection prompt
            focus_text = ""
            if focus_areas:
                focus_text = f"\nFocus particularly on these areas: {', '.join(focus_areas)}"

            prompt = f"""Reflect on the following memories and provide deep insights.{focus_text}
Consider:
1. What can be learned from these experiences?
2. What patterns or trends might be emerging?
3. What might be overlooked or underappreciated?
4. What opportunities or risks are suggested?

Memories to reflect upon:
{memory_texts}

Provide your reflection in the following JSON format:
{{
    "reflection": "Overall reflective analysis",
    "insights": ["Insight 1", "Insight 2", ...],
    "lessons_learned": ["Lesson 1", "Lesson 2", ...],
    "opportunities": ["Opportunity 1", "Opportunity 2", ...],
    "risks": ["Risk 1", "Risk 2", ...],
    "recommendations": ["Recommendation 1", "Recommendation 2", ...]
}}"""

            # Get LLM response
            response = await self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI reflection and insight generation system. Your task is to provide deep, thoughtful analysis of memories and experiences."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                response_format={ "type": "json" }
            )

            # Parse and validate response
            reflection = json.loads(response.choices[0].message.content)
            
            return {
                **reflection,
                "generated_at": datetime.utcnow(),
                "focus_areas": focus_areas,
                "memory_count": len(memories)
            }

        except Exception as e:
            raise ConsolidationError(f"Failed to generate reflection: {str(e)}")

consolidation_service = ConsolidationService() 