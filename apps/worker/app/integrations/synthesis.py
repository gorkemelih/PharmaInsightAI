"""Synchronous run synthesis service for worker."""

import os
import structlog

from app.core.llm import GeminiClient
from app.core.prompts import RUN_SYNTHESIS_PROMPT

logger = structlog.get_logger(__name__)


class RunSynthesisService:
    """Service to synthesize multiple paper findings."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.client = GeminiClient(api_key=self.api_key, model=model)

    def synthesize(
        self,
        query_text: str,
        evidence_rows: list[dict],
        language: str = "en",
    ) -> dict:
        """Synthesize findings from multiple papers."""
        
        if not evidence_rows:
            return {
                "tldr": "No evidence available for synthesis.",
                "key_points": [],
                "consensus_level": "low",
                "contradictions": [],
                "gaps": ["Insufficient evidence to draw conclusions"],
                "safety_notes": [],
                "claims_draft": [],
            }

        # Build evidence summary for prompt
        evidence_lines = []
        for row in evidence_rows[:15]:  # Limit to 15 papers
            citation = row.get("citation", {})
            line = f"[Paper ID: {row.get('paper_id')}]\n"
            line += f"  Title: {citation.get('title', 'N/A')}\n"
            line += f"  PMID: {citation.get('pmid', 'N/A')}, DOI: {citation.get('doi', 'N/A')}\n"
            line += f"  Study Type: {row.get('study_type', 'N/A')}\n"
            line += f"  Population: {row.get('population', 'N/A')}\n"
            line += f"  Intervention: {row.get('intervention', 'N/A')}\n"
            line += f"  Outcomes: {', '.join(row.get('outcomes', []))}\n"
            line += f"  Key Findings: {'; '.join(row.get('key_findings', []))}\n"
            evidence_lines.append(line)

        evidence_summary = "\n".join(evidence_lines)

        prompt = RUN_SYNTHESIS_PROMPT.format(
            query_text=query_text,
            language=language,
            paper_count=len(evidence_rows),
            evidence_summary=evidence_summary,
        )

        logger.info("run_synthesis_start", query=query_text[:50], papers=len(evidence_rows))

        # Use unified client
        # default temperature (0.1) from llm.py is good, but original code used 0.2
        result = self.client.generate_json(prompt, temperature=0.2, max_retries=3)

        # Validate citations exist
        for kp in result.get("key_points", []):
            if not kp.get("citations"):
                logger.warning("key_point_missing_citation", text=kp.get("text", "")[:50])

        logger.info("run_synthesis_complete", consensus=result.get("consensus_level"))

        return result
