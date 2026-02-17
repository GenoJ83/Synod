# Lecture Assistant - Documentation

## Overview

Lecture Assistant is a web application that helps students analyze lecture content, extract key concepts, generate summaries, and test their understanding through interactive quizzes.

## System Architecture

### Frontend (React + Vite)
- **Location:** `frontend/`
- **Tech Stack:** React, Vite, TailwindCSS, Framer Motion
- **Port:** 5173 (development)

### Backend (FastAPI)
- **Location:** `backend/`
- **Tech Stack:** FastAPI, Python, Transformers, Sentence Transformers
- **Port:** 8000

## Features

### 1. Content Analysis
Users can upload lecture content (text or files) and receive:
- **Executive Summary** - A concise overview of the lecture
- **Foundational Concepts** - Key terms and topics extracted from the content

### 2. Interactive Quiz
The system generates ~30 questions across 4 question types:
- **Fill-in-the-Blank** - Recall key terms (8 questions)
- **Multiple Choice** - Test term recognition (8 questions)
- **True/False** - Test comprehension of statements (8 questions)
- **Comprehension** - Test understanding of relationships (5 questions)

### 3. Concept Explanations
Click on any foundational concept to see:
- Educational definition of the concept
- Context-specific examples from the lecture
- Related concepts for deeper learning

### 4. History Tracking
All analyzed lectures are saved to localStorage, allowing users to:
- Browse past analyses
- Search through history
- Revisit previous quizzes

## User Flow

```
1. User logs in / lands on page
2. User enters lecture text OR uploads a file
3. System processes content:
   - Extracts concepts
   - Generates summary
   - Creates quiz questions
4. User views summary and concepts
5. User clicks concept for explanation
6. User takes quiz to test understanding
7. Results are shown with score
```

## Running the Application

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### POST /analyze
Analyze text content.

**Request:**
```json
{
  "text": "Lecture content here..."
}
```

**Response:**
```json
{
  "summary": "Executive summary...",
  "concepts": ["concept1", "concept2", ...],
  "quiz": {
    "fill_in_the_blanks": [...],
    "mcqs": [...],
    "true_false": [...],
    "comprehension": [...]
  },
  "explanations": {
    "global": "...",
    "concepts": [{"term": "...", "reason": "..."}]
  }
}
```

### POST /analyze-file
Analyze uploaded file (PDF, TXT, DOCX).

### POST /auth/login
User authentication.

### POST /auth/register
User registration.

## Project Structure

```
Lecture Assistant/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── QuizSection.jsx    # Quiz UI
│   │   │   ├── FileUploader.jsx    # File upload
│   │   │   └── ProtectedRoute.jsx  # Auth protection
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Main analysis page
│   │   │   ├── History.jsx         # Past analyses
│   │   │   └── ...
│   │   ├── context/
│   │   │   ├── AuthContext.jsx     # Authentication state
│   │   │   └── ThemeContext.jsx    # Theme (dark/light)
│   │   └── ...
│   └── ...
├── backend/
│   ├── app/
│   │   ├── nlp/
│   │   │   ├── summarizer.py       # Text summarization
│   │   │   ├── extractor.py        # Concept extraction
│   │   │   ├── quiz_gen.py        # Quiz generation
│   │   │   └── explanation_generator.py # Concept explanations
│   │   ├── auth/
│   │   │   └── routes.py          # Auth endpoints
│   │   └── ...
│   ├── main.py                     # FastAPI app
│   └── requirements.txt
└── ...
```

## NLP Pipeline

1. **Text Input** → Raw lecture content
2. **Summarization** → Uses DistilBART model to generate executive summary
3. **Concept Extraction** → Uses Sentence Transformers to find key concepts
4. **Quiz Generation** → Creates questions from full text (not just summary)
5. **Explanation Generation** → Creates educational definitions + context

## Quiz Generation Details

The quiz generator creates questions in 4 categories:

### Fill-in-the-Blank
- Finds sentences containing key concepts
- Masks the concept with "__________"
- Answer is the masked term

### Multiple Choice
- Same as FIB but with distractors from other concepts
- 4 options (1 correct, 3 distractors)

### True/False
- Takes statements from lecture
- Creates false versions by negation or swapping concepts
- Tests understanding of factual content

### Comprehension
- Generates questions about relationships between concepts
- Asks "How does X work?" or "What's the relationship between X and Y?"
- Tests deeper understanding

## Troubleshooting

### Backend won't start
- Ensure PYTHONPATH is set: `set PYTHONPATH=.`
- Run from project root: `cd backend && python -m uvicorn main:app`

### Quiz shows no questions
- Check backend is running on port 8000
- Check browser console for API errors

### Concepts not showing
- Ensure text has enough content (minimum ~50 words)
- Check concept extraction is working in backend logs

## Technology Choices

- **React** - Modern UI framework with component-based architecture
- **TailwindCSS** - Utility-first CSS for rapid styling
- **Framer Motion** - Smooth animations for better UX
- **FastAPI** - Modern, fast Python web framework
- **Transformers** - HuggingFace library for NLP models
- **Sentence Transformers** - For semantic concept extraction
- **LocalStorage** - For history persistence without backend database
