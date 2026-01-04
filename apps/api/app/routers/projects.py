"""Project management endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import AdminUser, AnalystUser, AuthenticatedUser
from app.db.session import get_db
from app.models.project import Project
from app.models.query_run import QueryRun
from app.services.audit import AuditActions, ResourceTypes, log_action

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    """Request body for creating a project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProjectUpdate(BaseModel):
    """Request body for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class ProjectResponse(BaseModel):
    """Project response."""

    id: str
    name: str
    description: str | None
    tenant_id: str
    created_by_user_id: str | None
    created_at: str


def get_project_or_404(
    project_id: UUID,
    tenant_id: UUID,
    db: Session,
    include_deleted: bool = False,
) -> Project:
    """Get project by ID or raise 404."""
    query = db.query(Project).filter(
        Project.id == project_id,
        Project.tenant_id == tenant_id,
    )
    if not include_deleted:
        query = query.filter(Project.deleted_at.is_(None))

    project = query.first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[ProjectResponse]:
    """List all active (non-deleted) projects in the tenant."""
    projects = (
        db.query(Project)
        .filter(
            Project.tenant_id == current_user.tenant_id,
            Project.deleted_at.is_(None),  # Exclude deleted
        )
        .order_by(Project.created_at.desc())
        .all()
    )
    return [
        ProjectResponse(
            id=str(p.id),
            name=p.name,
            description=p.description,
            tenant_id=str(p.tenant_id),
            created_by_user_id=str(p.created_by_user_id) if p.created_by_user_id else None,
            created_at=p.created_at.isoformat(),
        )
        for p in projects
    ]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    request: ProjectCreate,
    current_user: AnalystUser,  # ADMIN or ANALYST
    db: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    """Create a new project."""
    project = Project(
        tenant_id=current_user.tenant_id,
        name=request.name,
        description=request.description,
        created_by_user_id=current_user.user_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Audit log
    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        action=AuditActions.PROJECT_CREATED,
        resource_type=ResourceTypes.PROJECT,
        actor_user_id=current_user.user_id,
        resource_id=project.id,
        metadata={"name": project.name},
    )

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        tenant_id=str(project.tenant_id),
        created_by_user_id=str(project.created_by_user_id) if project.created_by_user_id else None,
        created_at=project.created_at.isoformat(),
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    """Get a project by ID."""
    project = get_project_or_404(project_id, current_user.tenant_id, db)
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        tenant_id=str(project.tenant_id),
        created_by_user_id=str(project.created_by_user_id) if project.created_by_user_id else None,
        created_at=project.created_at.isoformat(),
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    request: ProjectUpdate,
    current_user: AnalystUser,  # ADMIN or ANALYST
    db: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    """Update a project."""
    project = get_project_or_404(project_id, current_user.tenant_id, db)

    changes: dict[str, str] = {}

    if request.name is not None and request.name != project.name:
        changes["name"] = f"{project.name} -> {request.name}"
        project.name = request.name

    if request.description is not None and request.description != project.description:
        changes["description"] = "updated"
        project.description = request.description

    if changes:
        db.commit()
        db.refresh(project)

        # Audit log
        log_action(
            db=db,
            tenant_id=current_user.tenant_id,
            action=AuditActions.PROJECT_UPDATED,
            resource_type=ResourceTypes.PROJECT,
            actor_user_id=current_user.user_id,
            resource_id=project.id,
            metadata={"changes": changes},
        )

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        tenant_id=str(project.tenant_id),
        created_by_user_id=str(project.created_by_user_id) if project.created_by_user_id else None,
        created_at=project.created_at.isoformat(),
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    current_user: AdminUser,  # ADMIN only
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Soft-delete a project and cascade to its runs."""
    project = get_project_or_404(project_id, current_user.tenant_id, db)

    now = datetime.now(timezone.utc)

    # Soft-delete all runs belonging to this project
    db.query(QueryRun).filter(
        QueryRun.project_id == project_id,
        QueryRun.deleted_at.is_(None),
    ).update({
        QueryRun.deleted_at: now,
        QueryRun.deleted_by: current_user.user_id,
    })

    # Soft-delete the project
    project.deleted_at = now
    project.deleted_by = current_user.user_id
    db.commit()

    # Audit log
    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        action=AuditActions.PROJECT_DELETED,
        resource_type=ResourceTypes.PROJECT,
        actor_user_id=current_user.user_id,
        resource_id=project_id,
        metadata={"name": project.name, "soft_delete": True},
    )


@router.post("/{project_id}/restore", response_model=ProjectResponse)
def restore_project(
    project_id: UUID,
    current_user: AdminUser,  # ADMIN only
    db: Annotated[Session, Depends(get_db)],
) -> ProjectResponse:
    """Restore a soft-deleted project and its runs."""
    # Get project including deleted ones
    project = get_project_or_404(project_id, current_user.tenant_id, db, include_deleted=True)

    if project.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is not deleted",
        )

    # Restore all runs that were deleted at the same time as the project
    db.query(QueryRun).filter(
        QueryRun.project_id == project_id,
        QueryRun.deleted_at.isnot(None),
    ).update({
        QueryRun.deleted_at: None,
        QueryRun.deleted_by: None,
    })

    # Restore the project
    project.deleted_at = None
    project.deleted_by = None
    db.commit()
    db.refresh(project)

    # Audit log
    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        action=AuditActions.PROJECT_UPDATED,
        resource_type=ResourceTypes.PROJECT,
        actor_user_id=current_user.user_id,
        resource_id=project_id,
        metadata={"name": project.name, "action": "restored"},
    )

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        tenant_id=str(project.tenant_id),
        created_by_user_id=str(project.created_by_user_id) if project.created_by_user_id else None,
        created_at=project.created_at.isoformat(),
    )
