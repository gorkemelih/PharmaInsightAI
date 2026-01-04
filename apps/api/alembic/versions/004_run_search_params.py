"""Add search parameters to query_runs.

Revision ID: 004_run_search_params
Revises: 003_run_synthesis
Create Date: 2025-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_run_search_params'
down_revision: Union[str, None] = '003_run_synthesis'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add search parameter columns to query_runs
    op.add_column('query_runs', sa.Column('max_papers', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('query_runs', sa.Column('year_from', sa.Integer(), nullable=True))
    op.add_column('query_runs', sa.Column('year_to', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('query_runs', 'year_to')
    op.drop_column('query_runs', 'year_from')
    op.drop_column('query_runs', 'max_papers')
