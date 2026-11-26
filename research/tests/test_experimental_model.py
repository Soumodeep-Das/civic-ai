import base64
import hashlib
import sys
from types import SimpleNamespace

import pytest

from civicai.experimental_model import load_experimental_model


@pytest.fixture(autouse=True)
def clear_model_cache():
    load_experimental_model.cache_clear()
    yield
    load_experimental_model.cache_clear()


def configure(monkeypatch, content, expected):
    monkeypatch.setenv("CIVICAI_EXPERIMENTAL_MODEL_SHA256", expected)
    monkeypatch.setitem(
        sys.modules,
        "joblib",
        SimpleNamespace(
            load=lambda stream: {
                "pipeline": "verified-pipeline",
                "label_origin": "AI_proposals",
                "operational_release_approved": False,
            }
        ),
    )


def test_loads_checksum_pinned_base64_secret(monkeypatch, tmp_path):
    content = b"trusted experimental artifact"
    secret = tmp_path / "model.joblib.b64"
    secret.write_bytes(base64.b64encode(content))
    monkeypatch.delenv("CIVICAI_EXPERIMENTAL_MODEL_PATH", raising=False)
    monkeypatch.setenv("CIVICAI_EXPERIMENTAL_MODEL_BASE64_PATH", str(secret))
    configure(monkeypatch, content, hashlib.sha256(content).hexdigest())
    assert load_experimental_model() == ("verified-pipeline", hashlib.sha256(content).hexdigest())


def test_rejects_ambiguous_sources(monkeypatch, tmp_path):
    direct = tmp_path / "model.joblib"
    direct.write_bytes(b"model")
    encoded = tmp_path / "model.joblib.b64"
    encoded.write_bytes(base64.b64encode(b"model"))
    monkeypatch.setenv("CIVICAI_EXPERIMENTAL_MODEL_PATH", str(direct))
    monkeypatch.setenv("CIVICAI_EXPERIMENTAL_MODEL_BASE64_PATH", str(encoded))
    monkeypatch.setenv("CIVICAI_EXPERIMENTAL_MODEL_SHA256", hashlib.sha256(b"model").hexdigest())
    with pytest.raises(ValueError, match="exactly one"):
        load_experimental_model()


def test_rejects_checksum_difference(monkeypatch, tmp_path):
    content = b"model"
    direct = tmp_path / "model.joblib"
    direct.write_bytes(content)
    monkeypatch.setenv("CIVICAI_EXPERIMENTAL_MODEL_PATH", str(direct))
    monkeypatch.delenv("CIVICAI_EXPERIMENTAL_MODEL_BASE64_PATH", raising=False)
    configure(monkeypatch, content, "0" * 64)
    with pytest.raises(ValueError, match="checksum"):
        load_experimental_model()
