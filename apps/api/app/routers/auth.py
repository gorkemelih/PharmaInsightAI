"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.deps import AuthenticatedUser
from app.core.security import (
    clear_auth_cookie,
    create_access_token,
    set_auth_cookie,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.services.audit import AuditActions, ResourceTypes, log_action

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response."""

    message: str
    user_id: str
    email: str
    role: str


class MeResponse(BaseModel):
    """Current user response."""

    id: str
    email: str
    role: str
    tenant_id: str
    is_active: bool


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    """Authenticate user and set JWT cookie."""
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        # Log failed attempt
        if user:
            log_action(
                db=db,
                tenant_id=user.tenant_id,
                action=AuditActions.LOGIN_FAILURE,
                resource_type=ResourceTypes.AUTH,
                actor_user_id=user.id,
                metadata={"email": request.email, "reason": "invalid_password"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        log_action(
            db=db,
            tenant_id=user.tenant_id,
            action=AuditActions.LOGIN_FAILURE,
            resource_type=ResourceTypes.AUTH,
            actor_user_id=user.id,
            metadata={"email": request.email, "reason": "user_inactive"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # Create JWT token
    token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role.value,
    )

    # Set cookie
    set_auth_cookie(response, token)

    # Log success
    log_action(
        db=db,
        tenant_id=user.tenant_id,
        action=AuditActions.LOGIN_SUCCESS,
        resource_type=ResourceTypes.AUTH,
        actor_user_id=user.id,
        metadata={"email": request.email},
    )

    return LoginResponse(
        message="Login successful",
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
    )


@router.post("/logout")
def logout(
    response: Response,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Clear authentication cookie."""
    # Log logout
    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        action=AuditActions.LOGOUT,
        resource_type=ResourceTypes.AUTH,
        actor_user_id=current_user.user_id,
        metadata={},
    )

    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=MeResponse)
def get_current_user_info(current_user: AuthenticatedUser) -> MeResponse:
    """Get current authenticated user information."""
    if not current_user.user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return MeResponse(
        id=str(current_user.user.id),
        email=current_user.user.email,
        role=current_user.user.role.value,
        tenant_id=str(current_user.user.tenant_id),
        is_active=current_user.user.is_active,
    )
