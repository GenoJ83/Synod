import re
from typing import List, Dict
from sentence_transformers import util

# Rubric / assignment PDFs — not lecture definitions; blocks bad "context" blobs.
_ASSIGNMENT_OR_SUBMISSION = re.compile(
    r"(?i)\b("
    r"submit|submission|assignment|homework|semester|semi[-\s]?final|rubric|"
    r"please\s+discuss|please\s+note|please\s+make|write\s+one\s+comment|"
    r"per\s+line\s+of\s+code|python\s+file|you\s+must\s+present|"
    r"learning\s+data\s*\(|performance\s+comparison|confusion\s+matrix|"
    r"deep\s+learning\s+challenge|assignment\s+program|task\s*\d|"
    r"challenge\s+input|not\s+necessarily\s+the\s+same\s+as\s+the\s+original"
    r")\b"
)
# Run-on syllabus lines (many tasks jammed together)
_OCR_SYLLABUS_JAM = re.compile(
    r"(?i)(task\s*\d\s+.*task\s*\d|practice\s+1\.|flip,\s*pan,\s*rotate.*zoom)"
)


def _is_assignment_context_blob(s: str) -> bool:
    t = re.sub(r"\s+", " ", (s or "").strip())
    if len(t) < 12:
        return True
    if _ASSIGNMENT_OR_SUBMISSION.search(t):
        return True
    if _OCR_SYLLABUS_JAM.search(t):
        return True
    if len(t) > 420:
        return True
    if len(t.split()) > 55:
        return True
    return False


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
        "data augmentation": "Techniques that artificially expand a training set (e.g. flips, crops, color jitter) so models generalize better without collecting new labeled images.",
        "convolutional neural network": "A neural network that uses convolution layers to scan local patterns in images or sequences, sharing weights across positions.",
        "convolutional network": "A neural network architecture built around convolution layers, commonly used for image and spatial pattern recognition.",
        "vggnet": "A family of deep convolutional networks (e.g. VGG-16/VGG-19) known for stacked 3×3 convolutions and strong image-classification baselines.",
        "vgg": "A deep convolutional architecture (VGG) using repeated small convolutions, often used as a backbone for image classification and transfer learning.",
        "opencv": "An open-source computer-vision library for image and video I/O, transforms, filtering, and real-time processing.",
        "open cv": "An open-source computer-vision library for image and video I/O, transforms, filtering, and real-time processing.",
        "dropout": "A regularization method that randomly drops units during training to reduce co-adaptation and overfitting.",
        "dropblock": "A structured form of dropout that drops contiguous regions of a feature map, often used in convolutional networks.",
        "regularization": "Techniques (weight decay, dropout, data augmentation, etc.) that constrain a model to improve generalization beyond the training set.",
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
                    ranked = scores.argsort()[::-1]
                    for ri in ranked[:12]:
                        if scores[ri] < 0.38:
                            break
                        cand = sentences[int(ri)].strip()
                        if _is_assignment_context_blob(cand):
                            continue
                        specific_context = cand
                        break
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
        concept_clean = re.sub(r"\s+", " ", (concept or "").lower().strip())
        # OCR / spacing variants
        if concept_clean in ("open cv", "open-cv"):
            concept_clean = "opencv"
        if concept_clean.startswith("opencv "):
            concept_clean = "opencv"

        # 1. Try exact match first
        if concept_clean in self.CONCEPT_CATEGORIES:
            return self.CONCEPT_CATEGORIES[concept_clean]

        # 2. Prefix matches only (e.g. "machine learning basics" → "machine learning").
        # Do not use short shared-prefix heuristics: they map unrelated terms (e.g. "data augmentation" → "data structure").
        sorted_keys = sorted(self.CONCEPT_CATEGORIES.keys(), key=len, reverse=True)
        for key in sorted_keys:
            if concept_clean == key:
                return self.CONCEPT_CATEGORIES[key]
            if concept_clean.startswith(key + " ") or key.startswith(concept_clean + " "):
                return self.CONCEPT_CATEGORIES[key]

        return default_msg
    
    def _extract_context(self, text: str, concept: str, max_sentences: int = 2) -> str:
        """Extract relevant context sentences from text."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        concept_pattern = re.compile(re.escape(concept), re.IGNORECASE)

        context_sentences = []
        for sentence in sentences:
            if len(sentence.split()) > 5 and concept_pattern.search(sentence):
                st = sentence.strip()
                if _is_assignment_context_blob(st):
                    continue
                context_sentences.append(st)
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
                        if scores[idx] < 0.34:
                            break
                        if sent in used_contexts:
                            continue
                        if _is_assignment_context_blob(sent):
                            continue

                        # Prefer real sentences over rubric fragments
                        if len(sent.split()) >= 6 and not sent.isupper():
                            best_sent = sent
                            used_contexts.add(sent)
                            break
                except Exception:
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
