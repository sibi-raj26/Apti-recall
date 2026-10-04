import logging
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from backend.apps.recall.models import RecallRecord
from backend.apps.solve.models import UserAttempt

logger = logging.getLogger(__name__)

RECALL_STRONG_THRESHOLD = 0.75
RECALL_MODERATE_THRESHOLD = 0.45
WEAK_AVG_SCORE_THRESHOLD = 0.4
WEAK_CONSECUTIVE_INCORRECT_THRESHOLD = 2
WEAK_ACCURACY_THRESHOLD = 0.5
WEAK_MIN_ATTEMPTS = 3
RECALL_EMA_ALPHA = 0.7
MAX_HINTS = 3
EXPECTED_TIME_BY_DIFFICULTY = {
    "easy": 30,
    "medium": 60,
    "hard": 120,
}


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _get_difficulty(attempt: UserAttempt) -> str:
    if attempt.question and attempt.question.difficulty:
        return attempt.question.difficulty
    return "easy"


def _get_expected_time(difficulty: str) -> int:
    return EXPECTED_TIME_BY_DIFFICULTY.get(difficulty, 60)


def compute_recall_score(attempt: UserAttempt) -> float:
    accuracy = 1.0 if attempt.is_correct else 0.0
    difficulty = _get_difficulty(attempt)
    expected_time = _get_expected_time(difficulty)
    solving_time = attempt.time_taken_seconds or 0
    hints_used = attempt.hints_used or 0
    attempts_count = attempt.attempts_count or 1

    base_score = accuracy * 0.5
    time_penalty = max(0, (solving_time - expected_time) / expected_time) * 0.15 if expected_time > 0 else 0.0
    hint_penalty = (min(hints_used, MAX_HINTS) / MAX_HINTS) * 0.15
    attempt_penalty = (attempts_count - 1) * 0.05
    solution_penalty = 0.1 if attempt.viewed_solution else 0.0
    shortcut_penalty = 0.05 if attempt.viewed_shortcut else 0.0

    recall_score = base_score - time_penalty - hint_penalty - attempt_penalty - solution_penalty - shortcut_penalty
    return _clamp(recall_score, 0.0, 1.0)


def _compute_next_practice_at(recall_score: float) -> timezone.datetime:
    now = timezone.now()
    if recall_score >= RECALL_STRONG_THRESHOLD:
        interval = timedelta(days=7, hours=int(_jitter_hours(48)))
    elif recall_score >= RECALL_MODERATE_THRESHOLD:
        interval = timedelta(days=3, hours=int(_jitter_hours(24)))
    else:
        interval = timedelta(days=1, hours=int(_jitter_hours(12)))
    return now + interval


def _jitter_hours(max_hours: int) -> float:
    import random
    return random.uniform(0, max_hours)


def detect_weakness(record: RecallRecord, recent_attempts: list[UserAttempt]) -> bool:
    if len(recent_attempts) == 0:
        return False

    recent_scores = [compute_recall_score(a) for a in recent_attempts]
    if len(recent_scores) >= 5:
        avg_score = sum(recent_scores[-5:]) / 5
        if avg_score < WEAK_AVG_SCORE_THRESHOLD:
            return True

    consecutive_incorrect = 0
    for attempt in reversed(recent_attempts):
        if attempt.is_correct is False:
            consecutive_incorrect += 1
        else:
            break
    if consecutive_incorrect > WEAK_CONSECUTIVE_INCORRECT_THRESHOLD:
        return True

    total = len(recent_attempts)
    correct = sum(1 for a in recent_attempts if a.is_correct is True)
    if total > WEAK_MIN_ATTEMPTS and (correct / total) < WEAK_ACCURACY_THRESHOLD:
        return True

    return False


def _get_or_create_record(user, topic, problem_type, question):
    record, _ = RecallRecord.objects.get_or_create(
        user=user,
        topic=topic,
        problem_type=problem_type,
        question=question,
        defaults={
            "recall_score": 0.0,
            "accuracy_score": 0.0,
            "practice_count": 0,
            "is_weak": False,
        },
    )
    return record


def _update_accuracy_score(record: RecallRecord, recent_attempts: list[UserAttempt]) -> float:
    total = len(recent_attempts)
    if total == 0:
        return 0.0
    correct = sum(1 for a in recent_attempts if a.is_correct is True)
    return correct / total


def update_recall(user, attempt: UserAttempt) -> RecallRecord:
    if not attempt.question or not attempt.question.topic or not attempt.question.problem_type:
        raise ValueError("Attempt must have an associated question with topic and problem type.")

    topic = attempt.question.topic
    problem_type = attempt.question.problem_type
    question = attempt.question

    record = _get_or_create_record(user, topic, problem_type, question)

    recent_attempts = list(
        UserAttempt.objects.filter(
            user=user,
            question=question,
            status="completed",
        ).order_by("-created_at")[:20]
    )

    current_score = compute_recall_score(attempt)
    record.recall_score = _clamp(
        RECALL_EMA_ALPHA * record.recall_score + (1 - RECALL_EMA_ALPHA) * current_score,
        0.0,
        1.0,
    )
    record.accuracy_score = _update_accuracy_score(record, recent_attempts)
    record.practice_count = (record.practice_count or 0) + 1
    record.last_practiced = timezone.now()
    record.next_practice_at = _compute_next_practice_at(record.recall_score)
    record.difficulty_at_practice = _get_difficulty(attempt)
    record.is_weak = detect_weakness(record, recent_attempts)
    record.save()
    return record


def get_daily_queue(user):
    now = timezone.now()
    return RecallRecord.objects.filter(
        user=user,
        next_practice_at__lte=now,
    ).order_by("-is_weak", "recall_score")


def get_weak_topics(user):
    return RecallRecord.objects.filter(
        user=user,
        is_weak=True,
    ).order_by("recall_score")


def get_recall_analytics(user):
    records = RecallRecord.objects.filter(user=user)
    total = records.count()
    weak = records.filter(is_weak=True).count()
    strong = records.filter(recall_score__gte=RECALL_STRONG_THRESHOLD).count()
    moderate = records.filter(
        recall_score__gte=RECALL_MODERATE_THRESHOLD,
        recall_score__lt=RECALL_STRONG_THRESHOLD,
    ).count()

    avg_recall = 0.0
    if total > 0:
        avg_recall = sum(r.recall_score for r in records) / total

    return {
        "total_topics": total,
        "weak_count": weak,
        "moderate_count": moderate,
        "strong_count": strong,
        "average_recall_score": round(avg_recall, 4),
    }
