"""User schemas."""

from enum import Enum
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import BaseReadSchema, BaseSchema


class UserRole(str, Enum):
    """User roles enumeration."""

    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class UserCreate(BaseSchema):
    """Schema for creating a user."""

    tenant_id: UUID
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.VIEWER


class UserRead(BaseReadSchema):
    """Schema for reading a user."""

    tenant_id: UUID
    email: str
    role: UserRole
    is_active: bool
