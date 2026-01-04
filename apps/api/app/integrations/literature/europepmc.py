"""Europe PMC literature provider."""

from typing import Any

import httpx
import structlog

from app.integrations.literature.base import PaperCandidate

logger = structlog.get_logger(__name__)

EUROPEPMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


class EuropePMCProvider:
    """Europe PMC literature provider using REST API."""

    def __init__(
        self,
        timeout: float = 15.0,
        retries: int = 2,
    ):
        self.timeout = timeout
        self.retries = retries

    @property
    def name(self) -> str:
        return "europepmc"

    async def search(self, query: str, limit: int = 20) -> list[PaperCandidate]:
        """Search Europe PMC for papers matching the query."""
        try:
            params: dict[str, Any] = {
                "query": query,
                "format": "json",
                "pageSize": limit,
                "resultType": "core",  # Get full metadata
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for attempt in range(self.retries + 1):
                    try:
                        response = await client.get(EUROPEPMC_SEARCH_URL, params=params)
                        response.raise_for_status()
                        data = response.json()
                        return self._parse_response(data)
                    except httpx.HTTPError as e:
                        if attempt == self.retries:
                            raise
                        logger.warning("europepmc_search_retry", attempt=attempt, error=str(e))

        except Exception as e:
            logger.error("europepmc_search_error", query=query, error=str(e))
            return []

        return []

    def _parse_response(self, data: dict[str, Any]) -> list[PaperCandidate]:
        """Parse Europe PMC JSON response."""
        papers = []
        result_list = data.get("resultList", {}).get("result", [])

        for result in result_list:
            try:
                paper = self._parse_result(result)
                if paper:
                    papers.append(paper)
            except Exception as e:
                logger.error("europepmc_parse_result_error", error=str(e))

        logger.info("europepmc_search_found", count=len(papers))
        return papers

    def _parse_result(self, result: dict[str, Any]) -> PaperCandidate | None:
        """Parse a single Europe PMC result."""
        title = result.get("title")
        if not title:
            return None

        # Clean title (remove HTML tags if any)
        title = title.strip()

        # PMID
        pmid = result.get("pmid")
        if pmid:
            pmid = str(pmid)

        # DOI
        doi = result.get("doi")

        # Abstract
        abstract = result.get("abstractText")

        # Journal
        journal = result.get("journalTitle")

        # Year
        year = None
        pub_year = result.get("pubYear")
        if pub_year:
            try:
                year = int(pub_year)
            except ValueError:
                pass

        # Authors
        authors = []
        author_list = result.get("authorList", {}).get("author", [])
        for author in author_list[:5]:  # Limit to 5 authors
            full_name = author.get("fullName")
            if full_name:
                authors.append(full_name)

        # URL
        url = None
        if pmid:
            url = f"https://europepmc.org/article/MED/{pmid}"
        elif doi:
            url = f"https://doi.org/{doi}"

        return PaperCandidate(
            pmid=pmid,
            doi=doi,
            title=title,
            abstract=abstract,
            journal=journal,
            year=year,
            authors=authors,
            url=url,
            raw_source="europepmc",
        )
