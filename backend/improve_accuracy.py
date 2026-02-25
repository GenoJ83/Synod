#!/usr/bin/env python3
"""
Data Augmentation Script for Synod Lecture Assistant
Extracts training pairs from local lecture text to address underfitting.
"""

import os
import re
import json
import random

LECTURE_FILE = "cleaned_lecture_text.txt"
OUTPUT_DIR = "training_data"

def extract_summarization_pairs(text):
    """
    Simulates summary pairs by taking paragraphs and their 'titles' or 'first sentences'.
    In a real scenario, we might use a larger model to generate these once, but here
    we'll use rule-based extraction from the lecture format.
    """
    pairs = []
    # Split by topic-like headers or bulleted sections
    sections = re.split(r'\n(?=[A-Z\s]{5,})', text)
    
    for section in sections:
        lines = [l.strip() for l in section.split('\n') if l.strip()]
        if len(lines) < 3:
            continue
            
        header = lines[0]
        content = " ".join(lines[1:])
        
        if len(content.split()) > 30:
            # We treat the header + first sentence as a summary proxy for the rest
            summary = f"{header}: {lines[1]}"
            pairs.append({"text": content, "summary": summary})
            
    return pairs

def extract_concept_pairs(text):
    """
    Extracts potential concepts (Capitalized terms) and their contexts.
    """
    pairs = []
    # Find common educational concepts (capitalized words/phrases)
    # This is a heuristic for the 'all-MiniLM-L6-v2' model
    concepts = set(re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text))
    concepts = {c for c in concepts if len(c) > 3 and c.lower() not in ['the', 'this', 'that', 'from']}
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Positive pairs
    for concept in concepts:
        found_in = [s for s in sentences if concept in s]
        if found_in:
            pairs.append({"text": found_in[0], "concept": concept.lower(), "label": 1.0})
            
    # Negative pairs (random mismatch)
    concept_list = list(concepts)
    for _ in range(len(pairs)):
        s = random.choice(sentences)
        c = random.choice(concept_list)
        if c not in s:
            pairs.append({"text": s, "concept": c.lower(), "label": 0.0})
            
    return pairs

def main():
    if not os.path.exists(LECTURE_FILE):
        print(f"Error: {LECTURE_FILE} not found.")
        return

    with open(LECTURE_FILE, 'r') as f:
        text = f.read()

    print(f"Extracting data from {LECTURE_FILE}...")
    
    sum_pairs = extract_summarization_pairs(text)
    con_pairs = extract_concept_pairs(text)
    
    print(f"Extracted {len(sum_pairs)} summarization pairs.")
    print(f"Extracted {len(con_pairs)} concept pairs.")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(os.path.join(OUTPUT_DIR, "summarization_augmented.json"), 'w') as f:
        json.dump(sum_pairs, f, indent=2)
        
    with open(os.path.join(OUTPUT_DIR, "concepts_augmented.json"), 'w') as f:
        json.dump(con_pairs, f, indent=2)
        
    print(f"Data saved to {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
