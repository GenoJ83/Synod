from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import shutil
import uvicorn
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from app.nlp.summarizer import Summarizer
from app.nlp.extractor import ConceptExtractor
from app.nlp.quiz_gen import QuizGenerator
from app.nlp.explanation_generator import ExplanationGenerator
from app.ingestion.extractor_service import ExtractorService
from app.auth import router as auth_router

# Initialize Database
from app.database import engine, Base
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Synod API")

# Session middleware for OAuth (required by Authlib)
from starlette.middleware.sessions import SessionMiddleware

# Prioritize JWT_SECRET, fallback to SESSION_SECRET, then a dev default
SESSION_SECRET = os.getenv("JWT_SECRET", os.getenv("SESSION_SECRET", "session_development_secret_key_123"))
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Enable CORS for React development
ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
    "http://127.0.0.1:5173",
    "http://localhost:5173"
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
explanation_gen = ExplanationGenerator()
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
    concept_details: Optional[List[Dict]] = None
    quiz: Dict
    explanations: Optional[Dict] = None
    takeaways: Optional[List[str]] = None
    metrics: Optional[Dict] = None

def process_logic(text: str):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    # 1. Summarization (now returns dict with summary and metrics)
    sum_result = summarizer.summarize(text)
    summary = sum_result["summary"]
    metrics = sum_result.get("metrics", {})

    # 2. Concept extraction (returns list of dicts with term and relevance)
    concept_data = extractor.extract_concepts(text)
    concepts = [c["term"] for c in concept_data]

    # 3. Quiz generation from full text and concepts
    fibs = quiz_gen.generate_fill_in_the_blanks(text, concepts)
    mcqs = quiz_gen.generate_mcqs(text, concepts, concepts, extractor=extractor)
    true_false = quiz_gen.generate_true_false(text, concepts)
    comprehension = quiz_gen.generate_comprehension(text, concepts)

    # 4. Generate explanations for each concept (passing extractor for dynamic definitions)
    explanations = explanation_gen.generate_all_explanations(concepts, text, extractor=extractor)

    # 5. Generate structured takeaways
    takeaways = summarizer.generate_takeaways(text)

    return {
        "summary": summary,
        "concepts": concepts, 
        "concept_details": concept_data, 
        "takeaways": takeaways,
        "quiz": {
            "fill_in_the_blanks": fibs,
            "mcqs": mcqs,
            "true_false": true_false,
            "comprehension": comprehension,
        },
        "explanations": explanations,
        "metrics": metrics,
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to Synod API",
        "device_info": {
            "summarizer": summarizer.device if hasattr(summarizer, "device") else "mock",
            "extractor": extractor.device if hasattr(extractor, "device") else "mock"
        }
    }

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
