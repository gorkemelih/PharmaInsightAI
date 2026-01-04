"""Base types for literature providers."""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class PaperCandidate:
    """Normalized paper candidate from literature search."""

    title: str
    raw_source: str  # e.g., "pubmed", "europepmc"

    # Identifiers (at least one should be present)
    pmid: str | None = None
    doi: str | None = None

    # Metadata
    abstract: str | None = None
    journal: str | None = None
    year: int | None = None
    authors: list[str] = field(default_factory=list)
    url: str | None = None

    def normalize_doi(self) -> str | None:
        """Return normalized DOI for deduplication."""
        if self.doi:
            return self.doi.lower().strip()
        return None

    def normalize_title(self) -> str:
        """Return normalized title for deduplication."""
        return self.title.lower().strip()

    def get_url(self) -> str | None:
        """Get the best URL for this paper."""
        if self.url:
            return self.url
        if self.doi:
            return f"https://doi.org/{self.doi}"
        if self.pmid:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"
        return None


@runtime_checkable
class LiteratureProvider(Protocol):
    """Protocol for literature search providers."""

    @property
    def name(self) -> str:
        """Provider name for logging and tracking."""
        ...

    async def search(self, query: str, limit: int = 20) -> list[PaperCandidate]:
        """Search for papers matching the query.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of PaperCandidate objects
        """
        ...
