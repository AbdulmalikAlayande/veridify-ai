import hashlib
import time
import uuid
from pathlib import Path

import aiofiles
from PIL import Image, UnidentifiedImageError
from io import BytesIO

from app.config import get_settings
from app.exceptions import ImageTooLargeError, UnsupportedImageTypeError

settings = get_settings()

SUPPORTED_MIME_TYPES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

_PIL_FORMAT_TO_MIME = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


async def run_inference(image_bytes: bytes, image_hash: str) -> dict:
    if settings.mock_inference:
        return _mock_inference(image_hash)
    return await _real_inference(image_bytes)


def _mock_inference(image_hash: str) -> dict:
    seed = int(image_hash[:8], 16) % 100
    trust_score = seed
    start = time.time()
    time.sleep(0.3)
    processing_ms = int((time.time() - start) * 1000)

    if trust_score >= 70:
        verdict = "AUTHENTIC"
        confidence = "HIGH" if trust_score > 85 else "MEDIUM"
    elif trust_score >= 35:
        verdict = "MANIPULATED"
        confidence = "HIGH" if trust_score < 40 else "MEDIUM"
    else:
        verdict = "SYNTHETIC"
        confidence = "HIGH" if trust_score < 20 else "MEDIUM"

    return {
        "trust_score": trust_score,
        "verdict": verdict,
        "confidence": confidence,
        "spatial_score": min(trust_score + 3, 100),
        "frequency_score": max(trust_score - 3, 0),
        "processing_ms": processing_ms,
    }


async def _real_inference(image_bytes: bytes) -> dict:
    raise NotImplementedError(
        "Real inference not wired in. Set MOCK_INFERENCE=true, or load the model "
        "in main.py lifespan and replace this stub with model.predict()."
    )


async def validate_image(image_bytes: bytes, max_size_mb: int) -> tuple[str, str]:
    """Returns (mime_type, extension). Trusts magic bytes via Pillow — not filename."""
    if not image_bytes:
        raise UnsupportedImageTypeError("empty")

    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ImageTooLargeError(size_mb)

    try:
        with Image.open(BytesIO(image_bytes)) as img:
            pil_format = (img.format or "").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise UnsupportedImageTypeError("unknown") from exc

    mime_type = _PIL_FORMAT_TO_MIME.get(pil_format)
    if mime_type is None:
        raise UnsupportedImageTypeError(pil_format.lower() or "unknown")

    ext = SUPPORTED_MIME_TYPES[mime_type]
    return mime_type, ext


def compute_image_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


async def save_temp_image(image_bytes: bytes, ext: str) -> Path:
    temp_dir = Path(settings.temp_file_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / f"{uuid.uuid4()}.{ext}"
    async with aiofiles.open(path, "wb") as f:
        await f.write(image_bytes)
    return path


def delete_temp_image(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception:
        pass
