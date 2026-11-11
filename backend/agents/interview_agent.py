"""
CareerForge AI — Interview Agent
Orchestrates the interview session: question flow, answer evaluation, progress tracking.
"""

import uuid
import json
import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.rag.pipeline import CareerForgeRAGPipeline
from backend.models.schemas import (
    UserProfileRequest, InterviewQuestion, AnswerFeedback,
    ScoreBreakdown, QuestionType, Difficulty, SessionSummary
)

logger = logging.getLogger(__name__)


class InterviewAgent:
    """
    Stateful interview agent for a single session.
    Manages question flow, scoring, and session analytics.
    """

    QUESTION_SEQUENCE = [
        # Warm-up
        (QuestionType.HR, Difficulty.EASY, "self_introduction"),
        # Core technical rounds
        (QuestionType.TECHNICAL, Difficulty.MEDIUM, "core_skills"),
        (QuestionType.TECHNICAL, Difficulty.MEDIUM, "practical_application"),
        (QuestionType.TECHNICAL, Difficulty.HARD, "advanced_concepts"),
        # Behavioral rounds
        (QuestionType.BEHAVIORAL, Difficulty.MEDIUM, "leadership"),
        (QuestionType.BEHAVIORAL, Difficulty.MEDIUM, "conflict_resolution"),
        # Situational
        (QuestionType.SITUATIONAL, Difficulty.HARD, "crisis_handling"),
        # Culture fit
        (QuestionType.CULTURE_FIT, Difficulty.EASY, "values_alignment"),
        # Closing
        (QuestionType.HR, Difficulty.EASY, "salary_expectations"),
    ]

    def __init__(
        self,
        session_id: str,
        profile: UserProfileRequest,
        rag_pipeline: CareerForgeRAGPipeline,
    ):
        self.session_id = session_id
        self.profile = profile
        self.rag = rag_pipeline
        self.questions: List[InterviewQuestion] = []
        self.answers: List[Dict[str, Any]] = []
        self.scores: List[ScoreBreakdown] = []
        self.current_index = 0
        self.created_at = datetime.utcnow()

    # ─── Session Initialization ────────────────────────────────────────────────

    def generate_session_plan(self) -> List[InterviewQuestion]:
        """Generate a full set of personalized questions upfront."""
        logger.info(f"Generating session plan for {self.profile.name} — {self.profile.job_role}")

        for q_type, difficulty, topic in self.QUESTION_SEQUENCE:
            try:
                raw = self.rag.generate_questions(
                    job_role=self.profile.job_role,
                    experience_level=self.profile.experience_level.value,
                    question_type=q_type.value,
                    difficulty=difficulty.value,
                    skills=self.profile.skills or [],
                    resume_context=self.profile.resume_text,
                    num_questions=1,
                )
                question_text = self._extract_first_question(raw)
                tips = self._extract_tips(raw)
            except Exception as e:
                logger.warning(f"RAG generation failed for {q_type}/{topic}: {e}. Using fallback.")
                question_text = self._get_fallback_question(q_type, self.profile.job_role, topic)
                tips = ["Use the STAR method for behavioral questions.", "Be specific with examples."]

            self.questions.append(InterviewQuestion(
                question_id=str(uuid.uuid4()),
                question_text=question_text,
                question_type=q_type,
                difficulty=difficulty,
                context=f"Assessing {topic.replace('_', ' ')} for {self.profile.experience_level.value}-level {self.profile.job_role}",
                tips=tips,
                expected_duration_minutes=3 if difficulty == Difficulty.HARD else 2,
            ))

        logger.info(f"Generated {len(self.questions)} questions for session {self.session_id}")
        return self.questions

    def get_first_question(self) -> InterviewQuestion:
        """Return the first question in the session."""
        if not self.questions:
            self.generate_session_plan()
        self.current_index = 0
        return self.questions[0]

    def get_next_question(self) -> Optional[InterviewQuestion]:
        """Advance to the next question."""
        self.current_index += 1
        if self.current_index >= len(self.questions):
            return None
        return self.questions[self.current_index]

    # ─── Answer Evaluation ─────────────────────────────────────────────────────

    def evaluate_answer(
        self,
        question_id: str,
        question_text: str,
        answer_text: str,
        time_taken_seconds: Optional[int] = None,
    ) -> AnswerFeedback:
        """Evaluate answer using Granite and return structured feedback."""
        try:
            raw_feedback = self.rag.evaluate_answer(
                question=question_text,
                answer=answer_text,
                job_role=self.profile.job_role,
                experience_level=self.profile.experience_level.value,
            )
            feedback = self._parse_feedback(raw_feedback)
        except Exception as e:
            logger.warning(f"Evaluation failed: {e}. Using fallback scoring.")
            feedback = self._generate_fallback_feedback(answer_text)

        # Store for session analytics
        self.answers.append({
            "question_id": question_id,
            "question_text": question_text,
            "answer_text": answer_text,
            "time_taken_seconds": time_taken_seconds,
            "feedback": feedback.model_dump(),
        })
        self.scores.append(feedback.score)
        return feedback

    # ─── Session Summary ───────────────────────────────────────────────────────

    def get_session_summary(self) -> SessionSummary:
        """Generate comprehensive session summary with analytics."""
        if not self.scores:
            avg_score = 0.0
        else:
            avg_score = sum(s.overall for s in self.scores) / len(self.scores)

        # Compute per-type scores
        type_scores: Dict[str, List[float]] = {}
        for i, ans in enumerate(self.answers):
            if i < len(self.questions):
                q_type = self.questions[i].question_type.value
                if q_type not in type_scores:
                    type_scores[q_type] = []
                if i < len(self.scores):
                    type_scores[q_type].append(self.scores[i].overall)

        topic_performance = {
            k: round(sum(v) / len(v), 1)
            for k, v in type_scores.items() if v
        }

        # Generate strengths/weaknesses from feedback
        all_strengths = []
        all_improvements = []
        for ans in self.answers:
            fb = ans.get("feedback", {})
            all_strengths.extend(fb.get("strengths", []))
            all_improvements.extend(fb.get("improvements", []))

        top_strengths = list(dict.fromkeys(all_strengths))[:3]
        top_weaknesses = list(dict.fromkeys(all_improvements))[:3]

        recommendation = self._get_recommendation(avg_score)
        next_steps = self._get_next_steps(avg_score, topic_performance)

        return SessionSummary(
            session_id=self.session_id,
            candidate_name=self.profile.name,
            job_role=self.profile.job_role,
            total_questions=len(self.questions),
            answered_questions=len(self.answers),
            average_score=round(avg_score, 1),
            top_strengths=top_strengths,
            top_weaknesses=top_weaknesses,
            topic_performance=topic_performance,
            recommendation=recommendation,
            next_steps=next_steps,
            created_at=self.created_at,
            completed_at=datetime.utcnow(),
        )

    def get_progress(self) -> Dict[str, Any]:
        """Return current session progress stats."""
        answered = len(self.answers)
        total = len(self.questions)
        avg = (
            round(sum(s.overall for s in self.scores) / len(self.scores), 1)
            if self.scores else 0.0
        )
        return {
            "answered": answered,
            "total": total,
            "progress_pct": round((answered / total) * 100, 0) if total else 0,
            "average_score": avg,
            "current_question_index": self.current_index,
            "is_complete": answered >= total,
        }

    # ─── Private Helpers ───────────────────────────────────────────────────────

    def _extract_first_question(self, raw: str) -> str:
        """Extract clean question text from Granite's raw output."""
        lines = raw.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:
                # Remove common prefixes
                for prefix in ["Q1:", "Q[1]:", "1.", "Question:", "-", "*"]:
                    if line.startswith(prefix):
                        line = line[len(prefix):].strip()
                if "?" in line or len(line) > 30:
                    return line
        # Fallback: return first substantial line
        return next((l.strip() for l in lines if len(l.strip()) > 20), raw[:200])

    def _extract_tips(self, raw: str) -> List[str]:
        """Extract preparation tips from generation output."""
        tips = []
        for line in raw.split("\n"):
            line = line.strip()
            if any(kw in line.lower() for kw in ["tip:", "hint:", "note:", "consider:", "remember:"]):
                tips.append(line)
        return tips[:3] if tips else ["Structure your answer clearly.", "Use specific examples."]

    def _parse_feedback(self, raw: str) -> AnswerFeedback:
        """Parse Granite's evaluation response into AnswerFeedback."""
        def extract_score(text: str, label: str) -> float:
            # Match "Label: 8" or "Label Method: 7" or "Label Depth: 9"
            pattern = rf"{label}[^:\n]{{0,20}}:\s*(\d+(?:\.\d+)?)"
            match = re.search(pattern, text, re.IGNORECASE)
            return min(10.0, float(match.group(1))) if match else 6.0

        def extract_list(text: str, label: str) -> List[str]:
            items = []
            in_section = False
            for line in text.split("\n"):
                if label.lower() in line.lower():
                    in_section = True
                    continue
                if in_section:
                    line = line.strip().lstrip("-*•123456789. ")
                    if line and len(line) > 5:
                        items.append(line)
                    if any(kw in line.lower() for kw in ["improvement", "strength", "model", "keyword", "follow"]) and line != "":
                        if label.lower() not in line.lower():
                            break
            return items[:3] if items else [f"See detailed feedback above."]

        score = ScoreBreakdown(
            relevance=extract_score(raw, "relevance"),
            star_method=extract_score(raw, "star"),
            technical_depth=extract_score(raw, "technical"),
            communication=extract_score(raw, "communication"),
            originality=extract_score(raw, "originality"),
            overall=extract_score(raw, "overall"),
        )

        # Extract model answer hint
        hint_match = re.search(r"model answer[:\s]+(.+?)(?:\n|$)", raw, re.IGNORECASE)
        hint = hint_match.group(1).strip() if hint_match else "Focus on concrete, quantified examples."

        # Extract follow-up
        followup_match = re.search(r"follow[- ]up[:\s]+(.+?)(?:\n|$)", raw, re.IGNORECASE)
        followup = followup_match.group(1).strip() if followup_match else None

        return AnswerFeedback(
            score=score,
            strengths=extract_list(raw, "strength"),
            improvements=extract_list(raw, "improvement"),
            model_answer_hint=hint,
            follow_up_question=followup,
            keywords_used=extract_list(raw, "keywords used"),
            keywords_missed=extract_list(raw, "keywords missed"),
        )

    def _generate_fallback_feedback(self, answer: str) -> AnswerFeedback:
        """Generate basic feedback when Granite is unavailable."""
        word_count = len(answer.split())
        has_numbers = any(c.isdigit() for c in answer)
        score_val = 5.0 + (1.5 if word_count > 50 else 0) + (1.0 if has_numbers else 0)
        score_val = min(8.0, score_val)

        return AnswerFeedback(
            score=ScoreBreakdown(
                relevance=score_val,
                star_method=score_val - 0.5,
                technical_depth=score_val - 0.5,
                communication=score_val,
                originality=score_val - 1.0,
                overall=score_val,
            ),
            strengths=["You provided a response to the question.", "Your answer showed some relevant knowledge."],
            improvements=["Add quantified results (numbers, percentages, timeframes).", "Structure using the STAR method.", "Include more specific technical details."],
            model_answer_hint="A strong answer uses the STAR method with quantified results.",
            follow_up_question="Can you elaborate on the outcome you achieved?",
            keywords_used=[],
            keywords_missed=["quantified results", "STAR method", "specific examples"],
        )

    def _get_fallback_question(self, q_type: QuestionType, role: str, topic: str) -> str:
        fallbacks = {
            QuestionType.HR: f"Tell me about yourself and why you're interested in this {role} position.",
            QuestionType.TECHNICAL: f"What are the most important technical skills for a {role}, and how have you applied them?",
            QuestionType.BEHAVIORAL: f"Describe a challenging situation you faced as a {role} and how you resolved it.",
            QuestionType.SITUATIONAL: f"If you discovered a critical issue in production right before a major release, what would you do?",
            QuestionType.CULTURE_FIT: f"What kind of work environment do you thrive in?",
            QuestionType.CASE_STUDY: f"Walk me through how you would approach a new project as a {role}.",
        }
        return fallbacks.get(q_type, f"Tell me about your experience as a {role}.")

    def _get_recommendation(self, avg_score: float) -> str:
        if avg_score >= 8.5:
            return "🌟 Outstanding! You're highly likely to impress interviewers. Focus on fine-tuning delivery and researching the specific company."
        elif avg_score >= 7.0:
            return "✅ Strong performance. You demonstrate solid fundamentals. Practice the areas flagged for improvement to maximize your chances."
        elif avg_score >= 5.5:
            return "📈 Good foundation. Keep practicing — focus specifically on technical depth and the STAR method for behavioral answers."
        else:
            return "🎯 Needs improvement. Dedicate 2-3 weeks to structured preparation. Focus on core technical concepts and behavioral frameworks."

    def _get_next_steps(self, avg_score: float, topic_performance: Dict[str, float]) -> List[str]:
        steps = []
        weak_topics = [t for t, s in topic_performance.items() if s < 6.0]
        if weak_topics:
            steps.append(f"Deep-dive study on: {', '.join(weak_topics)}")
        if avg_score < 7.0:
            steps.append("Practice 2 mock interviews per week using this platform")
            steps.append("Record yourself answering questions to improve delivery")
        steps.append("Research the target company's tech stack and recent news")
        steps.append("Prepare 5 strong STAR stories covering different competencies")
        steps.append("Craft 5 thoughtful questions to ask your interviewers")
        return steps[:5]
