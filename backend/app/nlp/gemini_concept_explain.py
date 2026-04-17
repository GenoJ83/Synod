"""
Optional Gemini calls for on-demand key-concept explanations.

Enable with GOOGLE_API_KEY and USE_GEMINI_CONCEPT_EXPLAIN=true (see main /explain-concept).
Uses only a retrieved snippet of the lecture as grounding, then falls back to the
local ExplanationGenerator output if the API fails or returns invalid JSON.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _gemini_enabled() -> bool:
    if os.getenv("USE_GEMINI_CONCEPT_EXPLAIN", "").lower() not in ("1", "true", "yes"):
        return False
    key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    return bool(key)


def _parse_json_object(raw: str) -> Optional[Dict[str, Any]]:
    t = (raw or "").strip()
    if not t:
        return None
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```\s*$", "", t)
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def explain_concept_with_gemini(
    *,
    concept: str,
    snippet: str,
    api_key: str,
    model: Optional[str] = None,
    timeout_s: float = 45.0,
) -> Optional[Dict[str, str]]:
    """
    Returns {"term", "definition", "context"} or None on failure.
    ``snippet`` should be lecture-derived text only (bounded size).
    """
    concept = (concept or "").strip()
    snippet = (snippet or "").strip()
    if not concept:
        return None

    model = (model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")).strip()
    url = f"{_GEMINI_URL.format(model=model)}?key={api_key}"

    instruction = (
        "You help a student understand one key term from a lecture. "
        "You will receive SOURCE_SNIPPET: excerpts from the lecture (may contain OCR noise).\n\n"
        "Requirements:\n"
        "1. DEFINITION: Provide a clear 2 to 4 sentence technical definition. If the SOURCE_SNIPPET "
        "contains a specific local definition, prioritize it. If the snippet is empty or does not "
        "provide a definition, use your own general expert knowledge of the term's standard technical meaning.\n"
        "2. CONTEXT: Provide 1 or 2 short sentences quoting or paraphrasing ONLY what the snippet says "
        "about the term. If the snippet does not discuss the term at all, return an EMPTY string for context.\n"
        "3. FORMAT: Respond with a single JSON object only, keys exactly: \"definition\", \"context\".\n\n"
        f'CONCEPT: "{concept}"\n\nSOURCE_SNIPPET:\n"""{snippet}"""'
    )

    body: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": instruction}]}],
        "generationConfig": {
            "temperature": 0.35,
            "maxOutputTokens": 768,
            "responseMimeType": "application/json",
        },
    }

    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, json=body)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        logger.warning("Gemini concept explain HTTP error: %s", e)
        return None
    except Exception as e:
        logger.warning("Gemini concept explain request failed: %s", e)
        return None

    try:
        parts = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )
        text_out = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    except (IndexError, TypeError, AttributeError):
        text_out = ""

    parsed = _parse_json_object(text_out)
    if not parsed:
        logger.warning("Gemini concept explain: could not parse JSON from model output")
        return None

    definition = str(parsed.get("definition", "")).strip()
    context = str(parsed.get("context", "")).strip()
    if not definition:
        return None

    return {"term": concept, "definition": definition, "context": context}
