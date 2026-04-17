
import os
import sys
from app.ingestion.extractor_service import ExtractorService

def test_router():
    print("--- Testing Router ---")
    service = ExtractorService()
    
    # Test cases for extensions
    test_files = [
        "test.pdf",
        "test.pptx",
        "test.txt",
        "test.png",
        "test.jpg",
        "test.jpeg",
        "test.doc" # Should fail
    ]
    
    for f in test_files:
        ext = os.path.splitext(f)[1].lower()
        try:
            # We don't need the file to exist to test the router logic if we mock the methods
            print(f"Checking router for: {f}")
            # This is a bit tricky since they are static methods. 
            # I'll just check if the code reaches the right branch by checking the error message 
            # (which will be 'Failed to extract' or 'Unsupported extension')
            try:
                service.extract_text(f)
            except RuntimeError as e:
                msg = str(e)
                if "Failed to extract text from" in msg:
                    print(f"  ✅ Router correctly identified {ext}")
                else:
                    print(f"  ❌ Unexpected error for {ext}: {msg}")
            except ValueError as e:
                if "Unsupported file extension" in str(e):
                    if ext == ".doc":
                        print(f"  ✅ Router correctly rejected {ext}")
                    else:
                        print(f"  ❌ Router incorrectly rejected {ext}")
        except Exception as e:
            print(f"  💥 Fatal error testing {f}: {e}")

if __name__ == "__main__":
    # Add project root to path so we can import app
    sys.path.append(os.getcwd())
    test_router()
