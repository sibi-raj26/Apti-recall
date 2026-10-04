import logging
import re
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class QuestionCandidate:
    index: int
    text: str


class QuestionExtractor:
    def extract(self, text: str) -> List[QuestionCandidate]:
        if not text or not text.strip():
            return []

        cleaned = self._normalize(text)
        candidates = self._split_questions(cleaned)
        if not candidates:
            candidates = [QuestionCandidate(index=1, text=cleaned.strip())]
        return candidates

    def _normalize(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    def _split_questions(self, text: str) -> List[QuestionCandidate]:
        pattern = re.compile(r"(?:^|\n)(\d+)[\.\)]\s*(.*?)(?=\n\d+[\.\)]\s*|\Z)", re.DOTALL)
        matches = pattern.findall(text)
        if not matches:
            return []

        candidates = []
        for idx, (_, content) in enumerate(matches, start=1):
            candidate_text = content.strip()
            if candidate_text:
                candidates.append(QuestionCandidate(index=idx, text=candidate_text))
        return candidates
