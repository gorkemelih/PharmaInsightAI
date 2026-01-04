"""Dashboard endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import AuthenticatedUser
from app.db.session import get_db
from app.models.project import Project
from app.models.query_run import QueryRun, QueryStatus
from app.models.paper_summary import PaperSummary

router = APIRouter(tags=["dashboard"])


class DashboardSummary(BaseModel):
    """Dashboard summary statistics."""

    total_projects: int
    total_papers: int
    total_runs: int
    pending_runs: int


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> DashboardSummary:
    """Get dashboard summary stats for current tenant."""
    tenant_id = current_user.tenant_id

    # Count projects
    total_projects = db.query(func.count(Project.id)).filter(
        Project.tenant_id == tenant_id,
        Project.deleted_at.is_(None),
    ).scalar() or 0

    # Count unique papers via EvidenceRow (papers analyzed)
    from app.models.evidence_row import EvidenceRow
    
    total_papers = (
        db.query(func.count(func.distinct(EvidenceRow.paper_id)))
        .join(QueryRun, EvidenceRow.run_id == QueryRun.id)
        .join(Project, QueryRun.project_id == Project.id)
        .filter(
            Project.tenant_id == tenant_id,
            Project.deleted_at.is_(None),
            QueryRun.deleted_at.is_(None),
        )
        .scalar()
    ) or 0

    # Count runs (only for non-deleted projects)
    total_runs = (
        db.query(func.count(QueryRun.id))
        .join(Project, QueryRun.project_id == Project.id)
        .filter(
            Project.tenant_id == tenant_id,
            Project.deleted_at.is_(None),
            QueryRun.deleted_at.is_(None),
        )
        .scalar()
    ) or 0

    # Count pending runs (QUEUED or RUNNING)
    pending_runs = (
        db.query(func.count(QueryRun.id))
        .join(Project, QueryRun.project_id == Project.id)
        .filter(
            Project.tenant_id == tenant_id,
            Project.deleted_at.is_(None),
            QueryRun.deleted_at.is_(None),
            QueryRun.status.in_([QueryStatus.QUEUED, QueryStatus.RUNNING]),
        )
        .scalar()
    ) or 0

    return DashboardSummary(
        total_projects=total_projects,
        total_papers=total_papers,
        total_runs=total_runs,
        pending_runs=pending_runs,
    )


class RecentRunResponse(BaseModel):
    """Recent run response."""

    id: str
    query_text: str
    status: str
    paper_count: int
    created_at: str
    project_name: str


@router.get("/runs/recent", response_model=list[RecentRunResponse])
def get_recent_runs(
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 10,
) -> list[RecentRunResponse]:
    """Get recent runs across all projects for current tenant."""
    tenant_id = current_user.tenant_id

    # Get recent runs with project info
    runs = (
        db.query(QueryRun, Project.name.label("project_name"))
        .join(Project, QueryRun.project_id == Project.id)
        .filter(
            Project.tenant_id == tenant_id,
            Project.deleted_at.is_(None),
            QueryRun.deleted_at.is_(None),
        )
        .order_by(QueryRun.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for run, project_name in runs:
        # Count papers for this run via paper_summaries
        paper_count = db.query(func.count(PaperSummary.id)).filter(
            PaperSummary.run_id == run.id
        ).scalar() or 0

        result.append(
            RecentRunResponse(
                id=str(run.id),
                query_text=run.query_text,
                status=run.status.value if hasattr(run.status, 'value') else str(run.status),
                paper_count=paper_count,
                created_at=run.created_at.isoformat() if run.created_at else "",
                project_name=project_name,
            )
        )

    return result
