"""
Tests for the AI coaching chat endpoint.
POST /api/v1/session/{session_id}/chat
"""

import pytest


class TestChat:
    def test_chat_returns_200(self, started_session):
        client, session_id, _, _ = started_session
        resp = client.post(f"/api/v1/session/{session_id}/chat", json={
            "session_id": session_id,
            "message": "How should I answer behavioral questions?",
        })
        assert resp.status_code == 200

    def test_chat_returns_reply(self, started_session):
        client, session_id, _, _ = started_session
        resp = client.post(f"/api/v1/session/{session_id}/chat", json={
            "session_id": session_id,
            "message": "What is the STAR method?",
        })
        data = resp.json()
        assert "reply" in data
        assert len(data["reply"]) > 10

    def test_chat_returns_suggested_actions(self, started_session):
        client, session_id, _, _ = started_session
        resp = client.post(f"/api/v1/session/{session_id}/chat", json={
            "session_id": session_id,
            "message": "How do I negotiate salary?",
        })
        data = resp.json()
        assert "suggested_actions" in data
        assert isinstance(data["suggested_actions"], list)

    def test_chat_with_invalid_session_still_works(self, app_client):
        """Chat falls back gracefully when session_id is unknown — uses generic role."""
        resp = app_client.post("/api/v1/session/nonexistent-id/chat", json={
            "session_id": "nonexistent-id",
            "message": "What should I do?",
        })
        # The chat endpoint has a fallback (does not 404 for missing session)
        assert resp.status_code == 200

    def test_chat_empty_message_rejected(self, started_session):
        client, session_id, _, _ = started_session
        resp = client.post(f"/api/v1/session/{session_id}/chat", json={
            "session_id": session_id,
            "message": "",   # min_length=1
        })
        assert resp.status_code == 422
