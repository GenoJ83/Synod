
import sys
import os
import re
sys.path.insert(0, os.getcwd())

from app.nlp.summarizer import Summarizer

def repro():
    # EXACT text from user
    text = """
    Abstract Built upon the existing analysis of retrieval heads in large language models, we propose an alternative reranking framework that trains models to estimate passage–query relevance using the attention scores of selected heads. This approach provides a listwise solution that leverages the holistic information within the entire candidate shortlist during ranking. At the same time, it naturally produces continuous relevance scores, enabling training on arbitrary retrieval datasets without re...
    """
    
    print("Initializing Summarizer...")
    s = Summarizer()
    
    print("\nAttempting to summarize...")
    try:
        result = s.summarize(text)
        print("\n--- Result Summary ---")
        print(result["summary"])
        print("\n--- Metrics ---")
        print(result["metrics"])
    except Exception as e:
        print(f"\nCaught exception in main: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    repro()
