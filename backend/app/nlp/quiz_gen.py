import random
from typing import List, Dict, Tuple
import re

class QuizGenerator:
    def __init__(self):
        pass

    def generate_fill_in_the_blanks(self, text: str, concepts: List[str]) -> List[Dict]:
        """
        Generates fill-in-the-blank questions by masking concepts in the text.
        Uses full text (not just summary) for more comprehensive coverage.
        """
        questions = []
        # Split into sentences - handle both newlines and punctuation
        sentences = re.split(r'(?<=[.!?])\s+|(?:\n\n|\n)', text)
        
        for sentence in sentences:
            # Skip very short sentences
            if len(sentence.split()) < 5:
                continue
            for concept in concepts:
                # Case insensitive match for the concept in the sentence
                pattern = re.compile(re.escape(concept), re.IGNORECASE)
                match = pattern.search(sentence)
                if match:
                    question_text = pattern.sub("__________", sentence)
                    questions.append({
                        "type": "fill-in-the-blank",
                        "question": question_text.strip(),
                        "answer": concept
                    })
                    # Don't break - allow multiple concepts per sentence to generate more questions
        
        return questions[:15]  # Generate up to 15 fill-in-the-blank questions

    def generate_mcqs(self, text: str, concepts: List[str], all_concepts: List[str]) -> List[Dict]:
        """
        Generates Multiple Choice Questions from full text.
        """
        questions = []
        sentences = re.split(r'(?<=[.!?])\s+|(?:\n\n|\n)', text)

        for sentence in sentences:
            # Skip very short sentences
            if len(sentence.split()) < 5:
                continue
                
            matched_concepts = []
            for concept in concepts:
                pattern = re.compile(re.escape(concept), re.IGNORECASE)
                if pattern.search(sentence):
                    matched_concepts.append(concept)
            
            # Generate MCQ for each concept found in the sentence
            for matched_concept in matched_concepts:
                # For MCQ, the question is the sentence with the concept masked
                question_text = re.compile(re.escape(matched_concept), re.IGNORECASE).sub("__________", sentence)
                
                # Distractors: Randomly pick from other concepts
                distractors = [c for c in all_concepts if c.lower() != matched_concept.lower()]
                if len(distractors) >= 3:
                    options = random.sample(distractors, 3)
                    options.append(matched_concept)
                    random.shuffle(options)
                    
                    questions.append({
                        "type": "mcq",
                        "question": question_text.strip(),
                        "options": options,
                        "answer": matched_concept
                    })
        
        return questions[:15]  # Generate up to 15 MCQ questions

if __name__ == "__main__":
    # Test
    test_text = """
    Natural Language Processing is a subfield of artificial intelligence that focuses on the interaction between computers and humans. 
    Machine learning is a method of teaching computers to learn from data. Deep learning uses neural networks with many layers.
    Neural networks are computing systems inspired by biological neural networks. Transfer learning allows models to transfer knowledge between tasks.
    Computer vision enables computers to interpret visual information. Speech recognition converts spoken words into text.
    The transformer architecture has revolutionized natural language processing. Attention mechanisms help models focus on relevant information.
    Tokenization breaks text into smaller units. Embeddings represent words as dense vectors. Sentiment analysis determines the emotional tone of text.
    Named entity recognition identifies specific entities in text. Text summarization creates shorter versions of documents.
    Question answering systems can extract answers from large documents. Language models predict the probability of word sequences.
    """
    test_concepts = ["artificial intelligence", "machine learning", "neural networks", "deep learning", "computer vision", 
                    "speech recognition", "transformer", "attention", "tokenization", "embeddings", "sentiment analysis",
                    "named entity recognition", "text summarization", "question answering", "language models"]
    all_concepts = test_concepts
    
    qg = QuizGenerator()
    fibs = qg.generate_fill_in_the_blanks(test_text, test_concepts)
    mcqs = qg.generate_mcqs(test_text, test_concepts, all_concepts)
    
    print(f"Fill-in-the-blanks ({len(fibs)} questions)")
    for q in fibs[:3]:
        print(f"  - {q['question'][:60]}...")
    print(f"\nMCQs ({len(mcqs)} questions)")
    for q in mcqs[:3]:
        print(f"  - {q['question'][:60]}...")
    print(f"\nTotal questions: {len(fibs) + len(mcqs)}")
