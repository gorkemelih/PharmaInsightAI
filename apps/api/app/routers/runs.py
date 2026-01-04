"""QueryRun management endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import AdminUser, AnalystUser, AuthenticatedUser
from app.db.session import get_db
from app.models.project import Project
from app.models.query_run import QueryRun, QueryStatus
from app.services.audit import AuditActions, ResourceTypes, log_action
from app.services.reports.pdf_report import build_run_report_pdf

# Import schemas from dedicated module
from app.schemas.runs import (
    RunCreate,
    RunResponse,
    PaperResponse,
    SummaryStatusResponse,
    SummaryResponse,
    EvidenceRowResponse,
    RunSummaryResponse,
    FormattedReference,
    CitationWithIndex,
    KeyPointWithIndices,
    ClaimWithIndices,
    SummaryWithIndices,
    SummaryWithReferencesResponse,
    EvidenceDetailResponse,
)

router = APIRouter(tags=["runs"])


def get_project_or_404(
    project_id: UUID,
    tenant_id: UUID,
    db: Session,
) -> Project:
    """Get project by ID or raise 404."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.tenant_id == tenant_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


@router.post(
    "/projects/{project_id}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_run(
    project_id: UUID,
    request: RunCreate,
    current_user: AnalystUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunResponse:
    """Create a new query run and enqueue Celery task."""
    project = get_project_or_404(project_id, current_user.tenant_id, db)

    run = QueryRun(
        project_id=project.id,
        query_text=request.query_text,
        status=QueryStatus.QUEUED,
        max_papers=request.max_papers,
        year_from=request.year_from,
        year_to=request.year_to,
        analysis_mode=request.analysis_mode,
        include_marketing=request.include_marketing,
        language=request.language,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        action=AuditActions.RUN_CREATED,
        resource_type=ResourceTypes.QUERY_RUN,
        actor_user_id=current_user.user_id,
        resource_id=run.id,
        metadata={"query_text": request.query_text[:100], "status": "QUEUED"},
    )

    from app.celery_client import enqueue_run_pipeline
    enqueue_run_pipeline(str(run.id))

    return RunResponse(
        id=str(run.id),
        project_id=str(run.project_id),
        query_text=run.query_text,
        status=run.status.value,
        error_message=run.error_message,
        created_at=run.created_at.isoformat(),
        max_papers=run.max_papers,
        year_from=run.year_from,
        year_to=run.year_to,
        analysis_mode=run.analysis_mode,
        include_marketing=run.include_marketing,
        language=run.language,
    )


@router.get("/projects/{project_id}/runs", response_model=list[RunResponse])
def list_runs(
    project_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[RunResponse]:
    """List all active (non-deleted) runs for a project."""
    project = get_project_or_404(project_id, current_user.tenant_id, db)

    runs = (
        db.query(QueryRun)
        .filter(
            QueryRun.project_id == project.id,
            QueryRun.deleted_at.is_(None),
        )
        .order_by(QueryRun.created_at.desc())
        .all()
    )
    return [
        RunResponse(
            id=str(r.id),
            project_id=str(r.project_id),
            query_text=r.query_text,
            status=r.status.value,
            error_message=r.error_message,
            created_at=r.created_at.isoformat(),
            max_papers=r.max_papers,
            year_from=r.year_from,
            year_to=r.year_to,
            analysis_mode=r.analysis_mode,
            include_marketing=r.include_marketing,
            language=r.language,
        )
        for r in runs
    ]


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(
    run_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunResponse:
    """Get a run by ID."""
    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

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

    return RunResponse(
        id=str(run.id),
        project_id=str(run.project_id),
        query_text=run.query_text,
        status=run.status.value,
        error_message=run.error_message,
        created_at=run.created_at.isoformat(),
        max_papers=run.max_papers,
        year_from=run.year_from,
        year_to=run.year_to,
        analysis_mode=run.analysis_mode,
        include_marketing=run.include_marketing,
        language=run.language,
    )


@router.get("/runs/{run_id}/papers", response_model=list[PaperResponse])
def get_run_papers(
    run_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[PaperResponse]:
    """Get all papers for a run."""
    from app.models.evidence import Evidence
    from app.models.paper import Paper

    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

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

    papers = (
        db.query(Paper)
        .join(Evidence, Evidence.paper_id == Paper.id)
        .filter(Evidence.run_id == run_id)
        .all()
    )

    return [
        PaperResponse(
            id=str(p.id),
            title=p.title,
            abstract=p.abstract,
            journal=p.journal,
            year=p.year,
            authors=p.authors or [],
            pmid=p.pmid,
            doi=p.doi,
            url=p.url,
            source=p.source,
        )
        for p in papers
    ]


@router.get("/runs/{run_id}/summaries", response_model=list[SummaryStatusResponse])
def get_run_summaries(
    run_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[SummaryStatusResponse]:
    """Get summary status for all papers in a run."""
    from app.models.paper_summary import PaperSummary
    from app.models.paper import Paper

    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

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

    summaries = (
        db.query(PaperSummary, Paper)
        .join(Paper, Paper.id == PaperSummary.paper_id)
        .filter(PaperSummary.run_id == run_id)
        .all()
    )

    return [
        SummaryStatusResponse(
            paper_id=str(s.paper_id),
            title=p.title,
            status=s.status,
            error_message=s.error_message,
        )
        for s, p in summaries
    ]


@router.get("/papers/{paper_id}/summary", response_model=SummaryResponse)
def get_paper_summary(
    paper_id: UUID,
    run_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> SummaryResponse:
    """Get summary for a specific paper in a run."""
    from app.models.paper_summary import PaperSummary

    summary = (
        db.query(PaperSummary)
        .filter(PaperSummary.paper_id == paper_id, PaperSummary.run_id == run_id)
        .first()
    )

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found",
        )

    if summary.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found",
        )

    return SummaryResponse(
        paper_id=str(summary.paper_id),
        run_id=str(summary.run_id),
        status=summary.status,
        model=summary.model,
        summary=summary.summary_json,
        error_message=summary.error_message,
    )


@router.get("/runs/{run_id}/evidence-table", response_model=list[EvidenceRowResponse])
def get_evidence_table(
    run_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[EvidenceRowResponse]:
    """Get evidence table for a run."""
    from app.models.evidence_row import EvidenceRow

    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

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

    rows = db.query(EvidenceRow).filter(EvidenceRow.run_id == run_id).all()

    return [
        EvidenceRowResponse(
            paper_id=str(r.paper_id),
            citation=r.row_json.get("citation", {}),
            study_type=r.row_json.get("study_type"),
            population=r.row_json.get("population"),
            intervention=r.row_json.get("intervention"),
            comparator=r.row_json.get("comparator"),
            outcomes=r.row_json.get("outcomes", []),
            key_findings=r.row_json.get("key_findings", []),
            limitations=r.row_json.get("limitations", []),
        )
        for r in rows
    ]


@router.get("/runs/{run_id}/summary", response_model=RunSummaryResponse)
def get_run_summary(
    run_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunSummaryResponse:
    """Get run synthesis summary."""
    from app.models.run_summary import RunSummary

    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

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

    summary = db.query(RunSummary).filter(RunSummary.run_id == run_id).first()

    if not summary:
        return RunSummaryResponse(
            run_id=str(run_id),
            status="PENDING",
            model="",
            summary=None,
            error_message=None,
        )

    return RunSummaryResponse(
        run_id=str(summary.run_id),
        status=summary.status,
        model=summary.model,
        summary=summary.summary_json,
        error_message=summary.error_message,
    )


@router.post("/runs/{run_id}/summary/retry")
def retry_run_summary(
    run_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Retry failed run synthesis (admin only)."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

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

    from app.celery_client import celery_app
    celery_app.send_task("app.tasks.build_evidence_table", args=[str(run_id)])

    return {"message": "Retry triggered", "run_id": str(run_id)}


def _format_reference(paper, index: int) -> FormattedReference:
    """Format a paper as a reference string."""
    parts = []

    authors = paper.authors or []
    if authors:
        if len(authors) == 1:
            parts.append(authors[0])
        elif len(authors) == 2:
            parts.append(f"{authors[0]} & {authors[1]}")
        else:
            parts.append(f"{authors[0]} et al.")

    if paper.year:
        parts.append(f"({paper.year})")

    if paper.journal:
        parts.append(paper.journal)

    ids = []
    if paper.pmid:
        ids.append(f"PMID:{paper.pmid}")
    if paper.doi:
        ids.append(f"DOI:{paper.doi}")

    formatted = " ".join(parts)
    if ids:
        formatted += " — " + ", ".join(ids)

    link = None
    if paper.pmid:
        link = f"https://pubmed.ncbi.nlm.nih.gov/{paper.pmid}/"
    elif paper.doi:
        link = f"https://doi.org/{paper.doi}"
    elif paper.url:
        link = paper.url

    return FormattedReference(
        index=index,
        paper_id=str(paper.id),
        formatted=formatted or paper.title[:50],
        link=link,
    )


@router.get("/runs/{run_id}/summary-with-references", response_model=SummaryWithReferencesResponse)
def get_summary_with_references(
    run_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> SummaryWithReferencesResponse:
    """Get run summary with numbered references."""
    from app.models.run_summary import RunSummary
    from app.models.paper import Paper

    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.tenant_id == current_user.tenant_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    summary = db.query(RunSummary).filter(RunSummary.run_id == run_id).first()

    if not summary or not summary.summary_json:
        return SummaryWithReferencesResponse(
            run_id=str(run_id),
            status=summary.status if summary else "PENDING",
            summary=None,
            references=[],
            error_message=summary.error_message if summary else None,
        )

    summary_data = summary.summary_json

    cited_paper_ids: list[str] = []
    seen_ids: set[str] = set()

    def collect_citations(items: list[dict]):
        for item in items:
            for cit in item.get("citations", []):
                pid = cit.get("paper_id")
                if pid and pid not in seen_ids:
                    cited_paper_ids.append(pid)
                    seen_ids.add(pid)

    collect_citations(summary_data.get("key_points", []))
    collect_citations(summary_data.get("contradictions", []))
    collect_citations(summary_data.get("claims_draft", []))

    papers = {}
    if cited_paper_ids:
        paper_records = (
            db.query(Paper)
            .filter(Paper.id.in_([UUID(pid) for pid in cited_paper_ids if pid]))
            .all()
        )
        papers = {str(p.id): p for p in paper_records}

    paper_id_to_index: dict[str, int] = {}
    references: list[FormattedReference] = []
    for i, pid in enumerate(cited_paper_ids, 1):
        paper_id_to_index[pid] = i
        paper = papers.get(pid)
        if paper:
            references.append(_format_reference(paper, i))
        else:
            references.append(FormattedReference(index=i, paper_id=pid, formatted=f"[Paper {pid[:8]}]", link=None))

    def convert_citations(items: list[dict]) -> list[KeyPointWithIndices]:
        result = []
        for item in items:
            indices = []
            for cit in item.get("citations", []):
                pid = cit.get("paper_id")
                if pid and pid in paper_id_to_index:
                    indices.append(CitationWithIndex(index=paper_id_to_index[pid]))
            result.append(KeyPointWithIndices(text=item.get("text", ""), citations=indices))
        return result

    def convert_claims(items: list[dict]) -> list[ClaimWithIndices]:
        result = []
        for item in items:
            indices = []
            for cit in item.get("citations", []):
                pid = cit.get("paper_id")
                if pid and pid in paper_id_to_index:
                    indices.append(CitationWithIndex(index=paper_id_to_index[pid]))
            result.append(ClaimWithIndices(
                claim=item.get("claim", ""),
                allowed=item.get("allowed", False),
                rationale=item.get("rationale", ""),
                citations=indices,
            ))
        return result

    summary_with_indices = SummaryWithIndices(
        tldr=summary_data.get("tldr", ""),
        key_points=convert_citations(summary_data.get("key_points", [])),
        consensus_level=summary_data.get("consensus_level", "low"),
        contradictions=convert_citations(summary_data.get("contradictions", [])),
        gaps=summary_data.get("gaps", []),
        safety_notes=summary_data.get("safety_notes", []),
        claims_draft=convert_claims(summary_data.get("claims_draft", [])),
    )

    return SummaryWithReferencesResponse(
        run_id=str(run_id),
        status=summary.status,
        summary=summary_with_indices,
        references=references,
        error_message=summary.error_message,
    )


@router.get("/runs/{run_id}/evidence/{paper_id}", response_model=EvidenceDetailResponse)
def get_evidence_detail(
    run_id: UUID,
    paper_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> EvidenceDetailResponse:
    """Get detailed evidence for a specific paper in a run."""
    from app.models.evidence_row import EvidenceRow
    from app.models.paper import Paper

    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    project = (
        db.query(Project)
        .filter(Project.id == run.project_id, Project.tenant_id == current_user.tenant_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    evidence_row = (
        db.query(EvidenceRow)
        .filter(EvidenceRow.run_id == run_id, EvidenceRow.paper_id == paper_id)
        .first()
    )

    evidence_snippets = []
    key_findings = []
    study_type = None

    if evidence_row and evidence_row.row_json:
        raw_snippets = evidence_row.row_json.get("evidence_snippets", [])
        for snippet in raw_snippets:
            if isinstance(snippet, dict):
                evidence_snippets.append(snippet.get("quote", ""))
            elif isinstance(snippet, str):
                evidence_snippets.append(snippet)
        key_findings = evidence_row.row_json.get("key_findings", [])
        study_type = evidence_row.row_json.get("study_type")

    return EvidenceDetailResponse(
        paper_id=str(paper.id),
        title=paper.title,
        authors=paper.authors or [],
        year=paper.year,
        journal=paper.journal,
        pmid=paper.pmid,
        doi=paper.doi,
        url=paper.url,
        evidence_snippets=evidence_snippets,
        key_findings=key_findings,
        study_type=study_type,
    )


@router.get("/runs/{run_id}/report.pdf")
def get_run_report_pdf(
    run_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Generate and download PDF report for a run."""
    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    project = db.query(Project).filter(
        Project.id == run.project_id,
        Project.tenant_id == current_user.tenant_id,
    ).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    try:
        pdf_bytes = build_run_report_pdf(run_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        import logging
        logging.error(f"PDF generation failed for run {run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF report",
        )

    filename = f"pharmainsightai-run-{run_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    run_id: UUID,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Soft-delete a run."""
    run = db.query(QueryRun).filter(
        QueryRun.id == run_id,
        QueryRun.deleted_at.is_(None),
    ).first()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    project = db.query(Project).filter(
        Project.id == run.project_id,
        Project.tenant_id == current_user.tenant_id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    run.deleted_at = datetime.now(timezone.utc)
    run.deleted_by = current_user.user_id
    db.commit()

    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        action=AuditActions.RUN_DELETED,
        resource_type=ResourceTypes.RUN,
        actor_user_id=current_user.user_id,
        resource_id=run_id,
        metadata={"query_text": run.query_text[:100], "soft_delete": True},
    )


@router.post("/runs/{run_id}/restore", response_model=RunResponse)
def restore_run(
    run_id: UUID,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> RunResponse:
    """Restore a soft-deleted run."""
    run = db.query(QueryRun).filter(QueryRun.id == run_id).first()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    project = db.query(Project).filter(
        Project.id == run.project_id,
        Project.tenant_id == current_user.tenant_id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if run.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run is not deleted",
        )

    run.deleted_at = None
    run.deleted_by = None
    db.commit()
    db.refresh(run)

    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        action=AuditActions.RUN_UPDATED,
        resource_type=ResourceTypes.RUN,
        actor_user_id=current_user.user_id,
        resource_id=run_id,
        metadata={"action": "restored"},
    )

    return RunResponse(
        id=str(run.id),
        project_id=str(run.project_id),
        query_text=run.query_text,
        status=run.status.value,
        error_message=run.error_message,
        created_at=run.created_at.isoformat(),
        max_papers=run.max_papers,
        year_from=run.year_from,
        year_to=run.year_to,
        analysis_mode=run.analysis_mode,
        include_marketing=run.include_marketing,
        language=run.language,
    )
