"""Audit logging service."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    tenant_id: UUID,
    action: str,
    resource_type: str,
    actor_user_id: UUID | None = None,
    resource_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Create an audit log entry."""
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=metadata or {},
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


# Predefined actions
class AuditActions:
    """Constants for audit actions."""

    # Auth
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"

    # User CRUD
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"

    # Project CRUD
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"

    # QueryRun
    RUN_CREATED = "run_created"
    RUN_STATUS_CHANGED = "run_status_changed"


class ResourceTypes:
    """Constants for resource types."""

    USER = "user"
    PROJECT = "project"
    QUERY_RUN = "query_run"
    AUTH = "auth"
