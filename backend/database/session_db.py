"""
CareerForge AI — Session Database
SQLAlchemy + SQLite for persistent session storage.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.config import get_settings

logger = logging.getLogger(__name__)
Base = declarative_base()


# ─── ORM Models ───────────────────────────────────────────────────────────────

class SessionRecord(Base):
    __tablename__ = "sessions"

    session_id = Column(String(36), primary_key=True)
    candidate_name = Column(String(100), nullable=False)
    job_role = Column(String(100), nullable=False)
    experience_level = Column(String(20), nullable=False)
    status = Column(String(20), default="active")
    total_questions = Column(Integer, default=0)
    answered_questions = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    profile_json = Column(Text)          # Full UserProfileRequest serialized
    questions_json = Column(Text)        # List of generated questions
    answers_json = Column(Text)          # List of answers with feedback
    summary_json = Column(Text)          # Final session summary
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


# ─── Database Manager ──────────────────────────────────────────────────────────

class SessionDatabase:
    """Manages interview session persistence."""

    def __init__(self):
        settings = get_settings()
        self._engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},  # SQLite only
        )
        Base.metadata.create_all(self._engine)
        self._SessionFactory = sessionmaker(bind=self._engine)
        logger.info("✅ Session database initialized.")

    def _get_session(self) -> Session:
        return self._SessionFactory()

    def create_session(
        self,
        session_id: str,
        candidate_name: str,
        job_role: str,
        experience_level: str,
        profile: Dict[str, Any],
    ) -> SessionRecord:
        with self._get_session() as db:
            record = SessionRecord(
                session_id=session_id,
                candidate_name=candidate_name,
                job_role=job_role,
                experience_level=experience_level,
                status="active",
                profile_json=json.dumps(profile),
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        with self._get_session() as db:
            return db.query(SessionRecord).filter(
                SessionRecord.session_id == session_id
            ).first()

    def update_progress(
        self,
        session_id: str,
        answered: int,
        avg_score: float,
        answers_json: str,
    ):
        with self._get_session() as db:
            record = db.query(SessionRecord).filter(
                SessionRecord.session_id == session_id
            ).first()
            if record:
                record.answered_questions = answered
                record.average_score = avg_score
                record.answers_json = answers_json
                record.updated_at = datetime.utcnow()
                db.commit()

    def complete_session(self, session_id: str, summary_json: str):
        with self._get_session() as db:
            record = db.query(SessionRecord).filter(
                SessionRecord.session_id == session_id
            ).first()
            if record:
                record.status = "completed"
                record.completed_at = datetime.utcnow()
                record.summary_json = summary_json
                db.commit()

    def save_questions(self, session_id: str, questions_json: str, total: int):
        with self._get_session() as db:
            record = db.query(SessionRecord).filter(
                SessionRecord.session_id == session_id
            ).first()
            if record:
                record.questions_json = questions_json
                record.total_questions = total
                db.commit()

    def list_sessions(self, limit: int = 10) -> list:
        with self._get_session() as db:
            return db.query(SessionRecord).order_by(
                SessionRecord.created_at.desc()
            ).limit(limit).all()


# ─── Singleton ────────────────────────────────────────────────────────────────

_db_instance: Optional[SessionDatabase] = None


def get_session_db() -> SessionDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = SessionDatabase()
    return _db_instance
