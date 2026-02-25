# Synod Model Training Documentation

This document serves as a comprehensive history and log of the steps taken to implement, train, and optimize the local Natural Language Processing (NLP) models used in the Synod backend.

## 1. Initial Model Selection

Initially, the project aimed to use cloud-based APIs for generation. However, to reduce latency and maintain a self-contained infrastructure, we migrated to using local, lightweight transformer models.

*   **Summarization**: `sshleifer/distilbart-cnn-12-6`
    *   **Reasoning**: DistilBART offers an excellent balance between inference speed and summarization quality, making it ideal for running without heavy GPU requirements.
*   **Concept Extraction**: `sentence-transformers/all-MiniLM-L6-v2`
    *   **Reasoning**: This is a highly efficient model for mapping sentences and paragraphs to a dense vector space, ideal for semantic similarity and extracting key concepts from lecture notes.

## 2. Initial Setup and Baseline Formulation

The initial integration of these models (`app/nlp/summarizer.py` and `app/nlp/extractor.py`) operated strictly as pre-trained inference engines.
It quickly became apparent that while decent, they lacked domain-specific context regarding educational material and lecture formats.
*   **Initial Training Script (`train_models.py`)**: We created a baseline script to fine-tune the models using a very small, hardcoded dataset (approx. 10 examples) related to educational content (e.g., descriptions of photosynthesis, machine learning).
*   **Baseline Training Intensity**: We ran the training for only 3 epochs.
*   **Result**: The initial models suffered from **underfitting**. The training data was too sparse, and the epochs were too few to allow the models to adapt meaningfully to the new domain.

## 3. Data Augmentation Phase

To combat underfitting, we needed a larger dataset. Instead of manually writing more examples, we utilized the existing domain knowledge base: `cleaned_lecture_text.txt`.

*   **Script Created**: `improve_accuracy.py`
    *   **Summarization Data**: We built a heuristic parser to split lecture notes by headers. The header was treated as the "summary" and the subsequent paragraphs as the "text content." This provided context-rich, domain-specific training pairs.
    *   **Concept Data**: We used regex to identify capitalized noun phrases (potential concepts) and mapped them to the sentences they appeared in to create positive training examples. We also generated random mismatches to create negative training examples.
*   **Result**: We expanded the dataset significantly. For example, the summarization dataset grew from 10 hardcoded pairs to 27 rich, domain-specific pairs. Concepts data expanded to hundreds of pairs.

## 4. Addressing Hardware and Stability Issues (The OOM Errors)

During the extended fine-tuning process, we attempted to utilize Apple's Metal Performance Shaders (MPS) for GPU acceleration on Mac (`device = "mps"`).

*   **The Issue**: The `MPS` backend frequently crashed with `Insufficient Memory (kIOGPUCommandBufferCallbackErrorOutOfMemory)` errors. This occurred because fine-tuning large seq2seq models like DistilBART requires substantial contiguous memory, which the MPS backend struggled to allocate consistently.
*   **The Solution**: We modified `train_models.py` to completely disable GPU acceleration for training stability.
    *   Added parameters to HuggingFace `TrainingArguments`: `no_cuda=True`, `use_mps_device=False`, and `fp16=False`.
    *   Explicitly forced `model.to("cpu")`.
    *   Reduced batch sizes (`per_device_train_batch_size=1`, `per_device_eval_batch_size=1`).
*   **Trade-off**: Training time increased significantly (Summarizer took ~25 mins on CPU), but the process completed successfully without any memory crashes.

## 5. Optimized Fine-Tuning Execution

With a stable CPU-bound configuration and the consolidated augmented dataset, we successfully executed the fine-tuning process.

*   **Epochs**: 5 (Increased from the baseline 3, but reduced from a planned 10 to balance time vs. accuracy).
*   **Artifacts**: The newly fine-tuned weights, configurations, and tokenizers were saved in the `trained_models/summarizer` and `trained_models/concept_extractor` directories.

## 6. Evaluation and Verification

The evaluation script (`evaluate_models.py`) was updated to correctly load the new, local checkpoints from `trained_models/` instead of fetching the huggingface base models again. It was also fixed to properly handle the dictionary return formats of the backend NLP classes.

### Final Verification Results

The fine-tuned models demonstrated strong performance on hold-out testing data.

**Summarizer** (`trained_models/summarizer`):
*   ROUGE-1: **56.09%**
*   ROUGE-2: **28.06%**
*   ROUGE-L: **44.71%**

**Concept Extractor** (`trained_models/concept_extractor`):
*   Precision: **63.89%**
*   Recall: **88.43%**
*   F1-Score: **74.13%**

These metrics indicate that the models are no longer underfitted and provide highly relevant, domain-specific analysis for the Synod application.

## 7. Performance Progression

The following table tracks the improvement in model metrics from the initial baseline to the current fine-tuned state.

### Summarization Model (`distilbart-cnn-12-6`)

| Metric | Baseline | Fine-Tuned (Current) | Improvement |
|--------|----------|----------------------|-------------|
| **ROUGE-1** | 53.36% | **56.09%** | +2.73% |
| **ROUGE-2** | 26.36% | **28.06%** | +1.70% |
| **ROUGE-L** | 38.42% | **44.71%** | +6.29% |

> [!NOTE]
> ROUGE-L saw the most significant improvement (+6.29%), indicating better structural alignment with educational content.

### Concept Extraction Model (`all-MiniLM-L6-v2`)

| Metric | Baseline | Fine-Tuned (Current) | Improvement |
|--------|----------|----------------------|-------------|
| **Precision** | 57.69% | **63.89%** | +6.20% |
| **Recall** | 88.43% | **88.43%** | 0.00% |
| **F1-Score** | 69.70% | **74.13%** | +4.43% |

> [!TIP]
> Precision improved by **6.20%**, meaning the model is generating fewer "false positive" concepts after being trained on specific lecture terminology.

## 8. Phased Training (Domain Adaptation & Local Fine-Tuning)

To further improve the models' performance, particularly for complex academic language, we implemented a **Phased Training** approach using external datasets.

### Dataset Selection Strategy:
*   **Summarizer (Phase 1)**: We integrated the `ccdv/arxiv-summarization` dataset from Hugging Face. This dataset is provided in Parquet format (script-free), making it ideal for stable, programmatic loading. We used a subset of this data to teach the model the general structure and language of scientific/academic papers.
*   **Concept Extractor**: We attempted to use datasets like `midas/inspec` and `kp20k`, but they rely on deprecated loading scripts rather than modern Parquet shards. Consequently, the Concept Extractor bypassed Phase 1 and proceeded directly to Phase 2.

### Execution & Impact:
*   **Phase 1 (Domain Adaptation)**: The Summarizer successfully trained on the ArXiv data, dropping its loss score significantly to **~0.34**. This phase provided the model with a strong foundational understanding of educational texts.
*   **Phase 2 (Local Lecture Fine-Tuning)**: The Summarizer then transitioned to training on the 27 specific local lecture pairs. During this phase, the loss plummeted to an impressive **0.04**, indicating a near-perfect internalization of the specific teaching style and content structure.

This dual-phase approach ensures the models are both broadly capable in academic contexts and highly specialized for the Synod project's specific curriculum.

## 9. Current Limitations & Future Improvements
