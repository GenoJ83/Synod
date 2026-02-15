from app.nlp.summarizer import Summarizer
from app.nlp.extractor import ConceptExtractor
from app.nlp.quiz_gen import QuizGenerator

def run_pipeline(text: str):
    print("\n--- Starting NLP Pipeline ---\n")
    
    # 1. Summarization
    # Note: Using t5-small or similar for faster local testing if possible
    summarizer = Summarizer(model_name="t5-small")
    summary = summarizer.summarize(text)
    print(f"Summary:\n{summary}\n")
    
    # 2. Concept Extraction
    extractor = ConceptExtractor()
    concepts = extractor.extract_concepts(text)
    print(f"Extracted Concepts: {concepts}\n")
    
    # 3. Quiz Generation
    qg = QuizGenerator()
    fibs = qg.generate_fill_in_the_blanks(summary, concepts)
    mcqs = qg.generate_mcqs(summary, concepts, concepts) # Simplified all_concepts for test
    
    print("Generated Quiz Questions:")
    print("Fill-in-the-blanks:")
    for q in fibs:
        print(f"Q: {q['question']}")
        print(f"A: {q['answer']}\n")
        
    print("MCQs:")
    for q in mcqs:
        print(f"Q: {q['question']}")
        print(f"Options: {q['options']}")
        print(f"A: {q['answer']}\n")

if __name__ == "__main__":
    sample_text = """
    Quantum computing is a type of computation whose operations can harness the phenomena of quantum mechanics, 
    such as superposition, interference, and entanglement. Devices that perform quantum computations are known as 
    quantum computers. Though current quantum computers are too small to outperform usual (classical) computers 
    for practical applications, they are believed to be capable of solving certain computational problems, 
    such as integer factorization (which underlies RSA encryption), substantially faster than classical computers.
    """
    run_pipeline(sample_text)
