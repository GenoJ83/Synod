import json
import logging
import os
import re
import time
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)

def _parse_json_object(raw: str) -> Dict[str, Any]:
    t = (raw or "").strip()
    if not t:
        return {}
    # Remove markdown code blocks if present
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```\s*$", "", t)
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode LLM JSON: {str(e)} | Raw snippet: {t[:200]}...")
        return {}

def analyze_with_gemini(text: str, api_key: str, model: str = "gemini-2.5-flash", timeout_s: float = 60.0) -> Dict[str, Any]:
    """Fallback compatible wrapper for the original Gemini logic."""
    # This will be replaced by the cascade logic below, but kept as a signature if needed by main.py
    return analyze_with_cascade(text)

def analyze_with_cascade(text: str) -> Dict[str, Any]:
    """
    Tries multiple LLM providers in sequence to ensure 100% reliability on free tiers.
    Order: Gemini 1.5 Pro -> Gemini 1.5 Flash -> Groq Llama 3.1 -> OpenRouter Free
    """
    gemini_key = (os.getenv("GOOGLE_API_KEY") or "").strip()
    groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
    openrouter_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()

    # Define the sequence of models to try
    # Each entry: (provider, model_name, api_key, base_url)
    cascade_configs = []
    
    # 1. Google Gemini (Primary - Most Tokens)
    if gemini_key:
        cascade_configs.append(("gemini", "gemini-3.1-pro", gemini_key, "https://generativelanguage.googleapis.com/v1beta"))
        cascade_configs.append(("gemini", "gemini-2.5-flash", gemini_key, "https://generativelanguage.googleapis.com/v1beta"))
    
    # 2. Groq (High Speed Fallback)
    if groq_key:
        cascade_configs.append(("groq", "llama-3.3-70b-versatile", groq_key, "https://api.groq.com/openai/v1"))
        cascade_configs.append(("groq", "llama-3.1-8b-instant", groq_key, "https://api.groq.com/openai/v1"))
    
    # 3. OpenRouter (Universal Safety Net)
    if openrouter_key:
        cascade_configs.append(("openrouter", "google/gemini-flash-1.5-8b", openrouter_key, "https://openrouter.ai/api/v1"))

    if not cascade_configs:
        logger.error("No LLM API keys configured in .env (Gemini, Groq, or OpenRouter missing)")
        return {"error": "No API keys configured"}

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

    for provider, model, key, base_url in cascade_configs:
        logger.info(f"Attempting analysis with {provider} ({model})...")
        try:
            if provider == "gemini":
                res = _call_gemini(model, key, base_url, instruction)
            else:
                res = _call_openai_compatible(provider, model, key, base_url, instruction)
            
            if res:
                logger.info(f"Successfully completed analysis using {provider} ({model})")
                return res
                
        except Exception as e:
            logger.warning(f"Provider {provider} ({model}) failed: {str(e)}")
            continue # Try next model in cascade

    logger.error("All LLM providers in the cascade failed.")
    return {"error": "AI Synthesis currently unavailable across all providers. Please try again later."}

def _call_gemini(model: str, key: str, base_url: str, prompt: str) -> Optional[Dict[str, Any]]:
    url = f"{base_url}/models/{model}:generateContent?key={key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 8192,
        },
    }
    with httpx.Client(timeout=90.0) as client:
        r = client.post(url, json=body)
        if r.status_code == 429 or r.status_code == 503:
            raise Exception(f"Gemini Busy ({r.status_code})")
        r.raise_for_status()
        data = r.json()
        
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text_out = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
        return _parse_json_object(text_out)

def _call_openai_compatible(provider: str, model: str, key: str, base_url: str, prompt: str) -> Optional[Dict[str, Any]]:
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    # OpenRouter requires extra headers
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://synod.edu"
        headers["X-Title"] = "Synod Analysis"

    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "response_format": {"type": "json_object"} if provider != "groq" else None # Groq doesn't always support json_object mode on all models
    }
    
    with httpx.Client(timeout=90.0) as client:
        r = client.post(url, headers=headers, json=body)
        if r.status_code == 429 or r.status_code == 503:
            raise Exception(f"{provider} Busy ({r.status_code})")
        r.raise_for_status()
        data = r.json()
        
        text_out = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return _parse_json_object(text_out)
