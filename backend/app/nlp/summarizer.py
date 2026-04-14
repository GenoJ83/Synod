import re
import os
try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

import hashlib
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger("app.nlp.summarizer")

# Bumped when summary behavior changes so cache does not return old collapsed output.
_SUMMARY_CACHE_SALT = "v10-summary-deck-bib-scrub"

# Slide titles + instructor rows, bibliography tails, and OCR phrase stacks (pre-BART + extractive filters).
_LECTURER_COLON = re.compile(r"(?i)\blecturer\s*:")
_INTRO_THEN_LECTURER = re.compile(r"(?i)\bintroduction\s+to\s+[^.\n]{3,120}\s+lecturer\s*:")
_JOURNAL_VOLUME_PAGES = re.compile(
    r"(?i)\b\d{1,3}\.\d{1,3}\s*\(\s*(?:19|20)\d{2}\s*\)\s*:\s*\d{3,5}\s*[–-]\s*\d{3,5}\b"
)
_JOURNAL_PROPER = re.compile(
    r"(?i)\b(?:cerebral\s+cortex|nature\s+neuroscience|journal\s+of|"
    r"proceedings\s+of|ieee\s+transactions|arxiv)\b"
)
_QUOTED_TITLE_THEN_JOURNAL = re.compile(
    r'(?i)"[^"]{20,400}"\s*.{0,120}\(\s*(?:19|20)\d{2}\s*\)'
)
_DL_OCR_STACK = re.compile(
    r"(?i)deep\s+learning\s+combination\s+of\s+non[-\s]?linear"
)


def _is_slide_metadata_or_bibliography_unit(t: str) -> bool:
    """True for title/instructor lines, citation tails, and known OCR junk (not lecture substance)."""
    s = re.sub(r"\s+", " ", (t or "").strip())
    if len(s) < 10:
        return True
    sl = s.lower()
    if _LECTURER_COLON.search(s):
        return True
    if _INTRO_THEN_LECTURER.search(s):
        return True
    if re.search(r"(?i)\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b", s):
        if len(s.split()) <= 12 and not re.search(r"(?i)\b(is|are|was|were|uses|means|defines|shows|trains)\b", sl):
            return True
    if _JOURNAL_VOLUME_PAGES.search(s):
        return True
    if _JOURNAL_PROPER.search(s) and re.search(r"\(\s*(?:19|20)\d{2}\s*\)", s):
        return True
    if _QUOTED_TITLE_THEN_JOURNAL.search(s):
        return True
    if re.search(r"(?i)\bet\s+al\b", s):
        return True
    if _DL_OCR_STACK.search(s) and not re.search(r"(?i)\b(is|are|was|were|means|refers)\b", sl):
        return True
    return False


def _scrub_text_for_neural_summary(text: str) -> str:
    """Strip deck metadata and references before seq2seq so BART is not trained on garbage from the first slide."""
    raw = (text or "").replace("\r\n", "\n").strip()
    if not raw:
        return ""
    kept_lines: List[str] = []
    for ln in raw.split("\n"):
        s = re.sub(r"\s+", " ", ln.strip())
        if not s or _is_slide_metadata_or_bibliography_unit(s):
            continue
        s2 = _QUOTED_TITLE_THEN_JOURNAL.sub("", s)
        s2 = re.sub(r"\s+", " ", s2).strip()
        if s2 and not _is_slide_metadata_or_bibliography_unit(s2):
            kept_lines.append(s2)
    joined = " ".join(kept_lines) if kept_lines else re.sub(r"\s+", " ", raw)
    units = re.split(r"(?<=[.!?])\s+", joined)
    kept_u: List[str] = []
    for u in units:
        u = re.sub(r"\s+", " ", u.strip())
        if len(u) < 22:
            continue
        if _is_slide_metadata_or_bibliography_unit(u):
            continue
        kept_u.append(u)
    out = " ".join(kept_u) if kept_u else joined
    return re.sub(r"\s+", " ", out).strip()


def _clean_summary_output(text: str) -> str:
    """Remove any metadata or citation sentences that slipped through post-hoc."""
    s = re.sub(r"\s+", " ", (text or "").strip())
    if not s:
        return s
    parts = re.split(r"(?<=[.!?])\s+", s)
    out: List[str] = []
    for p in parts:
        p = p.strip()
        if len(p) < 18:
            continue
        if _is_slide_metadata_or_bibliography_unit(p):
            continue
        out.append(p)
    if not out:
        # No `.?` splits (e.g. one long clause): treat whole string as one unit.
        if len(s) >= 18 and not _is_slide_metadata_or_bibliography_unit(s):
            return s
        return ""
    return " ".join(out).strip()


def _safe_clean_summary_output(text: str) -> str:
    """Drop bad sentences; if one paragraph is entirely junk, try other paragraphs or strip the opener prefix."""
    raw = (text or "").strip()
    cleaned = _clean_summary_output(raw)
    if cleaned.strip():
        return cleaned
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    kept = []
    for b in blocks:
        c = _clean_summary_output(b)
        if c.strip():
            kept.append(c.strip())
    if kept:
        return "\n\n".join(kept)
    stripped = re.sub(
        r"(?i)^this\s+lecture\s+introduces\s+main\s+themes\s+from\s+the\s+session:\s*",
        "",
        raw,
    ).strip()
    stripped = re.sub(
        r"(?i)introduction\s+to\s+[^.!?\n]{3,120}\s+lecturer\s*:\s*.+$",
        " ",
        stripped,
    )
    stripped = re.sub(r"(?i)\blecturer\s*:\s*.+$", " ", stripped, flags=re.MULTILINE)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    if stripped:
        return stripped
    return ""


def _glitch_token_fraction(text: str, max_scan: int = 160) -> float:
    """Tokens with subword-merge glitches (e.g. aicWHAT, commcomm)."""
    words = text.split()
    if not words:
        return 0.0
    scan = words[: max_scan if max_scan > 0 else len(words)]
    bad = 0
    for w in scan:
        w2 = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", w)
        if not w2 or not re.search(r"[A-Za-z]", w2):
            continue
        if re.search(r"[a-z][A-Z]", w2):
            bad += 1
            continue
        if len(w2) > 9 and re.search(r"(.)\1{2,}", w2.lower()):
            bad += 0.8
    return float(bad) / max(len(scan), 1)


def _looks_like_degenerate_summary(s: str) -> bool:
    """Detect seq2seq collapse: LoRA mismatch, insane min_length, stuck decoding."""
    if not s:
        return True
    words = s.split()
    if len(words) < 12:
        return False
    gf = _glitch_token_fraction(s, min(200, len(words)))
    if len(words) >= 20 and gf > 0.12:
        return True
    if len(words) >= 14 and gf > 0.2:
        return True
    if len(words) >= 80:
        strict = re.compile(r"^[A-Za-z]{2,14}$")
        plain = sum(1 for w in words if strict.match(re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", w)))
        if plain / len(words) < 0.28:
            return True
    uniq = len({w.lower() for w in words})
    if len(words) > 60 and uniq / len(words) < 0.18:
        return True
    if re.search(r"\b(\w{3,})\s+\1\s+\1\b", s.lower()):
        return True
    return False


def _extractive_fallback_summary(text: str, max_chars: int = 2000) -> Tuple[str, List[str]]:
    """Dedupe lines/sentences from source when the neural summary is unusable."""
    raw = text.replace("\r\n", "\n").strip()
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    if len(lines) < 3:
        lines = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw) if len(s.strip()) > 15]
    seen: set[str] = set()
    kept: List[str] = []
    for ln in lines:
        key = re.sub(r"\s+", " ", ln.lower())
        if key in seen or len(ln) < 12:
            continue
        seen.add(key)
        kept.append(ln)
        if sum(len(x) for x in kept) >= max_chars:
            break
    if not kept:
        body = re.sub(r"\s+", " ", raw).strip()
        return (body[:max_chars] + ("…" if len(body) > max_chars else "")), []
    summary = " ".join(kept)
    if len(summary) > max_chars:
        summary = summary[: max_chars - 1] + "…"
    raw_take = [x for x in kept[:10] if len(x.split()) >= 8]
    takeaways = []
    for x in raw_take:
        fin = _finalize_takeaway_sentence(x)
        if fin:
            takeaways.append(fin)
    takeaways = _filter_redundant_sentences(takeaways)[:7]
    return summary, takeaways


def _balance_two_paragraphs(summary: str) -> str:
    """Split a single string into two blank-line paragraphs by sentence balance (plain prose)."""
    s = re.sub(r"\s+", " ", (summary or "").strip())
    if not s:
        return s
    blocks = [b.strip() for b in re.split(r"\n\s*\n", s) if b.strip()]
    if len(blocks) >= 2:
        return "\n\n".join(blocks[:3])
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", s) if len(x.strip()) > 14]
    if len(sentences) < 2:
        return s
    if len(sentences) == 2:
        return f"{sentences[0]}\n\n{sentences[1]}".strip()
    total_words = sum(len(x.split()) for x in sentences)
    target = total_words * 0.48
    acc, idx = 0, 0
    while idx < len(sentences) and acc < target:
        acc += len(sentences[idx].split())
        idx += 1
    idx = max(1, min(idx, len(sentences) - 1))
    return f"{' '.join(sentences[:idx]).strip()}\n\n{' '.join(sentences[idx:]).strip()}".strip()


_P1_HINT_TERMS = (
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "supervised",
    "unsupervised",
    "reinforcement",
    "classification",
    "regression",
    "neural",
    "dataset",
    "model",
    "training",
    "agent",
    "environment",
    "python",
    "programming",
    "object-oriented",
    "algorithm",
    "data structure",
)
_P2_HINT_TERMS = (
    "pipeline",
    "validation",
    "deployment",
    "preparation",
    "label",
    "cleans",
    "pytorch",
    "tensorflow",
    "diagnosis",
    "detection",
    "inspection",
    "application",
    "applications",
    "project",
    "homework",
    "climate",
    "medical",
    "image",
    "time series",
    "framework",
    "library",
    "libraries",
    "package",
    "install",
    "jupyter",
    "notebook",
    "documentation",
    "syntax",
    "numpy",
    "pandas",
)


def _hint_term_matches(sl: str, term: str) -> bool:
    """Phrase hints use substring match; single-token hints use word boundaries."""
    if " " in term:
        return term in sl
    return bool(re.search(rf"\b{re.escape(term)}\b", sl))


def _score_para1_sentence(s: str) -> int:
    sl = s.lower()
    return sum(1 for w in _P1_HINT_TERMS if _hint_term_matches(sl, w))


def _score_para2_sentence(s: str) -> int:
    sl = s.lower()
    return sum(1 for w in _P2_HINT_TERMS if _hint_term_matches(sl, w))


# Unicode math / slide OCR noise — never stitch into lecture summaries
_MATH_OR_SLIDE_JUNK = re.compile(
    r"[\U0001d400-\U0001d7ff]|"  # mathematical alphanumeric symbols
    r"[\u2190-\u22ff]|"  # arrows, math operators
    r"[\u03b1-\u03c9\u0391-\u03a9]"  # Greek (α–ω, Α–Ω) common in formula dumps
)
_SLIDE_FOOTER_BREAK = re.compile(
    r"\s+(?=\d{1,3}\s+(?:Machine Learning|The instructor|Deep Learning|AI and ML)\b)",
    re.IGNORECASE,
)
_HEX_SLUG = re.compile(r"-[0-9a-f]{10,}\b", re.IGNORECASE)


def _line_ok_for_lecture_support(s: str) -> bool:
    """Drop TOC lines, association-rule math, citations, and other slide debris."""
    t = re.sub(r"\s+", " ", (s or "").strip())
    if len(t) < 26 or len(t) > 520:
        return False
    if _is_slide_metadata_or_bibliography_unit(t):
        return False
    words = t.split()
    n = len(words)
    if n < 5 or n > 42:
        return False
    tl = t.lower()
    if re.match(r"^\d{1,3}\s+the instructor\b", tl):
        return False
    if re.match(r"^0\s+\S", t):
        return False
    if tl.count(":") >= 4:
        return False
    if len(re.findall(r"\btasks\b", tl)) >= 2:
        return False
    if len(re.findall(r"\bdiagnosis\b", tl)) >= 2:
        return False
    if re.search(r"the instructor\s+\d+\s*$", tl):
        return False
    if _MATH_OR_SLIDE_JUNK.search(t):
        return False
    if _HEX_SLUG.search(tl):
        return False
    if re.search(r"https?://|www\.\S", tl):
        return False
    if re.search(r"#customers|#\s*\[|px\s*,\s*y\b|py\s*\|\s*x", tl):
        return False
    if re.search(r"\*?\s*wikipedia\b", tl):
        return False
    if re.search(r"(?i)\bet\s+al\b", tl):
        return False
    if _JOURNAL_VOLUME_PAGES.search(t):
        return False
    if _JOURNAL_PROPER.search(t) and re.search(r"\(\s*(?:19|20)\d{2}\s*\)", t):
        return False
    if re.search(r"\b\d{1,2}\s+machine learning\b", tl):
        return False
    if re.search(r"\barxiv:", tl):
        return False
    if t.count("|") > 4 or t.count("=") > 6:
        return False
    letters = sum(1 for c in t if c.isalpha())
    if letters < 24:
        return False
    digits = sum(1 for c in t if c.isdigit())
    if digits / max(len(t), 1) > 0.14:
        return False
    if tl.count("the instructor") > 1:
        return False
    if _glitch_token_fraction(t, min(120, n)) > 0.08:
        return False
    return True


def _burst_long_sentence_units(text: str, max_words: int = 42) -> List[str]:
    """Break megachunks from flattened slides on semicolons / slide footers / wide gaps."""
    t = re.sub(r"\s+", " ", text.strip())
    if not t or len(t) < 24:
        return []
    if len(t.split()) <= max_words:
        return [t]
    parts = _SLIDE_FOOTER_BREAK.split(t)
    if len(parts) == 1:
        parts = re.split(r"\s*;\s+", t)
    if len(parts) == 1:
        parts = re.split(r"\s{3,}", t)
    out: List[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p.split()) <= max_words:
            if len(p) >= 24:
                out.append(p)
        else:
            subs = re.split(r'(?<=[.!?])\s+(?=[A-Z"(])', p)
            for s in subs:
                s = s.strip()
                if len(s) >= 24 and len(s.split()) <= max_words:
                    out.append(s)
    return out


def _split_source_sentences(text: str) -> List[str]:
    """Sentence-like units from source (slides often lack periods — add line-based chunks)."""
    raw = (text or "").strip()
    if not raw:
        return []
    flat = re.sub(r"\s+", " ", raw)
    merged: List[str] = []
    for x in re.split(r"(?<=[.!?])\s+", flat):
        x = x.strip()
        if len(x) < 24:
            continue
        merged.extend(_burst_long_sentence_units(x))
    sents = [s for s in merged if _line_ok_for_lecture_support(s)]
    if len(sents) >= 4:
        return sents[:100]
    lines = []
    for ln in raw.splitlines():
        ln = re.sub(r"\s+", " ", ln.strip())
        if len(ln) < 29:
            continue
        lines.extend(_burst_long_sentence_units(ln))
    lines = [s for s in lines if _line_ok_for_lecture_support(s)]
    if lines:
        return lines[:100]
    tail = flat[:520].strip()
    if tail and _line_ok_for_lecture_support(tail):
        return [tail]
    return []


def _pick_supporting_sentences(
    sentences: List[str],
    score_fn,
    avoid: str,
    max_words: int = 140,
    max_sents: int = 5,
    min_score: int = 1,
    overlap_threshold: float = 0.58,
) -> List[str]:
    scored = [(score_fn(s), re.sub(r"\s+", " ", s).strip()) for s in sentences if s.strip()]
    scored.sort(key=lambda x: (-x[0], -len(x[1])))
    avoid_accum = avoid or ""
    picked: List[str] = []
    wc = 0
    for sc, s in scored:
        if sc < min_score:
            continue
        if not _line_ok_for_lecture_support(s):
            continue
        sw = set(re.sub(r"\W+", " ", s.lower()).split())
        avoid_set = set(re.sub(r"\W+", " ", avoid_accum.lower()).split())
        if avoid_set and len(sw & avoid_set) / max(len(sw), 1) > overlap_threshold:
            continue
        picked.append(s)
        wc += len(s.split())
        avoid_accum = f"{avoid_accum} {s}"
        if wc >= max_words or len(picked) >= max_sents:
            break
    return picked


def _too_similar_to_anchor(sentence: str, anchor: str, threshold: float = 0.72) -> bool:
    """Skip extractive lines that mostly repeat the neural lead (common in slide decks)."""
    sw = set(re.sub(r"\W+", " ", sentence.lower()).split())
    aw = set(re.sub(r"\W+", " ", (anchor or "").lower()).split())
    if len(sw) < 6 or len(aw) < 6:
        return False
    inter = len(sw & aw)
    return inter / max(len(sw), len(aw), 1) >= threshold


def _lecture_narrative_from_bart_and_source(bart_summary: str, source_text: str) -> str:
    """
    Two-paragraph lecture recap without an LLM API: opener + neural summary, then extractive
    support from source (pipeline, tools, applications) when available — similar shape to
    long-form course recaps.
    """
    bart = re.sub(r"\s+", " ", (bart_summary or "").strip())
    if not bart.strip():
        fb, _ = _extractive_fallback_summary(source_text, max_chars=2800)
        bart = re.sub(r"\s+", " ", fb).strip()
    src_words = len((source_text or "").split())
    overlap_loose = src_words > 450
    sents = _split_source_sentences(source_text)
    sents = [s for s in sents if not _too_similar_to_anchor(s, bart)]
    if not re.match(r"^(?i)this lecture", bart):
        p1 = f"This lecture introduces main themes from the session: {bart}"
    else:
        p1 = bart
    extra_p1 = _pick_supporting_sentences(
        sents,
        _score_para1_sentence,
        p1,
        max_words=130,
        max_sents=2,
        min_score=2,
        overlap_threshold=0.5 if overlap_loose else 0.58,
    )
    if extra_p1:
        p1 = f"{p1.strip()} {' '.join(x.strip() for x in extra_p1)}".strip()
    p2_list = _pick_supporting_sentences(
        sents,
        _score_para2_sentence,
        p1,
        max_words=280,
        max_sents=8,
        min_score=2,
        overlap_threshold=0.45 if overlap_loose else 0.58,
    )
    if p2_list:
        p2 = " ".join(x.strip() for x in p2_list if x.strip())
        return f"{p1.strip()}\n\n{p2}".strip()
    return _balance_two_paragraphs(p1)

# Known tokenization artifacts from BART/distilBART on academic text
_ARTIFACT_FIXES = {
    "pro-ishlypose": "propose", "pro-ishlyposes": "proposes", "pro-ishlyposed": "proposed",
    "pro-ishypose": "propose", "pro-ishyposes": "proposes", "pro-ishyposed": "proposed",
    "an-ogleswering": "answering", "an-swering": "answering",
    "fol-gling": "following", "fol-lowing": "following",
    "pronening": "spanning", "spannen": "spanning",
    "com-pare": "compare", "QRRker": "QRRanker", "QRRanker": "QRRanker",
    "trans-former": "transformer", "trans-formers": "transformers",
    "re-ranking": "reranking", "re-rank": "rerank",
    "list-wise": "listwise", "pair-wise": "pairwise",
    "in-ference": "inference", "com-pression": "compression",
}

# Generic: hyphenated word fragments that look like one word (e.g. "pro-pose" -> "propose")
_HYPHEN_ARTIFACT = re.compile(r"\b(\w{2,5})-[\w]{1,6}(\w{2,8})\b")


def _sanitize_input(text: str) -> str:
    """Normalize spaces but preserve newlines for slide structure."""
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()


def _fix_tokenization_artifacts(text: str) -> str:
    """Fix common garbled words and hyphenation artifacts from seq2seq models."""
    if not text:
        return text
    for bad, good in _ARTIFACT_FIXES.items():
        text = re.sub(re.escape(bad), good, text, flags=re.IGNORECASE)
    # Merge obvious hyphenated fragments: "pro-pose" -> "propose" when parts concatenate sensibly
    def _merge(m):
        a, b = m.group(1), m.group(2)
        base = (a.lower() + b.lower()).rstrip('sd') # Check base word
        if base in {"propose", "compare", "follow", "answer", "rerank", "transform"}:
            return a + b
        return m.group(0)
    text = _HYPHEN_ARTIFACT.sub(_merge, text)
    return text


def _fix_repetition_artifacts(text: str) -> str:
    """Detect and collapse sequences where a word repeats due to model stuck-loops."""
    if not text:
        return text
    # Match words repeating 3+ times: "Cases Cases Cases" -> "Cases"
    # Also handles "software software" -> "software"
    words = text.split()
    if not words:
        return text
    
    new_words = [words[0]]
    for i in range(1, len(words)):
        # If the word is the same as the previous one and is 4+ chars (avoid "the the" if intentional)
        if words[i].lower() == words[i-1].lower() and len(words[i]) > 3:
            continue
        # Also catch alternating loops: "A B A B" -> "A B"
        if i > 2 and words[i].lower() == words[i-2].lower() and words[i-1].lower() == words[i-3].lower():
            continue
        new_words.append(words[i])
    
    return " ".join(new_words)


_INCOMPLETE_TAKEAWAY_TAIL = re.compile(
    r"(?i)\s(to|from|and|or|for|with|of|in|at|by|as|on|via|the|a|an|is|are|will|may|can|should|that|which)\s*$"
)


def _takeaway_lexically_grounded(candidate: str, source: str, min_ratio: float = 0.62) -> bool:
    """Reject abstractive bullets whose content words mostly do not appear in the source."""
    c = set(re.findall(r"[a-z]{4,}", (candidate or "").lower()))
    sset = set(re.findall(r"[a-z]{4,}", (source or "").lower()))
    if not c:
        return False
    if len(c) < 6:
        return len(c & sset) >= max(4, int(0.88 * len(c)))
    return len(c & sset) / max(len(c), 1) >= min_ratio


def _takeaway_semantically_close_to_source(
    candidate: str, source: str, extractor, min_cos: float = 0.28
) -> bool:
    """Optional embedding gate: takeaway must align with document semantics."""
    if not extractor or not getattr(extractor, "has_deps", False):
        return True
    try:
        from sentence_transformers import util

        c = (candidate or "").strip()[:480]
        src = (source or "").strip()[:12000]
        if len(c) < 20 or len(src) < 80:
            return True
        emb = extractor.model.encode([c, src], convert_to_tensor=True)
        sim = float(util.cos_sim(emb[0:1], emb[1:2]).cpu().numpy().flatten()[0])
        return sim >= min_cos
    except Exception:
        return True


def _finalize_takeaway_sentence(s: str, min_words: int = 9, max_words: int = 52) -> Optional[str]:
    """Keep only bullets that already end as real sentences; do not invent punctuation or trim semantics."""
    s = re.sub(r"\s+", " ", (s or "").strip())
    s = re.sub(r"\s+([.!?])", r"\1", s)
    if len(s) < 40:
        return None
    s = re.sub(r"[-–—]{2,}\s*$", "", s).strip()

    if s[-1] not in ".!?":
        cut = max(s.rfind("."), s.rfind("!"), s.rfind("?"))
        if cut >= 48:
            s = s[: cut + 1].strip()
        else:
            return None

    if _INCOMPLETE_TAKEAWAY_TAIL.search(s):
        return None

    words = s.split()
    if len(words) < min_words:
        return None
    if len(words) > max_words:
        s = " ".join(words[:max_words])
        cut = max(s.rfind("."), s.rfind("!"), s.rfind("?"))
        if cut >= 36:
            s = s[: cut + 1].strip()
        else:
            return None

    if s and s[0].isalpha() and s[0].islower():
        s = s[0].upper() + s[1:]
    return s


def _takeaway_sentences_from_source(text: str, min_words: int = 10) -> List[str]:
    """Prefer full declarative sentences from the document (complete thoughts)."""
    text = (text or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    seen: set[str] = set()
    good: List[str] = []
    for para in re.split(r"\n\s*\n+", text):
        para = para.strip()
        if not para:
            continue
        for u in re.split(r"(?<=[.!?])\s+", para):
            u = re.sub(r"\s+", " ", u.strip())
            if len(u.split()) < min_words:
                continue
            if not u or u[-1] not in ".!?":
                continue
            k = u.lower()
            if k in seen:
                continue
            seen.add(k)
            good.append(u)
    return good


def _filter_redundant_sentences(sentences: List[str], overlap_threshold: float = 0.5) -> List[str]:
    """Remove sentences that overlap too much with previously kept ones.
    Lowered threshold (0.5) to keep more distinct information for robust summaries.
    """
    if not sentences:
        return []
    kept = [str(sentences[0])]
    for sent in sentences[1:]:
        sent = str(sent)
        s1 = set(sent.lower().split())
        if not s1 or len(s1) < 4: # Ignore very short boilerplate
            continue
        is_redundant = False
        for prev in kept:
            s2 = set(str(prev).lower().split())
            if not s2: continue
            overlap = len(s1 & s2) / max(len(s1), len(s2), 1)
            if overlap >= overlap_threshold:
                is_redundant = True
                break
        if not is_redundant:
            kept.append(sent)
    return kept

def calculate_coverage_score(summary: str, original: str) -> float:
    """Calculates a simple n-gram overlap score (ROUGE-1 proxy)."""
    if not summary or not original:
        return 0.0
    s_words = set(summary.lower().split())
    o_words = set(original.lower().split())
    if not o_words:
        return 0.0
    overlap = len(s_words & o_words)
    return round(float(overlap / len(s_words)), 3) if s_words else 0.0

class Summarizer:
    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6"):
        """
        Initializes the summarization model and tokenizer.
        Uses distilbart for a good balance of speed and quality.
        """
        self._use_peft = False
        self.has_transformers = HAS_TRANSFORMERS
        self.cache = {} # Simple in-memory cache for speed
        if HAS_TRANSFORMERS:
            try:
                print(f"Loading summarization model: {model_name}...")
                try:
                    # Try local files first to avoid network hangs
                    self.tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, local_files_only=True)
                except Exception:
                    # If not local, try fetching (standard behavior)
                    self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                # LoRA only when explicitly enabled — a mismatched adapter produces keyword soup.
                adapter_path = os.path.join("trained_models", "summarizer_lora", "final_adapter")
                self._use_peft = False
                use_lora = os.getenv("SYNOD_USE_SUMMARIZER_LORA", "").lower() in ("1", "true", "yes")
                if use_lora and os.path.exists(adapter_path):
                    try:
                        from peft import PeftModel

                        print(f"Loading LoRA adapter from {adapter_path}...")
                        self.model = PeftModel.from_pretrained(self.model, adapter_path)
                        self._use_peft = True
                    except ImportError:
                        print("PEFT not installed. Skipping adapter loading.")
                    except Exception as pe:
                        print(f"Failed to load adapter: {pe}")
                elif os.path.exists(adapter_path) and not use_lora:
                    print(
                        "Summarizer LoRA present but skipped (set SYNOD_USE_SUMMARIZER_LORA=true to load)."
                    )

                # Device detection: CUDA -> MPS -> CPU (avoid half() on PEFT — unstable weights)
                if torch.cuda.is_available():
                    self.device = "cuda"
                    if not getattr(self, "_use_peft", False):
                        self.model = self.model.half()  # Precision optimization for CUDA
                    else:
                        logger.info("CUDA: float32 for PEFT-wrapped summarizer.")
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self.device = "mps"
                    # Half precision disabled for stability
                    # self.model = self.model.half()
                else:
                    self.device = "cpu"
                    # Dynamic Quantization for CPU speedup
                    try:
                        print("Applying Dynamic Quantization for CPU...")
                        self.model = torch.quantization.quantize_dynamic(
                            self.model, {torch.nn.Linear}, dtype=torch.qint8
                        )
                    except Exception as qe:
                        print(f"Quantization failed: {qe}")
                
                self.model.to(self.device)
                print(f"Model loaded on {self.device} with optimized precision.")
            except Exception as e:
                print(f"Error loading model: {e}. Falling back to MOCK mode.")
                self.has_transformers = False
        else:
            print("Transformers not found. Running in MOCK mode.")
    
    def summarize(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 40,
        extractor=None,
    ) -> dict:
        """
        Summarizes the input text.
        """
        from app.ingestion.extractor_service import ExtractorService

        text = ExtractorService.normalize_pipeline_text((text or "").strip())
        if not text or len(text) < 50:
            return {"summary": text or "", "metrics": {"compression_ratio": 1.0}}

        scrubbed = _scrub_text_for_neural_summary(text)
        if len((scrubbed or "").split()) < 35:
            scrubbed = text

        # Cache check (salt so behavior fixes invalidate old bad summaries)
        text_hash = hashlib.sha256(f"{_SUMMARY_CACHE_SALT}\n{text}".encode()).hexdigest()
        if text_hash in self.cache:
            cached = dict(self.cache[text_hash])
            if isinstance(cached.get("summary"), str):
                cached["summary"] = ExtractorService.normalize_pipeline_text(cached["summary"])
            return cached
        
        if not self.has_transformers:
            # Mock summary: just take the first few sentences
            sentences = scrubbed.split(". ")
            summary = ExtractorService.normalize_pipeline_text(
                _safe_clean_summary_output(
                    _lecture_narrative_from_bart_and_source(
                        ". ".join(sentences[:2]) + " (Mock Summary)", scrubbed
                    )
                )
            )
            mock_take = self.generate_takeaways(scrubbed, num_bullets=7, extractor=extractor)
            return {
                "summary": summary,
                "takeaways": mock_take,
                "metrics": {
                    "compression_ratio": round(float(len(summary.split()) / max(1, len(text.split()))), 3)
                },
            }

        try:
            word_count = len(scrubbed.split())
            # distilBART is CNN-tuned; scale output with doc length but cap to reduce collapse on tiny inputs.
            if max_length == 150:
                target_max = max(56, min(240, word_count // 4, word_count + 48))
                target_min = min(56, max(18, target_max // 5))
            else:
                target_max = max_length
                target_min = min_length

            # Clean up newlines for better split (scrubbed source → less title/citation leakage into BART)
            clean_text = scrubbed.replace('\n', ' ')
            sentences = re.split(r'(?<=[.!?])\s+', clean_text)
            chunks = []
            current_chunk = ""
            current_len = 0
            
            # Larger chunks (fewer boundaries) so long uploads retain cross-section context in each pass.
            chunk_target = 520
            for sentence in sentences:
                sentence_len = len(sentence.split())
                if current_len + sentence_len < chunk_target:
                    current_chunk += " " + sentence
                    current_len += sentence_len
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
                    current_len = sentence_len
            if current_chunk:
                chunks.append(current_chunk.strip())

            if len(chunks) <= 1:
                # Single pass for short documents
                inputs = self.tokenizer([clean_text], max_length=1024, return_tensors="pt", truncation=True).to(self.device)
                summary_ids = self.model.generate(
                    input_ids=inputs["input_ids"], 
                    num_beams=4, 
                    max_length=target_max, 
                    min_length=target_min, 
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3,
                    early_stopping=True
                )
                summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
            else:
                # 1. First Pass: Process chunks separately
                chunk_summaries: List[str] = []
                n_chunks = max(len(chunks), 1)
                c_max_base = min(200, max(52, 520 // n_chunks))
                c_min_base = min(36, max(10, c_max_base // 4))
                
                for chunk in chunks:
                    chunk_wc = len(chunk.split())
                    if chunk_wc < 12:
                        continue
                    c_max = min(200, max(28, c_max_base, chunk_wc // 3 + 24))
                    c_min = min(c_min_base, max(8, c_max // 5))
                    
                    inputs = self.tokenizer([chunk], max_length=1024, return_tensors="pt", truncation=True).to(self.device)
                    ids = self.model.generate(
                        input_ids=inputs["input_ids"], 
                        num_beams=4, 
                        max_length=c_max, 
                        min_length=c_min, 
                        repetition_penalty=1.1, # Slightly lower for chunks to maintain flow
                        no_repeat_ngram_size=3,
                        early_stopping=True
                    )
                    chunk_summary = self.tokenizer.decode(ids[0], skip_special_tokens=True).strip()
                    chunk_summaries.append(chunk_summary)
                
                # 2. Second Pass: Synthesis (Recursive Summarization)
                # Combine sectional summaries into a single synthesis input
                synthesis_input = " ".join(chunk_summaries)
                
                try:
                    syn_wc = len(synthesis_input.split())
                    final_max = min(280, max(96, syn_wc // 3))
                    final_min = min(56, max(20, final_max // 5))

                    inputs = self.tokenizer([synthesis_input], max_length=1024, return_tensors="pt", truncation=True).to(self.device)
                    ids = self.model.generate(
                        input_ids=inputs["input_ids"],
                        num_beams=4,
                        max_length=final_max,
                        min_length=final_min,
                        length_penalty=1.35,
                        repetition_penalty=1.2,
                        no_repeat_ngram_size=3,
                        early_stopping=True,
                    )
                    summary = self.tokenizer.decode(ids[0], skip_special_tokens=True).strip()
                except Exception as e:
                    print(f"Synthesis pass failed: {e}. Falling back to combined chunks.")
                    summary = "\n\n".join(chunk_summaries)

            # Post-process: fix artifacts, then sanity-check *before* weaving narrative text.
            summary = _fix_tokenization_artifacts(summary)
            summary = _fix_repetition_artifacts(summary)

            if _looks_like_degenerate_summary(summary):
                logger.warning(
                    "Summarizer output failed sanity check; using extractive fallback. "
                    "If you use a custom LoRA, set SYNOD_USE_SUMMARIZER_LORA=true only when it matches the base model."
                )
                fb_summary, fb_takeaways = _extractive_fallback_summary(scrubbed)
                summary = ExtractorService.normalize_pipeline_text(
                    _safe_clean_summary_output(
                        _lecture_narrative_from_bart_and_source(fb_summary, scrubbed)
                    )
                )
                if not summary.strip():
                    summary = ExtractorService.normalize_pipeline_text(
                        _balance_two_paragraphs(re.sub(r"\s+", " ", fb_summary))
                    )
                takeaways = fb_takeaways or self.generate_takeaways(
                    scrubbed, num_bullets=7, extractor=extractor
                )
                compression_ratio = len(summary.split()) / max(1, len(text.split()))
                coverage_score = calculate_coverage_score(summary, text)
                result = {
                    "summary": summary,
                    "takeaways": takeaways,
                    "metrics": {
                        "compression_ratio": round(float(compression_ratio), 3),
                        "coverage_score": coverage_score,
                        "summarizer_fallback": "extractive_degenerate_model_output",
                    },
                }
                self.cache[text_hash] = result
                return result

            summary = ExtractorService.normalize_pipeline_text(
                _safe_clean_summary_output(
                    _lecture_narrative_from_bart_and_source(summary, scrubbed)
                )
            )
            if not summary.strip():
                fb_summary, _ = _extractive_fallback_summary(scrubbed, max_chars=2800)
                summary = ExtractorService.normalize_pipeline_text(
                    _balance_two_paragraphs(re.sub(r"\s+", " ", fb_summary))
                )

            # Simple compression metric
            compression_ratio = len(summary.split()) / max(1, len(text.split()))
            coverage_score = calculate_coverage_score(summary, scrubbed)
            
            # Generate takeaways automatically for a complete result
            takeaways = self.generate_takeaways(scrubbed, num_bullets=7, extractor=extractor)
            
            result = {
                "summary": summary,
                "takeaways": takeaways,
                "metrics": {
                    "compression_ratio": round(float(compression_ratio), 3),
                    "coverage_score": coverage_score
                }
            }
            self.cache[text_hash] = result
            return result
        except Exception as e:
            print(f"Summary error: {e}")
            return {"summary": text[:200] + "...", "metrics": {"compression_ratio": 0.0}}

    def generate_takeaways(
        self, text: str, num_bullets: int = 7, extractor=None
    ) -> List[str]:
        """
        Verbatim or tightly grounded bullets only: full source sentences first;
        abstractive gap-fill only when lexically (and optionally embedding-) aligned with the document.
        """
        if not self.has_transformers:
            ext = _takeaway_sentences_from_source(text, min_words=8)
            mock_take = [
                x
                for x in (
                    _finalize_takeaway_sentence(_fix_tokenization_artifacts(s)) for s in ext
                )
                if x
            ]
            mock_take = _filter_redundant_sentences(mock_take)[:num_bullets]
            return mock_take or ["Key point from the lecture (Mock)"]

        ext = _takeaway_sentences_from_source(text, min_words=10)
        ext = [_finalize_takeaway_sentence(_fix_tokenization_artifacts(x)) for x in ext]
        ext = [x for x in ext if x and _takeaway_lexically_grounded(x, text, min_ratio=0.5)]
        ext = _filter_redundant_sentences(ext)
        out: List[str] = list(ext[:num_bullets])

        if len(out) >= num_bullets:
            return out[:num_bullets]

        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        need = num_bullets - len(out)
        chunk_size = max(2, len(sentences) // max(need + 2, 4))

        for i in range(0, len(sentences), chunk_size):
            if len(out) >= num_bullets:
                break
            chunk = " ".join(sentences[i : i + chunk_size])
            if len(chunk.split()) < 22:
                continue
            try:
                inputs = self.tokenizer(
                    [chunk], max_length=1024, return_tensors="pt", truncation=True
                ).to(self.device)
                ids = self.model.generate(
                    inputs["input_ids"],
                    max_length=88,
                    min_length=26,
                    num_beams=4,
                    length_penalty=1.05,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3,
                    early_stopping=True,
                )
                point = self.tokenizer.decode(ids[0], skip_special_tokens=True).strip()
                point = _fix_tokenization_artifacts(point)
                fin = _finalize_takeaway_sentence(point)
                if not fin or fin.lower() in {x.lower() for x in out}:
                    continue
                if not _takeaway_lexically_grounded(fin, text, min_ratio=0.62):
                    continue
                if not _takeaway_semantically_close_to_source(fin, text, extractor):
                    continue
                out.append(fin)
            except Exception:
                continue

        if len(out) < num_bullets:
            for s in sentences:
                if len(out) >= num_bullets:
                    break
                fin = _finalize_takeaway_sentence(_fix_tokenization_artifacts(s))
                if (
                    fin
                    and fin.lower() not in {x.lower() for x in out}
                    and _takeaway_lexically_grounded(fin, text, min_ratio=0.5)
                ):
                    out.append(fin)

        return _filter_redundant_sentences(out)[:num_bullets]

if __name__ == "__main__":
    # Quick test
    test_text = """
    Natural Language Processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence 
    concerned with the interactions between computers and human language, in particular how to program computers 
    to process and analyze large amounts of natural language data. The goal is a computer capable of "understanding" 
    the contents of documents, including the contextual nuances of the language within them. The technology can then 
    accurately extract information and insights contained in the documents as well as categorize and organize the 
    documents themselves. Challenges in natural language processing frequently involve speech recognition, 
    natural-language understanding, and natural-language generation.
    """
    s = Summarizer(model_name="t5-small") # Using small model for testing
    print(f"Result: {s.summarize(test_text)}")
