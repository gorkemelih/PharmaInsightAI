"""add full text support to papers

Revision ID: 012
Revises: 011_run_summary_status
Create Date: 2026-01-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '012_papers_fulltext'
down_revision: Union[str, None] = '008_evidence_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pmc_id column with index
    op.add_column('papers', sa.Column('pmc_id', sa.String(50), nullable=True))
    op.create_index('ix_papers_pmc_id', 'papers', ['pmc_id'])
    
    # Add full_text column
    op.add_column('papers', sa.Column('full_text', sa.Text(), nullable=True))
    
    # Add is_open_access column with default
    op.add_column('papers', sa.Column('is_open_access', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('papers', 'is_open_access')
    op.drop_column('papers', 'full_text')
    op.drop_index('ix_papers_pmc_id', 'papers')
    op.drop_column('papers', 'pmc_id')
