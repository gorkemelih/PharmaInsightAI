"""User model."""

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class UserRole(str, enum.Enum):
    """User roles enumeration."""

    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class User(BaseModel):
    """User entity."""

    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")  # noqa: F821
    projects: Mapped[list["Project"]] = relationship(  # noqa: F821
        "Project",
        back_populates="created_by_user",
        lazy="dynamic",
        foreign_keys="Project.created_by_user_id",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # noqa: F821
        "AuditLog", back_populates="actor_user", lazy="dynamic"
    )
