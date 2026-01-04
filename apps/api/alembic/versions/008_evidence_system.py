"""Add evidence_items and evidence_links tables.

Revision ID: 008_evidence_system
Revises: 007_analysis_mode
Create Date: 2025-12-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "008_evidence_system"
down_revision = "007_analysis_mode"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create evidence_items table
    op.create_table(
        "evidence_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_type", sa.String(20), nullable=False),  # "paper" or "company_doc"
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=True),
        sa.Column("doc_chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("authors", postgresql.JSONB, nullable=True),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("excerpt", sa.Text, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    
    # Create evidence_links table
    op.create_table(
        "evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("query_runs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("claim_key", sa.String(100), nullable=False),  # e.g., "key_point_0", "claim_1"
        sa.Column("evidence_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evidence_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label_number", sa.Integer, nullable=False),  # [1], [2], etc.
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    
    # Create indexes
    op.create_index("ix_evidence_items_paper", "evidence_items", ["paper_id"])
    op.create_index("ix_evidence_items_doc_chunk", "evidence_items", ["doc_chunk_id"])
    op.create_index("ix_evidence_links_run_claim", "evidence_links", ["run_id", "claim_key"])


def downgrade() -> None:
    op.drop_index("ix_evidence_links_run_claim", table_name="evidence_links")
    op.drop_index("ix_evidence_items_doc_chunk", table_name="evidence_items")
    op.drop_index("ix_evidence_items_paper", table_name="evidence_items")
    op.drop_table("evidence_links")
    op.drop_table("evidence_items")
