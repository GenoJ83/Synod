try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

from typing import List, Optional

class Summarizer:
    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6"):
        """
        Initializes the summarization model and tokenizer.
        Uses distilbart for a good balance of speed and quality.
        """
        self.has_transformers = HAS_TRANSFORMERS
        if HAS_TRANSFORMERS:
            try:
                print(f"Loading summarization model: {model_name}...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                self.model.to(self.device)
                print(f"Model loaded on {self.device}.")
            except Exception as e:
                print(f"Error loading model: {e}. Falling back to MOCK mode.")
                self.has_transformers = False
        else:
            print("Transformers not found. Running in MOCK mode.")
    
    def summarize(self, text: str, max_length: int = 150, min_length: int = 40) -> str:
        """
        Summarizes the input text.
        """
        if not text or len(text.strip()) < 50:
            return text
        
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
            
            # Simple compression metric
            compression_ratio = len(summary.split()) / max(1, len(text.split()))
            
            return {
                "summary": summary,
                "metrics": {
                    "compression_ratio": round(compression_ratio, 3)
                }
            }
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
