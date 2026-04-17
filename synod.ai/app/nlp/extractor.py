import os as _os

# Applied at import time (before hub clients are created in typical flows).
_os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")
_os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "60")

try:
    from sentence_transformers import SentenceTransformer, util
    import spacy
    HAS_ML_DEPS = True
except ImportError:
    HAS_ML_DEPS = False

import numpy as np
import re
from collections import Counter
from typing import List, Tuple, Set

# Comprehensive stopwords and generic phrases to filter from concepts
# Rubric / homework PDFs: noun phrases are often instructions, not concepts.
_ASSIGNMENT_LEX = re.compile(
    r"(?i)\b("
    r"submit|submission|assignment|homework|semester|semi[-\s]?final|rubric|"
    r"please\s+discuss|please\s+note|please\s+make|write\s+one\s+comment|"
    r"per\s+line|python\s+file|you\s+must|challenge\s+input|task\s*\d|"
    r"assignment\s+program|performance\s+graph|confusion\s+matrix|"
    r"learning\s+data\s*\(|not\s+necessarily\s+the\s+same"
    r")\b"
)
_CAMERA_UI_PAIR = re.compile(
    r"(?i)^(webcams?|flip|pan|rotate|zoom|shrink|go)\s+(flip|pan|rotate|zoom|webcams?|shrink|go)$"
)
_DUP_TOKEN_TRIPLET = re.compile(r"(?i)\b(\w{3,})\s+\w+\s+\1\b")
_MAX_CONCEPT_WORDS = 5


def _is_low_value_concept_term(term: str) -> bool:
    t = re.sub(r"\s+", " ", (term or "").strip())
    if len(t) < 3:
        return True
    tl = t.lower()
    words = tl.split()
    if len(words) > _MAX_CONCEPT_WORDS:
        return True
    if _ASSIGNMENT_LEX.search(tl):
        return True
    if _CAMERA_UI_PAIR.match(tl):
        return True
    if _DUP_TOKEN_TRIPLET.search(tl):
        return True
    if re.match(r"(?i)^(this|these|those|your|the\s+same)\s+", tl):
        return True
    if re.search(r"(?i)\b(architecture\s+network|your\s+own\s+designed|designed\s+network)\b", tl):
        return True
    if re.search(r"(?i)\b(image\s+processing)\s+task\b", tl):
        return True
    return False


CONCEPT_STOPWORDS = {
    'a', 'an', 'the', 'this', 'that', 'these', 'those',
    'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might',
    'can', 'shall', 'must', 'ought', 'it', 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves',
    'what', 'which', 'who', 'whom', 'whose', 'subset', 'type', 
    'kind', 'sort', 'form', 'part', 'piece', 'portion', 'section', 
    'segment', 'process', 'method', 'way', 'means', 'approach',
    'example', 'instance', 'case', 'sample', 'thing', 'object', 
    'item', 'element', 'component', 'aspect', 'feature', 
    'characteristic', 'quality', 'fact', 'detail', 'point', 
    'idea', 'concept', 'result', 'outcome', 'effect', 'consequence',
    'purpose', 'goal', 'aim', 'objective', 'target', 'reason', 
    'cause', 'factor', 'source', 'origin', 'use', 'usage', 
    'application', 'function', 'role', 'importance', 'significance', 
    'value', 'worth', 'problem', 'issue', 'matter', 'question', 
    'topic', 'subject', 'theme', 'area', 'field', 'domain',
    'context', 'background', 'setting', 'environment', 'condition', 
    'situation', 'circumstance', 'state', 'change', 'variation', 
    'difference', 'distinction', 'relationship', 'connection', 
    'link', 'tie', 'bond', 'structure', 'organization', 
    'arrangement', 'order', 'system', 'network', 'framework', 
    'model', 'pattern', 'development', 'growth', 'progress', 
    'advancement'
}

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
                try:
                    self.model = SentenceTransformer(
                        model_name, device=self.device, local_files_only=True
                    )
                    print("Loaded embedding model from local Hugging Face cache.")
                except Exception:
                    print(
                        "Local cache miss — downloading embedding model "
                        f"(timeout HF_HUB_DOWNLOAD_TIMEOUT={_os.environ.get('HF_HUB_DOWNLOAD_TIMEOUT', '?')}s)..."
                    )
                    self.model = SentenceTransformer(model_name, device=self.device)
                
                # Precision optimization (Disabled half() due to stability issues on some MPS versions)
                # if self.device in ["cuda", "mps"]:
                #     self.model = self.model.half()
                
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

    def extract_concepts(self, text: str, top_n: int = 10) -> List[dict]:
        """
        Extracts key concepts (noun phrases) and ranks them using centrality.
        """
        if not self.has_deps:
            # Mock concepts: very simple keyword extraction using split and frequency
            words = text.lower().split()
            unique_words = list(set([w for w in words if len(w) > 5]))
            return unique_words[:top_n]

        doc = self.nlp(text)
        
        # Candidate selection: Noun phrases AND Named Entities
        candidates = set()
        
        # 1. Noun phrases
        for chunk in doc.noun_chunks:
            clean_chunk = chunk.text.strip().lower()
            if len(clean_chunk) > 3 and not chunk.root.is_stop:
                candidates.add(clean_chunk)
        
        # 2. Named Entities (specific technical/formal terms)
        for ent in doc.ents:
            # Skip PERSON - lectures are usually about topics, not the professor's name
            if ent.label_ in ["PRODUCT", "ORG", "WORK_OF_ART", "EVENT"]:
                candidates.add(ent.text.strip().lower())
        
        # 3. Metadata Filter: remove anything that looks like university/department/author metadata
        metadata_patterns = [
            re.compile(r"(?:University|Institute|Department|Laboratory|School|College|Academy|Faculty of)", re.IGNORECASE),
            re.compile(r"DSC\d{4}:?", re.IGNORECASE),
            re.compile(r"Lecture\s+\d+", re.IGNORECASE),
            re.compile(r"Topic:\s+", re.IGNORECASE),
            re.compile(r"Simon\s+Fred", re.IGNORECASE)
        ]
        
        filtered_candidates = set()
        for cand in candidates:
            if any(p.search(cand) for p in metadata_patterns):
                continue
            if _is_low_value_concept_term(cand):
                continue
            filtered_candidates.add(cand)
        
        if not filtered_candidates:
            return []

        candidate_list = list(filtered_candidates)
        
        # Compute embeddings for candidates
        candidate_embeddings = self.model.encode(candidate_list, convert_to_tensor=True)
        
        # Compute document embedding as the mean of candidate embeddings (or of the whole text)
        doc_embedding = self.model.encode([text], convert_to_tensor=True)
        
        # Rank by cosine similarity to the document context
        cos_scores = util.cos_sim(candidate_embeddings, doc_embedding).cpu().numpy().flatten()
        
        # Post-processing quality filters
        threshold = 0.3
        ranked_indices = np.argsort(cos_scores)[::-1]
        
        concepts = []
        for i in ranked_indices:
            term = candidate_list[i]
            relevance = float(cos_scores[i])
            
            # Filter by relevance threshold
            if relevance < threshold and len(concepts) >= 5:
                continue
                
            # Filter generic terms and short fragments
            words = term.split()
            if any(w in CONCEPT_STOPWORDS for w in words) and len(words) == 1:
                continue
            if len(term) < 3:
                continue
            
            # --- Concept Merging Logic ---
            # If a very similar term already exists, only keep the more relevant one
            is_duplicate = False
            if concepts:
                # Compare new candidate with existing kept concepts
                current_emb = candidate_embeddings[i].reshape(1, -1)
                existing_terms = [c["term"] for c in concepts]
                existing_embs = self.model.encode(existing_terms, convert_to_tensor=True)
                
                sims = util.cos_sim(current_emb, existing_embs).cpu().numpy().flatten()
                if np.max(sims) > 0.85:
                    is_duplicate = True
            
            if not is_duplicate:
                concepts.append({"term": term, "relevance": round(relevance, 3)})
            
            if len(concepts) >= top_n:
                break
                
        return concepts

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
