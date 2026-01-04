"""Database engine configuration."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import get_settings

settings = get_settings()


def create_db_engine() -> Engine:
    """Create SQLAlchemy engine from settings."""
    return create_engine(
        settings.database_url,
        echo=settings.environment == "development",
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


engine = create_db_engine()
