"""Bounded local image storage; only decoded and re-encoded raster images survive."""
import io
import os
import re
import warnings
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
REFERENCE_PREFIX = "/api/v1/complaint-images/"


def upload_directory() -> Path:
    default = Path(__file__).resolve().parents[3] / "data/uploads/complaints"
    return Path(os.environ.get("UPLOAD_DIR", str(default))).resolve()


def save_image(content: bytes, content_type: str | None, directory: Path) -> str:
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Image must be 5 MiB or smaller.")
    if content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(422, "Only JPEG and PNG images are accepted.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as source:
                expected = {"image/jpeg": "JPEG", "image/png": "PNG"}[content_type]
                if source.format != expected or source.width * source.height > MAX_IMAGE_PIXELS:
                    raise ValueError("Invalid image format or dimensions")
                source.verify()
            with Image.open(io.BytesIO(content)) as source:
                source.load()
                clean = source.convert("RGB" if expected == "JPEG" else "RGBA")
                # Fresh pixels discard EXIF (including GPS), text and trailing payloads.
                clean = Image.frombytes(clean.mode, clean.size, clean.tobytes())
                output = io.BytesIO()
                clean.save(output, format=expected)
                encoded = output.getvalue()
                if len(encoded) > MAX_IMAGE_BYTES:
                    raise HTTPException(413, "Processed image must be 5 MiB or smaller.")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, "Upload must contain a valid JPEG or PNG image.") from None
    filename = uuid4().hex + (".jpg" if expected == "JPEG" else ".png")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    try:
        with path.open("xb") as target:
            target.write(encoded)
    except OSError:
        path.unlink(missing_ok=True)
        raise
    return REFERENCE_PREFIX + filename


def image_path(directory: Path, filename: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}\.(?:jpg|png)", filename):
        raise HTTPException(404, "Image not found.")
    path = directory / filename
    if not path.is_file() or path.is_symlink():
        raise HTTPException(404, "Image not found.")
    return path
