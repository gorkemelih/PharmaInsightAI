"""Celery tasks for background processing."""

import os
from datetime import datetime, timezone
from uuid import UUID

import structlog

from app.celery_app import celery_app
from app.db import get_db_session

logger = structlog.get_logger(__name__)

# Max papers to summarize per run (rate limiting)
MAX_SUMMARIES_PER_RUN = 20


@celery_app.task(name="app.tasks.run_pipeline", bind=True)
def run_pipeline(self, run_id: str) -> dict:
    """Execute the literature search pipeline for a query run."""
    db = get_db_session()

    try:
        from app.models import QueryRun, QueryStatus, Project, Paper, Evidence, AuditLog, PaperSummary, SummaryStatus

        # Get the run
        run = db.query(QueryRun).filter(QueryRun.id == UUID(run_id)).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        # Get project for tenant_id
        project = db.query(Project).filter(Project.id == run.project_id).first()
        if not project:
            raise ValueError(f"Project not found for run {run_id}")

        tenant_id = project.tenant_id

        # Update status to RUNNING
        run.status = QueryStatus.RUNNING
        db.commit()
        _log_status_change(db, run, tenant_id, "QUEUED", "RUNNING")

        logger.info("pipeline_started", run_id=run_id, query=run.query_text)

        # Perform literature search with run parameters
        from app.integrations.literature import LiteratureSearchService

        service = LiteratureSearchService(
            ncbi_api_key=os.getenv("NCBI_API_KEY"),
            ncbi_tool=os.getenv("NCBI_TOOL", "pharmainsightai"),
            ncbi_email=os.getenv("NCBI_EMAIL", "admin@pharmainsight.io"),
        )

        papers = service.search(
            run.query_text,
            limit=run.max_papers,
            year_from=run.year_from,
            year_to=run.year_to,
        )
        logger.info("papers_found", run_id=run_id, count=len(papers))

        # Ingest papers to database
        ingested_paper_ids = []
        for paper_candidate in papers:
            try:
                # Try to find existing paper by DOI or PMID
                existing_paper = None
                matched_by = "new"

                if paper_candidate.doi:
                    existing_paper = (
                        db.query(Paper)
                        .filter(Paper.tenant_id == tenant_id, Paper.doi == paper_candidate.doi)
                        .first()
                    )
                    if existing_paper:
                        matched_by = "doi"

                if not existing_paper and paper_candidate.pmid:
                    existing_paper = (
                        db.query(Paper)
                        .filter(Paper.tenant_id == tenant_id, Paper.pmid == paper_candidate.pmid)
                        .first()
                    )
                    if existing_paper:
                        matched_by = "pmid"

                if existing_paper:
                    paper = existing_paper
                    # Update metadata if better
                    if not paper.abstract and paper_candidate.abstract:
                        paper.abstract = paper_candidate.abstract
                    if not paper.journal and paper_candidate.journal:
                        paper.journal = paper_candidate.journal
                    if not paper.year and paper_candidate.year:
                        paper.year = paper_candidate.year
                else:
                    # Create new paper
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
                    db.flush()

                # Check if evidence already exists
                existing_evidence = (
                    db.query(Evidence)
                    .filter(Evidence.run_id == UUID(run_id), Evidence.paper_id == paper.id)
                    .first()
                )

                if not existing_evidence:
                    evidence = Evidence(
                        run_id=UUID(run_id),
                        paper_id=paper.id,
                        evidence_json={
                            "source": paper_candidate.raw_source,
                            "matched_by": matched_by,
                            "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                    db.add(evidence)

                ingested_paper_ids.append(str(paper.id))

            except Exception as e:
                logger.error("paper_ingestion_error", error=str(e))
                continue

        db.commit()

        # Determine if we should generate per-paper summaries
        # synthesis mode = skip per-paper (on-demand only)
        # per_paper mode = generate with cap
        analysis_mode = getattr(run, 'analysis_mode', 'synthesis') or 'synthesis'
        deep_dive_cap = int(os.getenv("DEEP_DIVE_MAX_PAPER_SUMMARIES", "10"))
        
        summaries_queued = 0
        
        if analysis_mode == "per_paper":
            # Deep Dive mode: summarize top N papers (capped)
            llm_model = os.getenv("LLM_MODEL", "gemini-2.0-flash-lite")
            papers_to_summarize = ingested_paper_ids[:min(deep_dive_cap, MAX_SUMMARIES_PER_RUN)]
            
            logger.info(
                "deep_dive_mode",
                run_id=run_id,
                total_papers=len(ingested_paper_ids),
                summarizing=len(papers_to_summarize),
                cap=deep_dive_cap,
            )
            
            for idx, paper_id in enumerate(papers_to_summarize):
                try:
                    existing_summary = (
                        db.query(PaperSummary)
                        .filter(PaperSummary.run_id == UUID(run_id), PaperSummary.paper_id == UUID(paper_id))
                        .first()
                    )
                    
                    if not existing_summary:
                        summary_record = PaperSummary(
                            tenant_id=tenant_id,
                            paper_id=UUID(paper_id),
                            run_id=UUID(run_id),
                            model=llm_model,
                            status=SummaryStatus.QUEUED,
                        )
                        db.add(summary_record)
                        db.flush()
                        
                        # Enqueue task with staggered delay
                        delay_seconds = idx * 5
                        summarize_paper.apply_async(
                            args=[run_id, paper_id],
                            countdown=delay_seconds
                        )
                        summaries_queued += 1
                        
                except Exception as e:
                    logger.error("summary_queue_error", paper_id=paper_id, error=str(e))
                    continue
            
            db.commit()
        else:
            # Synthesis mode: skip per-paper summaries (1 LLM call total)
            logger.info(
                "synthesis_mode",
                run_id=run_id,
                total_papers=len(ingested_paper_ids),
                message="Quick synthesis: 1 LLM call, no per-paper summaries",
            )
            # Trigger direct synthesis immediately
            quick_synthesis_direct.apply_async(args=[run_id], countdown=2)

        # Mark as DONE
        run.status = QueryStatus.DONE
        db.commit()
        _log_status_change(db, run, tenant_id, "RUNNING", "DONE")

        logger.info(
            "pipeline_completed",
            run_id=run_id,
            papers_ingested=len(ingested_paper_ids),
            summaries_queued=summaries_queued,
            analysis_mode=analysis_mode,
        )

        return {
            "status": "success",
            "run_id": run_id,
            "papers_found": len(papers),
            "papers_ingested": len(ingested_paper_ids),
            "summaries_queued": summaries_queued,
            "analysis_mode": analysis_mode,
        }

    except Exception as e:
        logger.error("pipeline_error", run_id=run_id, error=str(e))
        db.rollback()

        # Mark as FAILED
        try:
            from app.models import QueryRun, QueryStatus, Project

            run = db.query(QueryRun).filter(QueryRun.id == UUID(run_id)).first()
            if run:
                project = db.query(Project).filter(Project.id == run.project_id).first()
                run.status = QueryStatus.FAILED
                run.error_message = str(e)[:500]
                db.commit()

                if project:
                    _log_status_change(db, run, project.tenant_id, "RUNNING", "FAILED", error=str(e))
        except Exception as e2:
            logger.error("failed_to_mark_failed", error=str(e2))

        return {
            "status": "error",
            "run_id": run_id,
            "error": str(e),
        }

    finally:
        db.close()


@celery_app.task(name="app.tasks.summarize_paper", bind=True, max_retries=2)
def summarize_paper(self, run_id: str, paper_id: str) -> dict:
    """Generate LLM summary for a paper."""
    db = get_db_session()

    try:
        from app.models import Paper, PaperSummary, SummaryStatus

        # Get summary record
        summary = (
            db.query(PaperSummary)
            .filter(PaperSummary.run_id == UUID(run_id), PaperSummary.paper_id == UUID(paper_id))
            .first()
        )
        
        if not summary:
            logger.warning("summary_not_found", run_id=run_id, paper_id=paper_id)
            return {"status": "error", "error": "Summary record not found"}

        # Get paper
        paper = db.query(Paper).filter(Paper.id == UUID(paper_id)).first()
        if not paper:
            summary.status = SummaryStatus.FAILED
            summary.error_message = "Paper not found"
            db.commit()
            return {"status": "error", "error": "Paper not found"}

        # Skip if no abstract
        if not paper.abstract:
            summary.status = SummaryStatus.DONE
            summary.summary_json = {
                "study_type": None,
                "population": None,
                "intervention": None,
                "comparator": None,
                "outcomes": [],
                "key_findings": [],
                "limitations": ["No abstract available"],
                "evidence_snippets": [],
                "quality_flags": {
                    "is_review": False,
                    "has_humans": None,
                    "has_animals": None,
                    "has_rct_terms": False,
                    "contains_numbers": False,
                },
            }
            db.commit()
            return {"status": "success", "paper_id": paper_id, "skipped": "no_abstract"}

        # Update status to RUNNING
        summary.status = SummaryStatus.RUNNING
        db.commit()

        logger.info("summarize_paper_start", paper_id=paper_id, title=paper.title[:50])

        # Call Gemini
        from app.integrations.gemini import GeminiProvider

        provider = GeminiProvider(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model=os.getenv("LLM_MODEL", "gemini-3-flash"),
        )

        summary_data = provider.summarize_paper(
            title=paper.title,
            abstract=paper.abstract,
            year=paper.year,
            journal=paper.journal,
            pmid=paper.pmid,
            doi=paper.doi,
        )

        # Save result
        summary.status = SummaryStatus.DONE
        summary.summary_json = summary_data
        summary.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info("summarize_paper_complete", paper_id=paper_id)

        # Check if all summaries done and trigger synthesis
        check_and_trigger_synthesis.apply_async(args=[run_id], countdown=5)

        return {"status": "success", "paper_id": paper_id}

    except Exception as e:
        logger.error("summarize_paper_error", paper_id=paper_id, error=str(e))
        db.rollback()

        try:
            from app.models import PaperSummary, SummaryStatus

            summary = (
                db.query(PaperSummary)
                .filter(PaperSummary.run_id == UUID(run_id), PaperSummary.paper_id == UUID(paper_id))
                .first()
            )
            if summary:
                summary.status = SummaryStatus.FAILED
                summary.error_message = str(e)[:500]
                summary.updated_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as e2:
            logger.error("failed_to_mark_summary_failed", error=str(e2))

        return {"status": "error", "paper_id": paper_id, "error": str(e)}

    finally:
        db.close()


def _log_status_change(db, run, tenant_id, from_status: str, to_status: str, error: str = None):
    """Log a status change to the audit log."""
    try:
        from app.models import AuditLog

        audit_log = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=None,
            action="run_status_changed",
            resource_type="query_run",
            resource_id=run.id,
            metadata_json={
                "from_status": from_status,
                "to_status": to_status,
                "error": error,
            },
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.error("audit_log_error", error=str(e))


@celery_app.task(name="app.tasks.noop_task")
def noop_task() -> dict:
    """A no-op task for testing Celery connectivity."""
    return {"status": "ok", "message": "No-op task executed"}


@celery_app.task(name="app.tasks.health_check")
def health_check() -> dict:
    """Health check task."""
    return {"status": "healthy", "worker": "pharmainsight-worker"}


@celery_app.task(name="app.tasks.build_evidence_table", bind=True, max_retries=2)
def build_evidence_table(self, run_id: str) -> dict:
    """Build evidence table from completed paper summaries."""
    db = get_db_session()

    try:
        from app.models import PaperSummary, Paper, EvidenceRow, QueryRun, Project

        run = db.query(QueryRun).filter(QueryRun.id == UUID(run_id)).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        project = db.query(Project).filter(Project.id == run.project_id).first()
        tenant_id = project.tenant_id

        # Get all DONE paper summaries for this run
        summaries = (
            db.query(PaperSummary, Paper)
            .join(Paper, Paper.id == PaperSummary.paper_id)
            .filter(PaperSummary.run_id == UUID(run_id), PaperSummary.status == "DONE")
            .all()
        )

        logger.info("building_evidence_table", run_id=run_id, summaries=len(summaries))

        rows_created = 0
        for summary, paper in summaries:
            try:
                # Check if row already exists
                existing = (
                    db.query(EvidenceRow)
                    .filter(EvidenceRow.run_id == UUID(run_id), EvidenceRow.paper_id == paper.id)
                    .first()
                )

                if existing:
                    continue

                # Build evidence row from paper summary
                summary_data = summary.summary_json or {}

                row_json = {
                    "paper_id": str(paper.id),
                    "citation": {
                        "pmid": paper.pmid,
                        "doi": paper.doi,
                        "year": paper.year,
                        "title": paper.title,
                        "journal": paper.journal,
                    },
                    "study_type": summary_data.get("study_type"),
                    "population": summary_data.get("population"),
                    "intervention": summary_data.get("intervention"),
                    "comparator": summary_data.get("comparator"),
                    "outcomes": summary_data.get("outcomes", []),
                    "key_findings": summary_data.get("key_findings", []),
                    "limitations": summary_data.get("limitations", []),
                    "evidence_snippets": summary_data.get("evidence_snippets", []),
                }

                evidence_row = EvidenceRow(
                    tenant_id=tenant_id,
                    run_id=UUID(run_id),
                    paper_id=paper.id,
                    row_json=row_json,
                )
                db.add(evidence_row)
                rows_created += 1

            except Exception as e:
                logger.error("evidence_row_error", paper_id=str(paper.id), error=str(e))
                continue

        db.commit()

        logger.info("evidence_table_complete", run_id=run_id, rows_created=rows_created)

        # Trigger synthesis if we have evidence
        if rows_created > 0:
            synthesize_run.apply_async(args=[run_id], countdown=5)

        return {"status": "success", "run_id": run_id, "rows_created": rows_created}

    except Exception as e:
        logger.error("build_evidence_table_error", run_id=run_id, error=str(e))
        db.rollback()
        raise self.retry(exc=e, countdown=30)

    finally:
        db.close()


@celery_app.task(name="app.tasks.synthesize_run", bind=True, max_retries=2)
def synthesize_run(self, run_id: str) -> dict:
    """Synthesize findings across all papers in a run."""
    db = get_db_session()

    try:
        from app.models import QueryRun, Project, EvidenceRow, RunSummary

        run = db.query(QueryRun).filter(QueryRun.id == UUID(run_id)).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        project = db.query(Project).filter(Project.id == run.project_id).first()
        tenant_id = project.tenant_id

        llm_model = os.getenv("LLM_MODEL", "gemini-3-flash")

        # Get or create run summary record
        run_summary = db.query(RunSummary).filter(RunSummary.run_id == UUID(run_id)).first()

        if not run_summary:
            run_summary = RunSummary(
                tenant_id=tenant_id,
                run_id=UUID(run_id),
                model=llm_model,
                status="RUNNING",
            )
            db.add(run_summary)
        else:
            run_summary.status = "RUNNING"
            run_summary.updated_at = datetime.now(timezone.utc)

        db.commit()

        # Get evidence rows
        evidence_rows = (
            db.query(EvidenceRow)
            .filter(EvidenceRow.run_id == UUID(run_id))
            .limit(15)  # Limit to 15 papers for synthesis
            .all()
        )

        if not evidence_rows:
            run_summary.status = "DONE"
            run_summary.summary_json = {
                "tldr": "No evidence available for synthesis.",
                "key_points": [],
                "consensus_level": "low",
                "contradictions": [],
                "gaps": [],
                "safety_notes": [],
                "claims_draft": [],
            }
            db.commit()
            return {"status": "success", "run_id": run_id, "papers": 0}

        logger.info("synthesizing_run", run_id=run_id, papers=len(evidence_rows))

        # Run synthesis
        from app.integrations.synthesis import RunSynthesisService

        service = RunSynthesisService(model=llm_model)
        evidence_data = [row.row_json for row in evidence_rows]

        synthesis_result = service.synthesize(
            query_text=run.query_text,
            evidence_rows=evidence_data,
        )

        # Save result
        run_summary.status = "DONE"
        run_summary.summary_json = synthesis_result
        run_summary.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info("run_synthesis_complete", run_id=run_id)

        return {"status": "success", "run_id": run_id, "papers": len(evidence_rows)}

    except Exception as e:
        logger.error("synthesize_run_error", run_id=run_id, error=str(e))
        db.rollback()

        try:
            run_summary = db.query(RunSummary).filter(RunSummary.run_id == UUID(run_id)).first()
            if run_summary:
                run_summary.status = "FAILED"
                run_summary.error_message = str(e)[:500]
                run_summary.updated_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass

        return {"status": "error", "run_id": run_id, "error": str(e)}

    finally:
        db.close()


@celery_app.task(name="app.tasks.check_and_trigger_synthesis", bind=True)
def check_and_trigger_synthesis(self, run_id: str) -> dict:
    """Check if all paper summaries are done and trigger synthesis."""
    db = get_db_session()

    try:
        from app.models import PaperSummary

        # Count summaries by status
        total = db.query(PaperSummary).filter(PaperSummary.run_id == UUID(run_id)).count()
        done = db.query(PaperSummary).filter(
            PaperSummary.run_id == UUID(run_id),
            PaperSummary.status.in_(["DONE", "FAILED"])
        ).count()

        logger.info("checking_synthesis_trigger", run_id=run_id, total=total, done=done)

        if total > 0 and done >= total:
            # All summaries complete, trigger evidence table build
            build_evidence_table.apply_async(args=[run_id], countdown=2)
            return {"status": "triggered", "run_id": run_id}

        return {"status": "waiting", "run_id": run_id, "done": done, "total": total}

    finally:
        db.close()


@celery_app.task(name="app.tasks.quick_synthesis_direct", bind=True, max_retries=2)
def quick_synthesis_direct(self, run_id: str) -> dict:
    """Direct synthesis from papers without per-paper LLM calls.
    
    This is the QUICK SYNTHESIS mode:
    1. Get all papers for this run
    2. Build evidence rows directly from paper metadata + abstract
    3. Call synthesis LLM once with all paper data
    """
    db = get_db_session()

    try:
        from app.models import Paper, EvidenceRow, QueryRun, Project, RunSummary
        from app.integrations.synthesis import RunSynthesisService

        run = db.query(QueryRun).filter(QueryRun.id == UUID(run_id)).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        project = db.query(Project).filter(Project.id == run.project_id).first()
        tenant_id = project.tenant_id

        logger.info("quick_synthesis_start", run_id=run_id)

        # Get all papers for this run via Evidence table
        from app.models import Evidence
        
        evidences = db.query(Evidence).filter(Evidence.run_id == UUID(run_id)).all()
        
        papers = []
        for ev in evidences:
            paper = db.query(Paper).filter(Paper.id == ev.paper_id).first()
            if paper:
                papers.append(paper)

        logger.info("quick_synthesis_papers_found", run_id=run_id, count=len(papers))

        if not papers:
            # No papers, create empty summary
            llm_model = os.getenv("LLM_MODEL", "gemini-2.0-flash-lite")
            run_summary = RunSummary(
                tenant_id=tenant_id,
                run_id=UUID(run_id),
                model=llm_model,
                status="DONE",
                summary_json={
                    "tldr": "No papers found for this query.",
                    "key_points": [],
                    "consensus_level": "low",
                    "contradictions": [],
                    "gaps": ["No papers to analyze"],
                    "safety_notes": [],
                    "claims_draft": [],
                },
            )
            db.add(run_summary)
            db.commit()
            return {"status": "success", "run_id": run_id, "papers": 0}

        # Build evidence rows directly from papers (no per-paper LLM)
        # For OA papers, try to fetch full-text
        from app.integrations.fulltext import FullTextFetcher
        full_text_fetcher = FullTextFetcher()
        
        evidence_data = []
        oa_count = 0
        
        for idx, paper in enumerate(papers[:50]):  # Limit to 50
            # Try to fetch full-text for OA papers
            content_text = paper.abstract[:2000] if paper.abstract else ""
            has_full_text = False
            
            # Check if paper has PMC ID (Open Access indicator)
            pmc_id = getattr(paper, 'pmc_id', None)
            if pmc_id and not getattr(paper, 'full_text', None):
                # Fetch full-text from PMC
                logger.info("fetching_oa_full_text", paper_id=str(paper.id), pmc_id=pmc_id)
                full_text = full_text_fetcher.fetch_and_truncate(pmc_id, max_tokens=6000)
                if full_text:
                    # Update paper record
                    paper.full_text = full_text
                    paper.is_open_access = True
                    content_text = full_text
                    has_full_text = True
                    oa_count += 1
            elif getattr(paper, 'full_text', None):
                # Already have full-text
                content_text = paper.full_text[:24000]  # ~6k tokens
                has_full_text = True
                oa_count += 1
            
            # Create evidence row from paper metadata
            row_json = {
                "paper_id": str(paper.id),
                "citation": {
                    "pmid": paper.pmid,
                    "doi": paper.doi,
                    "title": paper.title,
                    "year": paper.year,
                    "journal": paper.journal,
                    "authors": paper.authors[:3] if paper.authors else [],
                },
                "study_type": None,  # Will be inferred by synthesis
                "population": None,
                "intervention": None,
                "comparator": None,
                "outcomes": [],
                "key_findings": [],  # Will be filled by synthesis
                "limitations": [],
                "abstract": paper.abstract[:2000] if paper.abstract else "",
                "content": content_text,  # Full-text or abstract
                "has_full_text": has_full_text,
            }
            
            # Create/update evidence row
            existing = db.query(EvidenceRow).filter(
                EvidenceRow.run_id == UUID(run_id),
                EvidenceRow.paper_id == paper.id
            ).first()
            
            if existing:
                existing.row_json = row_json
            else:
                evidence_row = EvidenceRow(
                    tenant_id=tenant_id,
                    run_id=UUID(run_id),
                    paper_id=paper.id,
                    row_json=row_json,
                )
                db.add(evidence_row)
            
            evidence_data.append(row_json)

        db.commit()
        logger.info("quick_synthesis_evidence_created", run_id=run_id, rows=len(evidence_data))

        # Now run synthesis with paper abstracts
        llm_model = os.getenv("LLM_MODEL", "gemini-2.0-flash-lite")
        
        # Get or create run summary
        run_summary = db.query(RunSummary).filter(RunSummary.run_id == UUID(run_id)).first()
        if not run_summary:
            run_summary = RunSummary(
                tenant_id=tenant_id,
                run_id=UUID(run_id),
                model=llm_model,
                status="RUNNING",
            )
            db.add(run_summary)
        else:
            run_summary.status = "RUNNING"
            run_summary.updated_at = datetime.now(timezone.utc)
        
        db.commit()

        # Build evidence summary for synthesis using content (full-text or abstract)
        evidence_for_synthesis = []
        for row in evidence_data:
            # Use content field (full-text if available, otherwise abstract)
            content = row.get("content", row.get("abstract", ""))[:2000]
            synth_row = {
                "paper_id": row["paper_id"],
                "citation": row["citation"],
                "study_type": "Unknown",
                "population": "See content",
                "intervention": "See content",
                "outcomes": [],
                "key_findings": [content] if content else [],
                "has_full_text": row.get("has_full_text", False),
            }
            evidence_for_synthesis.append(synth_row)

        logger.info("quick_synthesis_calling_llm", run_id=run_id, papers=len(evidence_for_synthesis), oa_papers=oa_count)

        # Call synthesis service
        service = RunSynthesisService(model=llm_model)
        synthesis_result = service.synthesize(
            query_text=run.query_text,
            evidence_rows=evidence_for_synthesis,
        )

        # Save result
        run_summary.summary_json = synthesis_result
        run_summary.status = "DONE"
        run_summary.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "quick_synthesis_complete",
            run_id=run_id,
            papers=len(papers),
            consensus=synthesis_result.get("consensus_level"),
        )

        return {
            "status": "success",
            "run_id": run_id,
            "papers": len(papers),
            "llm_calls": 1,
        }

    except Exception as e:
        logger.error("quick_synthesis_error", run_id=run_id, error=str(e))
        db.rollback()
        raise self.retry(exc=e, countdown=30)

    finally:
        db.close()
