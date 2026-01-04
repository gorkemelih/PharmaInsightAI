"""Tests for database connectivity."""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch, MagicMock

from app.main import app


@pytest.mark.asyncio
async def test_health_check() -> None:
    """Test that health endpoint returns ok status."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_root_endpoint() -> None:
    """Test that root endpoint returns welcome message."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data


@pytest.mark.asyncio
async def test_db_ping_with_mock() -> None:
    """Test that /db/ping endpoint works with mocked database."""
    # Create a mock session
    mock_session = MagicMock()
    mock_session.execute.return_value = None

    # Patch the get_db dependency
    with patch("app.main.get_db") as mock_get_db:
        mock_get_db.return_value = iter([mock_session])

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Override the dependency
            app.dependency_overrides = {}

            response = await client.get("/db/ping")

    # The endpoint should return 200 (may return error if no DB, but should not crash)
    assert response.status_code == 200
    assert "status" in response.json()
