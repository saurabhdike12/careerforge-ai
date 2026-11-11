"""
Tests for Pydantic schema validation — no server, no IBM calls needed.
"""

import pytest
from pydantic import ValidationError

from backend.models.schemas import (
    UserProfileRequest, AnswerSubmissionRequest, ChatMessageRequest,
    ScoreBreakdown, AnswerFeedback, InterviewQuestion,
    ExperienceLevel, QuestionType, Difficulty,
)


class TestUserProfileRequest:
    def test_valid_minimal_profile(self):
        p = UserProfileRequest(
            name="Alice",
            job_role="Data Scientist",
            experience_level=ExperienceLevel.JUNIOR,
        )
        assert p.name == "Alice"
        assert p.job_role == "Data Scientist"

    def test_name_cannot_be_empty(self):
        with pytest.raises(ValidationError):
            UserProfileRequest(name="", job_role="Engineer", experience_level="mid")

    def test_job_role_cannot_be_empty(self):
        with pytest.raises(ValidationError):
            UserProfileRequest(name="Alice", job_role="", experience_level="mid")

    def test_invalid_experience_level_rejected(self):
        with pytest.raises(ValidationError):
            UserProfileRequest(name="Alice", job_role="Engineer", experience_level="wizard")

    def test_all_experience_levels_valid(self):
        for level in ExperienceLevel:
            p = UserProfileRequest(name="Alice", job_role="Engineer", experience_level=level)
            assert p.experience_level == level

    def test_years_of_experience_must_be_non_negative(self):
        with pytest.raises(ValidationError):
            UserProfileRequest(
                name="Alice", job_role="Engineer",
                experience_level="mid", years_of_experience=-1
            )

    def test_years_of_experience_max_50(self):
        with pytest.raises(ValidationError):
            UserProfileRequest(
                name="Alice", job_role="Engineer",
                experience_level="mid", years_of_experience=51
            )

    def test_skills_defaults_to_empty_list(self):
        p = UserProfileRequest(name="Alice", job_role="Engineer", experience_level="mid")
        assert p.skills == []

    def test_difficulty_defaults_to_medium(self):
        p = UserProfileRequest(name="Alice", job_role="Engineer", experience_level="mid")
        assert p.difficulty == Difficulty.MEDIUM


class TestAnswerSubmissionRequest:
    def test_valid_answer(self):
        a = AnswerSubmissionRequest(
            session_id="sess-123",
            question_id="q-456",
            question_text="Tell me about yourself.",
            answer_text="I am a software engineer with 5 years of experience.",
        )
        assert a.session_id == "sess-123"

    def test_answer_text_too_short(self):
        with pytest.raises(ValidationError):
            AnswerSubmissionRequest(
                session_id="s", question_id="q",
                question_text="?", answer_text="short",  # < 10 chars
            )

    def test_time_taken_cannot_be_negative(self):
        with pytest.raises(ValidationError):
            AnswerSubmissionRequest(
                session_id="s", question_id="q",
                question_text="?", answer_text="A valid answer here.",
                time_taken_seconds=-5,
            )


class TestScoreBreakdown:
    def test_scores_in_valid_range(self):
        s = ScoreBreakdown(
            relevance=8.5, star_method=7.0, technical_depth=9.0,
            communication=7.5, originality=6.5, overall=7.7,
        )
        assert s.overall == 7.7

    def test_score_above_10_rejected(self):
        with pytest.raises(ValidationError):
            ScoreBreakdown(
                relevance=11.0, star_method=7.0, technical_depth=9.0,
                communication=7.5, originality=6.5, overall=7.7,
            )

    def test_score_below_0_rejected(self):
        with pytest.raises(ValidationError):
            ScoreBreakdown(
                relevance=-1.0, star_method=7.0, technical_depth=9.0,
                communication=7.5, originality=6.5, overall=7.7,
            )


class TestInterviewQuestion:
    def test_valid_question(self):
        q = InterviewQuestion(
            question_id="q-001",
            question_text="Describe a time you resolved a production incident.",
            question_type=QuestionType.BEHAVIORAL,
            difficulty=Difficulty.MEDIUM,
        )
        assert q.question_id == "q-001"

    def test_all_question_types_valid(self):
        for qt in QuestionType:
            q = InterviewQuestion(
                question_id="q-1", question_text="Test question?",
                question_type=qt, difficulty=Difficulty.EASY,
            )
            assert q.question_type == qt

    def test_all_difficulty_levels_valid(self):
        for d in Difficulty:
            q = InterviewQuestion(
                question_id="q-1", question_text="Test question?",
                question_type=QuestionType.TECHNICAL, difficulty=d,
            )
            assert q.difficulty == d


class TestChatMessageRequest:
    def test_valid_message(self):
        m = ChatMessageRequest(session_id="s-1", message="How do I answer STAR questions?")
        assert m.message == "How do I answer STAR questions?"

    def test_empty_message_rejected(self):
        with pytest.raises(ValidationError):
            ChatMessageRequest(session_id="s-1", message="")
