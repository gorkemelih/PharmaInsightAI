"""Internal analysis service for grounded synthesis."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.document import Document, DocumentChunk
from app.models.paper import Paper
from app.models.paper_summary import PaperSummary
from app.models.query_run import QueryRun


def retrieve_internal_chunks(
    project_id: UUID,
    tenant_id: UUID,
    question: str,
    db: Session,
    max_sources: int = 10,
) -> list[dict]:
    """Retrieve relevant chunks from internal documents.
    
    Uses keyword search (ILIKE) for MVP.
    TODO: Add embedding-based similarity search.
    """
    # Get keywords from question
    keywords = [w.strip() for w in question.lower().split() if len(w.strip()) > 3]

    if not keywords:
        # Fall back to all chunks
        chunks = (
            db.query(DocumentChunk)
            .join(Document)
            .filter(
                Document.project_id == project_id,
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
                Document.status == "processed",
            )
            .limit(max_sources)
            .all()
        )
    else:
        # Search with keywords using ILIKE
        from sqlalchemy import or_
        keyword_filters = [
            DocumentChunk.text.ilike(f"%{kw}%") for kw in keywords[:5]  # Limit to 5 keywords
        ]

        chunks = (
            db.query(DocumentChunk)
            .join(Document)
            .filter(
                Document.project_id == project_id,
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
                Document.status == "processed",
                or_(*keyword_filters),
            )
            .limit(max_sources)
            .all()
        )

    results = []
    for chunk in chunks:
        results.append({
            "type": "internal",
            "doc_id": str(chunk.document_id),
            "chunk_id": str(chunk.id),
            "filename": chunk.document.filename,
            "page_number": chunk.page_number,
            "text": chunk.text,
        })

    return results


def retrieve_literature_context(
    project_id: UUID,
    tenant_id: UUID,
    question: str,
    db: Session,
    max_sources: int = 10,
) -> list[dict]:
    """Retrieve relevant paper summaries from literature runs.
    
    Uses keyword search in summaries for MVP.
    """
    # Get recent paper summaries from this project
    summaries = (
        db.query(PaperSummary)
        .join(QueryRun)
        .filter(
            QueryRun.project_id == project_id,
            QueryRun.deleted_at.is_(None),
            PaperSummary.tenant_id == tenant_id,
            PaperSummary.status == "DONE",
        )
        .order_by(PaperSummary.created_at.desc())
        .limit(max_sources)
        .all()
    )

    results = []
    for ps in summaries:
        paper = ps.paper
        summary_json = ps.summary_json or {}

        # Extract key info
        key_findings = summary_json.get("key_findings", [])
        finding_text = " ".join(key_findings[:3]) if key_findings else ""

        results.append({
            "type": "literature",
            "paper_id": str(paper.id),
            "pmid": paper.pmid,
            "doi": paper.doi,
            "title": paper.title,
            "authors": paper.authors[:3] if paper.authors else [],
            "year": paper.year,
            "text": finding_text or paper.abstract[:500] if paper.abstract else "",
        })

    return results


def build_grounded_prompt(
    question: str,
    internal_chunks: list[dict],
    literature_chunks: list[dict],
) -> str:
    """Build a prompt for grounded synthesis with citations."""

    prompt = f"""You are an expert research analyst. Answer the following question based ONLY on the provided context.
Every claim must be cited using [I1], [I2] for internal docs or [L1], [L2] for literature.
If information is not in the context, say "No relevant information found."

QUESTION: {question}

"""

    if internal_chunks:
        prompt += "=== INTERNAL DOCUMENTS ===\n"
        for i, chunk in enumerate(internal_chunks, 1):
            prompt += f"[I{i}] (File: {chunk['filename']}, Page: {chunk.get('page_number', 'N/A')})\n{chunk['text'][:500]}\n\n"

    if literature_chunks:
        prompt += "=== LITERATURE ===\n"
        for i, chunk in enumerate(literature_chunks, 1):
            authors = ", ".join(chunk.get('authors', [])[:2])
            prompt += f"[L{i}] ({authors}, {chunk.get('year', 'N/A')}. {chunk['title'][:100]})\n{chunk['text'][:500]}\n\n"

    prompt += """
=== INSTRUCTIONS ===
1. Answer the question comprehensively using ONLY the provided context
2. Cite every claim with [I1], [L2] etc.
3. If no relevant information, clearly state that
4. Format in clear markdown

ANSWER:"""

    return prompt


def format_citations(
    internal_chunks: list[dict],
    literature_chunks: list[dict],
) -> list[dict]:
    """Format citations for the response."""
    citations = []

    for i, chunk in enumerate(internal_chunks, 1):
        citations.append({
            "key": f"I{i}",
            "type": "internal",
            "doc_id": chunk["doc_id"],
            "chunk_id": chunk["chunk_id"],
            "filename": chunk["filename"],
            "page_number": chunk.get("page_number"),
        })

    for i, chunk in enumerate(literature_chunks, 1):
        citations.append({
            "key": f"L{i}",
            "type": "literature",
            "paper_id": chunk["paper_id"],
            "pmid": chunk.get("pmid"),
            "doi": chunk.get("doi"),
            "title": chunk["title"],
        })

    return citations
