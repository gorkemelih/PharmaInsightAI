"""FastAPI dependencies for authentication and authorization."""

from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

settings = get_settings()


class CurrentUser:
    """Container for current authenticated user info from JWT."""

    def __init__(
        self, user_id: UUID, tenant_id: UUID, role: UserRole, user: User | None = None
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.user = user


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Cookie(alias="pharmainsight_token")] = None,
) -> CurrentUser:
    """Extract and validate current user from JWT cookie."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tenant_id"])
    role = UserRole(payload["role"])

    # Optionally fetch full user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return CurrentUser(user_id=user_id, tenant_id=tenant_id, role=role, user=user)


def require_user() -> CurrentUser:
    """Dependency that requires authenticated user."""
    return Depends(get_current_user)


def require_role(*allowed_roles: UserRole):
    """Dependency factory that requires specific roles."""

    def role_checker(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        # ADMIN can do anything
        if current_user.role == UserRole.ADMIN:
            return current_user

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role.value} not authorized for this action",
            )
        return current_user

    return Depends(role_checker)


# Type aliases for dependency injection
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
AdminUser = Annotated[CurrentUser, require_role(UserRole.ADMIN)]
AnalystUser = Annotated[CurrentUser, require_role(UserRole.ADMIN, UserRole.ANALYST)]
