"""SQLAlchemy models for worker."""

import enum
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class QueryStatus(enum.Enum):
    """Query run status."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class SummaryStatus(enum.Enum):
    """Summary processing status."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class QueryRun(Base):
    """Query run model."""
    __tablename__ = "query_runs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    query_text = Column(Text, nullable=False)
    status = Column(Enum(QueryStatus), nullable=False, default=QueryStatus.QUEUED)
    error_message = Column(Text, nullable=True)
    max_papers = Column(Integer, nullable=False, default=10)
    year_from = Column(Integer, nullable=True)
    year_to = Column(Integer, nullable=True)
    analysis_mode = Column(String(20), nullable=False, default="synthesis")
    include_marketing = Column(Boolean, nullable=False, default=True)
    language = Column(String(10), nullable=False, default="en")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Project(Base):
    """Project model."""
    __tablename__ = "projects"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Paper(Base):
    """Paper model."""
    __tablename__ = "papers"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False)
    doi = Column(String(255), nullable=True, index=True)
    pmid = Column(String(50), nullable=True, index=True)
    pmc_id = Column(String(50), nullable=True, index=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    is_open_access = Column(Boolean, nullable=False, default=False)
    journal = Column(String(500), nullable=True)
    year = Column(Integer, nullable=True)
    authors = Column(JSONB, nullable=False, default=list)
    url = Column(Text, nullable=True)
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Evidence(Base):
    """Evidence model linking papers to query runs."""
    __tablename__ = "evidences"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(PG_UUID(as_uuid=True), ForeignKey("query_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(PG_UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_json = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PaperSummary(Base):
    """Paper summary model."""
    __tablename__ = "paper_summaries"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False)
    paper_id = Column(PG_UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id = Column(PG_UUID(as_uuid=True), ForeignKey("query_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    status = Column(Enum(SummaryStatus), nullable=False, default=SummaryStatus.QUEUED)
    summary_json = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class AuditLog(Base):
    """Audit log model."""
    __tablename__ = "audit_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False)
    actor_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(PG_UUID(as_uuid=True), nullable=True)
    metadata_json = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class RunSummary(Base):
    """Run-level synthesis summary."""
    __tablename__ = "run_summaries"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False)
    run_id = Column(PG_UUID(as_uuid=True), ForeignKey("query_runs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    model = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="QUEUED")
    summary_json = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class EvidenceRow(Base):
    """Evidence table row."""
    __tablename__ = "evidence_rows"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False)
    run_id = Column(PG_UUID(as_uuid=True), ForeignKey("query_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(PG_UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    row_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

