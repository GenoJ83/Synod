
import sys
import os
import re
sys.path.insert(0, os.getcwd())

from app.ingestion.extractor_service import ExtractorService
from app.nlp.summarizer import Summarizer
from app.nlp.explanation_generator import ExplanationGenerator

def repro_failure():
    # Text from user's "Software Construction" lecture
Software Evolution Software systems change because: User needs evolve Business rules change Laws and regulations are updated Bugs are discovered Performance requirements increase -> Software that cannot evolve becomes obsolete, even if it once worked well.
Construction is the disciplined activity of building software systems that are readable, maintainable, testable, and adaptable to change.
Lecture Overview What Is Software Construction?
"""

    print("--- 1. Testing ExtractorService ---")
    cleaned = ExtractorService._sanitize_text(text)
    print("Cleaned text (first 200 chars):")
    print(repr(cleaned[:200]))
    
    # Check if headers are gone
    header_indicators = ["Simon Fred Lubambo", "Faculty of Engineering"]
    for ind in header_indicators:
        if ind in cleaned:
            print(f"WARNING: Header '{ind}' still present.")
        else:
            print(f"SUCCESS: Header '{ind}' removed.")

    print("\n--- 2. Testing Summarizer ---")
    s = Summarizer()
    res = s.summarize(cleaned)
    print(f"Summary: {res['summary']}")
    print(f"Metrics: {res['metrics']}")

    print("\n--- 3. Testing ExplanationGenerator ---")
    eg = ExplanationGenerator()
    concepts = ["programming and software construction", "software construction"]
    for concept in concepts:
        exp = eg.generate_explanation(concept, cleaned, extractor=None)
        print(f"\nConcept: {concept}")
        print(f"Explanation: {exp[:200]}...")

if __name__ == "__main__":
    repro_failure()
