#!/usr/bin/env bash
# CareerForge AI — Bash Startup Script (Linux / macOS)
# Run from project root: bash start.sh

set -e

echo ""
echo "========================================"
echo "  CareerForge AI — Interview Trainer    "
echo "  IBM Granite + watsonx.ai + RAG        "
echo "========================================"
echo ""

# ── Check .env ──────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found."
    echo "Run: cp .env.example .env"
    echo "Then add your WATSONX_API_KEY and WATSONX_PROJECT_ID."
    exit 1
fi

if grep -q "your_ibm_cloud_api_key_here" .env; then
    echo "WARNING: IBM credentials not set in .env"
    echo "App will run in DEGRADED MODE (fallback questions, no real Granite)."
    echo "To enable full IBM Granite: edit .env with your real credentials."
    echo ""
fi

# ── Check Python ─────────────────────────────────────────────────────────────
echo "Python: $(python3 --version 2>&1)"

# ── Check core deps ───────────────────────────────────────────────────────────
for pkg in fastapi uvicorn pydantic sqlalchemy; do
    python3 -c "import $pkg" 2>/dev/null || {
        echo "Installing core dependencies..."
        pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy python-dotenv python-multipart
        break
    }
done

# ── Load knowledge base (first run) ──────────────────────────────────────────
CHROMA_PATH="backend/data/chroma_db"
if [ ! -d "$CHROMA_PATH" ] || [ -z "$(ls -A $CHROMA_PATH 2>/dev/null)" ]; then
    echo "First run: loading knowledge base into ChromaDB..."
    python3 -m backend.rag.corpus_loader 2>/dev/null || echo "Knowledge base load skipped (degraded mode)."
fi

# ── Start backend ─────────────────────────────────────────────────────────────
echo ""
echo "Starting CareerForge AI backend..."
echo "  API:      http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs"
echo "  Health:   http://localhost:8000/health"
echo "  Frontend: Open frontend/index.html in your browser"
echo ""
echo "Press Ctrl+C to stop."
echo ""

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
