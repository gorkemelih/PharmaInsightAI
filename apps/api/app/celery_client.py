"""Celery client for enqueuing tasks from API."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

# Create Celery app instance for sending tasks
celery_app = Celery(
    "pharmainsight",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


def enqueue_run_pipeline(run_id: str) -> None:
    """Enqueue the run_pipeline task."""
    celery_app.send_task("app.tasks.run_pipeline", args=[run_id])
