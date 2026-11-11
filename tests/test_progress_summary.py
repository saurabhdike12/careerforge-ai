"""
Tests for session progress tracking and summary generation.
GET /api/v1/session/{id}/progress
GET /api/v1/session/{id}/summary
"""

import pytest


GOOD_ANSWER = (
    "In my previous role I led the migration of our monolithic application to microservices. "
    "I identified 3 tightly coupled services, designed the new architecture using domain-driven "
    "design principles, coordinated with 4 other engineers, and delivered the migration on time. "
    "The result was a 60% improvement in deployment frequency and a 40% reduction in incident rate."
)


class TestProgress:
    def test_get_progress_returns_200(self, started_session):
        client, session_id, _, _ = started_session
        resp = client.get(f"/api/v1/session/{session_id}/progress")
        assert resp.status_code == 200

    def test_progress_starts_at_zero(self, started_session):
        client, session_id, _, _ = started_session
        resp = client.get(f"/api/v1/session/{session_id}/progress")
        data = resp.json()
        assert data["answered"] == 0
        assert data["progress_pct"] == 0
        assert data["is_complete"] is False

    def test_progress_total_matches_session_plan(self, app_client, sample_profile):
        start = app_client.post("/api/v1/session/start", json=sample_profile).json()
        session_id = start["session_id"]
        planned = start["total_planned_questions"]

        prog = app_client.get(f"/api/v1/session/{session_id}/progress").json()
        assert prog["total"] == planned

    def test_progress_updates_after_answer(self, started_session):
        client, session_id, question_id, question_text = started_session
        client.post(f"/api/v1/session/{session_id}/answer", json={
            "session_id": session_id,
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": GOOD_ANSWER,
        })
        prog = client.get(f"/api/v1/session/{session_id}/progress").json()
        assert prog["answered"] == 1
        assert prog["average_score"] > 0

    def test_invalid_session_progress_returns_404(self, app_client):
        resp = app_client.get("/api/v1/session/bad-id/progress")
        assert resp.status_code == 404


class TestSummary:
    def test_get_summary_returns_200(self, started_session):
        client, session_id, _, _ = started_session
        resp = client.get(f"/api/v1/session/{session_id}/summary")
        assert resp.status_code == 200

    def test_summary_contains_required_fields(self, started_session):
        client, session_id, _, _ = started_session
        data = client.get(f"/api/v1/session/{session_id}/summary").json()
        required = [
            "session_id", "candidate_name", "job_role",
            "total_questions", "answered_questions", "average_score",
            "top_strengths", "top_weaknesses", "topic_performance",
            "recommendation", "next_steps", "created_at",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_summary_session_id_matches(self, started_session):
        client, session_id, _, _ = started_session
        data = client.get(f"/api/v1/session/{session_id}/summary").json()
        assert data["session_id"] == session_id

    def test_summary_candidate_name_matches(self, started_session, sample_profile):
        client, session_id, _, _ = started_session
        data = client.get(f"/api/v1/session/{session_id}/summary").json()
        assert data["candidate_name"] == sample_profile["name"]

    def test_summary_job_role_matches(self, started_session, sample_profile):
        client, session_id, _, _ = started_session
        data = client.get(f"/api/v1/session/{session_id}/summary").json()
        assert data["job_role"] == sample_profile["job_role"]

    def test_summary_score_is_valid_after_answers(self, started_session):
        client, session_id, question_id, question_text = started_session
        # Answer one question first
        client.post(f"/api/v1/session/{session_id}/answer", json={
            "session_id": session_id,
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": GOOD_ANSWER,
        })
        data = client.get(f"/api/v1/session/{session_id}/summary").json()
        assert 0 <= data["average_score"] <= 10

    def test_summary_recommendation_is_non_empty(self, started_session):
        client, session_id, _, _ = started_session
        data = client.get(f"/api/v1/session/{session_id}/summary").json()
        assert len(data["recommendation"]) > 10

    def test_summary_next_steps_is_list(self, started_session):
        client, session_id, _, _ = started_session
        data = client.get(f"/api/v1/session/{session_id}/summary").json()
        assert isinstance(data["next_steps"], list)

    def test_invalid_session_summary_returns_404(self, app_client):
        resp = app_client.get("/api/v1/session/bad-id/summary")
        assert resp.status_code == 404
