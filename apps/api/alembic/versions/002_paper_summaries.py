"""Add paper_summaries table.

Revision ID: 002_paper_summaries
Revises: 001_initial_schema
Create Date: 2025-12-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_paper_summaries'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create paper_summaries table using VARCHAR for status
    # The app model uses Enum but we'll store as string to avoid type conflicts
    op.create_table(
        'paper_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column(
            'tenant_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('tenants.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'paper_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('papers.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'run_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('query_runs.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='QUEUED'),
        sa.Column('summary_json', postgresql.JSONB, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    
    # Create unique constraint for paper + run combination
    op.create_unique_constraint(
        'uq_paper_summaries_paper_run',
        'paper_summaries',
        ['paper_id', 'run_id']
    )


def downgrade() -> None:
    op.drop_table('paper_summaries')

