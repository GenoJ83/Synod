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
_SUMMARY_CACHE_SALT = "v7-longer-whole-doc-summary"


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
    takeaways = [x for x in kept[:6] if len(x.split()) >= 5][:5]
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
    words = t.split()
    n = len(words)
    if n < 6 or n > 42:
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
    if re.search(r"\bet\s+al\b", tl):
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
    
    def summarize(self, text: str, max_length: int = 150, min_length: int = 40) -> dict:
        """
        Summarizes the input text.
        """
        from app.ingestion.extractor_service import ExtractorService

        text = ExtractorService.normalize_pipeline_text((text or "").strip())
        if not text or len(text) < 50:
            return {"summary": text or "", "metrics": {"compression_ratio": 1.0}}

        # Cache check (salt so behavior fixes invalidate old bad summaries)
        text_hash = hashlib.sha256(f"{_SUMMARY_CACHE_SALT}\n{text}".encode()).hexdigest()
        if text_hash in self.cache:
            cached = dict(self.cache[text_hash])
            if isinstance(cached.get("summary"), str):
                cached["summary"] = ExtractorService.normalize_pipeline_text(cached["summary"])
            return cached
        
        if not self.has_transformers:
            # Mock summary: just take the first few sentences
            sentences = text.split(". ")
            summary = ExtractorService.normalize_pipeline_text(
                _lecture_narrative_from_bart_and_source(
                    ". ".join(sentences[:2]) + " (Mock Summary)", text
                )
            )
            return {
                "summary": summary,
                "metrics": {
                    "compression_ratio": round(float(len(summary.split()) / max(1, len(text.split()))), 3)
                }
            }

        try:
            word_count = len(text.split())
            # distilBART is CNN-tuned; scale output with doc length but cap to reduce collapse on tiny inputs.
            if max_length == 150:
                target_max = max(56, min(240, word_count // 4, word_count + 48))
                target_min = min(56, max(18, target_max // 5))
            else:
                target_max = max_length
                target_min = min_length

            # Clean up newlines for better split
            clean_text = text.replace('\n', ' ')
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
                fb_summary, fb_takeaways = _extractive_fallback_summary(text)
                summary = ExtractorService.normalize_pipeline_text(
                    _lecture_narrative_from_bart_and_source(fb_summary, text)
                )
                takeaways = fb_takeaways or self.generate_takeaways(text)
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
                _lecture_narrative_from_bart_and_source(summary, text)
            )

            # Simple compression metric
            compression_ratio = len(summary.split()) / max(1, len(text.split()))
            coverage_score = calculate_coverage_score(summary, text)
            
            # Generate takeaways automatically for a complete result
            takeaways = self.generate_takeaways(text)
            
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

    def generate_takeaways(self, text: str, num_bullets: int = 5) -> List[str]:
        """ Extracts specific, important takeaways as bullet points. """
        if not self.has_transformers:
            return ["Key point from the lecture (Mock)"]
        
        # Split text into segments and summarize each to get diverse points
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) < 10:
            short_takeaways = [s.strip() for s in sentences if len(s.split()) > 5]
            # Fix artifacts
            short_takeaways = [_fix_tokenization_artifacts(s) for s in short_takeaways]
            # Filter redundancy
            return _filter_redundant_sentences(short_takeaways)[:num_bullets]
        
        # Group sentences into chunks
        chunk_size = max(1, len(sentences) // num_bullets)
        takeaways: List[str] = []
        
        for i in range(0, len(sentences), chunk_size):
            chunk = " ".join(sentences[i:i + chunk_size])
            if len(chunk.split()) < 20: continue
            
            try:
                inputs = self.tokenizer([chunk], max_length=1024, return_tensors="pt", truncation=True).to(self.device)
                # Generate very short summary for this chunk
                ids = self.model.generate(inputs["input_ids"], max_length=40, min_length=10, num_beams=2)
                point = self.tokenizer.decode(ids[0], skip_special_tokens=True).strip()
                
                # Fix artifacts and clean up
                point = _fix_tokenization_artifacts(point)
                
                if point and point not in takeaways:
                    takeaways.append(point)
            except:
                continue
            
            if len(takeaways) >= num_bullets:
                break
        
        # Final redundancy filter to ensure diverse points
        return _filter_redundant_sentences(takeaways)

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
