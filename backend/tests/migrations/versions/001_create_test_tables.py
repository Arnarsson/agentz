"""create test tables

Revision ID: 001
Revises: 
Create Date: 2024-01-08 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create test_agents table
    op.create_table(
        'test_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('goal', sa.String(), nullable=False),
        sa.Column('backstory', sa.String(), nullable=False),
        sa.Column('allow_delegation', sa.Boolean(), default=False),
        sa.Column('verbose', sa.Boolean(), default=True),
        sa.Column('memory', postgresql.JSONB(), default=dict),
        sa.Column('tools', postgresql.JSONB(), default=list),
        sa.Column('llm_config', postgresql.JSONB(), nullable=True),
        sa.Column('max_iterations', sa.Integer(), default=5),
        sa.Column('status', sa.String(), default='active'),
        sa.Column('execution_status', postgresql.JSONB(), default=dict),
        sa.Column('created_at', sa.String()),
        sa.Column('updated_at', sa.String())
    )

def downgrade() -> None:
    op.drop_table('test_agents') 