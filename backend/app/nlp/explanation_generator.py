import re
from typing import List, Dict
from sentence_transformers import util

class ExplanationGenerator:
    """
    Generates meaningful explanations for concepts based on lecture content.
    Uses context analysis to provide educational explanations.
    """
    
    # Common educational concept categories and their general explanations
    CONCEPT_CATEGORIES = {
        # Technology & AI
        "machine learning": "A method of teaching computers to learn from data without being explicitly programmed, enabling systems to improve performance on tasks through experience.",
        "deep learning": "A subset of machine learning using artificial neural networks with multiple layers to learn representations of data.",
        "neural network": "Computing systems inspired by biological neural networks, consisting of interconnected nodes that process information.",
        "artificial intelligence": "The simulation of human intelligence in machines to perform tasks like reasoning, learning, and problem-solving.",
        "natural language processing": "A field of AI that helps computers understand, interpret, and manipulate human language.",
        "computer vision": "A field of AI that enables computers to interpret and understand visual information from the world.",
        "transformer": "A deep learning architecture that uses self-attention mechanisms to process sequential data.",
        "attention mechanism": "A technique in neural networks that allows models to focus on relevant parts of the input when processing sequences.",
        "tokenization": "The process of breaking text into smaller units like words or subwords for processing.",
        "embeddings": "Dense vector representations of words or concepts that capture semantic relationships.",
        "sentiment analysis": "The process of determining the emotional tone or opinion expressed in text.",
        "named entity recognition": "The task of identifying and classifying entities like names, organizations, and locations in text.",
        "text summarization": "The process of creating a shorter version of a document while preserving key information.",
        "question answering": "AI systems designed to extract or generate answers from given text or knowledge bases.",
        "language model": "A model that predicts the probability of word sequences in language.",
        "speech recognition": "Technology that converts spoken language into written text.",
        "transfer learning": "A technique where a model trained on one task is repurposed for a related task.",
        
        # Data & Programming
        "database": "An organized collection of structured data stored electronically.",
        "algorithm": "A step-by-step procedure for solving a problem or accomplishing a task.",
        "data structure": "A way of organizing and storing data to enable efficient access and modification.",
        "recursion": "A programming technique where a function calls itself to solve smaller instances of a problem.",
        "optimization": "The process of making something as effective as possible, often minimizing or maximizing a function.",
        "classification": "The task of categorizing data into predefined classes or categories.",
        "regression": "A statistical method for modeling relationships between variables.",
        "clustering": "Grouping similar data points together based on their characteristics.",
        "feature engineering": "The process of creating input features for machine learning models.",
        "overfitting": "When a model learns noise in training data rather than general patterns.",
        "underfitting": "When a model is too simple to capture patterns in data.",
        "hyperparameter": "A parameter set before training that controls the learning process.",
        "gradient descent": "An optimization algorithm used to minimize functions by iteratively moving in the steepest descent direction.",
        
        # Software Engineering (Clean Code)
        "clean code": "Clean code is code that is easy to read, understand, and maintain. It follows principles like naming clarity, small functions, and minimal technical debt.",
        "technical debt": "Technical debt is the long-term cost of choosing an easy, quick solution now instead of a better approach that takes longer, eventually making the code harder to change.",
        "maintainability": "The ease with which software can be modified to correct faults, improve performance, or adapt to a changed environment.",
        "refactoring": "The process of restructuring existing computer code without changing its external behavior to improve non-functional attributes.",
        "single responsibility principle": "A computer-programming principle that states that every module, class or function should have responsibility over a single part of the functionality.",
        "dry principle": "Don't Repeat Yourself - a principle of software development aimed at reducing repetition of information of all kinds.",
        "kiss principle": "Keep It Simple, Stupid - a design principle which states that most systems work best if they are kept simple rather than made complicated.",
        "software construction": "The detailed creation of working, meaningful software through a combination of coding, verification, unit testing, and debugging.",
    }
    
    def __init__(self):
        pass
    
    def generate_explanation(self, concept: str, text: str, extractor=None) -> str:
        """
        Generate a specific explanation for a concept based on the lecture content.
        """
        concept_lower = concept.lower()
        
        # 1. Try to find the actual definition/context in the text using the extractor's embeddings
        specific_context = ""
        if extractor and hasattr(extractor, 'model'):
            try:
                sentences = re.split(r'(?<=[.!?])\s+', text)
                if len(sentences) > 3:
                    concept_emb = extractor.model.encode([concept], convert_to_tensor=True)
                    sent_embs = extractor.model.encode(sentences, convert_to_tensor=True)
                    scores = util.cos_sim(concept_emb, sent_embs).cpu().numpy().flatten()
                    top_idx = scores.argmax()
                    # If similarity is high enough, we assume it's a good descriptive sentence
                    if scores[top_idx] > 0.35:
                        specific_context = sentences[top_idx].strip()
            except Exception as e:
                print(f"Semantic context extraction failed: {e}")

        # 2. Get general dictionary-style explanation
        no_def_msg = "Not explicitly defined in the context, but identified as a key term based on its semantic centrality."
        general_explanation = self._get_general_explanation(concept_lower, no_def_msg)
        
        if specific_context:
            # Header heuristic: if it's very short, all uppercase, or starts with metadata prefixes
            is_header = (
                len(specific_context.split()) < 6 or 
                specific_context.isupper() or 
                any(re.search(p, specific_context, re.IGNORECASE) for p in [
                    r"Slide\s+\d+", r"Lecture\s+\d+", r"Topic:", r"Faculty of", 
                    r"Department of", r"Simon Fred", r"Lubambo"
                ])
            )
            
            if is_header and general_explanation != no_def_msg:
                return general_explanation
                
            # If the sentence is short but not a header, try to combine it.
            if len(specific_context.split()) < 12 and general_explanation != no_def_msg:
                return f"{general_explanation} In this context: '{specific_context}'"
            return specific_context
        
        return general_explanation
    
    def _get_general_explanation(self, concept: str, default_msg: str) -> str:
        """Get general explanation from knowledge base with precision and fuzzy normalization."""
        # Normalize: lower, strip
        concept_clean = concept.lower().strip()
        
        # 1. Try exact match first
        if concept_clean in self.CONCEPT_CATEGORIES:
            return self.CONCEPT_CATEGORIES[concept_clean]
            
        # 2. Try prefix/stem matches (e.g. "clean coding" matches "clean code")
        # Sort keys by length descending to get the most specific match
        sorted_keys = sorted(self.CONCEPT_CATEGORIES.keys(), key=len, reverse=True)
        for key in sorted_keys:
            # If the concept starts with the key or the key starts with the concept
            # (e.g. key="machine learning", concept="machine learning basics")
            if concept_clean.startswith(key) or key.startswith(concept_clean):
                return self.CONCEPT_CATEGORIES[key]
            
            # Stemming-lite: check if first 5 chars match for longer words
            if len(key) > 5 and len(concept_clean) > 5:
                if key[:5] == concept_clean[:5]:
                    return self.CONCEPT_CATEGORIES[key]
        
        return default_msg
    
    def _extract_context(self, text: str, concept: str, max_sentences: int = 2) -> str:
        """Extract relevant context sentences from text."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        concept_pattern = re.compile(re.escape(concept), re.IGNORECASE)
        
        context_sentences = []
        for sentence in sentences:
            if len(sentence.split()) > 5 and concept_pattern.search(sentence):
                context_sentences.append(sentence.strip())
                if len(context_sentences) >= max_sentences:
                    break
        
        if context_sentences:
            return " ".join(context_sentences[:2])
        return ""
    
    def generate_all_explanations(self, concepts: List[str], text: str, extractor=None) -> Dict:
        """Generate explanations for all concepts, ensuring contextual uniqueness."""
        explanations = {
            "global": "These foundational concepts are key to understanding the lecture material.",
            "concepts": []
        }
        
        used_contexts = set()
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for concept in concepts:
            # Custom logic to find a UNIQUE context for this concept
            explanation = ""
            best_sent = ""
            
            if extractor and hasattr(extractor, 'model'):
                try:
                    concept_emb = extractor.model.encode([concept], convert_to_tensor=True)
                    sent_embs = extractor.model.encode(sentences, convert_to_tensor=True)
                    scores = util.cos_sim(concept_emb, sent_embs).cpu().numpy().flatten()
                    
                    # Sort sentences by relevance
                    ranked_indices = scores.argsort()[::-1]
                    
                    for idx in ranked_indices:
                        sent = sentences[idx].strip()
                        if scores[idx] < 0.3: break # Threshold
                        if sent in used_contexts: continue
                        
                        # Heuristic check for "good" explanation sentence
                        # Relaxed from 6 to 3 words for short punchy definitions/segments
                        if len(sent.split()) >= 3 and not sent.isupper():
                            best_sent = sent
                            used_contexts.add(sent)
                            break
                except:
                    pass
            
            if best_sent:
                # If we found context, we still want a general definition if possible
                definition = self._get_general_explanation(concept, "Key term from the lecture.")
                contextual_use = best_sent
            else:
                definition = self._get_general_explanation(concept, "Key term identified based on semantic centrality.")
                contextual_use = ""
            
            explanations["concepts"].append({
                "term": concept,
                "definition": definition,
                "context": contextual_use
            })
        
        return explanations


if __name__ == "__main__":
    # Test
    eg = ExplanationGenerator()
    test_text = """
    Natural Language Processing is a subfield of artificial intelligence that focuses on the interaction between computers and humans. 
    Machine learning is a method of teaching computers to learn from data. Deep learning uses neural networks with many layers.
    Neural networks are computing systems inspired by biological neural networks. Transfer learning allows models to transfer knowledge between tasks.
    Computer vision enables computers to interpret visual information. Speech recognition converts spoken words into text.
    The transformer architecture has revolutionized natural language processing. Attention mechanisms help models focus on relevant information.
    Tokenization breaks text into smaller units. Embeddings represent words as dense vectors. Sentiment analysis determines the emotional tone of text.
    """
    concepts = ["machine learning", "neural networks", "transformer", "computer vision"]
    
    explanations = eg.generate_all_explanations(concepts, test_text)
    print("Explanations:")
    for c in explanations["concepts"]:
        print(f"\n{c['term']}:")
        print(f"  Definition: {c['definition'][:150]}...")
        if c['context']:
            print(f"  Context: {c['context']}")
