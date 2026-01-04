"""Paper ingestion service - saves papers to database."""

from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from app.integrations.literature.base import PaperCandidate
from app.models.paper import Paper
from app.models.evidence import Evidence

logger = structlog.get_logger(__name__)


def ingest_papers(
    db: Session,
    run_id: UUID,
    tenant_id: UUID,
    papers: list[PaperCandidate],
) -> int:
    """Ingest papers into the database and create evidence links.

    Args:
        db: Database session
        run_id: QueryRun ID
        tenant_id: Tenant ID
        papers: List of PaperCandidate objects

    Returns:
        Number of papers ingested
    """
    ingested_count = 0

    for paper_candidate in papers:
        try:
            # Try to find existing paper by DOI or PMID
            existing_paper = None
            matched_by = None

            if paper_candidate.doi:
                existing_paper = (
                    db.query(Paper)
                    .filter(Paper.tenant_id == tenant_id, Paper.doi == paper_candidate.doi)
                    .first()
                )
                matched_by = "doi"

            if not existing_paper and paper_candidate.pmid:
                existing_paper = (
                    db.query(Paper)
                    .filter(Paper.tenant_id == tenant_id, Paper.pmid == paper_candidate.pmid)
                    .first()
                )
                matched_by = "pmid"

            if existing_paper:
                # Update existing paper with potentially new metadata
                paper = existing_paper
                _update_paper_metadata(paper, paper_candidate)
            else:
                # Create new paper
                matched_by = "new"
                paper = Paper(
                    tenant_id=tenant_id,
                    pmid=paper_candidate.pmid,
                    doi=paper_candidate.doi,
                    title=paper_candidate.title,
                    abstract=paper_candidate.abstract,
                    journal=paper_candidate.journal,
                    year=paper_candidate.year,
                    authors=paper_candidate.authors,
                    url=paper_candidate.get_url(),
                    source=paper_candidate.raw_source,
                )
                db.add(paper)
                db.flush()  # Get the paper ID

            # Check if evidence already exists for this run-paper pair
            existing_evidence = (
                db.query(Evidence)
                .filter(Evidence.run_id == run_id, Evidence.paper_id == paper.id)
                .first()
            )

            if not existing_evidence:
                # Create evidence linking run to paper
                evidence = Evidence(
                    run_id=run_id,
                    paper_id=paper.id,
                    evidence_json={
                        "source": paper_candidate.raw_source,
                        "matched_by": matched_by,
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                db.add(evidence)

            ingested_count += 1

        except Exception as e:
            logger.error(
                "paper_ingestion_error",
                title=paper_candidate.title[:50],
                error=str(e),
            )
            continue

    db.commit()
    logger.info("papers_ingested", run_id=str(run_id), count=ingested_count)
    return ingested_count


def _update_paper_metadata(paper: Paper, candidate: PaperCandidate) -> None:
    """Update paper metadata if new data is better."""
    # Update abstract if we didn't have one
    if not paper.abstract and candidate.abstract:
        paper.abstract = candidate.abstract

    # Update journal if we didn't have one
    if not paper.journal and candidate.journal:
        paper.journal = candidate.journal

    # Update year if we didn't have one
    if not paper.year and candidate.year:
        paper.year = candidate.year

    # Update authors if we have more
    if candidate.authors and len(candidate.authors) > len(paper.authors or []):
        paper.authors = candidate.authors

    # Update DOI if we didn't have one
    if not paper.doi and candidate.doi:
        paper.doi = candidate.doi

    # Update PMID if we didn't have one
    if not paper.pmid and candidate.pmid:
        paper.pmid = candidate.pmid
