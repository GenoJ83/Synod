# Synod: Intelligent Lecture and Course Content Assistant

## Project Overview
**Synod** is an advanced NLP-based assistant designed to streamline the analysis of university lecture materials. The system helps both lecturers and students by automatically extracting key concepts, generating concise summaries, and producing high-quality revision questions from slides and documents.

## Group Details
- **Group Members:** Geno Joshua, Mokili Promise Pierre, Pouch Mabor Makuei, Calvin Diego
- **Course:** Natural Language Processing and Text Analytics
- **Project Duration:** 8 Weeks (Starting Feb 10, 2026)

## Key Features
- **Multi-format Ingestion:** Supports PDF, PPTX, and plain text via a unified upload flow.
- **Concept Extraction & Ranking:** Identifies and ranks the most important topics using transformer embeddings (Sentence-BERT) plus TF-IDF/TextRank.
- **Automated Summarization:** Generates abstractive summaries using state-of-the-art transformer models (T5/BART) from Hugging Face.
- **Quiz Generation:** Creates multiple-choice and fill-in-the-blank questions for revision from key concepts and salient sentences.
- **Importance Explanations:** Provides explanations of why content is important (e.g. attention/score-based sentence importance and concept frequencies).
- **Modern Web App:** React frontend with a FastAPI backend, supporting authentication (email/password + OAuth) and lecture analysis history.

## High-Level Architecture

Synod is built as a **modular pipeline** exposed via a REST API and consumed by a React UI:

- **Backend (`backend/`) – FastAPI + NLP pipeline**
  - `app/ingestion/` – file parsing modules (PDF via PyMuPDF, PPTX via `python-pptx`, TXT).
  - `app/processing/` – text normalization, cleaning, and sentence segmentation (NLTK/spaCy).
  - `app/nlp/` – core NLP logic (embeddings, summarization, key concept ranking, question generation, explanations, evaluation).
  - `app/auth/` – authentication (JWT, Google/GitHub OAuth, email/password) and related helpers.
  - `app/database.py`, `app/models.py` – SQLite-backed persistence for users and (optionally) analysis metadata.
  - `main.py` – FastAPI entrypoint exposing `/analyze`, `/analyze-file`, and `auth` routes.
  - `requirements.txt` – Python dependencies (FastAPI, transformers, sentence-transformers, PyMuPDF, python-pptx, etc.).

- **Frontend (`frontend/`) – React + Vite + Tailwind**
  - `src/pages/` – route-level pages (`LandingPage`, `Dashboard`, `History`, `Login`, `Signup`, `AuthCallback`, etc.).
  - `src/components/` – reusable UI components (`FileUploader`, `QuizSection`, `ProtectedRoute`, etc.).
  - `src/context/` – global state (theme + authentication context).
  - `src/App.jsx` – route configuration and layout shell.
  - `package.json` – frontend dependencies and scripts.

- **Shared project structure**
  - `data/` – sample lecture documents and upload directory for backend processing.
  - `models/` – fine-tuning notebooks, model configs, and saved weights (if any).
  - `backend/tests/` – automated tests for ingestion, auth, and the NLP pipeline.
  - `.venv/` – local Python virtual environment (not committed).

## Implementation Pipeline

1. **Data Ingestion**
   - Upload PDF/PPTX/TXT via the React dashboard.
   - Backend `ExtractorService` detects file type and extracts raw text using PyMuPDF (`fitz`), `python-pptx`, or standard file IO.

2. **Preprocessing**
   - Text is cleaned (whitespace/boilerplate removal, normalization).
   - Sentence segmentation using NLTK or spaCy to produce a list of sentences suitable for downstream models.

3. **Key Concept Extraction & Ranking**
   - Sentences/terms are embedded with a Sentence-BERT model (`sentence-transformers`).
   - TF-IDF/TextRank (and optionally embedding-based similarity) are used to score and rank key concepts/topics.

4. **Summarization**
   - A pre-trained summarization model (e.g. BART/T5 from Hugging Face) generates concise abstractive summaries.
   - For long lectures, the text is chunked and summarized hierarchically, then merged into an overall summary.

5. **Question Generation**
   - A sequence-to-sequence model (e.g. T5-based QG) generates multiple-choice and fill-in-the-blank questions.
   - Questions are conditioned on the most important concepts and/or key supporting sentences.

6. **Explanations & Evaluation**
   - Importance explanations are produced from attention/score distributions and concept frequencies and returned alongside concepts and summaries.
   - If a reference summary is provided, ROUGE scores can be computed for quantitative evaluation.
   - The React dashboard visualizes summaries, concepts, questions, and (optionally) evaluation metrics and history.

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+ and npm (or pnpm/yarn) for the React frontend
- [Optional] GPU for faster transformer inference and fine-tuning

### Backend Setup (FastAPI + NLP)

1. Create and activate a virtual environment (recommended):
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # source .venv/bin/activate  # On macOS/Linux
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the backend API server (default: `http://localhost:8000`):
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup (React)

1. Install frontend dependencies:
   ```bash
   cd ../frontend
   npm install
   ```
2. Start the development server (default: `http://localhost:5173`):
   ```bash
   npm run dev
   ```
3. Ensure the backend (`8000`) and frontend (`5173`) are both running. The React dashboard will call the FastAPI endpoints (e.g. `/analyze`, `/analyze-file`, `/auth/*`).

## License
MIT License
