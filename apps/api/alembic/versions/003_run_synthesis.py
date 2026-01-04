"""Add run_summaries and evidence_rows tables.

Revision ID: 003_run_synthesis
Revises: 002_paper_summaries
Create Date: 2025-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_run_synthesis'
down_revision: Union[str, None] = '002_paper_summaries'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create run_summaries table
    op.create_table(
        'run_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column(
            'tenant_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('tenants.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'run_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('query_runs.id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
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

    # Create evidence_rows table
    op.create_table(
        'evidence_rows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column(
            'tenant_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('tenants.id', ondelete='CASCADE'),
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
        sa.Column(
            'paper_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('papers.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column('row_json', postgresql.JSONB, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create unique constraint for run_id + paper_id
    op.create_unique_constraint(
        'uq_evidence_rows_run_paper',
        'evidence_rows',
        ['run_id', 'paper_id']
    )


def downgrade() -> None:
    op.drop_table('evidence_rows')
    op.drop_table('run_summaries')
