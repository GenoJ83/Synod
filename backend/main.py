from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
import os

from app.nlp.summarizer import Summarizer
from app.nlp.extractor import ConceptExtractor
from app.nlp.quiz_gen import QuizGenerator

app = FastAPI(title="Synod API")

# Enable CORS for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize NLP modules
summarizer = Summarizer(model_name="t5-small")
extractor = ConceptExtractor()
quiz_gen = QuizGenerator()

class ProcessRequest(BaseModel):
    text: str

class ProcessResponse(BaseModel):
    summary: str
    concepts: List[str]
    quiz: Dict

@app.get("/")
async def root():
    return {"message": "Welcome to Synod API"}

@app.post("/analyze", response_model=ProcessResponse)
async def analyze_text(request: ProcessRequest):
    try:
        text = request.text
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        summary = summarizer.summarize(text)
        concepts = extractor.extract_concepts(text)
        
        # For simplicity, we'll generate both types of quiz questions
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
