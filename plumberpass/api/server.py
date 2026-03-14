"""
PlumberPass API Server
========================
Serves exam questions to the Ohverlay exam reviewer overlay.

Endpoints:
  GET  /api/v1/questions/random     - Get random question(s)
  GET  /api/v1/questions/overlay    - Get smart-selected questions for overlay mode
  POST /api/v1/questions/answer     - Record an answer
  GET  /api/v1/subjects             - List subjects
  GET  /api/v1/stats                - Study statistics
  POST /api/v1/pdf/upload           - Upload PDF for extraction
  GET  /api/v1/pdf/status/{id}      - Check extraction status

Run:
  uvicorn plumberpass.api.server:app --port 8401
"""

from fastapi import FastAPI, Query, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import time
import tempfile

from plumberpass.api.question_bank import QuestionBank

app = FastAPI(
    title="PlumberPass API",
    description="Philippine Master Plumber Exam Reviewer - Question Bank API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow overlay HTML files
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize question bank
bank = QuestionBank()


class AnswerRequest(BaseModel):
    question_id: int
    was_correct: bool
    time_taken: float = 0


# ─── Questions ───

@app.get("/api/v1/questions/random")
async def random_question(
    subject: Optional[str] = Query(None),
    difficulty: Optional[int] = Query(None),
    count: int = Query(1, ge=1, le=20),
):
    """Get random question(s)."""
    questions = []
    exclude = []
    for _ in range(count):
        q = bank.get_random_question(subject, difficulty, exclude)
        if q:
            questions.append(q)
            exclude.append(q["id"])
    return {"questions": questions, "count": len(questions)}


@app.get("/api/v1/questions/overlay")
async def overlay_questions(
    subject: Optional[str] = Query(None),
    count: int = Query(10, ge=1, le=50),
    smart: bool = Query(True),
):
    """
    Get questions optimized for overlay mode.
    Smart mode prioritizes questions user struggles with.
    """
    questions = bank.get_questions_for_overlay(count, subject, smart)
    return {"questions": questions, "count": len(questions)}


@app.post("/api/v1/questions/answer")
async def record_answer(req: AnswerRequest):
    """Record a user's answer to a question."""
    bank.record_answer(req.question_id, req.was_correct, req.time_taken)
    return {"status": "recorded"}


# ─── Subjects ───

@app.get("/api/v1/subjects")
async def list_subjects():
    return {"subjects": bank.get_subjects()}


# ─── Stats ───

@app.get("/api/v1/stats")
async def get_stats(subject: Optional[str] = Query(None)):
    return bank.get_stats(subject)


# ─── PDF Upload ───

@app.post("/api/v1/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF reviewer for question extraction."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")

    # Save to temp location
    pdf_dir = os.path.join(os.path.expanduser("~"), ".ohverlay", "plumberpass_pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    filepath = os.path.join(pdf_dir, file.filename)

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    # Start extraction (synchronous for now, async with job queue later)
    try:
        from plumberpass.pipeline.pdf_extractor import PlumberPassPipeline
        pipeline = PlumberPassPipeline()
        result = pipeline.process_pdf(filepath)
        return {
            "status": "done",
            "filename": file.filename,
            "questions_extracted": result["questions_extracted"],
            "questions_added": result["questions_added"],
            "pages_processed": result["pages_processed"],
            "duration": result["duration_seconds"],
        }
    except Exception as e:
        return {
            "status": "error",
            "filename": file.filename,
            "error": str(e),
        }


# ─── Health ───

@app.get("/api/v1/health")
async def health():
    return {
        "status": "alive",
        "service": "PlumberPass",
        "total_questions": bank.get_total_questions(),
        "timestamp": int(time.time()),
    }


@app.on_event("startup")
async def startup():
    total = bank.get_total_questions()
    print(f"PlumberPass API started - {total} questions in bank")
