"""Pydantic schemas for QueryRun endpoints."""

from pydantic import BaseModel, Field, model_validator


class RunCreate(BaseModel):
    """Request body for creating a run."""

    query_text: str = Field(..., min_length=1)
    max_papers: int = Field(default=10, ge=1, le=50, description="Max papers to retrieve (1-50)")
    year_from: int | None = Field(default=None, ge=1900, le=2026, description="Start year filter")
    year_to: int | None = Field(default=None, ge=1900, le=2026, description="End year filter")
    analysis_mode: str = Field(default="synthesis", pattern="^(synthesis|per_paper)$")
    include_marketing: bool = Field(default=True)
    language: str = Field(default="en", pattern="^(en|tr)$")

    @model_validator(mode="after")
    def validate_year_range(self):
        if self.year_from and self.year_to and self.year_from > self.year_to:
            raise ValueError("year_from must be <= year_to")
        return self


class RunResponse(BaseModel):
    """Run response."""

    id: str
    project_id: str
    query_text: str
    status: str
    error_message: str | None
    created_at: str
    max_papers: int
    year_from: int | None
    year_to: int | None
    analysis_mode: str
    include_marketing: bool
    language: str


class PaperResponse(BaseModel):
    """Paper response."""

    id: str
    title: str
    abstract: str | None
    journal: str | None
    year: int | None
    authors: list[str]
    pmid: str | None
    doi: str | None
    url: str | None
    source: str


class SummaryStatusResponse(BaseModel):
    """Summary status for a paper."""

    paper_id: str
    title: str
    status: str
    error_message: str | None = None


class SummaryResponse(BaseModel):
    """Full summary response."""

    paper_id: str
    run_id: str
    status: str
    model: str
    summary: dict | None = None
    error_message: str | None = None


class EvidenceRowResponse(BaseModel):
    """Evidence row response."""

    paper_id: str
    citation: dict
    study_type: str | None
    population: str | None
    intervention: str | None
    comparator: str | None
    outcomes: list[str]
    key_findings: list[str]
    limitations: list[str]


class RunSummaryResponse(BaseModel):
    """Run synthesis summary response."""

    run_id: str
    status: str
    model: str
    summary: dict | None = None
    error_message: str | None = None


class FormattedReference(BaseModel):
    """Formatted reference with index."""

    index: int
    paper_id: str
    formatted: str
    link: str | None


class CitationWithIndex(BaseModel):
    """Citation with numeric index."""

    index: int


class KeyPointWithIndices(BaseModel):
    """Key point with numeric citation indices."""

    text: str
    citations: list[CitationWithIndex]


class ClaimWithIndices(BaseModel):
    """Claim with numeric citation indices."""

    claim: str
    allowed: bool
    rationale: str
    citations: list[CitationWithIndex]


class SummaryWithIndices(BaseModel):
    """Summary with numeric citations."""

    tldr: str
    key_points: list[KeyPointWithIndices]
    consensus_level: str
    contradictions: list[KeyPointWithIndices]
    gaps: list[str]
    safety_notes: list[str]
    claims_draft: list[ClaimWithIndices]


class SummaryWithReferencesResponse(BaseModel):
    """Summary with numbered references."""

    run_id: str
    status: str
    summary: SummaryWithIndices | None
    references: list[FormattedReference]
    error_message: str | None = None


class EvidenceDetailResponse(BaseModel):
    """Detailed evidence for a paper."""

    paper_id: str
    title: str
    authors: list[str]
    year: int | None
    journal: str | None
    pmid: str | None
    doi: str | None
    url: str | None
    evidence_snippets: list[str]
    key_findings: list[str]
    study_type: str | None
