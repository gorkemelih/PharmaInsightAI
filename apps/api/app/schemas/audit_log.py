"""AuditLog schemas."""

from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseReadSchema, BaseSchema


class AuditLogCreate(BaseSchema):
    """Schema for creating an audit log entry."""

    tenant_id: UUID
    actor_user_id: UUID | None = None
    action: str = Field(..., max_length=100)
    resource_type: str = Field(..., max_length=100)
    resource_id: UUID | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class AuditLogRead(BaseReadSchema):
    """Schema for reading an audit log entry."""

    tenant_id: UUID
    actor_user_id: UUID | None
    action: str
    resource_type: str
    resource_id: UUID | None
    metadata_json: dict[str, Any]
