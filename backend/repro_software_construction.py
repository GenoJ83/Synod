
import sys
import os
import re
sys.path.insert(0, os.getcwd())

from app.ingestion.extractor_service import ExtractorService
from app.nlp.summarizer import Summarizer
from app.nlp.explanation_generator import ExplanationGenerator

def repro_failure():
    # Text from user's "Software Construction" lecture
    text = """
Topic: Introduction to Software Construction Simon Fred Lubambo Department of Computing & Technology Faculty of Engineering, Design & Technology 
Lecture Objectives and Learning outcomes The Objectives of this lecture are : Explain the concept and scope of Software Construction within the software development lifecycle.

Why Software Construction Matters In real-world environments: Code Software is built by teams, not individuals Software is used for years, not weeks Software must adapt to changing requirements 
Why Software Construction Matters Poor software construction leads to: High maintenance costs Frequent system failures Difficulty onboarding new developers Eventual system replacement 
Programming vs Software Construction Programming: Focuses on writing instructions for a computer Emphasis on correctness and functionality Often short-term and individual-focused 

Software Construction: Focuses on building systems for people and teams Emphasis on quality, structure, and longevity Long-term responsibility and collaboration Key Differences 
Real World Example A script that calculates student grades -> Programming 
A university grading system that: Handles missing data Supports policy changes Is maintained over several years -> Software Construction 

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
