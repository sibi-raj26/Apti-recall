import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OCRResult:
    text: str
    confidence: Optional[float]
    provider: str
    language: str
    status: str


class BaseOCRProvider(ABC):
    @abstractmethod
    def extract_text(self, image_path: str, language: str = "eng") -> OCRResult:
        ...
