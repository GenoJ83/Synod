from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import shutil
import uvicorn
import logging
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit

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
    """Process text through the complete NLP pipeline with comprehensive error handling."""
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    # Validate text is not just whitespace
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be only whitespace")
    
    text = ExtractorService.normalize_pipeline_text(text.strip())
    if len(text) < 50:
        raise HTTPException(status_code=400, detail="Text must be at least 50 characters")
    
    logger.info(f"Processing text of length: {len(text)} characters (after metadata scrub)")
    
    try:
        # 1. Summarization (now returns dict with summary, takeaways, and metrics)
        logger.info("Starting summarization...")
        sum_result = summarizer.summarize(text, extractor=extractor)
        summary = sum_result.get("summary", "")
        takeaways = sum_result.get("takeaways", [])
        metrics = sum_result.get("metrics", {})
        logger.info(f"Summarization complete. Summary length: {len(summary)}")

        # 2. Concept extraction (returns list of dicts with term and relevance)
        logger.info("Starting concept extraction...")
        concept_data = extractor.extract_concepts(text)
        concepts = [c["term"] for c in concept_data]
        logger.info(f"Extracted {len(concepts)} concepts")

        # 3. Quiz generation from full text and concepts
        logger.info("Starting quiz generation...")
        mcqs = quiz_gen.generate_mcqs(text, concepts, concepts, extractor=extractor)
        fill_in_the_blanks = quiz_gen.generate_fill_in_the_blanks(
            text, concepts, concepts, extractor=extractor
        )
        true_false = quiz_gen.generate_true_false(text, concepts)
        comprehension = quiz_gen.generate_comprehension(text, concepts)
        logger.info(
            f"Generated {len(mcqs)} MCQ, {len(fill_in_the_blanks)} FIB, "
            f"{len(true_false)} TF, {len(comprehension)} comprehension"
        )

        # 4. Generate explanations for each concept (passing extractor for dynamic definitions)
        logger.info("Starting explanation generation...")
        explanations = explanation_gen.generate_all_explanations(concepts, text, extractor=extractor)
        logger.info("Explanation generation complete")

        return {
            "summary": summary,
            "concepts": concepts, 
            "concept_details": concept_data, 
            "takeaways": takeaways,
            "quiz": {
                "fill_in_the_blanks": fill_in_the_blanks,
                "mcqs": mcqs,
                "true_false": true_false,
                "comprehension": comprehension,
            },
            "explanations": explanations,
            "metrics": metrics,
        }
    except Exception as e:
        logger.error(f"Error in process_logic: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

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
        logger.info(f"Received analyze request with text length: {len(request.text)}")
        return process_logic(request.text)
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in /analyze endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/analyze-file", response_model=ProcessResponse)
async def analyze_file(file: UploadFile = File(...)):
    file_location = None
    try:
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()  # Get position (file size)
        file.file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
        
        logger.info(f"Received analyze-file request for: {file.filename} ({file_size} bytes)")
        
        # Save uploaded file
        file_location = UPLOAD_DIR / file.filename
        with file_location.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text from file
        logger.info(f"Extracting text from: {file_location}")
        text = file_extractor.extract_text(str(file_location))
        
        # Validate extracted text
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file or file is empty")
        
        logger.info(f"Extracted {len(text)} characters from file")
        
        # Cleanup uploaded file after extraction
        os.remove(file_location)
        file_location = None  # Mark as cleaned up
        
        return process_logic(text)
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in /analyze-file endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")
    finally:
        # Ensure cleanup in case of error
        if file_location and os.path.exists(file_location):
            try:
                os.remove(file_location)
                logger.info(f"Cleaned up uploaded file: {file_location}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup file {file_location}: {cleanup_error}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
