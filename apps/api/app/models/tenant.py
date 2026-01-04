"""Tenant model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class Tenant(BaseModel):
    """Tenant entity for multi-tenancy support."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User", back_populates="tenant", lazy="dynamic"
    )
    projects: Mapped[list["Project"]] = relationship(  # noqa: F821
        "Project", back_populates="tenant", lazy="dynamic"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # noqa: F821
        "AuditLog", back_populates="tenant", lazy="dynamic"
    )
