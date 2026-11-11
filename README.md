# 🎯 CareerForge AI — Intelligent Interview Trainer Agent

> **IBM SkillsBuild University Education — Problem Statement #22**
> Powered by IBM Granite (watsonx.ai) + RAG + LangChain

---

## 🌟 What Makes CareerForge AI Brilliant

CareerForge AI is a **full-stack, production-quality Interview Training Agent** that uses **Retrieval-Augmented Generation (RAG)** with **IBM Granite** to deliver hyper-personalized interview preparation. Unlike generic prep tools, CareerForge dynamically adapts to your resume, experience level, and target role — generating questions, model answers, scoring your responses in real-time, and tracking your progress over sessions.

### Key Differentiators
- 🧠 **IBM Granite LLM** via watsonx.ai — enterprise-grade, responsible AI
- 📄 **Resume-Aware RAG** — parses your actual resume to personalize every question
- 🎙️ **Real-time Response Scoring** — AI evaluates your answers with STAR-method feedback
- 📊 **Session Analytics** — tracks confidence scores, topic gaps, and improvement trends
- 🔒 **Ethical AI** — transparent reasoning, bias detection, no PII stored
- 🌐 **Multi-domain** — Tech, Finance, Healthcare, Marketing, HR roles
- 💬 **Conversational Flow** — multi-turn dialogue, follow-up probing questions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CareerForge AI                           │
│                                                                 │
│  ┌──────────────┐    ┌─────────────────────────────────────┐  │
│  │   React UI   │◄───│           FastAPI Backend            │  │
│  │  (Frontend)  │    │                                     │  │
│  └──────────────┘    │  ┌────────────┐  ┌───────────────┐ │  │
│                       │  │RAG Pipeline│  │Session Manager│ │  │
│  ┌──────────────┐    │  │(LangChain) │  │  (SQLite DB)  │ │  │
│  │Resume Upload │────►  └─────┬──────┘  └───────────────┘ │  │
│  │  (Docling)   │    │        │                            │  │
│  └──────────────┘    │        ▼                            │  │
│                       │  ┌──────────────────────────────┐  │  │
│                       │  │     IBM watsonx.ai            │  │  │
│                       │  │  (Granite-13b-chat-v2)        │  │  │
│                       │  └──────────────────────────────┘  │  │
│                       │                                     │  │
│                       │  ┌──────────────────────────────┐  │  │
│                       │  │   ChromaDB Vector Store       │  │  │
│                       │  │  (Role-specific Q&A corpus)   │  │  │
│                       │  └──────────────────────────────┘  │  │
│                       └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
careerforge-ai/
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # IBM watsonx.ai configuration
│   ├── rag/
│   │   ├── pipeline.py          # RAG pipeline (LangChain + ChromaDB)
│   │   ├── embeddings.py        # IBM Slate embeddings
│   │   └── corpus_loader.py     # Interview Q&A knowledge base loader
│   ├── agents/
│   │   ├── interview_agent.py   # Main interview trainer agent
│   │   ├── scorer.py            # Response scoring engine
│   │   └── question_generator.py# Dynamic question generation
│   ├── parsers/
│   │   └── resume_parser.py     # Docling-based resume parser
│   ├── models/
│   │   └── schemas.py           # Pydantic data models
│   ├── database/
│   │   └── session_db.py        # SQLite session management
│   └── data/
│       └── knowledge_base/      # Pre-built interview corpora
│           ├── software_engineer.json
│           ├── data_scientist.json
│           ├── product_manager.json
│           ├── hr_roles.json
│           └── behavioral.json
├── frontend/
│   ├── index.html               # Main SPA entry
│   ├── app.js                   # React application
│   ├── styles.css               # Tailwind-inspired custom CSS
│   └── components/              # UI components
├── demo/
│   └── demo_script.md           # Demo walkthrough script
├── docs/
│   ├── architecture_diagram.html # Interactive architecture diagram
│   └── api_reference.md         # API documentation
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Container definition
└── README.md                    # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- IBM Cloud account with watsonx.ai access
- Node.js 18+ (for frontend dev)

### 1. Clone & Install
```bash
git clone <repo-url>
cd careerforge-ai
pip install -r requirements.txt
```

### 2. Configure IBM watsonx.ai
```bash
cp .env.example .env
# Edit .env with your IBM Cloud credentials
```

### 3. Load Knowledge Base
```bash
python backend/rag/corpus_loader.py
```

### 4. Start the Backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 5. Open Frontend
Open `frontend/index.html` in a browser, or serve with:
```bash
python -m http.server 3000 --directory frontend
```

---

## 🔐 IBM Cloud Setup

1. Create an IBM Cloud account at [cloud.ibm.com](https://cloud.ibm.com)
2. Provision **watsonx.ai** service (Lite tier available)
3. Create an **API Key** from IBM Cloud IAM
4. Get your **Project ID** from watsonx.ai Studio
5. Add credentials to `.env` file

---

## 📊 Scoring Rubric (How AI evaluates your answers)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Relevance | 25% | Does the answer address the question? |
| STAR Method | 25% | Situation, Task, Action, Result structure |
| Technical Depth | 20% | Correct use of domain knowledge |
| Communication | 15% | Clarity, conciseness, confidence |
| Originality | 15% | Unique examples vs generic answers |

---

## 🛡️ Ethical AI Commitment

- **No PII storage** — resume data processed in-memory, not persisted
- **Bias monitoring** — questions reviewed for demographic neutrality
- **Transparent scoring** — all feedback explains the reasoning
- **IBM AI Ethics** — built on IBM's trusted AI principles
- **Data sovereignty** — IBM Cloud ensures enterprise-grade data governance

---

## 📄 License
MIT License — Free for educational use.

Built with ❤️ for IBM SkillsBuild University Education Challenge.
