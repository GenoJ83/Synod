
import sys
import os

# Add the current directory to sys.path so we can import app modules
sys.path.insert(0, os.getcwd())

from app.nlp.summarizer import Summarizer
from app.nlp.extractor import ConceptExtractor
from app.nlp.quiz_gen import QuizGenerator

def test_pipeline():
    print("--- Initializing Modules ---")
    try:
        summarizer = Summarizer()
        print("✅ Summarizer initialized")
    except Exception as e:
        print(f"❌ Summarizer failed: {e}")
        return

    try:
        extractor = ConceptExtractor()
        print("✅ ConceptExtractor initialized")
    except Exception as e:
        print(f"❌ ConceptExtractor failed: {e}")
        return

    try:
        quiz_gen = QuizGenerator()
        print("✅ QuizGenerator initialized")
    except Exception as e:
        print(f"❌ QuizGenerator failed: {e}")
        return

    text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural intelligence displayed by animals including humans. 
    AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.
    The term "artificial intelligence" had previously been used to describe machines that mimic and display "human" cognitive skills that are associated with the human mind, such as "learning" and "problem-solving".
    This definition has since been rejected by major AI researchers who now describe AI in terms of rationality and acting rationally, which does not limit how intelligence can be articulated.
    """

    print("\n--- Testing Summarization ---")
    try:
        summary = summarizer.summarize(text)
        if isinstance(summary, dict):
            summary = summary.get("summary", text)
        print(f"✅ Summary generated (Length: {len(summary)})")
        print(f"Snippet: {str(summary)[:50]}...")
    except Exception as e:
        print(f"❌ Summarization failed: {e}")
        summary = text # Fallback for next steps

    print("\n--- Testing Concept Extraction ---")
    try:
        concept_data = extractor.extract_concepts(text)
        concepts = (
            [c["term"] for c in concept_data]
            if concept_data and isinstance(concept_data[0], dict)
            else concept_data
        )
        print(f"✅ Concepts extracted: {concepts}")
    except Exception as e:
        print(f"❌ Concept extraction failed: {e}")
        concepts = ["Artificial intelligence"] # Fallback

    print("\n--- Testing Quiz Generation ---")
    try:
        fibs = quiz_gen.generate_fill_in_the_blanks(summary, concepts, concepts)
        mcqs = quiz_gen.generate_mcqs(summary, concepts, concepts)
        print(f"✅ Fill-in-the-blanks: {len(fibs)}")
        print(f"✅ MCQs: {len(mcqs)}")
    except Exception as e:
        print(f"❌ Quiz generation failed: {e}")

if __name__ == "__main__":
    test_pipeline()
