"""
Tests for session creation (POST /api/v1/session/start).
Validates profile handling, question generation, and session roadmap.
"""

import pytest


class TestSessionStart:
    def test_start_session_returns_200(self, app_client, sample_profile):
        resp = app_client.post("/api/v1/session/start", json=sample_profile)
        assert resp.status_code == 200

    def test_start_session_returns_session_id(self, app_client, sample_profile):
        resp = app_client.post("/api/v1/session/start", json=sample_profile)
        data = resp.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID format

    def test_start_session_contains_welcome_message(self, app_client, sample_profile):
        resp = app_client.post("/api/v1/session/start", json=sample_profile)
        data = resp.json()
        assert "message" in data
        assert sample_profile["name"] in data["message"]
        assert sample_profile["job_role"] in data["message"]

    def test_start_session_returns_first_question(self, app_client, sample_profile):
        resp = app_client.post("/api/v1/session/start", json=sample_profile)
        data = resp.json()
        fq = data["first_question"]
        assert "question_id" in fq
        assert "question_text" in fq
        assert len(fq["question_text"]) > 10
        assert "question_type" in fq
        assert "difficulty" in fq

    def test_start_session_returns_roadmap(self, app_client, sample_profile):
        resp = app_client.post("/api/v1/session/start", json=sample_profile)
        data = resp.json()
        assert "session_roadmap" in data
        assert isinstance(data["session_roadmap"], list)
        assert len(data["session_roadmap"]) > 0
        for item in data["session_roadmap"]:
            assert "type" in item
            assert "difficulty" in item

    def test_start_session_total_questions_matches_roadmap(self, app_client, sample_profile):
        resp = app_client.post("/api/v1/session/start", json=sample_profile)
        data = resp.json()
        assert data["total_planned_questions"] == len(data["session_roadmap"])

    def test_start_session_requires_name(self, app_client, sample_profile):
        bad = {**sample_profile, "name": ""}
        resp = app_client.post("/api/v1/session/start", json=bad)
        assert resp.status_code == 422  # Pydantic validation error

    def test_start_session_requires_job_role(self, app_client, sample_profile):
        bad = {**sample_profile, "job_role": ""}
        resp = app_client.post("/api/v1/session/start", json=bad)
        assert resp.status_code == 422

    def test_start_session_invalid_experience_level(self, app_client, sample_profile):
        bad = {**sample_profile, "experience_level": "god_tier"}
        resp = app_client.post("/api/v1/session/start", json=bad)
        assert resp.status_code == 422

    def test_start_session_all_experience_levels(self, app_client, sample_profile):
        for level in ["fresher", "junior", "mid", "senior", "principal"]:
            profile = {**sample_profile, "experience_level": level}
            resp = app_client.post("/api/v1/session/start", json=profile)
            assert resp.status_code == 200, f"Failed for level: {level}"

    def test_start_session_without_optional_fields(self, app_client):
        minimal = {
            "name": "Min User",
            "job_role": "Data Analyst",
            "experience_level": "junior",
        }
        resp = app_client.post("/api/v1/session/start", json=minimal)
        assert resp.status_code == 200

    def test_two_sessions_have_different_ids(self, app_client, sample_profile):
        r1 = app_client.post("/api/v1/session/start", json=sample_profile).json()
        r2 = app_client.post("/api/v1/session/start", json=sample_profile).json()
        assert r1["session_id"] != r2["session_id"]
