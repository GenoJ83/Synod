import sys
import os
from app.nlp.summarizer import Summarizer
from app.nlp.extractor import ConceptExtractor
from app.nlp.explanation_generator import ExplanationGenerator

def test_recursive_summary():
    print("\n=== Testing Recursive Executive Summary (>= 300 words) ===")
    summarizer = Summarizer()
    # Large text sample (Clean Code concepts repeated to simulate long lecture)
    text = """
    Clean code is not just a set of rules; it is a philosophy that prioritizes human readability and maintainability over clever tricks or technical density. 
    A fundamental aspect of clean code is the naming of variables, functions, and classes. Names should be descriptive, revealing intent without requiring 
    the reader to search for context elsewhere. For example, 'daysSinceCreation' is far superior to 'd'. 
    
    Functions should be small and do only one thing. If a function is too large, it often indicates that it's violating the Single Responsibility Principle, 
    making it harder to test and more prone to bugs during refactoring. We must also consider the 'Boy Scout Rule': leave the code better than you found it.
    
    Technical debt is another critical concept. It refers to the long-term cost of choosing an easy solution now instead of a better approach that takes longer. 
    While technical debt can be at times necessary for meeting deadlines, it must be managed carefully. Unresolved debt leads to 'software rot', where 
    the system becomes too brittle to change. 
    
    Continuous integration and automated testing are the safety nets of clean code. They allow developers to refactor with confidence, knowing that 
    existing functionality is preserved. Code reviews further ensure that shared standards are maintained across the team, fostering a culture of 
    collective ownership and continuous improvement. 
    
    Maintainability is the ultimate goal. Software is read far more often than it is written. Therefore, every line of code we write is an investment in 
    the future speed and efficiency of the development team. By following clean code practices, we reduce cognitive load and make the system sustainable.
    """ * 10 # Repeat to make it > 1000 words for the 300-word requirement
    
    result = summarizer.summarize(text)
    summary = result['summary']
    word_count = len(summary.split())
    
    print(f"Original Text Length: {len(text.split())} words")
    print(f"Summary Word Count: {word_count}")
    print("\nSummary Peek (First 100 words):")
    print(" ".join(summary.split()[:100]) + "...")
    
    if word_count >= 300:
        print(f"[SUCCESS] Executive summary reached {word_count} words.")
    else:
        print(f"[FAIL] Summary only has {word_count} words (needed >= 300).")

def test_structured_explanations():
    print("\n=== Testing Structured Explanations (definition + context) ===")
    eg = ExplanationGenerator()
    extractor = ConceptExtractor()
    text = "Clean coding involves writing maintainable systems. Technical debt is expensive."
    concepts = ["clean coding", "technical debt"]
    
    explanations = eg.generate_all_explanations(concepts, text, extractor=extractor)
    
    print("Explanation Structure:")
    for c in explanations['concepts']:
        print(f"Term: {c['term']}")
        print(f" - Definition: {c['definition']}")
        print(f" - Context: {c.get('context', 'N/A')}")
        
        if 'definition' in c and 'term' in c:
            print("[SUCCESS] Found correct fields.")
        else:
            print("[FAIL] Missing standard fields.")
            
    # Fuzzy match check
    if "Clean code" in explanations['concepts'][0]['definition']:
        print("[SUCCESS] Fuzzy match for 'clean coding' -> 'clean code' worked.")
    else:
        print("[FAIL] Fuzzy match failed.")

if __name__ == "__main__":
    test_recursive_summary()
    test_structured_explanations()
