from typing import List, Optional
from sqlalchemy.orm import Session
from crewai import Agent as CrewAgent
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate
from app.core.config import settings

class AgentService:
    """Service for managing agents."""

    @staticmethod
    async def create_agent(db: Session, agent_data: AgentCreate) -> Agent:
        """Create a new agent."""
        # Create CrewAI agent
        crew_agent = CrewAgent(
            role=agent_data.role,
            goal=agent_data.goal,
            backstory=agent_data.backstory,
            allow_delegation=agent_data.allow_delegation,
            verbose=agent_data.verbose
        )

        # Create database record
        db_agent = Agent(
            role=agent_data.role,
            goal=agent_data.goal,
            backstory=agent_data.backstory,
            allow_delegation=agent_data.allow_delegation,
            verbose=agent_data.verbose,
            memory={}  # Initialize empty memory
        )
        
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        return db_agent

    @staticmethod
    async def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return db.query(Agent).filter(Agent.id == agent_id).first()

    @staticmethod
    async def get_agent_by_role(db: Session, role: str) -> Optional[Agent]:
        """Get agent by role."""
        return db.query(Agent).filter(Agent.role == role).first()

    @staticmethod
    async def list_agents(db: Session, skip: int = 0, limit: int = 100) -> List[Agent]:
        """List all agents."""
        return db.query(Agent).offset(skip).limit(limit).all()

    @staticmethod
    async def update_agent(
        db: Session, agent_id: str, agent_data: AgentUpdate
    ) -> Optional[Agent]:
        """Update agent."""
        db_agent = await AgentService.get_agent(db, agent_id)
        if not db_agent:
            return None

        # Update agent attributes
        for field, value in agent_data.dict(exclude_unset=True).items():
            setattr(db_agent, field, value)

        db.commit()
        db.refresh(db_agent)
        return db_agent

    @staticmethod
    async def delete_agent(db: Session, agent_id: str) -> bool:
        """Delete agent."""
        db_agent = await AgentService.get_agent(db, agent_id)
        if not db_agent:
            return False

        db.delete(db_agent)
        db.commit()
        return True 