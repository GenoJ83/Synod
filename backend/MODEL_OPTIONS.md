# Synod Model Options

This document describes the NLP models used by Synod and how to switch or improve them.

## Current Default Models

| Component | Model | Use Case |
|-----------|-------|----------|
| **Summarization** | `sshleifer/distilbart-cnn-12-6` | General lecture notes, fast inference |
| **Concept Extraction** | `all-MiniLM-L6-v2` | Key phrase extraction, semantic similarity |
| **spaCy** | `en_core_web_sm` | POS tagging, NER (used by extractor) |

---

## Improving Summarization for Academic Papers

DistilBART is tuned for news-style text. For **academic papers and research documents**, use a model trained on scientific content:

### Recommended: Pegasus-X ArXiv (Best for Papers)

```bash
# 1. Download the model (one-time)
python download_models.py --academic

# 2. Use it via environment variable
export SUMMARY_MODEL=UNIST-Eunchan/Research-Paper-Summarization-Pegasus-x-ArXiv
uvicorn main:app --reload
```

**Model:** `UNIST-Eunchan/Research-Paper-Summarization-Pegasus-x-ArXiv`
- Fine-tuned on 200,000+ arXiv papers
- Handles up to 16K tokens (full papers)
- ROUGE-1: 43.23 (vs ~6 zero-shot)
- **Trade-off:** Larger and slower than DistilBART; better for research PDFs

### Alternative: BART Large (Better Quality, Slower)

```bash
export SUMMARY_MODEL=facebook/bart-large-cnn
```

- Higher quality than DistilBART
- ~3× larger, slower inference
- Good for mixed lecture + paper content

---

## Improving Concept Extraction

### MPNet (Better Precision)

```bash
export EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
```

- Better semantic understanding than MiniLM
- **Trade-off:** ~2× slower, higher memory

### BGE (Modern Alternative)

```bash
export EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

- Strong performance for retrieval/similarity
- Similar size to MiniLM

---

## Using Fine-Tuned (Trained) Models

After running `python train_models.py`, models are saved to `trained_models/`. The API **automatically uses them** if they exist—no env vars needed.

To force the pre-trained base model instead:
```bash
# Use HuggingFace model, ignore trained_models/
export SUMMARY_MODEL=sshleifer/distilbart-cnn-12-6
export EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## Retraining the Models

### Quick Retrain

```bash
cd backend
python train_models.py
```

This will:
1. Load 300 ArXiv paper (article→abstract) pairs for domain adaptation
2. Load local augmented data from `training_data/`
3. Fine-tune the summarizer for 3+5 epochs (CPU-safe)
4. Fine-tune the concept extractor
5. Save to `trained_models/summarizer` and `trained_models/concept_extractor`

### Add More Training Data

1. **Summarization:** Add pairs to `training_data/summarization_augmented.json`:
   ```json
   {"text": "Long lecture or paper excerpt...", "summary": "Concise summary..."}
   ```

2. **Concepts:** Add pairs to `training_data/concepts_augmented.json`:
   ```json
   {"text": "Sentence containing the concept", "concept": "key term", "label": 1.0}
   ```

3. **Auto-generate from lectures:** Run `python improve_accuracy.py` to extract pairs from `cleaned_lecture_text.txt`

### Requirements

- `transformers`, `datasets`, `sentence-transformers`
- Training uses CPU by default (GPU/MPS disabled for stability)
- Expect ~25–40 minutes for full training on CPU

---

## Summary: Quick Reference

| Goal | Action |
|------|--------|
| **Better academic paper summaries** | `SUMMARY_MODEL=UNIST-Eunchan/Research-Paper-Summarization-Pegasus-x-ArXiv` |
| **Faster inference** | Keep DistilBART (default) |
| **Domain adaptation** | Run `python train_models.py` |
| **Better concept precision** | `EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2` |
| **Download optional models** | `python download_models.py --academic` |
