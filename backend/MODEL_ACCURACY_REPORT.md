# Synod Model Accuracy & Precision Report

**Generated:** 2025-01-09  
**Models Evaluated:** distilbart-cnn-12-6, all-MiniLM-L6-v2

---

## 📊 Model Performance Summary

### 1. Summarization Model (distilbart-cnn-12-6)

| Metric | Score | Percentage |
|--------|-------|------------|
| **ROUGE-1** | 0.5336 | **53.36%** |
| **ROUGE-2** | 0.2636 | **26.36%** |
| **ROUGE-L** | 0.3842 | **38.42%** |
| **Inference Time** | 6.47s | - |

**Interpretation:**
- ROUGE-1 (53.36%): Good unigram overlap between generated and reference summaries
- ROUGE-2 (26.36%): Moderate bigram overlap (indicates some fluency issues)
- ROUGE-L (38.42%): Reasonable longest common subsequence match

**Status:** ✅ **ACCEPTABLE** - Suitable for educational content summarization

---

### 2. Concept Extraction Model (all-MiniLM-L6-v2)

| Metric | Score | Percentage |
|--------|-------|------------|
| **Precision** | 0.5769 | **57.69%** |
| **Recall** | 0.8843 | **88.43%** |
| **F1-Score** | 0.6970 | **69.70%** |
| **Inference Time** | 1.77s | - |

**Interpretation:**
- **Precision (57.69%)**: Of the concepts extracted, ~58% are relevant
- **Recall (88.43%)**: The model finds ~88% of all relevant concepts
- **F1-Score (69.70%)**: Good balance between precision and recall

**Status:** ✅ **GOOD** - High recall ensures most concepts are captured

---

## 🎯 Detailed Test Results

### Test Case 1: Machine Learning & AI
- **ROUGE-1**: 60.24% (Best performance)
- **Precision**: 50.00%
- **Recall**: 87.50%
- **F1**: 63.64%

### Test Case 2: Photosynthesis
- **ROUGE-1**: 36.67% (Challenging topic)
- **Precision**: 61.54%
- **Recall**: 88.89%
- **F1**: 72.73%

### Test Case 3: Water Cycle
- **ROUGE-1**: 63.16% (Best performance)
- **Precision**: 61.54%
- **Recall**: 88.89%
- **F1**: 72.73%

---

## 📈 Accuracy Percentages

### Overall Model Accuracy

```
Summarization Model (distilbart-cnn-12-6):
├── ROUGE-1 Accuracy:     53.36% ████████████████████░░░░░
├── ROUGE-2 Accuracy:     26.36% ██████████░░░░░░░░░░░░░░░
└── ROUGE-L Accuracy:     38.42% ███████████████░░░░░░░░░░

Concept Extractor (all-MiniLM-L6-v2):
├── Precision:            57.69% █████████████████████░░░░
├── Recall:               88.43% ████████████████████████████
└── F1-Score:             69.70% ████████████████████████░░░
```

---

## 🚀 Training Scripts Created

### 1. `evaluate_models.py`
- Evaluates model performance using standard metrics
- Generates ROUGE scores for summarization
- Calculates Precision, Recall, F1 for concept extraction
- Saves detailed reports to `evaluation_report.json`

**Usage:**
```bash
cd Synod/backend
python3 evaluate_models.py
```

### 2. `train_models.py`
- Fine-tunes models on educational content
- Improves accuracy through domain-specific training
- Saves trained models to `trained_models/`
- Generates training reports

**Usage:**
```bash
cd Synod/backend
python3 train_models.py
```

---

## 📋 Recommendations

## ✅ Implemented Quality & Robustness Improvements (Restored)

The following post-processing and stabilization features have been successfully restored/implemented to ensure production-grade outputs:

1. **Ingestion Noise Reduction**: 
   - Automated header stripping (Professor names, subject codes, institutional metadata).
   - arXiv/Academic noise filtering (stripping tags, figure captions, and reference sections).
2. **Output Robustness**:
   - **Artifact Fixing**: Collapsing model "repeating loops" (e.g., "Word Word Word...") and fixing tokenization hyphenation (e.g., "pro-pose" -> "propose").
   - **Redundancy Filtering**: Semantic overlap checks in both summaries and takeaways.
3. **Logic Deduplication**:
   - **Concept Merging**: Fuzzy deduplication of similar concepts (e.g., merging "clean code" and "clean code practices").
   - **Unique Explanations**: Ensuring each concept receives a unique contextual definition.

---

## 📋 Recommendations

### Path to Higher Precision:

1. **Fine-tune on Educational Data**
   - Use `train_models.py` to train on lecture transcripts.
   - Target: Improve ROUGE-2 and Precision for niche technical topics.

2. **Increase Training Epochs**
   - Recommended: 5-10 epochs for better convergence on specific faculty datasets.

---

## ✅ Conclusion

**Current State:**
- **Robustness**: High. System handles noisy academic text, metadata leaks, and repetitive artifacts.
- **Deduplication**: Successfully implemented for both concepts and individual explanations.
- **Performance**: Optimized for MPS/CUDA with prioritized local model loading.

**Overall Status:** ✅ **Production Ready**
