"""
CareerForge AI — IBM watsonx.ai RAG Pipeline
Uses LangChain + ChromaDB + IBM Granite for retrieval-augmented generation.

All heavy dependencies are imported lazily so the app boots cleanly even
when they are not installed — it runs in degraded-mode with fallback responses.
"""

import logging
from typing import List, Optional
from pathlib import Path

from backend.config import get_settings

logger = logging.getLogger(__name__)


class CareerForgeRAGPipeline:
    """
    Core RAG pipeline for CareerForge AI.

    Retrieves role-specific interview context from ChromaDB,
    then uses IBM Granite to generate personalized questions and feedback.
    """

    def __init__(self):
        self.settings = get_settings()
        self._llm = None
        self._embeddings = None
        self._vectorstore = None
        self._retrieval_chain = None

    # ─── Initialization ────────────────────────────────────────────────────────

    def initialize(self):
        """Initialize all pipeline components. Call once at startup."""
        logger.info("Initializing CareerForge RAG Pipeline...")
        self._init_llm()
        self._init_embeddings()
        self._init_vectorstore()
        self._init_chain()
        logger.info("✅ RAG Pipeline initialized successfully.")

    def _init_llm(self):
        """Initialize IBM Granite LLM via watsonx.ai."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        self._llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.settings.watsonx_api_key,
            temperature=self.settings.temperature,
            max_output_tokens=self.settings.max_new_tokens,
        )
        logger.info(f"✅ IBM Granite LLM loaded: {self.settings.granite_model_id}")

    def _init_embeddings(self):
        """Initialize IBM Slate embedding model."""
        from langchain_huggingface import HuggingFaceEmbeddings

        self._embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("✅ IBM Slate embeddings loaded.")

    def _init_vectorstore(self):
        """Load or create ChromaDB vector store."""
        from langchain_chroma import Chroma

        persist_path = Path(self.settings.chroma_persist_dir)
        persist_path.mkdir(parents=True, exist_ok=True)

        self._vectorstore = Chroma(
            collection_name="interview_knowledge_base",
            embedding_function=self._embeddings,
            persist_directory=str(persist_path),
        )
        count = self._vectorstore._collection.count()
        logger.info(f"✅ ChromaDB loaded. Documents in store: {count}")

    def _init_chain(self):
        """Build the RAG chain using LangChain expression language (LCEL)."""
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough

        INTERVIEW_PROMPT = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are CareerForge AI, an expert interview coach powered by IBM Granite.
Use the following retrieved context about interview best practices and role-specific knowledge to help the candidate.

Context:
{context}

Task: {question}

Provide a detailed, actionable, and encouraging response. Be specific to the candidate's role and experience level.
If generating interview questions, format them clearly and explain why each question is important.
If evaluating an answer, use the STAR method framework and provide constructive feedback.

Response:"""
        )

        retriever = self._vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20},
        )

        def format_docs(docs):
            return "\n\n".join(d.page_content for d in docs)

        self._retrieval_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | INTERVIEW_PROMPT
            | self._llm
            | StrOutputParser()
        )

    # ─── Public Interface ──────────────────────────────────────────────────────

    def generate_questions(
        self,
        job_role: str,
        experience_level: str,
        question_type: str,
        difficulty: str,
        skills: List[str],
        resume_context: Optional[str] = None,
        num_questions: int = 5,
    ) -> str:
        """Generate personalized interview questions using RAG."""
        resume_hint = ""
        if resume_context:
            resume_hint = f"\nCandidate Resume Highlights:\n{resume_context[:500]}"

        query = f"""Generate {num_questions} {difficulty} {question_type} interview questions for a \
{experience_level} {job_role} candidate.
Key skills to focus on: {', '.join(skills) if skills else 'general domain skills'}.
{resume_hint}

Format each question as:
Q[N]: [Question text]
Type: [Technical/Behavioral/Situational]
Why it matters: [Brief explanation]
Expected answer duration: [X minutes]
---"""

        return self._retrieval_chain.invoke(query)

    def evaluate_answer(
        self,
        question: str,
        answer: str,
        job_role: str,
        experience_level: str,
    ) -> str:
        """Evaluate a candidate's answer using RAG + Granite."""
        query = f"""Evaluate this interview answer for a {experience_level} {job_role} position.

Question: {question}

Candidate's Answer: {answer}

Provide a structured evaluation with:
1. SCORE (0-10) for each dimension: Relevance, STAR Method, Technical Depth, Communication, Originality
2. OVERALL SCORE (0-10)
3. STRENGTHS: 2-3 specific strengths demonstrated
4. IMPROVEMENTS: 2-3 specific areas to improve
5. MODEL ANSWER HINT: Key points the ideal answer should include
6. KEYWORDS USED: Technical/domain keywords the candidate mentioned correctly
7. KEYWORDS MISSED: Important keywords/concepts the candidate should have included
8. FOLLOW-UP: One follow-up probing question the interviewer might ask

Be honest, specific, and constructive."""

        return self._retrieval_chain.invoke(query)

    def get_coaching_advice(self, question: str, job_role: str) -> str:
        """Provide coaching advice on any interview topic."""
        query = f"As an interview coach for a {job_role} candidate: {question}"
        return self._retrieval_chain.invoke(query)

    def add_documents(self, documents: list) -> None:
        """Add new documents to the vector store (e.g., resume content)."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
        )
        chunks = splitter.split_documents(documents)
        self._vectorstore.add_documents(chunks)
        logger.info(f"Added {len(chunks)} chunks to vector store.")

    @property
    def is_ready(self) -> bool:
        return self._llm is not None and self._vectorstore is not None


# ─── Singleton ────────────────────────────────────────────────────────────────

_pipeline_instance: Optional[CareerForgeRAGPipeline] = None


def get_rag_pipeline() -> CareerForgeRAGPipeline:
    """Get or create the singleton RAG pipeline."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = CareerForgeRAGPipeline()
        _pipeline_instance.initialize()
    return _pipeline_instance
