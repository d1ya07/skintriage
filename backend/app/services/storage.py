"""Safe image storage.

Every upload is opened and verified with Pillow, auto-rotated, converted to RGB,
downscaled, and re-encoded as JPEG. Re-encoding drops all EXIF metadata
(GPS location, device info), which protects patient privacy.
"""
import io
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

Image.MAX_IMAGE_PIXELS = 40_000_000  # refuse "decompression bomb" images
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
_FILENAME_RE = re.compile(r"^[0-9a-f]{32}\.jpg$")
BACKEND_DIR = Path(__file__).resolve().parents[2]


def upload_root() -> Path:
    root = Path(settings.UPLOAD_DIR)
    return root if root.is_absolute() else BACKEND_DIR / root


@dataclass
class StoredImage:
    path: str  # relative: "<user_id>/<uuid>.jpg"
    width: int
    height: int
    size_bytes: int


def _open_verified(data: bytes) -> Image.Image:
    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            probe.verify()  # detects truncated / corrupt files
        img = Image.open(io.BytesIO(data))  # verify() leaves the image unusable, so reopen
        img.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That file isn't a readable image")
    if fmt not in ALLOWED_FORMATS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Please upload a JPG, PNG or WEBP image"
        )
    return img


def preprocess(data: bytes) -> Image.Image:
    """Validate raw bytes and return a clean, upright RGB image (not yet resized)."""
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The file is empty")
    if len(data) > settings.MAX_UPLOAD_BYTES:
        mb = settings.MAX_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Image is too large (max {mb} MB)")
    img = _open_verified(data)
    img = ImageOps.exif_transpose(img).convert("RGB")  # honour phone rotation
    if min(img.size) < settings.IMAGE_MIN_SIDE:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Image is too small. Use a photo at least {settings.IMAGE_MIN_SIDE} pixels wide and tall.",
        )
    return img


def save_image(user_id: int, data: bytes) -> tuple[StoredImage, Image.Image]:
    """Validate, clean and store an upload. Returns the stored info and the clean image."""
    img = preprocess(data)
    img.thumbnail((settings.IMAGE_MAX_SIDE, settings.IMAGE_MAX_SIDE), Image.Resampling.LANCZOS)

    folder = upload_root() / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.jpg"
    dest = folder / name
    img.save(dest, "JPEG", quality=90, optimize=True)  # no exif= argument, so metadata is dropped

    stored = StoredImage(
        path=f"{user_id}/{name}", width=img.width, height=img.height, size_bytes=dest.stat().st_size
    )
    return stored, img


def resolve_image(path: str) -> Optional[Path]:
    """Map a stored relative path to a real file, refusing anything suspicious."""
    parts = path.split("/")
    if len(parts) != 2 or not parts[0].isdigit() or not _FILENAME_RE.match(parts[1]):
        return None
    f = upload_root() / parts[0] / parts[1]
    return f if f.is_file() else None


def delete_image(path: str) -> None:
    f = resolve_image(path)
    if f:
        f.unlink(missing_ok=True)
