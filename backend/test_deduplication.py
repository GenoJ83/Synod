import sys
import os
from app.nlp.summarizer import Summarizer, _fix_repetition_artifacts
from app.nlp.extractor import ConceptExtractor
from app.nlp.explanation_generator import ExplanationGenerator

def test_repetition_fixing():
    print("\n=== Testing Repetition Artifact Fixing ===")
    text = "Detailed Use Cases Cases Cases are essential. software software construction."
    fixed = _fix_repetition_artifacts(text)
    print(f"Original: {text}")
    print(f"Fixed:    {fixed}")
    if "Cases Cases" not in fixed and "software software" not in fixed:
        print("[SUCCESS] Repetition artifacts collapsed.")
    else:
        print("[FAIL] Repetition artifacts still present.")

def test_concept_merging():
    print("\n=== Testing Concept Merging ===")
    extractor = ConceptExtractor()
    text = """
    Clean code philosophy is about writing maintainable software. 
    Clean code practices involve naming and structure.
    Quality clean code directly supports maintainability by reducing cognitive load.
    The lecture covers the importance of clean code and maintainability.
    """
    concepts = extractor.extract_concepts(text, top_n=5)
    print("Extracted Concepts:")
    for c in concepts:
        print(f" - {c['term']} (relevance: {c['relevance']})")
    
    # Check if we have too many variations of "clean code"
    clean_code_variations = [c['term'] for c in concepts if "clean code" in c['term']]
    if len(clean_code_variations) <= 2:
        print("[SUCCESS] Concept merging worked (variations limited).")
    else:
        print(f"[WARNING] Found {len(clean_code_variations)} variations of 'clean code'. Merging might be too loose.")

def test_unique_explanations():
    print("\n=== Testing Unique Explanations ===")
    extractor = ConceptExtractor()
    eg = ExplanationGenerator()
    text = """
    Clean code is about writing code that other people can read.
    Maintainable software is software that can be modified without fear.
    Technical debt slows innovation and increases costs over time.
    Shared standards are achieved through code reviews and refactoring.
    """
    concepts_dicts = extractor.extract_concepts(text, top_n=4)
    concept_names = [c['term'] for c in concepts_dicts]
    
    explanations = eg.generate_all_explanations(concept_names, text, extractor=extractor)
    
    reasons = [c['reason'] for c in explanations['concepts']]
    unique_reasons = set(reasons)
    
    print("Concepts and Explanations:")
    for c in explanations['concepts']:
        print(f" - {c['term']}: {c['reason'][:100]}...")
        
    if len(unique_reasons) == len(reasons):
        print("[SUCCESS] All explanations are unique.")
    else:
        print(f"[FAIL] Found duplicate explanations ({len(reasons) - len(unique_reasons)} duplicates).")

if __name__ == "__main__":
    test_repetition_fixing()
    test_concept_merging()
    test_unique_explanations()
