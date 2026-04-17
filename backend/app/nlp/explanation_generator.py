import re
from typing import List, Dict, Optional, Set
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
    
    # Common educational concept categories and their general explanations - EXPANDED
    CONCEPT_CATEGORIES = {
        # Technology & AI - Enhanced definitions
        "machine learning": "Machine Learning (ML) is a subset of artificial intelligence that enables computers to learn patterns from data without being explicitly programmed. Key types include supervised learning (labeled data for prediction), unsupervised learning (finding hidden patterns), and reinforcement learning (trial-and-error optimization). Common algorithms: decision trees, SVMs, random forests, gradient boosting. Applications: recommendation systems, fraud detection, predictive maintenance, autonomous vehicles.",
        "deep learning": "Deep Learning uses multi-layered neural networks (deep architectures) to automatically learn hierarchical feature representations from raw data. Excels in unstructured data (images, audio, text). Architectures: CNNs (vision), RNNs/LSTMs (sequences), Transformers (language/NLP). Requires GPUs, large datasets. State-of-the-art in computer vision (ImageNet), NLP (GPT/BERT), speech (Whisper). Challenges: interpretability, data requirements, overfitting.",
        "neural network": "Artificial Neural Network (ANN): Computational model inspired by brain neurons. Layers: input, hidden, output. Neurons apply weights, bias, activation (ReLU, sigmoid, tanh). Training: forward pass, loss calculation, backpropagation, gradient descent. Deep networks capture complex hierarchies. Variants: feedforward, convolutional, recurrent. Used in classification, generation, control systems.",
        "artificial intelligence": "AI aims to create intelligent agents performing tasks requiring human intelligence: perception, reasoning, learning, planning, NLP. Branches: symbolic (rules), connectionist (neural nets), statistical (probabilistic), evolutionary. Narrow AI (specific tasks), General AI (human-level), Super AI (surpass human). Ethics: bias mitigation, transparency, job displacement, existential risk.",
        "natural language processing": "NLP enables computers to process human language. Pipeline: tokenization, stemming/lemmatization, POS tagging, NER, parsing, coreference. Tasks: sentiment, summarization, translation, QA, chatbots. Models: word2vec, BERT, GPT, T5. Challenges: ambiguity, context, multilingualism, low-resource languages. Applications: virtual assistants (Siri), search engines, content moderation.",
        "computer vision": "CV gives computers 'sight': image/video understanding. Tasks: classification, detection (YOLO), segmentation (Mask R-CNN), tracking, generation (GANs). Features: edges, textures, objects via CNNs. Applications: medical imaging, autonomous driving, surveillance, AR/VR, defect detection. Datasets: ImageNet, COCO, OpenImages.",
        "transformer": "Transformer (Vaswani 2017): Revolutionized sequence modeling with self-attention (parallelizable, captures long-range dependencies). Encoder-decoder architecture. Positional encodings + multi-head attention + feedforward + layer norm. Models: BERT (bidirectional), GPT (autoregressive), T5 (text-to-text). Powers modern NLP/Speech/Vision.",
        # Add more detailed entries...
        "attention mechanism": "Attention computes weighted sum of input representations based on relevance to current position/query. Softmax over similarity scores. Self-attention: input attends to itself. Multi-head: parallel attention subspaces. Key innovation: fixed context window, no recurrence. Enables Transformers.",
        # Data & Programming
        "database": "Databases store/retrieve structured data efficiently. Relational (SQL: tables, keys, joins, ACID transactions) vs NoSQL (documents, graphs, key-value). Indexing (B-trees), normalization, sharding. SQL: SELECT/JOIN/GROUP BY. ORM: SQLAlchemy. Cloud: RDS, DynamoDB.",
        "algorithm": "Finite sequence of operations solving problem. Analysis: time/space complexity (Big O). Types: search (binary), sort (quicksort O(n log n)), dynamic programming, greedy, divide-conquer. Data structures dictate algorithm choice.",
        # Keep existing ones + add 10 more detailed
        "gradient descent": "Optimization minimizing loss function by iteratively adjusting parameters opposite gradient direction. Variants: batch, stochastic (SGD), mini-batch. Learning rate, momentum, Adam optimizer. Learning rate scheduling, early stopping prevent divergence.",
        "overfitting": "Model memorizes training data noise instead of general patterns. Signs: high train/low test accuracy. Prevention: regularization (L1/L2, dropout), early stopping, data augmentation, cross-validation, ensemble methods.",
        "backpropagation": "Efficient algorithm computing gradients in neural networks via chain rule (reverse-mode autodiff). Forward pass computes predictions/loss, backward pass propagates error derivatives updating weights. Foundation of deep learning training.",
        "loss function": "Quantifies model error. Regression: MSE, MAE. Classification: cross-entropy, hinge. Custom losses for specific tasks. Optimization target in training.",
        "epoch": "One complete pass through entire training dataset. Multiple epochs enable learning. Monitor validation loss to detect overfitting.",
        "batch size": "Number of training examples processed before parameter update. Tradeoff: large (stable gradients, memory), small (noisy but faster convergence). Typical: 32, 64, 128.",
        "validation set": "Subset (20%) for hyperparameter tuning, model selection. Separate from training (learn parameters) and test (final evaluation). K-fold CV for small data.",
        "feature engineering": "Create/transform input features improving model performance. Normalization/scaling, encoding categoricals (one-hot, embeddings), dimensionality reduction (PCA), interaction terms, domain-specific transformations.",
        "cross validation": "Robust performance estimation dividing data k folds, training k-1, validating 1 (rotate). Average performance + std dev. Stratified for imbalanced classes.",
        "activation function": "Introduces non-linearity enabling complex functions. Sigmoid (0-1 logistic), Tanh (-1 to 1), ReLU (max(0,x) fast), Leaky ReLU, Swish. Placement: after linear transformation.",
        "convolutional neural network": "CNNs for grid-structured data (images). Convolution extracts local features (edges→shapes→objects), pooling reduces dimensions, fully-connected classification. Filters/kernels learn hierarchies. Transfer learning (ImageNet pre-trained).",
        "batch normalization": "Normalizes layer inputs (mean 0, std 1) reducing internal covariate shift, accelerating training, regularization effect. Applied before activation.",
        # Original entries preserved
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
        "data structure": "A specialized format for organizing, processing, retrieving and storing data. Common types include arrays, linked lists, stacks, queues, trees (binary, AVL, B-trees), and hash tables. Choice depends on complexity of operations (insertion, deletion, search).",
        "big o notation": "Mathematical notation describing the limiting behavior of a function when the argument tends towards a particular value or infinity. In CS, it's used to classify algorithms according to how their run time or space requirements grow as the input size grows (e.g., O(1) constant, O(log n) logarithmic, O(n) linear, O(n^2) quadratic).",
        "operating system": "Software that manages computer hardware and software resources and provides common services for computer programs. Key functions: process management, memory management, file systems, device I/O, security, and user interface. Examples: Linux, Windows, macOS, Android.",
        "virtual memory": "A memory management technique that provides an idealized abstraction of the storage resources that are actually available on a given machine. It creates the illusion of a larger main memory by using disk space, involving paging, segmentation, and address translation via MMU.",
        "deadlock": "A state in which each member of a group is waiting for another member, including itself, to take action, such as sending a message or more commonly releasing a lock. Four conditions (Coffman): Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait.",
        "rest api": "Representational State Transfer (REST) is an architectural style for providing standards between computer systems on the web. Uses HTTP methods (GET, POST, PUT, DELETE), is stateless, and typically returns JSON or XML.",
        "microservices": "An architectural style that structures an application as a collection of services that are highly maintainable, testable, loosely coupled, independently deployable, and organized around business capabilities.",
        "docker": "A set of platform as a service products that use OS-level virtualization to deliver software in packages called containers. Containers are isolated from one another and bundle their own software, libraries and configuration files.",
        "version control": "A system that records changes to a file or set of files over time so that you can recall specific versions later (e.g., Git). Enables collaboration, branching, merging, and tracking history.",
        "cache": "A hardware or software component that stores data so that future requests for that data can be served faster. Types: L1/L2/L3 CPU cache, web cache (CDN), database cache (Redis/Memcached). Principle: Locality of Reference.",
        "recursion relation": "An equation that recursively defines a sequence or multidimensional array of values. In algorithm analysis, used to express the time complexity of recursive algorithms (e.g., T(n) = 2T(n/2) + O(n) for Merge Sort). Solved via Master Theorem.",
        "cloud computing": "On-demand availability of computer system resources, especially data storage and computing power, without direct active management by the user. Models: IaaS, PaaS, SaaS. Providers: AWS, Google Cloud, Azure.",
        "cybersecurity": "Protection of computer systems and networks from information disclosure, theft of or damage to their hardware, software, or electronic data, as well as from the disruption or misdirection of the services they provide.",
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
                    for ri in ranked[:16]: # Increased scan depth
                        if scores[ri] < 0.35: # Lowered threshold slightly for better coverage
                            break
                        cand = sentences[int(ri)].strip()
                        if _is_assignment_context_blob(cand):
                            continue
                        # Avoid items that are likely just slide titles/names
                        if len(cand.split()) < 7 and (cand.isupper() or ":" in cand):
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

    def generate_concept_detail(
        self,
        concept: str,
        text: str,
        extractor=None,
        *,
        reserved_context_sentences: Optional[Set[str]] = None,
        reserve_chosen: bool = False,
    ) -> Dict:
        """
        Definition + best lecture context for one concept.
        When ``reserve_chosen`` is True, adds the chosen context sentence to ``reserved_context_sentences``
        (for batch generation so each card gets a distinct context line when possible).
        """
        concept = (concept or "").strip()
        if not concept:
            return {"term": "", "definition": "", "context": ""}

        reserved = reserved_context_sentences or set()
        best_sent = ""
        sentences = re.split(r'(?<=[.!?])\s+', text)

        if extractor and hasattr(extractor, "model"):
            try:
                concept_emb = extractor.model.encode([concept], convert_to_tensor=True)
                sent_embs = extractor.model.encode(sentences, convert_to_tensor=True)
                scores = util.cos_sim(concept_emb, sent_embs).cpu().numpy().flatten()
                ranked_indices = scores.argsort()[::-1]

                for idx in ranked_indices:
                    sent = sentences[idx].strip()
                    if scores[idx] < 0.34:
                        break
                    if sent in reserved:
                        continue
                    if _is_assignment_context_blob(sent):
                        continue
                    if len(sent.split()) >= 6 and not sent.isupper():
                        best_sent = sent
                        if reserve_chosen:
                            reserved.add(sent)
                        break
            except Exception:
                pass

        if best_sent:
            definition = self._get_general_explanation(concept, "Key term from the lecture.")
            contextual_use = f"Lecture context: {best_sent}"
        else:
            definition = self._get_general_explanation(
                concept, "Key term identified based on semantic centrality in lecture."
            )
            contextual_use = "No specific lecture example found."

        return {"term": concept, "definition": definition, "context": contextual_use}

    def gather_grounding_snippet(
        self,
        concept: str,
        text: str,
        extractor,
        *,
        max_chars: int = 14000,
        max_sentences: int = 10,
        min_score: float = 0.26,
    ) -> str:
        """
        Concatenate the most relevant lecture sentences for external LLM grounding
        (keeps prompts bounded and reduces hallucination vs. sending the full document).
        """
        concept = (concept or "").strip()
        if not concept or not (text or "").strip():
            return ""

        sentences = re.split(r"(?<=[.!?])\s+", text)
        if not sentences or not extractor or not hasattr(extractor, "model"):
            return (text or "")[:max_chars]

        try:
            concept_emb = extractor.model.encode([concept], convert_to_tensor=True)
            sent_embs = extractor.model.encode(sentences, convert_to_tensor=True)
            scores = util.cos_sim(concept_emb, sent_embs).cpu().numpy().flatten()
            ranked_indices = scores.argsort()[::-1]
        except Exception:
            return (text or "")[:max_chars]

        parts: List[str] = []
        total = 0
        for idx in ranked_indices:
            if len(parts) >= max_sentences:
                break
            if scores[idx] < min_score:
                break
            sent = sentences[int(idx)].strip()
            if _is_assignment_context_blob(sent):
                continue
            if len(sent.split()) < 5:
                continue
            if total + len(sent) + 2 > max_chars:
                break
            parts.append(sent)
            total += len(sent) + 2

        if not parts:
            return (text or "")[:max_chars]
        return "\n\n".join(parts)

    def generate_all_explanations(self, concepts: List[str], text: str, extractor=None) -> Dict:
        """Generate explanations for all concepts, ensuring contextual uniqueness."""
        explanations = {
            "global": "These foundational concepts are key to understanding the lecture material.",
            "concepts": [],
        }

        used_contexts: Set[str] = set()
        for concept in concepts:
            explanations["concepts"].append(
                self.generate_concept_detail(
                    concept,
                    text,
                    extractor,
                    reserved_context_sentences=used_contexts,
                    reserve_chosen=True,
                )
            )

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

