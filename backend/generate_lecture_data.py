#!/usr/bin/env python3
"""
Lecture Data Generation Script
Extracts training pairs (summaries and concepts) from the combined lecture notes text.
Saves results to JSON files for fine-tuning.
"""

import os
import re
import json
import random
from pathlib import Path

INPUT_FILE = "training_data/lecture_notes_combined.txt"
OUTPUT_DIR = "training_data"

def extract_summarization_pairs(text):
    """
    Extracts header-content pairs as summarization training examples.
    """
    pairs = []
    # Split by the source markers we added in extraction
    sources = re.split(r'--- SOURCE: .* ---', text)
    
    for source_text in sources:
        if not source_text.strip():
            continue
            
        # Split by potential headers (lines that are short, capitalized, or end with :)
        # This is a heuristic adapted for lecture slides
        paragraphs = re.split(r'\n(?=[A-Z][\w\s]{2,40}(?::|\n))', source_text)
        
        for para in paragraphs:
            lines = [l.strip() for l in para.split('\n') if l.strip()]
            if len(lines) < 2:
                continue
                
            header = lines[0]
            # Heuristic: Headers shouldn't be too long and should look like titles
            if 3 < len(header.split()) < 10:
                content = " ".join(lines[1:])
                if len(content.split()) > 20:
                    pairs.append({
                        "text": content[:1500], # Cap input length
                        "summary": header
                    })
                    
    return pairs

def extract_concept_pairs(text):
    """
    Extracts terms and their contexts for concept extraction training.
    """
    pairs = []
    # Heuristic for technical concepts: Capitalized noun phrases
    concepts = set(re.findall(r'\b[A-Z][\w\s-]{3,30}\b', text))
    
    # Filter common non-concepts
    blacklist = {'Table', 'Figure', 'Slide', 'Source', 'Note', 'Example', 'Exercise', 'Quiz', 'Lecture', 'University'}
    concepts = {c.strip() for c in concepts if c.strip() not in blacklist and len(c.split()) <= 3}
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if 10 < len(s.split()) < 100]
    
    if not concepts or not sentences:
        return []

    # Positive pairs
    for concept in concepts:
        found_in = [s for s in sentences if concept in s]
        if found_in:
            # Take up to 3 context examples per concept
            for ctx in found_in[:3]:
                pairs.append({
                    "text": ctx,
                    "concept": concept.lower(),
                    "label": 1.0
                })
                
    # Negative pairs (random mismatch)
    concept_list = list(concepts)
    num_negatives = len(pairs)
    for _ in range(num_negatives):
        s = random.choice(sentences)
        c = random.choice(concept_list)
        if c.lower() not in s.lower():
            pairs.append({
                "text": s,
                "concept": c.lower(),
                "label": 0.0
            })
            
    return pairs

def main():
    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        print(f"Error: {INPUT_FILE} not found. Run extract_lecture_notes.py first.")
        return

    print(f"Reading extracted text from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    print("Generating summarization pairs...")
    sum_pairs = extract_summarization_pairs(text)
    print(f"✓ Generated {len(sum_pairs)} summarization pairs.")
    
    print("Generating concept pairs...")
    con_pairs = extract_concept_pairs(text)
    print(f"✓ Generated {len(con_pairs)} concept pairs.")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    sum_out = Path(OUTPUT_DIR) / "summarization_lecture_notes.json"
    with open(sum_out, 'w') as f:
        json.dump(sum_pairs, f, indent=2)
        
    con_out = Path(OUTPUT_DIR) / "concepts_lecture_notes.json"
    with open(con_out, 'w') as f:
        json.dump(con_pairs, f, indent=2)
        
    print(f"\n✅ Data saved to {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
