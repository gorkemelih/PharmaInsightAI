"""Gemini Flash LLM provider."""

import json
import structlog
import google.generativeai as genai

from app.llm.base import PaperInput, PaperSummarySchema

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
    {{"quote": "exact verbatim text from abstract", "location": "abstract", "confidence": 0.0-1.0}}
  ],
  "quality_flags": {{
    "is_review": boolean,
    "has_humans": boolean or null,
    "has_animals": boolean or null,
    "has_rct_terms": boolean,
    "contains_numbers": boolean
  }}
}}

CRITICAL: evidence_snippets quotes MUST be exact substrings from the abstract. If no suitable quotes, use empty array.
CRITICAL: Respond with ONLY valid JSON, no other text."""


class GeminiFlashProvider:
    """Gemini Flash LLM provider for paper summarization."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3-flash",
    ):
        self.api_key = api_key
        self.model = model
        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel(model)

    @property
    def model_name(self) -> str:
        return self.model

    async def summarize_paper(self, paper: PaperInput) -> PaperSummarySchema:
        """Generate a structured summary for a paper using Gemini."""
        # Build prompt
        prompt = PAPER_SUMMARY_PROMPT.format(
            title=paper.title,
            abstract=paper.abstract or "No abstract available",
            year=paper.year or "Unknown",
            journal=paper.journal or "Unknown",
            pmid=paper.pmid or "N/A",
            doi=paper.doi or "N/A",
        )

        logger.info(
            "gemini_summarize_start",
            title=paper.title[:50],
            model=self.model,
        )

        try:
            # Call Gemini API
            response = self._client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for structured output
                    max_output_tokens=2048,
                ),
            )

            # Extract text response
            response_text = response.text.strip()

            # Clean up response (remove markdown code blocks if present)
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                # Remove first and last lines if they are code block markers
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines)

            # Parse JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error("gemini_json_parse_error", error=str(e), response=response_text[:200])
                raise ValueError(f"Failed to parse LLM response as JSON: {e}")

            # Validate with Pydantic
            summary = PaperSummarySchema.model_validate(data)

            # Validate evidence snippets are in abstract
            if paper.abstract:
                validated_snippets = []
                for snippet in summary.evidence_snippets:
                    if snippet.quote.lower() in paper.abstract.lower():
                        validated_snippets.append(snippet)
                    else:
                        logger.warning(
                            "evidence_snippet_not_in_abstract",
                            quote=snippet.quote[:50],
                        )
                summary.evidence_snippets = validated_snippets

            logger.info(
                "gemini_summarize_complete",
                title=paper.title[:50],
                study_type=summary.study_type,
                findings_count=len(summary.key_findings),
            )

            return summary

        except Exception as e:
            logger.error("gemini_summarize_error", error=str(e), title=paper.title[:50])
            raise


def get_gemini_provider(api_key: str, model: str = "gemini-3-flash") -> GeminiFlashProvider:
    """Factory function to create a Gemini provider."""
    return GeminiFlashProvider(api_key=api_key, model=model)
