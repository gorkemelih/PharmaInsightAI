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

import google.generativeai as genai

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


def generate_paper_summary_llm(paper: Paper, language: str = "en") -> dict[str, Any]:
    """Generate summary for a single paper using LLM."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not configured")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    
    # Build prompt
    lang_instruction = "Respond in Turkish (Türkçe)." if language == "tr" else "Respond in English."
    
    prompt = f"""Analyze this scientific paper and provide a structured summary.

Title: {paper.title}
Authors: {', '.join(paper.authors[:5]) if paper.authors else 'Unknown'}
Year: {paper.year or 'Unknown'}
Journal: {paper.journal or 'Unknown'}
Abstract: {paper.abstract or 'No abstract available'}

{lang_instruction}

Provide a JSON response with these fields:
{{
  "study_type": "e.g., RCT, meta-analysis, cohort study",
  "sample_size": "if mentioned",
  "key_findings": ["finding1", "finding2"],
  "methodology": "brief description",
  "limitations": ["limitation1"],
  "clinical_relevance": "summary of clinical implications",
  "quality_score": "low/medium/high based on methodology",
  "pico": {{
    "population": "...",
    "intervention": "...",
    "comparison": "...",
    "outcome": "..."
  }}
}}

Return ONLY valid JSON, no markdown formatting."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean markdown if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        import json
        return json.loads(text)
    except Exception as e:
        return {
            "error": str(e),
            "study_type": "unknown",
            "key_findings": ["Summary generation failed"],
        }


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
    
    # Generate new summary
    language = getattr(run, 'language', 'en') or 'en'
    
    try:
        summary_json = generate_paper_summary_llm(paper, language)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}",
        )
    
    # Store summary
    if existing:
        existing.summary_json = summary_json
        existing.status = SummaryStatus.DONE
        db.commit()
        db.refresh(existing)
        summary_record = existing
    else:
        summary_record = PaperSummary(
            tenant_id=current_user.tenant_id,
            run_id=run_id,
            paper_id=paper_id,
            model=os.getenv("LLM_MODEL", "gemini-2.0-flash-lite"),
            status=SummaryStatus.DONE,
            summary_json=summary_json,
        )
        db.add(summary_record)
        db.commit()
        db.refresh(summary_record)
    
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
