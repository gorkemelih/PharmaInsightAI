"""Paper schemas."""

from pydantic import Field

from app.schemas.base import BaseReadSchema, BaseSchema


class PaperCreate(BaseSchema):
    """Schema for creating a paper."""

    doi: str | None = Field(None, max_length=255)
    pmid: str | None = Field(None, max_length=50)
    title: str = Field(..., min_length=1)
    abstract: str | None = None
    journal: str | None = Field(None, max_length=500)
    year: int | None = Field(None, ge=1800, le=2100)
    url: str | None = None
    raw_source: str = Field(..., max_length=50)


class PaperRead(BaseReadSchema):
    """Schema for reading a paper."""

    doi: str | None
    pmid: str | None
    title: str
    abstract: str | None
    journal: str | None
    year: int | None
    url: str | None
    raw_source: str
