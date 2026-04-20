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


def gemini_notes_chat_reply(
    *,
    notes_context: str,
    summary_hint: str,
    question: str,
    history: List[Dict[str, str]],
    api_key: str,
    model: Optional[str] = None,
    timeout_s: float = 75.0,
) -> str:
    model = (model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")).strip()
    url = f"{_GEMINI_URL.format(model=model)}?key={api_key}"

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

    body: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048,
        },
    }

    # Retry configuration
    max_retries = 3
    base_delay = 1.0  # seconds
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            with httpx.Client(timeout=timeout_s) as client:
                r = client.post(url, json=body)
                r.raise_for_status()
                data = r.json()
            break  # Success, exit retry loop
        except httpx.HTTPStatusError as e:
            last_exception = e
            status_code = e.response.status_code if e.response else "unknown"
            
            # Redact API key from logs
            url_str = str(e.request.url) if e.request else "unknown URL"
            if api_key in url_str:
                url_str = url_str.replace(api_key, "API_KEY_REDACTED")
            
            logger.warning(
                "Notes chat HTTP error (attempt %d/%d): %s - %s",
                attempt + 1,
                max_retries + 1,
                status_code,
                url_str
            )
            
            # Only retry on specific transient status codes
            if status_code in (503, 429, 500, 502, 504) and attempt < max_retries:
                delay = base_delay * (2 ** attempt) + (0.1 * attempt)  # exponential backoff with jitter
                logger.info("Retrying in %.1f seconds...", delay)
                time.sleep(delay)
                continue
            else:
                raise RuntimeError("The tutor service returned an error. Try again in a moment.") from e
        except Exception as e:
            last_exception = e
            logger.warning("Notes chat request failed (attempt %d/%d): %s", attempt + 1, max_retries + 1, e)
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            else:
                raise RuntimeError("Could not reach the tutor service.") from e

    try:
        parts = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )
        text_out = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    except (IndexError, TypeError, AttributeError):
        text_out = ""

    text_out = (text_out or "").strip()
    if not text_out:
        raise RuntimeError("Empty response from tutor model.")
    return text_out
