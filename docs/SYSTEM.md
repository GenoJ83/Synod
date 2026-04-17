# Synod — System Overview

Synod is a **lecture-study assistant**: students upload notes (text or PDF/PPTX/TXT), and the app returns a **summary**, **takeaways**, **key concepts**, **quizzes** (multiple choice, fill-in-the-blank, true/false, comprehension), **on-demand concept explanations**, and an optional **notes-grounded chat**. Most NLP runs **locally** with Transformers and Sentence-BERT; **Google Gemini** is used only where configured (concept polish and chat).

This document ties together the **runtime architecture**, **data flow**, **training pipeline**, and **recorded metrics**. For a deeper dive into the text-generation stack alone, see [`explanation.md`](../explanation.md) in the repo root.

---

## 1. Repository layout (high level)

| Area | Role |
|------|------|
| `frontend/` | React (Vite) UI: dashboard, analysis results, history, auth, quiz UI, concept explorer, study chat. |
| `backend/` | FastAPI app, NLP modules, ingestion, optional SQLite/Postgres auth DB. |
| `backend/training_data/` | JSON/TXT datasets used to build or augment fine-tuning pairs. |
| `backend/train_models.py` | Offline fine-tuning for summarizer + sentence encoder paths. |
| `backend/trained_models/` | **Optional** local checkpoints (created after training); runtime may still use Hugging Face hub IDs if these are absent. |
| `docs/` | This file and other project documentation. |

---

## 2. End-to-end data flow

```
Upload (file) or paste (text)
        │
        ▼
ExtractorService  ──►  normalize_pipeline_text (shared scrub for whole pipeline)
        │
        ▼
POST /analyze  or  POST /analyze-file
        │
        ├──► Summarizer (DistilBART) ──► summary, takeaways, metrics
        ├──► ConceptExtractor (MiniLM + spaCy) ──► concepts + relevance
        ├──► QuizGenerator ──► MCQ, FIB, T/F, comprehension
        └──► source_text echoed to client for explain / chat / history

Client stores result (e.g. navigation state + localStorage history) including source_text.
```

**Important:** `source_text` is the **normalized** lecture body returned to the client so follow-up calls (`/explain-concept`, `/chat/notes`) stay grounded without re-uploading the file.

---

## 3. Backend API (FastAPI)

| Endpoint | Purpose |
|----------|---------|
| `POST /analyze` | JSON `{ "text": "..." }` → full pipeline JSON. |
| `POST /analyze-file` | Multipart upload (PDF / PPTX / TXT, size-capped) → extract text → same pipeline. |
| `POST /explain-concept` | `{ text, concept }` → `{ term, definition, context }`; optional Gemini when enabled. |
| `POST /chat/notes` | `{ source_text, message, history?, summary_hint? }` → `{ reply }` (Gemini + retrieved snippets). |
| `GET /` | Health-ish JSON including device hints for loaded models. |
| Auth routes | Under `app/auth` (OAuth/JWT); see `backend/app/auth` and `main.py` includes. |

CORS is configured for the Vite dev origin (`FRONTEND_URL` / localhost).

---

## 4. Ingestion and text hygiene

**Module:** `backend/app/ingestion/extractor_service.py`

- **PDF:** PyMuPDF (`fitz`)
- **PPTX:** `python-pptx`
- **TXT:** raw read

Steps typically include **header stripping**, **sanitization** (URLs, boilerplate), **academic noise** cleanup for PDFs (arXiv lines, caption junk, etc.), then **`normalize_pipeline_text`**, which also strips common **slide metadata** (e.g. title + lecturer lines) so downstream summarization and quizzes see less noise.

---

## 5. NLP pipeline (core)

Orchestration lives in **`backend/main.py`** (`process_logic`).

### 5.1 Summarizer

**File:** `backend/app/nlp/summarizer.py`  
**Default model id:** `sshleifer/distilbart-cnn-12-6` (overridable via `SUMMARY_MODEL`).

- **Chunking + two-pass synthesis** for long inputs.
- **Lecture narrative** weaving (extractive support sentences + BART lead) for readable “course recap” shape.
- **Pre-BART scrub** of slide/bibliography junk and **post-output sentence cleanup** to improve semantic fidelity.
- **Takeaways:** grounded bullets with lexical (and optional embedding) checks; cache salt bumps when behavior changes.
- **Optional LoRA:** adapter under `trained_models/summarizer_lora/final_adapter` — loaded only if `SYNOD_USE_SUMMARIZER_LORA=true` and compatible with the base model.

### 5.2 Concept extraction

**File:** `backend/app/nlp/extractor.py`  
**Encoder:** `sentence-transformers/all-MiniLM-L6-v2` (overridable via `EMBEDDING_MODEL`; can point to a local folder).

- spaCy **noun chunks** + some **entities**, ranked by **cosine similarity** to the document embedding.
- **Heuristic filters** for assignment rubric phrases, junk OCR phrases, overly long “concepts,” etc.

**Hub / network:** `HF_HUB_DOWNLOAD_TIMEOUT` and `HF_HUB_ETAG_TIMEOUT` are raised by default (see `main.py` and `extractor.py`); local cache is tried with `local_files_only=True` before any download.

### 5.3 Quiz generation

**File:** `backend/app/nlp/quiz_gen.py`

- Produces **MCQ**, **fill-in-the-blank** (with options), **true/false**, and **comprehension** items from sentences gated for quality (length, predicates, no bibliography/MOOC slide junk, checkbox/tick OCR noise, etc.).

### 5.4 Concept explanations (on demand)

**Files:** `backend/app/nlp/explanation_generator.py`, optional `backend/app/nlp/gemini_concept_explain.py`

**Before Gemini**, explanations were produced only by **`ExplanationGenerator`**: a **static glossary** (`CONCEPT_CATEGORIES` — definitions for common CS/ML terms plus generic fallbacks when there is no match) combined with **local Sentence-BERT** (`all-MiniLM-L6-v2`): the lecture text is split into sentences, the concept and each sentence are embedded, and the **highest–cosine-similarity** sentence(s) are chosen as “in context,” with extra filters to drop assignment/rubric noise.

**Gemini** was added later as an **optional path** for concept cards: when `USE_GEMINI_CONCEPT_EXPLAIN` is on and a key is configured, the API may send a **small retrieved snippet** plus the term to Gemini for a clearer student-facing answer. **That earlier glossary + embedding pipeline is unchanged and remains the fallback** — it always runs first, and the response **falls back to it** whenever Gemini is disabled, misconfigured, or errors (so explanations never depend solely on the external API).

### 5.5 Notes chat (study assistant)

**File:** `backend/app/nlp/notes_chat.py`

- Retrieves note **sentences** most similar to the student’s question (same encoder), then calls **Gemini** with strict “answer from notes” instructions.
- Controlled by `USE_NOTES_CHAT` and `GOOGLE_API_KEY` / `GEMINI_API_KEY`.

---

## 6. Frontend (React)

**Router:** `frontend/src/App.jsx`

| Route | Feature |
|-------|---------|
| `/` | Landing |
| `/dashboard` | Paste text or upload file → `POST /analyze` or `/analyze-file` → navigate to `/analysis` with state |
| `/analysis` | Summary, takeaways, metrics, **Key concepts** (click → `/explain-concept`), **Study assistant** chat, **Quiz** |
| `/history` | Past runs from `localStorage` (entries should include `source_text` for chat/explain on newer runs) |
| `/login`, `/signup`, … | Auth |

**Config:** `frontend/src/config.js` → `VITE_API_URL` / default `http://localhost:8000`.

---

## 7. Training pipeline and artifacts

### 7.1 Scripts and data

| Artifact | Description |
|----------|-------------|
| `train_models.py` | Main **fine-tuning** entry: seq2seq summarizer + sentence-transformer style concept training; writes under `trained_models/` and `training_report.json`. |
| `train_concepts_only.py` | Narrower concept-training utility. |
| `improve_accuracy.py`, `build_rich_dataset.py`, `generate_lecture_data.py`, … | Dataset construction / augmentation helpers (historical experimentation). |
| `training_data/*.json`, `lecture_notes_combined.txt` | Curated or augmented **(text, summary)** and **(text, concept)** style pairs for domain fine-tuning. |
| `evaluate_models.py` | ROUGE for summarization; precision/recall/F1 style checks for concept ranking (see repo + `MODEL_ACCURACY_REPORT.md`). |

**Design notes** (from `MODEL_TRAINING_DOCUMENTATION.md`):

- Early runs used **tiny** seed data → underfitting.
- Datasets were **expanded** from lecture-style text (headers as pseudo-summaries, noun-phrase heuristics for concepts).
- Training was stabilized on **CPU** (`no_cuda`, `use_mps_device=False`, small batches) to avoid Apple MPS OOM during full fine-tunes.
- **Phased summarization:** optional **ArXiv-style** domain adaptation, then **local lecture pairs** for specialization.

### 7.2 `training_report.json` (example snapshot)

The file at `backend/training_report.json` records one training run (timestamps and durations will differ if you re-run):

| Model key | Epochs | Final loss (reported) | Accuracy % (script metric) | Wall time |
|-----------|--------|-------------------------|----------------------------|-----------|
| `distilbart-cnn-12-6` | 5 | ~0.377 | **92.47%** | ~55.9 min (CPU) |
| `all-MiniLM-L6-v2` | 5 | ~0.15 | **85.00%** | ~4.6 min (CPU) |

> **Caveat:** The “accuracy” fields here are **training-script metrics**, not ROUGE or production quiz accuracy. Treat them as internal training diagnostics alongside the evaluation reports below.

### 7.3 Evaluation-style metrics (reports in repo)

**`backend/MODEL_ACCURACY_REPORT.md`** — baseline **pre-trained** inference-style evaluation (representative numbers from that report):

| Component | Metric | Value |
|-----------|--------|-------|
| Summarization (DistilBART) | ROUGE-1 | **53.36%** |
| | ROUGE-2 | **26.36%** |
| | ROUGE-L | **38.42%** |
| Concept encoder ranking | Precision | **57.69%** |
| | Recall | **88.43%** |
| | F1 | **69.70%** |

**`MODEL_TRAINING_DOCUMENTATION.md`** — **after fine-tune** checkpoint evaluation (on project hold-out style checks):

| Component | ROUGE-1 | ROUGE-2 | ROUGE-L | Precision | Recall | F1 |
|-----------|---------|---------|---------|-----------|--------|-----|
| Summarizer (fine-tuned path) | **56.09%** | **28.06%** | **44.71%** | — | — | — |
| Concept extractor (fine-tuned path) | — | — | — | **63.89%** | **88.43%** | **74.13%** |

These tables summarize **intent**: domain fine-tuning improved ROUGE and precision while keeping recall high for concepts.

### 7.4 Optional runtime checkpoints

If present (not committed by default in many clones):

- `trained_models/summarizer/` — full or partial seq2seq fine-tune output from `train_models.py`.
- `trained_models/concept_extractor/` — sentence-transformer checkpoint directory.
- `trained_models/summarizer_lora/final_adapter` — **LoRA** adapter; **off** unless `SYNOD_USE_SUMMARIZER_LORA=true`.

The live app defaults to **Hugging Face model IDs** unless you point env vars or code at local folders.

---

## 8. Environment variables (cheat sheet)

| Variable | Role |
|----------|------|
| `FRONTEND_URL`, `BACKEND_URL` | URLs for OAuth/CORS. |
| `JWT_SECRET` / `SESSION_SECRET` | Auth session signing. |
| `DATABASE_URL`, `USE_LOCAL_SQLITE` | DB backend. |
| `SUMMARY_MODEL` | Hugging Face id or local path for summarizer. |
| `EMBEDDING_MODEL` | MiniLM id or local path for concept/chat retrieval. |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini for concept explain + notes chat. |
| `USE_GEMINI_CONCEPT_EXPLAIN` | `true` to enable Gemini on `/explain-concept`. |
| `USE_NOTES_CHAT` | `true` (default) to allow `/chat/notes` when a key is set. |
| `GEMINI_MODEL` | e.g. `gemini-2.5-flash`. |
| `SYNOD_USE_SUMMARIZER_LORA` | `true` to load LoRA adapter. |
| `HF_HUB_DOWNLOAD_TIMEOUT`, `HF_HUB_ETAG_TIMEOUT` | Longer Hub reads (defaults set in `main.py` / `extractor.py`). |

See `backend/.env.example` for a starter list.

---

## 9. Running locally

1. **Backend:** Python 3.9+ recommended; `pip install -r backend/requirements.txt`; download spaCy `en_core_web_sm` if prompted; `cd backend && uvicorn main:app --reload` (or `python main.py` if wired).
2. **Frontend:** `cd frontend && npm install && npm run dev` — set `VITE_API_URL` if the API is not on port 8000.
3. **First run:** Hugging Face will **download** DistilBART and MiniLM unless caches exist; use a stable network or `huggingface-cli download` ahead of time.

---

## 10. Related documents

| Document | Focus |
|----------|--------|
| [`explanation.md`](../explanation.md) | Long-form explanation of the text-generation / transformer behavior. |
| [`backend/MODEL_TRAINING_DOCUMENTATION.md`](../backend/MODEL_TRAINING_DOCUMENTATION.md) | Training history, phased training, OOM mitigations. |
| [`backend/MODEL_ACCURACY_REPORT.md`](../backend/MODEL_ACCURACY_REPORT.md) | ROUGE + concept metrics and evaluation script usage. |
| [`backend/training_report.json`](../backend/training_report.json) | Raw training run summary JSON. |

---

## 11. Security and operations notes

- **Never commit** real `.env` secrets or live API keys.
- **Uploaded files** are written temporarily under `backend/data/uploads/`, processed, then deleted in the happy path.
- **Chat and Gemini** send **excerpts** of student text to Google when enabled — disclose in your product privacy policy if you ship this to end users.

---

*Last updated to reflect the Synod codebase structure (NLP modules, Gemini hooks, training reports, and evaluation docs). Re-run `train_models.py` / `evaluate_models.py` and refresh metrics tables if you change models or datasets.*
