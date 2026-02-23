try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

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

from typing import List, Optional

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
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                # Device detection: CUDA -> MPS -> CPU
                if torch.cuda.is_available():
                    self.device = "cuda"
                    self.model = self.model.half() # Precision optimization for CUDA
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self.device = "mps"
                    # Half precision (FP16) is highly efficient on MPS
                    self.model = self.model.half()
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
        
        # Cache check
        text_hash = hash(text)
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
            inputs = self.tokenizer([text], max_length=1024, return_tensors="pt", truncation=True).to(self.device)
            summary_ids = self.model.generate(inputs["input_ids"], num_beams=4, max_length=max_length, min_length=min_length, early_stopping=True)
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            
            # Post-processing: Redundancy filter
            sentences = summary.split(". ")
            if len(sentences) > 2:
                # Basic redundancy check: remove sentences that are too similar or almost identical
                filtered_sentences = [sentences[0]]
                for i in range(1, len(sentences)):
                    is_redundant = False
                    for prev in filtered_sentences:
                        # Simple overlap check for now; could be upgraded to embedding similarity
                        s1, s2 = set(sentences[i].lower().split()), set(prev.lower().split())
                        if len(s1 & s2) / max(len(s1), len(s2)) > 0.8:
                            is_redundant = True
                            break
                    if not is_redundant:
                        filtered_sentences.append(sentences[i])
                summary = ". ".join(filtered_sentences)

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
