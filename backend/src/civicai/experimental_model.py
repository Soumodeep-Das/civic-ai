"""Load the checksum-pinned experimental model from an explicit local source."""
import base64
import hashlib
import io
import os
from functools import lru_cache
from pathlib import Path

MAX_MODEL_BYTES = 5 * 1024 * 1024
MAX_BASE64_BYTES = 8 * 1024 * 1024


def _read_model_bytes() -> bytes:
    path = os.environ.get("CIVICAI_EXPERIMENTAL_MODEL_PATH", "").strip()
    encoded_path = os.environ.get("CIVICAI_EXPERIMENTAL_MODEL_BASE64_PATH", "").strip()
    if bool(path) == bool(encoded_path):
        raise ValueError("Configure exactly one experimental model source")
    if path:
        content = Path(path).read_bytes()
    else:
        encoded = Path(encoded_path).read_bytes()
        if len(encoded) > MAX_BASE64_BYTES:
            raise ValueError("Encoded model is too large")
        content = base64.b64decode(b"".join(encoded.split()), validate=True)
    if not content or len(content) > MAX_MODEL_BYTES:
        raise ValueError("Model size is invalid")
    return content


@lru_cache(maxsize=1)
def load_experimental_model():
    """Return the trusted pipeline only after source, hash and metadata checks."""
    expected = os.environ.get("CIVICAI_EXPERIMENTAL_MODEL_SHA256", "").strip().lower()
    if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
        raise ValueError("Experimental model hash is invalid")
    content = _read_model_bytes()
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError("Experimental model checksum differs")
    import joblib

    bundle = joblib.load(io.BytesIO(content))
    if bundle.get("label_origin") != "AI_proposals" or bundle.get("operational_release_approved") is not False:
        raise ValueError("Unsupported experimental model metadata")
    return bundle["pipeline"], expected
