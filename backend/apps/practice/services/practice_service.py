import logging
from typing import Optional

from django.conf import settings

from backend.apps.questions.models import Question
from backend.apps.topics.models import Topic, ProblemType
from backend.ai_services.llm_client import LLMClient
from backend.ai_services.prompt_templates import PRACTICE_QUESTION_PROMPT
from backend.apps.solve.services.verification_service import VerificationService, VERIFICATION_STATUS_VERIFIED, VERIFICATION_STATUS_FAILED, VERIFICATION_STATUS_UNABLE

logger = logging.getLogger(__name__)

PRACTICE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "question_text": {"type": "string"},
        "topic": {"type": "string"},
        "problem_type": {"type": "string"},
        "difficulty": {"type": "string"},
        "concept": {"type": "string"},
        "approach": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "integer"},
                    "title": {"type": "string"},
                    "calculation": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["step", "title", "calculation", "explanation"],
            },
        },
        "final_answer": {"type": "string"},
        "shortcut": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["question_text", "topic", "problem_type", "difficulty", "concept", "approach", "steps", "final_answer"],
}


class PracticeService:
    def __init__(self, llm_client=None):
        if llm_client is not None:
            self.llm_client = llm_client
        else:
            self.llm_client = LLMClient()

    def _normalize_question_text(self, text: str) -> str:
        return " ".join(text.strip().split())

    def _find_existing_question(self, question_text: str):
        normalized = self._normalize_question_text(question_text)
        if len(normalized) < 10:
            return None
        qs = Question.objects.filter(is_active=True)
        if len(normalized) >= 20:
            match = qs.filter(question_text__iexact=normalized).first()
            if match:
                return match
        return qs.filter(question_text__icontains=normalized[:60]).first()

    def _validate_output(self, data: dict) -> dict:
        if not isinstance(data, dict):
            raise ValueError("Practice question output is not a JSON object.")
        required = ["question_text", "topic", "problem_type", "difficulty", "concept", "approach", "steps", "final_answer"]
        for field in required:
            if field not in data:
                raise ValueError(f"Practice question output missing required field: {field}")
        if not isinstance(data["steps"], list) or len(data["steps"]) == 0:
            raise ValueError("Practice question steps must be a non-empty list.")
        for idx, step in enumerate(data["steps"]):
            if not isinstance(step, dict):
                raise ValueError(f"Step {idx} is not an object.")
            for required_step_field in ["step", "title", "calculation", "explanation"]:
                if required_step_field not in step:
                    raise ValueError(f"Step {idx} missing field: {required_step_field}")
        if "confidence" not in data:
            data["confidence"] = 0.0
        try:
            data["confidence"] = float(data["confidence"])
        except (TypeError, ValueError):
            data["confidence"] = 0.0
        data["confidence"] = max(0.0, min(1.0, data["confidence"]))
        if "shortcut" not in data:
            data["shortcut"] = ""
        return data

    def _build_prompt(self, context: dict) -> str:
        return PRACTICE_QUESTION_PROMPT.format(
            question_text=context.get("question_text", ""),
            topic=context.get("topic", ""),
            problem_type=context.get("problem_type", ""),
            difficulty=context.get("difficulty", "easy"),
            concept=context.get("concept", ""),
        )

    def _match_topic(self, topic_slug: str) -> Optional[Topic]:
        if not topic_slug:
            return None
        slug = topic_slug.strip().lower().replace(" ", "-")
        return Topic.objects.filter(slug=slug, is_active=True).first()

    def _match_problem_type(self, topic: Optional[Topic], problem_type_name: str) -> Optional[ProblemType]:
        if not topic or not problem_type_name:
            return None
        name = problem_type_name.strip().lower()
        return ProblemType.objects.filter(topic=topic, is_active=True).filter(name__iexact=name).first() or \
               ProblemType.objects.filter(topic=topic, is_active=True).filter(name__icontains=name).first()

    def generate_similar_question(
        self,
        user,
        source_question=None,
        upload=None,
        question_index=None,
        topic=None,
        problem_type=None,
        difficulty=None,
        question_text=None,
        concept=None,
        approach=None,
        max_retries: int = 3,
    ) -> dict:
        context = self._build_context(
            source_question=source_question,
            upload=upload,
            question_index=question_index,
            topic=topic,
            problem_type=problem_type,
            difficulty=difficulty,
            question_text=question_text,
            concept=concept,
            approach=approach,
        )

        last_result = None
        for attempt in range(max_retries):
            raw = self.llm_client.structured_call(
                self._build_prompt(context),
                PRACTICE_OUTPUT_SCHEMA,
                timeout=getattr(settings, "AI_REQUEST_TIMEOUT", 120),
            )
            validated = self._validate_output(raw)

            duplicate = self._find_existing_question(validated["question_text"])
            if duplicate:
                if attempt < max_retries - 1:
                    context["question_text"] = f"Original: {context['question_text']}\nAlready generated: {validated['question_text']}\nGenerate a DIFFERENT similar question."
                    continue
                validated["duplicate_found"] = True
                validated["duplicate_question_id"] = duplicate.id

            topic_obj = self._match_topic(validated.get("topic", ""))
            problem_type_obj = self._match_problem_type(topic_obj, validated.get("problem_type", ""))

            solve_output = {
                "question_text": validated["question_text"],
                "topic": {"id": topic_obj.id, "name": topic_obj.name} if topic_obj else None,
                "problem_type": {"id": problem_type_obj.id, "name": problem_type_obj.name} if problem_type_obj else None,
                "concept": validated.get("concept", ""),
                "approach": validated.get("approach", ""),
                "steps": validated.get("steps", []),
                "final_answer": validated.get("final_answer", ""),
            }

            verifier = VerificationService()
            result = verifier.verify(None, solve_output)

            last_result = {
                "question_text": validated["question_text"],
                "topic": {"id": topic_obj.id, "name": topic_obj.name} if topic_obj else None,
                "problem_type": {"id": problem_type_obj.id, "name": problem_type_obj.name} if problem_type_obj else None,
                "difficulty": validated.get("difficulty", context.get("difficulty", "easy")),
                "concept": validated.get("concept", ""),
                "approach": validated.get("approach", ""),
                "steps": validated.get("steps", []),
                "final_answer": validated.get("final_answer", ""),
                "shortcut": validated.get("shortcut", ""),
                "confidence": validated.get("confidence", 0.0),
                "verification_status": result.status,
                "verification_details": {
                    "method": result.method,
                    "confidence": result.confidence,
                    "details": result.details,
                    "checks": result.checks,
                    "expected": result.expected,
                    "actual": result.actual,
                },
                "source": "practice_generated",
                "attempt": attempt + 1,
            }

            if result.status == VERIFICATION_STATUS_VERIFIED:
                return last_result

            if attempt < max_retries - 1:
                context["question_text"] = f"Original: {context['question_text']}\nPreviously generated: {validated['question_text']}\nVerification failed: {result.details}\nGenerate a DIFFERENT similar question with correct math."
                continue

        return last_result

    def _build_context(
        self,
        source_question=None,
        upload=None,
        question_index=None,
        topic=None,
        problem_type=None,
        difficulty=None,
        question_text=None,
        concept=None,
        approach=None,
    ) -> dict:
        if source_question is not None:
            return {
                "question_text": source_question.question_text,
                "topic": source_question.topic.name,
                "problem_type": source_question.problem_type.name,
                "difficulty": source_question.difficulty,
                "concept": source_question.explanation_concept,
                "approach": source_question.explanation_approach,
            }

        if upload is not None and question_index is not None:
            candidates = upload.question_candidates or []
            if not candidates:
                raise ValueError("No question candidates found for this upload.")
            if question_index < 1 or question_index > len(candidates):
                raise ValueError(f"question_index {question_index} is out of range for this upload.")
            selected = candidates[question_index - 1]
            selected_text = selected.get("text", "")
            if not selected_text.strip():
                raise ValueError("Selected question text is empty.")
            return {
                "question_text": selected_text,
                "topic": topic or upload.detected_topic.name if upload.detected_topic else "",
                "problem_type": problem_type or upload.detected_problem_type.name if upload.detected_problem_type else "",
                "difficulty": difficulty or "easy",
                "concept": concept or "",
                "approach": approach or "",
            }

        if all([topic, problem_type, difficulty, question_text]):
            return {
                "question_text": question_text,
                "topic": topic,
                "problem_type": problem_type,
                "difficulty": difficulty,
                "concept": concept or "",
                "approach": approach or "",
            }

        raise ValueError("Insufficient context to generate a similar question. Provide source_question, upload+question_index, or topic+problem_type+difficulty+question_text.")
