"""Database session management for worker."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.celery_app import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get a new database session for worker tasks."""
    return SessionLocal()
