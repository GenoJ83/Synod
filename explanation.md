# Text Generation System Explanation - Synod Application

This document provides a comprehensive explanation of how the text generation system works in the Synod application. The system processes educational content such as lecture notes, presentations, research papers and generates summaries, extracts key concepts, creates quizzes, and provides explanations.

## Architecture Overview

The text generation system consists of several interconnected components that work together to transform raw text into structured educational content:

```
User Input (Text/File)
       ↓
┌─────────────────────────────┐
│   File Extraction Service   │  → Extracts text from PDF/PPTX/TXT
└─────────────────────────────┘
       ↓
┌─────────────────────────────┐
│      Text Sanitization      │  → Cleans and normalizes text
└─────────────────────────────┘
       ↓
┌─────────────────────────────┐
│   NLP Pipeline (Main.py)    │  → Orchestrates all model interactions
└─────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────────────┐
│  1. Summarizer         2. Concept Extractor    3. Quiz Generator   │
│     - Transformer         - SBERT                 - FIB            │
│     - Two-pass approach   - spaCy                - MCQ             │
│                          - Cosine similarity    - True/False      │
│                                                 - Comprehension    │
└─────────────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────┐
│   Explanation Generator     │  → Context + Knowledge base
└─────────────────────────────┘
       ↓
    Final Output
```

## Component Details

### 1. File Extraction Service (`backend/app/ingestion/extractor_service.py`)

The entry point for processing uploaded files. This service handles multiple file formats and performs initial text cleaning.

**Supported File Types:**
- PDF (`.pdf`) - Uses PyMuPDF (fitz)
- PowerPoint (`.pptx`) - Uses python-pptx
- Text files (`.txt`) - Direct text reading

**Processing Steps:**

```
File → Extract Text → Strip Headers → Sanitize → Clean Academic Noise → Clean Text
```

1. **Text Extraction**: Reads raw text from the file
2. **Header Stripping**: Removes metadata (author names, affiliations, course codes, lecture topics)
3. **Sanitization**: 
   - Truncates at References/Bibliography sections
   - Fixes hyphenated line-breaks
   - Removes URLs
   - Filters repeating headers/footers
4. **Academic Noise Removal** (PDF-specific):
   - Removes arXiv citation lines
   - Filters figure captions and table noise
   - Removes QA prompt templates from appendices

---

### 2. Summarizer (`backend/app/nlp/summarizer.py`)

Generates concise summaries from long-form educational content using transformer-based sequence-to-sequence models.

**Model Used:** `sshleifer/distilbart-cnn-12-6` (default)
- A distilled version of BART for summarization
- Optimized for news-style summarization but works well with educational content

**How the Summarization Model Works:**

The DistilBART model is a sequence-to-sequence transformer that works in two main phases:

1. **Encoding Phase:**
   - The input text is tokenized (converted to numerical tokens)
   - The encoder processes the entire input and creates contextual representations of each word
   - It understands the relationships between all words in the document

2. **Decoding Phase:**
   - The decoder generates output tokens one at a time
   - Each new token is generated based on:
     - The encoded input (what the text is about)
     - Previously generated tokens (building the summary progressively)
   - Uses beam search: considers multiple possible next tokens and picks the best sequence

The "distilled" version means it was trained to mimic a larger model but with fewer parameters, making it faster while retaining most of the quality.

**Processing Flow:**

```
Input Text → Check Cache → Dynamic Length Calculation → Chunking (if long) → Model Inference → Post-processing → Output
```

**Key Features:**

1. **Dynamic Length Calculation:**
   - Targets 20-30% of original document size
   - Max length: 1500 words for deep context
   - Min length: 80-250 words depending on input

2. **Two-Pass Approach for Long Documents:**
   - **First Pass**: Splits text into 400-word chunks, generates separate summaries for each
   - **Second Pass (Synthesis)**: Combines chunk summaries into a coherent final summary
   - Uses beam search with higher length_penalty (2.5) for better fluency

3. **Device Optimization:**
   ```python
   if torch.cuda.is_available():     # GPU (NVIDIA)
       device = "cuda"
       model = model.half()           # FP16 precision
   elif torch.backends.mps.is_available():  # Apple Silicon
       device = "mps"
   else:                             # CPU
       device = "cpu"
       model = torch.quantization.quantize_dynamic(model, ...)  # INT8 quantization
   ```

4. **Post-Processing:**
   - Fixes tokenization artifacts (e.g., "pro-pose" → "propose")
   - Removes repetition loops
   - Filters redundant sentences

5. **Takeaway Generation:**
   - Divides text into segments
   - Generates short bullet points for each segment
   - Filters for uniqueness

---

### 3. Concept Extractor (`backend/app/nlp/extractor.py`)

Extracts key educational concepts from text using semantic similarity and NLP techniques.

**Models Used:**
- **Embedding Model**: `all-MiniLM-L6-v2` (Sentence-BERT)
- **NLP Model**: spaCy `en_core_web_sm`

**How Sentence-BERT Works:**

Sentence-BERT is a sentence embedding model that converts sentences into dense numerical vectors (embeddings). Here's how it works:

1. **Architecture:**
   - Based on BERT (Bidirectional Encoder Representations from Transformers)
   - Uses a siamese network structure: two identical BERT encoders share weights
   - One encoder processes the sentence, another processes a comparison sentence

2. **Training Process:**
   - Trained on large datasets of sentence pairs
   - Learns to minimize the distance between similar sentences
   - Maximizes distance between dissimilar sentences
   - Produces 384-dimensional embeddings (vectors of 384 numbers)

3. **Semantic Similarity Calculation:**
   - Both the concept and all sentences are converted to embeddings
   - Cosine similarity measures how similar the directions of two vectors are
   - Score of 1.0 = identical meaning, 0.0 = completely different
   - Higher scores indicate the sentence is more relevant to the concept

4. **Advantages over Word Embeddings:**
   - Understands context: "bank" (river) vs "bank" (financial) get different embeddings
   - Works at sentence level, not just word level
   - Captures semantic meaning, not just word frequency

**How spaCy Works:**

spaCy is an industrial-strength NLP library that provides:

1. **Tokenization:** Breaks text into words, punctuation, and spaces
2. **Part-of-Speech Tagging:** Identifies nouns, verbs, adjectives, etc.
3. **Named Entity Recognition:** Identifies proper names, organizations, locations
4. **Dependency Parsing:** Analyzes grammatical structure (subject, object, etc.)
5. **Noun Chunking:** Groups nouns with their modifying words

**Processing Flow:**

```
Input Text → spaCy Processing → Candidate Selection → Filtering → Embedding → Similarity Ranking → Output
```

**Step-by-Step Process:**

1. **NLP Processing (spaCy):**
   - Part-of-speech tagging
   - Named entity recognition
   - Dependency parsing

2. **Candidate Selection:**
   ```python
   # Noun phrases from text chunks
   for chunk in doc.noun_chunks:
       candidates.add(chunk.text.lower())
   
   # Named entities (PRODUCT, ORG, WORK_OF_ART, EVENT)
   for ent in doc.ents:
       if ent.label_ in ["PRODUCT", "ORG", ...]:
           candidates.add(ent.text.lower())
   ```

3. **Filtering:**
   - Removes metadata patterns (university, department, lecture numbers)
   - Filters generic terms using stopword list
   - Removes short fragments (< 3 characters)

4. **Embedding & Ranking:**
   ```python
   # Generate embeddings for all candidates
   candidate_embeddings = model.encode(candidates)
   
   # Generate document embedding (mean of candidates)
   doc_embedding = model.encode([text])
   
   # Cosine similarity ranking
   cos_scores = util.cos_sim(candidate_embeddings, doc_embedding)
   
   # Filter by relevance threshold (0.3)
   # Remove duplicate/similar concepts (> 0.85 similarity)
   ```

---

### 4. Quiz Generator (`backend/app/nlp/quiz_gen.py`)

Generates multiple types of quiz questions from the input text and extracted concepts.

**Question Types:**

#### 4.1 Fill-in-the-Blank Questions
```
Process:
1. Split text into sentences
2. Filter sentences containing concepts
3. Mask concept in sentence with "__________"
4. Return question with answer

Example:
Input: "Machine learning is a subset of artificial intelligence."
Concept: "machine learning"
Output: "__________ is a subset of artificial intelligence."
Answer: "Machine learning"
```

#### 4.2 Multiple Choice Questions
```
Process:
1. Select sentence with concept
2. Generate incorrect options (distractors) using semantic similarity
3. Shuffle options

Distractor Selection (Semantic):
- If extractor available:
  1. Get embedding of correct answer
  2. Get embeddings of all other concepts
  3. Calculate cosine similarities
  4. Pick top 3 most similar (but not identical)
- Else: Random sampling

Example:
Question: "__________ enables computers to understand human language."
Options: ["Natural Language Processing", "Computer Vision", "Machine Learning", "Neural Networks"]
Answer: "Natural Language Processing"
```

#### 4.3 True/False Questions
```
Process:
1. Extract concept-containing sentences (True)
2. Create false statements:
   - Add negation (not, never, cannot)
   - Swap concepts
3. Convert statements to questions
4. Shuffle and mix True/False

Example:
True: "Deep learning uses neural networks with multiple layers."
False: "Deep learning does not use neural networks."
```

#### 4.4 Comprehension Questions
```
Process:
1. Find relationship sentences (cause-effect keywords)
2. Generate "How does X work?" questions
3. Generate "What is the relationship between X and Y?" questions

Keywords Used:
['because', 'therefore', 'however', 'means', 'enables', 
 'allows', 'helps', 'results', 'used for', 'involves']
```

---

### 5. Explanation Generator (`backend/app/nlp/explanation_generator.py`)

Generates educational explanations for extracted concepts using context and a knowledge base.

**How It Works - Two-Source Approach:**

1. **Context Extraction (Primary Method):**
   
   Uses semantic similarity to find the most relevant sentence in the text that describes the concept:
   
   ```python
   # Semantic search for relevant sentences
   concept_emb = model.encode([concept])
   sent_embs = model.encode(sentences)
   scores = util.cos_sim(concept_emb, sent_embs)
   
   # Pick highest scoring sentence above threshold (0.35)
   best_sentence = sentences[scores.argmax()]
   ```
   
   This works by:
   - Converting the concept name into a numerical embedding (vector)
   - Converting every sentence in the document into embeddings
   - Comparing the concept embedding with each sentence embedding using cosine similarity
   - Selecting the sentence with the highest similarity score that also exceeds a minimum threshold

2. **Knowledge Base (Fallback Method):**
   
   When no good context is found in the text, the system falls back to a pre-defined dictionary containing ~40 common technical terms organized into categories:
   
   - **Artificial Intelligence & Machine Learning:** machine learning, deep learning, neural networks, natural language processing, computer vision, transformer, attention mechanism, tokenization, embeddings, sentiment analysis, named entity recognition, text summarization, question answering, language model, speech recognition, transfer learning
   
   - **Data & Programming:** database, algorithm, data structure, recursion, optimization, classification, regression, clustering, feature engineering, overfitting, underfitting, hyperparameter, gradient descent
   
   - **Software Engineering:** clean code, technical debt, maintainability, refactoring, single responsibility principle, DRY principle, KISS principle, software construction

   The system uses fuzzy matching to handle variations (e.g., "machine learning basics" matches "machine learning").

**Output Structure:**
```python
{
    "global": "These foundational concepts are key to understanding...",
    "concepts": [
        {
            "term": "machine learning",
            "definition": "A method of teaching computers to learn...",
            "context": "Machine learning is a subset of artificial intelligence..."
        },
        ...
    ]
}
```

---

## Complete Processing Pipeline

The main orchestration happens in `backend/main.py`:

```python
def process_logic(text: str):
    # Step 1: Summarization
    sum_result = summarizer.summarize(text)
    summary = sum_result.get("summary", "")
    takeaways = sum_result.get("takeaways", [])
    
    # Step 2: Concept Extraction
    concept_data = extractor.extract_concepts(text)
    concepts = [c["term"] for c in concept_data]
    
    # Step 3: Quiz Generation (uses full text + concepts)
    fibs = quiz_gen.generate_fill_in_the_blanks(text, concepts)
    mcqs = quiz_gen.generate_mcqs(text, concepts, concepts, extractor=extractor)
    true_false = quiz_gen.generate_true_false(text, concepts)
    comprehension = quiz_gen.generate_comprehension(text, concepts)
    
    # Step 4: Explanation Generation
    explanations = explanation_gen.generate_all_explanations(concepts, text, extractor=extractor)
    
    return {
        "summary": summary,
        "concepts": concepts,
        "concept_details": concept_data,
        "takeaways": takeaways,
        "quiz": {
            "fill_in_the_blanks": fibs,
            "mcqs": mcqs,
            "true_false": true_false,
            "comprehension": comprehension
        },
        "explanations": explanations,
        "metrics": metrics
    }
```

---

## Model Interactions Summary

| Component | Model/Library | Purpose | Output |
|-----------|---------------|---------|--------|
| **ExtractorService** | PyMuPDF (fitz), python-pptx | Extracts text from PDF, PowerPoint, and text files | Raw text with headers stripped and cleaned |
| **Summarizer** | DistilBART CNN 12-6 (transformer) | Sequence-to-sequence summarization using encoder-decoder architecture | Summary, key takeaways, compression metrics |
| **ConceptExtractor** | Sentence-BERT (all-MiniLM-L6-v2), spaCy | Semantic embedding generation and NLP processing | Ranked list of key concepts with relevance scores |
| **QuizGenerator** | Rule-based logic + Sentence-BERT | Question generation from text and concepts | Fill-in-the-blank, Multiple Choice, True/False, Comprehension questions |
| **ExplanationGenerator** | Sentence-BERT + Knowledge base | Contextual explanation generation | Explanations with definitions and context from text |

---

## Error Handling and Fallback Mechanisms

The system includes robust fallback mechanisms to ensure the application remains functional even when certain components fail:

1. **Missing Transformers Library:**
   - If the transformers library is not installed, the summarizer uses mock summarization
   - Mock mode simply returns the first two sentences of the text as a placeholder summary
   
2. **Missing Machine Learning Dependencies:**
   - If sentence-transformers or spaCy are not available, the concept extractor falls back to simple keyword extraction
   - Uses basic string splitting and frequency analysis instead of semantic embeddings
   
3. **Model Loading Failure:**
   - If the preferred model fails to load, the system automatically falls back to CPU mode
   - If GPU acceleration is unavailable, it uses CPU with quantization for acceptable performance
   
4. **Extraction Failure:**
   - If file text extraction fails, returns user-friendly error messages describing the issue
   - Validates file size (50MB limit) before processing

5. **Insufficient Text Quality:**
   - Minimum text length of 50 characters is enforced
   - Validates that extracted text is not just whitespace

---

## API Endpoints

### POST `/analyze`
Process raw text input directly.

**Request:**
```json
{
  "text": "Educational content here..."
}
```

**Response:**
```json
{
  "summary": "Generated summary...",
  "concepts": ["concept1", "concept2", ...],
  "concept_details": [{"term": "...", "relevance": 0.85}, ...],
  "takeaways": ["Key point 1", "Key point 2", ...],
  "quiz": {
    "fill_in_the_blanks": [...],
    "mcqs": [...],
    "true_false": [...],
    "comprehension": [...]
  },
  "explanations": {...},
  "metrics": {"compression_ratio": 0.25, "coverage_score": 0.82}
}
```

### POST `/analyze-file`
Upload and process a file (PDF, PowerPoint, or text file).

**Request:** Multipart form data with file

**Response:** Same structure as `/analyze` endpoint

**Supported File Formats:**
- PDF documents (`.pdf`)
- PowerPoint presentations (`.pptx`)
- Plain text files (`.txt`)

---

## Performance Considerations

1. **Caching:** Summaries are cached using SHA256 hash of input
2. **Device Selection:** Automatically selects best available device (CUDA > MPS > CPU)
3. **Quantization:** CPU inference uses dynamic INT8 quantization
4. **Chunking:** Long documents are processed in chunks to avoid memory issues
5. **Batch Processing:** Embeddings are computed in batches where possible

