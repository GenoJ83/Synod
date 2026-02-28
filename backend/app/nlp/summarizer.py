import re
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
                # Process chunks separately to capture full document context
                chunk_summaries = []
                c_max = min(180, max(80, target_max // len(chunks)))
                c_min = min(70, max(40, target_min // len(chunks)))
                
                for chunk in chunks:
                    chunk_wc = len(chunk.split())
                    if chunk_wc < 40: 
                        continue # Skip tiny straggling chunks at the end
                    
                    actual_c_max = min(c_max, int(chunk_wc * 0.8))
                    actual_c_min = min(c_min, int(chunk_wc * 0.3))
                    
                    inputs = self.tokenizer([chunk], max_length=1024, return_tensors="pt", truncation=True).to(self.device)
                    ids = self.model.generate(inputs["input_ids"], num_beams=4, max_length=actual_c_max, min_length=actual_c_min, early_stopping=True)
                    chunk_summary = self.tokenizer.decode(ids[0], skip_special_tokens=True).strip()
                    
                    # Redundancy filter per chunk (prevents repeating sentences within the chunk)
                    c_sentences = re.split(r'(?<=[.!?])\s+', chunk_summary)
                    if len(c_sentences) > 1:
                        filtered = [c_sentences[0]]
                        for i in range(1, len(c_sentences)):
                            is_redundant = False
                            for prev in filtered:
                                s1, s2 = set(c_sentences[i].lower().split()), set(prev.lower().split())
                                if len(s1 & s2) / max(1, len(s1), len(s2)) > 0.7:
                                    is_redundant = True
                                    break
                            if not is_redundant:
                                filtered.append(c_sentences[i])
                        chunk_summary = " ".join(filtered)
                        
                    chunk_summaries.append(chunk_summary)
                
                # Combine chunks into distinct readable paragraphs
                summary = "\n\n".join(chunk_summaries)

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
