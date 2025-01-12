"""create memories table

Revision ID: 512684a5d3c1
Revises: a50b1298c1b6
Create Date: 2024-01-09 17:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = '512684a5d3c1'
down_revision: Union[str, None] = 'a50b1298c1b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create memories table
    op.create_table(
        'memories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('content', sqlite.JSON, nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata', sqlite.JSON, nullable=True, server_default='{}'),
        sa.Column('importance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('context', sqlite.JSON, nullable=True),
        sa.Column('embedding', sqlite.JSON, nullable=True),
        sa.Column('references', sqlite.JSON, nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_memories_id', 'memories', ['id'], unique=False)
    op.create_index('ix_memories_agent_type', 'memories', ['agent_id', 'type'], unique=False)
    op.create_index('ix_memories_timestamp', 'memories', ['timestamp'], unique=False)
    op.create_index('ix_memories_importance', 'memories', ['importance'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_memories_importance', table_name='memories')
    op.drop_index('ix_memories_timestamp', table_name='memories')
    op.drop_index('ix_memories_agent_type', table_name='memories')
    op.drop_index('ix_memories_id', table_name='memories')

    # Drop table
    op.drop_table('memories')
