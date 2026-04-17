from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
import os
import shutil
import asyncio
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

# Hugging Face Hub defaults to a 10s read timeout; slow or flaky networks see endless retries.
# Must be set before importing transformers / sentence_transformers.
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "60")

from app.nlp.extractor import ConceptExtractor
from app.nlp.explanation_generator import ExplanationGenerator
from app.nlp.gemini_concept_explain import _gemini_enabled, explain_concept_with_gemini
from app.nlp.gemini_analyzer import analyze_with_gemini
from app.nlp.notes_chat import (
    build_retrieved_notes_context,
    gemini_notes_chat_reply,
    notes_chat_enabled,
)
from app.ingestion.extractor_service import ExtractorService
from app.auth import router as auth_router
from app.auth.dependencies import get_current_user
from sqlalchemy.orm import Session
from fastapi import Depends
from datetime import datetime
from app.database import get_db, engine, Base
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
# Removing Summarizer & QuizGenerator to mitigate high CPU/RAM layout and model flakiness.
# summarizer = Summarizer(model_name=os.getenv("SUMMARY_MODEL", "sshleifer/distilbart-cnn-12-6"))
extractor = ConceptExtractor(model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
# quiz_gen = QuizGenerator()
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
    source_text: Optional[str] = Field(
        default=None,
        description="Normalized lecture text for POST /explain-concept when the user opens a concept.",
    )


class ExplainConceptRequest(BaseModel):
    text: str
    concept: str


class ConceptExplanationResponse(BaseModel):
    term: str
    definition: str
    context: str


class NotesChatTurn(BaseModel):
    role: str
    content: str = Field(..., min_length=1, max_length=6000)

    @field_validator("role")
    @classmethod
    def _normalize_role(cls, v: str) -> str:
        r = (v or "").strip().lower()
        if r not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        return r


class NotesChatRequest(BaseModel):
    source_text: str = Field(..., min_length=50)
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[NotesChatTurn] = Field(default_factory=list)
    summary_hint: Optional[str] = Field(default=None, max_length=8000)


class NotesChatResponse(BaseModel):
    reply: str


def process_logic(text: str, user: any = None, db: Session = None):
    """Process text through the Gemini NLP pipeline natively with rate limiting."""
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    if user and db:
        # Rate limiting logic
        today = datetime.now().strftime("%Y-%m-%d")
        if user.last_analysis_date == today:
            if user.daily_analysis_count >= 5:
                logger.warning(f"User {user.email} hit daily rate limit")
                raise HTTPException(
                    status_code=429, 
                    detail="You have reached your daily limit of 5 lecture analyses. Please return tomorrow."
                )
            user.daily_analysis_count += 1
        else:
            user.last_analysis_date = today
            user.daily_analysis_count = 1
        
        db.commit()
        logger.info(f"User {user.email} analysis count: {user.daily_analysis_count}/5")

    text = ExtractorService.normalize_pipeline_text(text.strip())
    # Minimum words stripped to 0 to fix strict ingestion limits
    
    logger.info(f"Processing text of length: {len(text)} characters via Gemini")
    
    api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key missing or not set in backend .env")
        
    try:
        # Single robust LLM call replacing sum, extraction, and quiz heuristics
        result = analyze_with_gemini(text, api_key)
        quiz = result.get("quiz", {})
        
        return {
            "summary": result.get("summary", "No summary generated."),
            "concepts": result.get("concepts", []),
            "concept_details": result.get("concept_details", []),
            "takeaways": result.get("takeaways", []),
            "quiz": {
                "fill_in_the_blanks": quiz.get("fill_in_the_blanks", []),
                "mcqs": quiz.get("mcqs", []),
                "true_false": quiz.get("true_false", []),
                "comprehension": quiz.get("comprehension", []),
            },
            "explanations": None,
            "metrics": {},
            "source_text": text,
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

@app.post("/explain-concept", response_model=ConceptExplanationResponse)
async def explain_concept(request: ExplainConceptRequest):
    """Generate definition + lecture context for one concept (on demand)."""
    raw = (request.text or "").strip()
    concept = (request.concept or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Text is required")
    if not concept:
        raise HTTPException(status_code=400, detail="Concept is required")
    text = ExtractorService.normalize_pipeline_text(raw)
    if len(text) < 50:
        raise HTTPException(status_code=400, detail="Text must be at least 50 characters")
    try:
        baseline = explanation_gen.generate_concept_detail(concept, text, extractor=extractor)
        if _gemini_enabled():
            api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
            snippet = explanation_gen.gather_grounding_snippet(concept, text, extractor)
            if api_key and snippet.strip():

                def _gemini_call():
                    return explain_concept_with_gemini(
                        concept=concept, snippet=snippet, api_key=api_key
                    )

                improved = await asyncio.to_thread(_gemini_call)
                if improved and improved.get("definition"):
                    logger.info("explain-concept: using Gemini for term=%r", concept[:48])
                    return improved
        return baseline
    except Exception as e:
        logger.error(f"Error in /explain-concept: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")


@app.post("/chat/notes", response_model=NotesChatResponse)
async def chat_notes(request: NotesChatRequest):
    """
    Tutor-style Q&A grounded in the student's uploaded notes (requires Gemini API key).
    """
    if len(request.history) > 24:
        raise HTTPException(status_code=400, detail="At most 24 prior turns are supported.")
    if not notes_chat_enabled():
        raise HTTPException(
            status_code=503,
            detail="Notes chat is disabled (set USE_NOTES_CHAT=true) or GOOGLE_API_KEY is not configured.",
        )
    raw = (request.source_text or "").strip()
    if len(raw) > 600_000:
        raw = raw[:600_000]
    text = ExtractorService.normalize_pipeline_text(raw)
    if len(text) < 50:
        raise HTTPException(status_code=400, detail="Notes text is too short after normalization.")

    api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    hint = (request.summary_hint or "").strip()

    def _run() -> str:
        ctx = build_retrieved_notes_context(text, request.message.strip(), extractor)
        hist = [{"role": t.role, "content": t.content} for t in request.history]
        return gemini_notes_chat_reply(
            notes_context=ctx,
            summary_hint=hint,
            question=request.message.strip(),
            history=hist,
            api_key=api_key,
        )

    try:
        reply = await asyncio.to_thread(_run)
        return NotesChatResponse(reply=reply)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("chat/notes: %s", e)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Chat failed.") from e


@app.post("/analyze", response_model=ProcessResponse)
async def analyze_text(request: ProcessRequest, current_user: any = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        logger.info(f"Received analyze request from {current_user.email} with text length: {len(request.text)}")
        return process_logic(request.text, user=current_user, db=db)
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in /analyze endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/analyze-file", response_model=ProcessResponse)
async def analyze_file(file: UploadFile = File(...), current_user: any = Depends(get_current_user), db: Session = Depends(get_db)):
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
        
        return process_logic(text, user=current_user, db=db)
        
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
