import logging
import os
import tempfile
from dataclasses import dataclass, field
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PreprocessedImage:
    path: str
    width: int
    height: int
    format: str
    metadata: dict = field(default_factory=dict)


class ImagePreprocessor:
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or os.path.join(tempfile.gettempdir(), "aptirecall_ocr")

    def preprocess(self, image_file) -> PreprocessedImage:
        try:
            from PIL import Image, ImageEnhance, ImageFilter

            if hasattr(image_file, "temporary_file_path"):
                image_path = image_file.temporary_file_path()
            elif hasattr(image_file, "read"):
                suffix = self._get_suffix(image_file.name)
                tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                for chunk in image_file.chunks():
                    tf.write(chunk)
                tf.close()
                image_path = tf.name
            elif isinstance(image_file, str):
                image_path = image_file
            else:
                return PreprocessedImage(
                    path=str(image_file),
                    width=0,
                    height=0,
                    format="UNKNOWN",
                    metadata={"error": "unsupported image file type"},
                )

            image = Image.open(image_path)
            width, height = image.size
            image_format = image.format or "UNKNOWN"

            if image.mode != "RGB":
                image = image.convert("RGB")

            processed = self._apply_preprocessing(image)
            output_path = self._save_processed(processed, image_path)
            return PreprocessedImage(
                path=output_path,
                width=width,
                height=height,
                format=image_format,
                metadata={"original_mode": image.mode},
            )
        except Exception as exc:
            logger.warning("Image preprocessing failed, using original: %s", exc)
            image_path = getattr(image_file, "temporary_file_path", lambda: str(image_file))()
            return PreprocessedImage(
                path=image_path,
                width=0,
                height=0,
                format="UNKNOWN",
                metadata={"error": str(exc)},
            )

    def _get_suffix(self, filename: str) -> str:
        _, ext = os.path.splitext(filename)
        return ext or ".png"

    def _apply_preprocessing(self, image):
        try:
            from PIL import ImageEnhance, ImageFilter
            image = image.convert("L")
            image = image.point(lambda p: 255 if p > 128 else 0)
            return image
        except Exception as exc:
            logger.debug("Basic preprocessing skipped: %s", exc)
            return image

    def _save_processed(self, image, original_path: str) -> str:
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
            base_name = os.path.basename(original_path)
            name, _ = os.path.splitext(base_name)
            output_path = os.path.join(self.temp_dir, f"{name}_processed.png")
            image.save(output_path, format="PNG")
            return output_path
        except Exception as exc:
            logger.warning("Could not save processed image: %s", exc)
            return original_path
