from transformers import pipeline
from typing import List, Optional

class Summarizer:
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """
        Initializes the summarization pipeline.
        Default model is BART, which is excellent for abstractive summarization.
        """
        print(f"Loading summarization model: {model_name}...")
        self.summarizer = pipeline("summarization", model=model_name)
    
    def summarize(self, text: str, max_length: int = 150, min_length: int = 40) -> str:
        """
        Summarizes the input text.
        """
        if not text or len(text.strip()) < 50:
            return text
        
        # Split text into chunks if it's too long (transformers have a token limit)
        # For simplicity, we'll assume the input is within limits for now or should be pre-chunked.
        summary = self.summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']

    def summarize_batch(self, texts: List[str]) -> List[str]:
        """
        Summarizes a list of text chunks.
        """
        summaries = self.summarizer(texts, max_length=150, min_length=40, do_sample=False)
        return [s['summary_text'] for s in summaries]

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
