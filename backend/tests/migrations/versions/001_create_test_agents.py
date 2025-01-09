"""create test agents table

Revision ID: 001
Revises: 
Create Date: 2024-01-08 20:00:00.000000

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
    op.create_table(
        'test_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('goal', sa.String(), nullable=True),
        sa.Column('backstory', sa.String(), nullable=True),
        sa.Column('allow_delegation', sa.Boolean(), nullable=True),
        sa.Column('verbose', sa.Boolean(), nullable=True),
        sa.Column('memory', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tools', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('llm_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('max_iterations', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('execution_status', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )

def downgrade() -> None:
    op.drop_table('test_agents') 