"""
CareerForge AI — pytest fixtures and mock IBM Granite setup.

ALL tests use mocked IBM Granite so no real API credentials are needed.
The mocks simulate the exact response format that Granite returns,
so tests validate the full parsing and business logic pipeline.

Heavy optional packages (langchain, ibm-watsonx-ai, chromadb) are stubbed
at the top of this file so the entire test suite runs without them.
"""

import sys
import pytest
import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# ── Stub optional heavy packages before any backend import ───────────────────
for _mod in [
    "langchain", "langchain.chains", "langchain.prompts",
    "langchain_ibm", "langchain_community", "langchain_community.vectorstores",
    "langchain.text_splitter", "langchain.schema",
    "ibm_watsonx_ai", "ibm_watsonx_ai.metanames",
    "ibm_watsonx_ai.foundation_models", "ibm_watsonx_ai.foundation_models.utils",
    "ibm_watsonx_ai.foundation_models.utils.enums",
    "chromadb",
    "docling", "docling.document_converter",
    "spacy", "nltk", "sentence_transformers",
    "slowapi", "slowapi.util", "slowapi.errors",
    "aiofiles", "jose", "passlib", "passlib.context",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()


# ─── Mock IBM Granite LLM ─────────────────────────────────────────────────────

MOCK_QUESTION_RESPONSE = """
Q1: Can you walk me through a challenging system design problem you solved, and what trade-offs you considered?
Type: Technical
Why it matters: Tests architectural thinking and trade-off awareness critical for senior engineers.
Expected answer duration: 3 minutes
Tip: Structure your answer around requirements → high-level design → deep dive → trade-offs.
"""

MOCK_EVALUATION_RESPONSE = """
SCORE:
Relevance: 8
STAR Method: 7
Technical Depth: 8
Communication: 7
Originality: 7
Overall: 7.5

STRENGTHS:
- Clearly quantified the business impact with a 40% latency reduction
- Demonstrated ownership and end-to-end thinking
- Used appropriate technical vocabulary

IMPROVEMENTS:
- Could elaborate more on the Result phase with team outcomes
- Missing mention of monitoring and observability post-deployment
- Should explain the trade-offs considered more explicitly

MODEL ANSWER HINT: Include the specific bottleneck identified, the architectural decision made, the implementation steps, and measurable outcomes including performance metrics and business impact.

KEYWORDS USED: microservices, latency, API, Python, AWS

KEYWORDS MISSED: distributed tracing, load balancing, circuit breaker, SLA

FOLLOW-UP: What monitoring did you put in place after the migration to catch regressions early?
"""

MOCK_COACHING_RESPONSE = """
For behavioral questions as a Software Engineer, use the STAR method:
- Situation: Set the context briefly (1-2 sentences)
- Task: Describe your specific responsibility
- Action: Focus on YOUR actions using "I" not "we"
- Result: Quantify the outcome — numbers, percentages, time saved

Key tip: Spend 70% of your answer on Action and Result. Most candidates over-explain the Situation.
"""


@pytest.fixture
def mock_rag_pipeline():
    """
    Returns a mock CareerForgeRAGPipeline that simulates IBM Granite responses
    without making any real API calls.
    """
    pipeline = MagicMock()
    pipeline.is_ready = True

    pipeline.generate_questions.return_value = MOCK_QUESTION_RESPONSE
    pipeline.evaluate_answer.return_value = MOCK_EVALUATION_RESPONSE
    pipeline.get_coaching_advice.return_value = MOCK_COACHING_RESPONSE
    pipeline.add_documents.return_value = None

    return pipeline


@pytest.fixture
def app_client(mock_rag_pipeline):
    """
    FastAPI TestClient with IBM Granite mocked out.
    Patches get_rag_pipeline so no real watsonx.ai connection is attempted.
    """
    # Patch settings to avoid needing a real .env
    with patch("backend.config.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            watsonx_api_key="test-key",
            watsonx_project_id="test-project",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            granite_model_id="ibm/granite-13b-chat-v2",
            granite_embedding_model="ibm/slate-125m-english-rtrvr",
            max_new_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            database_url="sqlite:///./test_careerforge.db",
            chroma_persist_dir="./test_chroma",
            session_expiry_hours=24,
            max_questions_per_session=20,
            max_requests_per_minute=30,
            debug=True,
            secret_key="test-secret",
        )

        with patch("backend.rag.pipeline.get_rag_pipeline", return_value=mock_rag_pipeline):
            with patch("backend.main.get_rag_pipeline", return_value=mock_rag_pipeline):
                from backend.main import app
                client = TestClient(app, raise_server_exceptions=True)
                yield client


@pytest.fixture
def sample_profile():
    """Standard user profile for test sessions."""
    return {
        "name": "Test Candidate",
        "job_role": "Software Engineer",
        "experience_level": "mid",
        "years_of_experience": 4.0,
        "target_company": "IBM",
        "industry": "Technology",
        "skills": ["Python", "AWS", "System Design"],
        "focus_areas": ["technical", "behavioral"],
        "difficulty": "medium",
        "resume_text": None,
    }


@pytest.fixture
def started_session(app_client, sample_profile):
    """
    Creates a live session via the API and returns
    (client, session_id, first_question_id, first_question_text).
    """
    resp = app_client.post("/api/v1/session/start", json=sample_profile)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return (
        app_client,
        data["session_id"],
        data["first_question"]["question_id"],
        data["first_question"]["question_text"],
    )
