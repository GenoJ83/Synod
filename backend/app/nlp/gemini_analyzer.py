import json
import logging
import os
import re
from typing import Dict, Any, List
import httpx

logger = logging.getLogger(__name__)

def _parse_json_object(raw: str) -> Dict[str, Any]:
    t = (raw or "").strip()
    if not t:
        return {}
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```\s*$", "", t)
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode Gemini JSON: {str(e)} | Raw: {raw[:200]}...")
        return {}

def analyze_with_gemini(text: str, api_key: str, model: str = "gemini-2.0-flash", timeout_s: float = 60.0) -> Dict[str, Any]:
    """Generates summary, concepts, and quizzes using the Gemini API directly."""
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
    
    instruction = (
        "You are an expert NLP lecture assistant. Analyze the provided lecture text "
        "and return a single JSON object with the following exact structure and keys:\n"
        "{\n"
        '  "summary": "A concise executive summary of the lecture (2-3 paragraphs).",\n'
        '  "takeaways": ["str1", "str2"],\n'
        '  "concepts": ["term1", "term2"],\n'
        '  "concept_details": [{"term": "term1", "relevance": 0.95}],\n'
        '  "quiz": {\n'
        '    "fill_in_the_blanks": [{"type": "fill_in_the_blank", "question": "Fill in the blank: X is __________.", "options": ["A", "B", "C", "D"], "answer": "correct_option"}],\n'
        '    "mcqs": [{"type": "mcq", "question": "Question text?", "options": ["A", "B", "C", "D"], "answer": "correct_option"}],\n'
        '    "true_false": [{"type": "true_false", "question": "Statement?", "correct": true, "explanation": "Why it is true/false."}],\n'
        '    "comprehension": [{"type": "comprehension", "question": "Deeper question?", "options": ["A", "B", "C", "D"], "answer": "correct_option", "explanation": "Reasoning."}]\n'
        '  }\n'
        "}\n\n"
        "Requirements:\n"
        "- Generate exactly 5 questions per quiz category (except true_false which should have 10).\n"
        "- Ensure True/False statements are grammatically correct and based on factual points in the text.\n"
        "- Generate robust distractors for multiple choice options.\n"
        '- Return ONLY valid JSON, no markdown formatting.\n\n'
        f"SOURCE LECTURE TEXT:\n\n{text[:60000]}"
    )

    body = {
        "contents": [{"role": "user", "parts": [{"text": instruction}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
        },
    }

    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(url, json=body)
        if r.status_code >= 400:
            logger.error(f"Gemini API Error {r.status_code}: {r.text}")
        r.raise_for_status()
        data = r.json()

    try:
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text_out = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    except Exception as e:
        logger.error(f"Gemini output parsing failed: {str(e)}")
        text_out = "{}"

    res = _parse_json_object(text_out)
    return res
