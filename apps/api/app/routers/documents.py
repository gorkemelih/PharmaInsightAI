"""Document management endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import AnalystUser, AuthenticatedUser
from app.db.session import get_db
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.project import Project
from app.services.documents import storage, extractor

router = APIRouter(tags=["documents"])


# Allowed file types
ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "markdown", "csv"}
ALLOWED_MIMES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "text/csv",
    "application/octet-stream",  # Fallback for some clients
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class DocumentResponse(BaseModel):
    """Document response."""

    id: str
    project_id: str
    filename: str
    content_type: str
    size_bytes: int
    status: str
    error_message: str | None
    created_at: str
    chunk_count: int


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    id: str
    filename: str
    status: str
    message: str


def get_project_or_404(project_id: UUID, tenant_id: UUID, db: Session) -> Project:
    """Get project by ID or raise 404."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.tenant_id == tenant_id,
        Project.deleted_at.is_(None),
    ).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def get_document_or_404(document_id: UUID, tenant_id: UUID, db: Session) -> Document:
    """Get document by ID or raise 404."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant_id,
        Document.deleted_at.is_(None),
    ).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


@router.post("/projects/{project_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    project_id: UUID,
    current_user: AnalystUser,
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """Upload a document to a project."""
    # Verify project
    project = get_project_or_404(project_id, current_user.tenant_id, db)
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    
    # Validate MIME type
    if file.content_type and file.content_type not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type not allowed: {file.content_type}",
        )
    
    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)} MB",
        )
    
    # Create document record
    document = Document(
        project_id=project.id,
        tenant_id=current_user.tenant_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        storage_path="",  # Will be set after save
        uploaded_by=current_user.user_id,
        status=DocumentStatus.UPLOADED.value,
    )
    db.add(document)
    db.flush()  # Get the ID
    
    # Save file to disk
    try:
        storage_path = storage.save_file(
            tenant_id=current_user.tenant_id,
            project_id=project.id,
            document_id=document.id,
            filename=file.filename,
            file_content=content,
        )
        document.storage_path = storage_path
        db.commit()
        db.refresh(document)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )
    
    return DocumentUploadResponse(
        id=str(document.id),
        filename=document.filename,
        status=document.status,
        message="Document uploaded successfully. Call /documents/{id}/process to extract text.",
    )


@router.get("/projects/{project_id}/documents", response_model=list[DocumentResponse])
def list_documents(
    project_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[DocumentResponse]:
    """List all documents in a project."""
    project = get_project_or_404(project_id, current_user.tenant_id, db)
    
    documents = db.query(Document).filter(
        Document.project_id == project.id,
        Document.deleted_at.is_(None),
    ).order_by(Document.created_at.desc()).all()
    
    result = []
    for doc in documents:
        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).count()
        result.append(DocumentResponse(
            id=str(doc.id),
            project_id=str(doc.project_id),
            filename=doc.filename,
            content_type=doc.content_type,
            size_bytes=doc.size_bytes,
            status=doc.status,
            error_message=doc.error_message,
            created_at=doc.created_at.isoformat(),
            chunk_count=chunk_count,
        ))
    
    return result


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: UUID,
    current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Download a document file."""
    document = get_document_or_404(document_id, current_user.tenant_id, db)
    
    try:
        content = storage.read_file(document.storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )
    
    return Response(
        content=content,
        media_type=document.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.filename}"',
        },
    )


@router.post("/documents/{document_id}/process", response_model=DocumentResponse)
def process_document(
    document_id: UUID,
    current_user: AnalystUser,
    db: Annotated[Session, Depends(get_db)],
) -> DocumentResponse:
    """Process a document: extract text and create chunks."""
    document = get_document_or_404(document_id, current_user.tenant_id, db)
    
    if document.status == DocumentStatus.PROCESSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document already processed",
        )
    
    # Update status
    document.status = DocumentStatus.PROCESSING.value
    db.commit()
    
    try:
        # Read file
        content = storage.read_file(document.storage_path)
        
        # Extract text
        pages = extractor.extract_text(document.filename, content)
        
        if not pages:
            raise ValueError("No text extracted from document")
        
        # Delete existing chunks (if re-processing)
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
        
        # Create chunks
        chunks = extractor.process_document_text(pages)
        
        for chunk_data in chunks:
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk_data["chunk_index"],
                text=chunk_data["text"],
                page_number=chunk_data["page_number"],
            )
            db.add(chunk)
        
        document.status = DocumentStatus.PROCESSED.value
        document.error_message = None
        db.commit()
        db.refresh(document)
        
    except Exception as e:
        document.status = DocumentStatus.FAILED.value
        document.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}",
        )
    
    chunk_count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document.id
    ).count()
    
    return DocumentResponse(
        id=str(document.id),
        project_id=str(document.project_id),
        filename=document.filename,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        status=document.status,
        error_message=document.error_message,
        created_at=document.created_at.isoformat(),
        chunk_count=chunk_count,
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    current_user: AnalystUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Soft-delete a document."""
    document = get_document_or_404(document_id, current_user.tenant_id, db)
    
    document.deleted_at = datetime.now(timezone.utc)
    document.deleted_by = current_user.user_id
    db.commit()


# ============ Internal Analysis ============

from enum import Enum
from pydantic import Field
from app.services.documents import analysis as analysis_service
import os
import google.generativeai as genai


class AnalysisScope(str, Enum):
    """Scope for internal analysis."""
    INTERNAL_ONLY = "internal_only"
    LITERATURE_ONLY = "literature_only"
    HYBRID = "hybrid"


class InternalAnalysisRequest(BaseModel):
    """Request for internal analysis."""
    question: str = Field(..., min_length=5, max_length=2000)
    scope: AnalysisScope = AnalysisScope.HYBRID
    max_sources_internal: int = Field(default=10, ge=1, le=50)
    max_sources_literature: int = Field(default=10, ge=1, le=50)


class Citation(BaseModel):
    """Citation in analysis response."""
    key: str
    type: str  # "internal" or "literature"
    doc_id: str | None = None
    chunk_id: str | None = None
    filename: str | None = None
    page_number: int | None = None
    paper_id: str | None = None
    pmid: str | None = None
    doi: str | None = None
    title: str | None = None


class InternalAnalysisResponse(BaseModel):
    """Response from internal analysis."""
    markdown_report: str
    citations: list[Citation]
    warning: str | None = None


@router.post("/projects/{project_id}/internal-analysis", response_model=InternalAnalysisResponse)
def run_internal_analysis(
    project_id: UUID,
    request: InternalAnalysisRequest,
    current_user: AnalystUser,
    db: Annotated[Session, Depends(get_db)],
) -> InternalAnalysisResponse:
    """Run grounded analysis using internal documents and/or literature.
    
    Retrieves relevant chunks, builds a prompt with citations,
    and generates a response using Gemini.
    """
    project = get_project_or_404(project_id, current_user.tenant_id, db)
    
    # Retrieve context based on scope
    internal_chunks: list = []
    literature_chunks: list = []
    
    if request.scope in (AnalysisScope.INTERNAL_ONLY, AnalysisScope.HYBRID):
        internal_chunks = analysis_service.retrieve_internal_chunks(
            project_id=project.id,
            tenant_id=current_user.tenant_id,
            question=request.question,
            db=db,
            max_sources=request.max_sources_internal,
        )
    
    if request.scope in (AnalysisScope.LITERATURE_ONLY, AnalysisScope.HYBRID):
        literature_chunks = analysis_service.retrieve_literature_context(
            project_id=project.id,
            tenant_id=current_user.tenant_id,
            question=request.question,
            db=db,
            max_sources=request.max_sources_literature,
        )
    
    # Check if we have any context
    warning = None
    if not internal_chunks and not literature_chunks:
        warning = "No relevant documents or literature found. Upload documents or run literature analyses first."
        return InternalAnalysisResponse(
            markdown_report="No relevant context found to answer this question.",
            citations=[],
            warning=warning,
        )
    
    # Build grounded prompt
    prompt = analysis_service.build_grounded_prompt(
        question=request.question,
        internal_chunks=internal_chunks,
        literature_chunks=literature_chunks,
    )
    
    # Call LLM
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not configured")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt)
        response_text = response.text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation failed: {str(e)}",
        )
    
    # Format citations
    citations_data = analysis_service.format_citations(
        internal_chunks=internal_chunks,
        literature_chunks=literature_chunks,
    )
    citations = [Citation(**c) for c in citations_data]
    
    # Add warning if citations not used properly
    if "[I" not in response_text and "[L" not in response_text:
        if not warning:
            warning = "Response may not include proper citations."
    
    return InternalAnalysisResponse(
        markdown_report=response_text,
        citations=citations,
        warning=warning,
    )
