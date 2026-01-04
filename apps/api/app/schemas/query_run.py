"""QueryRun schemas."""

from enum import Enum
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseReadSchema, BaseSchema


class QueryStatus(str, Enum):
    """Query run status enumeration."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class QueryRunCreate(BaseSchema):
    """Schema for creating a query run."""

    project_id: UUID
    query_text: str = Field(..., min_length=1)


class QueryRunRead(BaseReadSchema):
    """Schema for reading a query run."""

    project_id: UUID
    query_text: str
    status: QueryStatus
    error_message: str | None
