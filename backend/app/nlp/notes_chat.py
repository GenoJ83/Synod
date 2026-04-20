"""
Grounded Q&A over uploaded lecture notes (Gemini + retrieved excerpts).
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

import httpx
from sentence_transformers import util

from app.nlp.explanation_generator import _is_assignment_context_blob

logger = logging.getLogger(__name__)

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_MAX_NOTES_CHARS = 600_000
_MAX_QUESTION_CHARS = 4000
_MAX_HISTORY_TURNS = 16
_MAX_MESSAGE_IN_TURN = 6000


def notes_chat_enabled() -> bool:
    if os.getenv("USE_NOTES_CHAT", "true").lower() in ("0", "false", "no"):
        return False
    key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    return bool(key)


def build_retrieved_notes_context(
    notes: str,
    question: str,
    extractor,
    *,
    max_chars: int = 32000,
    max_sentences: int = 28,
    min_score: float = 0.22,
) -> str:
    """Topically relevant sentences from notes for prompting (bounded size)."""
    notes = (notes or "").strip()
    question = (question or "").strip()
    if len(notes) > 120_000:
        notes = notes[:120_000] + "\n…"
    if not notes:
        return ""
    if not question:
        return notes[:max_chars]

    sentences = re.split(r"(?<=[.!?])\s+", notes)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 40]

    if not extractor or not getattr(extractor, "has_deps", False):
        return notes[:max_chars]

    try:
        q_emb = extractor.model.encode([question], convert_to_tensor=True)
        sent_embs = extractor.model.encode(sentences, convert_to_tensor=True)
        scores = util.cos_sim(q_emb, sent_embs).cpu().numpy().flatten()
        ranked = scores.argsort()[::-1]
    except Exception:
        return notes[:max_chars]

    parts: List[str] = []
    total = 0
    for idx in ranked:
        if len(parts) >= max_sentences:
            break
        if scores[idx] < min_score:
            break
        sent = sentences[int(idx)]
        if _is_assignment_context_blob(sent):
            continue
        if len(sent.split()) < 6:
            continue
        if total + len(sent) + 2 > max_chars:
            break
        parts.append(sent)
        total += len(sent) + 2

    if not parts:
        return notes[:max_chars]
    return "\n\n".join(parts)


def _format_history_block(history: List[Dict[str, str]]) -> str:
    lines: List[str] = []
    for turn in history[-_MAX_HISTORY_TURNS:]:
        role = (turn.get("role") or "").strip().lower()
        content = (turn.get("content") or "").strip()
        if not content:
            continue
        content = content[:_MAX_MESSAGE_IN_TURN]
        if role == "user":
            lines.append(f"Student: {content}")
        elif role == "assistant":
            lines.append(f"Assistant: {content}")
    return "\n\n".join(lines).strip()


def notes_chat_with_cascade(
    *,
    notes_context: str,
    summary_hint: str,
    question: str,
    history: List[Dict[str, str]],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout_s: float = 75.0,
) -> str:
    """
    Multi-provider cascade for notes chat.
    If api_key is provided, uses only that provider. Otherwise tries all configured providers.
    """
    # Build provider configurations
    providers = []
    
    # Check each provider from environment
    gemini_key = (os.getenv("GOOGLE_API_KEY") or "").strip()
    groq_key = (os.getenv("GROQ_API_KEY") or "").strip()\n    openrouter_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()\n    anthropic_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()\n    \n    # If explicit api_key provided, use only that (for backward compatibility)\n    if api_key:\n        providers = [("gemini", model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), api_key, "https://generativelanguage.googleapis.com/v1beta")]\n    else:\n        # Try all configured providers in order\n        if gemini_key:\n            providers.append(("gemini", "gemini-2.5-flash", gemini_key, "https://generativelanguage.googleapis.com/v1beta"))\n        if groq_key:\n            providers.append(("groq", "llama-3.3-70b-versatile", groq_key, "https://api.groq.com/openai/v1"))\n        if openrouter_key:\n            providers.append(("openrouter", "google/gemini-flash-1.5-8b", openrouter_key, "https://openrouter.ai/api/v1"))\n        if anthropic_key:\n            providers.append(("anthropic", "claude-3.5-sonnet-20240620", anthropic_key, "https://api.anthropic.com/v1"))
    
    if not providers:
        raise RuntimeError("No LLM API keys configured for notes chat (set GOOGLE_API_KEY, GROQ_API_KEY, or OPENROUTER_API_KEY)")

    hint = (summary_hint or "").strip()
    hint_block = ""
    if hint:
        hint_block = f"Course summary (may omit details; prefer NOTES for facts):\n{hint[:2400]}\n\n"

    hist = _format_history_block(history)
    hist_block = f"Earlier in this conversation:\n{hist}\n\n" if hist else ""

    prompt = (
        "You are a patient tutor helping a student study their own uploaded notes.\n"
        "Rules:\n"
        "- Ground your answer primarily in the NOTES excerpt below. You may use the summary only as orientation.\n"
        "- If the notes do not contain enough information, say clearly that it is not in the materials and suggest what to re-read or ask.\n"
        "- Do not invent paper titles, dates, or citations that are not in the notes.\n"
        "- Be concise but clear; use short paragraphs or bullets when helpful.\n\n"
        f"{hint_block}"
        f"{hist_block}"
        "NOTES (retrieved excerpt from the student's upload):\n"
        f'"""\n{notes_context}\n"""\n\n'
        f"Student question:\n{question.strip()}"
    )

    last_error = None
    
    for provider, model_name, key, base_url in providers:
        logger.info("Trying notes chat with %s (%s)...", provider, model_name)
        
        # Prepare request based on provider
                if provider == "gemini":\n                    url = f"{_GEMINI_URL.format(model=model_name)}?key={key}"\n                    body = {\n                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],\n                        "generationConfig": {\n                            "temperature": 0.4,\n                            "maxOutputTokens": 2048,\n                        },\n                    }\n                elif provider == "anthropic":\n                    url = f"{base_url}/messages"\n                    headers = {\n                        "x-api-key": key,\n                        "anthropic-version": "2023-06-01",\n                        "Content-Type": "application/json"\n                    }\n                    body = {\n                        "model": model_name,\n                        "max_tokens": 2048,\n                        "temperature": 0.4,\n                        "messages": [{"role": "user", "content": prompt}]\n                    }\n                else:\n                    url = f"{base_url}/chat/completions"\n                    headers = {\n                        "Authorization": f"Bearer {key}",\n                        "Content-Type": "application/json"\n                    }\n                    body = {\n                        "model": model_name,\n                        "messages": [{"role": "user", "content": prompt}],\n                        "temperature": 0.4,\n                        "max_tokens": 2048,\n                    }
        
        # Retry logic per provider
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(timeout=timeout_s) as client:
                    if provider == "gemini":
                        r = client.post(url, json=body)
                    else:
                        r = client.post(url, headers=headers, json=body)
                r.raise_for_status()
                data = r.json()
                
                # Success! Parse and return\n                if provider == "gemini":\n                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])\n                    text_out = "".join(p.get("text", "") for p in parts if isinstance(p, dict))\n                elif provider == "anthropic":\n                    text_out = data.get("content", [{}])[0].get("text", "")\n                else:\n                    text_out = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                text_out = (text_out or "").strip()
                if text_out:
                    return text_out
                else:
                    raise ValueError("Empty response from model")
                    
            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code if e.response else "unknown"
                
                # Redact API key from logs
                url_str = str(e.request.url) if e.request else "unknown URL"
                if key in url_str:
                    url_str = url_str.replace(key, "API_KEY_REDACTED")
                
                logger.warning(
                    "Notes chat %s HTTP error (attempt %d/%d): %s - %s",
                    provider, attempt + 1, max_retries + 1, status_code, url_str
                )
                
                # Retry on transient errors
                if status_code in (429, 503, 500, 502, 504) and attempt < max_retries:
                    delay = base_delay * (2 ** attempt) + (0.1 * attempt)
                    logger.info("Retrying in %.1f seconds...", delay)
                    time.sleep(delay)
                    continue
                else:
                    # Non-retryable or max retries exceeded - try next provider
                    break
            
            except Exception as e:
                last_error = e
                logger.warning("Notes chat %s request failed (attempt %d/%d): %s", provider, attempt + 1, max_retries + 1, e)
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                break
    
    # If we get here, all providers failed
    # Sanitize error: never expose API keys or full URLs to the caller
    safe_error = str(last_error)
    # Redact anything that looks like a key= query param
    safe_error = re.sub(r"key=[A-Za-z0-9_\-]+", "key=[REDACTED]", safe_error)
    # If a full URL is still in the message, strip it entirely
    safe_error = re.sub(r"https?://\S+", "[provider URL redacted]", safe_error)
    raise RuntimeError(f"AI assistant temporarily unavailable. Please try again in a moment.")
