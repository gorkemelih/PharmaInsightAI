"""Add soft-delete fields to projects and runs.

Revision ID: 005_soft_delete
Revises: 004_run_search_params
Create Date: 2025-12-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "005_soft_delete"
down_revision = "004_run_search_params"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add soft-delete columns to projects
    op.add_column(
        "projects",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column(
            "deleted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_projects_not_deleted",
        "projects",
        ["deleted_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Add soft-delete columns to query_runs
    op.add_column(
        "query_runs",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "query_runs",
        sa.Column(
            "deleted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_runs_not_deleted",
        "query_runs",
        ["deleted_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_runs_not_deleted", table_name="query_runs")
    op.drop_column("query_runs", "deleted_by")
    op.drop_column("query_runs", "deleted_at")

    op.drop_index("ix_projects_not_deleted", table_name="projects")
    op.drop_column("projects", "deleted_by")
    op.drop_column("projects", "deleted_at")
