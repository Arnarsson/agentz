"""fix max_iterations column type

Revision ID: 16ac1682d5e1
Revises: d4867f3a4c35
Create Date: 2025-01-09 16:10:24.804239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '16ac1682d5e1'
down_revision: Union[str, None] = 'd4867f3a4c35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support altering column types directly
    # We'll use a batch operation to modify the column
    with op.batch_alter_table('agents') as batch_op:
        batch_op.alter_column('max_iterations',
                            existing_type=sa.String(),
                            type_=sa.Integer(),
                            existing_nullable=True,
                            existing_server_default='5')


def downgrade() -> None:
    with op.batch_alter_table('agents') as batch_op:
        batch_op.alter_column('max_iterations',
                            existing_type=sa.Integer(),
                            type_=sa.String(),
                            existing_nullable=True,
                            existing_server_default='5')
