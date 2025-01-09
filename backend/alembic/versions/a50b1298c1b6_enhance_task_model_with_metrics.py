"""enhance_task_model_with_metrics

Revision ID: a50b1298c1b6
Revises: 16ac1682d5e1
Create Date: 2025-01-09 16:54:34.415491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = 'a50b1298c1b6'
down_revision: Union[str, None] = '16ac1682d5e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns for task result tracking
    op.add_column('tasks', sa.Column('result', sqlite.JSON, nullable=True))
    op.add_column('tasks', sa.Column('error', sqlite.JSON, nullable=True))
    op.add_column('tasks', sa.Column('tools', sqlite.JSON, nullable=True, server_default='[]'))
    op.add_column('tasks', sa.Column('context', sqlite.JSON, nullable=True, server_default='{}'))
    
    # Add new columns for timing and retry tracking
    op.add_column('tasks', sa.Column('start_time', sa.DateTime(), nullable=True))
    op.add_column('tasks', sa.Column('end_time', sa.DateTime(), nullable=True))
    op.add_column('tasks', sa.Column('execution_time', sa.Float(), nullable=True))
    op.add_column('tasks', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tasks', sa.Column('retry_config', sqlite.JSON, nullable=True))


def downgrade() -> None:
    # Remove added columns in reverse order
    op.drop_column('tasks', 'retry_config')
    op.drop_column('tasks', 'retry_count')
    op.drop_column('tasks', 'execution_time')
    op.drop_column('tasks', 'end_time')
    op.drop_column('tasks', 'start_time')
    op.drop_column('tasks', 'context')
    op.drop_column('tasks', 'tools')
    op.drop_column('tasks', 'error')
    op.drop_column('tasks', 'result')
