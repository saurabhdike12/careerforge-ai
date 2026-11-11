"""
CareerForge AI — Pydantic Data Models / Schemas
All request/response models for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ─── Enums ───────────────────────────────────────────────────────────────────

class ExperienceLevel(str, Enum):
    FRESHER = "fresher"
    JUNIOR = "junior"          # 1–3 years
    MID = "mid"                # 3–6 years
    SENIOR = "senior"          # 6–10 years
    PRINCIPAL = "principal"    # 10+ years


class QuestionType(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"
    CASE_STUDY = "case_study"
    CULTURE_FIT = "culture_fit"
    HR = "hr"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


# ─── Request Models ───────────────────────────────────────────────────────────

class UserProfileRequest(BaseModel):
    """User profile to personalize the interview session."""
    name: str = Field(..., min_length=1, max_length=100, description="Candidate name")
    job_role: str = Field(..., min_length=2, max_length=100, description="Target job role")
    experience_level: ExperienceLevel
    years_of_experience: Optional[float] = Field(None, ge=0, le=50)
    target_company: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    skills: Optional[List[str]] = Field(default_factory=list)
    focus_areas: Optional[List[QuestionType]] = Field(
        default=[QuestionType.TECHNICAL, QuestionType.BEHAVIORAL]
    )
    difficulty: Optional[Difficulty] = Difficulty.MEDIUM
    resume_text: Optional[str] = Field(None, description="Extracted resume text")


class AnswerSubmissionRequest(BaseModel):
    """Candidate's answer to an interview question."""
    session_id: str
    question_id: str
    question_text: str
    answer_text: str = Field(..., min_length=10, description="Candidate's answer")
    time_taken_seconds: Optional[int] = Field(None, ge=0)


class ChatMessageRequest(BaseModel):
    """Free-form chat with the interview coach."""
    session_id: str
    message: str = Field(..., min_length=1)


class NextQuestionRequest(BaseModel):
    """Request the next interview question."""
    session_id: str
    question_type: Optional[QuestionType] = None
    difficulty: Optional[Difficulty] = None


# ─── Response Models ──────────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    relevance: float = Field(..., ge=0, le=10)
    star_method: float = Field(..., ge=0, le=10)
    technical_depth: float = Field(..., ge=0, le=10)
    communication: float = Field(..., ge=0, le=10)
    originality: float = Field(..., ge=0, le=10)
    overall: float = Field(..., ge=0, le=10)


class AnswerFeedback(BaseModel):
    score: ScoreBreakdown
    strengths: List[str]
    improvements: List[str]
    model_answer_hint: str
    follow_up_question: Optional[str] = None
    keywords_used: List[str]
    keywords_missed: List[str]


class InterviewQuestion(BaseModel):
    question_id: str
    question_text: str
    question_type: QuestionType
    difficulty: Difficulty
    context: Optional[str] = None          # Why this question was chosen
    tips: Optional[List[str]] = None       # Quick preparation tips
    expected_duration_minutes: Optional[int] = None


class SessionSummary(BaseModel):
    session_id: str
    candidate_name: str
    job_role: str
    total_questions: int
    answered_questions: int
    average_score: float
    top_strengths: List[str]
    top_weaknesses: List[str]
    topic_performance: Dict[str, float]   # e.g. {"technical": 7.5, "behavioral": 6.2}
    recommendation: str
    next_steps: List[str]
    created_at: datetime
    completed_at: Optional[datetime] = None


class SessionCreateResponse(BaseModel):
    session_id: str
    message: str
    first_question: InterviewQuestion
    total_planned_questions: int
    session_roadmap: List[Dict[str, Any]]  # Overview of planned question categories


class AnswerResponse(BaseModel):
    feedback: AnswerFeedback
    next_question: Optional[InterviewQuestion] = None
    session_progress: Dict[str, Any]


class ChatResponse(BaseModel):
    reply: str
    suggested_actions: Optional[List[str]] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    granite_model: str
    vector_store_status: str
    timestamp: datetime
