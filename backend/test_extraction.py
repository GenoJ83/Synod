import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.ingestion.extractor_service import ExtractorService

def test_sanitization():
    print("Testing ExtractorService Sanitization...")
    
    dirty_text = """
    In this research, we pro-
    pose a new method for syn-
    thesized intelligence. 
    
    Check out our code at https://github.com/example/repo for more details.
    
    Abstract: This is the introduction.
    
    Results: We found great things.
    
    References
    1. Smith et al. (2020). Random Paper.
    2. Doe et al. (2021). Another Paper.
    """
    
    sanitized = ExtractorService._sanitize_text(dirty_text)
    
    print("\n--- Original ---")
    print(dirty_text)
    
    print("\n--- Sanitized ---")
    print(sanitized)
    
    # Assertions
    assert "propose" in sanitized, "Failed to merge 'pro-\\npose'"
    assert "synthesized" in sanitized, "Failed to merge 'syn-\\nthesized'"
    assert "https://" not in sanitized, "Failed to strip URL"
    assert "References" not in sanitized, "Failed to truncate at References"
    assert "Smith et al." not in sanitized, "Failed to remove reference content"
    
    print("\n✅ Sanitization Test Passed!")

if __name__ == "__main__":
    test_sanitization()
