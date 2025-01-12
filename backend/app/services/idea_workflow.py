"""Idea workflow service module."""
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.workflow import Workflow
from app.models.agent import Agent
from app.core.errors import WorkflowError
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate
from app.services.crew_service import CrewService

class IdeaWorkflowService:
    """Service for managing idea creation and refinement workflow."""
    
    PHASE = "idea_creation"
    
    @staticmethod
    async def create_workflow(db: AsyncSession, workflow_data: WorkflowCreate) -> Workflow:
        """Create a new idea workflow with its agents."""
        try:
            # Create workflow
            workflow_id = str(uuid.uuid4())
            workflow = Workflow(
                id=workflow_id,
                name=workflow_data.name,
                description=workflow_data.description,
                phase=IdeaWorkflowService.PHASE,
                config=workflow_data.config or {},
                status="pending"
            )
            
            # Create agents for the workflow
            agents = [
                Agent(
                    id=str(uuid.uuid4()),
                    name="Visionary",
                    role="visionary",
                    description="Generate groundbreaking ideas with transformative potential",
                    prompt_template=(
                        "Analyze the current market and develop a high-level concept for "
                        "a business idea that solves a critical market problem. Consider "
                        "emerging trends, unmet needs, and potential disruption opportunities. "
                        "Your output should include:\n"
                        "1. Problem Statement\n"
                        "2. Proposed Solution\n"
                        "3. Target Market\n"
                        "4. Key Innovation Points\n"
                        "5. Potential Impact"
                    ),
                    workflow_id=workflow_id,
                    capabilities={
                        "ideation": True,
                        "market_analysis": True,
                        "innovation": True
                    }
                ),
                Agent(
                    id=str(uuid.uuid4()),
                    name="Ideator",
                    role="ideator",
                    description="Expand and iterate on initial ideas to explore their full potential",
                    prompt_template=(
                        "Based on the initial concept, brainstorm 10 creative variations "
                        "or alternative approaches. For each variation, provide:\n"
                        "1. Unique Value Proposition\n"
                        "2. Key Differentiators\n"
                        "3. Business Model Possibilities\n"
                        "4. Market Opportunity\n"
                        "5. Technical Feasibility"
                    ),
                    workflow_id=workflow_id,
                    capabilities={
                        "brainstorming": True,
                        "iteration": True,
                        "creativity": True
                    }
                ),
                Agent(
                    id=str(uuid.uuid4()),
                    name="Creative Refiner",
                    role="creative_refiner",
                    description="Shape the idea into a market-ready concept with clear value propositions",
                    prompt_template=(
                        "Review and refine the proposed concepts into a cohesive, "
                        "actionable business idea. Your output should include:\n"
                        "1. Refined Value Proposition\n"
                        "2. Market Strategy\n"
                        "3. Revenue Model\n"
                        "4. Competitive Analysis\n"
                        "5. Implementation Roadmap\n"
                        "6. Risk Assessment"
                    ),
                    workflow_id=workflow_id,
                    capabilities={
                        "refinement": True,
                        "value_proposition": True,
                        "market_fit": True
                    }
                )
            ]
            
            # Add to database
            db.add(workflow)
            for agent in agents:
                db.add(agent)
            
            await db.commit()
            await db.refresh(workflow)
            
            return workflow
            
        except Exception as e:
            await db.rollback()
            raise WorkflowError(f"Failed to create idea workflow: {str(e)}")
    
    @staticmethod
    async def get_workflow(db: AsyncSession, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        result = await db.execute(
            select(Workflow)
            .filter(Workflow.id == workflow_id)
            .filter(Workflow.phase == IdeaWorkflowService.PHASE)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_workflows(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Workflow]:
        """List all idea workflows."""
        result = await db.execute(
            select(Workflow)
            .filter(Workflow.phase == IdeaWorkflowService.PHASE)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_workflow(
        db: AsyncSession,
        workflow_id: str,
        workflow_data: WorkflowUpdate
    ) -> Workflow:
        """Update workflow details."""
        workflow = await IdeaWorkflowService.get_workflow(db, workflow_id)
        if not workflow:
            raise WorkflowError(f"Workflow {workflow_id} not found")
            
        try:
            update_data = workflow_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(workflow, field, value)
            
            workflow.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(workflow)
            
            return workflow
            
        except Exception as e:
            await db.rollback()
            raise WorkflowError(f"Failed to update workflow: {str(e)}")
    
    @staticmethod
    async def execute_workflow(db: AsyncSession, workflow_id: str) -> Dict:
        """Execute the idea creation workflow."""
        workflow = await IdeaWorkflowService.get_workflow(db, workflow_id)
        if not workflow:
            raise WorkflowError(f"Workflow {workflow_id} not found")
            
        try:
            # Update workflow status
            workflow.status = "executing"
            await db.commit()
            
            # Get workflow agents
            result = await db.execute(
                select(Agent)
                .filter(Agent.workflow_id == workflow_id)
                .order_by(Agent.created_at)
            )
            agents = result.scalars().all()
            
            # Create CrewAI agents and tasks
            crew_agents = []
            tasks = []
            workflow_results = {}
            
            for agent in agents:
                # Create CrewAI agent
                crew_agent = CrewService.create_agent(
                    name=agent.name,
                    role=agent.role,
                    goal=agent.description,
                    prompt_template=agent.prompt_template
                )
                crew_agents.append(crew_agent)
                
                # Create task for the agent
                task = CrewService.create_task(
                    description=agent.prompt_template,
                    agent=crew_agent,
                    context=workflow.config,
                    expected_output="Detailed analysis and recommendations"
                )
                tasks.append(task)
            
            # Execute the workflow
            results = CrewService.execute_tasks(crew_agents, tasks)
            
            # Update workflow with results
            workflow.results = results
            workflow.status = "completed"
            workflow.updated_at = datetime.utcnow()
            await db.commit()
            
            return results
            
        except Exception as e:
            workflow.status = "failed"
            await db.commit()
            raise WorkflowError(f"Failed to execute workflow: {str(e)}") 