"""create agents and tasks tables

Revision ID: 001
Revises: 
Create Date: 2024-01-08 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('goal', sa.String(), nullable=False),
        sa.Column('backstory', sa.String(), nullable=False),
        sa.Column('allow_delegation', sa.Boolean(), nullable=True, default=False),
        sa.Column('verbose', sa.Boolean(), nullable=True, default=True),
        sa.Column('memory', sqlite.JSON, nullable=True, default=dict),
        sa.Column('tools', sqlite.JSON, nullable=True, default=list),
        sa.Column('llm_config', sqlite.JSON, nullable=True, default=dict),
        sa.Column('max_iterations', sa.Integer(), nullable=True, default=5),
        sa.Column('status', sa.String(), nullable=True, default='active'),
        sa.Column('execution_status', sqlite.JSON, nullable=True, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role')
    )
    op.create_index(op.f('ix_agents_id'), 'agents', ['id'], unique=False)
    op.create_index(op.f('ix_agents_role'), 'agents', ['role'], unique=True)

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, default=1),
        sa.Column('requires_delegation', sa.Boolean(), nullable=True, default=False),
        sa.Column('execution_params', sqlite.JSON, nullable=True, default=dict),
        sa.Column('status', sa.String(), nullable=True, default='pending'),
        sa.Column('metrics', sqlite.JSON, nullable=True, default=dict),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_agent_id'), 'tasks', ['agent_id'], unique=False)


def downgrade() -> None:
    op.drop_table('tasks')
    op.drop_table('agents') 