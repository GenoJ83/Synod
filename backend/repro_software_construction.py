import sys
import os
import re

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.ingestion.extractor_service import ExtractorService
    from app.nlp.summarizer import Summarizer
    from app.nlp.explanation_generator import ExplanationGenerator
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def repro_robustness():
    # Much larger text sample from the "Software Construction" lecture to test robustness
    sample_text = """
Topic: Introduction to Software Construction
Simon Fred Lubambo
Department of Computing & Technology
Faculty of Engineering, Design & Technology 

Lecture Objectives and Learning outcomes
The Objectives of the lecture are;
1. Introduction to Software construction
2. Define software construction
3. Importance of software construction

What is Software Construction?
Software construction is a software engineering discipline that refers to the detailed creation of working, meaningful software through a combination of coding, verification, unit testing, integration testing, and debugging.
It is the process of building software systems that are readable, maintainable, testable, and adaptable to change.
In real-world environments, software is typically built by teams, not individuals. This necessitates clear communication, documentation, and the use of version control systems.
Software Construction is not just about writing code. It involves a set of activities that ensure the resulting software is of high quality and meets the needs of the users.

Why Software Construction Matters?
1. Quality: High-quality software is more reliable, efficient, and secure. Poorly constructed software is prone to bugs, crashes, and security vulnerabilities.
2. Maintainability: Software systems are often long-lived and need to be updated and maintained over time. Readable and well-structured code is easier to understand and modify, which reduces the cost of maintenance.
3. Evolution: Software that cannot evolve becomes obsolete, even if it once worked well. Software must be able to adapt to changing requirements, new technologies, and evolving user needs.
4. Professionalism: Software construction is a disciplined activity that requires a high level of skill and professionalism.

The Programming Perspective vs. The Construction Perspective
Programming is a part of software construction, but construction is much broader. 
Programming focuses on the individual activity of writing code to solve a specific problem.
Software Construction focuses on the collaborative activity of building large, complex systems that involve multiple components, multiple developers, and long-term maintenance.
Construction includes activities like:
- Peer reviews (verification)
- Unit testing and Integration testing
- Debugging and optimization
- Architectural design at a local level

The Role of Teams
In modern software development, teams are essential. No single person can build a complex system like a web browser, an operating system, or a large-scale enterprise application.
Teams rely on:
- Coding standards to ensure consistency.
- Version control (like Git) to manage changes.
- Automated build systems and Continuous Integration (CI).
- Effective communication and documentation.

Consequences of Poor Construction
- High technical debt: Shortcuts taken during construction lead to higher costs later.
- Fragility: The system breaks easily when changes are made.
- Onboarding difficulty: New developers take a long time to understand the messy code.
- Eventual replacement: The system becomes so difficult to maintain that it must be rewritten from scratch.
"""

    print("\n--- 1. Testing ExtractorService (Robustness) ---")
    # Wrap in a dummy file context if needed, but here we test the direct cleanup logic
    # We'll use a temporary file to simulate file-based extraction
    test_file = "temp_robust_test.txt"
    with open(test_file, "w") as f:
        f.write(sample_text)
    
    try:
        cleaned_text = ExtractorService.extract_text(test_file)
        print(f"Cleaned text length: {len(cleaned_text)}")
        
        # Check for header removal
        headers_found = []
        if "Simon Fred" in cleaned_text: headers_found.append("Simon Fred")
        if "Faculty of Engineering" in cleaned_text: headers_found.append("Faculty of Engineering")
        if "Topic:" in cleaned_text: headers_found.append("Topic:")
        
        if headers_found:
            print(f"WARNING: Headers {headers_found} still present.")
        else:
            print("SUCCESS: Headers successfully stripped.")
            
        print("\n--- 2. Testing Summarizer (Robustness) ---")
        summarizer = Summarizer()
        print(f"Summary Word Count: {len(summary_data['summary'].split())} words")
        print(f"Summary: {summary_data['summary']}")
        print(f"\nTakeaways ({len(summary_data['takeaways'])} points):")
        for i, pt in enumerate(summary_data['takeaways'], 1):
            print(f"{i}. {pt}")
            
        print(f"\nMetrics: {summary_data['metrics']}")
        
        print("\n--- 3. Testing Concept Extraction (Robustness) ---")
        from app.nlp.extractor import ConceptExtractor
        extractor = ConceptExtractor()
        concepts = extractor.extract_concepts(cleaned_text)
        print(f"Top Concepts: {[c['term'] for c in concepts]}")
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    repro_robustness()
