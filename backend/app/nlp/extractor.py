try:
    from sentence_transformers import SentenceTransformer, util
    import spacy
    HAS_ML_DEPS = True
except ImportError:
    HAS_ML_DEPS = False

import numpy as np
from collections import Counter
from typing import List, Tuple

class ConceptExtractor:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initializes S-BERT and Spacy for text processing.
        """
        self.has_deps = HAS_ML_DEPS
        if HAS_ML_DEPS:
            try:
                # Device detection: CUDA -> MPS -> CPU
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self.device = "mps"
                else:
                    self.device = "cpu"
                
                print(f"Loading embedding model: {model_name} on {self.device}...")
                self.model = SentenceTransformer(model_name, device=self.device)
                
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    print("Downloading spacy model...")
                    import os
                    os.system("python -m spacy download en_core_web_sm")
                    self.nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                print(f"Error initializing extractor: {e}. Falling back to MOCK mode.")
                self.has_deps = False
        else:
            print("ML dependencies not found. Running in MOCK mode.")
            self.model = None
            self.nlp = None

    def extract_concepts(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extracts key concepts (noun phrases) and ranks them using centrality.
        """
        if not self.has_deps:
            # Mock concepts: very simple keyword extraction using split and frequency
            words = text.lower().split()
            unique_words = list(set([w for w in words if len(w) > 5]))
            return unique_words[:top_n]

        doc = self.nlp(text)
        
        # Candidate selection: Noun phrases and proper nouns
        candidates = set()
        for chunk in doc.noun_chunks:
            # Clean and filter candidates
            clean_chunk = chunk.text.strip().lower()
            if len(clean_chunk) > 3 and not chunk.root.is_stop:
                candidates.add(clean_chunk)
        
        if not candidates:
            return []

        candidate_list = list(candidates)
        
        # Compute embeddings for candidates
        candidate_embeddings = self.model.encode(candidate_list, convert_to_tensor=True)
        
        # Compute document embedding as the mean of candidate embeddings (or of the whole text)
        doc_embedding = self.model.encode([text], convert_to_tensor=True)
        
        # Rank by cosine similarity to the document context
        cos_scores = util.cos_sim(candidate_embeddings, doc_embedding).cpu().numpy().flatten()
        
        # Quality filter: Only keep candidates with similarity > threshold
        threshold = 0.3
        valid_indices = [i for i, score in enumerate(cos_scores) if score > threshold]
        
        if not valid_indices:
            # Fallback if everything is below threshold
            ranked_indices = np.argsort(cos_scores)[::-1]
        else:
            ranked_indices = [i for i in np.argsort(cos_scores)[::-1] if i in valid_indices]
        
        return [candidate_list[i] for i in ranked_indices[:top_n]]

    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        Simpler keyword extraction based on POS tagging.
        """
        doc = self.nlp(text)
        words = [token.text.lower() for token in doc if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop]
        return [w for w, _ in Counter(words).most_common(top_n)]

if __name__ == "__main__":
    test_text = """
    Deep learning is part of a broader family of machine learning methods based on artificial neural networks 
    with representation learning. Learning can be supervised, semi-supervised or unsupervised. 
    Deep-learning architectures such as deep neural networks, deep belief networks, deep reinforcement learning, 
    recurrent neural networks and convolutional neural networks have been applied to fields including computer vision, 
    speech recognition, natural language processing, machine translation, bioinformatics, drug design, 
    medical image analysis, climate science, material inspection and board game programs, 
    where they have produced results comparable to and in some cases surpassing human expert performance.
    """
    extractor = ConceptExtractor()
    concepts = extractor.extract_concepts(test_text)
    print(f"Top Concepts: {concepts}")
