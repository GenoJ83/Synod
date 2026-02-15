import sys
import traceback
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "sshleifer/distilbart-cnn-12-6"

print(f"Attempting to load: {model_name}")
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    print("Tokenizer loaded.")
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    print("Model loaded.")
    print("SUCCESS")
except Exception:
    traceback.print_exc()
