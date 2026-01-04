"""PubMed literature provider using NCBI E-utilities."""

import xml.etree.ElementTree as ET
from typing import Any

import httpx
import structlog

from app.integrations.literature.base import PaperCandidate

logger = structlog.get_logger(__name__)

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


class PubMedProvider:
    """PubMed literature provider using NCBI E-utilities."""

    def __init__(
        self,
        api_key: str | None = None,
        tool: str = "pharmainsightai",
        email: str = "admin@pharmainsight.io",
        timeout: float = 15.0,
        retries: int = 2,
    ):
        self.api_key = api_key
        self.tool = tool
        self.email = email
        self.timeout = timeout
        self.retries = retries

    @property
    def name(self) -> str:
        return "pubmed"

    async def search(self, query: str, limit: int = 20) -> list[PaperCandidate]:
        """Search PubMed for papers matching the query."""
        try:
            # Step 1: Search for PMIDs
            pmids = await self._esearch(query, limit)
            if not pmids:
                logger.info("pubmed_search_no_results", query=query)
                return []

            logger.info("pubmed_search_found", query=query, count=len(pmids))

            # Step 2: Fetch paper details
            papers = await self._efetch(pmids)
            return papers

        except Exception as e:
            logger.error("pubmed_search_error", query=query, error=str(e))
            return []

    async def _esearch(self, query: str, limit: int) -> list[str]:
        """Search for PMIDs using ESearch."""
        params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmax": limit,
            "retmode": "json",
            "tool": self.tool,
            "email": self.email,
        }
        if self.api_key:
            params["api_key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.retries + 1):
                try:
                    response = await client.get(ESEARCH_URL, params=params)
                    response.raise_for_status()
                    data = response.json()
                    return data.get("esearchresult", {}).get("idlist", [])
                except httpx.HTTPError as e:
                    if attempt == self.retries:
                        raise
                    logger.warning("pubmed_esearch_retry", attempt=attempt, error=str(e))

        return []

    async def _efetch(self, pmids: list[str]) -> list[PaperCandidate]:
        """Fetch paper details using EFetch."""
        params: dict[str, Any] = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "tool": self.tool,
            "email": self.email,
        }
        if self.api_key:
            params["api_key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.retries + 1):
                try:
                    response = await client.get(EFETCH_URL, params=params)
                    response.raise_for_status()
                    return self._parse_xml(response.text)
                except httpx.HTTPError as e:
                    if attempt == self.retries:
                        raise
                    logger.warning("pubmed_efetch_retry", attempt=attempt, error=str(e))

        return []

    def _parse_xml(self, xml_text: str) -> list[PaperCandidate]:
        """Parse PubMed XML response."""
        papers = []
        try:
            root = ET.fromstring(xml_text)
            for article in root.findall(".//PubmedArticle"):
                paper = self._parse_article(article)
                if paper:
                    papers.append(paper)
        except ET.ParseError as e:
            logger.error("pubmed_xml_parse_error", error=str(e))
        return papers

    def _parse_article(self, article: ET.Element) -> PaperCandidate | None:
        """Parse a single PubmedArticle element."""
        try:
            medline = article.find("MedlineCitation")
            if medline is None:
                return None

            # PMID
            pmid_elem = medline.find("PMID")
            pmid = pmid_elem.text if pmid_elem is not None else None

            # Article info
            article_elem = medline.find("Article")
            if article_elem is None:
                return None

            # Title
            title_elem = article_elem.find("ArticleTitle")
            title = title_elem.text if title_elem is not None else "Untitled"

            # Abstract
            abstract = None
            abstract_elem = article_elem.find(".//AbstractText")
            if abstract_elem is not None:
                abstract = abstract_elem.text

            # Journal
            journal = None
            journal_elem = article_elem.find(".//Journal/Title")
            if journal_elem is not None:
                journal = journal_elem.text

            # Year
            year = None
            year_elem = article_elem.find(".//PubDate/Year")
            if year_elem is not None and year_elem.text:
                try:
                    year = int(year_elem.text)
                except ValueError:
                    pass

            # DOI
            doi = None
            for eloc in article_elem.findall(".//ELocationID"):
                if eloc.get("EIdType") == "doi":
                    doi = eloc.text
                    break

            # Also check PubmedData for DOI
            if not doi:
                pubmed_data = article.find("PubmedData")
                if pubmed_data is not None:
                    for article_id in pubmed_data.findall(".//ArticleId"):
                        if article_id.get("IdType") == "doi":
                            doi = article_id.text
                            break

            # Authors
            authors = []
            for author in article_elem.findall(".//Author"):
                last_name = author.find("LastName")
                fore_name = author.find("ForeName")
                if last_name is not None and last_name.text:
                    name = last_name.text
                    if fore_name is not None and fore_name.text:
                        name = f"{fore_name.text} {name}"
                    authors.append(name)

            return PaperCandidate(
                pmid=pmid,
                doi=doi,
                title=title or "Untitled",
                abstract=abstract,
                journal=journal,
                year=year,
                authors=authors[:5],  # Limit authors
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                raw_source="pubmed",
            )
        except Exception as e:
            logger.error("pubmed_parse_article_error", error=str(e))
            return None
