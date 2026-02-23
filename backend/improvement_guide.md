# How to Improve Model Accuracy

## Current Performance
- **Summarizer ROUGE-1**: 53.36%
- **Concept Extractor F1**: 69.70%

## Quick Wins (No Training Required)

### 1. Filter Low-Quality Concepts
Add to `app/nlp/extractor.py`:

```python
def filter_concepts(self, concepts: List[str]) -> List[str]:
    \"\"\"Filter out low-quality concepts.\"\"\"
    stopwords = {'a', 'an', 'the', 'this', 'that', 'is', 'are', 'was', 'were'}
    filtered = []
    for concept in concepts:
        # Remove short concepts
        if len(concept) < 4:
            continue
        # Remove concepts that are mostly stopwords
        words = concept.lower().split()
        if len(words) == 0:
            continue
        stopword_ratio = sum(1 for w in words if w in stopwords) / len(words)
        if stopword_ratio > 0.5:
            continue
        filtered.append(concept)
    return filtered
```

**Expected Improvement**: +5-8% precision

### 2. Deduplicate Similar Concepts
```python
from sklearn.metrics.pairwise import cosine_similarity

def deduplicate_concepts(self, concepts: List[str], threshold: float = 0.85):
    \"\"\"Remove semantically similar concepts.\"\"\"
    if len(concepts) <= 1:
        return concepts
    
    embeddings = self.model.encode(concepts)
    similarity_matrix = cosine_similarity(embeddings)
    
    unique = []
    for i, concept in enumerate(concepts):
        is_duplicate = False
        for j in range(i):
            if similarity_matrix[i][j] > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            unique.append(concept)
    return unique
```

**Expected Improvement**: +3-5% precision

### 3. Minimum Length Threshold
```python
# In extract_concepts method
candidates = [c for c in candidates if len(c.strip()) > 3]
```

**Expected Improvement**: +2-3% precision

## Training-Based Improvements

### 1. Fine-tune with More Data
Run the training script with expanded dataset:

```bash
cd Synod/backend
python3 improve_accuracy.py
```

**Expected Improvement**: +10-15% accuracy

### 2. Hyperparameter Optimization
Current → Optimized:
- Learning rate: 5e-5 → 3e-5
- Batch size: 2 → 4
- Epochs: 3 → 10 (with early stopping)
- Gradient accumulation: 1 → 2

**Expected Improvement**: +5-8% accuracy

### 3. Hard Negative Mining
For concept extraction, train with hard negatives:

```python
# Add negative examples that are similar but wrong
train_examples.append(InputExample(
    texts=[text, similar_but_wrong_concept],
    label=0.0
))
```

**Expected Improvement**: +8-12% F1-score

## Advanced Techniques

### 1. Use Larger Models
- Summarizer: `distilbart-cnn-12-6` → `facebook/bart-base`
- Extractor: `all-MiniLM-L6-v2` → `all-mpnet-base-v2`

**Expected Improvement**: +10-15% accuracy
**Trade-off**: 2-3x slower inference

### 2. Ensemble Methods
Combine multiple models:
```python
def ensemble_summarize(text):
    summary1 = model1.summarize(text)
    summary2 = model2.summarize(text)
    # Select best using ROUGE score
    return best_summary
```

**Expected Improvement**: +5-10% accuracy
**Trade-off**: 2x inference time

### 3. Domain-Specific Training
Train on lecture transcripts specifically:
- Collect 100+ lecture transcripts
- Create summaries and concept lists
- Fine-tune models on this data

**Expected Improvement**: +15-20% accuracy

## Implementation Priority

1. **Immediate (Today)**: Apply quick wins → +10% improvement
2. **Short-term (This week)**: Fine-tune with more data → +15% improvement  
3. **Medium-term (This month)**: Use larger models → +15% improvement
4. **Long-term (Ongoing)**: Domain-specific training → +20% improvement

## Expected Final Accuracy

After all improvements:
- **Summarizer ROUGE-1**: 70-75%
- **Concept Extractor F1**: 80-85%

## Run Improved Training

```bash
# 1. Run optimized training
cd Synod/backend
python3 improve_accuracy.py

# 2. Test improvements
python3 evaluate_models.py

# 3. Compare results
cat evaluation_report.json
```

## Monitoring

Track these metrics over time:
1. ROUGE-1, ROUGE-2, ROUGE-L for summarization
2. Precision, Recall, F1 for concept extraction
3. Inference time (should not increase >20%)
4. Memory usage

## When to Stop Improving

Stop when:
- Accuracy gains < 2% per iteration
- Inference time increases >50%
- Diminishing returns on training time
- Model overfits to training data

Current models are **production-ready**. Improvements are optional but recommended for better user experience.
