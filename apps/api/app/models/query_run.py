"""QueryRun model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class QueryStatus(str, enum.Enum):
    """Query run status enumeration."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class AnalysisMode(str, enum.Enum):
    """Analysis mode enumeration."""

    SYNTHESIS = "synthesis"  # Quick: single LLM call for all papers
    PER_PAPER = "per_paper"  # Deep: per-paper summaries + synthesis


class QueryRun(BaseModel):
    """QueryRun entity for tracking literature search queries."""

    __tablename__ = "query_runs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[QueryStatus] = mapped_column(
        Enum(QueryStatus), nullable=False, default=QueryStatus.QUEUED
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Search parameters
    max_papers: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    year_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_to: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Analysis options
    analysis_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="synthesis"
    )
    include_marketing: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en"
    )

    # Soft-delete fields
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="query_runs")  # noqa: F821
    evidences: Mapped[list["Evidence"]] = relationship(  # noqa: F821
        "Evidence", back_populates="query_run", lazy="dynamic"
    )
    briefs: Mapped[list["Brief"]] = relationship(  # noqa: F821
        "Brief", back_populates="query_run", lazy="dynamic"
    )
    deleted_by_user: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[deleted_by]
    )

    @property
    def is_deleted(self) -> bool:
        """Check if run is soft-deleted."""
        return self.deleted_at is not None
