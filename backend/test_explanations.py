
import os
import asyncio
from dotenv import load_dotenv

# Add project root to path
import sys
sys.path.append(os.getcwd())

from app.nlp.gemini_concept_explain import explain_concept_with_gemini, _gemini_enabled

async def test_explanation_without_snippet():
    load_dotenv()
    
    if not _gemini_enabled():
        print("❌ Gemini explanation not enabled (check USE_GEMINI_CONCEPT_EXPLAIN and GOOGLE_API_KEY)")
        return

    api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    concept = "Quantum Entanglement" # Something likely NOT in a simple lecture snippet
    snippet = "" # EMPTY SNIPPET
    
    print(f"--- Testing Explanation for '{concept}' with EMPTY snippet ---")
    
    result = await asyncio.to_thread(
        explain_concept_with_gemini,
        concept=concept,
        snippet=snippet,
        api_key=api_key
    )
    
    if result:
        print("✅ Received result from Gemini:")
        print(f"  Term: {result.get('term')}")
        print(f"  Definition: {result.get('definition')}")
        print(f"  Context: '{result.get('context')}' (Should be empty)")
        
        if result.get('definition') and not result.get('context'):
            print("🎉 Success! General knowledge used, context left empty.")
    else:
        print("❌ Failed to receive result from Gemini.")

if __name__ == "__main__":
    asyncio.run(test_explanation_without_snippet())
