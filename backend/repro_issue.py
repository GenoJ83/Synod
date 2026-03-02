
import sys
import os
import re
sys.path.insert(0, os.getcwd())

from app.nlp.summarizer import Summarizer

def repro():
    # Academic paper abstract (similar to user's example)
    text = """
    Built upon the existing analysis of retrieval heads in large language models, we propose an alternative reranking framework that trains models to estimate passage–query relevance using the attention scores of selected heads. This approach provides a listwise solution that leverages the holistic context of multiple passages to improve retrieval accuracy.
    """
    
    print("Initializing Summarizer with Pegasus model (forced DistilBART fallback on 8GB)...")
    s = Summarizer(model_name="UNIST-Eunchan/Research-Paper-Summarization-Pegasus-x-ArXiv")
    
    # Force a failure in the model generation to test our fallback UI
    print("\n--- FORCING MODEL FAILURE ---")
    s.has_transformers = True
    def dummy_generate(*args, **kwargs):
        raise RuntimeError("Simulated OOM or Model task error")
    
    if HAS_TRANSFORMERS:
        s.model.generate = dummy_generate

    print("\nAttempting to summarize...")
    try:
        result = s.summarize(text)
        print("\n--- Result Summary ---")
        print(result["summary"])
        print("\n--- Metrics ---")
        print(result["metrics"])
    except Exception as e:
        print(f"\nCaught exception in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from app.nlp.summarizer import HAS_TRANSFORMERS
    repro()
