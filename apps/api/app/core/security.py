"""Security utilities for password hashing and JWT handling."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import Response

from app.config import get_settings

settings = get_settings()


# Password Hashing with bcrypt
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


# JWT Token Handling
def create_access_token(
    user_id: str,
    tenant_id: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_expire_minutes)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# Cookie Helpers
def set_auth_cookie(response: Response, token: str) -> None:
    """Set the authentication cookie on the response."""
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=settings.cookie_httponly,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Clear the authentication cookie."""
    response.delete_cookie(
        key=settings.cookie_name,
        path="/",
        httponly=settings.cookie_httponly,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )
