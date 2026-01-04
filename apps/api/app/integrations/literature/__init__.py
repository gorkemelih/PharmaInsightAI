"""Literature search integrations package."""

from app.integrations.literature.base import LiteratureProvider, PaperCandidate
from app.integrations.literature.pubmed import PubMedProvider
from app.integrations.literature.europepmc import EuropePMCProvider
from app.integrations.literature.service import LiteratureSearchService

__all__ = [
    "LiteratureProvider",
    "PaperCandidate",
    "PubMedProvider",
    "EuropePMCProvider",
    "LiteratureSearchService",
]
