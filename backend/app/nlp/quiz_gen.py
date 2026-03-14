import random
from typing import List, Dict, Tuple
import re
import spacy

class QuizGenerator:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            # Fallback if model not downloaded
            self.nlp = None

    def generate_fill_in_the_blanks(self, text: str, concepts: List[str]) -> List[Dict]:
        """
        Generates fill-in-the-blank questions by masking concepts in the text.
        """
        questions: List[Dict] = []
        sentences = re.split(r'(?<=[.!?])\s+|(?:\n\n|\n)', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not self._is_sentence_specific(sentence, concepts):
                continue
            
            for concept in concepts:
                pattern = re.compile(re.escape(concept), re.IGNORECASE)
                match = pattern.search(sentence)
                if match:
                    question_text = pattern.sub("__________", sentence)
                    questions.append({
                        "type": "fill-in-the-blank",
                        "question": question_text.strip(),
                        "answer": concept
                    })
        
        return questions[:8]

    def generate_mcqs(self, text: str, concepts: List[str], all_concepts: List[str], extractor=None) -> List[Dict]:
        """Standard MCQ - mask a word in sentence with semantically relevant distractors"""
        questions: List[Dict] = []
        sentences = re.split(r'(?<=[.!?])\s+|(?:\n\n|\n)', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not self._is_sentence_specific(sentence, concepts):
                continue
                
            matched_concepts = []
            for concept in concepts:
                pattern = re.compile(re.escape(concept), re.IGNORECASE)
                if pattern.search(sentence):
                    matched_concepts.append(concept)
            
            for matched_concept in matched_concepts:
                question_text = re.compile(re.escape(matched_concept), re.IGNORECASE).sub("__________", sentence)
                
                # Semantic Distractor Selection
                distractors = []
                other_candidates = [c for c in all_concepts if c.lower() != matched_concept.lower()]
                
                if extractor and extractor.has_deps and len(other_candidates) > 3:
                    try:
                        # Find distractors semantically similar to the answer
                        from sentence_transformers import util
                        ans_emb = extractor.model.encode([matched_concept], convert_to_tensor=True)
                        cand_embs = extractor.model.encode(other_candidates, convert_to_tensor=True)
                        scores = util.cos_sim(ans_emb, cand_embs).cpu().numpy().flatten()
                        # Pick top 5 most similar but not identical
                        top_indices = scores.argsort()[-5:][::-1]
                        distractors = [other_candidates[i] for i in top_indices if other_candidates[i].lower() not in matched_concept.lower() and matched_concept.lower() not in other_candidates[i].lower()]
                    except:
                        distractors = random.sample(other_candidates, min(len(other_candidates), 3))
                else:
                    distractors = random.sample(other_candidates, min(len(other_candidates), 3))

                if len(distractors) >= 2:
                    options = distractors[:3]
                    options.append(matched_concept)
                    random.shuffle(options)
                    
                    questions.append({
                        "type": "mcq",
                        "question": question_text.strip(),
                        "options": options,
                        "answer": matched_concept
                    })
        
        return questions[:8]

    def generate_true_false(self, text: str, concepts: List[str]) -> List[Dict]:
        """
        Generates True/False questions about the lecture content.
        Tests comprehension by presenting statements about the content.
        """
        questions: List[Dict] = []
        sentences = re.split(r'(?<=[.!?])\s+|(?:\n\n|\n)', text)
        
        # Create statements from sentences - some true, some modified (false)
        true_statements = []
        false_statements = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not self._is_sentence_specific(sentence, concepts):
                continue
            
            # This is a true statement from the text
            true_statements.append(sentence.strip())
            
            # Create a false statement by negating or changing key parts
            false_statement = self._create_false_statement(sentence, concepts)
            if false_statement:
                false_statements.append(false_statement)
        
        # Generate true questions
        for statement in true_statements[:5]:
            # Convert statement to question
            question = self._statement_to_question(statement)
            if question and len(question) > 20:
                questions.append({
                    "type": "true_false",
                    "question": question,
                    "correct": True,
                    "explanation": statement[:100] + "..." if len(statement) > 100 else statement
                })
        
        # Generate false questions
        for statement in false_statements[:5]:
            question = self._statement_to_question(statement)
            if question and len(question) > 20:
                questions.append({
                    "type": "true_false",
                    "question": question,
                    "correct": False,
                    "explanation": "This statement is not accurate according to the lecture."
                })
        
        random.shuffle(questions)
        return questions[:8]

    def generate_comprehension(self, text: str, concepts: List[str]) -> List[Dict]:
        """
        Generates comprehension questions that test understanding of concepts and relationships.
        """
        questions: List[Dict] = []
        sentences = re.split(r'(?<=[.!?])\s+|(?:\n\n|\n)', text)
        
        # Find sentences that describe relationships or processes
        process_keywords = ['because', 'therefore', 'however', 'although', 'means', 'enables', 
                           'allows', 'helps', 'results', 'leads to', 'used for', 'involves',
                           'depends on', 'consists of', 'includes', 'requires']
        
        cause_effect_pairs = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence describes a cause-effect or relationship
            for keyword in process_keywords:
                if keyword in sentence_lower and self._is_sentence_specific(sentence, concepts):
                    # Extract main concepts from sentence
                    sentence_concepts = [c for c in concepts if c.lower() in sentence_lower]
                    if sentence_concepts:
                        cause_effect_pairs.append({
                            'sentence': sentence.strip(),
                            'concepts': sentence_concepts,
                            'keyword': keyword
                        })
                    break
        
        # Generate cause-effect questions
        for pair in cause_effect_pairs[:4]:
            sentence = pair['sentence']
            main_concept = pair['concepts'][0]
            
            # What/How question
            questions.append({
                "type": "comprehension",
                "question": f"According to the lecture, how does {main_concept} work?",
                "options": [
                    sentence[:100] + "..." if len(sentence) > 100 else sentence,
                    "It is not discussed in the lecture",
                    "It works in multiple unrelated ways",
                    "It has no significant role"
                ],
                "answer": 0,
                "explanation": sentence[:150] + "..." if len(sentence) > 150 else sentence
            })
            
            # Why question  
            if len(pair['concepts']) > 1:
                related = pair['concepts'][1]
                questions.append({
                    "type": "comprehension",
                    "question": f"What is the relationship between {main_concept} and {related}?",
                    "options": [
                        f"They are discussed together in the context of: {sentence[:80]}...",
                        "They are completely unrelated",
                        "One is a replacement for the other",
                        "They are competing technologies"
                    ],
                    "answer": 0,
                    "explanation": f"The lecture mentions both in relation to each other."
                })
        
        # Generate concept application questions
        for concept in concepts[:5]:
            questions.append({
                "type": "comprehension",
                "question": f"What is the main purpose of {concept}?",
                "options": [
                    "To process and analyze information",  # Generic correct-ish
                    "To store data permanently",
                    "To connect to the internet",
                    "To display visual content"
                ],
                "answer": 0,
                "explanation": f"{concept} is used for processing information as discussed in the lecture."
            })
        
        random.shuffle(questions)
        return questions[:8]

    def _create_false_statement(self, sentence: str, concepts: List[str]) -> str:
        """Create a semantically plausible false version of a statement."""
        if self.nlp:
            doc = self.nlp(sentence)
            # Find the root verb or auxiliary to negate
            for token in doc:
                if (token.pos_ == "VERB" or token.pos_ == "AUX") and token.dep_ == "ROOT":
                    # Simple negation: "is" -> "is not", "contains" -> "does not contain"
                    if token.lemma_ == "be":
                        # Find the next token to insert 'not' after
                        idx = token.idx + len(token.text)
                        return sentence[:idx] + " not" + sentence[idx:]
                    else:
                        # For other verbs, use a simple heuristic for now
                        neg = "does not " if token.tag_ == "VBZ" else "did not " if token.tag_ == "VBD" else "do not "
                        return sentence[:token.idx] + neg + token.lemma_ + sentence[token.idx + len(token.text):]
        
        # Fallback to simple negation if spaCy is missing or fails
        words = sentence.split()
        if len(words) > 3:
            insert_pos = len(words) // 2
            return " ".join(words[:insert_pos]) + " not " + " ".join(words[insert_pos:])

        return ""

    def _is_sentence_specific(self, sentence: str, concepts: List[str]) -> bool:
        """
        Heuristic to determine if a sentence is high-quality enough for a quiz question.
        Rejects sentences that start with vague pronouns, bullet points, or lack enough context.
        """
        # Strip common slide bullet characters
        bullets = "❑●•*-◦▪"
        sentence = sentence.lstrip(bullets).strip()
        
        words = sentence.split()
        if len(words) < 7:
            return False
            
        # 1. Reject sentences ending with colons (likely headers)
        if sentence.endswith(":"):
            return False

        # 2. Reject sentences starting with generic pronouns (likely lacking context)
        first_word = words[0].lower().strip(".,!?;:\"'")
        vague_pronouns = {"it", "they", "this", "these", "those", "that", "he", "she"}
        if first_word in vague_pronouns:
            # Only allow if the sentence contains at least 2 other key concepts to provide context
            concept_count = self._count_unique_concepts(sentence, concepts)
            if concept_count < 2:
                return False
        
        # 3. Reject objective headers and action-verb fragments (Bloom's Taxonomy)
        # These are common in slides but poor for factual quiz questions
        objective_patterns = ["should be able to", "learning outcomes", "lecture objectives", "learning objectives", "by the end of"]
        if any(pat in sentence.lower() for pat in objective_patterns):
            return False
            
        # Reject sentences starting with imperative/objective verbs
        objective_verbs = {"understand", "learn", "know", "discuss", "explain", "describe", "identify", "analyze", "evaluate", "synthesize", "apply"}
        if first_word in objective_verbs:
            return False

        # 4. Reject very short sentences that are likely just bridge phrases
        if len(words) < 10 and self._count_unique_concepts(sentence, concepts) < 1:
            return False
            
        return True

    def _count_unique_concepts(self, sentence: str, concepts: List[str]) -> int:
        """Count how many unique concepts from the list appear in the sentence."""
        sentence_lower = sentence.lower()
        count = 0
        for concept in concepts:
            if concept.lower() in sentence_lower:
                count += 1
        return count

    def _statement_to_question(self, statement: str) -> str:
        """Convert a statement to a clean TRUE/FALSE assertion format."""
        statement = statement.strip()
        if not statement:
            return ""
        
        # Remove leading conjunctions or interrogative starts that make poor T/F questions
        # This handles cases like "Why deep convolutional neural network is useful?" -> "Deep convolutional neural network is useful."
        bad_starts = ('however', 'therefore', 'additionally', 'furthermore', 'why', 'how', 'when', 'what', 'which')
        words = statement.split()
        if words and words[0].lower().strip(".,!?;:\"'") in bad_starts:
            if len(words) > 1:
                # If first word is why/how/what, strip it and try to fix the remaining sentence
                statement = " ".join(words[1:])
        
        # Capitalize and ensure it ends with a period for a T/F assertion
        statement = statement.strip()
        if not statement:
            return ""
            
        statement = statement[0].upper() + statement[1:]
        
        if statement.endswith('?'):
            statement = statement[:-1] + '.'
        elif not statement.endswith('.'):
            statement = statement + '.'
            
        return statement


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
    tf = qg.generate_true_false(test_text, test_concepts)
    comp = qg.generate_comprehension(test_text, test_concepts)
    
    print(f"Fill-in-the-blanks ({len(fibs)} questions)")
    print(f"MCQs ({len(mcqs)} questions)")
    print(f"True/False ({len(tf)} questions)")
    print(f"Comprehension ({len(comp)} questions)")
    print(f"\nTotal questions: {len(fibs) + len(mcqs) + len(tf) + len(comp)}")
