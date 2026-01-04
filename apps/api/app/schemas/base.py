"""Base schemas with common configurations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(from_attributes=True)


class BaseReadSchema(BaseSchema):
    """Base schema for read operations."""

    id: UUID
    created_at: datetime
