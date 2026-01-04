"""Unified Gemini LLM Client."""

import json
import os
import time
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class GeminiClient:
    """Unified client for Google Gemini interactions."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not configured")

    def generate_json(self, prompt: str, temperature: float = 0.1, max_retries: int = 3) -> dict[str, Any]:
        """
        Generate JSON content from Gemini with retries and JSON repair.
        
        Args:
            prompt: Input text prompt
            temperature: Generation temperature (0.0 to 1.0)
            max_retries: Number of retry attempts for rate limits
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If API key missing, max retries exceeded, or JSON parse fails
        """
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json",
            },
        }

        # Retry loop for rate limiting
        data = None
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=90.0) as client:
                    response = client.post(url, json=payload)
                    
                    if response.status_code == 429:
                        wait_time = (2 ** attempt) * 3
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
            raise ValueError(f"Max retries ({max_retries}) exceeded for Gemini API")

        # Extract text
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            logger.error("gemini_response_parse_error", error=str(e), raw=data)
            raise ValueError(f"Failed to parse Gemini response: {e}")

        # Clean markdown
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines)

        # Parse JSON with basic repair attempt
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # Simple repair: try to close brackets if truncated
            logger.warning("gemini_json_truncated", error=str(e), attempting_repair=True)
            try:
                repaired = text
                # Simple heuristic to close open structures
                # This is not a full parser but catches common truncation cases
                open_braces = repaired.count("{") - repaired.count("}")
                open_brackets = repaired.count("[") - repaired.count("]")
                
                if repaired.count('"') % 2 == 1:
                    repaired += '"'
                
                repaired += "]" * open_brackets
                repaired += "}" * open_braces
                
                result = json.loads(repaired)
                logger.info("gemini_json_repaired")
                return result
            except json.JSONDecodeError:
                logger.error("gemini_json_parse_error", error=str(e), text=text[:200])
                raise ValueError(f"Failed to parse LLM response as JSON: {e}")
