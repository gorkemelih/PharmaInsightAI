"""Synchronous run synthesis service for worker."""

import json
import os
import time

import httpx
import structlog

logger = structlog.get_logger(__name__)


RUN_SYNTHESIS_PROMPT = """You are a biomedical research analyst synthesizing findings from multiple studies.

USER QUERY: {query_text}

EVIDENCE FROM {paper_count} PAPERS:
{evidence_summary}

INSTRUCTIONS:
1. Synthesize the findings across all papers
2. For each paper, extract 1-2 DIRECT QUOTES that support key findings
3. Identify consensus, contradictions, and gaps
4. Generate evidence-based claims with citations
5. Every key_point and claim MUST reference at least one paper_id

OUTPUT FORMAT:
You MUST respond with valid JSON only, no markdown, no explanation:
{{
  "tldr": "One paragraph executive summary of all findings",
  "key_points": [
    {{"text": "Key finding", "citations": [{{"paper_id": "uuid", "pmid": "...", "doi": "..."}}]}}
  ],
  "consensus_level": "high|medium|low",
  "contradictions": [
    {{"text": "Contradiction description", "citations": [...]}}
  ],
  "gaps": ["Research gap 1", "Research gap 2"],
  "safety_notes": ["Safety note if applicable"],
  "claims_draft": [
    {{
      "claim": "Marketing claim text",
      "allowed": true,
      "rationale": "Why this claim is/isn't supported",
      "citations": [{{"paper_id": "...", "pmid": "...", "doi": "..."}}]
    }}
  ],
  "paper_snippets": [
    {{
      "paper_id": "uuid-of-paper",
      "snippets": [
        {{"quote": "Exact text from abstract/content", "section": "abstract|results|conclusion"}}
      ]
    }}
  ]
}}

CRITICAL RULES:
- Every key_point MUST have at least 1 citation with paper_id
- Every claim MUST have at least 1 citation with paper_id
- paper_snippets MUST contain direct quotes from the paper's abstract/content
- Quotes must be EXACT substrings, not paraphrased
- Set allowed=false if evidence is insufficient
- Respond with ONLY valid JSON, no other text"""


class RunSynthesisService:
    """Service to synthesize multiple paper findings."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3-flash",
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def synthesize(
        self,
        query_text: str,
        evidence_rows: list[dict],
    ) -> dict:
        """Synthesize findings from multiple papers."""
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not configured")

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
            paper_count=len(evidence_rows),
            evidence_summary=evidence_summary,
        )

        logger.info("run_synthesis_start", query=query_text[:50], papers=len(evidence_rows))

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4096,
            },
        }

        # Retry with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=90.0) as client:
                    response = client.post(url, json=payload)
                    if response.status_code == 429:
                        wait_time = (2 ** attempt) * 3
                        logger.warning("gemini_rate_limit", wait_time=wait_time)
                        time.sleep(wait_time)
                        continue
                    response.raise_for_status()
                    data = response.json()
                    break
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 3
                    time.sleep(wait_time)
                    continue
                raise
        else:
            raise ValueError("Max retries exceeded for Gemini API")

        # Extract text
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
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

        # Parse JSON
        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("synthesis_json_parse_error", error=str(e), text=text[:200])
            raise ValueError(f"Failed to parse synthesis response: {e}")

        # Validate citations exist
        for kp in result.get("key_points", []):
            if not kp.get("citations"):
                logger.warning("key_point_missing_citation", text=kp.get("text", "")[:50])

        logger.info("run_synthesis_complete", consensus=result.get("consensus_level"))

        return result
