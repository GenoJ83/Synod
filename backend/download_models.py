"""
Script to download all NLP models used in the Lecture Assistant project.
This allows the models to be used offline after initial download.

Usage:
    python download_models.py

Requirements:
    - transformers
    - sentence-transformers
    - spacy
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
import subprocess
import sys
import os

# Define models to download
MODELS = {
    "summarizer": "sshleifer/distilbart-cnn-12-6",
    "summarizer_test": "t5-small",
    "embeddings": "all-MiniLM-L6-v2"
}

# Base directory for storing models
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

def run_command(cmd: list) -> bool:
    """Run a command and return success status."""
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

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

def download_spacy_model(model_name: str = "en_core_web_sm"):
    """Download and cache the spaCy model."""
    print(f"\n{'='*60}")
    print(f"Downloading spaCy model: {model_name}")
    print(f"{'='*60}")
    
    try:
        # Try to download the model
        result = subprocess.run(
            [sys.executable, "-m", "spacy", "download", model_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"spaCy model '{model_name}' downloaded successfully!")
            return True
        else:
            print(f"Error downloading spaCy model: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error downloading spaCy model: {e}")
        return False

def create_offline_config():
    """Create a configuration file for offline model loading."""
    config_content = f"""# Offline Model Configuration
# Set these environment variables before running the application:
#
# For Hugging Face models:
#   Windows: set TRANSFORMERS_CACHE={os.path.abspath(MODEL_DIR)}
#   Linux/Mac: export TRANSFORMERS_CACHE="{os.path.abspath(MODEL_DIR)}"
#
# Models downloaded:
# - summarizer: sshleifer/distilbart-cnn-12-6
# - summarizer_test: t5-small  
# - embeddings: all-MiniLM-L6-v2
# - spacy: en_core_web_sm
"""
    
    config_path = os.path.join(MODEL_DIR, "OFFLINE_CONFIG.txt")
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"\nOffline config saved to: {config_path}")

def main():
    """Download all required models."""
    print("="*60)
    print("Lecture Assistant - Model Downloader")
    print("="*60)
    print(f"\nModels will be saved to: {MODEL_DIR}")
    print(f"Total models to download: 4")
    print("1. distilbart-cnn-12-6 (summarizer)")
    print("2. t5-small (testing summarizer)")
    print("3. all-MiniLM-L6-v2 (embeddings)")
    print("4. en_core_web_sm (spaCy)")
    
    # Create models directory if it doesn't exist
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Track results
    results = {}
    
    # Download summarizer models
    results["distilbart-cnn-12-6"] = download_summarizer_model(MODELS["summarizer"], MODEL_DIR)
    results["t5-small"] = download_summarizer_model(MODELS["summarizer_test"], MODEL_DIR)
    
    # Download embedding model
    results["all-MiniLM-L6-v2"] = download_embedding_model(MODELS["embeddings"], MODEL_DIR)
    
    # Download spaCy model
    results["en_core_web_sm"] = download_spacy_model()
    
    # Create offline config
    create_offline_config()
    
    # Print summary
    print(f"\n{'='*60}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    
    for model_name, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{model_name}: {status}")
    
    # Check if all succeeded
    if all(results.values()):
        print(f"\n{'='*60}")
        print("ALL MODELS DOWNLOADED SUCCESSFULLY!")
        print(f"{'='*60}")
        print(f"\nModels saved to: {os.path.abspath(MODEL_DIR)}")
        print("\nTo use these models offline:")
        print("-" * 40)
        print("Option 1 - Set environment variable:")
        print("  Windows CMD:")
        print(f"    set TRANSFORMERS_CACHE={os.path.abspath(MODEL_DIR)}")
        print("  Windows PowerShell:")
        print(f"    $env:TRANSFORMERS_CACHE='{os.path.abspath(MODEL_DIR)}'")
        print("  Linux/Mac:")
        print(f"    export TRANSFORMERS_CACHE='{os.path.abspath(MODEL_DIR)}'")
        print()
        print("Option 2 - Run the backend and models will load from cache automatically")
    else:
        print("\nSome models failed to download. Please check the errors above.")
        print("You can re-run this script to retry.")

if __name__ == "__main__":
    main()
