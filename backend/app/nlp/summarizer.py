import re
try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

import hashlib
from typing import List, Optional

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
    return round(overlap / len(s_words), 3) if s_words else 0.0

class Summarizer:
    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6"):
        """
        Initializes the summarization model and tokenizer.
        Uses distilbart for a good balance of speed and quality.
        """
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
                print(f"Error loading model: {e}. Falling back to MOCK mode.")
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
            
            # Dynamic length: target ~20-30% of document size, up to a massive 1500 words for deep context
            if max_length == 150: # If using the default short limit, override it dynamically
                target_max = min(1500, max(250, int(word_count * 0.3)))
                target_min = min(500, max(80, int(word_count * 0.1)))
            else:
                target_max = max_length
                target_min = min_length

            # Clean up newlines for better split
            clean_text = text.replace('\n', ' ')
            sentences = re.split(r'(?<=[.!?])\s+', clean_text)
            chunks = []
            current_chunk = ""
            current_len = 0
            
            # Use smaller chunks (400 words) so the model MUST describe more details per section
            for sentence in sentences:
                sentence_len = len(sentence.split())
                if current_len + sentence_len < 400:
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
                summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            else:
                # 1. First Pass: Process chunks separately
                chunk_summaries: List[str] = []
                # Use higher length per chunk to ensure we have enough "fuel" for a 300-word synthesis
                c_max = min(250, max(120, (target_max * 2) // len(chunks)))
                c_min = min(100, max(60, (target_min * 2) // len(chunks)))
                
                for chunk in chunks:
                    chunk_wc = len(chunk.split())
                    if chunk_wc < 40: continue
                    
                    inputs = self.tokenizer([chunk], max_length=1024, return_tensors="pt", truncation=True).to(self.device)
                    ids = self.model.generate(inputs["input_ids"], num_beams=4, max_length=c_max, min_length=c_min, early_stopping=True)
                    chunk_summary = self.tokenizer.decode(ids[0], skip_special_tokens=True).strip()
                    chunk_summaries.append(chunk_summary)
                
                # 2. Second Pass: Synthesis (Recursive Summarization)
                # Combine sectional summaries into a single synthesis input
                synthesis_input = " ".join(chunk_summaries)
                
                # If we need a 300-word executive summary, we summarize the summaries
                # This ensures global coherence instead of just chopped paragraphs
                try:
                    # User requirement: At least 300 words for the final summary if document is large
                    # Words to tokens ratio is ~1.4 for BART. So 300 words => ~420 tokens.
                    final_min = 450 if word_count > 1000 else int(target_min * 1.5)
                    final_max = max(final_min + 200, target_max)
                    
                    # Synthesis requires more "creativity" and flow
                    inputs = self.tokenizer([synthesis_input], max_length=1024, return_tensors="pt", truncation=True).to(self.device)
                    # Higher length_penalty favors longer, more detailed summaries
                    ids = self.model.generate(
                        inputs["input_ids"], 
                        num_beams=6, 
                        max_length=final_max, 
                        min_length=final_min, 
                        length_penalty=2.5,
                        early_stopping=True
                    )
                    summary = self.tokenizer.decode(ids[0], skip_special_tokens=True).strip()
                except Exception as e:
                    print(f"Synthesis pass failed: {e}. Falling back to combined chunks.")
                    summary = "\n\n".join(chunk_summaries)

            # Post-process: fix artifacts, apply length cap
            summary = _fix_tokenization_artifacts(summary)
            summary = _fix_repetition_artifacts(summary)
            
            # Simple compression metric
            compression_ratio = len(summary.split()) / max(1, len(text.split()))
            coverage_score = calculate_coverage_score(summary, text)
            
            # Generate takeaways automatically for a complete result
            takeaways = self.generate_takeaways(text)
            
            result = {
                "summary": summary,
                "takeaways": takeaways,
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
