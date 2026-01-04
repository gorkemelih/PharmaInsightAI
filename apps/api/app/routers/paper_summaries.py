"""On-demand paper summary generation endpoint."""

import os
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import AuthenticatedUser
from app.db.session import get_db
from app.models.project import Project
from app.models.query_run import QueryRun
from app.models.paper import Paper
from app.models.paper_summary import PaperSummary, SummaryStatus
from app.celery_client import enqueue_summarize_paper

router = APIRouter(tags=["paper-summaries"])


class PaperSummaryResponse(BaseModel):
    """Response for paper summary."""
    
    id: str
    paper_id: str
    run_id: str
    status: str
    summary_json: dict[str, Any] | None
    created_at: str
    cached: bool = False


@router.post(
    "/runs/{run_id}/papers/{paper_id}/summary",
    response_model=PaperSummaryResponse,
)
def generate_paper_summary(
    run_id: UUID,
    paper_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> PaperSummaryResponse:
    """Generate or return cached summary for a paper in a run."""
    
    # Verify run exists and user has access
    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    
    # Verify tenant ownership via project
    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.tenant_id == current_user.tenant_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    
    # Check if paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    
    # Check for existing summary (cache hit)
    existing = (
        db.query(PaperSummary)
        .filter(
            PaperSummary.run_id == run_id,
            PaperSummary.paper_id == paper_id,
        )
        .first()
    )
    
    if existing and existing.status == SummaryStatus.DONE and existing.summary_json:
        # Return cached summary
        return PaperSummaryResponse(
            id=str(existing.id),
            paper_id=str(existing.paper_id),
            run_id=str(existing.run_id),
            status=existing.status.value,
            summary_json=existing.summary_json,
            created_at=existing.created_at.isoformat(),
            cached=True,
        )
    
    if existing and existing.status in [SummaryStatus.QUEUED, SummaryStatus.RUNNING]:
        # Already processing
        return PaperSummaryResponse(
            id=str(existing.id),
            paper_id=str(existing.paper_id),
            run_id=str(existing.run_id),
            status=existing.status.value,
            summary_json=existing.summary_json,
            created_at=existing.created_at.isoformat(),
            cached=False,
        )

    # Need to generate (or retry)
    if existing:
        summary_record = existing
        summary_record.status = SummaryStatus.QUEUED
        # Clear previous error if any
        summary_record.error_message = None
    else:
        summary_record = PaperSummary(
            tenant_id=current_user.tenant_id,
            run_id=run_id,
            paper_id=paper_id,
            model=os.getenv("LLM_MODEL", "gemini-3-flash"),
            status=SummaryStatus.QUEUED,
            summary_json=None,
        )
        db.add(summary_record)
    
    db.commit()
    db.refresh(summary_record)
    
    # Enqueue Celery task
    try:
        enqueue_summarize_paper(str(run_id), str(paper_id))
    except Exception as e:
        # If queuing fails, mark as failed
        summary_record.status = SummaryStatus.FAILED
        summary_record.error_message = f"Failed to enqueue task: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start background process",
        )
    
    return PaperSummaryResponse(
        id=str(summary_record.id),
        paper_id=str(summary_record.paper_id),
        run_id=str(summary_record.run_id),
        status=summary_record.status.value,
        summary_json=summary_record.summary_json,
        created_at=summary_record.created_at.isoformat(),
        cached=False,
    )


@router.get(
    "/runs/{run_id}/papers/{paper_id}/summary",
    response_model=PaperSummaryResponse,
)
def get_paper_summary(
    run_id: UUID,
    paper_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> PaperSummaryResponse:
    """Get existing summary for a paper (404 if not yet generated)."""
    
    # Verify run exists and user has access
    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    
    # Verify tenant ownership
    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.tenant_id == current_user.tenant_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    
    # Get summary
    summary = (
        db.query(PaperSummary)
        .filter(
            PaperSummary.run_id == run_id,
            PaperSummary.paper_id == paper_id,
        )
        .first()
    )
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not yet generated. Use POST to generate.",
        )
    
    return PaperSummaryResponse(
        id=str(summary.id),
        paper_id=str(summary.paper_id),
        run_id=str(summary.run_id),
        status=summary.status.value,
        summary_json=summary.summary_json,
        created_at=summary.created_at.isoformat(),
        cached=True,
    )
