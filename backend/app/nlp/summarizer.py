import re
import hashlib
from typing import List, Optional

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

# Known tokenization artifacts from BART/distilBART on academic text
_ARTIFACT_FIXES = {
    "pro-ishlypose": "propose", "pro-ishlyposes": "proposes", "pro-ishlyposed": "proposed",
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
_HYPHEN_ARTIFACT = re.compile(r"\b(\w{2,5})-[\w]{1,4}(\w{2,8})\b")


def _fix_tokenization_artifacts(text: str) -> str:
    """Fix common garbled words and hyphenation artifacts from seq2seq models."""
    if not text:
        return text
    for bad, good in _ARTIFACT_FIXES.items():
        text = re.sub(re.escape(bad), good, text, flags=re.IGNORECASE)
    # Merge obvious hyphenated fragments: "pro-pose" -> "propose" when parts concatenate sensibly
    def _merge(m):
        a, b = m.group(1), m.group(2)
        if a.lower() + b.lower() in {"propose", "compare", "following", "answering", "reranking"}:
            return a + b
        return m.group(0)
    text = _HYPHEN_ARTIFACT.sub(_merge, text)
    return text


def _filter_redundant_sentences(sentences: List[str], overlap_threshold: float = 0.65) -> List[str]:
    """Remove sentences that overlap too much with previously kept ones."""
    if not sentences:
        return []
    kept = [sentences[0]]
    for sent in sentences[1:]:
        s1 = set(sent.lower().split())
        if not s1:
            continue
        is_redundant = False
        for prev in kept:
            s2 = set(prev.lower().split())
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
    return round(overlap / len(s_words), 3) if s_words else 0.0


class Summarizer:
    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6"):
        """
        Initializes the summarization model and tokenizer.
        Uses distilbart for a good balance of speed and quality.
        """
        self.has_transformers = HAS_TRANSFORMERS
        self.cache = {}
        self.model_name = model_name  # For model-specific logic (e.g. Pegasus full-paper mode)
        if HAS_TRANSFORMERS:
            try:
                print(f"Loading summarization model: {model_name}...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                # Device detection: CUDA -> MPS -> CPU
                if torch.cuda.is_available():
                    self.device = "cuda"
                    self.model = self.model.half() # Precision optimization for CUDA
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
                print(f"Error loading model {model_name}: {e}")
                # Fallback to DistilBART if Pegasus/academic model fails (e.g. not yet downloaded)
                fallback = "sshleifer/distilbart-cnn-12-6"
                if model_name != fallback:
                    print(f"Attempting fallback to {fallback}...")
                    try:
                        self.tokenizer = AutoTokenizer.from_pretrained(fallback)
                        self.model = AutoModelForSeq2SeqLM.from_pretrained(fallback)
                        if torch.cuda.is_available():
                            self.device = "cuda"
                            self.model = self.model.half()
                        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                            self.device = "mps"
                        else:
                            self.device = "cpu"
                            try:
                                self.model = torch.quantization.quantize_dynamic(
                                    self.model, {torch.nn.Linear}, dtype=torch.qint8
                                )
                            except Exception:
                                pass
                        self.model.to(self.device)
                        self.model_name = fallback  # Use fallback logic going forward
                        print(f"Fallback model loaded on {self.device}.")
                    except Exception as e2:
                        print(f"Fallback failed: {e2}. Running in MOCK mode.")
                        self.has_transformers = False
                else:
                    self.has_transformers = False
        else:
            print("Transformers not found. Running in MOCK mode.")
    
    def summarize(self, text: str, max_length: int = 150, min_length: int = 40) -> dict:
        """
        Summarizes the input text.
        """
        if not text or len(text.strip()) < 50:
            return {"summary": text, "metrics": {"compression_ratio": 1.0}}
        
        # Cache check (use stable hash)
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        if not self.has_transformers:
            # Mock summary: just take the first few sentences
            sentences = text.split(". ")
            summary = ". ".join(sentences[:2]) + " (Mock Summary)"
            return {
                "summary": summary,
                "metrics": {
                    "compression_ratio": round(len(summary.split()) / max(1, len(text.split())), 3)
                }
            }

        try:
            word_count = len(text.split())
            SUMMARY_WORD_CAP = 500  # Hard cap for conciseness (per Grok feedback)
            is_pegasus = "pegasus" in self.model_name.lower() or "Pegasus" in self.model_name

            # Pegasus-X: trained on full papers -> abstract; use single-pass for docs that fit
            PEGASUS_MAX_WORDS = 5500  # ~8K tokens, under 16K limit
            if is_pegasus and word_count <= PEGASUS_MAX_WORDS:
                clean_text = text.replace('\n', ' ')
                # Model card: max_length=512, min_length=150, no_repeat_ngram_size=3
                input_max = min(8192, word_count * 2)  # tokens
                inputs = self.tokenizer(
                    [clean_text],
                    max_length=input_max,
                    return_tensors="pt",
                    truncation=True,
                    padding=True,
                ).to(self.device)
                gen_kwargs = {
                    "max_length": 512,
                    "min_length": 150,
                    "num_beams": 4,
                    "length_penalty": 1.0,
                    "early_stopping": True,
                }
                if hasattr(self.model, "generate"):
                    gen_kwargs["no_repeat_ngram_size"] = 3
                summary_ids = self.model.generate(
                    inputs["input_ids"],
                    attention_mask=inputs.get("attention_mask"),
                    **gen_kwargs,
                )
                summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
            else:
                # Target 20-30% of doc, capped at SUMMARY_WORD_CAP
                if max_length == 150:
                    target_max = min(SUMMARY_WORD_CAP, max(150, int(word_count * 0.25)))
                    target_min = min(100, max(50, int(word_count * 0.08)))
                else:
                    target_max = max_length
                    target_min = min_length

                # Clean up newlines for better split
                clean_text = text.replace('\n', ' ')
                sentences = re.split(r'(?<=[.!?])\s+', clean_text)
                chunks = []
                current_chunk = ""
                current_len = 0

                chunk_size = 600 if is_pegasus else 400  # Pegasus prefers longer chunks
                for sentence in sentences:
                    sentence_len = len(sentence.split())
                    if current_len + sentence_len < chunk_size:
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
                    summary_ids = self.model.generate(inputs["input_ids"], num_beams=4, max_length=target_max, min_length=target_min, early_stopping=True)
                    summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
                else:
                    # Process chunks; Pegasus needs higher output limits when chunking
                    chunk_summaries: List[str] = []
                    base_max, base_min = (200, 80) if is_pegasus else (120, 30)
                    per_chunk_max = max(base_min, min(base_max, target_max // len(chunks)))
                    per_chunk_min = max(base_min // 2, min(base_min, target_min // len(chunks)))

                for chunk in chunks:
                    chunk_wc = len(chunk.split())
                    if chunk_wc < 40:
                        continue

                    actual_c_max = min(per_chunk_max, int(chunk_wc * 0.5))
                    actual_c_min = min(per_chunk_min, int(chunk_wc * 0.15))

                    inputs = self.tokenizer([chunk], max_length=1024, return_tensors="pt", truncation=True).to(self.device)
                    ids = self.model.generate(inputs["input_ids"], num_beams=4, max_length=actual_c_max, min_length=actual_c_min, early_stopping=True)
                    chunk_summary = self.tokenizer.decode(ids[0], skip_special_tokens=True).strip()

                    # Per-chunk redundancy filter
                    c_sentences = re.split(r'(?<=[.!?])\s+', chunk_summary)
                    if len(c_sentences) > 1:
                        filtered = _filter_redundant_sentences(c_sentences, overlap_threshold=0.7)
                        chunk_summary = " ".join(filtered)
                    chunk_summaries.append(chunk_summary)

                # Cross-chunk redundancy: dedupe across all chunk summaries
                all_sentences = []
                for cs in chunk_summaries:
                    all_sentences.extend(re.split(r'(?<=[.!?])\s+', cs))
                all_sentences = [s.strip() for s in all_sentences if len(s.strip()) > 10]
                deduped = _filter_redundant_sentences(all_sentences, overlap_threshold=0.6)
                summary = "\n\n".join(deduped)

            # Post-process: fix artifacts, apply length cap
            summary = _fix_tokenization_artifacts(summary)
            words = summary.split()
            if len(words) > SUMMARY_WORD_CAP:
                summary = " ".join(words[:SUMMARY_WORD_CAP])
                # End at sentence boundary if possible
                last_period = summary.rfind(". ")
                if last_period > 200:
                    summary = summary[: last_period + 1]

            # Simple compression metric
            compression_ratio = len(summary.split()) / max(1, len(text.split()))
            coverage_score = calculate_coverage_score(summary, text)
            
            result = {
                "summary": summary,
                "metrics": {
                    "compression_ratio": round(compression_ratio, 3),
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
            return [s for s in sentences if len(s.split()) > 5][:num_bullets]
        
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
                if point and point not in takeaways:
                    takeaways.append(point)
            except:
                continue
            
            if len(takeaways) >= num_bullets:
                break
                
        return takeaways[:num_bullets]

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
