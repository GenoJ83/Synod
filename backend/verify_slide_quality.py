
import sys
import os
import re
sys.path.insert(0, os.getcwd())

from app.ingestion.extractor_service import ExtractorService
from app.nlp.summarizer import Summarizer
from app.nlp.explanation_generator import ExplanationGenerator

def verify_quality():
    # Simulate a lecture slide deck with repetitive headers
    lecture_text = """
Faculty of Engineering, Design & Technology DSC3108: Big Data Mining and Analytics Lecture 01 (BSCS_3:1) Fri 6th Sept 2024
COURSE OVERVIEW
Big Data Fundamentals and Mining
Data Analytics
Predictive analytics
Descriptive analytics
Data Mining Techniques
Architectures, storage of data
COURSE OVERVIEW 1.

Faculty of Engineering, Design & Technology DSC3108: Big Data Mining and Analytics Lecture 01 (BSCS_3:1) Fri 6th Sept 2024
What is Data?
Data is a collection of facts, such as numbers, words, measurements, observations or just descriptions of things.
It is the raw material for information and knowledge.

Faculty of Engineering, Design & Technology DSC3108: Big Data Mining and Analytics Lecture 01 (BSCS_3:1) Fri 6th Sept 2024
Need for Data Science
Introduction to Big Data
Big Data can bring "big values" to our life in almost every aspect.
It helps in predicting trends and making informed decisions.

Faculty of Engineering, Design & Technology DSC3108: Big Data Mining and Analytics Lecture 01 (BSCS_3:1) Fri 6th Sept 2024
Lecture Objectives
Understand the characteristics, challenges, and opportunities of big data
Learn about the big data architectures
Learn about big data storage and management.
    """
    
    print("--- 1. Testing ExtractorService Header Removal ---")
    # We need to simulate the sanitize process which identifies headers based on frequency
    # Since our sample is small, we'll see if the new logic catches it
    cleaned_text = ExtractorService._sanitize_text(lecture_text)
    print("\nCleaned Text Preview:")
    print(cleaned_text[:500])
    
    header_phrase = "Faculty of Engineering"
    if header_phrase in cleaned_text and cleaned_text.count(header_phrase) > 1:
        print(f"\nFAILURE: Header '{header_phrase}' still repeats {cleaned_text.count(header_phrase)} times.")
    else:
        print(f"\nSUCCESS: Header '{header_phrase}' removed or significantly reduced.")

    print("\n--- 2. Testing Summarizer with Sparse Content ---")
    s = Summarizer()
    sum_result = s.summarize(cleaned_text)
    print("\nSummary:")
    print(sum_result["summary"])

    print("\n--- 3. Testing ExplanationGenerator Header Filtering ---")
    eg = ExplanationGenerator()
    # "Big Data" might be in a header-like line
    explanation = eg.generate_explanation("Big Data", cleaned_text)
    print(f"\nExplanation for 'Big Data':")
    print(explanation)
    
    if "Faculty of Engineering" in explanation:
        print("\nFAILURE: Header leaked into concept explanation.")
    else:
        print("\nSUCCESS: Concept explanation is clean.")

if __name__ == "__main__":
    verify_quality()
