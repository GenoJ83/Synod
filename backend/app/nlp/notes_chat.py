"""
Grounded Q&A over uploaded lecture notes (Gemini + retrieved excerpts).
"""

from __future__ import annotations

import logging
import os
import re
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

    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, json=body)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        logger.warning("Notes chat HTTP error: %s", e)
        raise RuntimeError("The tutor service returned an error. Try again in a moment.") from e
    except Exception as e:
        logger.warning("Notes chat request failed: %s", e)
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
