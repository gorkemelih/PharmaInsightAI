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


def enqueue_summarize_paper(run_id: str, paper_id: str) -> None:
    """Enqueue the summarize_paper task."""
    celery_app.send_task("app.tasks.summarize_paper", args=[run_id, paper_id])
