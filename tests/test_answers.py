"""
Tests for answer submission and feedback evaluation.
POST /api/v1/session/{session_id}/answer
"""

import pytest


GOOD_ANSWER = (
    "In my previous role at TechCorp, our API response times had degraded to over 2 seconds "
    "under peak load, causing a 15% drop in user retention. I was tasked with reducing latency "
    "below 500ms. I profiled the bottleneck to a single N+1 database query pattern in our "
    "order service. I refactored it using eager loading with SQLAlchemy joinedload, added a "
    "Redis caching layer with a 5-minute TTL, and deployed behind a CDN. Response time dropped "
    "to 180ms — a 91% improvement — and retention recovered within two weeks."
)

SHORT_ANSWER = "I worked on some projects."


class TestAnswerSubmission:
    def test_submit_answer_returns_200(self, started_session):
        client, session_id, question_id, question_text = started_session
        resp = client.post(f"/api/v1/session/{session_id}/answer", json={
            "session_id": session_id,
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": GOOD_ANSWER,
            "time_taken_seconds": 120,
        })
        assert resp.status_code == 200, resp.text

    def test_submit_answer_returns_feedback(self, started_session):
        client, session_id, question_id, question_text = started_session
        resp = client.post(f"/api/v1/session/{session_id}/answer", json={
            "session_id": session_id,
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": GOOD_ANSWER,
        })
        data = resp.json()
        assert "feedback" in data
        fb = data["feedback"]
        assert "score" in fb
        assert "strengths" in fb
        assert "improvements" in fb
        assert "model_answer_hint" in fb

    def test_feedback_score_has_all_dimensions(self, started_session):
        client, session_id, question_id, question_text = started_session
        resp = client.post(f"/api/v1/session/{session_id}/answer", json={
            "session_id": session_id,
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": GOOD_ANSWER,
        })
        score = resp.json()["feedback"]["score"]
        for dim in ["relevance", "star_method", "technical_depth", "communication", "originality", "overall"]:
            assert dim in score, f"Missing dimension: {dim}"
            assert 0 <= score[dim] <= 10, f"Score out of range for {dim}: {score[dim]}"

    def test_submit_answer_returns_session_progress(self, started_session):
        client, session_id, question_id, question_text = started_session
        resp = client.post(f"/api/v1/session/{session_id}/answer", json={
            "session_id": session_id,
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": GOOD_ANSWER,
        })
        progress = resp.json()["session_progress"]
        assert "answered" in progress
        assert "total" in progress
        assert "progress_pct" in progress
        assert "average_score" in progress
        assert progress["answered"] == 1

    def test_submit_answer_progress_increments(self, started_session):
        client, session_id, question_id, question_text = started_session
        # Submit first answer
        resp1 = client.post(f"/api/v1/session/{session_id}/answer", json={
            "session_id": session_id,
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": GOOD_ANSWER,
        })
        p1 = resp1.json()["session_progress"]
        assert p1["answered"] == 1

        # Submit second answer if next question is available
        next_q = resp1.json().get("next_question")
        if next_q:
            resp2 = client.post(f"/api/v1/session/{session_id}/answer", json={
                "session_id": session_id,
                "question_id": next_q["question_id"],
                "question_text": next_q["question_text"],
                "answer_text": GOOD_ANSWER,
            })
            p2 = resp2.json()["session_progress"]
            assert p2["answered"] == 2

    def test_short_answer_rejected_by_validation(self, started_session):
        client, session_id, question_id, question_text = started_session
        resp = client.post(f"/api/v1/session/{session_id}/answer", json={
            "session_id": session_id,
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": "hi",   # less than 10 chars — Pydantic min_length
        })
        assert resp.status_code == 422

    def test_invalid_session_id_returns_404(self, app_client):
        resp = app_client.post("/api/v1/session/nonexistent-id/answer", json={
            "session_id": "nonexistent-id",
            "question_id": "some-q-id",
            "question_text": "Tell me about yourself.",
            "answer_text": GOOD_ANSWER,
        })
        assert resp.status_code == 404

    def test_feedback_contains_keywords(self, started_session):
        client, session_id, question_id, question_text = started_session
        resp = client.post(f"/api/v1/session/{session_id}/answer", json={
            "session_id": session_id,
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": GOOD_ANSWER,
        })
        fb = resp.json()["feedback"]
        assert "keywords_used" in fb
        assert "keywords_missed" in fb
        assert isinstance(fb["keywords_used"], list)
        assert isinstance(fb["keywords_missed"], list)
