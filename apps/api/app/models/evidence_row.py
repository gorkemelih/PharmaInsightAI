"""Evidence row model for structured evidence table."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class EvidenceRow(BaseModel):
    """Evidence table row with structured PICO data."""

    __tablename__ = "evidence_rows"
    __table_args__ = (
        UniqueConstraint("run_id", "paper_id", name="uq_evidence_rows_run_paper"),
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("query_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", lazy="joined")  # noqa: F821
    query_run: Mapped["QueryRun"] = relationship("QueryRun")  # noqa: F821
