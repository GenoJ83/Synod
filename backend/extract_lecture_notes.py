#!/usr/bin/env python3
"""
Extraction Script for Synod Lecture Assistant
Iterates through the 'Lecture Notes' directory and extracts text from PDF and PPTX files.
Saves the combined text to 'training_data/lecture_notes_combined.txt'.
"""

import os
import sys
from pathlib import Path

# Add backend to path to import ExtractorService
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ingestion.extractor_service import ExtractorService

LECTURE_NOTES_DIR = "../Lecture Notes"
OUTPUT_FILE = "training_data/lecture_notes_combined.txt"

def main():
    extractor = ExtractorService()
    lecture_notes_path = Path(LECTURE_NOTES_DIR).resolve()
    output_path = Path(OUTPUT_FILE).resolve()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Scanning directory: {lecture_notes_path}")
    
    combined_text = []
    
    # Supported extensions
    extensions = {'.pdf', '.pptx', '.txt'}
    
    files = [f for f in lecture_notes_path.iterdir() if f.suffix.lower() in extensions]
    print(f"Found {len(files)} files to process.")
    
    for i, file_path in enumerate(files):
        print(f"[{i+1}/{len(files)}] Extracting text from: {file_path.name}")
        try:
            text = extractor.extract_text(str(file_path))
            if text and len(text.strip()) > 100:
                combined_text.append(f"--- SOURCE: {file_path.name} ---\n")
                combined_text.append(text)
                combined_text.append("\n\n")
            else:
                print(f"  ! Warning: Extracted text too short or empty for {file_path.name}")
        except Exception as e:
            print(f"  ! Error processing {file_path.name}: {e}")
            
    if combined_text:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("".join(combined_text))
        print(f"\n✅ Successfully extracted text from {len(combined_text)//3} files.")
        print(f"✅ Combined text saved to: {output_path}")
    else:
        print("\n❌ No text was extracted.")

if __name__ == "__main__":
    main()
