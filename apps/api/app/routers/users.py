"""User management endpoints (ADMIN only)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.deps import AdminUser
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.audit import AuditActions, ResourceTypes, log_action

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    """Request body for creating a user."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    """Request body for updating a user."""

    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """User response."""

    id: str
    email: str
    role: str
    is_active: bool
    tenant_id: str
    created_at: str


@router.get("", response_model=list[UserResponse])
def list_users(
    admin_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[UserResponse]:
    """List all users in the tenant (ADMIN only)."""
    users = (
        db.query(User).filter(User.tenant_id == admin_user.tenant_id).all()
    )
    return [
        UserResponse(
            id=str(u.id),
            email=u.email,
            role=u.role.value,
            is_active=u.is_active,
            tenant_id=str(u.tenant_id),
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: UserCreate,
    admin_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Create a new user (ADMIN only)."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        tenant_id=admin_user.tenant_id,
        email=request.email,
        password_hash=hash_password(request.password),
        role=request.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit log
    log_action(
        db=db,
        tenant_id=admin_user.tenant_id,
        action=AuditActions.USER_CREATED,
        resource_type=ResourceTypes.USER,
        actor_user_id=admin_user.user_id,
        resource_id=user.id,
        metadata={"email": user.email, "role": user.role.value},
    )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        tenant_id=str(user.tenant_id),
        created_at=user.created_at.isoformat(),
    )


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    request: UserUpdate,
    admin_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Update a user (ADMIN only)."""
    user = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == admin_user.tenant_id)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Track changes for audit
    changes: dict[str, str] = {}

    if request.role is not None and request.role != user.role:
        changes["role"] = f"{user.role.value} -> {request.role.value}"
        user.role = request.role

    if request.is_active is not None and request.is_active != user.is_active:
        changes["is_active"] = f"{user.is_active} -> {request.is_active}"
        user.is_active = request.is_active

    if changes:
        db.commit()
        db.refresh(user)

        # Audit log
        log_action(
            db=db,
            tenant_id=admin_user.tenant_id,
            action=AuditActions.USER_UPDATED,
            resource_type=ResourceTypes.USER,
            actor_user_id=admin_user.user_id,
            resource_id=user.id,
            metadata={"changes": changes, "email": user.email},
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        tenant_id=str(user.tenant_id),
        created_at=user.created_at.isoformat(),
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    admin_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a user (ADMIN only)."""
    user = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == admin_user.tenant_id)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent self-deletion
    if user.id == admin_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    email = user.email
    db.delete(user)
    db.commit()

    # Audit log
    log_action(
        db=db,
        tenant_id=admin_user.tenant_id,
        action=AuditActions.USER_DELETED,
        resource_type=ResourceTypes.USER,
        actor_user_id=admin_user.user_id,
        resource_id=user_id,
        metadata={"email": email},
    )
