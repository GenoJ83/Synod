from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import os
import shutil
from pathlib import Path

from app.nlp.summarizer import Summarizer
from app.nlp.extractor import ConceptExtractor
from app.nlp.quiz_gen import QuizGenerator
from app.ingestion.extractor_service import ExtractorService
from app.auth import router as auth_router

# Initialize Database
from app.database import engine, Base
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Synod API")

# Session middleware for OAuth (required by Authlib)
from starlette.middleware.sessions import SessionMiddleware

SESSION_SECRET = os.getenv("SESSION_SECRET", os.getenv("JWT_SECRET", "session_development_secret_key_123"))
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Enable CORS for React development
ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
Lightweight NLP pipeline wiring.
The heavy model objects are instantiated once at startup and reused.
Each component has an internal MOCK/fallback mode when dependencies are missing.
"""
summarizer = Summarizer(model_name=os.getenv("SUMMARY_MODEL", "sshleifer/distilbart-cnn-12-6"))
extractor = ConceptExtractor(model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
quiz_gen = QuizGenerator()
file_extractor = ExtractorService()

# Register authentication routes
app.include_router(auth_router)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class ProcessRequest(BaseModel):
    text: str

class ProcessResponse(BaseModel):
    summary: str
    concepts: List[str]
    quiz: Dict
    explanations: Optional[Dict] = None
    metrics: Optional[Dict] = None

def process_logic(text: str):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    # 1. Summarization
    summary = summarizer.summarize(text)

    # 2. Concept extraction (ranked key phrases)
    concepts = extractor.extract_concepts(text)

    # 3. Quiz generation from summary + concepts
    fibs = quiz_gen.generate_fill_in_the_blanks(summary, concepts)
    mcqs = quiz_gen.generate_mcqs(summary, concepts, concepts)

    # 4. Simple explanation scaffold (can be enriched later)
    explanations = {
        "global": "Concepts are ranked by semantic similarity to the overall lecture content.",
        "concepts": [{"term": c, "reason": "High semantic similarity and frequent occurrence."} for c in concepts],
    }

    return {
        "summary": summary,
        "concepts": concepts,
        "quiz": {
            "fill_in_the_blanks": fibs,
            "mcqs": mcqs,
        },
        "explanations": explanations,
        "metrics": None,
    }

@app.get("/")
async def root():
    return {"message": "Welcome to Synod API"}

@app.post("/analyze", response_model=ProcessResponse)
async def analyze_text(request: ProcessRequest):
    try:
        return process_logic(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-file", response_model=ProcessResponse)
async def analyze_file(file: UploadFile = File(...)):
    try:
        file_location = UPLOAD_DIR / file.filename
        with file_location.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        text = file_extractor.extract_text(str(file_location))
        
        # Cleanup uploaded file after extraction
        os.remove(file_location)
        
        return process_logic(text)
    except Exception as e:
        if 'file_location' in locals() and file_location.exists():
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
