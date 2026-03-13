#!/usr/bin/env python3
"""
Dedicated Concept Extractor Training Script
Fine-tunes the sentence transformer model on enriched concept data.
"""

import os
import sys
import json
import time
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# Configuration
MODEL_NAME = "all-MiniLM-L6-v2"
RICH_DATA_PATH = "training_data/rich_concepts.json"
OUTPUT_DIR = "trained_models/concept_extractor"

def train():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load model
    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    
    # Force CPU/MPS stability detection
    import torch
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    
    print(f"Training on device: {device}")
    model.to(device)

    # Load rich concept data
    if not os.path.exists(RICH_DATA_PATH):
        print(f"Error: {RICH_DATA_PATH} not found. Run build_rich_dataset.py first.")
        return

    print(f"Loading data from {RICH_DATA_PATH}...")
    with open(RICH_DATA_PATH, 'r') as f:
        concept_data = json.load(f)
    
    train_examples = []
    for item in concept_data:
        train_examples.append(InputExample(texts=[item["text"], item["concept"]], label=float(item["label"])))
    
    print(f"Total concept training examples: {len(train_examples)}")
    
    # Create data loader
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=8)
    
    # Use cosine similarity loss
    train_loss = losses.CosineSimilarityLoss(model)
    
    # Train
    epochs = 10
    print(f"\nStarting training for {epochs} epochs...")
    start_time = time.time()
    
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=100,
        output_path=OUTPUT_DIR,
        show_progress_bar=True
    )
    
    training_time = time.time() - start_time
    print(f"\n✅ Training complete in {training_time/60:.2f} minutes!")
    print(f"✅ Model saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    train()
