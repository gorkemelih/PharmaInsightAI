"""Add documents and document_chunks tables.

Revision ID: 006_documents
Revises: 005_soft_delete
Create Date: 2025-12-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "006_documents"
down_revision = "005_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="internal"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    
    # Create document_chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column("embedding", postgresql.JSONB, nullable=True),  # Store as JSON array for simplicity
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    
    # Create indexes
    op.create_index("ix_documents_not_deleted", "documents", ["deleted_at"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("ix_document_chunks_document_index", "document_chunks", ["document_id", "chunk_index"])


def downgrade() -> None:
    op.drop_index("ix_document_chunks_document_index", table_name="document_chunks")
    op.drop_index("ix_documents_not_deleted", table_name="documents")
    op.drop_table("document_chunks")
    op.drop_table("documents")
