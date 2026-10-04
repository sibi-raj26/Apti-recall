import logging
from django.conf import settings

from backend.apps.questions.models import Question, SolutionStep, Shortcut
from backend.apps.topics.models import Topic, ProblemType
from backend.apps.solve.models import UserAttempt
from backend.ai_services.base import BaseLLMProvider
from backend.ai_services.prompt_templates import SOLVER_PROMPT

logger = logging.getLogger(__name__)

SOLVE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "question_understanding": {"type": "string"},
        "topic": {"type": "string"},
        "problem_type": {"type": "string"},
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
    "required": ["question_understanding", "topic", "problem_type", "concept", "approach", "steps", "final_answer"],
}

MAX_QUESTION_LENGTH = 5000


class SolveService:
    def __init__(self, llm_client=None):
        if llm_client is not None:
            self.llm_client = llm_client
        else:
            from backend.ai_services.llm_client import LLMClient
            self.llm_client = LLMClient()

        self._topics_cache = None
        self._problem_types_cache = None

    def _get_topics(self):
        if self._topics_cache is None:
            self._topics_cache = list(Topic.objects.filter(is_active=True).values("id", "name", "slug"))
        return self._topics_cache

    def _get_problem_types(self):
        if self._problem_types_cache is None:
            self._problem_types_cache = list(ProblemType.objects.filter(is_active=True).values("id", "name", "topic__id", "topic__slug"))
        return self._problem_types_cache

    def _build_topic_context(self):
        topics = self._get_topics()
        problem_types = self._get_problem_types()
        topic_slugs = ", ".join(t["slug"] for t in topics) or "none"
        pt_entries = ", ".join(f"{pt['topic__slug']}: {pt['name']}" for pt in problem_types) or "none"
        return topic_slugs, pt_entries

    def _find_existing_question(self, question_text):
        normalized = " ".join(question_text.strip().split())
        if len(normalized) < 10:
            return None
        qs = Question.objects.filter(is_active=True)
        if len(normalized) >= 20:
            match = qs.filter(question_text__iexact=normalized).first()
            if match:
                return match
        return qs.filter(question_text__icontains=normalized[:60]).first()

    def _match_topic(self, topic_slug):
        if not topic_slug:
            return None
        slug = topic_slug.strip().lower().replace(" ", "-")
        return Topic.objects.filter(slug=slug, is_active=True).first()

    def _match_problem_type(self, topic, problem_type_name):
        if not topic or not problem_type_name:
            return None
        name = problem_type_name.strip().lower()
        return ProblemType.objects.filter(topic=topic, is_active=True).filter(name__iexact=name).first() or \
               ProblemType.objects.filter(topic=topic, is_active=True).filter(name__icontains=name).first()

    def _validate_ai_output(self, data):
        if not isinstance(data, dict):
            raise ValueError("AI response is not a JSON object.")
        required = ["question_understanding", "topic", "problem_type", "concept", "approach", "steps", "final_answer"]
        for field in required:
            if field not in data:
                raise ValueError(f"AI response missing required field: {field}")
        if not isinstance(data["steps"], list) or len(data["steps"]) == 0:
            raise ValueError("AI response steps must be a non-empty list.")
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

    def _build_existing_response(self, question, user, uploaded_question=None):
        steps = []
        for step in question.solution_steps.all().order_by("step_number"):
            steps.append({
                "step": step.step_number,
                "title": step.title,
                "calculation": step.description,
                "explanation": step.description,
            })
        shortcut = ""
        shortcut_qs = question.shortcuts.all().order_by("title")
        if shortcut_qs.exists():
            shortcut = shortcut_qs.first().description
        topic_data = {"id": question.topic.id, "name": question.topic.name}
        problem_type_data = {"id": question.problem_type.id, "name": question.problem_type.name}
        attempt = UserAttempt.objects.create(
            user=user,
            question=question,
            uploaded_question=uploaded_question,
            status="completed",
            user_answer="",
            is_correct=None,
            solution_feedback={"source": "existing", "verification_status": "NOT_VERIFIED"},
        )
        return {
            "question_text": question.question_text,
            "topic": topic_data,
            "problem_type": problem_type_data,
            "concept": question.explanation_concept,
            "approach": question.explanation_approach,
            "steps": steps,
            "final_answer": question.correct_answer,
            "shortcut": shortcut,
            "confidence": 1.0,
            "verification_status": "NOT_VERIFIED",
            "source": "existing",
            "attempt_id": attempt.id,
        }

    def _build_ai_response(self, validated, user, topic, problem_type, uploaded_question=None):
        topic_data = {"id": topic.id, "name": topic.name} if topic else None
        problem_type_data = {"id": problem_type.id, "name": problem_type.name} if problem_type else None
        attempt = UserAttempt.objects.create(
            user=user,
            question=None,
            uploaded_question=uploaded_question,
            status="completed",
            user_answer="",
            is_correct=None,
            solution_feedback={
                "source": "ai_generated",
                "raw_topic": validated.get("topic", ""),
                "raw_problem_type": validated.get("problem_type", ""),
                "verification_status": "PENDING",
            },
        )
        solve_output = {
            "question_text": validated["question_understanding"],
            "topic": topic_data,
            "problem_type": problem_type_data,
            "concept": validated.get("concept", ""),
            "approach": validated.get("approach", ""),
            "steps": validated.get("steps", []),
            "final_answer": validated.get("final_answer", ""),
        }
        verification_status = "NOT_VERIFIED"
        verification_details = {}
        try:
            from backend.apps.solve.services.verification_service import VerificationService
            verifier = VerificationService()
            result = verifier.verify(attempt, solve_output)
            verification_status = result.status
            verification_details = {
                "method": result.method,
                "confidence": result.confidence,
                "details": result.details,
                "checks": result.checks,
                "expected": result.expected,
                "actual": result.actual,
            }
            attempt.solution_feedback["verification_status"] = verification_status
            attempt.solution_feedback["verification_details"] = verification_details
            attempt.save(update_fields=["solution_feedback"])
        except Exception as exc:
            logger.exception("Verification failed for attempt %s", attempt.id)
            verification_status = "UNABLE_TO_VERIFY"
            verification_details = {"error": str(exc)}
            attempt.solution_feedback["verification_status"] = verification_status
            attempt.solution_feedback["verification_details"] = verification_details
            attempt.save(update_fields=["solution_feedback"])
        return {
            "question_text": validated["question_understanding"],
            "topic": topic_data,
            "problem_type": problem_type_data,
            "concept": validated.get("concept", ""),
            "approach": validated.get("approach", ""),
            "steps": validated.get("steps", []),
            "final_answer": validated.get("final_answer", ""),
            "shortcut": validated.get("shortcut", ""),
            "confidence": validated.get("confidence", 0.0),
            "verification_status": verification_status,
            "verification_details": verification_details,
            "source": "ai_generated",
            "attempt_id": attempt.id,
        }

    def solve(self, user, question_text, uploaded_question=None):
        if not question_text or not question_text.strip():
            raise ValueError("Question text is required.")
        question_text = question_text.strip()
        if len(question_text) > MAX_QUESTION_LENGTH:
            raise ValueError(f"Question text exceeds maximum length of {MAX_QUESTION_LENGTH} characters.")

        existing_question = self._find_existing_question(question_text)
        if existing_question:
            return self._build_existing_response(existing_question, user, uploaded_question=uploaded_question)

        topic_slugs, pt_entries = self._build_topic_context()
        prompt = SOLVER_PROMPT.format(
            question_text=question_text,
            topics=topic_slugs,
            problem_types=pt_entries,
        )
        raw = self.llm_client.structured_call(
            prompt,
            SOLVE_OUTPUT_SCHEMA,
            timeout=getattr(settings, "AI_REQUEST_TIMEOUT", 120),
        )

        validated = self._validate_ai_output(raw)
        topic = self._match_topic(validated.get("topic", ""))
        problem_type = self._match_problem_type(topic, validated.get("problem_type", ""))
        return self._build_ai_response(validated, user, topic, problem_type, uploaded_question=uploaded_question)
