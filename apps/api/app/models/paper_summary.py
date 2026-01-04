"""Paper summary model."""

import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class SummaryStatus(str, enum.Enum):
    """Summary processing status."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class PaperSummary(BaseModel):
    """Paper summary entity with LLM-generated structured data."""

    __tablename__ = "paper_summaries"
    __table_args__ = (
        UniqueConstraint("paper_id", "run_id", name="uq_paper_summaries_paper_run"),
    )

    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("query_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="QUEUED",
    )
    summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", lazy="joined")  # noqa: F821
    query_run: Mapped["QueryRun"] = relationship("QueryRun")  # noqa: F821

    @property
    def status_enum(self) -> SummaryStatus:
        """Get status as enum."""
        return SummaryStatus(self.status)

