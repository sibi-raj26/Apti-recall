import logging

from backend.ai_services.ocr.base import BaseOCRProvider, OCRResult
from backend.ai_services.ocr.tesseract import TesseractOCRProvider

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self, provider: BaseOCRProvider = None):
        if provider is not None:
            self.provider = provider
        else:
            self.provider = TesseractOCRProvider()

    def extract_text(self, image_path: str, language: str = "eng") -> OCRResult:
        try:
            return self.provider.extract_text(image_path, language=language)
        except Exception as exc:
            logger.exception("OCR extraction failed")
            return OCRResult(text="", confidence=None, provider="unknown", language=language, status="failed")
