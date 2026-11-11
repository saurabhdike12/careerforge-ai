"""
Tests for the InterviewAgent business logic — no HTTP, no IBM Granite.
Tests the agent directly with a mock RAG pipeline.

langchain and ibm-watsonx-ai are mocked at import time so this test module
works without those heavy packages installed.
"""

import sys
import pytest
import uuid
from unittest.mock import MagicMock, patch

# ── Stub heavy optional packages before importing anything from backend.rag ──
for _mod in [
    "langchain", "langchain.chains", "langchain.prompts",
    "langchain_ibm", "langchain_community", "langchain_community.vectorstores",
    "langchain.text_splitter", "langchain.schema",
    "ibm_watsonx_ai", "ibm_watsonx_ai.metanames",
    "ibm_watsonx_ai.foundation_models", "ibm_watsonx_ai.foundation_models.utils",
    "ibm_watsonx_ai.foundation_models.utils.enums",
    "chromadb",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

from backend.agents.interview_agent import InterviewAgent
from backend.models.schemas import (
    UserProfileRequest, ExperienceLevel, QuestionType, Difficulty
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

MOCK_QUESTION_OUTPUT = """
Q1: Walk me through a complex system you designed and the key trade-offs you made.
Type: Technical
Why it matters: Tests architectural thinking.
Tip: Use the 4Cs: Context, Constraints, Choices, Consequences.
"""

MOCK_EVAL_OUTPUT = """
SCORE:
Relevance: 8
STAR Method: 7
Technical Depth: 9
Communication: 8
Originality: 7
Overall: 7.8

STRENGTHS:
- Strong quantification of results
- Clear ownership language

IMPROVEMENTS:
- Add more context on team coordination
- Mention post-deployment monitoring

MODEL ANSWER HINT: Include metrics, trade-offs, and a clear result.

KEYWORDS USED: microservices, latency, Python
KEYWORDS MISSED: observability, SLO

FOLLOW-UP: What would you do differently if you had more time?
"""


@pytest.fixture
def mock_pipeline():
    p = MagicMock()
    p.is_ready = True
    p.generate_questions.return_value = MOCK_QUESTION_OUTPUT
    p.evaluate_answer.return_value = MOCK_EVAL_OUTPUT
    return p


@pytest.fixture
def profile():
    return UserProfileRequest(
        name="Agent Test User",
        job_role="Software Engineer",
        experience_level=ExperienceLevel.MID,
        years_of_experience=4.0,
        skills=["Python", "AWS"],
        focus_areas=[QuestionType.TECHNICAL, QuestionType.BEHAVIORAL],
        difficulty=Difficulty.MEDIUM,
    )


@pytest.fixture
def agent(profile, mock_pipeline):
    return InterviewAgent(
        session_id=str(uuid.uuid4()),
        profile=profile,
        rag_pipeline=mock_pipeline,
    )


# ─── Session Plan ─────────────────────────────────────────────────────────────

class TestSessionPlan:
    def test_generates_correct_number_of_questions(self, agent):
        questions = agent.generate_session_plan()
        assert len(questions) == len(InterviewAgent.QUESTION_SEQUENCE)

    def test_all_questions_have_text(self, agent):
        questions = agent.generate_session_plan()
        for q in questions:
            assert q.question_text
            assert len(q.question_text) > 5

    def test_all_questions_have_unique_ids(self, agent):
        questions = agent.generate_session_plan()
        ids = [q.question_id for q in questions]
        assert len(ids) == len(set(ids))

    def test_question_types_match_sequence(self, agent):
        questions = agent.generate_session_plan()
        for i, (expected_type, _, _) in enumerate(InterviewAgent.QUESTION_SEQUENCE):
            assert questions[i].question_type == expected_type

    def test_get_first_question_returns_first(self, agent):
        agent.generate_session_plan()
        q = agent.get_first_question()
        assert q.question_id == agent.questions[0].question_id

    def test_get_next_question_advances_index(self, agent):
        agent.generate_session_plan()
        agent.get_first_question()
        q2 = agent.get_next_question()
        assert q2.question_id == agent.questions[1].question_id

    def test_get_next_question_returns_none_at_end(self, agent):
        agent.generate_session_plan()
        # Advance past the last question
        for _ in range(len(InterviewAgent.QUESTION_SEQUENCE) + 1):
            agent.get_next_question()
        q = agent.get_next_question()
        assert q is None

    def test_fallback_used_when_rag_fails(self, profile):
        """If Granite throws, fallback questions must still be generated."""
        failing_pipeline = MagicMock()
        failing_pipeline.generate_questions.side_effect = RuntimeError("Granite unavailable")
        agent = InterviewAgent(
            session_id=str(uuid.uuid4()),
            profile=profile,
            rag_pipeline=failing_pipeline,
        )
        questions = agent.generate_session_plan()
        assert len(questions) == len(InterviewAgent.QUESTION_SEQUENCE)
        for q in questions:
            assert len(q.question_text) > 10


# ─── Answer Evaluation ────────────────────────────────────────────────────────

class TestAnswerEvaluation:
    def test_evaluate_answer_returns_feedback(self, agent):
        agent.generate_session_plan()
        q = agent.get_first_question()
        feedback = agent.evaluate_answer(
            question_id=q.question_id,
            question_text=q.question_text,
            answer_text="I designed a distributed cache system to reduce database load by 60%.",
            time_taken_seconds=90,
        )
        assert feedback is not None
        assert feedback.score.overall >= 0
        assert feedback.score.overall <= 10

    def test_evaluate_stores_answer_in_history(self, agent):
        agent.generate_session_plan()
        q = agent.get_first_question()
        assert len(agent.answers) == 0
        agent.evaluate_answer(
            question_id=q.question_id,
            question_text=q.question_text,
            answer_text="I reduced latency by 40% using caching.",
        )
        assert len(agent.answers) == 1

    def test_evaluate_stores_score(self, agent):
        agent.generate_session_plan()
        q = agent.get_first_question()
        agent.evaluate_answer(
            question_id=q.question_id,
            question_text=q.question_text,
            answer_text="I reduced latency by 40% using caching.",
        )
        assert len(agent.scores) == 1
        assert agent.scores[0].overall >= 0

    def test_fallback_feedback_when_evaluation_fails(self, profile):
        """If Granite eval fails, fallback feedback must be returned (not raise)."""
        failing_pipeline = MagicMock()
        failing_pipeline.generate_questions.return_value = MOCK_QUESTION_OUTPUT
        failing_pipeline.evaluate_answer.side_effect = RuntimeError("Granite unavailable")
        agent = InterviewAgent(
            session_id=str(uuid.uuid4()),
            profile=profile,
            rag_pipeline=failing_pipeline,
        )
        agent.generate_session_plan()
        q = agent.get_first_question()
        feedback = agent.evaluate_answer(
            question_id=q.question_id,
            question_text=q.question_text,
            answer_text="I worked on several impactful projects in my 4 years of experience.",
        )
        assert feedback is not None
        assert feedback.score.overall > 0  # fallback score based on word count


# ─── Progress Tracking ────────────────────────────────────────────────────────

class TestProgressTracking:
    def test_initial_progress_is_zero(self, agent):
        agent.generate_session_plan()
        p = agent.get_progress()
        assert p["answered"] == 0
        assert p["progress_pct"] == 0
        assert p["average_score"] == 0.0
        assert p["is_complete"] is False

    def test_progress_after_one_answer(self, agent):
        agent.generate_session_plan()
        q = agent.get_first_question()
        agent.evaluate_answer(q.question_id, q.question_text, "A detailed answer with metrics.")
        p = agent.get_progress()
        assert p["answered"] == 1
        assert p["progress_pct"] > 0
        assert p["average_score"] > 0

    def test_is_complete_when_all_answered(self, agent):
        agent.generate_session_plan()
        agent.get_first_question()
        # Answer all questions
        for q in agent.questions:
            agent.evaluate_answer(q.question_id, q.question_text, "Detailed answer with metrics and outcomes.")
        p = agent.get_progress()
        assert p["is_complete"] is True


# ─── Session Summary ──────────────────────────────────────────────────────────

class TestSessionSummary:
    def test_summary_has_all_required_fields(self, agent):
        agent.generate_session_plan()
        summary = agent.get_session_summary()
        assert summary.session_id == agent.session_id
        assert summary.candidate_name == agent.profile.name
        assert summary.job_role == agent.profile.job_role
        assert summary.total_questions == len(agent.questions)
        assert isinstance(summary.recommendation, str)
        assert isinstance(summary.next_steps, list)

    def test_summary_score_is_zero_with_no_answers(self, agent):
        agent.generate_session_plan()
        summary = agent.get_session_summary()
        assert summary.average_score == 0.0

    def test_summary_score_reflects_answers(self, agent):
        agent.generate_session_plan()
        q = agent.get_first_question()
        agent.evaluate_answer(q.question_id, q.question_text, "Detailed answer with numbers.")
        summary = agent.get_session_summary()
        assert summary.average_score > 0

    def test_recommendation_not_empty(self, agent):
        agent.generate_session_plan()
        summary = agent.get_session_summary()
        assert len(summary.recommendation) > 10

    def test_next_steps_not_empty(self, agent):
        agent.generate_session_plan()
        summary = agent.get_session_summary()
        assert len(summary.next_steps) > 0


# ─── Feedback Parsing ─────────────────────────────────────────────────────────

class TestFeedbackParsing:
    def test_parse_feedback_extracts_overall_score(self, agent):
        feedback = agent._parse_feedback(MOCK_EVAL_OUTPUT)
        assert feedback.score.overall == 7.8

    def test_parse_feedback_extracts_all_dimensions(self, agent):
        feedback = agent._parse_feedback(MOCK_EVAL_OUTPUT)
        assert feedback.score.relevance == 8.0
        assert feedback.score.star_method == 7.0
        assert feedback.score.technical_depth == 9.0
        assert feedback.score.communication == 8.0
        assert feedback.score.originality == 7.0

    def test_parse_feedback_extracts_strengths(self, agent):
        feedback = agent._parse_feedback(MOCK_EVAL_OUTPUT)
        assert len(feedback.strengths) > 0

    def test_parse_feedback_extracts_improvements(self, agent):
        feedback = agent._parse_feedback(MOCK_EVAL_OUTPUT)
        assert len(feedback.improvements) > 0

    def test_parse_feedback_extracts_model_hint(self, agent):
        feedback = agent._parse_feedback(MOCK_EVAL_OUTPUT)
        assert len(feedback.model_answer_hint) > 5

    def test_parse_feedback_extracts_follow_up(self, agent):
        feedback = agent._parse_feedback(MOCK_EVAL_OUTPUT)
        assert feedback.follow_up_question is not None
        assert "?" in feedback.follow_up_question or len(feedback.follow_up_question) > 5

    def test_parse_feedback_scores_capped_at_10(self, agent):
        """Even if Granite returns 11, it must be clamped to 10."""
        raw = "Overall: 15\nRelevance: 12\nSTAR: 8\nTechnical: 7\nCommunication: 9\nOriginality: 6"
        feedback = agent._parse_feedback(raw)
        assert feedback.score.overall <= 10
        assert feedback.score.relevance <= 10

    def test_parse_feedback_missing_score_defaults_to_6(self, agent):
        """If a dimension is missing, default is 6.0."""
        raw = "Some feedback without structured scores."
        feedback = agent._parse_feedback(raw)
        assert feedback.score.overall == 6.0

    def test_fallback_feedback_short_answer(self, agent):
        feedback = agent._generate_fallback_feedback("Yes.")
        assert 0 < feedback.score.overall <= 10

    def test_fallback_feedback_long_answer_with_numbers(self, agent):
        long_answer = "I improved system performance by 40% through 3 key optimizations. " * 10
        feedback = agent._generate_fallback_feedback(long_answer)
        # Long answer with numbers should score higher than minimum
        assert feedback.score.overall > 5.0
