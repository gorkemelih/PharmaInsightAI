"""Literature search service - aggregates and deduplicates results from providers."""

import asyncio
from typing import Sequence

import structlog

from app.integrations.literature.base import LiteratureProvider, PaperCandidate
from app.integrations.literature.pubmed import PubMedProvider
from app.integrations.literature.europepmc import EuropePMCProvider

logger = structlog.get_logger(__name__)


class LiteratureSearchService:
    """Service to search multiple literature providers and deduplicate results."""

    def __init__(
        self,
        providers: Sequence[LiteratureProvider] | None = None,
        ncbi_api_key: str | None = None,
        ncbi_tool: str = "pharmainsightai",
        ncbi_email: str = "admin@pharmainsight.io",
    ):
        if providers is not None:
            self.providers = list(providers)
        else:
            # Default providers
            self.providers: list[LiteratureProvider] = [
                PubMedProvider(
                    api_key=ncbi_api_key,
                    tool=ncbi_tool,
                    email=ncbi_email,
                ),
                EuropePMCProvider(),
            ]

    async def search(self, query: str, limit: int = 20) -> list[PaperCandidate]:
        """Search all providers and return deduplicated results.

        Args:
            query: Search query string
            limit: Maximum results per provider

        Returns:
            Deduplicated list of PaperCandidate objects
        """
        logger.info("literature_search_start", query=query, limit=limit)

        # Search all providers in parallel
        tasks = [provider.search(query, limit) for provider in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all papers
        all_papers: list[PaperCandidate] = []
        for i, result in enumerate(results):
            provider_name = self.providers[i].name
            if isinstance(result, Exception):
                logger.error(
                    "literature_provider_error",
                    provider=provider_name,
                    error=str(result),
                )
            else:
                logger.info(
                    "literature_provider_results",
                    provider=provider_name,
                    count=len(result),
                )
                all_papers.extend(result)

        # Deduplicate
        deduplicated = self._deduplicate(all_papers)

        logger.info(
            "literature_search_complete",
            query=query,
            total_raw=len(all_papers),
            total_deduplicated=len(deduplicated),
        )

        return deduplicated

    def _deduplicate(self, papers: list[PaperCandidate]) -> list[PaperCandidate]:
        """Deduplicate papers by DOI, then PMID, then normalized title.

        Priority order for keeping papers:
        1. Papers with DOI are preferred
        2. Papers with PMID are preferred
        3. Papers with longer abstracts are preferred
        """
        seen_dois: set[str] = set()
        seen_pmids: set[str] = set()
        seen_titles: set[str] = set()

        unique_papers: list[PaperCandidate] = []

        # Sort to prioritize papers with more metadata
        sorted_papers = sorted(
            papers,
            key=lambda p: (
                p.doi is not None,  # Has DOI
                p.pmid is not None,  # Has PMID
                len(p.abstract or ""),  # Longer abstract
            ),
            reverse=True,
        )

        for paper in sorted_papers:
            # Check DOI
            doi_norm = paper.normalize_doi()
            if doi_norm:
                if doi_norm in seen_dois:
                    continue
                seen_dois.add(doi_norm)

            # Check PMID
            if paper.pmid:
                if paper.pmid in seen_pmids:
                    continue
                seen_pmids.add(paper.pmid)

            # Check normalized title (fallback)
            title_norm = paper.normalize_title()
            if title_norm in seen_titles:
                continue
            seen_titles.add(title_norm)

            unique_papers.append(paper)

        return unique_papers


def get_literature_service(
    ncbi_api_key: str | None = None,
    ncbi_tool: str = "pharmainsightai",
    ncbi_email: str = "admin@pharmainsight.io",
) -> LiteratureSearchService:
    """Factory function to create a LiteratureSearchService with default providers."""
    return LiteratureSearchService(
        ncbi_api_key=ncbi_api_key,
        ncbi_tool=ncbi_tool,
        ncbi_email=ncbi_email,
    )
