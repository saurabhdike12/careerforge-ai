"""
CareerForge AI — Resume Parser
Uses Docling + PyPDF2 + python-docx to extract text from uploaded resumes.
"""

import io
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ResumeParser:
    """
    Parses uploaded resume files (PDF, DOCX, TXT) into clean text
    for personalization of the interview session.
    """

    SUPPORTED_FORMATS = {".pdf", ".docx", ".doc", ".txt"}

    def parse_bytes(self, file_bytes: bytes, filename: str) -> Optional[str]:
        """Parse resume from raw bytes, auto-detecting format by filename extension."""
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {ext}. Supported: {', '.join(self.SUPPORTED_FORMATS)}")

        if ext == ".pdf":
            return self._parse_pdf(file_bytes)
        elif ext in {".docx", ".doc"}:
            return self._parse_docx(file_bytes)
        elif ext == ".txt":
            return file_bytes.decode("utf-8", errors="ignore")
        return None

    def _parse_pdf(self, data: bytes) -> str:
        """Extract text from PDF using Docling (preferred) with PyPDF2 fallback."""
        # Try Docling first (better layout understanding)
        try:
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            # Docling works with file paths, so write to temp
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(data)
                tmp_path = f.name
            try:
                result = converter.convert(tmp_path)
                text = result.document.export_to_text()
                return self._clean_text(text)
            finally:
                os.unlink(tmp_path)
        except ImportError:
            logger.info("Docling not available, falling back to PyPDF2.")
        except Exception as e:
            logger.warning(f"Docling parsing failed: {e}. Falling back to PyPDF2.")

        # PyPDF2 fallback
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(data))
            text_parts = [page.extract_text() or "" for page in reader.pages]
            return self._clean_text("\n".join(text_parts))
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            return ""

    def _parse_docx(self, data: bytes) -> str:
        """Extract text from DOCX using python-docx."""
        try:
            from docx import Document
            doc = Document(io.BytesIO(data))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return self._clean_text("\n".join(paragraphs))
        except Exception as e:
            logger.error(f"DOCX parsing failed: {e}")
            return ""

    def _clean_text(self, text: str) -> str:
        """Clean extracted text — remove excess whitespace and junk characters."""
        import re
        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        # Remove null bytes and control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return text.strip()

    def extract_skills_hint(self, resume_text: str) -> list[str]:
        """Quick heuristic extraction of skills from resume text for personalization."""
        import re
        tech_keywords = [
            "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
            "React", "Vue", "Angular", "Node.js", "FastAPI", "Django", "Flask", "Spring",
            "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform", "CI/CD",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "Machine Learning", "Deep Learning", "NLP", "LLM", "RAG", "TensorFlow", "PyTorch",
            "Agile", "Scrum", "Product Management", "A/B Testing", "SQL", "Spark",
        ]
        found = []
        for kw in tech_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", resume_text, re.IGNORECASE):
                found.append(kw)
        return found[:15]  # Return top 15 detected skills
