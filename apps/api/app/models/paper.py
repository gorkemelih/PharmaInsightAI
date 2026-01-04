"""Paper model."""


from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class Paper(BaseModel):
    """Paper entity for storing literature references."""

    __tablename__ = "papers"

    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    pmid: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    pmc_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_open_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    journal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    authors: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., "pubmed", "europepmc", "crossref", "openalex", "arxiv"

    # Relationships
    evidences: Mapped[list["Evidence"]] = relationship(  # noqa: F821
        "Evidence", back_populates="paper", lazy="dynamic"
    )

