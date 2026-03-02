import sys
import os
sys.path.insert(0, os.getcwd())

from app.nlp.summarizer import Summarizer
from app.ingestion.extractor_service import ExtractorService

def test_quality():
    print("=== Testing Ingestion Quality (Header Stripping) ===")
    lecture_text = """DSC4001: Software Construction
Lecture 5: Design Patterns
Faculty of Engineering
Simon Fred
Lubambo

Introduction:
Design patterns are reusable solutions to common problems in software design.
They serve as templates that can be applied to real-world coding challenges.
This lecture covers the Observer pattern and the Factory pattern.
"""
    # Simulate saving to a txt file and extracting
    test_file = "test_lecture.txt"
    with open(test_file, "w") as f:
        f.write(lecture_text)
    
    # Test Extraction (should strip headers)
    service = ExtractorService()
    extracted = service.extract_text(test_file)
    os.remove(test_file)
    
    print("\n--- Extracted Text (Head) ---")
    print("\n".join(extracted.splitlines()[:5]))
    
    if "Simon Fred" in extracted or "DSC4001" in extracted:
        print("\n[WARNING] Metadata still present in extracted text!")
    else:
        print("\n[SUCCESS] Metadata successfully stripped.")

    print("\n=== Testing Summarization Robustness ===")
    noisy_text = """
    Design patterns are reusable solutions to common problems in software design.
    Design patterns are reusable solutions to common problems in software design.
    The model pro-ishyposes a new framework for an-ogleswering complex questions.
    It fol-lowing the standard implementation steps for trans-formers.
    The list-wise approach is superior to pair-wise ranking in many cases.
    """
    
    summarizer = Summarizer()
    result = summarizer.summarize(noisy_text)
    summary = result["summary"]
    
    print("\n--- Result Summary ---")
    print(summary)
    
    # Check for artifacts
    artifacts = ["pro-ishypose", "an-ogleswering", "fol-lowing", "trans-former"]
    found_artifacts = [a for a in artifacts if a in summary.lower()]
    
    if found_artifacts:
        print(f"\n[WARNING] Artifacts found: {found_artifacts}")
    else:
        print("\n[SUCCESS] No tokenization artifacts found.")
        
    # Check for redundancy (simple check)
    original_line = "Design patterns are reusable solutions to common problems in software design."
    if summary.count(original_line) > 1:
        print("\n[WARNING] Redundancy filter failed (duplicate sentences found).")
    else:
        print("\n[SUCCESS] Redundancy filter worked.")
        
    print("\n--- Takeaways ---")
    print(result.get("takeaways", []))

if __name__ == "__main__":
    test_quality()
