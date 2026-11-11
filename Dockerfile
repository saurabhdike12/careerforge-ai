FROM python:3.11-slim

WORKDIR /app

# System dependencies for Docling PDF parsing
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .

# Upgrade pip and install build tools globally
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install requirements with build isolation disabled so setuptools is accessible
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY backend/ ./backend/

# Create data directories
RUN mkdir -p ./backend/data/chroma_db

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
