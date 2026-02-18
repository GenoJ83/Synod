"""
Script to download all NLP models used in the Lecture Assistant project.
This allows the models to be used offline after initial download.

Usage:
    # Without token (slower downloads):
    python download_models.py
    
    # With Hugging Face token (faster downloads, higher rate limits):
    set HF_TOKEN=your_token_here
    python download_models.py

Get a free HF token at: https://huggingface.co/settings/tokens
"""

import os
import sys
import subprocess

# Define models to download
MODELS = {
    "summarizer": "sshleifer/distilbart-cnn-12-6",
    "summarizer_test": "t5-small",
    "embeddings": "all-MiniLM-L6-v2"
}

# Base directory for storing models
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

def get_token():
    """Get Hugging Face token from environment or .env file."""
    # Check environment variable
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        return token
    
    # Check .env file in backend directory
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("HF_TOKEN=") or line.startswith("HUGGING_FACE_HUB_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if token:
                        return token
    return None

def setup_huggingface_token():
    """Set up Hugging Face token for authenticated downloads."""
    token = get_token()
    if token:
        os.environ["HF_TOKEN"] = token
        os.environ["HUGGING_FACE_HUB_TOKEN"] = token
        print("[OK] Hugging Face token configured")
        return True
    else:
        print("[WARNING] No HF_TOKEN found. Downloads will be slower/unauthenticated.")
        print("  Get a free token at: https://huggingface.co/settings/tokens")
        print("  Set it with: set HF_TOKEN=your_token_here")
        return False

def download_model_with_hfhub():
    """Download models using huggingface_hub."""
    token = get_token()
    
    print("\n" + "="*60)
    print("Downloading all models with Hugging Face Hub...")
    print("="*60)
    
    try:
        from huggingface_hub import snapshot_download
        
        # Download each model
        for model_name in MODELS.values():
            print(f"\nDownloading: {model_name}")
            try:
                cache_dir = os.path.join(MODEL_DIR, "transformers")
                os.makedirs(cache_dir, exist_ok=True)
                
                snapshot_download(
                    model_name,
                    cache_dir=cache_dir,
                    token=token,
                    local_files_only=False
                )
                print(f"  [OK] {model_name} downloaded")
            except Exception as e:
                print(f"  [ERROR] {e}")
        
        # Download spaCy model
        print(f"\nDownloading spaCy model: en_core_web_sm")
        result = subprocess.run(
            [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  [OK] en_core_web_sm downloaded")
        else:
            print(f"  [ERROR] spaCy error: {result.stderr}")
            
        return True
    except ImportError:
        print("huggingface_hub not installed. Trying alternative method...")
        return False

def download_with_transformers():
    """Alternative: Download using transformers library directly."""
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from sentence_transformers import SentenceTransformer
    
    token = get_token()
    
    print("\n" + "="*60)
    print("Downloading models using transformers...")
    print("="*60)
    
    results = {}
    
    # Download summarizer models
    for model_name in [MODELS["summarizer"], MODELS["summarizer_test"]]:
        print(f"\nDownloading: {model_name}")
        try:
            cache_dir = os.path.join(MODEL_DIR, "transformers", model_name.replace("/", "_"))
            os.makedirs(cache_dir, exist_ok=True)
            
            AutoTokenizer.from_pretrained(model_name, token=token, cache_dir=cache_dir)
            AutoModelForSeq2SeqLM.from_pretrained(model_name, token=token, cache_dir=cache_dir)
            print(f"  [OK] Success")
            results[model_name] = True
        except Exception as e:
            print(f"  [ERROR] {e}")
            results[model_name] = False
    
    # Download embeddings model
    print(f"\nDownloading: {MODELS['embeddings']}")
    try:
        cache_dir = os.path.join(MODEL_DIR, "transformers", MODELS['embeddings'].replace("/", "_"))
        os.makedirs(cache_dir, exist_ok=True)
        SentenceTransformer(MODELS['embeddings'], cache_folder=cache_dir)
        print(f"  [OK] Success")
        results[MODELS['embeddings']] = True
    except Exception as e:
        print(f"  [ERROR] {e}")
        results[MODELS['embeddings']] = False
    
    # Download spaCy model
    print(f"\nDownloading spaCy model...")
    result = subprocess.run(
        [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
        capture_output=True,
        text=True
    )
    results["en_core_web_sm"] = result.returncode == 0
    if result.returncode == 0:
        print(f"  [OK] Success")
    else:
        print(f"  [ERROR]")
    
    return results

def create_offline_config():
    """Create a configuration file for offline model loading."""
    config_content = f"""# Offline Model Configuration
# Models downloaded to: {os.path.abspath(MODEL_DIR)}
#
# To use offline, set environment variables:
#   set TRANSFORMERS_CACHE={os.path.abspath(MODEL_DIR)}
#
# Models:
# - distilbart-cnn-12-6 (summarizer)
# - t5-small (testing)
# - all-MiniLM-L6-v2 (embeddings)
# - en_core_web_sm (spaCy)
"""
    
    config_path = os.path.join(MODEL_DIR, "OFFLINE_CONFIG.txt")
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"\n[OK] Config saved: {config_path}")

def main():
    """Download all required models."""
    print("="*60)
    print("Lecture Assistant - Model Downloader")
    print("="*60)
    
    # Setup token
    has_token = setup_huggingface_token()
    
    print(f"\nModels will be saved to: {MODEL_DIR}")
    print("\nDownloading models...")
    
    # Create models directory
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Try huggingface_hub first, fall back to transformers
    success = download_model_with_hfhub()
    if not success:
        results = download_with_transformers()
    
    # Create config
    create_offline_config()
    
    print("\n" + "="*60)
    print("Download complete!")
    print("="*60)
    print(f"\nModels saved to: {os.path.abspath(MODEL_DIR)}")
    
    if not has_token:
        print("\n[NOTE] For faster future downloads, add your HF_TOKEN:")
        print("   Create backend/.env with: HF_TOKEN=your_token")

if __name__ == "__main__":
    main()
