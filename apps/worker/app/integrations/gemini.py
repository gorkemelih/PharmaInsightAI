"""Synchronous Gemini provider for worker."""

import os
import structlog

from app.core.llm import GeminiClient
from app.core.prompts import PAPER_SUMMARY_PROMPT

logger = structlog.get_logger(__name__)


class GeminiProvider:
    """Synchronous Gemini provider for worker."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.client = GeminiClient(api_key=self.api_key, model=model)

    @property
    def model_name(self) -> str:
        return self.client.model

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
        
        prompt = PAPER_SUMMARY_PROMPT.format(
            title=title,
            abstract=abstract or "No abstract available",
            year=year or "Unknown",
            journal=journal or "Unknown",
            pmid=pmid or "N/A",
            doi=doi or "N/A",
        )

        logger.info("gemini_summarize_start", title=title[:50], model=self.model_name)

        # Use unified client
        # Use slightly lower temperature for structured extraction
        summary = self.client.generate_json(prompt, temperature=0.1, max_retries=5)

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
