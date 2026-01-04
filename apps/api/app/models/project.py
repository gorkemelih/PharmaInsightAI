"""Project model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class Project(BaseModel):
    """Project entity for organizing research queries."""

    __tablename__ = "projects"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="projects")  # noqa: F821
    created_by_user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="projects", foreign_keys=[created_by_user_id]
    )
    deleted_by_user: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[deleted_by]
    )
    query_runs: Mapped[list["QueryRun"]] = relationship(  # noqa: F821
        "QueryRun", back_populates="project", lazy="dynamic"
    )

    @property
    def is_deleted(self) -> bool:
        """Check if project is soft-deleted."""
        return self.deleted_at is not None
