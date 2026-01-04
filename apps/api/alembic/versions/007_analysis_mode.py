"""Add analysis_mode to query_runs.

Revision ID: 007_analysis_mode
Revises: 006_documents
Create Date: 2025-12-29
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "007_analysis_mode"
down_revision = "006_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add analysis_mode column with default 'synthesis'
    op.add_column(
        "query_runs",
        sa.Column(
            "analysis_mode",
            sa.String(20),
            nullable=False,
            server_default="synthesis",
        ),
    )
    
    # Add include_marketing column
    op.add_column(
        "query_runs",
        sa.Column(
            "include_marketing",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
    )
    
    # Add language column
    op.add_column(
        "query_runs",
        sa.Column(
            "language",
            sa.String(10),
            nullable=False,
            server_default="en",
        ),
    )


def downgrade() -> None:
    op.drop_column("query_runs", "language")
    op.drop_column("query_runs", "include_marketing")
    op.drop_column("query_runs", "analysis_mode")
