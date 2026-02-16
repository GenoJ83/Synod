from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
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
import secrets

app.add_middleware(SessionMiddleware, secret_key=secrets.token_urlsafe(32))

# Enable CORS for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize NLP modules
summarizer = Summarizer(model_name="sshleifer/distilbart-cnn-12-6")
extractor = ConceptExtractor()
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

def process_logic(text: str):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    summary = summarizer.summarize(text)
    concepts = extractor.extract_concepts(text)
    
    fibs = quiz_gen.generate_fill_in_the_blanks(summary, concepts)
    mcqs = quiz_gen.generate_mcqs(summary, concepts, concepts)
    
    return {
        "summary": summary,
        "concepts": concepts,
        "quiz": {
            "fill_in_the_blanks": fibs,
            "mcqs": mcqs
        }
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
