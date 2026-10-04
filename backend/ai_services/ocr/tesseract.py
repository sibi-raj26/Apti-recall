import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from backend.ai_services.ocr.base import OCRResult, BaseOCRProvider

logger = logging.getLogger(__name__)


@dataclass
class TesseractConfig:
    tesseract_cmd: Optional[str] = None
    language: str = "eng"
    timeout: int = 30


class TesseractOCRProvider(BaseOCRProvider):
    def __init__(self, config: Optional[TesseractConfig] = None):
        self.config = config or TesseractConfig()
        self.tesseract_cmd = self._resolve_tesseract_cmd()

    def _resolve_tesseract_cmd(self) -> Optional[str]:
        cmd = self.config.tesseract_cmd or os.environ.get("TESSERACT_CMD", "")
        if cmd:
            return cmd
        return None

    def extract_text(self, image_path: str, language: str = "eng") -> OCRResult:
        try:
            import pytesseract
            from PIL import Image

            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

            if not os.path.exists(image_path):
                return OCRResult(text="", confidence=None, provider="tesseract", language=language, status="failed")

            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=language)
            return OCRResult(
                text=text,
                confidence=None,
                provider="tesseract",
                language=language,
                status="success",
            )
        except ImportError:
            logger.warning("pytesseract is not installed.")
            return OCRResult(text="", confidence=None, provider="tesseract", language=language, status="failed")
        except Exception as exc:
            logger.warning("Tesseract OCR failed: %s", exc)
            return OCRResult(text="", confidence=None, provider="tesseract", language=language, status="failed")
