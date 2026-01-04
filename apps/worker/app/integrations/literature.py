"""Literature search for worker - simplified synchronous version."""

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx
import structlog
import xml.etree.ElementTree as ET

logger = structlog.get_logger(__name__)


@dataclass
class PaperCandidate:
    """Normalized paper candidate from literature search."""

    title: str
    raw_source: str

    pmid: str | None = None
    doi: str | None = None
    abstract: str | None = None
    journal: str | None = None
    year: int | None = None
    authors: list[str] = field(default_factory=list)
    url: str | None = None

    def normalize_doi(self) -> str | None:
        if self.doi:
            return self.doi.lower().strip()
        return None

    def normalize_title(self) -> str:
        return self.title.lower().strip()

    def get_url(self) -> str | None:
        if self.url:
            return self.url
        if self.doi:
            return f"https://doi.org/{self.doi}"
        if self.pmid:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"
        return None


class LiteratureSearchService:
    """Synchronous literature search service for worker."""

    def __init__(
        self,
        ncbi_api_key: str | None = None,
        ncbi_tool: str = "pharmainsightai",
        ncbi_email: str = "admin@pharmainsight.io",
        timeout: float = 15.0,
    ):
        self.ncbi_api_key = ncbi_api_key
        self.ncbi_tool = ncbi_tool
        self.ncbi_email = ncbi_email
        self.timeout = timeout

    def search(
        self,
        query: str,
        limit: int = 20,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[PaperCandidate]:
        """Search PubMed and Europe PMC, return deduplicated results."""
        logger.info("literature_search_start", query=query, limit=limit, year_from=year_from, year_to=year_to)

        all_papers: list[PaperCandidate] = []

        # Search PubMed
        try:
            pubmed_papers = self._search_pubmed(query, limit, year_from, year_to)
            all_papers.extend(pubmed_papers)
            logger.info("pubmed_results", count=len(pubmed_papers))
        except Exception as e:
            logger.error("pubmed_search_error", error=str(e))

        # Search Europe PMC
        try:
            europepmc_papers = self._search_europepmc(query, limit, year_from, year_to)
            all_papers.extend(europepmc_papers)
            logger.info("europepmc_results", count=len(europepmc_papers))
        except Exception as e:
            logger.error("europepmc_search_error", error=str(e))

        # Deduplicate
        deduplicated = self._deduplicate(all_papers)
        logger.info(
            "literature_search_complete",
            total_raw=len(all_papers),
            total_deduplicated=len(deduplicated),
        )

        return deduplicated[:limit]  # Ensure we don't exceed limit after dedup

    def _search_pubmed(
        self,
        query: str,
        limit: int,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[PaperCandidate]:
        """Search PubMed using NCBI E-utilities."""
        # Step 1: ESearch to get PMIDs
        params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmax": limit,
            "retmode": "json",
            "tool": self.ncbi_tool,
            "email": self.ncbi_email,
        }
        if self.ncbi_api_key:
            params["api_key"] = self.ncbi_api_key

        # Add date filters
        if year_from or year_to:
            params["datetype"] = "pdat"  # Publication date
            if year_from:
                params["mindate"] = f"{year_from}/01/01"
            if year_to:
                params["maxdate"] = f"{year_to}/12/31"

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params=params,
            )
            response.raise_for_status()
            pmids = response.json().get("esearchresult", {}).get("idlist", [])

        if not pmids:
            return []

        # Step 2: EFetch to get full records
        fetch_params: dict[str, Any] = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "tool": self.ncbi_tool,
            "email": self.ncbi_email,
        }
        if self.ncbi_api_key:
            fetch_params["api_key"] = self.ncbi_api_key

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                params=fetch_params,
            )
            response.raise_for_status()
            return self._parse_pubmed_xml(response.text)

    def _parse_pubmed_xml(self, xml_text: str) -> list[PaperCandidate]:
        """Parse PubMed XML response."""
        papers = []
        try:
            root = ET.fromstring(xml_text)
            for article in root.findall(".//PubmedArticle"):
                paper = self._parse_pubmed_article(article)
                if paper:
                    papers.append(paper)
        except ET.ParseError as e:
            logger.error("pubmed_xml_parse_error", error=str(e))
        return papers

    def _parse_pubmed_article(self, article: ET.Element) -> PaperCandidate | None:
        """Parse a single PubmedArticle element."""
        try:
            medline = article.find("MedlineCitation")
            if medline is None:
                return None

            pmid_elem = medline.find("PMID")
            pmid = pmid_elem.text if pmid_elem is not None else None

            article_elem = medline.find("Article")
            if article_elem is None:
                return None

            title_elem = article_elem.find("ArticleTitle")
            title = title_elem.text if title_elem is not None else "Untitled"

            abstract = None
            abstract_elem = article_elem.find(".//AbstractText")
            if abstract_elem is not None:
                abstract = abstract_elem.text

            journal = None
            journal_elem = article_elem.find(".//Journal/Title")
            if journal_elem is not None:
                journal = journal_elem.text

            year = None
            year_elem = article_elem.find(".//PubDate/Year")
            if year_elem is not None and year_elem.text:
                try:
                    year = int(year_elem.text)
                except ValueError:
                    pass

            doi = None
            for eloc in article_elem.findall(".//ELocationID"):
                if eloc.get("EIdType") == "doi":
                    doi = eloc.text
                    break

            if not doi:
                pubmed_data = article.find("PubmedData")
                if pubmed_data is not None:
                    for article_id in pubmed_data.findall(".//ArticleId"):
                        if article_id.get("IdType") == "doi":
                            doi = article_id.text
                            break

            authors = []
            for author in article_elem.findall(".//Author")[:5]:
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
                authors=authors,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                raw_source="pubmed",
            )
        except Exception as e:
            logger.error("pubmed_parse_article_error", error=str(e))
            return None

    def _search_europepmc(
        self,
        query: str,
        limit: int,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[PaperCandidate]:
        """Search Europe PMC."""
        # Add year filter to query
        search_query = query
        if year_from and year_to:
            search_query = f"{query} AND (PUB_YEAR:[{year_from} TO {year_to}])"
        elif year_from:
            search_query = f"{query} AND (PUB_YEAR:[{year_from} TO 2100])"
        elif year_to:
            search_query = f"{query} AND (PUB_YEAR:[1900 TO {year_to}])"

        params = {
            "query": search_query,
            "format": "json",
            "pageSize": limit,
            "resultType": "core",
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        papers = []
        for result in data.get("resultList", {}).get("result", []):
            title = result.get("title")
            if not title:
                continue

            pmid = result.get("pmid")
            if pmid:
                pmid = str(pmid)

            doi = result.get("doi")

            year = None
            if result.get("pubYear"):
                try:
                    year = int(result.get("pubYear"))
                except ValueError:
                    pass

            authors = []
            for author in result.get("authorList", {}).get("author", [])[:5]:
                if author.get("fullName"):
                    authors.append(author.get("fullName"))

            url = None
            if pmid:
                url = f"https://europepmc.org/article/MED/{pmid}"
            elif doi:
                url = f"https://doi.org/{doi}"

            papers.append(
                PaperCandidate(
                    pmid=pmid,
                    doi=doi,
                    title=title.strip(),
                    abstract=result.get("abstractText"),
                    journal=result.get("journalTitle"),
                    year=year,
                    authors=authors,
                    url=url,
                    raw_source="europepmc",
                )
            )

        return papers

    def _deduplicate(self, papers: list[PaperCandidate]) -> list[PaperCandidate]:
        """Deduplicate papers by DOI, PMID, then title."""
        seen_dois: set[str] = set()
        seen_pmids: set[str] = set()
        seen_titles: set[str] = set()

        unique_papers: list[PaperCandidate] = []

        # Sort to prioritize papers with more metadata
        sorted_papers = sorted(
            papers,
            key=lambda p: (
                p.doi is not None,
                p.pmid is not None,
                len(p.abstract or ""),
            ),
            reverse=True,
        )

        for paper in sorted_papers:
            doi_norm = paper.normalize_doi()
            if doi_norm:
                if doi_norm in seen_dois:
                    continue
                seen_dois.add(doi_norm)

            if paper.pmid:
                if paper.pmid in seen_pmids:
                    continue
                seen_pmids.add(paper.pmid)

            title_norm = paper.normalize_title()
            if title_norm in seen_titles:
                continue
            seen_titles.add(title_norm)

            unique_papers.append(paper)

        return unique_papers
