"""Project schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseReadSchema, BaseSchema


class ProjectCreate(BaseSchema):
    """Schema for creating a project."""

    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    created_by_user_id: UUID | None = None


class ProjectRead(BaseReadSchema):
    """Schema for reading a project."""

    tenant_id: UUID
    name: str
    description: str | None
    created_by_user_id: UUID | None
