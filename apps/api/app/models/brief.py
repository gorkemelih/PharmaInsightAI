"""Brief model."""

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class Brief(BaseModel):
    """Brief entity for storing generated PDF reports."""

    __tablename__ = "briefs"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("query_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pdf_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Relationships
    query_run: Mapped["QueryRun"] = relationship(  # noqa: F821
        "QueryRun", back_populates="briefs"
    )
