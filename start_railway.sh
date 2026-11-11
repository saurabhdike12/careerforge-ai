#!/usr/bin/env bash
# Railway startup script — loads knowledge base then starts the server
set -e

echo "CareerForge AI — Starting up on Railway..."

# Load knowledge base into ChromaDB on first deploy
CHROMA_DIR="./backend/data/chroma_db"
if [ ! -d "$CHROMA_DIR" ] || [ -z "$(ls -A $CHROMA_DIR 2>/dev/null)" ]; then
    echo "Loading knowledge base into ChromaDB..."
    python -m backend.rag.corpus_loader || echo "KB load skipped (degraded mode)"
fi

echo "Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
