"""
CareerForge AI — Knowledge Base Corpus Loader
Loads role-specific interview Q&A data into ChromaDB vector store.
Run once: python -m backend.rag.corpus_loader
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Knowledge Base: Software Engineer ────────────────────────────────────────

SOFTWARE_ENGINEER_KB = [
    {
        "content": "System Design Interview: Designing a URL shortener like bit.ly. Expected topics: hash functions (MD5/SHA256 truncated, base62 encoding), database schema (short_url, long_url, created_at, expiry), scalability with sharding and consistent hashing, caching with Redis/CDN, load balancing, analytics tracking. Key insight: 302 vs 301 redirect for analytics.",
        "metadata": {"role": "software_engineer", "type": "technical", "topic": "system_design", "difficulty": "hard"}
    },
    {
        "content": "Data Structures & Algorithms: Binary search tree operations — insertion O(log n) average O(n) worst, deletion with 3 cases (leaf, one child, two children using inorder successor), traversal (inorder gives sorted output). Common interview: validate BST, lowest common ancestor, convert BST to sorted array.",
        "metadata": {"role": "software_engineer", "type": "technical", "topic": "dsa", "difficulty": "medium"}
    },
    {
        "content": "Concurrency Interview Topics: Race conditions, deadlocks (4 conditions: mutual exclusion, hold and wait, no preemption, circular wait), mutex vs semaphore vs monitor. Thread-safe singleton pattern with double-checked locking. Producer-consumer problem with bounded buffer. Python GIL implications.",
        "metadata": {"role": "software_engineer", "type": "technical", "topic": "concurrency", "difficulty": "hard"}
    },
    {
        "content": "REST API Design Best Practices: HTTP methods semantics (GET idempotent, POST not, PUT idempotent, DELETE idempotent), status codes (200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Rate Limited, 500 Server Error), versioning strategies (URI vs header), pagination (cursor-based vs offset), HATEOAS.",
        "metadata": {"role": "software_engineer", "type": "technical", "topic": "api_design", "difficulty": "medium"}
    },
    {
        "content": "Microservices Interview: Service mesh (Istio/Linkerd), circuit breaker pattern (Hystrix/Resilience4j), API gateway vs BFF, event sourcing vs CQRS, distributed tracing (Jaeger/Zipkin), service discovery (Consul/Eureka). CAP theorem — consistency vs availability tradeoff in distributed systems.",
        "metadata": {"role": "software_engineer", "type": "technical", "topic": "microservices", "difficulty": "hard"}
    },
    {
        "content": "Behavioral Question for Engineers: 'Tell me about a time you had to deal with a critical production bug.' STAR answer framework: Situation (describe the production impact and urgency), Task (your role and ownership), Action (debugging steps: monitoring/logs, root cause analysis, hotfix deployment, communication to stakeholders), Result (quantify resolution time, preventive measures added like monitoring alerts, post-mortem culture).",
        "metadata": {"role": "software_engineer", "type": "behavioral", "topic": "incident_handling", "difficulty": "medium"}
    },
    {
        "content": "Code Review Best Practices Interview: Look for correctness first, then readability, performance, security (SQL injection, XSS), test coverage. Give specific actionable feedback with examples. Non-blocking vs blocking comments. Pull request size best practices (< 400 lines). Psychological safety in reviews.",
        "metadata": {"role": "software_engineer", "type": "behavioral", "topic": "code_review", "difficulty": "easy"}
    },
    {
        "content": "Database Interview Topics: ACID properties (Atomicity-Consistency-Isolation-Durability), isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable), indexing strategies (B-tree, Hash, Composite, Covering index), query optimization with EXPLAIN ANALYZE, N+1 query problem and eager loading solutions, normalization (1NF-3NF) vs denormalization for performance.",
        "metadata": {"role": "software_engineer", "type": "technical", "topic": "databases", "difficulty": "hard"}
    },
    {
        "content": "Object-Oriented Design Interview: SOLID principles — Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. Design patterns: Factory (object creation), Observer (event handling), Strategy (algorithm family), Decorator (behavior extension), Command (undo/redo). When to use composition over inheritance.",
        "metadata": {"role": "software_engineer", "type": "technical", "topic": "oop", "difficulty": "medium"}
    },
    {
        "content": "CI/CD Pipeline Interview: Git branching strategies (Gitflow vs trunk-based), blue-green vs canary deployments, feature flags, infrastructure as code (Terraform/Pulumi), containerization (Docker multi-stage builds), Kubernetes concepts (pods, deployments, services, ingress, HPA). SRE practices: SLI/SLO/SLA, error budget.",
        "metadata": {"role": "software_engineer", "type": "technical", "topic": "devops", "difficulty": "medium"}
    },
]

# ─── Knowledge Base: Data Scientist ───────────────────────────────────────────

DATA_SCIENTIST_KB = [
    {
        "content": "Machine Learning Fundamentals Interview: Bias-variance tradeoff — high bias underfitting (simple model), high variance overfitting (complex model). Regularization: L1 (Lasso, feature selection), L2 (Ridge, weight shrinkage). Cross-validation (k-fold, stratified k-fold for imbalanced). Evaluation metrics: precision/recall/F1 for classification, RMSE/MAE/R² for regression.",
        "metadata": {"role": "data_scientist", "type": "technical", "topic": "ml_fundamentals", "difficulty": "medium"}
    },
    {
        "content": "Feature Engineering Interview: Handling missing data (imputation strategies: mean/median/mode, KNN, iterative), outlier detection (IQR, Z-score, Isolation Forest), categorical encoding (one-hot, label, target encoding, embeddings), feature scaling (StandardScaler, MinMaxScaler, RobustScaler), feature selection (ANOVA, mutual information, RFE, SHAP values).",
        "metadata": {"role": "data_scientist", "type": "technical", "topic": "feature_engineering", "difficulty": "medium"}
    },
    {
        "content": "Deep Learning Interview: Vanishing/exploding gradients — solutions: batch normalization, residual connections (ResNet), gradient clipping, better activations (ReLU vs sigmoid). Attention mechanisms and Transformers — self-attention, multi-head attention, positional encoding. Transfer learning: feature extraction vs fine-tuning, when to use each.",
        "metadata": {"role": "data_scientist", "type": "technical", "topic": "deep_learning", "difficulty": "hard"}
    },
    {
        "content": "A/B Testing Interview: Hypothesis testing (null/alternative hypothesis, Type I/II errors), statistical significance (p-value < 0.05), statistical power, sample size calculation, multiple testing problem (Bonferroni correction), novelty effect, network effects in experiments. Bayesian vs frequentist A/B testing approaches.",
        "metadata": {"role": "data_scientist", "type": "technical", "topic": "experimentation", "difficulty": "hard"}
    },
    {
        "content": "LLM & GenAI Interview for Data Scientists: Prompt engineering (zero-shot, few-shot, chain-of-thought), RAG architecture (embedding models, vector databases, chunking strategies, reranking), fine-tuning vs RAG tradeoffs, hallucination detection and mitigation, evaluation metrics for LLMs (ROUGE, BLEU, BERTScore, human eval), responsible AI in LLMs.",
        "metadata": {"role": "data_scientist", "type": "technical", "topic": "llm_genai", "difficulty": "hard"}
    },
    {
        "content": "Data Science Behavioral: 'Describe a project where your model had unexpected results in production.' Key answer points: train/test distribution shift (data drift), feature drift monitoring, model performance degradation, retraining pipeline, A/B testing model versions, stakeholder communication about ML uncertainty. Shows maturity in understanding real-world ML.",
        "metadata": {"role": "data_scientist", "type": "behavioral", "topic": "production_ml", "difficulty": "medium"}
    },
]

# ─── Knowledge Base: Product Manager ──────────────────────────────────────────

PRODUCT_MANAGER_KB = [
    {
        "content": "Product Strategy Interview: Product vision vs strategy vs roadmap hierarchy. Frameworks: OKRs (Objectives and Key Results) for goal-setting, North Star Metric identification, Jobs-To-Be-Done (JTBD) theory, Kano model for feature prioritization (must-haves vs performance vs delighters). Product-market fit signals and measurement.",
        "metadata": {"role": "product_manager", "type": "technical", "topic": "strategy", "difficulty": "medium"}
    },
    {
        "content": "Prioritization Frameworks for PM Interviews: RICE score (Reach × Impact × Confidence / Effort), MoSCoW (Must/Should/Could/Won't), ICE framework, Value vs Effort matrix, Opportunity Scoring. When to use each framework. How to handle stakeholder pushback on prioritization decisions with data.",
        "metadata": {"role": "product_manager", "type": "technical", "topic": "prioritization", "difficulty": "medium"}
    },
    {
        "content": "Product Metrics Interview: Acquisition (CAC, conversion rate), Activation (time-to-value, onboarding completion), Retention (DAU/MAU ratio, churn rate, cohort analysis), Revenue (ARR, LTV, LTV:CAC ratio), Referral (NPS, viral coefficient). Leading vs lagging indicators. Vanity metrics to avoid.",
        "metadata": {"role": "product_manager", "type": "technical", "topic": "metrics", "difficulty": "medium"}
    },
    {
        "content": "PM Behavioral: 'Tell me about a product you launched that failed and what you learned.' STAR answer: Define failure clearly (missed metrics not just low engagement), root cause analysis (wrong problem, wrong solution, wrong timing, wrong execution), lessons learned (better discovery process, more user research, faster iteration), how you applied learnings. Shows self-awareness and growth mindset.",
        "metadata": {"role": "product_manager", "type": "behavioral", "topic": "failure_learning", "difficulty": "medium"}
    },
    {
        "content": "User Research & Discovery for PMs: Jobs-to-be-done interviews, contextual inquiry, usability testing, surveys (Likert scale, NPS), diary studies. How to synthesize qualitative insights into product requirements. Avoiding confirmation bias. Building empathy maps and user journey maps. When to use qual vs quant research.",
        "metadata": {"role": "product_manager", "type": "technical", "topic": "user_research", "difficulty": "easy"}
    },
]

# ─── Knowledge Base: Behavioral (Universal) ───────────────────────────────────

BEHAVIORAL_KB = [
    {
        "content": "STAR Method Framework: Situation (set the scene with specific context, 1-2 sentences), Task (your specific responsibility and challenge, what was expected of you), Action (YOUR specific actions — use 'I' not 'we', be specific about steps taken, show decision-making process), Result (quantify impact: %, $, time saved, user satisfaction). Common mistake: spending too long on Situation, not enough on Action and Result.",
        "metadata": {"role": "all", "type": "behavioral", "topic": "star_method", "difficulty": "easy"}
    },
    {
        "content": "Leadership Interview Questions: 'Tell me about a time you led without authority.' Key elements: how you built credibility and trust, influencing through data and storytelling, handling resistance, aligning different stakeholders on a shared goal, the outcome and relationship preservation. Shows EQ and strategic influence skills.",
        "metadata": {"role": "all", "type": "behavioral", "topic": "leadership", "difficulty": "medium"}
    },
    {
        "content": "Conflict Resolution Interview: 'Describe a conflict with a coworker/manager.' Framework: acknowledge the conflict professionally, active listening and understanding their perspective, finding common ground (shared goals), proposing collaborative solution, outcome and relationship preservation. Avoid: blaming others, vague answers, claiming no conflicts ever happened.",
        "metadata": {"role": "all", "type": "behavioral", "topic": "conflict", "difficulty": "medium"}
    },
    {
        "content": "Adaptability and Change Interview: 'Tell me about a time when you had to adapt to a major change.' Key signals interviewers look for: positive framing of change, proactive learning approach, resilience, helping others adapt, concrete actions taken. Growth mindset demonstration. Contrast with fixed mindset behaviors.",
        "metadata": {"role": "all", "type": "behavioral", "topic": "adaptability", "difficulty": "easy"}
    },
    {
        "content": "Time Management & Prioritization Behavioral: 'How do you handle multiple competing deadlines?' Framework: Eisenhower matrix (urgent/important), transparent communication about capacity, early escalation of conflicts, delegation when appropriate, time-boxing techniques. Avoid: saying you just 'work harder' or 'multi-task' — these are red flags.",
        "metadata": {"role": "all", "type": "behavioral", "topic": "time_management", "difficulty": "easy"}
    },
    {
        "content": "Salary Negotiation and HR Questions: 'What are your salary expectations?' Best practice: research market rate (Glassdoor, levels.fyi, LinkedIn Salary), give a range not a single number, anchor higher, emphasize total compensation, delay giving numbers if possible (ask for their budget first). Never lie about current salary.",
        "metadata": {"role": "all", "type": "hr", "topic": "salary", "difficulty": "easy"}
    },
    {
        "content": "'Tell me about yourself' — The Perfect 90-Second Pitch: Structure: Present (current role and key achievement) → Past (relevant experience trajectory) → Future (why this role/company). Tailor to the job description. End with a specific reason you're excited about this company/role. Avoid: listing your resume, personal life details, going over 2 minutes.",
        "metadata": {"role": "all", "type": "hr", "topic": "self_introduction", "difficulty": "easy"}
    },
    {
        "content": "Weakness Question Strategy: 'What is your greatest weakness?' Framework: choose a REAL weakness (not strengths in disguise), show self-awareness, demonstrate active steps you're taking to improve, show measurable progress. Examples: public speaking → joined Toastmasters, delegation → started using RACI matrices. Avoid: claiming perfectionism, saying you have no weaknesses.",
        "metadata": {"role": "all", "type": "hr", "topic": "weakness", "difficulty": "easy"}
    },
    {
        "content": "Questions to Ask the Interviewer: 'What does success look like in this role in the first 90 days?', 'What are the biggest challenges the team is currently facing?', 'How would you describe the engineering/team culture?', 'What growth opportunities exist?', 'Why did the last person leave this role?'. Avoid: asking about salary/benefits in first round, asking things easily found on website.",
        "metadata": {"role": "all", "type": "hr", "topic": "questions_to_ask", "difficulty": "easy"}
    },
]

# ─── Loader ────────────────────────────────────────────────────────────────────

ALL_KNOWLEDGE_BASES = {
    "software_engineer": SOFTWARE_ENGINEER_KB,
    "data_scientist": DATA_SCIENTIST_KB,
    "product_manager": PRODUCT_MANAGER_KB,
    "behavioral": BEHAVIORAL_KB,
}


def load_all_knowledge_bases() -> list:
    """Convert all KB entries into LangChain Documents."""
    from langchain_core.documents import Document
    documents = []
    total = 0
    for kb_name, entries in ALL_KNOWLEDGE_BASES.items():
        for entry in entries:
            doc = Document(
                page_content=entry["content"],
                metadata={**entry["metadata"], "source": kb_name}
            )
            documents.append(doc)
            total += 1
    logger.info(f"Loaded {total} knowledge base documents across {len(ALL_KNOWLEDGE_BASES)} domains.")
    return documents


def get_role_documents(role: str) -> list:
    """Get documents relevant to a specific role + universal behavioral docs."""
    from langchain_core.documents import Document
    role_normalized = role.lower().replace(" ", "_")
    docs = []

    # Add role-specific docs
    for kb_name, entries in ALL_KNOWLEDGE_BASES.items():
        if kb_name == role_normalized or kb_name == "behavioral":
            for entry in entries:
                docs.append(Document(
                    page_content=entry["content"],
                    metadata={**entry["metadata"], "source": kb_name}
                ))

    # Fallback to all docs if role not found
    if not docs:
        docs = load_all_knowledge_bases()

    return docs


if __name__ == "__main__":
    """Run this script to populate the ChromaDB vector store."""
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        from backend.rag.pipeline import get_rag_pipeline
        
        pipeline = get_rag_pipeline()
        documents = load_all_knowledge_bases()
        pipeline.add_documents(documents)
        print(f"✅ Successfully loaded {len(documents)} documents into ChromaDB.")
    except Exception as e:
        print(f"❌ Error loading knowledge base: {e}")
        print("Make sure your .env file is configured with valid IBM watsonx.ai credentials.")
        sys.exit(1)
