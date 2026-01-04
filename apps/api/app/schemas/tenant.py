"""Tenant schemas."""

from pydantic import Field

from app.schemas.base import BaseReadSchema, BaseSchema


class TenantCreate(BaseSchema):
    """Schema for creating a tenant."""

    name: str = Field(..., min_length=1, max_length=255)


class TenantRead(BaseReadSchema):
    """Schema for reading a tenant."""

    name: str
