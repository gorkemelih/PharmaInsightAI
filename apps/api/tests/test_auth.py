"""Tests for authentication endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_different_hash(self) -> None:
        """Test that hashing same password twice returns different hashes."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # Different salts

    def test_verify_password_success(self) -> None:
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self) -> None:
        """Test password verification with wrong password."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False


class TestJWT:
    """Tests for JWT token functions."""

    def test_create_and_decode_token(self) -> None:
        """Test creating and decoding a JWT token."""
        user_id = str(uuid4())
        tenant_id = str(uuid4())
        role = "ADMIN"

        token = create_access_token(user_id, tenant_id, role)
        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["tenant_id"] == tenant_id
        assert payload["role"] == role

    def test_decode_invalid_token(self) -> None:
        """Test decoding an invalid token returns None."""
        result = decode_access_token("invalid.token.here")
        assert result is None

    def test_decode_expired_token(self) -> None:
        """Test decoding an expired token returns None."""
        from datetime import timedelta
        
        user_id = str(uuid4())
        tenant_id = str(uuid4())
        role = "ADMIN"

        # Create token that's already expired
        token = create_access_token(
            user_id, tenant_id, role,
            expires_delta=timedelta(seconds=-10)
        )
        result = decode_access_token(token)
        assert result is None
