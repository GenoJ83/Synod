import random
from typing import List, Dict, Tuple
import re

class QuizGenerator:
    def __init__(self):
        pass

    def generate_fill_in_the_blanks(self, summary: str, concepts: List[str]) -> List[Dict]:
        """
        Generates fill-in-the-blank questions by masking concepts in the summary.
        """
        questions = []
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', summary)
        
        for sentence in sentences:
            for concept in concepts:
                # Case insensitive match for the concept in the sentence
                pattern = re.compile(re.escape(concept), re.IGNORECASE)
                if pattern.search(sentence):
                    question_text = pattern.sub("__________", sentence)
                    questions.append({
                        "type": "fill-in-the-blank",
                        "question": question_text,
                        "answer": concept
                    })
                    break # One concept per sentence for clarity
        
        return questions[:5] # Limit to 5 questions

    def generate_mcqs(self, summary: str, concepts: List[str], all_concepts: List[str]) -> List[Dict]:
        """
        Generates Multiple Choice Questions.
        """
        questions = []
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', summary)

        for sentence in sentences:
            matched_concept = None
            for concept in concepts:
                pattern = re.compile(re.escape(concept), re.IGNORECASE)
                if pattern.search(sentence):
                    matched_concept = concept
                    break
            
            if matched_concept:
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
                        "question": question_text,
                        "options": options,
                        "answer": matched_concept
                    })
        
        return questions[:5]

if __name__ == "__main__":
    # Test
    test_summary = "Natural Language Processing is a subfield of artificial intelligence. It focuses on the interaction between computers and humans."
    test_concepts = ["artificial intelligence", "computers"]
    all_concepts = ["artificial intelligence", "computers", "neural networks", "robotics", "deep learning", "databases"]
    
    qg = QuizGenerator()
    fibs = qg.generate_fill_in_the_blanks(test_summary, test_concepts)
    mcqs = qg.generate_mcqs(test_summary, test_concepts, all_concepts)
    
    print("FIBs:", fibs)
    print("MCQs:", mcqs)
