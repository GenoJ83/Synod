"""
Script to download all NLP models used in the Lecture Assistant project.
This allows the models to be used offline after initial download.
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
import os

# Define models to download
MODELS = {
    "summarizer": "sshleifer/distilbart-cnn-12-6",
    "summarizer_test": "t5-small",
    "embeddings": "all-MiniLM-L6-v2"
}

# Base directory for storing models
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

def download_summarizer_model(model_name: str, cache_dir: str):
    """Download and cache the summarization model."""
    print(f"\n{'='*60}")
    print(f"Downloading summarization model: {model_name}")
    print(f"{'='*60}")
    
    try:
        print("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
        print(f"Tokenizer downloaded successfully!")
        
        print("Downloading model...")
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name, cache_dir=cache_dir)
        print(f"Model downloaded successfully!")
        
        # Save model locally
        save_path = os.path.join(cache_dir, model_name.replace("/", "_"))
        tokenizer.save_pretrained(save_path)
        model.save_pretrained(save_path)
        print(f"Model saved to: {save_path}")
        
        return True
    except Exception as e:
        print(f"Error downloading {model_name}: {e}")
        return False

def download_embedding_model(model_name: str, cache_dir: str):
    """Download and cache the sentence embedding model."""
    print(f"\n{'='*60}")
    print(f"Downloading embedding model: {model_name}")
    print(f"{'='*60}")
    
    try:
        print("Downloading model (this may take a while for first time)...")
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        print(f"Model downloaded successfully!")
        
        # Save model locally
        save_path = os.path.join(cache_dir, model_name.replace("/", "_"))
        model.save(save_path)
        print(f"Model saved to: {save_path}")
        
        return True
    except Exception as e:
        print(f"Error downloading {model_name}: {e}")
        return False

def main():
    """Download all required models."""
    print("="*60)
    print("Lecture Assistant - Model Downloader")
    print("="*60)
    print(f"\nModels will be saved to: {MODEL_DIR}")
    
    # Create models directory if it doesn't exist
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Track results
    results = {}
    
    # Download summarizer models
    results["distilbart"] = download_summarizer_model(MODELS["summarizer"], MODEL_DIR)
    results["t5-small"] = download_summarizer_model(MODELS["summarizer_test"], MODEL_DIR)
    
    # Download embedding model
    results["embeddings"] = download_embedding_model(MODELS["embeddings"], MODEL_DIR)
    
    # Print summary
    print(f"\n{'='*60}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    
    for model_name, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{model_name}: {status}")
    
    print(f"\nAll models downloaded to: {MODEL_DIR}")
    print("\nTo use these models offline:")
    print("1. Set HF_HOME or TRANSFORMERS_CACHE environment variable")
    print(f"   to: {os.path.abspath(MODEL_DIR)}")
    print("2. Or modify the code to load from the local path")

if __name__ == "__main__":
    main()
