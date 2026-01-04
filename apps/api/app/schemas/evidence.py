"""Evidence schemas."""

from typing import Any
from uuid import UUID

from app.schemas.base import BaseReadSchema, BaseSchema


class EvidenceCreate(BaseSchema):
    """Schema for creating evidence."""

    run_id: UUID
    paper_id: UUID
    evidence_json: dict[str, Any]


class EvidenceRead(BaseReadSchema):
    """Schema for reading evidence."""

    run_id: UUID
    paper_id: UUID
    evidence_json: dict[str, Any]
