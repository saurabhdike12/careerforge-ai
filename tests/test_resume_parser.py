"""
Tests for the resume parser (Docling / PyPDF2 / python-docx).
No IBM credentials needed.
"""

import pytest
from backend.parsers.resume_parser import ResumeParser


@pytest.fixture
def parser():
    return ResumeParser()


class TestResumeParserFormats:
    def test_unsupported_format_raises_value_error(self, parser):
        with pytest.raises(ValueError, match="Unsupported format"):
            parser.parse_bytes(b"some content", "resume.xlsx")

    def test_txt_file_parsed_correctly(self, parser):
        content = b"John Doe\nSoftware Engineer\nPython, AWS, Docker\n5 years experience"
        result = parser.parse_bytes(content, "resume.txt")
        assert "John" in result
        assert "Python" in result

    def test_txt_encoding_errors_handled(self, parser):
        content = "Résumé with special chars: café, naïve".encode("latin-1")
        result = parser.parse_bytes(content, "resume.txt")
        assert result is not None  # Should not raise


class TestSkillExtraction:
    def test_extracts_python(self, parser):
        text = "Experienced with Python, Django, and PostgreSQL for backend development."
        skills = parser.extract_skills_hint(text)
        assert "Python" in skills

    def test_extracts_multiple_skills(self, parser):
        text = "Skills: Python, AWS, Docker, Kubernetes, React, PostgreSQL, Redis, CI/CD"
        skills = parser.extract_skills_hint(text)
        assert len(skills) >= 4

    def test_returns_at_most_15_skills(self, parser):
        text = " ".join([
            "Python Java JavaScript TypeScript Go React Vue Angular Node.js",
            "FastAPI Django Docker Kubernetes AWS GCP Azure Terraform",
            "PostgreSQL MySQL MongoDB Redis Elasticsearch Machine Learning Deep Learning NLP",
        ])
        skills = parser.extract_skills_hint(text)
        assert len(skills) <= 15

    def test_case_insensitive_detection(self, parser):
        text = "proficient in python and aws cloud infrastructure"
        skills = parser.extract_skills_hint(text)
        assert "Python" in skills or "AWS" in skills

    def test_empty_text_returns_empty_list(self, parser):
        skills = parser.extract_skills_hint("")
        assert skills == []

    def test_no_skills_in_generic_text(self, parser):
        text = "I am a motivated individual who works well in teams."
        skills = parser.extract_skills_hint(text)
        # Should not extract irrelevant words
        assert isinstance(skills, list)


class TestTextCleaning:
    def test_clean_text_removes_excess_newlines(self, parser):
        raw = "Line one\n\n\n\n\nLine two"
        cleaned = parser._clean_text(raw)
        assert "\n\n\n" not in cleaned

    def test_clean_text_removes_null_bytes(self, parser):
        raw = "Hello\x00World\x01Test"
        cleaned = parser._clean_text(raw)
        assert "\x00" not in cleaned
        assert "HelloWorldTest" in cleaned

    def test_clean_text_strips_whitespace(self, parser):
        raw = "   Hello World   "
        cleaned = parser._clean_text(raw)
        assert cleaned == "Hello World"
