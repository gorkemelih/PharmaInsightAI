"""Evidence models."""

import enum
import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class Evidence(BaseModel):
    """Evidence entity linking papers to query runs with extracted evidence."""

    __tablename__ = "evidences"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("query_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Relationships
    query_run: Mapped["QueryRun"] = relationship(  # noqa: F821
        "QueryRun", back_populates="evidences"
    )
    paper: Mapped["Paper"] = relationship("Paper", back_populates="evidences")  # noqa: F821


# ============ New Evidence System ============


class SourceType(str, enum.Enum):
    """Evidence source type."""

    PAPER = "paper"
    COMPANY_DOC = "company_doc"


class EvidenceItem(BaseModel):
    """Evidence item from paper or company document."""

    __tablename__ = "evidence_items"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    paper_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=True,
    )
    doc_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    authors: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    links: Mapped[list["EvidenceLink"]] = relationship(
        "EvidenceLink", back_populates="evidence_item", cascade="all, delete-orphan"
    )


class EvidenceLink(BaseModel):
    """Link between a run claim and an evidence item."""

    __tablename__ = "evidence_links"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("query_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim_key: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    label_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    evidence_item: Mapped["EvidenceItem"] = relationship(
        "EvidenceItem", back_populates="links"
    )
