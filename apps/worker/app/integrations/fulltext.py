"""PMC Full-Text Fetcher Service.

Fetches full-text content from PubMed Central (PMC) for Open Access papers.
"""

import time
import httpx
import structlog

logger = structlog.get_logger(__name__)

# PMC BioC API endpoint for Open Access articles
PMC_BIOC_API = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmc_id}/unicode"

# Alternative: PMC OA Web Service
PMC_OA_API = "https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi"


class FullTextFetcher:
    """Service to fetch full-text from PMC for Open Access papers."""

    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    def fetch_full_text(self, pmc_id: str) -> str | None:
        """Fetch full-text from PMC BioC API.
        
        Args:
            pmc_id: PubMed Central ID (e.g., "PMC1234567" or just "1234567")
            
        Returns:
            Full text content or None if not available
        """
        # Normalize PMC ID
        pmc_id_clean = pmc_id.replace("PMC", "").strip()
        
        url = PMC_BIOC_API.format(pmc_id=pmc_id_clean)
        
        logger.info("fetching_full_text", pmc_id=pmc_id)
        
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(url)
                    
                    if response.status_code == 404:
                        logger.info("pmc_not_found", pmc_id=pmc_id)
                        return None
                    
                    if response.status_code == 429:
                        wait_time = (2 ** attempt) * 2
                        logger.warning("pmc_rate_limit", wait_time=wait_time)
                        time.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Extract text from BioC JSON structure
                    text_parts = self._extract_text_from_bioc(data)
                    
                    if text_parts:
                        full_text = "\n\n".join(text_parts)
                        logger.info("full_text_fetched", pmc_id=pmc_id, length=len(full_text))
                        return full_text
                    
                    return None
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    time.sleep(wait_time)
                    continue
                logger.error("pmc_http_error", pmc_id=pmc_id, error=str(e))
                return None
            except Exception as e:
                logger.error("pmc_fetch_error", pmc_id=pmc_id, error=str(e))
                return None
        
        return None

    def _extract_text_from_bioc(self, data: dict) -> list[str]:
        """Extract text sections from BioC JSON format.
        
        BioC format: documents -> passages -> text
        We extract: Abstract, Introduction, Methods, Results, Discussion
        """
        text_parts = []
        target_sections = ["abstract", "intro", "method", "result", "discussion", "conclusion"]
        
        try:
            documents = data.get("documents", [])
            for doc in documents:
                passages = doc.get("passages", [])
                for passage in passages:
                    section_type = passage.get("infons", {}).get("section_type", "").lower()
                    text = passage.get("text", "")
                    
                    # Include if section is relevant or if section_type not specified
                    if any(target in section_type for target in target_sections) or not section_type:
                        if text and len(text) > 50:  # Skip very short passages
                            text_parts.append(text)
            
            return text_parts
        except Exception as e:
            logger.error("bioc_parse_error", error=str(e))
            return []

    def fetch_and_truncate(self, pmc_id: str, max_tokens: int = 8000) -> str | None:
        """Fetch full text and truncate to token limit.
        
        Args:
            pmc_id: PMC ID
            max_tokens: Maximum number of tokens (rough estimate: 4 chars = 1 token)
            
        Returns:
            Truncated full text or None
        """
        full_text = self.fetch_full_text(pmc_id)
        
        if not full_text:
            return None
        
        # Rough token estimation (4 chars ~= 1 token)
        max_chars = max_tokens * 4
        
        if len(full_text) > max_chars:
            # Truncate and add indicator
            full_text = full_text[:max_chars] + "\n\n[... truncated for length ...]"
        
        return full_text
