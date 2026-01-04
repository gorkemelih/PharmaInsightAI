"""Centralized prompt registry for LLM tasks."""

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


RUN_SYNTHESIS_PROMPT = """You are a biomedical research analyst synthesizing findings from multiple studies.

USER QUERY: {query_text}
OUTPUT LANGUAGE: {language}

EVIDENCE FROM {paper_count} PAPERS:
{evidence_summary}

INSTRUCTIONS:
1. Synthesize the findings across all papers
2. For each paper, extract 1-2 DIRECT QUOTES that support key findings
3. Identify consensus, contradictions, and gaps
4. Generate evidence-based claims with citations
5. Every key_point and claim MUST reference at least one paper_id
6. Your entire response content (tldr, key_points text, etc.) MUST be in {language} language. Keep JSON keys in English.

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
