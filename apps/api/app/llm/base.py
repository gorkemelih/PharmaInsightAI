"""Base types for LLM providers."""

from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field


class EvidenceSnippet(BaseModel):
    """A quote extracted from the paper abstract."""

    quote: str = Field(..., description="Verbatim quote from abstract")
    location: str = Field(default="abstract", description="Source location")
    confidence: float = Field(ge=0, le=1, default=0.8, description="Confidence score")


class QualityFlags(BaseModel):
    """Quality indicators for the paper."""

    is_review: bool = Field(default=False, description="Is this a review article")
    has_humans: bool | None = Field(default=None, description="Study involves humans")
    has_animals: bool | None = Field(default=None, description="Study involves animals")
    has_rct_terms: bool = Field(default=False, description="Contains RCT terminology")
    contains_numbers: bool = Field(default=False, description="Contains numerical data")


class PaperSummarySchema(BaseModel):
    """Structured summary of a paper following PICO framework."""

    study_type: str | None = Field(
        default=None,
        description="Type of study (RCT, observational, review, meta-analysis, etc.)",
    )
    population: str | None = Field(
        default=None,
        description="Study population or patient group",
    )
    intervention: str | None = Field(
        default=None,
        description="Main intervention or treatment studied",
    )
    comparator: str | None = Field(
        default=None,
        description="Control or comparison group",
    )
    outcomes: list[str] = Field(
        default_factory=list,
        description="Primary and secondary outcomes measured",
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Key findings and results",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Study limitations noted",
    )
    evidence_snippets: list[EvidenceSnippet] = Field(
        default_factory=list,
        description="Verbatim quotes supporting the analysis",
    )
    quality_flags: QualityFlags = Field(
        default_factory=QualityFlags,
        description="Quality indicators",
    )


class PaperInput(BaseModel):
    """Input data for paper summarization."""

    title: str
    abstract: str | None
    year: int | None
    journal: str | None
    pmid: str | None
    doi: str | None
    url: str | None


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        ...

    async def summarize_paper(self, paper: PaperInput) -> PaperSummarySchema:
        """Generate a structured summary for a paper.

        Args:
            paper: Paper input data

        Returns:
            Structured summary following PICO framework

        Raises:
            Exception: If LLM call fails
        """
        ...
