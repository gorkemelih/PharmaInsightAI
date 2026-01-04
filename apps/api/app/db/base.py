"""SQLAlchemy declarative base and mixins."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
    }


class UUIDMixin:
    """Mixin that adds a UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Mixin that adds created_at timestamp."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Abstract base model with UUID and timestamp."""

    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
