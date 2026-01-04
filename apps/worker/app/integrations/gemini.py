"""Synchronous Gemini provider for worker."""

import json
import os

import httpx
import structlog

logger = structlog.get_logger(__name__)


PAPER_SUMMARY_PROMPT = """You are a biomedical research analyst. Analyze the following paper and extract structured information.

PAPER INFORMATION:
Title: {title}
Abstract: {abstract}
Year: {year}
Journal: {journal}
PMID: {pmid}
DOI: {doi}

INSTRUCTIONS:
1. Extract information following the PICO framework (Population, Intervention, Comparator, Outcomes)
2. Identify study type (RCT, observational, review, meta-analysis, case study, etc.)
3. List key findings and limitations
4. Extract 1-3 evidence snippets that are EXACT VERBATIM quotes from the abstract
5. Set quality flags based on content analysis

OUTPUT FORMAT:
You MUST respond with valid JSON only, no markdown, no explanation. Use this exact structure:
{{
  "study_type": "string or null",
  "population": "string or null",
  "intervention": "string or null", 
  "comparator": "string or null",
  "outcomes": ["string", ...],
  "key_findings": ["string", ...],
  "limitations": ["string", ...],
  "evidence_snippets": [
    {{"quote": "exact verbatim text from abstract", "location": "abstract", "confidence": 0.9}}
  ],
  "quality_flags": {{
    "is_review": false,
    "has_humans": true,
    "has_animals": false,
    "has_rct_terms": false,
    "contains_numbers": true
  }}
}}

CRITICAL: evidence_snippets quotes MUST be exact substrings from the abstract. If no suitable quotes, use empty array.
CRITICAL: Respond with ONLY valid JSON, no other text."""


class GeminiProvider:
    """Synchronous Gemini provider for worker."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3-flash",
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def model_name(self) -> str:
        return self.model

    def summarize_paper(
        self,
        title: str,
        abstract: str | None,
        year: int | None,
        journal: str | None,
        pmid: str | None,
        doi: str | None,
    ) -> dict:
        """Generate a structured summary for a paper using Gemini."""
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not configured")

        prompt = PAPER_SUMMARY_PROMPT.format(
            title=title,
            abstract=abstract or "No abstract available",
            year=year or "Unknown",
            journal=journal or "Unknown",
            pmid=pmid or "N/A",
            doi=doi or "N/A",
        )

        logger.info("gemini_summarize_start", title=title[:50], model=self.model)

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json",
            },
        }

        # Retry with exponential backoff for rate limiting
        import time
        max_retries = 5
        data = None
        
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=90.0) as client:
                    response = client.post(url, json=payload)
                    
                    if response.status_code == 429:
                        wait_time = (2 ** attempt) * 3  # 3, 6, 12, 24, 48 seconds
                        logger.warning("gemini_rate_limit", wait_time=wait_time, attempt=attempt + 1)
                        time.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    break
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 3
                    logger.warning("gemini_rate_limit_retry", wait_time=wait_time, attempt=attempt + 1)
                    time.sleep(wait_time)
                    continue
                raise
        
        if data is None:
            raise ValueError(f"Max retries ({max_retries}) exceeded for Gemini API rate limiting")

        # Extract text from response
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            logger.error("gemini_response_parse_error", error=str(e))
            raise ValueError(f"Failed to parse Gemini response: {e}")

        # Clean up response
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines)

        # Parse JSON with repair for truncated responses
        try:
            summary = json.loads(text)
        except json.JSONDecodeError as e:
            # Try to repair truncated JSON
            logger.warning("gemini_json_truncated", error=str(e), attempting_repair=True)
            try:
                # Add missing closing brackets/braces
                repaired = text
                open_braces = repaired.count("{") - repaired.count("}")
                open_brackets = repaired.count("[") - repaired.count("]")
                
                # Close any open strings
                if repaired.count('"') % 2 == 1:
                    repaired += '"'
                
                repaired += "]" * open_brackets
                repaired += "}" * open_braces
                
                summary = json.loads(repaired)
                logger.info("gemini_json_repaired")
            except json.JSONDecodeError:
                logger.error("gemini_json_parse_error", error=str(e), text=text[:200])
                raise ValueError(f"Failed to parse LLM response as JSON: {e}")

        # Validate evidence snippets are in abstract
        if abstract and "evidence_snippets" in summary:
            validated_snippets = []
            for snippet in summary.get("evidence_snippets", []):
                quote = snippet.get("quote", "")
                if quote.lower() in abstract.lower():
                    validated_snippets.append(snippet)
                else:
                    logger.warning("evidence_snippet_not_in_abstract", quote=quote[:50])
            summary["evidence_snippets"] = validated_snippets

        logger.info(
            "gemini_summarize_complete",
            title=title[:50],
            study_type=summary.get("study_type"),
        )

        return summary
