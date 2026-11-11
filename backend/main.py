"""
CareerForge AI — FastAPI Application Entry Point
Main API server with all interview training endpoints.
"""

import uuid
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.models.schemas import (
    UserProfileRequest, AnswerSubmissionRequest, ChatMessageRequest,
    NextQuestionRequest, SessionCreateResponse, AnswerResponse,
    ChatResponse, HealthResponse, SessionSummary
)
from backend.agents.interview_agent import InterviewAgent
from backend.rag.pipeline import get_rag_pipeline, CareerForgeRAGPipeline
from backend.parsers.resume_parser import ResumeParser
from backend.database.session_db import get_session_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

# ─── In-memory session store (production: use Redis) ──────────────────────────
# Maps session_id → InterviewAgent instance
_active_sessions: Dict[str, InterviewAgent] = {}

# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, clean up on shutdown."""
    logger.info("🚀 CareerForge AI starting up...")
    settings = get_settings()
    
    # Initialize RAG pipeline (connects to IBM watsonx.ai)
    try:
        pipeline = get_rag_pipeline()
        logger.info(f"✅ IBM Granite ({settings.granite_model_id}) connected.")
    except Exception as e:
        logger.error(f"⚠️  RAG pipeline init failed: {e}. Running in degraded mode.")
    
    # Initialize database
    try:
        get_session_db()
        logger.info("✅ Session database ready.")
    except Exception as e:
        logger.error(f"⚠️  Database init failed: {e}")
    
    logger.info("✅ CareerForge AI ready to serve!")
    yield
    logger.info("👋 CareerForge AI shutting down.")


# ─── FastAPI Application ───────────────────────────────────────────────────────

app = FastAPI(
    title="CareerForge AI",
    description="Intelligent Interview Trainer Agent powered by IBM Granite & RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Dependency Injection ──────────────────────────────────────────────────────

def get_pipeline() -> CareerForgeRAGPipeline:
    return get_rag_pipeline()


def get_agent(session_id: str) -> InterviewAgent:
    agent = _active_sessions.get(session_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found or expired.")
    return agent


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """System health check — verifies IBM Granite and vector store connectivity."""
    settings = get_settings()
    try:
        pipeline = get_rag_pipeline()
        vs_status = "healthy" if pipeline.is_ready else "degraded"
    except Exception:
        vs_status = "unavailable"
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        granite_model=settings.granite_model_id,
        vector_store_status=vs_status,
        timestamp=datetime.utcnow(),
    )


@app.post("/api/v1/session/start", response_model=SessionCreateResponse, tags=["Interview Session"])
async def start_session(
    profile: UserProfileRequest,
    pipeline: CareerForgeRAGPipeline = Depends(get_pipeline),
):
    """
    Start a new interview session.
    
    Creates a personalized interview plan based on the candidate's profile,
    experience level, and target job role using IBM Granite RAG.
    """
    session_id = str(uuid.uuid4())
    
    agent = InterviewAgent(
        session_id=session_id,
        profile=profile,
        rag_pipeline=pipeline,
    )
    
    # Generate full session plan
    questions = agent.generate_session_plan()
    
    # Persist session
    _active_sessions[session_id] = agent
    
    db = get_session_db()
    db.create_session(
        session_id=session_id,
        candidate_name=profile.name,
        job_role=profile.job_role,
        experience_level=profile.experience_level.value,
        profile=profile.model_dump(mode="json"),
    )
    db.save_questions(
        session_id=session_id,
        questions_json=json.dumps([q.model_dump(mode="json") for q in questions]),
        total=len(questions),
    )
    
    first_question = agent.get_first_question()
    
    roadmap = [
        {"index": i + 1, "type": q.question_type.value, "difficulty": q.difficulty.value}
        for i, q in enumerate(questions)
    ]
    
    logger.info(f"✅ Session {session_id} started for {profile.name} — {profile.job_role}")
    
    return SessionCreateResponse(
        session_id=session_id,
        message=f"Welcome to CareerForge AI, {profile.name}! Your personalized {profile.job_role} interview session is ready. I've prepared {len(questions)} tailored questions based on your {profile.experience_level.value}-level profile.",
        first_question=first_question,
        total_planned_questions=len(questions),
        session_roadmap=roadmap,
    )


@app.post("/api/v1/session/{session_id}/upload-resume", tags=["Interview Session"])
async def upload_resume(
    session_id: str,
    file: UploadFile = File(...),
):
    """
    Upload a resume PDF/DOCX to personalize the interview session.
    The resume text is parsed and added to the RAG context.
    Supports PDF (via Docling), DOCX, and TXT formats.
    """
    agent = get_agent(session_id)
    
    content = await file.read()
    parser = ResumeParser()
    
    try:
        resume_text = parser.parse_bytes(content, file.filename)
        detected_skills = parser.extract_skills_hint(resume_text)
        
        # Update agent profile with resume data
        agent.profile.resume_text = resume_text[:3000]  # Limit context size
        if detected_skills:
            agent.profile.skills = list(set(agent.profile.skills or []) | set(detected_skills))
        
        return {
            "status": "success",
            "message": f"Resume parsed successfully. Detected {len(detected_skills)} skills.",
            "detected_skills": detected_skills,
            "character_count": len(resume_text),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {e}")


@app.post("/api/v1/session/{session_id}/answer", response_model=AnswerResponse, tags=["Interview"])
async def submit_answer(
    session_id: str,
    submission: AnswerSubmissionRequest,
):
    """
    Submit an answer to a question and receive AI-powered feedback.
    
    Uses IBM Granite to evaluate the answer against STAR method,
    technical accuracy, and communication quality.
    Returns detailed scores, strengths, improvements, and a model answer hint.
    """
    agent = get_agent(session_id)
    
    feedback = agent.evaluate_answer(
        question_id=submission.question_id,
        question_text=submission.question_text,
        answer_text=submission.answer_text,
        time_taken_seconds=submission.time_taken_seconds,
    )
    
    next_question = agent.get_next_question()
    progress = agent.get_progress()
    
    # Persist progress
    db = get_session_db()
    db.update_progress(
        session_id=session_id,
        answered=progress["answered"],
        avg_score=progress["average_score"],
        answers_json=json.dumps(agent.answers),
    )
    
    # Auto-complete session if all questions answered
    if progress["is_complete"]:
        summary = agent.get_session_summary()
        db.complete_session(
            session_id=session_id,
            summary_json=summary.model_dump_json(),
        )
    
    return AnswerResponse(
        feedback=feedback,
        next_question=next_question,
        session_progress=progress,
    )


@app.get("/api/v1/session/{session_id}/next-question", tags=["Interview"])
async def get_next_question(session_id: str):
    """Get the next question without submitting an answer (for skipping)."""
    agent = get_agent(session_id)
    question = agent.get_next_question()
    if not question:
        return {"message": "Session complete — no more questions.", "question": None}
    return {"question": question.model_dump()}


@app.get("/api/v1/session/{session_id}/summary", response_model=SessionSummary, tags=["Interview"])
async def get_session_summary(session_id: str):
    """Get the comprehensive session summary with analytics and recommendations."""
    agent = get_agent(session_id)
    summary = agent.get_session_summary()
    
    db = get_session_db()
    db.complete_session(session_id, summary.model_dump_json())
    
    return summary


@app.get("/api/v1/session/{session_id}/progress", tags=["Interview"])
async def get_progress(session_id: str):
    """Get real-time session progress stats."""
    agent = get_agent(session_id)
    return agent.get_progress()


@app.post("/api/v1/session/{session_id}/chat", response_model=ChatResponse, tags=["Interview Coach"])
async def chat_with_coach(
    session_id: str,
    message: ChatMessageRequest,
    pipeline: CareerForgeRAGPipeline = Depends(get_pipeline),
):
    """
    Chat with the AI interview coach for guidance, tips, and preparation advice.
    Powered by IBM Granite with role-specific RAG context.
    """
    agent = _active_sessions.get(session_id)
    job_role = agent.profile.job_role if agent else "the target role"
    
    reply = pipeline.get_coaching_advice(
        question=message.message,
        job_role=job_role,
    )
    
    suggested_actions = [
        "Practice this answer out loud",
        "Review related questions in your study plan",
        "Request a follow-up question on this topic",
    ]
    
    return ChatResponse(reply=reply, suggested_actions=suggested_actions)


@app.get("/api/v1/sessions", tags=["System"])
async def list_recent_sessions():
    """List the 10 most recent interview sessions."""
    db = get_session_db()
    records = db.list_sessions(limit=10)
    return [
        {
            "session_id": r.session_id,
            "candidate_name": r.candidate_name,
            "job_role": r.job_role,
            "status": r.status,
            "average_score": r.average_score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "CareerForge AI",
        "tagline": "Your IBM Granite-powered Interview Coach",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }
