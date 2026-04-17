from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
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
from app.models import User

# Initialize database
try:
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    # If using SQLite, check if the directory is writable
    if str(engine.url).startswith("sqlite"):
        db_path = str(engine.url).replace("sqlite:///", "")
        db_dir = os.path.dirname(os.path.abspath(db_path)) if os.path.isabs(db_path) else os.getcwd()
        logger.error(f"SQLite DB Path: {db_path}")
        logger.error(f"Directory {db_dir} writable: {os.access(db_dir, os.W_OK)}")
        if os.path.exists(db_path):
            logger.error(f"File {db_path} writable: {os.access(db_path, os.W_OK)}")
    raise


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
        # Pre-check rate limit
        today = datetime.now().strftime("%Y-%m-%d")
        if user.last_analysis_date == today:
            if user.daily_analysis_count >= 5:
                logger.warning(f"User {user.email} hit daily rate limit")
                raise HTTPException(
                    status_code=429, 
                    detail="You have reached your daily limit of 5 lecture analyses. Please return tomorrow."
                )

    text = ExtractorService.normalize_pipeline_text(text.strip())
    # Minimum words stripped to 0 to fix strict ingestion limits
    
    logger.info(f"Processing text of length: {len(text)} characters via Gemini")
    
    api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key missing or not set in backend .env")
        
    try:
        # Single robust LLM call replacing sum, extraction, and quiz heuristics
        result = analyze_with_gemini(text, api_key)
        
        if "error" in result:
            logger.error(f"Analysis failed (all providers): {result['error']}")
            raise HTTPException(status_code=503, detail=result["error"])

        if user and db:
            # Increment credit ONLY on success
            today = datetime.now().strftime("%Y-%m-%d")
            if user.last_analysis_date == today:
                user.daily_analysis_count += 1
            else:
                user.last_analysis_date = today
                user.daily_analysis_count = 1
            db.commit()
            logger.info(f"User {user.email} analysis count incremented: {user.daily_analysis_count}/5")

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

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Synod.ai | API Node</title>
        <link rel="icon" type="image/svg+xml" href="/favicon.ico">
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Outfit', sans-serif; background: #09090b; color: #fafafa; }
            .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }
            .gradient-text { background: linear-gradient(135deg, #60a5fa 0%, #a855f7 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .animate-blob { animation: blob 7s infinite; }
            @keyframes blob {
                0% { transform: translate(0px, 0px) scale(1); }
                33% { transform: translate(30px, -50px) scale(1.1); }
                66% { transform: translate(-20px, 20px) scale(0.9); }
                100% { transform: translate(0px, 0px) scale(1); }
            }
        </style>
    </head>
    <body class="min-h-screen flex items-center justify-center overflow-hidden">
        <div class="fixed top-0 -left-4 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
        <div class="fixed top-0 -right-4 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
        <div class="fixed -bottom-8 left-20 w-72 h-72 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
        
        <div class="glass p-12 rounded-[2.5rem] max-w-xl w-full text-center relative z-10 shadow-2xl">
            <div class="mb-8 inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/20">
                <svg viewBox="0 0 24 24" fill="none" class="w-10 h-10 text-white" stroke="currentColor" stroke-width="2">
                    <path d="M9.5 2A1.5 1.5 0 0 0 8 3.5c0 .3.1.6.3.8-.1.2-.3.4-.3.7a1.5 1.5 0 0 0 1.5 1.5c.3 0 .6-.1.8-.3.2.1.4.3.7.3h.1a1.5 1.5 0 0 0 1.5-1.5c0-.3-.1-.6-.3-.8.1-.2.3-.4.3-.7a1.5 1.5 0 0 0-1.5-1.5h-1.1Zm2 6a4 4 0 0 0-4 4c0 1.1.4 2.1 1.1 2.9-.1.2-.1.4-.1.6 0 1.1.9 2 2 2h1a2 2 0 1 0 0-4h-1a1.5 1.5 0 0 1-1.5-1.5c0-.8.7-1.5 1.5-1.5h.5a1.5 1.5 0 0 1 0 3h-.5" />
                    <path d="M12 18.5a1.5 1.5 0 0 1-1.5 1.5c-.8 0-1.5-.7-1.5-1.5s.7-1.5 1.5-1.5 1.5.7 1.5 1.5Z" />
                    <path d="M12 13V9" />
                    <path d="M12 6a4 4 0 0 1 4 4c0 1.1-.4 2.1-1.1 2.9.1.2.1.4.1.6 0 1.1-.9 2-2 2h-1a2 2 0 1 1 0-4h1a1.5 1.5 0 0 0 1.5-1.5c0-.8-.7-1.5-1.5-1.5h-.5a1.5 1.5 0 0 0 0 3h.5" />
                </svg>
            </div>
            
            <h1 class="text-5xl font-extrabold mb-4 tracking-tight">
                <span class="gradient-text">Synod.ai</span>
            </h1>
            <p class="text-zinc-400 text-lg mb-10 font-medium">Intelligence Engine v2026.4 is Active</p>
            
            <div class="grid grid-cols-2 gap-4 text-left">
                <div class="p-4 rounded-2xl bg-white/5 border border-white/10">
                    <p class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Status</p>
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                        <span class="text-sm font-bold text-emerald-400">Operational</span>
                    </div>
                </div>
                <div class="p-4 rounded-2xl bg-white/5 border border-white/10">
                    <p class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Models</p>
                    <span class="text-sm font-bold text-blue-400">Gemini 3.1 & 2.5</span>
                </div>
            </div>
            
            <div class="mt-8 pt-8 border-t border-white/10">
                <p class="text-xs text-zinc-500 font-medium tracking-wide">
                    © 2026 Synod Assistants | Advanced Lecture Synthesis
                </p>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/favicon.ico")
async def favicon():
    icon_path = Path("brain-icon.svg")
    if icon_path.exists():
        return FileResponse(icon_path)
    return HTTPException(status_code=404)


@app.get("/user/usage")
def get_user_usage(user: User = Depends(get_current_user)):
    """Return the current user's daily analysis usage."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # If the user hasn't analyzed today, the stored count is effectively 0 for the UI
    count = user.daily_analysis_count if user.last_analysis_date == today else 0
    
    return {
        "daily_count": count,
        "daily_limit": 5,
        "remaining": max(0, 5 - count),
        "last_analysis": user.last_analysis_date
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
            if api_key:
                snippet = explanation_gen.gather_grounding_snippet(concept, text, extractor)

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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
