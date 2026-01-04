"""Tests for Alembic migrations."""

import subprocess
import sys
from pathlib import Path


def test_alembic_revision_exists() -> None:
    """Test that initial migration file exists."""
    api_dir = Path(__file__).parent.parent
    migrations_dir = api_dir / "alembic" / "versions"
    
    assert migrations_dir.exists(), "Migrations directory should exist"
    
    migration_files = list(migrations_dir.glob("*.py"))
    assert len(migration_files) > 0, "At least one migration should exist"
    
    # Check for initial schema migration
    initial_migration = migrations_dir / "001_initial_schema.py"
    assert initial_migration.exists(), "Initial schema migration should exist"


def test_alembic_config_exists() -> None:
    """Test that alembic.ini configuration exists."""
    api_dir = Path(__file__).parent.parent
    alembic_ini = api_dir / "alembic.ini"
    
    assert alembic_ini.exists(), "alembic.ini should exist"


def test_alembic_env_exists() -> None:
    """Test that alembic env.py exists and imports settings."""
    api_dir = Path(__file__).parent.parent
    env_py = api_dir / "alembic" / "env.py"
    
    assert env_py.exists(), "alembic/env.py should exist"
    
    content = env_py.read_text()
    assert "get_settings" in content, "env.py should import get_settings"
    assert "Base.metadata" in content, "env.py should use Base.metadata"
