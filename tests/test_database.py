"""
Tests for the session database (SQLite + SQLAlchemy).
Uses an in-memory SQLite DB — no file system side effects.
"""

import pytest
import uuid
from unittest.mock import patch

from backend.database.session_db import SessionDatabase


@pytest.fixture
def db(tmp_path):
    """Each test gets a fresh in-memory database."""
    with patch("backend.database.session_db.get_settings") as mock_settings:
        mock_settings.return_value = type("S", (), {
            "database_url": f"sqlite:///{tmp_path}/test.db"
        })()
        yield SessionDatabase()


@pytest.fixture
def sample_session_data():
    return {
        "session_id": str(uuid.uuid4()),
        "candidate_name": "Alice Smith",
        "job_role": "Product Manager",
        "experience_level": "senior",
        "profile": {"name": "Alice Smith", "job_role": "Product Manager"},
    }


class TestSessionDatabase:
    def test_create_session(self, db, sample_session_data):
        record = db.create_session(**sample_session_data)
        assert record is not None

    def test_get_session_returns_record(self, db, sample_session_data):
        db.create_session(**sample_session_data)
        record = db.get_session(sample_session_data["session_id"])
        assert record is not None
        assert record.candidate_name == "Alice Smith"

    def test_get_nonexistent_session_returns_none(self, db):
        record = db.get_session("nonexistent-id")
        assert record is None

    def test_update_progress(self, db, sample_session_data):
        db.create_session(**sample_session_data)
        db.update_progress(
            session_id=sample_session_data["session_id"],
            answered=3,
            avg_score=7.5,
            answers_json="[]",
        )
        record = db.get_session(sample_session_data["session_id"])
        assert record.answered_questions == 3
        assert record.average_score == 7.5

    def test_complete_session(self, db, sample_session_data):
        db.create_session(**sample_session_data)
        db.complete_session(
            session_id=sample_session_data["session_id"],
            summary_json='{"average_score": 8.0}',
        )
        record = db.get_session(sample_session_data["session_id"])
        assert record.status == "completed"
        assert record.completed_at is not None

    def test_save_questions(self, db, sample_session_data):
        db.create_session(**sample_session_data)
        db.save_questions(
            session_id=sample_session_data["session_id"],
            questions_json='[{"id": "q1"}]',
            total=9,
        )
        record = db.get_session(sample_session_data["session_id"])
        assert record.total_questions == 9

    def test_list_sessions_returns_created(self, db, sample_session_data):
        db.create_session(**sample_session_data)
        records = db.list_sessions(limit=10)
        ids = [r.session_id for r in records]
        assert sample_session_data["session_id"] in ids

    def test_list_sessions_respects_limit(self, db):
        for i in range(5):
            db.create_session(
                session_id=str(uuid.uuid4()),
                candidate_name=f"User {i}",
                job_role="Engineer",
                experience_level="mid",
                profile={},
            )
        records = db.list_sessions(limit=3)
        assert len(records) <= 3

    def test_new_session_default_status_is_active(self, db, sample_session_data):
        db.create_session(**sample_session_data)
        record = db.get_session(sample_session_data["session_id"])
        assert record.status == "active"
