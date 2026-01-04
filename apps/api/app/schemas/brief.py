"""Brief schemas."""

from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseReadSchema, BaseSchema


class BriefCreate(BaseSchema):
    """Schema for creating a brief."""

    run_id: UUID
    pdf_path: str = Field(..., max_length=1000)
    metadata_json: dict[str, Any]


class BriefRead(BaseReadSchema):
    """Schema for reading a brief."""

    run_id: UUID
    pdf_path: str
    metadata_json: dict[str, Any]
